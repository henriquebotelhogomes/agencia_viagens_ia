# 11 — Riscos, Premissas e Decisões Arquiteturais (ADRs)

Consolida o que pode dar errado, o que assumimos como verdade e por que escolhemos cada
caminho. Demonstrar este tipo de raciocínio explícito é o que separa engenharia sênior de
"montar features".

---

## Parte A — Premissas

| ID | Premissa | Impacto se falsa |
|----|----------|------------------|
| AS-01 | Há acesso estável a providers de LLM (Groq/Gemini) com custo previsível. | Reavaliar tiering/fallback e margem. |
| AS-02 | Latência de geração (~30–45s) é aceitável com streaming de progresso. | Investir mais em paralelização/cache. |
| AS-03 | Usuários valorizam **confiança/transparência** acima de respostas instantâneas. | Repriorizar velocidade sobre proveniência. |
| AS-04 | Cache (exato + semântico) atinge hit ratio relevante (≥30%). | Custo por roteiro maior; revisar pricing. |
| AS-05 | Dados de viagem são sensíveis, mas não regulados como saúde/financeiro. | Reforçar compliance se mudar o público. |
| AS-06 | Time pequeno (1 dev) — operação precisa ser simples. | Evitar microsserviços; preferir managed services. |
| AS-07 | Busca web (Serper) e geocoding (Nominatim) cobrem a qualidade necessária na v1. | Trocar por provedores pagos/robustos. |

---

## Parte B — Riscos

Escala: Probabilidade (B/M/A) × Impacto (B/M/A).

| ID | Risco | P × I | Mitigação |
|----|-------|-------|-----------|
| RK-01 | **Alucinação** do LLM (preço/horário/local errado) | A×A | Multiagente + proveniência + eval + feedback + disclaimer |
| RK-02 | **Custo de LLM** escala além da margem | M×A | FinOps, cache, roteamento de modelo, cotas por plano |
| RK-03 | **Indisponibilidade de provider** | M×A | Fallback chain + circuit breaker multi-provider |
| RK-04 | **Prompt injection** via conteúdo web | M×M | Tratar tool output como não confiável; sanitização; agência limitada |
| RK-05 | **Latência alta** frustra usuário | M×M | Streaming, paralelização, cache, skeletons |
| RK-06 | **Rate limit / quotas** dos providers | M×M | Concorrência limitada, backoff, filas |
| RK-07 | **Vazamento de PII** em logs/prompts | B×A | Redaction, criptografia, secret manager |
| RK-08 | **Lock-in** de provider/cloud | B×M | Abstrações (LiteLLM, OTel, S3-compatível) |
| RK-09 | **Over-engineering** para 1 dev | M×M | Roadmap faseado; monólito modular; managed services |
| RK-10 | **Qualidade do geocoding** (locais não encontrados) | M×B | Degradação graciosa; cache; provider alternativo |
| RK-11 | **Dependências com CVE** | M×M | Scan no CI, lockfiles, atualizações |
| RK-12 | **Custo/limite do Render free** em produção | A×M | Planejar upgrade/migração; IaC portável |

---

## Parte C — Architecture Decision Records (ADRs)

Formato curto: **Contexto · Decisão · Consequências · Alternativas**.

### ADR-001 — Manter CrewAI como motor de orquestração
- **Contexto:** núcleo atual usa CrewAI com 3 agentes; funciona e reduz alucinação.
- **Decisão:** manter CrewAI; envolvê-lo em worker assíncrono.
- **Consequências:** reuso máximo; acoplamento ao framework mitigado por camada de serviço.
- **Alternativas:** LangGraph (mais controle de fluxo, mais código), orquestração própria.

### ADR-002 — API desacoplada (FastAPI) em vez de manter Streamlit como produto
- **Contexto:** Streamlit acopla UI e lógica; não escala como SaaS.
- **Decisão:** FastAPI como API de domínio; Next.js como frontend; Streamlit vira playground.
- **Consequências:** mais flexível, testável e escalável; custo de construir novo frontend.
- **Alternativas:** continuar no Streamlit (rejeitado por limites de UX/escala/multi-tenant).

### ADR-003 — Geração assíncrona com fila + streaming SSE
- **Contexto:** geração leva dezenas de segundos; síncrono trava UI e API.
- **Decisão:** job assíncrono (fila/worker) + progresso via SSE.
- **Consequências:** UX responsiva, escala independente; complexidade de fila/estado.
- **Alternativas:** síncrono (rejeitado), WebSocket (overkill para fluxo unidirecional).

