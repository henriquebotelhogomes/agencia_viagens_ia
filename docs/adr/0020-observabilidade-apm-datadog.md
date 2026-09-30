# ADR-0020 — Observabilidade Full-Stack: Datadog Pro APM via GitHub Student

- **Status**: Aceita
- **Data**: 2026-09-29
- **Contexto do PRD**: D12
- **Alinhamento do Harness**: `~/.gemini/config/resources.md` (§2) e `GEMINI.md` (§3)

## Contexto e problema

O [ADR-0012](0012-observabilidade-llm.md) estabeleceu o **Langfuse Cloud** como a plataforma central de observabilidade de LLMs (tracing de agentes CrewAI, spans de execução e contagem de tokens). Complementarmente, os logs da aplicação foram estruturados em JSON para stdout ([ADR-0006](0006-backend.md)).

No entanto, o sistema opera de forma distribuída e assíncrona entre múltiplos componentes no Google Cloud Run ([ADR-0018](0018-hospedagem-gcp-cloud-run.md)):

```
[Browser / Next.js] ──► [Cloud Run: voyager-api] ──► [Redis / SAQ] ──► [Cloud Run: voyager-worker]
                                    │                                           │
                                    ▼                                           ▼
                            [PostgreSQL DB]                              [APIs Externas]
```

Existiam os seguintes gaps de observabilidade de infraestrutura:

1. **Ausência de Tracing Distribuído Unificado:** Não havia correlação ponta a ponta entre a requisição HTTP recebida na API, o tempo de permanência do job na fila SAQ e o tempo de execução do worker.
2. **Métricas de Infraestrutura e Latência:** Falta de telemetria consolidada de latência p95/p99 de queries ao PostgreSQL, cold starts de containers do Cloud Run e chamadas HTTP a serviços externos (Geoapify e Tavily).

## Opções consideradas

### 1. Manter apenas Langfuse + Cloud Run Metrics (status quo)

- ✅ Simplicidade e custo zero.
- ❌ Visão fragmentada: o Langfuse enxerga apenas a execução da LLM, mas não detalha gargalos de banco de dados, conexão com Redis ou filas assíncronas.

### 2. Prometheus + Grafana auto-hospedados

- ✅ Padrão open-source amplamente adotado.
- ❌ Incompatível com o princípio **Scale-to-Zero ($0/mês)**: exigiria containers continuamente ativos com consumo fixo de RAM e disco.

### 3. Datadog Pro (Ativo via GitHub Student Developer Pack)

- ✅ **Recurso Ativo e Gratuito:** Conta corporativa Datadog Pro com 2 anos de gratuidade ativa na região `us5.datadoghq.com`.
- ✅ **APM Distribuído Completo:** Suporte oficial a Python via `ddtrace` com instrumentação automática para FastAPI, SQLAlchemy, Redis e HTTPX.
- ✅ **Métricas com Retenção Estendida:** 13 meses de histórico, monitoramento de até 10 hosts/containers e dashboards corporativos pré-configurados.
- ✅ **Sinergia:** O Datadog gerencia o APM e a infraestrutura, enquanto o Langfuse permanece dedicado à avaliação de prompts e LLMOps.

## Decisão

Adotar o **Datadog Pro** como a camada corporativa de **APM e Tracing Distribuído** da aplicação:

1. **Instrumentação da API e Worker:** Utilização do pacote `ddtrace` no container backend (`voyager-api` e `voyager-worker`).
2. **Correlação de Traces:** Injeção de `trace_id` e `span_id` nos logs estruturados JSON (`structlog`/`loguru`).
3. **Métricas de Serviços Externos:** Rastreamento do tempo de resposta de integrações críticas (Tavily Search API, Geoapify Geocoding API e gateways OpenCode Go / OpenRouter).

## Consequências

### Positivas

- **Visibilidade Ponta a Ponta:** Rastreabilidade completa da jornada do usuário: do clique no Next.js até a persistência no PostgreSQL e retorno por SSE.
- **Detecção Imediata de Gargalos:** Identificação precisa de quando uma lentidão decorre de latência de rede externa (Tavily/OpenCode Go) vs. processamento interno.
- **Portfólio de Nível Sênior:** Demonstração prática de observabilidade corporativa padrão Big Tech em um projeto com custo fixo zero.

### Negativas / Mitigações

- **Sobrecarga de Inicialização (Overhead de CPU/RAM):** O agente do Datadog roda em modo slim (`DD_TRACE_AGENT_URL` ou ingestão serverless) para não impactar os tempos de cold start do Cloud Run.
- **Degradação Graciosa:** Se as chaves do Datadog não estiverem configuradas no ambiente local, o `ddtrace` opera em modo passivo sem interromper o fluxo da aplicação.
