"""Agregados de custo operacional (FinOps).

Responde à pergunta que um avaliador técnico faz sobre qualquer produto com LLM:
*quanto isso custa para rodar?* Os números são medidos — vêm dos tokens que o
provedor reportou em cada execução, não de estimativa.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import Float, case, cast, func, select

from src.api.deps import SessionDep
from src.api.schemas import FinOpsDailyPoint, FinOpsSummary
from src.db.models import Execution, ExecutionStatus, UsageRecord

router = APIRouter(prefix="/v1/finops", tags=["finops"])

# Janela máxima consultável — protege o banco de varreduras longas
MAX_WINDOW_DAYS = 90


@router.get(
    "",
    response_model=FinOpsSummary,
    summary="Custo operacional agregado",
)
async def finops_summary(
    session: SessionDep,
    days: int = Query(
        default=30,
        ge=1,
        le=MAX_WINDOW_DAYS,
        description="Janela de dias a considerar.",
    ),
) -> FinOpsSummary:
    """Agrega custo, tokens e eficiência de cache no período."""
    since = datetime.now(UTC) - timedelta(days=days)

    # `total_tokens` não é coluna: soma prompt + completion na própria query,
    # em vez de trazer as linhas e somar em Python.
    tokens_expr = UsageRecord.prompt_tokens + UsageRecord.completion_tokens

    totals = (
        await session.execute(
            select(
                func.count(UsageRecord.id),
                func.coalesce(func.sum(tokens_expr), 0),
                func.coalesce(func.sum(UsageRecord.cost_usd), 0.0),
                func.coalesce(func.sum(UsageRecord.baseline_cost_usd), 0.0),
            ).where(UsageRecord.created_at >= since)
        )
    ).one()

    usage_records, tokens, cost, baseline = totals

    status_rows = (
        await session.execute(
            select(Execution.status, func.count(Execution.id))
            .where(Execution.created_at >= since)
            .group_by(Execution.status)
        )
    ).all()
    by_status = {str(status.value): count for status, count in status_rows}

    # Cache hit ratio sai de `Execution`: a flag mora lá, não no registro de uso
    execution_stats = (
        await session.execute(
            select(
                func.count(Execution.id),
                func.coalesce(
                    func.sum(case((Execution.served_from_cache, 1), else_=0)), 0
                ),
            ).where(
                Execution.created_at >= since,
                Execution.status == ExecutionStatus.SUCCEEDED,
            )
        )
    ).one()
    succeeded, from_cache = execution_stats

    avg_duration = (
        await session.scalar(
            select(func.avg(cast(Execution.duration_seconds, Float))).where(
                Execution.created_at >= since,
                Execution.status == ExecutionStatus.SUCCEEDED,
            )
        )
        or 0.0
    )

    daily_rows = (
        await session.execute(
            select(
                func.date(UsageRecord.created_at),
                func.coalesce(func.sum(tokens_expr), 0),
                func.coalesce(func.sum(UsageRecord.cost_usd), 0.0),
                func.count(UsageRecord.id),
            )
            .where(UsageRecord.created_at >= since)
            .group_by(func.date(UsageRecord.created_at))
            .order_by(func.date(UsageRecord.created_at))
        )
    ).all()

    return FinOpsSummary(
        window_days=days,
        executions=usage_records,
        total_tokens=int(tokens),
        cost_usd=round(float(cost), 6),
        baseline_cost_usd=round(float(baseline), 6),
        savings_usd=round(float(baseline) - float(cost), 6),
        cache_hit_ratio=round(from_cache / succeeded, 4) if succeeded else 0.0,
        avg_duration_seconds=round(float(avg_duration), 1),
        by_status=by_status,
        daily=[
            FinOpsDailyPoint(
                date=str(day),
                total_tokens=int(day_tokens),
                cost_usd=round(float(day_cost), 6),
                executions=day_count,
            )
            for day, day_tokens, day_cost, day_count in daily_rows
        ],
    )
