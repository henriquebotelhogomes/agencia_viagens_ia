# 09 — Proposta de Frontend e Experiência do Usuário

> Objetivo: um frontend **impecável, moderno e memorável**, que sozinho já comunique
> qualidade de engenharia e produto. A experiência é parte do diferencial competitivo.

## 1. Princípios de UX

1. **Confiança visível** — mostrar fontes, custo e raciocínio transforma "caixa-preta" em
   ferramenta confiável.
2. **Velocidade percebida** — streaming de progresso e skeletons; nunca um spinner mudo.
3. **Foco e clareza** — uma ação principal por tela; tipografia e espaçamento generosos.
4. **Deleite com propósito** — micro-interações que orientam, não que distraem.
5. **Acessível por padrão** — WCAG 2.1 AA, teclado, contraste, `prefers-reduced-motion`.
6. **Mobile-first** — planeja-se viagem no celular tanto quanto no desktop.

## 2. Stack de frontend

| Camada | Escolha | Justificativa |
|--------|---------|---------------|
| Framework | **React 18 + Next.js 14 (App Router)** + TypeScript | RSC, streaming, SSR, SEO para páginas públicas |
| Estilo | **Tailwind CSS** + **CSS variables (design tokens)** | consistência e velocidade |
| Componentes | **shadcn/ui** + **Radix UI** | acessíveis, headless, customizáveis |
| Animação | **Framer Motion** | transições fluidas e orientadas a estado |
| Dados | **TanStack Query** + **Zustand** | cache de servidor + estado de UI mínimo |
| Formulários | **React Hook Form** + **Zod** | validação tipada compartilhada com a API |
| Mapa | **MapLibre GL / Mapbox GL** | mapas vetoriais performáticos, clustering |
| Streaming | **EventSource (SSE)** | progresso de execução em tempo real |
| Gráficos | **Recharts / visx** | painel FinOps e métricas |
| i18n | **next-intl** | PT-BR / EN |
| Testes | **Vitest** + **Testing Library** + **Playwright** | unidade + e2e |
| Qualidade | **ESLint + Prettier + Storybook** + **Lighthouse CI** | DX e regressão visual |

## 3. Design system

- **Design tokens** (cor, tipografia, espaçamento, raio, sombra, motion) em CSS variables →
  base para **tema claro/escuro** e white-label (planos Business).
- **Biblioteca de componentes** documentada no **Storybook** (sinal forte de maturidade).
- **Linguagem visual:** moderna e editorial — inspiração em "travel premium": fotografia
  generosa, tipografia confiante (ex.: *Inter/Geist* + display serif para títulos),
  paleta com acento de marca e neutros sofisticados, dark mode caprichado.
- **Acessibilidade** embutida nos componentes (foco visível, ARIA, contraste).

## 4. Arquitetura de informação (rotas)

```
/                      Landing (marketing, SEO, demo)
/login · /signup       Autenticação (OIDC + e-mail)
/app                   Dashboard (workspace)
/app/plan              Briefing de viagem (criação)
/app/executions/:id    Execução ao vivo (streaming de progresso)
/app/itineraries       Biblioteca de roteiros
/app/itineraries/:id   Roteiro (cronograma + mapa + custos + fontes)
/app/itineraries/:id/refine   Refinamento/versões
/app/finops            Painel de custos (admin)
/app/settings          Conta, workspace, membros, billing
/r/:publicId           Roteiro público (somente leitura, SEO)
```

## 5. Telas-chave (descrição de experiência)

### 5.1 Landing
- Hero com proposta de valor + **demo interativa** (gerar roteiro de exemplo sem login).
- Prova de qualidade técnica: seção "como funciona" mostrando agentes e transparência.
- Performance e SEO de ponta (RSC, imagens otimizadas).

### 5.2 Briefing de viagem
- **Formulário inteligente** em etapas leves (origem, destino, dias, interesses) com
  autocomplete e chips de interesse.
- Validação inline (Zod) e sugestões; campos avançados colapsáveis (orçamento, estilo, ritmo).
- CTA único e claro: "Planejar roteiro".

### 5.3 Execução ao vivo (o "momento mágico")
- **Timeline de agentes** atualizada via **SSE**: "Guia Local pesquisando…", "Logística
  calculando custos…", "Arquiteto montando o roteiro…".
