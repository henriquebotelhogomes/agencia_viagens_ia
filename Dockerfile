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
COPY app.py ./
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

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
