# Repository Guidelines

## Project Structure & Module Organization

Voyager AI is a Python 3.12 backend (FastAPI, SAQ, PostgreSQL and Redis) with a
Next.js frontend in `frontend/`. The backend core is deliberately separated:
`src/api/` owns HTTP, request validation and SSE; `src/worker/` owns queued job
execution; `src/services/` owns Redis, cache, geocoding, queue and other
integration adapters; and `src/db/` owns SQLAlchemy models and persistence.
Do not run CrewAI from an API route or introduce HTTP concerns in worker tasks.
The worker persists terminal execution state and publishes progress; the API
relays it to the browser. Read `docs/architecture/execution-flow.md` and
`docs/adr/0014-fila-saq.md` before changing that path.

Treat `src/config.py` as the configuration boundary. Do not hardcode business
configuration or secrets. External integrations must degrade gracefully and log
failures without exposing credentials. `frontend/AGENTS.md` contains mandatory
Next.js-specific instructions; read the relevant local Next.js documentation
before editing frontend code.

## Build, Test, and Development Commands

```bash
uv sync --group dev
docker compose up --build
uv run pytest tests/test_worker_tasks.py -q
uv run ruff check src/ tests/ scripts/ alembic/
uv run ruff format src/ tests/ scripts/ alembic/ --check
uv run mypy src/ --strict
uv run pytest tests/ --cov=src
uv run mkdocs build --strict
```

For frontend work, run from `frontend/`: `npm ci`, then `npm run typecheck`,
`npm run lint`, `npm run test:cov`, `npm run build`, and `npm run e2e` as
applicable. The local pre-commit hooks run the backend Ruff and mypy gates.

## Coding Style & Testing

Ruff enforces an 88-character, Python 3.12 style; mypy runs in strict mode.
Keep public Python signatures typed. `Any` is reserved for untyped library
boundaries such as CrewAI and loguru. Tests use pytest (asyncio auto mode) and
must not use real provider keys; shared isolation lives in `tests/conftest.py`.
The coverage gate is 90% for `src/`. Add a regression test for every bug fix.

## Commits & References

Use Conventional Commit subjects, as in `fix(worker): ...` or `docs: ...`.
Keep architecture decisions in `docs/adr/`, technical documentation in `docs/`,
and consult `CONTRIBUTING.md` plus `docs/guides/contributing.md` for the full
Definition of Done. Update documentation in the same change when behavior or
architecture changes.
