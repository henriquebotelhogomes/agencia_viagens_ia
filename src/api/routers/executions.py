"""Rotas de execução de roteiros (FR-02, FR-03, FR-04, FR-05, FR-07)."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from src.api.deps import (
    ClientIpHashDep,
    ProgressBusDep,
    RateLimiterDep,
    SessionDep,
    SettingsDep,
)
from src.api.errors import ExecutionNotFound, RateLimitExceeded, ServiceUnavailable
from src.api.schemas import (
    CostSummary,
    ExecutionCreated,
    ExecutionDetail,
    GeoJSONFeatureCollection,
    ProgressEvent,
    TripBriefing,
)
from src.db.models import Execution, ExecutionStatus, Itinerary, UsageRecord
from src.services.progress_bus import HEARTBEAT_SECONDS, ProgressBus
from src.services.queue_service import enqueue_generation

router = APIRouter(prefix="/v1/executions", tags=["executions"])

IdempotencyKeyHeader = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        description=(
            "Chave opcional para evitar execuções duplicadas: repetir a mesma "
            "chave retorna a execução original."
        ),
    ),
]


@router.post(
    "",
    response_model=ExecutionCreated,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cria uma execução de roteiro",
    responses={
        429: {"description": "Limite de execuções por hora excedido"},
        503: {"description": "Banco de dados ou fila indisponíveis"},
    },
)
async def create_execution(
    briefing: TripBriefing,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    rate_limiter: RateLimiterDep,
    client_ip_hash: ClientIpHashDep,
    idempotency_key: IdempotencyKeyHeader = None,
) -> ExecutionCreated:
    """Aceita um briefing e enfileira a geração do roteiro.

    Responde `202 Accepted` imediatamente — a geração leva 50-90s e roda no
    worker (ADR-0014). Acompanhe o progresso pelo endpoint SSE retornado.
    """
    if not settings.database_enabled:
        raise ServiceUnavailable("database")
    if not settings.cache_enabled:
        raise ServiceUnavailable("queue")

    # Idempotência: mesma chave devolve a execução original, sem novo custo
    if idempotency_key:
        existing = await session.scalar(
            select(Execution).where(Execution.idempotency_key == idempotency_key)
        )
        if existing is not None:
            return _created_response(existing, request)

    limit_result = await rate_limiter.check(client_ip_hash)
    if not limit_result.allowed:
        raise RateLimitExceeded(
            limit=limit_result.limit,
            retry_after_seconds=limit_result.retry_after_seconds,
        )

    execution = Execution(
        origem=briefing.origem,
        destino=briefing.destino,
        dias=briefing.dias,
        interesses=briefing.interesses,
        moeda=briefing.moeda,
        idioma=briefing.idioma,
        briefing_hash=briefing.fingerprint(),
        idempotency_key=idempotency_key,
        client_ip_hash=client_ip_hash,
        status=ExecutionStatus.QUEUED,
    )
    session.add(execution)
    await session.commit()
    await session.refresh(execution)

    await enqueue_generation(execution.id)
    return _created_response(execution, request)


@router.get(
    "/{execution_id}",
    response_model=ExecutionDetail,
    summary="Consulta o estado de uma execução",
    responses={404: {"description": "Execução não encontrada"}},
)
async def get_execution(
    execution_id: uuid.UUID, session: SessionDep
) -> ExecutionDetail:
    """Retorna estado, roteiro e custo real de uma execução."""
    execution = await _load_execution(session, execution_id)
    return await _to_detail(session, execution)


@router.get(
    "/{execution_id}/stream",
    summary="Acompanha o progresso em tempo real (SSE)",
    response_class=EventSourceResponse,
    responses={
        200: {
            "description": "Fluxo de eventos `text/event-stream`",
            "content": {"text/event-stream": {}},
        },
        404: {"description": "Execução não encontrada"},
    },
)
async def stream_execution(
    execution_id: uuid.UUID,
    session: SessionDep,
    progress_bus: ProgressBusDep,
) -> EventSourceResponse:
    """Transmite o progresso da execução via Server-Sent Events (FR-03).

    Envia o estado atual imediatamente e, se a execução já terminou, encerra o
    fluxo — assim um cliente que reconecta não fica pendurado.
    """
    execution = await _load_execution(session, execution_id)
    return EventSourceResponse(
        _event_generator(execution, progress_bus),
        ping=int(HEARTBEAT_SECONDS),
    )


@router.get(
    "/{execution_id}/geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Locais do roteiro em GeoJSON",
    responses={404: {"description": "Execução não encontrada"}},
)
async def get_execution_geojson(
    execution_id: uuid.UUID, session: SessionDep
) -> GeoJSONFeatureCollection:
    """Devolve os locais geocodificados para renderização no mapa (FR-05)."""
    execution = await _load_execution(session, execution_id)
    itinerary = await session.scalar(
        select(Itinerary).where(Itinerary.execution_id == execution.id)
    )
    if itinerary is None or not itinerary.locations_geojson:
        return GeoJSONFeatureCollection()
    payload: dict[str, Any] = dict(itinerary.locations_geojson)
    features = payload.get("features", [])
    return GeoJSONFeatureCollection(features=features)


@router.post(
    "/{execution_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancela uma execução pendente",
    responses={404: {"description": "Execução não encontrada"}},
)
async def cancel_execution(execution_id: uuid.UUID, session: SessionDep) -> Response:
    """Marca uma execução ainda não finalizada como cancelada.

    Execuções em estado terminal são ignoradas (idempotente).
    """
    execution = await _load_execution(session, execution_id)
    if not execution.is_terminal:
        execution.status = ExecutionStatus.CANCELLED
        execution.finished_at = datetime.now(UTC)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


async def _load_execution(session: AsyncSession, execution_id: uuid.UUID) -> Execution:
    execution = await session.get(Execution, execution_id)
    if execution is None:
        raise ExecutionNotFound(str(execution_id))
    return execution


def _created_response(execution: Execution, request: Request) -> ExecutionCreated:
    stream_path = request.url_for("stream_execution", execution_id=execution.id)
    return ExecutionCreated(
        id=execution.id,
        status=execution.status,
        stream_url=str(stream_path),
    )


async def _to_detail(session: AsyncSession, execution: Execution) -> ExecutionDetail:
    itinerary = await session.scalar(
        select(Itinerary).where(Itinerary.execution_id == execution.id)
    )
    usage = list(
        await session.scalars(
            select(UsageRecord).where(UsageRecord.execution_id == execution.id)
        )
    )
    return ExecutionDetail(
        id=execution.id,
        status=execution.status,
        briefing=TripBriefing(
            origem=execution.origem,
            destino=execution.destino,
            dias=execution.dias,
            interesses=execution.interesses,
            moeda=execution.moeda,  # type: ignore[arg-type]
            idioma=execution.idioma,  # type: ignore[arg-type]
        ),
        itinerary_markdown=itinerary.content_markdown if itinerary else None,
        error=execution.error_message,
        llm_gateway=execution.llm_gateway,
        used_fallback=execution.used_fallback,
        duration_seconds=execution.duration_seconds,
        cost=_summarize_cost(usage, execution.served_from_cache),
        created_at=execution.created_at,
        finished_at=execution.finished_at,
    )


def _summarize_cost(records: list[UsageRecord], served_from_cache: bool) -> CostSummary:
    """Agrega os registros de uso numa visão de custo (FR-07)."""
    prompt = sum(r.prompt_tokens for r in records)
    completion = sum(r.completion_tokens for r in records)
    cost = sum(r.cost_usd for r in records)
    baseline = sum(r.baseline_cost_usd for r in records)
    return CostSummary(
        total_tokens=prompt + completion,
        prompt_tokens=prompt,
        completion_tokens=completion,
        cost_usd=cost,
        baseline_cost_usd=baseline,
        savings_usd=baseline - cost,
        served_from_cache=served_from_cache,
    )


async def _event_generator(execution: Execution, progress_bus: ProgressBus) -> Any:
    """Produz os eventos SSE: estado atual e, depois, o fluxo do pub/sub."""
    current = ProgressEvent(
        execution_id=execution.id,
        status=execution.status,
        message=f"Estado atual: {execution.status.value}",
        at=datetime.now(UTC),
    )
    yield {"event": "progress", "data": current.model_dump_json()}

    if execution.is_terminal:
        return

    async for event in progress_bus.subscribe(execution.id):
        yield {"event": "progress", "data": event.model_dump_json()}
