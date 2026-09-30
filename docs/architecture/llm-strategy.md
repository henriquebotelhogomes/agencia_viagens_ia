# Estratégia de LLM

Dois gateways com papéis definidos, tiers por tipo de tarefa, decision models
ultrarrápidos e failover explícito. Decisões registradas em [ADR-0002](../adr/0002-gateways-llm.md) e [ADR-0019](../adr/0019-decision-models-jev.md).

## Tiers & Hierarquia de Execução

| Tier | Uso | Primário | Fallback | Latência / Custo |
| ---- | --- | -------- | -------- | ---------------- |
| `tier-0` (Decisão / Guardrail) | Triagem de briefing, estilo e guardrail | OpenRouter (`typesafe/jev-latest`) | Pydantic local | <50ms · Saída US$ 0,00 |
| `fast` | Guia Local, extração de POIs | OpenCode Go (`deepseek-v4.1-flash`) | Gemini 3.8 Flash | Alta vazão · Cota inclusa |
| `fast-tools` | Logística (busca web Tavily) | OpenCode Go (`kimi-k2.7-code`) | OpenRouter (`:free` com tools) | Tool calling confiável |
| `pro` | Arquiteto de Roteiros | Gemini 3.8 Flash / Pro | OpenCode Go (`deepseek-v4-pro`) | Máxima consistência |

Todos os identificadores vêm de **configuração** (`LLM_MODEL_*`,
`LLM_FALLBACK_*`), nunca do código — trocar de modelo não exige deploy de código.

!!! tip "Decision Models Especializados (Jev First — ADR-0019)"
    Para tarefas puramente de decisão, categorização discreta (`Choice`) ou validação
    booleana (`Noul`), o **Jev (`typesafe/jev-latest`)** é priorizado sobre LLMs de chat.
    Com latência sub-50ms e **US$ 0,00 por output token**, ele protege o worker contra
    entradas inválidas ou maliciosas com custo marginal zero.

!!! warning "Modelos mudam de catálogo dinamicamente"
    Conforme documentado no inventário global de recursos (`resources.md`), modelos
    gratuitos com a tag `:free` no OpenRouter têm alta rotatividade. Sempre consulte a
    coleção oficial em [openrouter.ai/collections/free-models](https://openrouter.ai/collections/free-models)
    para verificar quais modelos estão ativos no momento. O script `scripts/check_env.py`
    valida os IDs configurados contra o catálogo real.

## Divisão de papéis entre gateways

=== "OpenCode Go (primário)"

    - Endpoint OpenAI-compatible
    - Modelos open curados **para agentes** — tool calling confiável
    - Capacidade reservada: sem fila nem `429` de concorrência
    - **Zero-retention**: prompts não são usados para treino
    - Orçamento incluso na assinatura (~US$ 60/mês de uso)

    !!! danger "Orçamento compartilhado"
        A cota do Go é a mesma usada para desenvolvimento pessoal (tetos de
        US$ 12/5h e US$ 30/semana). Um pico na demo **não pode** consumir a cota
        de trabalho — daí o failover e o teto de requests planejado.

=== "OpenRouter (pro + rede de segurança)"

    - Retorna **custo em USD por request** (base do FinOps)
    - Acesso a modelos proprietários (Gemini, Grok) quando a consistência do
      output final importa
    - ~300 modelos para experimentação e evals comparativos
    - Créditos pré-pagos, independentes da assinatura do Go

## Failover: por que é explícito

A intenção inicial era usar o parâmetro `fallbacks` do litellm. **Não funciona
com o CrewAI 1.x**:

```python
# ❌ Falha com: Completions.create() got an unexpected keyword argument 'fallbacks'
LLM(model="openai/deepseek-v4-flash", api_base=..., fallbacks=[...])
```

O CrewAI usa **providers nativos** (SDK do próprio provedor) para prefixos
conhecidos como `openai/`, e só cai no litellm para prefixos desconhecidos. O
caminho nativo não aceita opções exclusivas do litellm.

A solução ficou melhor que o plano original:

```python
# ✅ Failover na camada da aplicação
agents = TravelAgents(settings, use_fallback=True)  # reaponta todos os tiers
```

`CrewBuilder.run()` captura a exceção, reconstrói a crew em modo fallback e
tenta **uma** vez. Ganhos colaterais:

1. O ponto de decisão é nosso — permite aplicar política (teto de orçamento).
2. É testável sem rede (3 testes cobrem os cenários de failover).
3. Sem risco de loop: já em fallback, a falha propaga.

## Degradação sem chave

| Configuração | Comportamento |
| ------------ | ------------- |
| Go + OpenRouter | Estratégia completa (primário + failover) |
| Apenas OpenRouter | `use_fallback` ativado automaticamente |
| Apenas Go | Funciona, sem rede de segurança |
| Nenhum | Falha explícita na primeira chamada |

## Custo

Medição real (roteiro de 2 dias): **8.430 tokens** → economia de **US$ 0,105**
comparada ao GPT-4o. Como os tiers baratos rodam no Go (assinatura já paga), o
gasto marginal por roteiro fica **abaixo de US$ 0,01**.

Ver [FinOps](../operations/finops.md) para a metodologia de cálculo.
