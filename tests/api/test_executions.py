"""Testes das rotas de execução (FR-02, FR-04, FR-05, FR-09, FR-40, FR-41)."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import PROBLEM_CONTENT_TYPE
from src.db.models import (
    Execution,
    ExecutionKind,
    ExecutionStatus,
    Itinerary,
    UsageRecord,
)

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


# ---------------------------------------------------------------------------
# POST /v1/executions/{id}/refine (FR-40)
# ---------------------------------------------------------------------------


async def test_refine_creates_child_execution(
    client: AsyncClient, db_session: AsyncSession, mocker
) -> None:
    """Refine cria execução filha com kind=refine e enfileira."""
    spy = mocker.patch("src.api.routers.executions.enqueue_generation")
    parent = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(Itinerary(execution_id=parent.id, content_markdown="# Roteiro"))
    await db_session.commit()

    response = await client.post(
        f"/v1/executions/{parent.id}/refine",
        json={"instruction": "Inclua mais museus"},
    )

    assert response.status_code == 202
    body = response.json()
    child_id = uuid.UUID(body["id"])
    assert child_id != parent.id
    spy.assert_awaited_once()

    child = await db_session.get(Execution, child_id)
    assert child is not None
    assert child.kind == ExecutionKind.REFINE
    assert child.parent_execution_id == parent.id
    assert child.root_execution_id == parent.id
    assert child.refine_instruction == "Inclua mais museus"
    assert child.status == ExecutionStatus.QUEUED


async def test_refine_returns_409_when_parent_not_succeeded(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Refine de execução não concluída retorna 409."""
    parent = await _persist_execution(db_session, status=ExecutionStatus.RUNNING)

    response = await client.post(
        f"/v1/executions/{parent.id}/refine",
        json={"instruction": "mude algo"},
    )

    assert response.status_code == 409
    assert response.json()["type"].endswith("execution-not-succeeded")


async def test_refine_returns_409_when_no_itinerary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Refine de execução sem roteiro retorna 409."""
    parent = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)

    response = await client.post(
        f"/v1/executions/{parent.id}/refine",
        json={"instruction": "mude algo"},
    )

    assert response.status_code == 409
    assert response.json()["type"].endswith("no-itinerary")


async def test_refine_returns_404_for_unknown_execution(
    client: AsyncClient,
) -> None:
    """Refine de execução inexistente retorna 404."""
    response = await client.post(
        f"/v1/executions/{uuid.uuid4()}/refine",
        json={"instruction": "teste"},
    )

    assert response.status_code == 404


async def test_refine_returns_422_for_empty_instruction(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Instrução vazia retorna 422."""
    parent = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(Itinerary(execution_id=parent.id, content_markdown="# Roteiro"))
    await db_session.commit()

    response = await client.post(
        f"/v1/executions/{parent.id}/refine",
        json={"instruction": ""},
    )

    assert response.status_code == 422


async def test_refine_returns_429_when_rate_limited(
    client: AsyncClient, db_session: AsyncSession, fake_rate_limiter
) -> None:
    """Refine consome cota do rate limit."""
    fake_rate_limiter.allowed = False
    parent = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(Itinerary(execution_id=parent.id, content_markdown="# Roteiro"))
    await db_session.commit()

    response = await client.post(
        f"/v1/executions/{parent.id}/refine",
        json={"instruction": "mude algo"},
    )

    assert response.status_code == 429


# ---------------------------------------------------------------------------
# POST /v1/executions/{id}/rollback (FR-41)
# ---------------------------------------------------------------------------


async def test_rollback_creates_child_execution(
    client: AsyncClient, db_session: AsyncSession, mocker
) -> None:
    """Rollback cria execução filha com kind=rollback."""
    spy = mocker.patch("src.api.routers.executions.enqueue_generation")
    root = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(
        Itinerary(execution_id=root.id, content_markdown="# Versão 1", version=1)
    )
    await db_session.commit()

    response = await client.post(
        f"/v1/executions/{root.id}/rollback",
        json={"target_execution_id": str(root.id)},
    )

    assert response.status_code == 202
    body = response.json()
    child_id = uuid.UUID(body["id"])
    spy.assert_awaited_once()

    child = await db_session.get(Execution, child_id)
    assert child is not None
    assert child.kind == ExecutionKind.ROLLBACK
    assert child.parent_execution_id == root.id
    assert child.root_execution_id == root.id
    assert "Restaurada a versão 1" in (child.refine_instruction or "")


async def test_rollback_returns_409_when_target_has_no_itinerary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rollback para alvo sem roteiro retorna 409."""
    current = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    target = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)

    response = await client.post(
        f"/v1/executions/{current.id}/rollback",
        json={"target_execution_id": str(target.id)},
    )

    assert response.status_code == 409
    assert response.json()["type"].endswith("no-itinerary")


async def test_rollback_returns_404_for_unknown_target(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rollback com alvo inexistente retorna 404."""
    current = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)

    response = await client.post(
        f"/v1/executions/{current.id}/rollback",
        json={"target_execution_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/executions/{id}/versions (FR-41)
# ---------------------------------------------------------------------------


async def test_versions_lists_lineage_ordered(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Lista as versões da linhagem ordenadas por número."""
    root = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(
        Itinerary(execution_id=root.id, content_markdown="# V1", version=1)
    )
    child = await _persist_execution(
        db_session,
        status=ExecutionStatus.SUCCEEDED,
        kind=ExecutionKind.REFINE,
        parent_execution_id=root.id,
        root_execution_id=root.id,
        refine_instruction="mais museus",
    )
    db_session.add(
        Itinerary(execution_id=child.id, content_markdown="# V2", version=2)
    )
    await db_session.commit()

    response = await client.get(f"/v1/executions/{child.id}/versions")

    assert response.status_code == 200
    body = response.json()
    assert body["root_execution_id"] == str(root.id)
    assert body["current_version"] == 2
    assert len(body["versions"]) == 2
    assert body["versions"][0]["version"] == 1
    assert body["versions"][0]["kind"] == "initial"
    assert body["versions"][1]["version"] == 2
    assert body["versions"][1]["kind"] == "refine"


async def test_versions_returns_404_for_unknown_execution(
    client: AsyncClient,
) -> None:
    """Versions de execução inexistente retorna 404."""
    response = await client.get(f"/v1/executions/{uuid.uuid4()}/versions")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/executions/{id} — campos de linhagem
# ---------------------------------------------------------------------------


async def test_get_execution_includes_lineage_fields(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Detalhe inclui kind, version e IDs de linhagem."""
    root = await _persist_execution(db_session, status=ExecutionStatus.SUCCEEDED)
    db_session.add(
        Itinerary(execution_id=root.id, content_markdown="# Roteiro", version=1)
    )
    child = await _persist_execution(
        db_session,
        status=ExecutionStatus.SUCCEEDED,
        kind=ExecutionKind.REFINE,
        parent_execution_id=root.id,
        root_execution_id=root.id,
        refine_instruction="Inclua museus",
    )
    db_session.add(
        Itinerary(execution_id=child.id, content_markdown="# V2", version=2)
    )
    await db_session.commit()

    response = await client.get(f"/v1/executions/{child.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "refine"
    assert body["version"] == 2
    assert body["parent_execution_id"] == str(root.id)
    assert body["root_execution_id"] == str(root.id)
    assert body["refine_instruction"] == "Inclua museus"
