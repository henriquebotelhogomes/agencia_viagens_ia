# ADR-0007 — Fila e worker

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D7

## Contexto e problema

Gerar um roteiro leva **50-90 segundos** (medição real: 50,7s). Manter isso dentro
de um request HTTP é inviável: timeouts de proxy, conexões ociosas, impossibilidade
de retry e nenhuma visibilidade de progresso.

A geração precisa virar um **job assíncrono**, com a API respondendo `202 Accepted`
imediatamente e o cliente acompanhando o progresso por SSE.

## Opções consideradas

### 1. Arq (async, sobre Redis)

- ✅ Async-nativo — combina com FastAPI e com o I/O de LLM
- ✅ Usa o Redis que **já existe** no projeto: zero infra nova
- ✅ API minimalista, fácil de entender e testar
- ❌ Ecossistema menor que Celery; menos recursos prontos (ex.: agendamento
  complexo, workflows)

### 2. Celery + Redis/RabbitMQ

- ✅ Padrão de mercado, maduro, muitos recursos
- ❌ Modelo síncrono combina mal com stack async
- ❌ Configuração significativamente mais pesada para o mesmo resultado

### 3. Temporal

- ✅ Workflows duráveis, retry sofisticado, compensação (saga)
- ❌ Overhead alto: exige servidor próprio ou serviço pago
- ❌ Complexidade injustificada para um fluxo linear de 3 etapas

## Decisão

**Arq**, usando o Redis existente como broker.

O worker consome jobs da fila, executa a crew e **publica progresso via Redis
pub/sub**; a API faz relay desses eventos para o cliente por SSE. Assim o worker
não conhece o transporte HTTP e a API não conhece a orquestração.

## Consequências

### Positivas

- Isola carga: picos de LLM (minutos) não afetam o tráfego HTTP (milissegundos).
- Habilita autoscaling por profundidade de fila.
- Retry e cancelamento de execução passam a ser possíveis.
- Nenhum serviço de infraestrutura novo (o Redis já está lá).

### Negativas

- Redis passa a ser **componente crítico** (era opcional, apenas cache). Se cair,
  não há geração de roteiro — diferente de hoje, em que a aplicação degrada.
- Mais um processo para operar e observar no Render.
- Se o produto precisar de workflows com compensação (ex.: reservas reais), o Arq
  não basta — nesse cenário, migrar para Temporal e substituir este ADR.

### Gatilho de revisão

Necessidade de workflows de longa duração com estado durável e compensação
transacional.
