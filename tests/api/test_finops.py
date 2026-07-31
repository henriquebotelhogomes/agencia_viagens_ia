"""Testes do endpoint de FinOps (agregação de custo)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Execution, ExecutionStatus, UsageRecord


async def _seed(
    session: AsyncSession,
    *,
    status: ExecutionStatus = ExecutionStatus.SUCCEEDED,
    from_cache: bool = False,
    prompt: int = 1000,
    completion: int = 500,
    cost: float = 0.01,
    baseline: float = 0.2,
    duration: float = 90.0,
    age_days: int = 0,
) -> Execution:
    """Cria uma execução com registro de uso, no passado se preciso."""
    created = datetime.now(UTC) - timedelta(days=age_days)
    execution = Execution(
        origem="São Paulo",
        destino="Lisboa",
        dias=3,
        interesses="gastronomia",
        moeda="EUR",
        idioma="pt-BR",
        briefing_hash=uuid.uuid4().hex,
        status=status,
        served_from_cache=from_cache,
        duration_seconds=duration,
        created_at=created,
    )
    session.add(execution)
    await session.flush()

    session.add(
        UsageRecord(
            execution_id=execution.id,
            model="test-model",
            gateway="opencode_go",
            prompt_tokens=prompt,
            completion_tokens=completion,
            cost_usd=cost,
            baseline_cost_usd=baseline,
            created_at=created,
        )
    )
    await session.commit()
    return execution


async def test_sem_dados_retorna_zeros(client: AsyncClient) -> None:
    """Painel novo não deve quebrar nem dividir por zero."""
    response = await client.get("/v1/finops")

    assert response.status_code == 200
    body = response.json()
    assert body["executions"] == 0
    assert body["total_tokens"] == 0
    assert body["cache_hit_ratio"] == 0.0
    assert body["daily"] == []


async def test_agrega_tokens_e_custo(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, prompt=1000, completion=500, cost=0.01, baseline=0.2)
    await _seed(db_session, prompt=2000, completion=1000, cost=0.02, baseline=0.4)

    body = (await client.get("/v1/finops")).json()

    assert body["executions"] == 2
    # total_tokens é derivado: prompt + completion de cada registro
    assert body["total_tokens"] == 4500
    assert body["cost_usd"] == 0.03
    assert body["baseline_cost_usd"] == 0.6
    assert body["savings_usd"] == 0.57


async def test_cache_hit_ratio(client: AsyncClient, db_session: AsyncSession) -> None:
    """Proporção calculada sobre execuções bem-sucedidas."""
    await _seed(db_session, from_cache=True)
    await _seed(db_session, from_cache=False)
    await _seed(db_session, from_cache=False)

    body = (await client.get("/v1/finops")).json()

    assert body["cache_hit_ratio"] == 0.3333


async def test_conta_por_estado(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed(db_session, status=ExecutionStatus.SUCCEEDED)
    await _seed(db_session, status=ExecutionStatus.FAILED)
    await _seed(db_session, status=ExecutionStatus.FAILED)

    body = (await client.get("/v1/finops")).json()

    assert body["by_status"] == {"succeeded": 1, "failed": 2}


async def test_duracao_media_ignora_execucoes_falhas(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Uma falha em 1s não pode puxar a média para baixo."""
    await _seed(db_session, status=ExecutionStatus.SUCCEEDED, duration=100.0)
    await _seed(db_session, status=ExecutionStatus.FAILED, duration=1.0)

    body = (await client.get("/v1/finops")).json()

    assert body["avg_duration_seconds"] == 100.0


async def test_janela_exclui_dados_antigos(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, age_days=0, prompt=100, completion=100)
    await _seed(db_session, age_days=10, prompt=900, completion=900)

    recente = (await client.get("/v1/finops", params={"days": 5})).json()
    completo = (await client.get("/v1/finops", params={"days": 30})).json()

    assert recente["total_tokens"] == 200
    assert completo["total_tokens"] == 2000


async def test_serie_diaria_agrupa_por_data(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, age_days=0, prompt=100, completion=0)
    await _seed(db_session, age_days=0, prompt=200, completion=0)
    await _seed(db_session, age_days=1, prompt=50, completion=0)

    body = (await client.get("/v1/finops")).json()

    assert len(body["daily"]) == 2
    # Ordenado do mais antigo para o mais novo
    assert body["daily"][0]["total_tokens"] == 50
    assert body["daily"][1]["total_tokens"] == 300
    assert body["daily"][1]["executions"] == 2


async def test_janela_maxima_e_validada(client: AsyncClient) -> None:
    """Janela absurda seria varredura completa da tabela."""
    response = await client.get("/v1/finops", params={"days": 5000})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
