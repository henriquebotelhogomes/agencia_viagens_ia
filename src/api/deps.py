"""Dependências injetáveis da API (FastAPI `Depends`).

O trabalho de injeção de dependência feito na Fase 0 (item S2) é o que permite
que os serviços de domínio sejam usados aqui sem singleton global.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.base import get_session
from src.services.progress_bus import ProgressBus
from src.services.rate_limiter import RateLimiter, hash_client_ip


def settings_dep() -> Settings:
    """Configuração da aplicação."""
    return get_settings()


async def session_dep() -> AsyncIterator[AsyncSession]:
    """Sessão de banco por request, com rollback automático em erro."""
    async for session in get_session():
        yield session


def progress_bus_dep(request: Request) -> ProgressBus:
    """Barramento de progresso compartilhado (criado no lifespan)."""
    return request.app.state.progress_bus  # type: ignore[no-any-return]


def rate_limiter_dep(request: Request) -> RateLimiter:
    """Rate limiter compartilhado (criado no lifespan)."""
    return request.app.state.rate_limiter  # type: ignore[no-any-return]


def client_ip_hash_dep(request: Request) -> str:
    """Hash do IP do cliente, respeitando `X-Forwarded-For` do proxy.

    O IP em claro nunca é persistido nem logado (ver `rate_limiter`).
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        # O primeiro valor é o cliente original; os demais são proxies
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    return hash_client_ip(ip)


SettingsDep = Annotated[Settings, Depends(settings_dep)]
SessionDep = Annotated[AsyncSession, Depends(session_dep)]
ProgressBusDep = Annotated[ProgressBus, Depends(progress_bus_dep)]
RateLimiterDep = Annotated[RateLimiter, Depends(rate_limiter_dep)]
ClientIpHashDep = Annotated[str, Depends(client_ip_hash_dep)]
