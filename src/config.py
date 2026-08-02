"""Configuração centralizada da aplicação (12-factor, via Pydantic Settings).

Referência das decisões: PRD.md §2 (D2, D10, D11, D12) e §8.2 (segredos).

Segredos são declarados como ``SecretStr`` para não vazarem em ``repr``/logs.
Use as propriedades em minúsculo para obter o valor em texto puro no ponto de uso.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Localiza o diretório raiz do projeto (onde está o .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Segredos: declarados juntos para o validador de sanitização
_SECRET_FIELDS = (
    "OPENCODE_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "GEOAPIFY_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "OTEL_EXPORTER_OTLP_HEADERS",
)


class Settings(BaseSettings):
    """Configuração da aplicação, carregada de variáveis de ambiente e ``.env``."""

    # ------------------------------------------------------------------
    # Aplicação
    # ------------------------------------------------------------------
    APP_ENV: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: str = "INFO"
    # Rate limiting da demo pública sem autenticação (FR-09)
    RATE_LIMIT_EXECUTIONS_PER_HOUR: int = 5
    # Origens permitidas no CORS (separadas por vírgula). Vazio = apenas localhost.
    CORS_ALLOWED_ORIGINS: str = ""

    # ------------------------------------------------------------------
    # LLM — gateway primário: OpenCode Go (PRD D2)
    # ------------------------------------------------------------------
    OPENCODE_API_KEY: SecretStr = SecretStr("")
    OPENCODE_API_BASE: str = "https://opencode.ai/zen/go/v1"
    LLM_MODEL_FAST: str = "deepseek-v4-flash"
    LLM_MODEL_FAST_TOOLS: str = "kimi-k2.7-code"
    # Teto de uso da aplicação no Go, preservando a cota pessoal de coding
    LLM_GO_MAX_REQUESTS_PER_DAY: int = 200

    # ------------------------------------------------------------------
    # LLM — tier `pro` e fallback universal: OpenRouter (PRD D2)
    # ------------------------------------------------------------------
    OPENROUTER_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL_PRO: str = "openrouter/google/gemini-3.5-flash"
    LLM_FALLBACK_FAST: str = "openrouter/google/gemini-3.5-flash"
    LLM_FALLBACK_TOOLS: str = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"

    # ------------------------------------------------------------------
    # Ferramentas dos agentes
    # ------------------------------------------------------------------
    TAVILY_API_KEY: SecretStr = SecretStr("")  # busca web (PRD D11)
    GEOAPIFY_API_KEY: SecretStr = SecretStr("")  # geocoding (PRD D10)

    # ------------------------------------------------------------------
    # Observabilidade de LLM — Langfuse Cloud (PRD D12)
    # ------------------------------------------------------------------
    LANGFUSE_PUBLIC_KEY: SecretStr = SecretStr("")
    LANGFUSE_SECRET_KEY: SecretStr = SecretStr("")
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # ------------------------------------------------------------------
    # Infraestrutura
    # ------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="",
        # `APP_REDIS_URL` tem precedência: é onde o bootstrap guarda a URL ao
        # esconder `REDIS_URL` de bibliotecas que leem o ambiente no import
        # (ver src/bootstrap.py).
        validation_alias=AliasChoices("APP_REDIS_URL", "REDIS_URL"),
    )
    REDIS_CONNECT_TIMEOUT: float = 2.0
    DATABASE_URL: str = ""
    # Pool de conexões do PostgreSQL (ADR-0008)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    # Fila de jobs (ADR-0014): nome, timeout de execução e concorrência do worker
    QUEUE_NAME: str = "voyager"
    JOB_TIMEOUT_SECONDS: int = 600
    WORKER_CONCURRENCY: int = 2
    # Somente CI E2E: executa um roteiro determinístico sem LLM ou rede.
    E2E_FAKE_GENERATION: bool = False
    CACHE_TTL_SECONDS: int = 86400  # 24 horas
    # TTL longo: coordenadas de atrações turísticas raramente mudam
    GEOCODING_CACHE_TTL_SECONDS: int = 2_592_000  # 30 dias

    # ------------------------------------------------------------------
    # OpenTelemetry — traces de infraestrutura (API, worker, banco, Redis).
    # Complementa o Langfuse (ADR-0012), que cobre só as chamadas de LLM.
    # Vazio = telemetria desligada (degradação graciosa, sem overhead).
    # ------------------------------------------------------------------
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    # Autenticação do backend OTLP (ex.: "Authorization=Bearer <token>")
    OTEL_EXPORTER_OTLP_HEADERS: SecretStr = SecretStr("")
    OTEL_SERVICE_NAME: str = "voyager-api"

    # ------------------------------------------------------------------
    # Preços de referência (USD por 1M tokens) para o comparativo FinOps
    # ------------------------------------------------------------------
    price_gpt4o_input: float = 5.0
    price_gpt4o_output: float = 15.0
    price_groq_input: float = 0.59
    price_groq_output: float = 0.79

    # Geocoding — user_agent do Nominatim (fallback) e rate limit de 1 req/s
    user_agent: str = "agencia_viagens_ia_portfolio"
    geocoding_delay: float = 1.1

    @field_validator(*_SECRET_FIELDS, mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> Any:
        """Remove espaços em branco acidentais das chaves de API."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_async_database_url(cls, v: Any) -> Any:
        """Garante o driver async na URL do PostgreSQL.

        Provedores gerenciados (Render, Heroku) entregam a URL como
        ``postgres://`` ou ``postgresql://``, que o SQLAlchemy tenta abrir com o
        driver **síncrono** e falha em contexto async. A normalização aqui evita
        depender de configuração manual correta no dashboard.
        """
        if not isinstance(v, str) or not v:
            return v
        v = v.strip()
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ------------------------------------------------------------------
    # Acesso aos segredos em texto puro (uso pontual, nunca em log)
    # ------------------------------------------------------------------
    @property
    def opencode_api_key(self) -> str:
        return self.OPENCODE_API_KEY.get_secret_value()

    @property
    def openrouter_api_key(self) -> str:
        return self.OPENROUTER_API_KEY.get_secret_value()

    @property
    def tavily_api_key(self) -> str:
        return self.TAVILY_API_KEY.get_secret_value()

    @property
    def geoapify_api_key(self) -> str:
        return self.GEOAPIFY_API_KEY.get_secret_value()

    @property
    def langfuse_public_key(self) -> str:
        return self.LANGFUSE_PUBLIC_KEY.get_secret_value()

    @property
    def langfuse_secret_key(self) -> str:
        return self.LANGFUSE_SECRET_KEY.get_secret_value()

    # ------------------------------------------------------------------
    # Flags derivadas — habilitam degradação graciosa por serviço
    # ------------------------------------------------------------------
    @property
    def cors_origins(self) -> list[str]:
        """Origens permitidas no CORS.

        Sem configuração explícita, libera apenas os endereços de desenvolvimento
        local — nunca `*`, que quebraria o uso de credenciais.
        """
        if self.CORS_ALLOWED_ORIGINS:
            return [
                origin.strip()
                for origin in self.CORS_ALLOWED_ORIGINS.split(",")
                if origin.strip()
            ]
        return ["http://localhost:3000", "http://localhost:8501"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cache_enabled(self) -> bool:
        return bool(self.REDIS_URL)

    @property
    def database_enabled(self) -> bool:
        """Indica se a persistência está configurada (ADR-0008)."""
        return bool(self.DATABASE_URL)

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def telemetry_enabled(self) -> bool:
        """Indica se há um backend OTLP configurado para traces."""
        return bool(self.OTEL_EXPORTER_OTLP_ENDPOINT)

    @property
    def opencode_enabled(self) -> bool:
        """Indica se o gateway primário de LLM está configurado."""
        return bool(self.opencode_api_key)

    @property
    def openrouter_enabled(self) -> bool:
        """Indica se o fallback/tier `pro` de LLM está configurado."""
        return bool(self.openrouter_api_key)

    # O motor que lê o arquivo .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a configuração da aplicação (memoizada).

    Forma preferida de obter a configuração: permite injeção de dependência
    (ex.: ``Depends(get_settings)`` no FastAPI) e substituição em testes via
    ``get_settings.cache_clear()``.
    """
    return Settings()


# Instância de módulo mantida por compatibilidade com o código atual.
# Será removida com a conclusão do item S2 do PRD (injeção de dependência).
settings = get_settings()
