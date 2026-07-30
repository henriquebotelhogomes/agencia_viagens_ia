"""Cache de roteiros em Redis.

O serviço degrada graciosamente: sem ``REDIS_URL`` ou com o Redis inacessível,
as operações se tornam no-ops e a aplicação segue funcionando.

Nota (S1 do PRD): este módulo **não** muta ``os.environ``. A supressão de um Redis
quebrado para as bibliotecas de LLM é feita explicitamente pelo runtime
(``src.runtime.configure_llm_runtime``), nunca como efeito colateral de import.
"""

import hashlib
from functools import lru_cache

import redis
from loguru import logger

from src.config import Settings, get_settings
from src.services.redis_client import create_client
from src.utils.localization import DEFAULT_CURRENCY, DEFAULT_LANGUAGE


class CacheService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.enabled = self.settings.cache_enabled
        self.client: redis.Redis | None = None

        if self.enabled:
            try:
                self.client = create_client(self.settings, decode_responses=True)
                # Ping para confirmar que a conexão realmente funciona
                self.client.ping()
                logger.info("🟢 Redis Cache Service configurado com sucesso.")
            except Exception as e:
                logger.warning(
                    "🔴 Redis inacessível. Cache desativado para garantir "
                    f"estabilidade (a aplicação segue normalmente). Erro: {e}"
                )
                self.client = None
                self.enabled = False

    def _generate_key(
        self,
        origin: str,
        destination: str,
        duration: int,
        interests: str,
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
    ) -> str:
        """Gera um hash único baseado nos parâmetros de busca da viagem.

        Moeda e idioma compõem a chave (item S14 do PRD): um roteiro em
        pt-BR/BRL não pode ser servido para um pedido em en-US/USD.
        """
        raw_key = (
            f"{origin.lower().strip()}_{destination.lower().strip()}_"
            f"{duration}_{interests.lower().strip()}_"
            f"{moeda.upper().strip()}_{idioma.lower().strip()}"
        )
        return f"itinerary:{hashlib.sha256(raw_key.encode()).hexdigest()}"

    def get_cached_itinerary(
        self,
        origin: str,
        destination: str,
        duration: int,
        interests: str,
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
    ) -> str | None:
        """Tenta buscar o roteiro no cache do Redis."""
        if not self.enabled or not self.client:
            return None

        key = self._generate_key(
            origin, destination, duration, interests, moeda, idioma
        )
        try:
            cached_data = self.client.get(key)
            if cached_data:
                logger.info("🚀 Roteiro encontrado no cache do Redis!")
                return str(cached_data)
        except Exception as e:
            logger.error(f"⚠️ Erro ao ler do Redis: {e}")

        return None

    def save_itinerary(
        self,
        origin: str,
        destination: str,
        duration: int,
        interests: str,
        content: str,
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
    ) -> None:
        """Salva o roteiro gerado no Redis."""
        if not self.enabled or not self.client:
            return

        key = self._generate_key(
            origin, destination, duration, interests, moeda, idioma
        )
        try:
            # Salva a string com expiração
            self.client.setex(key, self.settings.CACHE_TTL_SECONDS, content)
            logger.info("💾 Roteiro salvo no cache do Redis.")
        except Exception as e:
            logger.error(f"⚠️ Erro ao salvar no Redis: {e}")


@lru_cache(maxsize=1)
def get_cache_service() -> CacheService:
    """Retorna o serviço de cache (memoizado).

    Forma preferida de obter o serviço: nada é conectado no import do módulo,
    apenas no primeiro uso real (item S2 do PRD). Em testes, use
    ``get_cache_service.cache_clear()`` para reinicializar.
    """
    return CacheService()
