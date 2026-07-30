"""Testes da telemetria OpenTelemetry (src/telemetry.py).

O contrato central: sem endpoint configurado, **nada** é instrumentado nem
importado do SDK; com endpoint, provider e instrumentações são ativados uma
única vez por processo.
"""

import pytest

from src import telemetry
from src.config import Settings
from src.telemetry import (
    _parse_headers,
    configure_telemetry,
    get_tracer,
    reset_telemetry_state,
)


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def _reset_guard():
    reset_telemetry_state()
    yield
    reset_telemetry_state()


# ---------------------------------------------------------------------------
# Degradação graciosa
# ---------------------------------------------------------------------------
def test_sem_endpoint_e_noop(mocker) -> None:
    """Sem OTEL_EXPORTER_OTLP_ENDPOINT, nada é instrumentado."""
    instrument = mocker.patch("src.telemetry._instrument_sqlalchemy")

    activated = configure_telemetry(_settings())

    assert activated is False
    instrument.assert_not_called()


def test_telemetry_enabled_reflete_o_endpoint() -> None:
    assert _settings().telemetry_enabled is False
    assert (
        _settings(
            OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com"
        ).telemetry_enabled
        is True
    )


# ---------------------------------------------------------------------------
# Ativação
# ---------------------------------------------------------------------------
@pytest.fixture
def instrumented(mocker) -> dict[str, object]:
    """Mocka as instrumentações e o exporter (nenhuma conexão real)."""
    return {
        "sqlalchemy": mocker.patch("src.telemetry._instrument_sqlalchemy"),
        "redis": mocker.patch("src.telemetry._instrument_redis"),
        "fastapi": mocker.patch("src.telemetry._instrument_fastapi"),
        "exporter": mocker.patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
            autospec=True,
        ),
    }


def test_ativa_com_endpoint(instrumented) -> None:
    settings = _settings(OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com")

    activated = configure_telemetry(settings, service_name="voyager-test")

    assert activated is True
    instrumented["sqlalchemy"].assert_called_once()
    instrumented["redis"].assert_called_once()
    # Sem app, o FastAPI não é instrumentado
    instrumented["fastapi"].assert_not_called()


def test_segunda_chamada_nao_reinstrumenta(instrumented) -> None:
    """Instrumentar duas vezes duplicaria spans."""
    settings = _settings(OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com")

    assert configure_telemetry(settings) is True
    assert configure_telemetry(settings) is False
    instrumented["sqlalchemy"].assert_called_once()


def test_app_pode_ser_instrumentado_depois_do_runtime(instrumented, mocker) -> None:
    """O worker configura primeiro; o app da API chega depois no mesmo processo."""
    settings = _settings(OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com")
    app = mocker.MagicMock()

    configure_telemetry(settings)
    configure_telemetry(settings, app=app)

    instrumented["fastapi"].assert_called_once_with(app)


def test_endpoint_recebe_o_caminho_de_traces(instrumented) -> None:
    """O exporter deve apontar para /v1/traces, sem barras duplicadas."""
    settings = _settings(OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com/")

    configure_telemetry(settings)

    _, kwargs = instrumented["exporter"].call_args
    assert kwargs["endpoint"] == "https://otlp.example.com/v1/traces"


def test_headers_de_autenticacao_chegam_ao_exporter(instrumented) -> None:
    settings = _settings(
        OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.example.com",
        OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer abc123",
    )

    configure_telemetry(settings)

    _, kwargs = instrumented["exporter"].call_args
    assert kwargs["headers"] == {"Authorization": "Bearer abc123"}


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", {}),
        ("Authorization=Bearer tok", {"Authorization": "Bearer tok"}),
        ("a=1,b=2", {"a": "1", "b": "2"}),
        (" a = 1 , b = 2 ", {"a": "1", "b": "2"}),
        ("semseparador", {}),
    ],
)
def test_parse_headers(raw: str, expected: dict[str, str]) -> None:
    assert _parse_headers(raw) == expected


def test_get_tracer_e_noop_sem_provider() -> None:
    """Sem provider configurado, o span existe mas não grava nada."""
    tracer = get_tracer("teste")

    with tracer.start_as_current_span("span-de-teste") as span:
        span.set_attribute("chave", "valor")

    # Nenhuma exceção: o tracer default do OTel é um no-op seguro


def test_import_do_modulo_nao_tem_efeito_colateral() -> None:
    """Invariante S1: importar src.telemetry não configura nada."""
    assert telemetry._configured is False
