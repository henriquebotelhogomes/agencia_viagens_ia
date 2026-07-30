# 06 — Observabilidade e Rastreabilidade

> Diferencial-chave para recrutadores: observabilidade **de produtos de IA** é raramente
> bem-feita. Demonstrá-la sinaliza maturidade de engenharia de ponta.

## 1. Filosofia

Observabilidade não é "adicionar logs". É a capacidade de **responder perguntas novas
sobre o sistema sem fazer novo deploy**. Cobrimos os três pilares — **traces, métricas,
logs** — mais um quarto pilar específico de IA: **avaliação de qualidade (LLM eval)**.

Padrão base: **OpenTelemetry (OTel)** para instrumentação vendor-neutral; backends
intercambiáveis (Grafana Tempo/Loki/Prometheus, ou Grafana Cloud/Datadog/Honeycomb).

## 2. Rastreabilidade ponta a ponta

Cada requisição carrega um **`request_id`** e gera um **`trace_id`** propagado por todo o
caminho: BFF → API → fila → worker → cada chamada de LLM/ferramenta.

```
[Web/BFF] trace_id=abc
   └─ [API POST /executions] span
        └─ [enqueue job] span (trace_id propagado via mensagem)
             └─ [Worker run] span
                  ├─ [Agent: Guia Local] span
                  │     └─ [LLM call groq/llama-8b] span (tokens, custo, latência)
                  ├─ [Agent: Logística] span
                  │     ├─ [Tool: Serper search] span
                  │     └─ [LLM call] span
                  └─ [Agent: Arquiteto] span
                        └─ [LLM call groq/llama-70b] span
```

- O **`trace_id` é persistido na entidade `Execution`** (ver [`04`](./04-architecture.md)),
  ligando dado de negócio ↔ telemetria. Um suporte pode partir do roteiro do usuário e
  abrir o trace completo da geração.
- Propagação de contexto **através da fila** (W3C Trace Context nos headers da mensagem)
  para não "quebrar" o trace na fronteira assíncrona.

## 3. Tracing específico de LLM

Ferramenta dedicada: **Langfuse** (ou OpenLLMetry), complementando o OTel. Para cada
chamada de modelo registramos:

- prompt e resposta (com **redaction** de PII — ver [`08`](./08-security.md));
- modelo, provider, **tokens de prompt/completion**, **custo real**;
- latência, se foi **fallback**, número de retries;
- avaliação de qualidade associada (quando houver).

Isso permite responder: *"Qual agente mais consome tokens?"*, *"Qual prompt dispara mais
fallback?"*, *"O modelo 70B melhora a aprovação o suficiente para justificar o custo?"*.

## 4. Métricas

### 4.1 RED (serviços de request)
- **Rate** — req/s por rota.
- **Errors** — taxa de erro por rota/status.
- **Duration** — histograma de latência (p50/p95/p99).

### 4.2 USE (recursos)
- **Utilization / Saturation / Errors** de CPU, memória, **profundidade da fila**, pool de
  conexões do banco.

### 4.3 Métricas de domínio / IA
| Métrica | Uso |
|---------|-----|
| `executions_total{status}` | volume e taxa de sucesso/falha/cancelamento |
| `execution_duration_seconds` | SLO de geração de roteiro |
| `cache_hit_ratio` | eficiência (FinOps) |
| `llm_tokens_total{provider,model,type}` | custo e consumo |
| `llm_cost_usd_total{provider,workspace}` | FinOps por tenant |
| `llm_fallback_total{from,to}` | saúde dos providers |
| `feedback_total{rating,reason}` | qualidade percebida |
| `provider_circuit_state{provider}` | resiliência |

## 5. Logs estruturados

- **JSON** (já há base com **Loguru** em `src/utils/logger.py`), com campos padrão:
  `timestamp, level, message, trace_id, request_id, workspace_id, execution_id, component`.
- **Sem PII em texto livre**; usar redaction/hashing.
- Correlação direta com traces via `trace_id`.
- Níveis disciplinados: `DEBUG` (dev), `INFO` (eventos de negócio), `WARNING`
  (degradação), `ERROR` (falha acionável).

> O sink atual para o Streamlit (`add_streamlit_sink`) evolui para um **stream SSE** de
> progresso no novo frontend — observabilidade vira também **feature de transparência**.

## 6. FinOps como observabilidade

O `FinanceService` atual usa **heurística de tokens**. Evolução:

1. Capturar **uso real de tokens** retornado pelos providers (via LiteLLM callbacks).
2. Gravar `UsageRecord` por chamada (ver modelo em [`04`](./04-architecture.md)).
3. **Painel FinOps**: custo por execução, por tenant, por modelo, por dia; comparação
   "custo real vs. custo equivalente GPT-4o" (a narrativa de economia que já existe, agora
   baseada em dados reais).
4. **Budgets e alertas** por tenant (anti-abuso e proteção de margem).

## 7. Alertas e SLOs

- Definir **SLOs** (ver [`05`](./05-non-functional-requirements.md)) com **error budgets**.
- Alertas **baseados em sintoma** (ex.: "p95 de geração > 60s por 10min", "fallback ratio
  > 30%", "custo do tenant > budget"), não em ruído de infraestrutura.
- Política de **on-call/runbook** leve (mesmo em projeto de portfólio, documentar o runbook
  impressiona).

## 8. Qualidade de IA (LLM Evaluation)

- **Offline**: dataset de briefings de referência → execução → métricas automáticas
  (groundedness, relevância, aderência ao formato/moeda) via LLM-as-judge + checagens
  determinísticas.
- **Online**: amostragem de execuções de produção + feedback do usuário (👍/👎 + motivo).
- **Regressão**: rodar o eval set no CI quando prompts/modelos mudarem (evita "prompt drift").

## 9. Painéis (dashboards) propostos

1. **Visão de Saúde** — RED da API, fila, disponibilidade, error budget.
2. **Funil de Execução** — volume por status, duração p95, cache hit ratio.
3. **FinOps** — custo por tenant/modelo/dia, economia vs. GPT-4o.
4. **Qualidade de IA** — feedback, fallback ratio, scores de eval.
5. **Experiência (RUM)** — Web Vitals do frontend.

## 10. Privacidade na telemetria

- **Redaction** de PII antes de exportar prompts/logs.
- Retenção diferenciada: traces detalhados (curto prazo), métricas agregadas (longo prazo).
- Conformidade com [`08-security.md`](./08-security.md).

