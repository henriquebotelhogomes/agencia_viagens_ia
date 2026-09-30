# 🧠 Diretrizes de Engenharia & Governança Local: Voyager AI (Tier 2)

> **Manual Normativo Local** — Especializado para o ecossistema Voyager AI: Multi-Agentes assíncronos, FastAPI, Next.js, SAQ, Redis, PostgreSQL e infraestrutura serverless no Google Cloud Run.

---

## 1. Stack & Padrões Normativos do Backend de IA (Python 3.12)
* **Gerenciador de Dependências:** Uso estrito de **`uv`** com **`pyproject.toml`** (PEP 621) e lockfile determinístico (`uv.lock`). Proibido `setup.py` ou `pip install` solto.
* **Framework Web & Lifespan:** **FastAPI** assíncrono. Inicialização de conexões (PostgreSQL, Redis, HTTP pools, tracing) estritamente via **`@asynccontextmanager lifespan`**. Proibido usar eventos legados `@app.on_event`.
* **Separação Arquitetural Rígida:**
  * `src/api/`: Camada HTTP, validação de briefing (Pydantic v2), streaming SSE e documentação. Proibido invocar orquestrações pesadas de IA diretamente na thread do request.
  * `src/worker/`: Tarefas assíncronas do **SAQ**, execução de agentes e persistência de estado. Proibido acoplar dependências de HTTP no worker.
  * `src/services/`: Clientes de integração (Redis, Geocoding, Cache, Langfuse, LiteLLM/OpenCode Go/OpenRouter).
  * `src/db/`: Modelos SQLAlchemy e migrations com Alembic.
* **Documentação de API:** **Scalar obrigatório** servido em `/docs` ou `/api/docs`. Proibido Swagger UI clássico.
* **Structured Outputs & Schema Enforcement:** Validação estrita com Pydantic v2 para pontos de interesse (POIs), planos de gastos e metadados de geocodificação.
* **Logging Estruturado:** `structlog` ou `loguru` com injeção de `trace_id`, `execution_id`, `model` e tokens.

---

## 2. Orquestração de Agentes, Modelos & FinOps
* **Orquestração de Agentes:** Orquestração desacoplada em background com controle de concorrência, idempotência e fallback.
* **Decision Models & Roteamento Especializado (Jev First):**
  * Para triagem rápida de intenção, validação pré-execução de briefing, classificação de estilo de viagem e guardrails (<30ms) onde não há geração de texto livre para o usuário, avaliar e priorizar **Jev (`typesafe/jev-latest` via OpenRouter)** com custo de output \$0.00.
* **Roteamento de LLMs & FinOps (Conforme `~/.gemini/config/resources.md`):**
  * **Tier 0 (Decisão / Guardrail):** Jev (`typesafe/jev-latest`).
  * **Tier 1 (Alta Velocidade / Custo Zero na Assinatura):** **Gemini 3.8 Flash** (Google Gemini Pro) e **DeepSeek V4.1 Flash** / **Qwen 3.8 Flash** (OpenCode Go).
  * **Tier 2 (Fallback & Evals Gratuitos):** Modelos `:free` do OpenRouter com saldo mantido > \$10 (consultar dinamicamente [https://openrouter.ai/collections/free-models](https://openrouter.ai/collections/free-models)).
  * **Tier 3 (Raciocínio Profundo):** DeepSeek V4 Pro, Qwen 3.8 Max ou Gemini 3 Pro para roteiros complexos e síntese crítica.
* **Telemetria Analítica & OLAP (Zero-Daemon):**
  * **`DuckDB`**: Consultas analíticas locais ultrarrápidas sobre histórico de execuções, consumo de tokens e logs particionados em `.parquet` para o painel de FinOps.

---

## 3. Observabilidade Corporativa & APM
* **APM & Tracing de Infraestrutura:** Priorizar **Datadog Pro (Ativo via GitHub Student)** para tracing distribuído de requisições, latência do worker SAQ e métricas de container no Cloud Run.
* **APM de IA (Langfuse):** Tracing de spans, visualização de custos por execução e gestão de prompts via Langfuse Cloud.
* **Crash Reporting:** Sentry para captura e rastreamento de exceções no frontend e backend.

---

## 4. Segurança, Guardrails & Red-Teaming
* **Guardrails em Runtime:** Sanitização estrita de entradas do usuário para prevenir prompt injection em campos de briefing de viagem e proteção de PII (LGPD).
* **Red-Teaming Gate no CI/CD:** Auditoria automatizada via **Promptfoo** em pull requests contra tentativas de jailbreak e vazamento de system prompt.
* **Proteção de Segredos:** Zero chaves expostas no código. Segredos exclusivos em `.env` e variáveis do Cloud Run, protegidos pelo Secret Scanning Push Protection do GitHub.

---

## 5. Qualidade de Software, Testes & Fechamento por Evidência
* **Mypy em Modo Estrito:** `mypy src/ --strict` aprovado com 100% de tipagem estrita.
* **Linting & Formatação:** `ruff check src/ tests/ scripts/ alembic/` e `ruff format --check`.
* **Gates de Cobertura:** $\ge 90\%$ no backend (`uv run pytest tests/ --cov=src`) e $\ge 85\%$ no frontend (`npm run test:cov`).
* **Harness Engineering & Comprovação por Evidência:** Toda alteração de código deve ser comprovada determinísticamente via execução no terminal dos testes e linters antes da entrega.