### ADR-004 — Modular monolith antes de microsserviços
- **Contexto:** time pequeno; produto novo.
- **Decisão:** monólito modular com fronteiras claras; extrair serviços só quando justificar.
- **Consequências:** menor custo operacional; risco de erosão de fronteiras (mitigado por ADRs/testes).
- **Alternativas:** microsserviços desde o início (rejeitado por complexidade prematura).

### ADR-005 — PostgreSQL + pgvector como armazenamento primário
- **Contexto:** precisamos de relacional confiável + busca vetorial (cache semântico).
- **Decisão:** PostgreSQL com `pgvector`; Redis para cache/fila/pubsub; object storage para artefatos.
- **Consequências:** menos serviços para operar; um banco resolve OLTP + vetorial.
- **Alternativas:** banco vetorial dedicado (Pinecone/Qdrant) — adiado até a escala exigir.

### ADR-006 — Abstração multi-provider de LLM (LiteLLM) com fallback
- **Contexto:** risco de indisponibilidade/custo; evitar lock-in.
- **Decisão:** LiteLLM com tiers (`fast`/`pro`) e fallback chain configurável.
- **Consequências:** resiliência e flexibilidade de custo; complexidade de configuração.
- **Alternativas:** SDK único de provider (rejeitado por lock-in/fragilidade).

### ADR-007 — Observabilidade com OpenTelemetry + Langfuse
- **Contexto:** precisamos de rastreabilidade ponta a ponta e visão de custo/qualidade de LLM.
- **Decisão:** OTel (vendor-neutral) + Langfuse para tracing/eval de LLM.
- **Consequências:** liberdade de backend; instrumentação como critério de "pronto".
- **Alternativas:** APM proprietário (lock-in), só logs (insuficiente).

### ADR-008 — Multi-tenant por banco compartilhado + RLS
- **Contexto:** SaaS com isolamento, mas operação simples.
- **Decisão:** `workspace_id` em todas as queries + PostgreSQL RLS (defesa em profundidade).
- **Consequências:** simples e seguro o suficiente; caminho para DB-per-tenant em enterprise.
- **Alternativas:** schema/DB por tenant desde já (rejeitado por overhead operacional).

### ADR-009 — Frontend com Next.js (App Router) + design system shadcn/Radix
- **Contexto:** precisamos de UX premium, acessível, SEO e streaming.
- **Decisão:** React 18 + Next.js 14, Tailwind + shadcn/ui + Radix + Framer Motion.
- **Consequências:** DX e qualidade altas; curva de design system a manter.
- **Alternativas:** SPA Vite pura (sem SSR/SEO), Remix (válido; Next escolhido por ecossistema).

### ADR-010 — FinOps baseado em uso real de tokens (evoluir da heurística)
- **Contexto:** `FinanceService` atual estima custo por heurística de caracteres.
- **Decisão:** capturar tokens reais via callbacks do provider e gravar `UsageRecord`.
- **Consequências:** custo preciso, base para billing e alertas; depende de telemetria do provider.
- **Alternativas:** manter heurística (rejeitada para produção; ok para demo inicial).

---

## Parte D — Decisões em aberto (a revisitar)

| ID | Questão | Quando decidir |
|----|---------|----------------|
| OP-01 | Celery vs Arq para fila | Início da Fase 1 |
| OP-02 | Backend de observabilidade (self-host vs Grafana Cloud) | Fase 2 |
| OP-03 | Provider de busca web definitivo (Serper vs Tavily/Bing) | Fase 3 |
| OP-04 | Estratégia de billing/metering detalhada | Fase 4 |
| OP-05 | Quando extrair o Orquestrador como serviço | Guiado por métricas de escala |

---

## Parte E — Como estas decisões reduzem risco para o avaliador

Cada ADR registra **trade-offs explícitos** e alternativas rejeitadas — evidência de
pensamento de arquitetura. Os riscos têm **mitigações concretas e mensuráveis**, ligadas a
[`05`](./05-non-functional-requirements.md), [`06`](./06-observability.md),
[`07`](./07-performance-scalability.md) e [`08`](./08-security.md). O conjunto mostra um
projeto que pensa como **produto em produção**, não como protótipo.

