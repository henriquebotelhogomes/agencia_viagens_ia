"""Testes do runtime explícito e da ausência de efeitos colaterais de import."""

import os
import subprocess
import sys

from src.config import Settings
from src.runtime import (
    _export_provider_env,
    _purge_unreachable_redis,
    configure_llm_runtime,
    reset_runtime_state,
)


def test_import_of_domain_modules_has_no_side_effects() -> None:
    """Importar o domínio não deve mutar ``os.environ`` (item S1 do PRD).

    Executa num subprocesso limpo para não sofrer influência do ambiente atual.

    Exceção tolerada: o **CrewAI** chama ``load_dotenv()`` no próprio import
    (efeito de terceiro, fora do nosso controle), então chaves vindas do `.env`
    local são permitidas — qualquer outra chave nova, ou alteração de valor
    pré-existente, continua reprovando.
    """
    script = (
        "import os;"
        "from dotenv import dotenv_values;"
        "allowed = set(dotenv_values('.env').keys());"
        "before = dict(os.environ);"
        "import src.agents, src.crew_builder, src.services.cache_service,"
        " src.services.geocoding_service;"
        "after = dict(os.environ);"
        "unexpected = set(after) - set(before) - allowed;"
        "changed = {k for k in before if after.get(k) != before[k]};"
        "assert not unexpected and not changed,"
        " (sorted(unexpected), sorted(changed));"
        "print('OK')"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_export_provider_env_does_not_overwrite_existing(mocker) -> None:
    """Chaves já presentes no ambiente têm precedência."""
    mocker.patch.dict(os.environ, {"GROQ_API_KEY": "from_environment"}, clear=True)
    settings = Settings(_env_file=None, GROQ_API_KEY="from_settings")

    _export_provider_env(settings)

    assert os.environ["GROQ_API_KEY"] == "from_environment"


def test_export_provider_env_fills_missing_keys(mocker) -> None:
    """Chaves ausentes no ambiente são preenchidas a partir da configuração."""
    mocker.patch.dict(os.environ, {}, clear=True)
    settings = Settings(_env_file=None, GOOGLE_API_KEY="google_key")

    _export_provider_env(settings)

    assert os.environ["GOOGLE_API_KEY"] == "google_key"
    assert os.environ["GEMINI_API_KEY"] == "google_key"
    # Chaves vazias não são exportadas
    assert "TAVILY_API_KEY" not in os.environ


def test_purge_unreachable_redis_removes_env(mocker) -> None:
    """Redis inacessível deve ser removido do ambiente, sem lançar exceção."""
    mocker.patch.dict(
        os.environ, {"REDIS_URL": "redis://invalid-host:6379/0"}, clear=True
    )
    mock_client = mocker.MagicMock()
    mock_client.ping.side_effect = Exception("Connection refused")
    mocker.patch("src.runtime.create_client", return_value=mock_client)

    settings = Settings(_env_file=None, REDIS_URL="redis://invalid-host:6379/0")
    _purge_unreachable_redis(settings)

    assert "REDIS_URL" not in os.environ


def test_purge_keeps_reachable_redis(mocker) -> None:
    """Redis acessível permanece no ambiente."""
    mocker.patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}, clear=True)
    mocker.patch("src.runtime.create_client", return_value=mocker.MagicMock())

    settings = Settings(_env_file=None, REDIS_URL="redis://localhost:6379/0")
    _purge_unreachable_redis(settings)

    assert os.environ["REDIS_URL"] == "redis://localhost:6379/0"


def test_purge_remove_redis_com_tls_self_signed(mocker) -> None:
    """Redis `rediss://` sai do ambiente mesmo estando acessível.

    Regressão de produção (2026-07-30): o Heroku Key-Value Store usa certificado
    self-signed. Nossa fábrica de clientes trata isso, mas LiteLLM e CrewAI
    constroem o próprio cliente a partir do ambiente e falhavam com
    ``CERTIFICATE_VERIFY_FAILED`` no meio da orquestração — toda execução
    terminava em `failed`.
    """
    url = "rediss://:senha@host.compute.amazonaws.com:26770"
    mocker.patch.dict(os.environ, {"REDIS_URL": url}, clear=True)
    # Cliente saudável: a remoção não depende de falha de conexão
    mocker.patch("src.runtime.create_client", return_value=mocker.MagicMock())

    _purge_unreachable_redis(Settings(_env_file=None, REDIS_URL=url))

    assert "REDIS_URL" not in os.environ


def test_purge_com_tls_nao_afeta_a_configuracao_da_app() -> None:
    """A aplicação lê de ``Settings``, não do ambiente — o cache segue ativo."""
    url = "rediss://:senha@host:26770"
    settings = Settings(_env_file=None, REDIS_URL=url)

    _purge_unreachable_redis(settings)

    assert url == settings.REDIS_URL
    assert settings.cache_enabled is True


def test_configure_llm_runtime_is_idempotent(mocker) -> None:
    """A configuração roda uma única vez por processo, salvo ``force=True``."""
    reset_runtime_state()
    spy = mocker.patch("src.runtime._configure_litellm")
    settings = Settings(_env_file=None)

    configure_llm_runtime(settings)
    configure_llm_runtime(settings)
    assert spy.call_count == 1

    configure_llm_runtime(settings, force=True)
    assert spy.call_count == 2

    reset_runtime_state()
