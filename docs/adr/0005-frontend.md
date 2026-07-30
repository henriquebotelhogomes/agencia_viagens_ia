# ADR-0005 — Framework de frontend

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D5

## Contexto e problema

A interface era Streamlit. Isso traz limitações estruturais para um produto:

- **Orquestração no request**: a geração roda dentro do ciclo de execução do
  script, bloqueando por 50-90s.
- **Modelo de re-execução**: qualquer interação reexecuta o script inteiro,
  tornando estado e streaming complexos.
- **Sem controle de UX**: layout, roteamento, SEO e acessibilidade são limitados
  ao que o framework oferece.
- **Acoplamento**: o logging da aplicação precisou de um *sink* customizado só
  para exibir o raciocínio dos agentes na UI.

## Opções consideradas

### 1. Next.js 15 (App Router) + TypeScript

- ✅ SSR e streaming nativos — essenciais para mostrar progresso dos agentes
- ✅ SEO para páginas públicas (landing, roteiros compartilhados)
- ✅ Maior ecossistema: mapas, i18n, componentes, testes
- ✅ Habilidade mais demandada no mercado — relevante para portfólio
- ❌ Stack adicional (Node) e mais código que Streamlit

### 2. Remix ou SvelteKit

- ✅ Tecnicamente excelentes, DX agradável
- ❌ Ecossistema menor para as necessidades específicas (mapas, i18n, design system)
- ❌ Menor reconhecimento em processos seletivos

### 3. Angular (enterprise)

- ❌ Overhead de estrutura desproporcional para o tamanho do produto

### 4. Manter Streamlit

- ✅ Zero trabalho
- ❌ Não resolve nenhuma das limitações estruturais acima

## Decisão

**Next.js 15 (App Router) + TypeScript** como interface de produto.

Stack complementar:

| Camada | Escolha |
| ------ | ------- |
| Estilo e componentes | Tailwind CSS + shadcn/ui (design system próprio, sem lock-in) |
| Estado de servidor | TanStack Query |
| Estado de UI | Zustand (mínimo) |
| Mapas | MapLibre GL ([ADR-0009](0009-mapas.md)) |
| i18n | next-intl |
| Progresso da execução | SSE (Server-Sent Events) |

O Streamlit **não é descartado imediatamente**: continua como *playground
interno* para testar prompts e agentes, e é aposentado quando o Next.js cobrir
100% do fluxo.

## Consequências

### Positivas

- Streaming real do raciocínio dos agentes, sem o hack de sink de log.
- Controle total de UX, acessibilidade e performance (Lighthouse como gate).
- Separação clara: a UI só conhece a API HTTP, nunca o CrewAI.

### Negativas

- Duas linguagens e dois ecossistemas de dependências para manter.
- Exige a API da Fase 1 pronta antes de qualquer ganho visível — o frontend
  depende de `POST /v1/executions` e do SSE.
- Mais código para o mesmo resultado funcional inicial; o retorno vem em UX,
  performance e escalabilidade.
