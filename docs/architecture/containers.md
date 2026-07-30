# C4 nível 2 — Contêineres

## Estado atual (Fase 0 concluída)

```mermaid
graph TB
    U["👤 Viajante"]

    subgraph proc["Processo Python único"]
        ST["<b>Streamlit</b><br/><i>app.py</i><br/>UI + orquestração no request"]
        CORE["<b>Núcleo de domínio</b><br/><i>src/</i><br/>CrewAI + serviços"]
        ST --> CORE
    end

    RD[("<b>Redis</b><br/><i>opcional</i><br/>cache de roteiros<br/>e geocoding")]
    EXT["Serviços externos<br/><i>LLM · Tavily · Geoapify<br/>Frankfurter · Langfuse</i>"]

    U -->|HTTPS| ST
    CORE --> RD
    CORE --> EXT

    style ST fill:#ff7043,color:#fff
    style CORE fill:#3f51b5,color:#fff
```

**Limitação conhecida**: a orquestração roda **dentro do request** do Streamlit
(50-90s de espera bloqueante), e os roteiros só existem em cache efêmero. É
exatamente o que a Fase 1 resolve.

## Alvo (Fase 1 + Fase 2)

```mermaid
graph TB
    U["👤 Viajante"]

    subgraph render["Render"]
        FE["<b>Next.js 15</b><br/><i>web service</i><br/>UI + BFF"]
        API["<b>FastAPI</b><br/><i>web service</i><br/>REST + SSE + rate limit"]
        WK["<b>Worker Arq</b><br/><i>background</i><br/>orquestração CrewAI"]
        PG[("<b>PostgreSQL</b><br/>Execution · Itinerary<br/>UsageRecord")]
        RD[("<b>Redis</b><br/>fila · cache<br/>pub/sub · rate limit")]
    end

    EXT["Serviços externos"]
    OTEL["OpenTelemetry<br/>+ Langfuse"]

    U -->|HTTPS| FE
    FE -->|"REST + SSE"| API
    API --> PG
    API --> RD
    API -->|enfileira job| RD
    RD -->|consome| WK
    WK --> EXT
    WK --> PG
    WK -->|"publica progresso"| RD
    RD -->|"relay SSE"| API
    API -.traces.-> OTEL
    WK -.traces.-> OTEL

    style FE fill:#00897b,color:#fff
    style API fill:#3f51b5,color:#fff
    style WK fill:#5e35b1,color:#fff
```

## Contêineres

| Contêiner | Tecnologia | Responsabilidade | Estado |
| --------- | ---------- | ---------------- | ------ |
| **Streamlit** | Streamlit | UI atual (playground) | ✅ ativo |
| **Núcleo de domínio** | Python 3.12, CrewAI, litellm | Agentes, tarefas, serviços | ✅ ativo |
| **Redis** | Render Key Value | Cache; futuro: fila, pub/sub, rate limit | ✅ opcional |
| **FastAPI** | FastAPI, Pydantic v2 | Contratos REST/OpenAPI, SSE, rate limit | ⏳ Fase 1 |
| **Worker** | Arq | Execução assíncrona da crew | ⏳ Fase 1 |
| **PostgreSQL** | Render Postgres, SQLAlchemy 2.0 async | Persistência de execuções e roteiros | ⏳ Fase 1 |
| **Next.js** | Next.js 15, TypeScript, Tailwind | UI de produto, streaming, mapa | ⏳ Fase 2 |

## Por que essa separação

| Decisão | Motivo |
| ------- | ------ |
| Worker separado da API | Isola carga de LLM (minutos) do tráfego HTTP (ms); permite escalar por profundidade de fila |
| SSE em vez de WebSocket | Progresso é unidirecional; SSE é mais simples e sobrevive a proxies |
| Redis como pub/sub | O worker publica progresso; a API faz relay para o cliente sem acoplamento direto |
| PostgreSQL além do Redis | Roteiro é ativo do usuário, não cache — precisa de durabilidade e histórico |

Ver [ADR-0006](../adr/0006-backend.md), [ADR-0007](../adr/0007-fila-worker.md) e
[ADR-0008](../adr/0008-persistencia.md) para os trade-offs completos.
