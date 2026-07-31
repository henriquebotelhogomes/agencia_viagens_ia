# syntax=docker/dockerfile:1
# Dockerfile multi-stage (item S10 do PRD):
#   builder -> dependências e código de produção (sem dev)
#   test    -> imagem para o CI rodar a suite (dev deps + tests/)
#   runtime -> imagem final enxuta, rodando como usuário non-root

############################################
# Estágio 1: builder — deps de produção
############################################
FROM python:3.12-slim-bookworm AS builder

# Binário do uv a partir da imagem oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Camada de dependências (cacheável enquanto o lock não mudar)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# COPY seletivo do código (nada de `COPY . .`)
# README.md é exigido pelo hatchling (metadado `readme` do pyproject)
COPY README.md ./
COPY src/ src/
# Migrations do banco (PRD D8) — necessárias para `alembic upgrade head`
COPY alembic.ini ./
COPY alembic/ alembic/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

############################################
# Estágio 2: test — usado apenas pelo CI
# docker build --target test -t app:test .
############################################
FROM builder AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

COPY tests/ tests/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["pytest", "tests/", "-v"]

############################################
# Estágio 3: runtime — produção non-root
############################################
FROM python:3.12-slim-bookworm AS runtime

# Usuário sem privilégios (CIS Docker Benchmark)
RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    # Plataformas gerenciadas (Heroku, OpenShift) ignoram o `USER` e rodam com
    # um UID **arbitrário** e GID 0. Sem um HOME gravável, o CrewAI quebra no
    # import: ele resolve `$HOME/.local/share` para o storage do ChromaDB e
    # tenta criar o diretório (ADR-0015).
    HOME=/app \
    XDG_DATA_HOME=/app/.local/share \
    XDG_CACHE_HOME=/app/.cache

# Diretórios de escrita pertencendo ao grupo root com permissão de owner:
# receita padrão para funcionar com qualquer UID (o GID é sempre 0).
RUN mkdir -p /app/.local/share /app/.cache /app/logs \
    && chgrp -R 0 /app \
    && chmod -R g=u /app

USER app

# Sem CMD: `runtime` é a base comum — cada estágio de deploy (web/worker/
# release) e o docker-compose definem o seu próprio comando.

############################################
# Estágios de deploy (ADR-0015)
#
# O Heroku Container Registry entrega uma imagem por process type, cada uma com
# seu próprio CMD. Os três herdam de `runtime`, então compartilham camadas: o
# build extra custa apenas a camada do comando.
#
# Todos usam a forma shell do CMD de propósito — a plataforma injeta `$PORT` em
# tempo de execução e a forma exec não expandiria a variável.
############################################
FROM runtime AS web
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM runtime AS worker
CMD ["sh", "-c", "saq src.worker.settings.settings"]

# Release phase: se a migration falhar, o Heroku aborta o deploy e mantém a
# versão anterior no ar.
FROM runtime AS release
CMD ["sh", "-c", "alembic upgrade head"]
