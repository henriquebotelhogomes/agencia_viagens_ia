"""Testes das rotas de execução (FR-02, FR-04, FR-05, FR-09)."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import PROBLEM_CONTENT_TYPE
from src.db.models import Execution, ExecutionStatus, Itinerary, UsageRecord

VALID_BRIEFING = {
    "origem": "São Paulo, Brasil",
    "destino": "Roma, Itália",
    "dias": 3,
    "interesses": "história e gastronomia",
    "moeda": "EUR",
    "idioma": "pt-BR",
}


async def _persist_execution(session: AsyncSession, **overrides: object) -> Execution:
    """Cria uma execução no banco de teste."""
    defaults = {
        "origem": "São Paulo, Brasil",
        "destino": "Roma, Itália",
        "dias": 3,
        "interesses": "história",
        "moeda": "EUR",
        "idioma": "pt-BR",
        "briefing_hash": "hash_qualquer",
        "status": ExecutionStatus.QUEUED,
    }
    defaults.update(overrides)
    execution = Execution(**defaults)  # type: ignore[arg-type]
    session.add(execution)
    await session.commit()
    await session.refresh(execution)
    return execution


# ---------------------------------------------------------------------------
# POST /v1/executions
# ---------------------------------------------------------------------------


async def test_create_execution_returns_202_and_stream_url(client: AsyncClient) -> None:
    """O aceite é imediato (202) e informa onde acompanhar o progresso."""
    response = await client.post("/v1/executions", json=VALID_BRIEFING)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == ExecutionStatus.QUEUED.value
    assert uuid.UUID(body["id"])
    assert body["id"] in body["stream_url"]
    assert body["stream_url"].endswith("/stream")


async def test_create_execution_persists_briefing(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """O briefing é persistido exatamente como recebido."""
    response = await client.post("/v1/executions", json=VALID_BRIEFING)

    execution = await db_session.get(Execution, uuid.UUID(response.json()["id"]))
    assert execution is not None
    assert execution.destino == "Roma, Itália"
    assert execution.moeda == "EUR"
    assert execution.idioma == "pt-BR"
    assert execution.briefing_hash  # fingerprint calculado


async def test_create_execution_enqueues_job(client: AsyncClient, mocker) -> None:
    """A API enfileira o job em vez de executar a crew (ADR-0014)."""
    spy = mocker.patch("src.api.routers.executions.enqueue_generation")

    await client.post("/v1/executions", json=VALID_BRIEFING)

    spy.assert_awaited_once()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dias", 0),  # abaixo do mínimo
        ("dias", 31),  # acima do máximo
        ("origem", "x"),  # curto demais
        ("moeda", "JPY"),  # fora do enum
        ("idioma", "fr-FR"),  # fora do enum
    ],
)
async def test_create_execution_rejects_invalid_briefing(
    client: AsyncClient, field: str, value: object
) -> None:
    """Entrada inválida retorna 422 no formato RFC 9457."""
    payload = {**VALID_BRIEFING, field: value}

    response = await client.post("/v1/executions", json=payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    body = response.json()
    assert body["title"] == "Requisição inválida"
    assert any(field in err["field"] for err in body["errors"])


async def test_create_execution_honors_idempotency_key(client: AsyncClient) -> None:
    """Repetir a mesma Idempotency-Key devolve a execução original."""
    headers = {"Idempotency-Key": "chave-unica-123"}

    first = await client.post("/v1/executions", json=VALID_BRIEFING, headers=headers)
    second = await client.post("/v1/executions", json=VALID_BRIEFING, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]


async def test_create_execution_returns_429_when_rate_limited(
    client: AsyncClient, fake_rate_limiter
) -> None:
    """Cota excedida retorna 429 com Retry-After (FR-09)."""
    fake_rate_limiter.allowed = False

    response = await client.post("/v1/executions", json=VALID_BRIEFING)

    assert response.status_code == 429
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    assert response.headers["retry-after"] == "1800"
    body = response.json()
    assert body["type"].endswith("rate-limit-exceeded")
    assert body["limit"] == 5


async def test_create_execution_returns_503_without_database(
    client: AsyncClient, api_settings, mocker
) -> None:
    """Sem banco configurado, a API recusa explicitamente (503)."""
    mocker.patch.object(
        type(api_settings), "database_enabled", property(lambda self: False)
    )

    response = await client.post("/v1/executions", json=VALID_BRIEFING)

    assert response.status_code == 503
    assert response.json()["dependency"] == "database"


# ---------------------------------------------------------------------------
# GET /v1/executions/{id}
# ---------------------------------------------------------------------------


async def test_get_execution_returns_detail(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Detalhe traz briefing, roteiro e custo agregado."""
    execution = await _persist_execution(
        db_session,
        status=ExecutionStatus.SUCCEEDED,
        duration_seconds=51.2,
        llm_gateway="opencode_go",
    )
    db_session.add(
        Itinerary(execution_id=execution.id, content_markdown="# Roteiro de Roma")
    )
    db_session.add(
        UsageRecord(
            execution_id=execution.id,
            model="deepseek-v4-flash",
            gateway="opencode_go",
            prompt_tokens=1500,
            completion_tokens=6900,
            cost_usd=0.006,
            baseline_cost_usd=0.111,
        )
    )
    await db_session.commit()

    response = await client.get(f"/v1/executions/{execution.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["itinerary_markdown"] == "# Roteiro de Roma"
    assert body["briefing"]["destino"] == "Roma, Itália"
    assert body["cost"]["total_tokens"] == 8400
    assert body["cost"]["savings_usd"] == pytest.approx(0.105)
    assert body["duration_seconds"] == 51.2


async def test_get_execution_returns_404_for_unknown_id(client: AsyncClient) -> None:
    """ID inexistente retorna 404 no formato RFC 9457."""
    response = await client.get(f"/v1/executions/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    assert response.json()["type"].endswith("execution-not-found")


# ---------------------------------------------------------------------------
# GET /v1/executions/{id}/geojson
# ---------------------------------------------------------------------------


async def test_geojson_returns_features(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Locais geocodificados saem como FeatureCollection (FR-05)."""
    execution = await _persist_execution(db_session)
    db_session.add(
        Itinerary(
            execution_id=execution.id,
            content_markdown="# Roteiro",
            locations_geojson={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [2.33, 48.86]},
                        "properties": {"name": "Museu do Louvre"},
                    }
                ],
            },
        )
    )
    await db_session.commit()

    response = await client.get(f"/v1/executions/{execution.id}/geojson")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert body["features"][0]["properties"]["name"] == "Museu do Louvre"


async def test_geojson_empty_when_no_itinerary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Sem roteiro ainda, devolve coleção vazia em vez de erro."""
    execution = await _persist_execution(db_session)

    response = await client.get(f"/v1/executions/{execution.id}/geojson")

    assert response.status_code == 200
    assert response.json()["features"] == []


# ---------------------------------------------------------------------------
# POST /v1/executions/{id}/cancel
# ---------------------------------------------------------------------------


async def test_cancel_pending_execution(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Execução pendente passa para `cancelled`."""
    execution = await _persist_execution(db_session, status=ExecutionStatus.QUEUED)

    response = await client.post(f"/v1/executions/{execution.id}/cancel")

    assert response.status_code == 204
    await db_session.refresh(execution)
    assert execution.status == ExecutionStatus.CANCELLED
    assert execution.finished_at is not None


async def test_cancel_is_idempotent_for_terminal_execution(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Cancelar execução já concluída não altera o resultado."""
    execution = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)

    response = await client.post(f"/v1/executions/{execution.id}/cancel")

    assert response.status_code == 204
    await db_session.refresh(execution)
    assert execution.status == ExecutionStatus.SUCCEEDED


# ---------------------------------------------------------------------------
# GET /v1/executions/{id}/stream (SSE)
# ---------------------------------------------------------------------------


async def test_stream_sends_current_state_and_closes_when_terminal(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Execução já finalizada envia o estado atual e encerra o fluxo (FR-03)."""
    execution = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)

    async with client.stream(
        "GET", f"/v1/executions/{execution.id}/stream"
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        payload = "".join([chunk async for chunk in response.aiter_text()])

    assert "succeeded" in payload
    assert str(execution.id) in payload


async def test_stream_relays_progress_events(
    client: AsyncClient, db_session: AsyncSession, fake_progress_bus
) -> None:
    """Eventos publicados pelo worker chegam ao cliente."""
    from src.api.schemas import ProgressEvent

    execution = await _persist_execution(db_session, status=ExecutionStatus.RUNNING)
    fake_progress_bus.events_to_emit = [
        ProgressEvent(
            execution_id=execution.id,
            status=ExecutionStatus.RUNNING,
            message="Consultando o Guia Local…",
            step="orquestracao",
            at=datetime.now(UTC),
        ),
        ProgressEvent(
            execution_id=execution.id,
            status=ExecutionStatus.SUCCEEDED,
            message="Roteiro concluído.",
            step="concluido",
            at=datetime.now(UTC),
        ),
    ]

    async with client.stream(
        "GET", f"/v1/executions/{execution.id}/stream"
    ) as response:
        payload = "".join([chunk async for chunk in response.aiter_text()])

    assert "Consultando o Guia Local" in payload
    assert "Roteiro concluído" in payload
