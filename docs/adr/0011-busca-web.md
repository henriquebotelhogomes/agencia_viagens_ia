# ADR-0011 — Busca web dos agentes

- **Status**: Aceita (implementada)
- **Data**: 2026-07-29
- **Contexto do PRD**: D11

## Contexto e problema

O agente de Logística usava o **`SerperDevTool`** (Serper) para buscar preços
reais de voos e hotéis. O Serper devolve a **SERP crua do Google**: títulos,
links e snippets curtos.

Isso gera dois custos indiretos:

1. **Tokens desperdiçados**: o agente precisa interpretar snippets fragmentados,
   às vezes disparando buscas adicionais para completar a informação.
2. **Risco de alucinação**: com informação parcial, o modelo tende a preencher
   lacunas.

Havia também um problema de sustentabilidade: os 2.500 créditos gratuitos do
Serper são **únicos** — ao esgotarem, viram custo fixo.

## Opções consideradas

### 1. Tavily

- ✅ Desenhado **para agentes**: extrai e limpa o conteúdo das páginas, ranqueia
  por relevância e pode sintetizar
- ✅ Free tier de **1.000 créditos/mês renováveis**
- ✅ `TavilySearchTool` nativo no CrewAI
- ❌ Menos "cru" — se o agente precisar da SERP literal, não é o ideal

### 2. Manter Serper

- ✅ Já integrado e funcionando
- ❌ Créditos gratuitos não renovam
- ❌ Agente gasta tokens interpretando resultado bruto

### 3. Exa

- ✅ Busca semântica de qualidade
- ❌ Free tier menos generoso; menos integrado ao CrewAI

## Decisão

**Tavily**, via `TavilySearchTool` do CrewAI, com `max_results=5`.

## Consequências

### Positivas

- Menos tokens por busca: o agente recebe conteúdo já extraído e relevante.
- Free tier renovável mensalmente — sustentável para uma demo contínua.
- Menor tendência à alucinação, pois a informação chega mais completa.
- Validado com busca real: 4,2 KB de conteúdo processado retornados.

### Negativas

- Uma chave a mais no `.env`.
- 1.000 créditos/mês é um limite real: cada execução consome ao menos uma busca.
  Mitigação planejada: cachear resultados de busca em Redis com TTL de horas
  (ainda **não implementado**).
- Perda de acesso à SERP literal do Google, caso algum agente futuro precise dela.

### Dívida associada

- [ ] Cache Redis dos resultados de busca (reduz consumo de créditos)
- [ ] `SERPER_API_KEY` sai da configuração quando o Streamlit for aposentado
