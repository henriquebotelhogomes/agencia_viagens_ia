# 📚 Specs — Voyager AI (Plataforma SaaS de Planejamento de Viagens com IA)

Este diretório contém a **documentação de produto e engenharia** que reposiciona o
projeto `agencia_viagens_ia` de um repositório de portfólio para um **SaaS
profissional**, pronto para evoluir de forma incremental.

> ⚠️ **Escopo desta fase:** documentação apenas. Nenhuma linha de código de produção
> é escrita aqui. O objetivo é guiar a próxima fase de implementação com clareza
> arquitetural, de produto e de experiência.

## 🎯 Por que estes documentos existem

Recrutadores técnicos exigentes (Staff/Principal Engineers, Engineering Managers,
fundadores técnicos) avaliam projetos de portfólio por **maturidade de decisão**, não
apenas por features. Estes documentos demonstram:

- Pensamento de **produto** (problema → valor → público → monetização).
- Pensamento de **arquitetura** (trade-offs explícitos, não "stack da moda").
- Cuidado com **operação real**: observabilidade, custo (FinOps), segurança,
  escalabilidade e confiabilidade.
- **Excelência de frontend** com React e ecossistema moderno.

## 🗂️ Índice dos documentos

| # | Documento | O que responde |
|---|-----------|----------------|
| 00 | [`00-glossary.md`](./00-glossary.md) | Glossário e convenções |
| 01 | [`01-product-vision.md`](./01-product-vision.md) | Visão, proposta de valor, público-alvo, monetização |
| 02 | [`02-functional-spec.md`](./02-functional-spec.md) | Especificação funcional (features, fluxos, regras) |
| 03 | [`03-technical-spec.md`](./03-technical-spec.md) | Especificação técnica de alto nível e stack |
| 04 | [`04-architecture.md`](./04-architecture.md) | Arquitetura, componentes, fluxos e dados |
| 05 | [`05-non-functional-requirements.md`](./05-non-functional-requirements.md) | Requisitos não funcionais (SLOs, NFRs) |
| 06 | [`06-observability.md`](./06-observability.md) | Observabilidade e rastreabilidade |
| 07 | [`07-performance-scalability.md`](./07-performance-scalability.md) | Performance e escalabilidade |
| 08 | [`08-security.md`](./08-security.md) | Segurança, privacidade e compliance |
| 09 | [`09-frontend-ux.md`](./09-frontend-ux.md) | Proposta de frontend e experiência do usuário |
| 10 | [`10-roadmap.md`](./10-roadmap.md) | Roadmap de evolução por fases |
| 11 | [`11-risks-assumptions-decisions.md`](./11-risks-assumptions-decisions.md) | Riscos, premissas e ADRs |

## 🧭 Como ler

1. Comece por **`01-product-vision.md`** para entender o "porquê".
2. Siga para **`02`** e **`03`** para o "o quê".
3. Aprofunde em **`04` a `08`** para o "como" técnico.
4. Veja **`09`** para a camada de experiência.
5. Use **`10`** e **`11`** para planejar a execução e mitigar riscos.

## 📌 Estado atual (baseline) vs. visão

| Dimensão | Hoje (repositório) | Visão (SaaS) |
|----------|-------------------|--------------|
| Frontend | Streamlit (monolito) | React + Next.js, design system próprio |
| Backend | Lógica acoplada ao Streamlit | API FastAPI desacoplada + workers assíncronos |
| Multiagente | CrewAI síncrono no request | Orquestração assíncrona com streaming (SSE) |
| Persistência | Redis (cache efêmero) | PostgreSQL + Redis + object storage |
| Auth | Inexistente | OIDC/OAuth2, multi-tenant, RBAC |
| Observabilidade | Loguru + heurística FinOps | OpenTelemetry, tracing LLM, métricas, custo real |
| Deploy | Render (free) | Containers + IaC + ambientes (dev/stg/prod) |

---
*Documentação elaborada como artefato de arquitetura e produto. Versão 1.0.*

