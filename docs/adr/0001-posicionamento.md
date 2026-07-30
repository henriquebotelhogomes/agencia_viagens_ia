# ADR-0001 — Posicionamento do produto

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D1

## Contexto e problema

O repositório existia como projeto de portfólio com Streamlit + CrewAI. A
modernização exigia definir **para quem** o produto existe — a resposta muda
radicalmente o escopo: um SaaS real precisa de billing, multi-tenancy e
compliance; um portfólio precisa de excelência técnica demonstrável.

Decidir isso primeiro evita construir infraestrutura que ninguém vai usar.

## Opções consideradas

### 1. Portfólio de elite

Demonstrar maturidade de engenharia (arquitetura, observabilidade, FinOps,
testes) para recrutadores técnicos e clientes. Escopo enxuto.

- ✅ Foco total em qualidade técnica visível
- ✅ Sem custo de infraestrutura ociosa
- ✅ Permite profundidade em vez de amplitude
- ❌ Sem validação de mercado real

### 2. SaaS real com usuários

Lançar com auth, planos pagos (Stripe), LGPD/GDPR completo.

- ✅ Validação de mercado
- ❌ Escopo 3-4x maior; billing e compliance consomem semanas
- ❌ Custo de infra e suporte sem receita garantida
- ❌ Dilui o foco técnico que o portfólio precisa demonstrar

### 3. Híbrido evolutivo

Portfólio production-grade com multi-tenancy e billing *desenhados* mas não
implementados.

- ✅ Prepara terreno para virar SaaS
- ❌ Risco de "arquitetura especulativa": abstrações para requisitos que podem
  nunca chegar

## Decisão

**Portfólio de elite.**

O objetivo é demonstrar excelência de engenharia. Isso define os *non-goals*
explicitamente: billing, multi-tenancy real, autenticação de usuários,
white-label e API pública ficam **fora de escopo** nesta fase.

Em compensação, tudo que entra no escopo é feito em nível de produção:
observabilidade real, FinOps com dados medidos, gates de qualidade no CI,
container non-root, defesa contra prompt injection.

## Consequências

### Positivas

- Foco: cada hora vai para qualidade técnica visível, não para plumbing de billing.
- Escopo defensável: os non-goals estão documentados, evitando *scope creep*.
- Decisões de infra podem ser pragmáticas (free tiers) sem culpa.

### Negativas

- Sem feedback de usuários reais, algumas decisões de UX permanecem hipóteses.
- A ausência de autenticação exige mitigação para abuso da demo pública
  (ver [ADR-0004](0004-autenticacao.md)).
- Se o projeto virar SaaS depois, auth e multi-tenancy serão retrofit — aceito
  conscientemente, pois a arquitetura desacoplada reduz o custo dessa mudança.

### Gatilho de revisão

Se houver intenção de monetizar ou onboarding de usuários reais, este ADR deve
ser substituído e o PRD revisado por completo.
