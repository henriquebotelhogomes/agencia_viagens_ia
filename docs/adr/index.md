# Decisões de arquitetura (ADRs)

Registro das decisões arquiteturais no formato
[MADR](https://adr.github.io/madr/). Cada ADR é **imutável**: se uma decisão
muda, cria-se um novo ADR que supersede o anterior.

## Por que ADRs

Código mostra *o que* foi feito. ADRs mostram *por que* — e, sobretudo, **o que
foi descartado e sob qual critério**. É o registro que permite a um novo membro
(ou ao próprio autor meses depois) entender se uma decisão ainda faz sentido
quando o contexto muda.

## Índice

| # | Decisão | Status | Escolha |
| - | ------- | ------ | ------- |
| [0001](0001-posicionamento.md) | Posicionamento do produto | Aceita | Portfólio de elite |
| [0002](0002-gateways-llm.md) | Gateways de LLM | Aceita | OpenCode Go primário + OpenRouter |
| [0003](0003-hospedagem.md) | Hospedagem | Substituída por [ADR-0015](0015-hospedagem-heroku.md) | Tudo no Render |
| [0004](0004-autenticacao.md) | Autenticação | Aceita | Adiada (rate limit por IP) |
| [0005](0005-frontend.md) | Framework de frontend | Aceita | Next.js 15 substitui Streamlit |
| [0006](0006-backend.md) | Backend de API | Aceita | FastAPI + Pydantic v2 |
| [0007](0007-fila-worker.md) | Fila e worker | Substituída por [ADR-0014](0014-fila-saq.md) | Arq |
| [0008](0008-persistencia.md) | Persistência | Aceita | PostgreSQL + Redis |
| [0009](0009-mapas.md) | Mapas | Aceita | MapLibre GL JS |
| [0010](0010-geocoding.md) | Geocoding | Aceita | Geoapify + cache Redis |
| [0011](0011-busca-web.md) | Busca web dos agentes | Aceita | Tavily |
| [0012](0012-observabilidade-llm.md) | Observabilidade de LLM | Aceita | Langfuse Cloud |
| [0013](0013-documentacao-viva.md) | Documentação viva | Aceita | MkDocs Material |
| [0014](0014-fila-saq.md) | Fila async | Aceita | SAQ (supersede ADR-0007) |
| [0015](0015-hospedagem-heroku.md) | Hospedagem | Aceita | Heroku com crédito Student (supersede ADR-0003) |
| [0016](0016-i18n.md) | Internacionalização | Aceita | Conteúdo i18n; interface somente em português |
| [0017](0017-versionamento-roteiro.md) | Versionamento de roteiro | Aceita | Linhagem root/parent, rollback append-only, diff client-side |

## Formato

Cada ADR segue esta estrutura:

```markdown
# ADR-NNNN — Título

- **Status**: Proposta | Aceita | Substituída por ADR-XXXX | Descartada
- **Data**: AAAA-MM-DD
- **Contexto do PRD**: Dx

## Contexto e problema
## Opções consideradas
## Decisão
## Consequências (positivas e negativas)
```

## Como criar um novo ADR

1. Copie a estrutura acima em `docs/adr/NNNN-titulo-curto.md`.
2. Registre as opções **realmente** consideradas, com o motivo do descarte.
3. Seja honesto nas consequências negativas — é o que dá credibilidade.
4. Adicione ao `nav` do `mkdocs.yml` e à tabela acima.
5. Referencie o ADR no código quando a decisão não for óbvia.

!!! tip "Decisões revisadas são sinal de maturidade"
    O [ADR-0002](0002-gateways-llm.md) já é a **segunda** versão da estratégia de
    LLM — a primeira (OpenRouter como gateway único) foi revisada quando novos
    ativos ficaram disponíveis. O [ADR-0014](0014-fila-saq.md) substituiu o
    [ADR-0007](0007-fila-worker.md) por um conflito de dependências descoberto
    apenas na implementação. E o [ADR-0015](0015-hospedagem-heroku.md) substituiu
    o [ADR-0003](0003-hospedagem.md) ao descobrir, na leitura da documentação de
    preços, que o free tier escolhido não cobria a arquitetura. Revisar com
    critério é melhor que insistir por consistência.
