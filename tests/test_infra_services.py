"""Testes dos serviços de infraestrutura da Fase 1.

Cobre o barramento de progresso, o rate limiter, a fila e a camada de banco —
todos com Redis/Postgres mockados: nenhum teste toca infraestrutura real.
"""

import uuid
from datetime import UTC, datetime

import pytest

from src.api.schemas import ProgressEvent
from src.config import Settings
from src.db import base as db_base
from src.db.models import ExecutionStatus
from src.services.progress_bus import ProgressBus, channel_for
from src.services.queue_service import (
    GENERATE_ITINERARY_TASK,
    build_queue,
    enqueue_generation,
)
from src.services.rate_limiter import (
    RateLimiter,
    hash_client_ip,
)


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def _event(execution_id: uuid.UUID, status: ExecutionStatus) -> ProgressEvent:
    return ProgressEvent(
        execution_id=execution_id,
        status=status,
        message="evento de teste",
        step="orquestracao",
        at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# ProgressBus
# ---------------------------------------------------------------------------


def test_channel_is_unique_per_execution() -> None:
    """Cada execução tem seu próprio canal — sem vazamento entre clientes."""
    a, b = uuid.uuid4(), uuid.uuid4()

    assert channel_for(a) != channel_for(b)
    assert str(a) in channel_for(a)


async def test_progress_bus_disabled_without_redis() -> None:
    """Sem Redis, publicar é no-op e assinar encerra de imediato."""
    bus = ProgressBus(_settings())

    assert bus.enabled is False
    await bus.publish(_event(uuid.uuid4(), ExecutionStatus.RUNNING))  # não levanta
    assert [e async for e in bus.subscribe(uuid.uuid4())] == []


async def test_progress_bus_publishes_to_execution_channel(mocker) -> None:
    """O evento é publicado no canal da própria execução."""
    client = mocker.AsyncMock()
    mocker.patch("src.services.progress_bus.aioredis.from_url", return_value=client)
    execution_id = uuid.uuid4()
    bus = ProgressBus(_settings(REDIS_URL="redis://localhost:6379/0"))

    await bus.publish(_event(execution_id, ExecutionStatus.RUNNING))

    channel, payload = client.publish.call_args[0]
    assert channel == channel_for(execution_id)
    assert str(execution_id) in payload


async def test_progress_bus_publish_survives_redis_failure(mocker) -> None:
    """Falha no Redis não interrompe o job em andamento."""
    client = mocker.AsyncMock()
    client.publish.side_effect = Exception("connection reset")
    mocker.patch("src.services.progress_bus.aioredis.from_url", return_value=client)
    bus = ProgressBus(_settings(REDIS_URL="redis://localhost:6379/0"))

    await bus.publish(_event(uuid.uuid4(), ExecutionStatus.RUNNING))  # não propaga


async def test_progress_bus_stops_on_terminal_event(mocker) -> None:
    """A assinatura encerra ao receber estado terminal — sem stream pendurado."""
    execution_id = uuid.uuid4()
    running = _event(execution_id, ExecutionStatus.RUNNING)
    done = _event(execution_id, ExecutionStatus.SUCCEEDED)

    pubsub = mocker.AsyncMock()
    pubsub.get_message.side_effect = [
        {"data": running.model_dump_json()},
        {"data": done.model_dump_json()},
    ]
    client = mocker.MagicMock()
    client.pubsub.return_value = pubsub
    mocker.patch("src.services.progress_bus.aioredis.from_url", return_value=client)
    bus = ProgressBus(_settings(REDIS_URL="redis://localhost:6379/0"))

    events = [e async for e in bus.subscribe(execution_id)]

    assert [e.status for e in events] == [
        ExecutionStatus.RUNNING,
        ExecutionStatus.SUCCEEDED,
    ]


async def test_progress_bus_discards_invalid_payload(mocker) -> None:
    """Mensagem malformada é descartada sem derrubar o stream."""
    execution_id = uuid.uuid4()
    done = _event(execution_id, ExecutionStatus.SUCCEEDED)

    pubsub = mocker.AsyncMock()
    pubsub.get_message.side_effect = [
        {"data": "isso não é json"},
        {"data": done.model_dump_json()},
    ]
    client = mocker.MagicMock()
    client.pubsub.return_value = pubsub
    mocker.patch("src.services.progress_bus.aioredis.from_url", return_value=client)
    bus = ProgressBus(_settings(REDIS_URL="redis://localhost:6379/0"))

    events = [e async for e in bus.subscribe(execution_id)]

    assert len(events) == 1
    assert events[0].status == ExecutionStatus.SUCCEEDED


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------


def test_hash_client_ip_is_deterministic_and_opaque() -> None:
    """O IP nunca aparece em claro; o hash é estável."""
    ip = "203.0.113.42"

    digest = hash_client_ip(ip)

    assert digest == hash_client_ip(ip)
    assert ip not in digest
    assert len(digest) == 64


async def test_rate_limiter_allows_without_redis() -> None:
    """Sem Redis, o limiter é fail-open (documentado no ADR-0004)."""
    limiter = RateLimiter(_settings())

    result = await limiter.check("hash")

    assert result.allowed is True
    assert limiter.enabled is False


async def test_rate_limiter_allows_within_quota(mocker) -> None:
    """Dentro da cota, permite e informa o saldo restante."""
    _redis_with_pipeline(mocker, count=2, ttl=1800)
    limiter = RateLimiter(
        _settings(
            REDIS_URL="redis://localhost:6379/0", RATE_LIMIT_EXECUTIONS_PER_HOUR=5
        )
    )

    result = await limiter.check("hash")

    assert result.allowed is True
    assert result.remaining == 3
    assert result.limit == 5


async def test_rate_limiter_blocks_above_quota(mocker) -> None:
    """Acima da cota, bloqueia e informa quando tentar de novo."""
    client = _redis_with_pipeline(mocker, count=6, ttl=1200)
    limiter = RateLimiter(
        _settings(
            REDIS_URL="redis://localhost:6379/0", RATE_LIMIT_EXECUTIONS_PER_HOUR=5
        )
    )

    result = await limiter.check("hash")

    assert result.allowed is False
    assert result.remaining == 0
    assert result.retry_after_seconds == 1200
    client.expire.assert_not_called()


async def test_rate_limiter_sets_ttl_on_first_request(mocker) -> None:
    """A primeira requisição da janela define a expiração da chave."""
    client = _redis_with_pipeline(mocker, count=1, ttl=-1)
    limiter = RateLimiter(_settings(REDIS_URL="redis://localhost:6379/0"))

    await limiter.check("hash")

    client.expire.assert_awaited_once()


async def test_rate_limiter_fails_open_on_redis_error(mocker) -> None:
    """Erro no Redis permite a requisição em vez de derrubar a API."""
    client = mocker.MagicMock()
    client.pipeline.side_effect = Exception("redis down")
    mocker.patch("src.services.rate_limiter.aioredis.from_url", return_value=client)
    limiter = RateLimiter(_settings(REDIS_URL="redis://localhost:6379/0"))

    result = await limiter.check("hash")

    assert result.allowed is True


def _redis_with_pipeline(mocker, *, count: int, ttl: int):
    """Cliente Redis fake cujo pipeline devolve ``(count, ttl)``."""
    pipeline = mocker.AsyncMock()
    pipeline.execute.return_value = [count, ttl]
    pipeline.__aenter__.return_value = pipeline
    pipeline.__aexit__.return_value = None

    client = mocker.AsyncMock()
    client.pipeline = mocker.MagicMock(return_value=pipeline)
    mocker.patch("src.services.rate_limiter.aioredis.from_url", return_value=client)
    return client


# ---------------------------------------------------------------------------
# Fila (SAQ)
# ---------------------------------------------------------------------------


def test_build_queue_requires_redis() -> None:
    """Sem Redis, a fila falha explicitamente em vez de silenciar."""
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        build_queue(_settings())


async def test_enqueue_generation_sends_task_with_timeout(mocker) -> None:
    """O job é enfileirado com o identificador da execução e timeout."""
    job = mocker.MagicMock(key="job-123")
    queue = mocker.AsyncMock()
    queue.enqueue.return_value = job
    execution_id = uuid.uuid4()

    key = await enqueue_generation(execution_id, queue=queue)

    assert key == "job-123"
    task_name, kwargs = queue.enqueue.call_args[0][0], queue.enqueue.call_args[1]
    assert task_name == GENERATE_ITINERARY_TASK
    assert kwargs["execution_id"] == str(execution_id)
    assert kwargs["timeout"] > 0


# ---------------------------------------------------------------------------
# Camada de banco
# ---------------------------------------------------------------------------


def test_build_engine_requires_database_url() -> None:
    """Sem DATABASE_URL, o erro é explícito (não uma falha obscura depois)."""
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db_base.build_engine(_settings())


def test_build_engine_accepts_injected_settings() -> None:
    """A configuração pode ser injetada — essencial para testes.

    Regressão: com `lru_cache` na função que recebia `Settings`, isso levantava
    ``TypeError: unhashable type: 'Settings'``.
    """
    engine = db_base.build_engine(
        _settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
    )

    assert engine.url.drivername == "sqlite+aiosqlite"


def test_get_engine_is_memoized(mocker) -> None:
    """O engine do processo é criado uma única vez."""
    db_base.get_engine.cache_clear()
    mocker.patch(
        "src.db.base.get_settings",
        return_value=_settings(DATABASE_URL="sqlite+aiosqlite:///:memory:"),
    )

    first = db_base.get_engine()
    second = db_base.get_engine()

    assert first is second
    db_base.get_engine.cache_clear()


async def test_dispose_engine_clears_caches(mocker) -> None:
    """O shutdown libera o pool e limpa a memoização."""
    db_base.get_engine.cache_clear()
    mocker.patch(
        "src.db.base.get_settings",
        return_value=_settings(DATABASE_URL="sqlite+aiosqlite:///:memory:"),
    )
    db_base.get_engine()

    await db_base.dispose_engine()

    assert db_base.get_engine.cache_info().currsize == 0
