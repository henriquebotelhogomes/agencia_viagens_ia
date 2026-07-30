# tests/test_config.py
import os

from src.config import Settings, get_settings


def test_settings_load_from_env(mock_settings):
    """Testa se as configurações são carregadas corretamente."""
    assert mock_settings.groq_api_key == "mock_groq_key"
    assert mock_settings.serper_api_key == "mock_serper_key"


def test_secrets_are_not_exposed_in_repr(mock_settings):
    """Garante que segredos não vazam em repr/log (PRD §8.2)."""
    assert "mock_groq_key" not in repr(mock_settings)
    assert "mock_opencode_key" not in repr(mock_settings)


def test_new_provider_settings_are_available(mock_settings):
    """Testa as chaves dos novos provedores (PRD D2, D10, D11, D12)."""
    assert mock_settings.opencode_api_key == "mock_opencode_key"
    assert mock_settings.openrouter_api_key == "mock_openrouter_key"
    assert mock_settings.tavily_api_key == "mock_tavily_key"
    assert mock_settings.geoapify_api_key == "mock_geoapify_key"
    assert mock_settings.opencode_enabled is True
    assert mock_settings.openrouter_enabled is True


def test_settings_default_empty_values(mocker):
    """
    Testa se as chaves de API iniciam vazias por padrão (comportamento resiliente).
    """
    mocker.patch.dict(os.environ, {}, clear=True)
    # Passar _env_file=None para evitar que ele leia o arquivo .env real do projeto
    s = Settings(_env_file=None)
    assert s.groq_api_key == ""
    assert s.serper_api_key == ""
    assert s.google_api_key == ""
    assert s.opencode_api_key == ""
    assert s.tavily_api_key == ""


def test_derived_flags_degrade_gracefully(mocker):
    """Sem configuração, os serviços opcionais ficam desabilitados."""
    mocker.patch.dict(os.environ, {}, clear=True)
    s = Settings(_env_file=None)
    assert s.cache_enabled is False
    assert s.langfuse_enabled is False
    assert s.opencode_enabled is False
    assert s.is_production is False


def test_get_settings_is_memoized():
    """``get_settings`` deve devolver sempre a mesma instância."""
    assert get_settings() is get_settings()
