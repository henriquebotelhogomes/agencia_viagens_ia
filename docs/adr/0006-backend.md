# ADR-0006 — Backend de API

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D6

## Contexto e problema

Com a decisão de trocar o Streamlit por Next.js ([ADR-0005](0005-frontend.md)),
é preciso uma API HTTP entre a interface e o núcleo de domínio. O núcleo é Python
(CrewAI, litellm) e já está desacoplado da apresentação.

## Opções consideradas

### 1. FastAPI + Pydantic v2

- ✅ Reaproveita 100% do `src/` existente — zero reescrita do domínio
- ✅ Async nativo (importante para SSE e I/O de LLM)
- ✅ OpenAPI gerada automaticamente → habilita testes de contrato
- ✅ Pydantic v2 já é usado na configuração e nos modelos do projeto
- ❌ Python é mais lento que Go/Node para I/O puro (irrelevante aqui: o gargalo
  são os 50s de LLM)

### 2. Reescrita em Node.js (Nest/Express)

- ✅ Uma linguagem só no projeto (com o frontend)
- ❌ Reescrever toda a orquestração CrewAI — o ecossistema de agentes em Python
  é significativamente mais maduro
- ❌ Descarta o núcleo já testado

### 3. Reescrita em Go

- ✅ Performance e binário único
- ❌ Mesmo problema: não há equivalente maduro do CrewAI

## Decisão

**FastAPI + Pydantic v2 (Python 3.12)**, reaproveitando `src/` como núcleo de
domínio.

Contratos do MVP:

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| `POST` | `/v1/executions` | Cria execução (202 + `Idempotency-Key`) |
| `GET` | `/v1/executions/{id}` | Estado, resultado e custo |
| `GET` | `/v1/executions/{id}/stream` | SSE de progresso |
| `GET` | `/v1/itineraries/{id}/geojson` | Locais para o mapa |
| `GET` | `/v1/finops/summary` | Agregado de custo |

Padrões: versionamento em `/v1`, erros no formato **RFC 9457**
(`application/problem+json`), idempotência onde aplicável.

## Consequências

### Positivas

- O trabalho da Fase 0 (injeção de dependência, inicialização lazy, `Settings`
  injetável) foi feito exatamente para este momento: os serviços já são
  compatíveis com `Depends()`.
- OpenAPI automática habilita schemathesis (testes de contrato) sem esforço extra.
- Async nativo permite SSE sem gambiarra.

### Negativas

- Duas stacks de runtime (Python + Node) para operar e atualizar.
- A geração continua sendo processo longo — a API sozinha não resolve; exige o
  worker ([ADR-0007](0007-fila-worker.md)).
- `settings = get_settings()` no fim do `config.py` ainda existe por
  compatibilidade com o Streamlit; deve sair quando a API assumir.
