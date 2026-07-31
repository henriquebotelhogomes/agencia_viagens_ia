"""Configuração de logging da aplicação (item S9 do PRD).

12-factor: em produção, logs são um **stream JSON em stdout** (coletado pelo
agregador da plataforma) — nunca arquivos locais. Em desenvolvimento, saída
colorida no terminal + arquivo rotacionado por conveniência.
"""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from src.config import Settings, get_settings

# Configuração de Caminhos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"

# Formato Profissional (desenvolvimento)
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger(settings: Settings | None = None) -> Any:
    """
    Configura o logger padrão da aplicação conforme o ambiente.

    - ``production``: JSON estruturado em stdout (12-factor, sem arquivo).
    - demais ambientes: console colorido + arquivo com rotação/retenção.
    """
    settings = settings or get_settings()

    # Remove configurações anteriores para evitar duplicidade
    logger.remove()

    if settings.is_production:
        # Stream JSON em stdout; o agregador da plataforma faz o resto
        logger.add(
            sys.stdout,
            serialize=True,
            level=settings.LOG_LEVEL,
            backtrace=False,
            diagnose=False,  # não vaza valores de variáveis em produção
        )
        return logger

    # Desenvolvimento: console colorido
    logger.add(sys.stderr, format=LOG_FORMAT, level=settings.LOG_LEVEL, colorize=True)

    # Arquivo apenas em desenvolvimento. Falha de permissão (ex.: container
    # rodando como non-root) **não** pode derrubar a aplicação — segue só console.
    try:
        LOG_DIR.mkdir(exist_ok=True)
        logger.add(
            LOG_DIR / "app.log",
            rotation="10 MB",
            retention="10 days",
            format=LOG_FORMAT,
            level="DEBUG",
            encoding="utf-8",
        )
    except OSError as e:
        logger.warning(
            f"Log em arquivo desabilitado ({LOG_DIR} indisponível): {e}. "
            "Seguindo apenas com saída no console."
        )

    return logger
