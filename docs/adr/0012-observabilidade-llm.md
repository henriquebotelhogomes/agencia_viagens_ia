# ADR-0012 — Observabilidade de LLM

- **Status**: Aceita (implementada)
- **Data**: 2026-07-29
- **Contexto do PRD**: D12, S4

## Contexto e problema

Quando um roteiro saía ruim ou caro, não havia como investigar: nenhum registro
de quais prompts foram enviados, quantos tokens cada agente consumiu, qual
fallback disparou ou onde estava a lentidão.

Pior: o painel "FinOps" era **fictício** — estimava custo a partir do
**comprimento dos logs** (`len(logs) * 0.55` tokens). Uma métrica de custo
inventada é pior que não ter métrica, porque transmite falsa confiança.

## Opções consideradas

### 1. Langfuse Cloud (Hobby free)

- ✅ 50k observações/mês grátis
- ✅ Callback nativo do litellm (`success_callback=["langfuse"]`) — integração
  de poucas linhas
- ✅ Trace por execução: prompt, resposta, tokens, custo, latência, erro
- ✅ Base para evals comparativos entre modelos
- ❌ Dados em serviço terceiro (região EU ou US, configurável)

### 2. Langfuse self-hosted

- ✅ Controle total dos dados
- ❌ Exige PostgreSQL **e** ClickHouse (~US$ 15-25/mês no Render) — infra
  desproporcional para um portfólio

### 3. Apenas OpenTelemetry + logs estruturados

- ✅ Padrão aberto, sem serviço específico de LLM
- ❌ Não entende semântica de LLM: prompts, tokens e custo exigiriam
  instrumentação manual e uma UI própria para visualizar

### 4. Adiar

- ❌ Mantém o FinOps fictício e o debug às cegas

## Decisão

**Langfuse Cloud** (free tier) para tracing de LLM + **FinOps com tokens reais**
do `CrewOutput.token_usage`.

A heurística antiga sobrevive **apenas** para cache hit, onde não houve execução
de LLM e o custo é genuinamente zero.

As variáveis do Langfuse são exportadas para o ambiente por
`configure_llm_runtime()`, porque o callback do litellm lê a configuração de lá.

## Consequências

### Positivas

- Debug real: é possível ver exatamente o que cada agente perguntou e recebeu.
- **FinOps honesto**: medição real de 8.430 tokens numa execução → economia de
  US$ 0,105 vs GPT-4o. Números que sustentam a narrativa.
- Base pronta para os evals comparativos entre modelos (Fase 3).
- Se as chaves não estiverem configuradas, o tracing simplesmente não é ativado —
  a aplicação segue normal.

### Negativas

- **`totalCost` fica zero para modelos do OpenCode Go**: é endpoint custom, e o
  Langfuse não conhece a tabela de preços dele. Os tokens são capturados
  corretamente; o custo vem do nosso cálculo. Limitação documentada, não resolvida.
- Prompts (que podem conter o briefing do usuário) trafegam para o Langfuse —
  relevante para a política de privacidade.
- **Pegadinha operacional**: as chaves são vinculadas à região. Usar
  `cloud.langfuse.com` com chaves da região US retorna **401** silencioso. O
  `scripts/check_env.py` detecta isso.
- O flush do callback é assíncrono: um processo que encerra imediatamente após a
  chamada pode perder o trace.
