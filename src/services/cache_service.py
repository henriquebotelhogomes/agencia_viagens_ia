import hashlib
from typing import Optional

import redis
from loguru import logger

from src.config import settings


class CacheService:
    def __init__(self) -> None:
        self.enabled = bool(settings.REDIS_URL)
        self.client = None
        if self.enabled:
            try:
                # We expect something like redis://username:password@host:port/db
                self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                # Ping to check if connection is actually working
                self.client.ping()
                logger.info("🟢 Redis Cache Service configurado com sucesso.")
            except Exception as e:
                logger.warning(
                    f"🔴 Falha ao conectar no Redis. Fallback. Erro: {e}"
                )
                self.enabled = False

    def _generate_key(self, origin: str, destination: str, duration: int, interests: str) -> str:
        """Gera um hash único baseado nos parâmetros de busca da viagem."""
        raw_key = (
            f"{origin.lower().strip()}_{destination.lower().strip()}_"
            f"{duration}_{interests.lower().strip()}"
        )
        return f"itinerary:{hashlib.sha256(raw_key.encode()).hexdigest()}"

    def get_cached_itinerary(
        self, origin: str, destination: str, duration: int, interests: str
    ) -> Optional[str]:
        """Tenta buscar o roteiro no cache do Redis."""
        if not self.enabled or not self.client:
            return None

        key = self._generate_key(origin, destination, duration, interests)
        try:
            cached_data = self.client.get(key)
            if cached_data:
                logger.info("🚀 Roteiro encontrado no cache do Redis!")
                return str(cached_data)
        except Exception as e:
            logger.error(f"⚠️ Erro ao ler do Redis: {e}")

        return None

    def save_itinerary(
        self, origin: str, destination: str, duration: int, interests: str, content: str
    ) -> None:
        """Salva o roteiro gerado no Redis."""
        if not self.enabled or not self.client:
            return

        key = self._generate_key(origin, destination, duration, interests)
        try:
            # Save string with expiration
            self.client.setex(key, settings.CACHE_TTL_SECONDS, content)
            logger.info("💾 Roteiro salvo no cache do Redis.")
        except Exception as e:
            logger.error(f"⚠️ Erro ao salvar no Redis: {e}")

# Singleton instance
cache_service = CacheService()
