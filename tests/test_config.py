# tests/test_config.py
import os

import pytest

from src.config import Settings


def test_settings_load_from_env(mock_settings):
    """Testa se as configurações são carregadas corretamente."""
    assert mock_settings.GROQ_API_KEY == "mock_groq_key"
    assert mock_settings.SERPER_API_KEY == "mock_serper_key"


def test_settings_missing_required_env_var(mocker):
    """
    Testa se um erro é levantado quando uma variável de ambiente
    obrigatória está faltando.
    """
    mocker.patch.dict(os.environ, {}, clear=True)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        # Passar _env_file=None para evitar que ele leia o arquivo .env real do projeto
        Settings(_env_file=None)
