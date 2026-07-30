# ADR-0003 — Hospedagem

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D3

## Contexto e problema

A arquitetura alvo tem 5 componentes: frontend, API, worker, PostgreSQL e Redis.
O deploy atual era um único serviço no Render (free tier). Era preciso decidir se
a stack ficaria concentrada ou distribuída entre provedores especializados.

## Opções consideradas

### 1. Vercel (frontend) + Render (backend)

- ✅ Vercel é o melhor lugar para Next.js: edge network, CDN, previews por PR
- ❌ Dois dashboards, dois billings, dois modelos de configuração
- ❌ Latência extra entre frontend e API (regiões diferentes)

### 2. Tudo no Render

- ✅ Um provedor: web services, background worker, Postgres e Key Value
- ✅ `render.yaml` (Blueprint) versionado = IaC auditável no repositório
- ✅ Comunicação interna entre serviços, sem sair para a internet
- ❌ Sem edge/CDN nativo; cold start no free tier

### 3. Containers próprios (VPS ou Fly.io)

- ✅ Controle total e aprendizado de infraestrutura
- ❌ Trabalho operacional (TLS, backups, monitoring) desproporcional ao objetivo

## Decisão

**Tudo no Render**, declarado em `render.yaml`.

Para um projeto de portfólio ([ADR-0001](0001-posicionamento.md)), simplicidade
operacional e um único ponto de configuração valem mais que a performance de
edge. O Blueprint versionado também é um artefato demonstrável de IaC.

## Consequências

### Positivas

- Um único `render.yaml` descreve toda a infraestrutura.
- Serviços conversam pela rede interna do Render (menor latência, sem egress).
- Billing e observabilidade de plataforma centralizados.

### Negativas

- Sem CDN/edge: o TTFB do frontend será maior que na Vercel. Mitigável com cache
  HTTP e, se necessário, um CDN na frente.
- Cold start no free tier: a primeira requisição após inatividade pode levar
  segundos. Mitigado com healthcheck e, para demos agendadas, upgrade pontual.
- Migrar o frontend para a Vercel depois é simples (é um serviço isolado), então
  a decisão é reversível a baixo custo.
