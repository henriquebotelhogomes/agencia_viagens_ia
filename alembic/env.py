"""Ambiente do Alembic — migrations async sobre a configuração da aplicação.

A URL do banco vem sempre de ``Settings.DATABASE_URL``; nunca do `alembic.ini`.
Assim a migration usa exatamente a mesma configuração da aplicação.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection

from alembic import context
from src.config import get_settings

# Importa os modelos para que o autogenerate os enxergue
from src.db.base import Base
from src.db.models import Execution, Itinerary, UsageRecord  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """URL do banco a partir da configuração da aplicação."""
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada — impossível migrar.")
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Gera o SQL das migrations sem conectar ao banco."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executa as migrations numa conexão já estabelecida."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detecta mudança de tipo de coluna
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria o engine async e aplica as migrations."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(_database_url(), poolclass=None)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Ponto de entrada do modo online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
