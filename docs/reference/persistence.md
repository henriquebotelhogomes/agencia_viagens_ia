# Persistência e worker

## Modelos

Entidades persistidas em PostgreSQL ([ADR-0008](../adr/0008-persistencia.md)).

```mermaid
erDiagram
    EXECUTION ||--o| ITINERARY : produz
    EXECUTION ||--o{ USAGE_RECORD : registra

    EXECUTION {
        uuid id PK
        string status
        string origem
        string destino
        int dias
        string moeda
        string idioma
        string briefing_hash
        string idempotency_key
        bool used_fallback
        bool served_from_cache
        float duration_seconds
    }
    ITINERARY {
        uuid id PK
        uuid execution_id FK
        text content_markdown
        json locations_geojson
        int version
    }
    USAGE_RECORD {
        uuid id PK
        uuid execution_id FK
        string model
        string gateway
        int prompt_tokens
        int completion_tokens
        float cost_usd
        float baseline_cost_usd
    }
```

!!! tip "Tipos portáveis"
    `JSONB` e `UUID` são nativos no PostgreSQL, mas o SQLite (usado nos testes)
    não os conhece. Os modelos usam `JSON().with_variant(JSONB(), "postgresql")`
    — o mesmo schema sobe nos dois bancos.

::: src.db.models
    options:
      show_root_heading: false

## Sessão e engine

::: src.db.base
    options:
      show_root_heading: false
      members:
        - build_engine
        - get_engine
        - get_session
        - dispose_engine

## Migrations

```bash
# Gerar migration a partir dos modelos
uv run alembic revision --autogenerate -m "descrição da mudança"

# Aplicar
uv run alembic upgrade head

# Reverter a última
uv run alembic downgrade -1
```

A URL vem sempre de `Settings.DATABASE_URL`, nunca do `alembic.ini` — a migration
usa exatamente a mesma configuração da aplicação.

## Worker

O worker consome a fila e executa a orquestração
([ADR-0014](../adr/0014-fila-saq.md)):

```bash
saq src.worker.settings.settings
```

Etapas de um job, com progresso publicado a cada transição:

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> running : worker pega o job
    running --> cache : verifica cache
    cache --> geocoding : hit
    cache --> orquestracao : miss
    orquestracao --> geocoding : roteiro pronto
    geocoding --> succeeded : locais resolvidos
    running --> failed : exceção
    queued --> cancelled : cancelamento
    succeeded --> [*]
    failed --> [*]
    cancelled --> [*]
```

::: src.worker.tasks
    options:
      show_root_heading: false
      members:
        - generate_itinerary
        - find_stale_executions

## Fila e progresso

::: src.services.queue_service
    options:
      show_root_heading: false

::: src.services.progress_bus
    options:
      show_root_heading: false

## Rate limiting

::: src.services.rate_limiter
    options:
      show_root_heading: false
