# ADR-0015 — Hospedagem: Heroku em vez de Render

- **Status**: Aceita
- **Data**: 2026-07-30
- **Supersede**: [ADR-0003](0003-hospedagem.md)
- **Contexto do PRD**: D3

## Contexto e problema

O [ADR-0003](0003-hospedagem.md) escolheu o **Render** partindo de duas
premissas: plano gratuito suficiente para um portfólio e Blueprint declarativo.
Ao preparar o deploy da Fase 1, três restrições do free tier invalidaram a
primeira premissa:

| Restrição verificada na documentação | Efeito sobre a arquitetura |
| ------------------------------------ | -------------------------- |
| Free instances existem apenas para *web services*, Postgres e Key Value — [não para background workers](https://render.com/docs/free) | O worker do [ADR-0014](0014-fila-saq.md) não tem onde rodar sem custo |
| *"Free Render Postgres databases expire 30 days after creation"*, com 14 dias de carência antes da **exclusão dos dados** | Persistência ([ADR-0008](0008-persistencia.md)) tem prazo de validade |
| *"The pre-deploy command is available for **paid** web services"* | Migrations não podem rodar como etapa isolada do deploy |

Manter o Render no plano gratuito exigiria duas concessões arquiteturais:
acoplar o worker ao processo da API (perdendo o isolamento que motivou o
ADR-0007) e conviver com um banco que se apaga sozinho. Nenhuma delas é
defensável num projeto cujo objetivo é demonstrar arquitetura de produção
([ADR-0001](0001-posicionamento.md)).

Um dado novo mudou o espaço de soluções: o autor foi aprovado no **GitHub
Student Developer Pack**, que inclui crédito em provedores de nuvem.

## Opções consideradas

Ofertas de hospedagem ativas no pack, verificadas em 30/07/2026:

| Provedor | Crédito | Prazo | Adequação |
| -------- | ------- | ----- | --------- |
| **Heroku** | **US$ 13/mês** | **24 meses** | Worker dyno, Postgres e Redis gerenciados de origem |
| DigitalOcean | US$ 200 | **encerra 31/07/2026** | Programa sendo descontinuado — inviável construir sobre |
| Azure | US$ 100 | 12 meses | Cobre o custo, mas exigiria reescrever todo o deploy em App Service + Bicep/ARM |

### 1. Permanecer no Render com worker embutido

- ✅ Custo zero e nenhuma mudança de plataforma
- ❌ Worker no mesmo processo da API: um roteiro em geração compete por CPU com
  o tráfego HTTP, exatamente o que a fila deveria evitar
- ❌ Banco apagado em 30 dias — a demo perde o histórico de execuções e custos

### 2. Render em plano pago

- ✅ Arquitetura intacta
- ❌ ~US$ 13/mês do próprio bolso, sem contrapartida sobre a opção 3

### 3. Heroku com o crédito de estudante

- ✅ **Worker dyno é cidadão de primeira classe** — `run.worker` no manifesto
- ✅ Postgres permanente (Essential-0, 1 GB)
- ✅ *Release phase* roda migrations em qualquer plano, com **rollback
  automático**: se `alembic upgrade head` falhar, a versão anterior segue no ar
- ✅ Custo real coberto por 24 meses:

  | Componente | Plano | Custo |
  | ---------- | ----- | ----- |
  | web + worker dynos | Eco (pool compartilhado de 1.000 h) | US$ 5 |
  | PostgreSQL | Essential-0 | US$ 5 |
  | Redis | Key-Value Mini | US$ 3 |
  | | **Total** | **US$ 13/mês** |

- ✅ O Eco adormece web **e** worker juntos após 30 min sem tráfego, então o pool
  de 1.000 h cobre ~500 h de atividade real por mês — muito acima da demanda de
  um portfólio
- ❌ Container stack **não faz cache de layers**: cada deploy rebuilda a imagem
- ❌ Cold start após o adormecimento (mesmo comportamento do Render free)
- ❌ Crédito tem prazo; ao fim dos 24 meses a decisão precisa ser revisitada

### 4. Azure for Students

- ✅ Crédito maior por mês do que o consumo previsto
- ❌ Reescrever o deploy inteiro para ganhar 12 meses em vez de 24

## Decisão

**Heroku**, container stack, declarado em [`heroku.yml`](https://github.com/henriquebotelhogomes/agencia_viagens_ia/blob/master/heroku.yml).

Uma única imagem serve os três papéis (`web`, `worker` e `release`), porque sem
cache de layers cada imagem adicional custaria um build completo.

O Blueprint do Render foi **removido** em vez de mantido como alternativa: uma
configuração de deploy que ninguém executa apodrece silenciosamente. A
portabilidade real está preservada onde importa — a aplicação continua sendo um
container 12-Factor que lê tudo do ambiente, sem uma linha de código específica
de provedor.

## Consequências

### Positivas

- Arquitetura da Fase 1 no ar como projetada, sem concessões.
- Migrations com rollback automático, melhor do que o `preDeployCommand` que o
  plano gratuito do Render negava.
- Dados persistentes de verdade — o painel de FinOps acumula histórico real.

### Negativas

- Deploy mais lento pela ausência de cache de layers.
- Dependência de um crédito com prazo: **revisitar até julho de 2028**.
- Atualizações de segurança da imagem base exigem rebuild explícito (no
  buildpack seriam automáticas) — mitigado pelo Dependabot já ativo.

## Ajustes técnicos exigidos pela plataforma

Descobertos ao ler a documentação, antes do primeiro deploy:

| Achado | Tratamento |
| ------ | ---------- |
| Key-Value Store usa `rediss://` com **certificado self-signed**; `redis-py` recusa a conexão | [`src/services/redis_client.py`](../reference/services.md) centraliza a criação de clientes e desabilita apenas a verificação da cadeia, preservando a cifra |
| `DATABASE_URL` chega como `postgres://`, que o SQLAlchemy async não aceita | Validator em `Settings` normaliza para `postgresql+asyncpg://` |
| Postgres Essential-0 permite **20 conexões**; o padrão do projeto (5 + 10 overflow) daria 30 com dois dynos | `DB_POOL_SIZE=2` e `DB_MAX_OVERFLOW=3` no ambiente de produção |
| `EXPOSE` é ignorado; o processo web precisa escutar em `$PORT` | Comando `run.web` usa `--port $PORT` |
| Container roda com UID arbitrário e GID 0, ignorando o `USER` do Dockerfile — **o CrewAI quebrava no import** ao criar `$HOME/.local/share` para o storage do ChromaDB | `HOME=/app`, `XDG_DATA_HOME`/`XDG_CACHE_HOME` sob `/app` e `chgrp -R 0 /app && chmod -R g=u /app` (receita de UID arbitrário) |
| Conexões ociosas são encerradas em 55 s | Heartbeat de SSE já configurado em 15 s |

### Como esses achados foram encontrados

Antes do primeiro deploy, a imagem foi executada localmente **simulando a
plataforma**: `docker run --user 54321:0 -e PORT=41234`. A simulação revelou um
bug que passaria por todos os outros gates — o worker não subia com UID
arbitrário:

```text
PermissionError: [Errno 13] Permission denied: '/.local'
  crewai/rag/chromadb/constants.py:11 → DEFAULT_STORAGE_PATH = db_storage_path()
```

Ironia registrada: é um **efeito colateral de import** de biblioteca de terceiros,
exatamente a classe de problema que o item S1 do PRD eliminou do nosso código.

O `CREWAI_STORAGE_DIR` não resolve o caso: ele define apenas o *nome* do
diretório, mantendo `$HOME/.local/share` como base.

Dois testes no CI impedem a regressão: um roda o import do worker com
`--user 54321:0`, outro sobe a API com `$PORT` arbitrário e exige resposta em
`/health`.
