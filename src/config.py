from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Localiza o diretório raiz do projeto (onde está o .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # Nomes EXATOS das variáveis do .env (Puro Pydantic v2)
    GROQ_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    @field_validator("GROQ_API_KEY", "SERPER_API_KEY", "GOOGLE_API_KEY", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove espaços em branco acidentais das chaves de API."""
        if isinstance(v, str):
            return v.strip()
        return v

    # Atalhos em minúsculo para manter a compatibilidade com o resto do código
    @property
    def groq_api_key(self) -> str:
        return self.GROQ_API_KEY

    @property
    def serper_api_key(self) -> str:
        return self.SERPER_API_KEY

    @property
    def google_api_key(self) -> str:
        return self.GOOGLE_API_KEY

    # Configurações de Modelos e Preços
    model_pro: str = "groq/llama-3.3-70b-versatile"
    model_fast: str = "groq/llama-3.1-8b-instant"
    model_extractor: str = "llama-3.1-8b-instant"
    model_pro_fallback: str = "gemini/gemini-flash-latest"
    model_fast_fallback: str = "gemini/gemini-flash-latest"

    # Configs Financeiras e GPS
    price_gpt4o_input: float = 5.0
    price_gpt4o_output: float = 15.0
    price_groq_input: float = 0.59
    price_groq_output: float = 0.79
    user_agent: str = "agencia_viagens_ia_portfolio"
    geocoding_delay: float = 1.1

    # O motor que lê o arquivo .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )


# Singleton instance
settings = Settings()  # type: ignore
