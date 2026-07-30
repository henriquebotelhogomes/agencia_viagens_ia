# ADR-0014 — Fila async: SAQ em vez de Arq

- **Status**: Aceita
- **Data**: 2026-07-29
- **Supersede**: [ADR-0007](0007-fila-worker.md)
- **Contexto do PRD**: D7

## Contexto e problema

O [ADR-0007](0007-fila-worker.md) escolheu o **Arq** como fila async, com o
argumento de reusar o Redis existente. Ao implementar, a resolução de
dependências falhou:

```text
arq==0.28.0 depends on redis[hiredis]>=4.2.0,<6
o projeto depende de redis>=7.4,<8.0
→ requisitos insatisfazíveis
```

Todas as versões do Arq travam o `redis` em `<6`. O projeto usa `redis 7.4`, e o
`redis` é **dependência direta nossa** (nada transitivo o exige), usado no cache
de roteiros e de geocoding.

## Opções consideradas

Levantamento das restrições reais no PyPI:

| Biblioteca | Restrição de `redis` | Async-nativo | Compatível com 7.x |
| ---------- | -------------------- | ------------ | ------------------ |
| `arq` 0.28 | `>=4.2,<6` | ✅ | ❌ |
| **`saq` 0.26.4** | `>=4.2,<8.0` | ✅ | ✅ |
| `taskiq-redis` 1.2.3 | `>=8.0,<9` | ✅ | ❌ (exige redis 8+) |
| `dramatiq` 2.2.0 | `>=4.0,<9.0` | ❌ (sync) | ✅ |

### 1. Manter Arq e rebaixar `redis` para `<6`

- ✅ Preserva a decisão original; Arq é conhecido
- ❌ Rebaixar uma dependência direta por causa da fila inverte a prioridade
- ❌ Trava o projeto numa linha antiga do `redis-py`, criando atrito futuro
  (correções de segurança, novas features)

### 2. SAQ (Simple Async Queue)

- ✅ Compatível com `redis` 7.x
- ✅ Async-nativo, API minimalista, semelhante em espírito ao Arq
- ✅ Suporta **PostgreSQL como broker** — caminho para eliminar a criticidade do
  Redis apontada nas consequências do ADR-0007
- ✅ Traz uma UI web de monitoramento de jobs
- ❌ Comunidade menor que a do Arq

### 3. taskiq-redis

- ❌ Exige `redis>=8.0`, versão muito recente; empurraria o problema para o outro
  extremo

### 4. dramatiq

- ❌ Síncrono — descartado pelo mesmo motivo do Celery no ADR-0007

## Decisão

**SAQ** (`saq[redis]`), mantendo `redis 7.x`.

O critério é o mesmo do ADR-0007 (fila async sobre o Redis existente); apenas a
biblioteca muda, por incompatibilidade de versão descoberta na implementação.
Toda a arquitetura de execução permanece: job enfileirado pela API, worker
consumindo, progresso publicado via pub/sub e relay por SSE.

## Consequências

### Positivas

- Sem rebaixamento de dependência: o `redis` continua atualizado.
- API de jobs async e enxuta, mantendo o desenho previsto.
- Opção futura de usar Postgres como broker, reduzindo a criticidade do Redis.
- UI de monitoramento de jobs sem custo adicional.

### Negativas

- Comunidade e material de referência menores que os do Arq — mais leitura do
  código-fonte quando algo fugir do caminho comum.
- Decisão tomada por restrição de empacotamento, não por superioridade técnica
  intrínseca; se o Arq atualizar o pin do `redis`, vale reavaliar.

### Lição registrada

Pinar dependências com teto de major (item S13 do PRD) **expôs** este conflito na
resolução, em vez de deixá-lo aparecer como erro de runtime. O incômodo do lock
falhando foi, na prática, um ganho.
