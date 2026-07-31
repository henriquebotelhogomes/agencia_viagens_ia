"""Inicialização explícita do runtime da aplicação.

Este módulo concentra tudo o que antes acontecia como **efeito colateral de
import** (item S1 do PRD): configuração global do LiteLLM, exportação de chaves
para variáveis de ambiente exigidas por SDKs de terceiros e supressão de um
Redis inacessível.

Regra: nenhum módulo de domínio deve mutar estado global no import. Os
entrypoints (API, worker) chamam ``configure_llm_runtime()`` uma única vez,
no início da execução.
"""

import os

from loguru import logger

from src.config import Settings, get_settings
from src.services.redis_client import create_client

_configured = False


def _purge_unreachable_redis(settings: Settings) -> None:
    """Retira ``REDIS_URL`` do ambiente quando bibliotecas externas não podem usá-la.

    LiteLLM e CrewAI leem ``REDIS_URL`` diretamente do ambiente para habilitar
    cache próprio, construindo o cliente com **configuração própria** — fora da
    nossa fábrica em :mod:`src.services.redis_client`. Dois cenários as fazem
    falhar no meio da orquestração:

    1. **Host inacessível** — erro de conexão em cada chamada de LLM.
    2. **TLS com certificado self-signed** (``rediss://``, padrão do Heroku
       Key-Value Store) — elas validam a cadeia e recebem
       ``CERTIFICATE_VERIFY_FAILED``.

    Remover a variável do ambiente não afeta a aplicação: nosso código lê
    ``settings.REDIS_URL`` e conecta pela fábrica, que trata o TLS. O único
    efeito é desligar o cache interno dessas bibliotecas — que não usamos, pois
    o cache de roteiros é nosso (``CacheService``).
    """
    if not settings.REDIS_URL:
        return

    if settings.REDIS_URL.startswith("rediss://"):
        logger.info(
            "Redis com TLS self-signed: REDIS_URL retirada do ambiente para que "
            "LiteLLM e CrewAI não tentem conectar sem a config de certificado. "
            "O cache da aplicação segue ativo pela fábrica de clientes."
        )
        os.environ.pop("REDIS_URL", None)
        return

    try:
        client = create_client(settings)
        client.ping()
    except Exception as e:
        logger.warning(
            "Redis inacessível no arranque; removendo REDIS_URL do ambiente "
            f"para evitar falhas nas bibliotecas de LLM. Erro: {e}"
        )
        os.environ.pop("REDIS_URL", None)


def _export_provider_env(settings: Settings) -> None:
    """Exporta chaves para as variáveis de ambiente esperadas pelos SDKs.

    Alguns SDKs (litellm e integrações) leem apenas do ambiente. A
    exportação é feita aqui, de forma explícita e sem sobrescrever valores que
    já existam no ambiente.
    """
    provider_keys = {
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "TAVILY_API_KEY": settings.tavily_api_key,
        # Callback "langfuse" do litellm lê a configuração do ambiente (PRD D12)
        "LANGFUSE_PUBLIC_KEY": settings.langfuse_public_key,
        "LANGFUSE_SECRET_KEY": settings.langfuse_secret_key,
        "LANGFUSE_HOST": settings.LANGFUSE_HOST if settings.langfuse_enabled else "",
    }
    for name, value in provider_keys.items():
        if value and not os.environ.get(name):
            os.environ[name] = value


def _configure_litellm(settings: Settings) -> None:
    """Ajusta o LiteLLM para operação previsível em produção."""
    import litellm

    # Desativa o cache interno, que pode tentar usar o Redis automaticamente
    litellm.cache = None
    # Remove parâmetros não suportados pelo provider em vez de falhar
    litellm.drop_params = True
    # Logs de debug apenas fora de produção (via LITELLM_LOG; `set_verbose`
    # está deprecado no litellm >= 1.8)
    if not settings.is_production:
        os.environ.setdefault("LITELLM_LOG", "INFO")

    if settings.langfuse_enabled:
        # Tracing de LLM: tokens, custo e prompts por chamada (PRD D12)
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        logger.info("🔭 Langfuse habilitado para tracing de LLM.")


def configure_llm_runtime(
    settings: Settings | None = None, *, force: bool = False
) -> Settings:
    """Prepara o runtime da aplicação. Idempotente por padrão.

    Deve ser chamada uma vez por processo, antes de construir agentes ou LLMs.
    """
    global _configured

    resolved = settings or get_settings()
    if _configured and not force:
        return resolved

    _purge_unreachable_redis(resolved)
    _export_provider_env(resolved)
    _configure_litellm(resolved)

    _configured = True
    return resolved


def reset_runtime_state() -> None:
    """Permite reconfigurar o runtime (uso em testes)."""
    global _configured
    _configured = False
