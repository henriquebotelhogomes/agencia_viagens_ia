# ADR-0002 — Gateways de LLM

- **Status**: Aceita (revisão da decisão original de gateway único)
- **Data**: 2026-07-29
- **Contexto do PRD**: D2

## Contexto e problema

O código original usava **Groq** como provedor primário, com cadeias de fallback
duplicadas e hardcoded em `agents.py` — inclusive apontando para
`gemini/gemini-1.5-flash`, um modelo já descontinuado. Ou seja: o fallback
provavelmente falharia justamente quando fosse necessário.

Restrições do contexto:

- Custo marginal deve ser próximo de zero (é um projeto de portfólio).
- O agente de Logística usa ferramentas → precisa de **function calling confiável**.
- O output final precisa de **qualidade consistente** (é o que o usuário lê).
- É desejável ter **custo por request** medido para o painel FinOps.

Ativos disponíveis: assinatura **OpenCode Go** (US$ 10/mês, ~US$ 60 de uso
incluído) e **créditos no OpenRouter** (≥ US$ 10, o que destrava 1.000 req/dia
nos modelos `:free`).

## Opções consideradas

### 1. OpenRouter como gateway único

Uma chave, ~300 modelos, com `openrouter/free` selecionando modelos gratuitos.

- ✅ Simplicidade operacional; FinOps trivial (retorna custo em USD)
- ❌ Modelos `:free` são instáveis: `429` por fila compartilhada (~20 req/min)
- ❌ O router automático pode escolher modelo **sem function calling** — quebra
  o agente de Logística
- ❌ Endpoints free podem usar prompts para treino

### 2. OpenCode Go como gateway único

- ✅ Modelos curados para agentes; capacidade reservada; zero-retention
- ❌ Orçamento **compartilhado com o uso pessoal de coding** (tetos de US$ 12/5h
  e US$ 30/semana) — um pico na demo bloquearia o trabalho do desenvolvedor
- ❌ Sem rede de segurança se o serviço cair

### 3. Chaves diretas (Gemini, Grok) via litellm

- ✅ Menor latência e custo no caminho feliz
- ❌ Gerenciar quotas, billing e fallback de cada provedor manualmente

### 4. Híbrido: Go primário + OpenRouter como fallback e tier `pro`

- ✅ Custo marginal ~US$ 0 (ambos já pagos)
- ✅ Confiabilidade do Go nos tiers de volume; OpenRouter garante o output final
- ✅ Protege a cota de coding pessoal
- ❌ Duas configurações para manter

## Decisão

**Opção 4 — híbrido com papéis definidos:**

| Tier | Primário | Fallback |
| ---- | -------- | -------- |
| `fast` | Go (`deepseek-v4-flash`) | OpenRouter (Gemini Flash pago) |
| `fast-tools` | Go (`kimi-k2.7-code`) | OpenRouter (`:free` com tools → pago) |
| `pro` | OpenRouter (Gemini Flash pago) | Go (`glm-5.2`) |

Regras que acompanham a decisão:

1. Identificadores de modelo vêm de **configuração**, nunca do código.
2. **Nunca** usar `openrouter/free` (router automático) em agente com ferramentas.
3. Failover **explícito na camada da aplicação** — ver abaixo.
4. `litellm` mantido como abstração, preservando a opção de migrar para chaves
   diretas sem mudar código.

### Detalhe de implementação descoberto na execução

A intenção era usar o parâmetro `fallbacks` do litellm. **Não funciona com o
CrewAI 1.x**: ele usa *providers nativos* (SDK do próprio provedor) para
prefixos conhecidos como `openai/`, e esse caminho rejeita opções exclusivas do
litellm (`Completions.create() got an unexpected keyword argument 'fallbacks'`).

O failover ficou então em `TravelAgents(use_fallback=True)` + retry único em
`CrewBuilder.run()`.

## Consequências

### Positivas

- Custo marginal desprezível: medição real de 8.430 tokens por roteiro com
  gasto novo < US$ 0,01.
- Tool calling confiável no agente que depende dele.
- O ponto de decisão do failover é **nosso** — habilita política de teto de
  orçamento (planejado) e é testável sem rede.
- `scripts/check_env.py` valida os IDs configurados contra os catálogos reais.

### Negativas

- Duas configurações de gateway para manter.
- O `totalCost` no Langfuse fica **zero** para modelos do Go: é endpoint custom,
  sem tabela de preços conhecida. O custo real vem do nosso cálculo por tokens.
- O teto de requests do Go (proteção da cota pessoal) ainda **não está
  implementado** — exige store persistente; planejado junto com o rate limiting.
- Catálogos de modelo mudam sem aviso: durante a implementação o
  `llama-3.3-70b:free` desapareceu do OpenRouter. Mitigado pelo script de
  diagnóstico, não eliminado.
