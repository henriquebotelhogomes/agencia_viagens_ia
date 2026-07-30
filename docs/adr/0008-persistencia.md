# ADR-0008 — Persistência

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D8

## Contexto e problema

Hoje o **Redis é o único armazenamento**, com TTL de 24h. Consequência: os
roteiros gerados **evaporam**. Não há histórico, não há como compartilhar um
roteiro por link, não há dados para o painel FinOps agregado nem base para evals.

Um roteiro é um **ativo do usuário**, não um resultado de cache.

## Opções consideradas

### 1. PostgreSQL + Redis (cada um no seu papel)

- ✅ Durabilidade e consultas relacionais no Postgres
- ✅ Redis volta a ser cache, fila e pub/sub (o que faz bem)
- ✅ `pgvector` habilita cache semântico depois, sem novo serviço
- ❌ Um serviço a mais para operar; migrations para manter

### 2. Manter apenas Redis

- ✅ Simplicidade máxima
- ❌ Sem durabilidade, histórico ou consultas analíticas
- ❌ Persistir dado de negócio em cache é uso indevido da ferramenta

### 3. MongoDB

- ✅ Schema flexível para o roteiro (documento)
- ❌ As entidades são naturalmente relacionais (`Execution` → `Itinerary` →
  `ItineraryVersion`)
- ❌ Sem busca vetorial nativa no free tier equivalente ao `pgvector`

### 4. SQLite

- ✅ Zero infraestrutura
- ❌ Incompatível com múltiplas instâncias (API + worker escrevendo)
- ❌ Filesystem efêmero no Render

## Decisão

**PostgreSQL** (Render Postgres) para dado de negócio, **Redis** para cache,
fila, pub/sub e rate limiting.

Entidades iniciais:

| Entidade | Papel |
| -------- | ----- |
| `Execution` | Uma rodada de orquestração: estado, custo, latência, trace |
| `Itinerary` + `ItineraryVersion` | Saída versionada (permite refinamento) |
| `ItineraryItem` | Dia/atividade com proveniência e geolocalização |
| `UsageRecord` | Tokens e custo por chamada (base do FinOps) |

Acesso via **SQLAlchemy 2.0 async** + **Alembic** para migrations.

## Consequências

### Positivas

- Roteiros deixam de ser efêmeros: histórico, compartilhamento e refinamento
  passam a ser possíveis.
- `UsageRecord` transforma o FinOps de "por execução" em análise agregada.
- `pgvector` no futuro habilita **cache semântico** (reaproveitar roteiros
  "parecidos o suficiente"), aumentando o hit ratio sem novo serviço.

### Negativas

- Mais um componente de infraestrutura: backups, migrations e connection pooling
  passam a ser responsabilidade nossa.
- O free tier do Render Postgres tem limite de armazenamento e expira após um
  período — exige atenção para uma demo de longa duração.
- Migrations mal planejadas podem gerar downtime; mitigado com Alembic e revisão
  em PR.
