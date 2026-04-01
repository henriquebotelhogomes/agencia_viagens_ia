# tests/test_config.py
import os

from src.config import Settings


def test_settings_load_from_env(mock_settings):
    """Testa se as configurações são carregadas corretamente."""
    assert mock_settings.GROQ_API_KEY == "mock_groq_key"
    assert mock_settings.SERPER_API_KEY == "mock_serper_key"


def test_settings_default_empty_values(mocker):
    """
    Testa se as chaves de API iniciam vazias por padrão (comportamento resiliente).
    """
    mocker.patch.dict(os.environ, {}, clear=True)
    # Passar _env_file=None para evitar que ele leia o arquivo .env real do projeto
    s = Settings(_env_file=None)
    assert s.GROQ_API_KEY == ""
    assert s.SERPER_API_KEY == ""
    assert s.GOOGLE_API_KEY == ""
