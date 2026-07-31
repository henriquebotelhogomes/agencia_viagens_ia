"""Job de geração de roteiro executado pelo worker (ADR-0014).

Este módulo é o único lugar onde a orquestração CrewAI encontra a persistência.
A API nunca executa a crew; o worker nunca conhece HTTP.
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import select

from src.api.schemas import ProgressEvent
from src.config import get_settings
from src.crew_builder import CrewBuilder
from src.db.base import get_session_factory
from src.db.models import Execution, ExecutionStatus, Itinerary, UsageRecord
from src.services.cache_service import get_cache_service
from src.services.finance_service import FinanceService
from src.services.geocoding_service import GeocodingService
from src.services.progress_bus import ProgressBus
from src.telemetry import get_tracer

# Etapas reportadas ao cliente durante a execução
STEP_CACHE = "cache"
STEP_ORCHESTRATION = "orquestracao"
STEP_GEOCODING = "geocoding"
STEP_DONE = "concluido"


async def generate_itinerary(
    ctx: dict[str, Any],  # noqa: ARG001 - contexto injetado pelo SAQ
    *,
    execution_id: str,
) -> str:
    """Gera o roteiro de uma execução persistida.

    Fluxo: cache → orquestração dos agentes → geocoding → custo real.
    Qualquer falha marca a execução como `failed` e é reportada ao cliente.

    Args:
        ctx: contexto do worker (injetado pelo SAQ).
        execution_id: identificador da execução a processar.

    Returns:
        Status final da execução.
    """
    settings = get_settings()
    exec_uuid = uuid.UUID(execution_id)
    progress = ProgressBus(settings)
    session_factory = get_session_factory()

    # Span raiz do job: liga a execução assíncrona ao trace de infraestrutura.
    # Sem backend OTLP configurado é um no-op (tracer default não grava nada).
    with get_tracer("voyager.worker").start_as_current_span(
        "generate_itinerary",
        attributes={"voyager.execution_id": execution_id},
    ) as span:
        status = await _run_job(exec_uuid, progress, session_factory)
        span.set_attribute("voyager.execution_status", status)
        return status


async def _run_job(
    exec_uuid: uuid.UUID,
    progress: ProgressBus,
    session_factory: Any,
) -> str:
    """Corpo do job, separado para o span raiz envolver o fluxo inteiro."""
    execution_id = str(exec_uuid)
    async with session_factory() as session:
        execution = await session.get(Execution, exec_uuid)
        if execution is None:
            logger.error(f"Execução {execution_id} não encontrada; job descartado.")
            return ExecutionStatus.FAILED.value

        if execution.status == ExecutionStatus.CANCELLED:
            logger.info(f"Execução {execution_id} já cancelada; job ignorado.")
            return ExecutionStatus.CANCELLED.value

        started = time.perf_counter()
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(UTC)
        await session.commit()
        await _publish(progress, execution, "Execução iniciada.", STEP_ORCHESTRATION)

        try:
            markdown, token_usage, used_fallback, from_cache = await _produce_itinerary(
                execution, progress
            )

            await _publish(
                progress, execution, "Geolocalizando pontos do roteiro…", STEP_GEOCODING
            )
            geojson = await _build_geojson(markdown)

            session.add(
                Itinerary(
                    execution_id=execution.id,
                    content_markdown=markdown,
                    locations_geojson=geojson,
                )
            )
            _record_usage(session, execution, token_usage, from_cache)

            execution.status = ExecutionStatus.SUCCEEDED
            execution.served_from_cache = from_cache
            execution.used_fallback = used_fallback
            execution.llm_gateway = "openrouter" if used_fallback else "opencode_go"
            execution.duration_seconds = round(time.perf_counter() - started, 2)
            execution.finished_at = datetime.now(UTC)
            await session.commit()

            await _publish(progress, execution, "Roteiro concluído.", STEP_DONE)
            logger.info(
                f"Execução {execution_id} concluída em "
                f"{execution.duration_seconds}s (cache={from_cache})."
            )
            return ExecutionStatus.SUCCEEDED.value

        except Exception as e:
            # `exception=True` inclui o stack trace: sem ele, só se sabe *que*
            # falhou, não *onde* — diagnosticar em produção fica impossível.
            # `diagnose=False` (configurado no logger) mantém valores de
            # variáveis fora do log, então nenhum segredo vaza.
            logger.opt(exception=True).error(f"Execução {execution_id} falhou: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)[:2000]
            execution.duration_seconds = round(time.perf_counter() - started, 2)
            execution.finished_at = datetime.now(UTC)
            await session.commit()
            await _publish(progress, execution, f"Falha na geração: {e}", STEP_DONE)
            return ExecutionStatus.FAILED.value
        finally:
            await progress.close()


async def _produce_itinerary(
    execution: Execution, progress: ProgressBus
) -> tuple[str, Any, bool, bool]:
    """Obtém o roteiro do cache ou executa a crew.

    Returns:
        Tupla ``(markdown, token_usage, used_fallback, served_from_cache)``.
    """
    cache = get_cache_service()
    cached = cache.get_cached_itinerary(
        execution.origem,
        execution.destino,
        execution.dias,
        execution.interesses,
        moeda=execution.moeda,
        idioma=execution.idioma,
    )
    if cached:
        await _publish(progress, execution, "Roteiro recuperado do cache.", STEP_CACHE)
        return cached, None, False, True

    builder = CrewBuilder(
        destino=execution.destino,
        dias=execution.dias,
        origem=execution.origem,
        interesses=execution.interesses,
        moeda=execution.moeda,
        idioma=execution.idioma,
    )
    # CrewAI é síncrono; roda no executor default para não bloquear o loop
    result = await asyncio.to_thread(builder.run)
    markdown = str(result)
    cache.save_itinerary(
        execution.origem,
        execution.destino,
        execution.dias,
        execution.interesses,
        markdown,
        moeda=execution.moeda,
        idioma=execution.idioma,
    )
    return markdown, getattr(result, "token_usage", None), builder.use_fallback, False


async def _build_geojson(markdown: str) -> dict[str, Any] | None:
    """Extrai e geocodifica os locais do roteiro, no formato GeoJSON (FR-05)."""
    service = GeocodingService(cache=get_cache_service())
    locations = await asyncio.to_thread(service.process_itinerary_locations, markdown)
    if not locations:
        return None
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [loc.lon, loc.lat]},
                "properties": {"name": loc.name, "type": loc.type},
            }
            for loc in locations
            if loc.lat is not None and loc.lon is not None
        ],
    }


def _record_usage(
    session: Any, execution: Execution, token_usage: Any, from_cache: bool
) -> None:
    """Persiste o consumo real de tokens (item S4 do PRD)."""
    if from_cache or token_usage is None:
        return

    prompt_tokens = int(getattr(token_usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(token_usage, "completion_tokens", 0) or 0)
    if not prompt_tokens and not completion_tokens:
        return

    stats = FinanceService().estimate_costs_from_usage(
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
    )
    settings = get_settings()
    session.add(
        UsageRecord(
            execution_id=execution.id,
            model=settings.LLM_MODEL_FAST,
            gateway="openrouter" if execution.used_fallback else "opencode_go",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=stats["custo_groq"],
            baseline_cost_usd=stats["custo_gpt4o"],
        )
    )


async def _publish(
    progress: ProgressBus, execution: Execution, message: str, step: str
) -> None:
    """Publica um evento de progresso para o cliente conectado ao SSE."""
    await progress.publish(
        ProgressEvent(
            execution_id=execution.id,
            status=execution.status,
            message=message,
            step=step,
            at=datetime.now(UTC),
        )
    )


async def find_stale_executions() -> list[uuid.UUID]:
    """Lista execuções presas em `running` (diagnóstico operacional)."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = await session.scalars(
            select(Execution.id).where(Execution.status == ExecutionStatus.RUNNING)
        )
        return list(rows)
