"""Telemetria de infraestrutura com OpenTelemetry (NFR de observabilidade).

Divisão de responsabilidades com o Langfuse (ADR-0012):

- **Langfuse**: traces das chamadas de LLM (prompts, tokens, custo por agente).
- **OpenTelemetry**: o resto do sistema — latência das rotas HTTP, queries do
  SQLAlchemy, comandos Redis e o ciclo de vida dos jobs do worker.

Segue as mesmas invariantes do runtime (item S1 do PRD): nada acontece no
import; os entrypoints chamam :func:`configure_telemetry` explicitamente. Sem
``OTEL_EXPORTER_OTLP_ENDPOINT`` configurado, a função é um no-op — zero
overhead e zero dependência de backend em dev.
"""

from typing import TYPE_CHECKING, Any

from loguru import logger

from src.config import Settings, get_settings

if TYPE_CHECKING:  # pragma: no cover - só para tipos
    from fastapi import FastAPI

_configured = False


def configure_telemetry(
    settings: Settings | None = None,
    *,
    service_name: str | None = None,
    app: "FastAPI | None" = None,
) -> bool:
    """Ativa traces OTLP para o processo atual (idempotente).

    Args:
        settings: configuração a usar (injeta em testes).
        service_name: identifica o processo no backend (``voyager-api`` /
            ``voyager-worker``); usa ``OTEL_SERVICE_NAME`` se omitido.
        app: aplicação FastAPI a instrumentar (apenas no processo web).

    Returns:
        ``True`` se a telemetria foi ativada nesta chamada.
    """
    global _configured

    resolved = settings or get_settings()
    if not resolved.telemetry_enabled:
        logger.debug("OpenTelemetry desligado (OTEL_EXPORTER_OTLP_ENDPOINT vazio).")
        return False
    if _configured:
        # Instrumentar duas vezes duplicaria spans; só o FastAPI pode ser
        # adicionado depois (processo web cria o app após o runtime).
        if app is not None:
            _instrument_fastapi(app)
        return False

    # Imports locais: o SDK só entra em memória quando a telemetria está ativa
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": service_name or resolved.OTEL_SERVICE_NAME,
            "deployment.environment": resolved.APP_ENV,
        }
    )
    headers = _parse_headers(resolved.OTEL_EXPORTER_OTLP_HEADERS.get_secret_value())
    exporter = OTLPSpanExporter(
        endpoint=f"{resolved.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip('/')}/v1/traces",
        headers=headers or None,
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _instrument_sqlalchemy()
    _instrument_redis()
    if app is not None:
        _instrument_fastapi(app)

    _configured = True
    logger.info(
        f"OpenTelemetry ativo (service={resource.attributes['service.name']}, "
        f"endpoint={resolved.OTEL_EXPORTER_OTLP_ENDPOINT})"
    )
    return True


def _parse_headers(raw: str) -> dict[str, str]:
    """Converte ``chave1=valor1,chave2=valor2`` (formato padrão OTel) em dict."""
    headers: dict[str, str] = {}
    for pair in raw.split(","):
        key, sep, value = pair.partition("=")
        if sep and key.strip():
            headers[key.strip()] = value.strip()
    return headers


def _instrument_fastapi(app: "FastAPI") -> None:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    if not getattr(app.state, "otel_instrumented", False):
        FastAPIInstrumentor.instrument_app(app)
        app.state.otel_instrumented = True


def _instrument_sqlalchemy() -> None:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(enable_commenter=False)


def _instrument_redis() -> None:
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    RedisInstrumentor().instrument()


def get_tracer(name: str) -> Any:
    """Tracer para spans manuais (ex.: etapas do job no worker)."""
    from opentelemetry import trace

    return trace.get_tracer(name)


def reset_telemetry_state() -> None:
    """Reseta o guard de idempotência (uso exclusivo em testes)."""
    global _configured
    _configured = False
