"""Testes do job de geração executado pelo worker (ADR-0014).

O CrewAI, o geocoding e o cache são substituídos: o objetivo é validar a máquina
de estados da execução, a persistência do resultado e o registro de custo real.
"""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.models import Execution, ExecutionStatus, Itinerary, UsageRecord
from src.models.location import Location
from src.worker import tasks

MARKDOWN = "# Roteiro de Roma\n\nDia 1: Coliseu."


@dataclass
class FakeTokenUsage:
    """Simula o `token_usage` do `CrewOutput`."""

    prompt_tokens: int = 1500
    completion_tokens: int = 6900


class FakeCrewOutput(str):
    """Saída da crew: comporta-se como string e expõe `token_usage`."""

    token_usage = FakeTokenUsage()


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Fábrica de sessões sobre SQLite em memória compartilhado."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(bind=engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def worker_env(mocker, session_factory):
    """Substitui as dependências externas do worker."""
    mocker.patch("src.worker.tasks.get_session_factory", return_value=session_factory)
    progress = mocker.patch("src.worker.tasks.ProgressBus").return_value
    progress.publish = mocker.AsyncMock()
    progress.close = mocker.AsyncMock()
    cache = mocker.patch("src.worker.tasks.get_cache_service").return_value
    cache.get_cached_itinerary.return_value = None
    return {"progress": progress, "cache": cache}


async def _create_execution(
    factory: async_sessionmaker[AsyncSession], **overrides: object
) -> uuid.UUID:
    defaults: dict[str, object] = {
        "origem": "São Paulo, Brasil",
        "destino": "Roma, Itália",
        "dias": 2,
        "interesses": "história",
        "moeda": "EUR",
        "idioma": "pt-BR",
        "briefing_hash": "hash",
        "status": ExecutionStatus.QUEUED,
    }
    defaults.update(overrides)
    async with factory() as session:
        execution = Execution(**defaults)  # type: ignore[arg-type]
        session.add(execution)
        await session.commit()
        await session.refresh(execution)
        return execution.id


def _mock_crew(mocker, output: object) -> None:
    builder = mocker.patch("src.worker.tasks.CrewBuilder").return_value
    builder.run.return_value = output
    builder.use_fallback = False


def _mock_geocoding(mocker, locations: list[Location]) -> None:
    service = mocker.patch("src.worker.tasks.GeocodingService").return_value
    service.process_itinerary_locations.return_value = locations


# ---------------------------------------------------------------------------
# Caminho de sucesso
# ---------------------------------------------------------------------------


async def test_successful_run_persists_itinerary_and_usage(
    mocker, session_factory, worker_env
) -> None:
    """Execução bem-sucedida grava roteiro, GeoJSON e custo real."""
    execution_id = await _create_execution(session_factory)
    _mock_crew(mocker, FakeCrewOutput(MARKDOWN))
    _mock_geocoding(mocker, [Location(name="Coliseu", lat=41.89, lon=12.49)])

    result = await tasks.generate_itinerary({}, execution_id=str(execution_id))

    assert result == ExecutionStatus.SUCCEEDED.value
    async with session_factory() as session:
        execution = await session.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == ExecutionStatus.SUCCEEDED
        assert execution.duration_seconds is not None
        assert execution.finished_at is not None
        assert execution.llm_gateway == "opencode_go"

        itinerary = await session.scalar(
            Itinerary.__table__.select().where(
                Itinerary.__table__.c.execution_id == execution_id
            )
        )
        assert itinerary is not None

        usage = list(await session.scalars(UsageRecord.__table__.select()))
        assert len(usage) == 1


async def test_successful_run_builds_geojson_features(
    mocker, session_factory, worker_env
) -> None:
    """Os locais viram um FeatureCollection com coordenadas lon/lat."""
    execution_id = await _create_execution(session_factory)
    _mock_crew(mocker, FakeCrewOutput(MARKDOWN))
    _mock_geocoding(
        mocker,
        [
            Location(name="Coliseu", lat=41.8902, lon=12.4922),
            Location(name="Sem coordenada", lat=None, lon=None),
        ],
    )

    await tasks.generate_itinerary({}, execution_id=str(execution_id))

    async with session_factory() as session:
        itinerary = (
            (
                await session.execute(
                    Itinerary.__table__.select().where(
                        Itinerary.__table__.c.execution_id == execution_id
                    )
                )
            )
            .mappings()
            .one()
        )
    geojson = itinerary["locations_geojson"]
    assert geojson["type"] == "FeatureCollection"
    # O local sem coordenada é descartado
    assert len(geojson["features"]) == 1
    assert geojson["features"][0]["geometry"]["coordinates"] == [12.4922, 41.8902]


