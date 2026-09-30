# ADR-0019 — Decision Models & Triagem Pré-Execução (Jev First)

- **Status**: Aceita
- **Data**: 2026-09-29
- **Contexto do PRD**: D2, D11
- **Alinhamento do Harness**: `~/.gemini/config/resources.md` (§1, §4) e `GEMINI.md` (§2)

## Contexto e problema

No fluxo de geração de roteiros do Voyager AI ([ADR-0006](0006-backend.md) e [ADR-0014](0014-fila-saq.md)), o endpoint HTTP `/v1/executions` valida a sintaxe do briefing com Pydantic v2 e imediatamente despacha o job para o worker assíncrono SAQ. No worker, a Trip Crew (composta por três agentes CrewAI) é instanciada para executar o planejamento completo.

Esse modelo apresenta duas limitações de latência e FinOps:

1. **Custo de Triagem Desproporcional:** Se um usuário submete uma entrada inválida, ambígua, maliciosa ou fora de escopo (ex.: prompt injection tentando forçar geração de código ou perguntas aleatórias), o sistema descobre isso apenas durante a execução dos agentes no worker, consumindo tempo de fila e tokens de LLMs conversacionais de fronteira.
2. **Latência de Modelos Conversacionais:** Avaliar viabilidade orçamentária ou classificar o estilo de viagem (Luxo, Mochilão, Família, Negócios) usando LLMs generativas tradicionais (ex.: Gemini Flash, GPT-4o) impõe latência de 2 a 5 segundos e cobra por tokens de saída para gerar texto conversacional dispensável.

## Opções consideradas

### 1. Manter validação apenas sintática (status quo)

- ✅ Código simples; valida apenas tipos, ranges e datas no Pydantic.
- ❌ Desperdiça recursos do worker e tokens ao processar briefings inviáveis ou maliciosos.
- ❌ Não calibra previamente as personas dos agentes de acordo com o estilo de viagem.

### 2. Triagem com LLM conversacional (Gemini Flash / DeepSeek Flash)

- ✅ Boa capacidade semântica para entender pedidos complexos.
- ❌ Latência de 2 a 4 segundos antes de enfileirar o job.
- ❌ Custo de geração de texto de saída (output tokens) para responder perguntas de decisão discretas.

### 3. Decision Model Especializado — Jev (`typesafe/jev-latest` via OpenRouter)

- ✅ **Modelo "System One" Nativo:** Especializado exclusivamente em tomadas de decisão estruturadas e tipadas (sem geração de texto livre conversacional).
- ✅ **Latência Ultrabaixa:** Execução sub-50ms (40x a 200x mais veloz que LLMs conversacionais de raciocínio).
- ✅ **Pricing FinOps Ótimo:** **US$ 0,00 por output tokens** (100% gratuito na saída) e apenas US$ 0,042 por 1 milhão de input tokens.
- ✅ **Primitivas Nativas de Decisão:**
  - `Noul`: Avaliação Booleana calibrada (0.0 a 1.0) para guardrails pré-execução (`IsSafeTravelRequest`).
  - `Choice`: Classificação discreta do estilo de viagem (`[Luxo, Mochilão, Família, Negócios, Romântico, Aventura]`).
  - `Score`: Calibração de viabilidade financeira (orçamento disponível vs. dias de estadia vs. destino).

## Decisão

Adotar o **Jev (`typesafe/jev-latest` via OpenRouter)** como **Tier 0 (Decision Models & Roteamento Especializado)** na arquitetura de IA:

```
[Request HTTP] 
      │
      ▼
┌───────────────┐      Inválido/Inseguro      ┌─────────────────────────┐
│ Jev (Tier 0)  │ ──────────────────────────► │ Rejeição Imediata 400   │
│ Latência <50ms│                             │ (Custo de saída $0.00)  │
└───────┬───────┘                             └─────────────────────────┘
        │ Válido + Estilo Classificado
        ▼
┌───────────────┐
│ SAQ Worker    │ ──► [Trip Crew: Guia -> Logística -> Arquiteto]
└───────────────┘
```

1. **Pre-Flight Guardrail (`Noul`):** A API valida a legitimidade do pedido antes de enfileirar no Redis/SAQ, bloqueando prompt injections e requisições fora de contexto em <50ms.
2. **Classificação de Estilo (`Choice`):** A intenção do usuário é enriquecida com o perfil exato de viagem, permitindo que a Crew personalize recomendações com maior precisão.
3. **Análise de Viabilidade (`Score`):** Se o orçamento informado for manifestamente insuficiente para o destino e período, o sistema emite um alerta prévio.

## Consequências

### Positivas

- **Feedback Imediato:** O usuário recebe validação semântica em menos de 100ms no frontend.
- **Proteção FinOps Rigorosa:** Requisições inválidas são abortadas antes de consumirem buscas no Tavily API ou invocar LLMs do OpenCode Go.
- **Custo Marginal de Saída Zero:** Como o Jev cobra US$ 0.00 em output tokens, o custo da camada de triagem é virtualmente desprezível.

### Negativas / Mitigações

- **Dependência de Conexão com OpenRouter:** Mitigada mantendo bypass local determinístico via Pydantic caso o gateway do OpenRouter apresente instabilidade ou timeout.