- **Painel de raciocínio** opcional (transparência), com fontes aparecendo em tempo real.
- Skeletons do roteiro preenchendo progressivamente → reduz latência percebida.
- Botão **cancelar** sempre disponível.

### 5.4 Roteiro
- Layout **split**: cronograma dia a dia (esquerda) + **mapa interativo** sincronizado
  (direita); hover no item destaca o pin (e vice-versa).
- **Tabela de custos** clara, na moeda do workspace, com badge de proveniência por item.
- Ações: **exportar** (PDF/Markdown/.ics), **compartilhar** (link público), **refinar**.
- **Feedback** 👍/👎 + motivo, inline por item e no roteiro.

> **Entregue na Fase 2** ([FR-06](../PRD.md)): export **Markdown** — download
> direto no cliente, com bloco de proveniência no cabeçalho. PDF/.ics,
> compartilhar e refinar seguem no backlog (Q5).

### 5.5 Refinamento ✅
- Caixa de instrução (“mais barato”, “menos caminhada”) → gera **nova versão**.
- **Comparação de versões** (diff visual) e histórico.

> **Entregue** (v1.26): `refine-panel.tsx` (textarea + Zod 1–1000),
> `version-history.tsx` (badges por kind, link “Ver”, rollback),
> `version-diff.tsx` (jsdiff, linhas verde/vermelho).

### 5.6 Painel FinOps (admin)
- Gráficos de custo por dia/modelo/tenant, **cache hit ratio**, economia vs. GPT-4o.
- Demonstra cuidado com **custo operacional** — muito valorizado por avaliadores.

## 6. Padrões de estado e feedback

| Estado | Tratamento |
|--------|-----------|
| Loading | Skeletons contextuais (não spinners genéricos) |
| Streaming | Progresso incremental via SSE |
| Vazio | Empty states com orientação e CTA |
| Erro | Mensagem amigável + ação de retry; nunca stack trace |
| Degradado | Aviso não-bloqueante (ex.: "mapa indisponível, roteiro pronto") |
| Sucesso | Confirmação sutil + próximos passos |

## 7. Acessibilidade (WCAG 2.1 AA)

- Navegação completa por teclado; foco visível; ordem lógica.
- Contraste ≥ 4.5:1; suporte a leitor de tela (ARIA correto via Radix).
- `prefers-reduced-motion` respeitado nas animações.
- Formulários com labels, descrições e erros associados programaticamente.

## 8. Performance de frontend

(Ver também [`07`](./07-performance-scalability.md).)
- RSC + streaming, code splitting, lazy-load do mapa/editor.
- `next/image`, fontes otimizadas, prefetch de rotas.
- Metas de **Web Vitals**: LCP < 2.5s, INP < 200ms, CLS < 0.1, com **Lighthouse CI** no pipeline.
- **RUM** (Real User Monitoring) integrado à observabilidade.

## 9. Internacionalização e moeda

> **Decisão revisada** ([ADR-0016](../docs/adr/0016-i18n.md)): a interface é
> **somente em português**, por decisão de produto. A internacionalização vale
> para o **conteúdo**: o roteiro é gerado no idioma escolhido (pt-BR/en-US/es-ES)
> e os custos na moeda do briefing (BRL/USD/EUR/GBP). O `next-intl` previsto
> abaixo não foi adotado.

- ~~`next-intl` para PT-BR/EN; formatação de número/data/moeda por locale.~~
- Moeda de custos conforme preferência do briefing.

## 10. Qualidade e DX do frontend

- **Storybook** + testes de componentes (Vitest/Testing Library).
- **Playwright** para e2e dos fluxos críticos (briefing → execução → roteiro → export).
- **Regressão visual** (Chromatic/Storybook) opcional.
- **Contratos tipados** ponta a ponta: schema Zod/OpenAPI compartilhado entre front e API
  evita drift.

## 11. Por que isso impressiona recrutadores

- Mostra domínio do **ecossistema React moderno** (RSC, streaming, design system).
- Evidencia **UX de produto real** (estados, acessibilidade, performance medida).
- Liga frontend à **engenharia de IA** (streaming de agentes, transparência, FinOps visível)
  — uma combinação rara em portfólios.