async def test_cache_hit_skips_crew_and_records_no_cost(
    mocker, session_factory, worker_env
) -> None:
    """Roteiro em cache não executa a crew nem gera registro de custo."""
    execution_id = await _create_execution(session_factory)
    worker_env["cache"].get_cached_itinerary.return_value = MARKDOWN
    crew = mocker.patch("src.worker.tasks.CrewBuilder")
    _mock_geocoding(mocker, [])

    result = await tasks.generate_itinerary({}, execution_id=str(execution_id))

    assert result == ExecutionStatus.SUCCEEDED.value
    crew.assert_not_called()
    async with session_factory() as session:
        execution = await session.get(Execution, execution_id)
        assert execution is not None
        assert execution.served_from_cache is True
        usage = list(await session.scalars(UsageRecord.__table__.select()))
        assert usage == []


async def test_progress_events_are_published(
    mocker, session_factory, worker_env
) -> None:
    """O cliente conectado ao SSE recebe início, geocoding e conclusão."""
    execution_id = await _create_execution(session_factory)
    _mock_crew(mocker, FakeCrewOutput(MARKDOWN))
    _mock_geocoding(mocker, [])

    await tasks.generate_itinerary({}, execution_id=str(execution_id))

    steps = [
        call.args[0].step for call in worker_env["progress"].publish.call_args_list
    ]
    assert tasks.STEP_ORCHESTRATION in steps
    assert tasks.STEP_GEOCODING in steps
    assert tasks.STEP_DONE in steps


# ---------------------------------------------------------------------------
# Caminhos de falha e borda
# ---------------------------------------------------------------------------


async def test_crew_failure_marks_execution_failed(
    mocker, session_factory, worker_env
) -> None:
    """Falha na orquestração registra o erro e não deixa a execução pendurada."""
    execution_id = await _create_execution(session_factory)
    builder = mocker.patch("src.worker.tasks.CrewBuilder").return_value
    builder.run.side_effect = RuntimeError("todos os gateways falharam")
    builder.use_fallback = True

    result = await tasks.generate_itinerary({}, execution_id=str(execution_id))

    assert result == ExecutionStatus.FAILED.value
    async with session_factory() as session:
        execution = await session.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == ExecutionStatus.FAILED
        assert "gateways falharam" in (execution.error_message or "")
        assert execution.finished_at is not None


async def test_missing_execution_is_discarded(
    mocker, session_factory, worker_env
) -> None:
    """Job órfão (execução inexistente) falha sem levantar exceção."""
    result = await tasks.generate_itinerary({}, execution_id=str(uuid.uuid4()))

    assert result == ExecutionStatus.FAILED.value


async def test_cancelled_execution_is_not_processed(
    mocker, session_factory, worker_env
) -> None:
    """Execução cancelada antes do worker pegar o job é ignorada."""
    execution_id = await _create_execution(
        session_factory, status=ExecutionStatus.CANCELLED
    )
    crew = mocker.patch("src.worker.tasks.CrewBuilder")

    result = await tasks.generate_itinerary({}, execution_id=str(execution_id))

    assert result == ExecutionStatus.CANCELLED.value
    crew.assert_not_called()


async def test_usage_is_not_recorded_without_tokens(
    mocker, session_factory, worker_env
) -> None:
    """Sem tokens reportados, nenhum custo é inventado."""
    execution_id = await _create_execution(session_factory)
    _mock_crew(mocker, MARKDOWN)  # str puro: sem token_usage
    _mock_geocoding(mocker, [])

    await tasks.generate_itinerary({}, execution_id=str(execution_id))

    async with session_factory() as session:
        usage = list(await session.scalars(UsageRecord.__table__.select()))
    assert usage == []


async def test_find_stale_executions_lists_running(mocker, session_factory) -> None:
    """Diagnóstico operacional: identifica execuções presas em `running`."""
    mocker.patch("src.worker.tasks.get_session_factory", return_value=session_factory)
    running_id = await _create_execution(
        session_factory, status=ExecutionStatus.RUNNING
    )
    await _create_execution(session_factory, status=ExecutionStatus.SUCCEEDED)

    stale = await tasks.find_stale_executions()

    assert stale == [running_id]
