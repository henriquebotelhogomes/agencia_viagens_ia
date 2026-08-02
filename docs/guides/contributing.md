# Guia de contribuição

Este projeto usa **padrões verificados por ferramenta**, não por convenção
verbal. Se o CI passa, o código está no padrão.

## Fluxo de trabalho

1. Crie um branch a partir de `master`.
2. Implemente com testes (ver [Testes](#testes)).
3. Rode os gates localmente (ou confie no pre-commit).
4. **Atualize a documentação no mesmo PR** — é parte da Definition of Done.
5. Abra o PR com título em [Conventional Commits](#commits).

## Definition of Done

Uma mudança está pronta quando:

- [x] Tem teste (unitário no mínimo; de regressão se for correção de bug)
- [x] Passa nos gates de backend, frontend e documentação aplicáveis à mudança
- [x] Mantém a cobertura ≥ 90%
- [x] Trata erros com log estruturado (nunca `except: pass`)
- [x] Documentação atualizada no mesmo PR (docstring conta)
- [x] Não introduz nenhum dos [code smells banidos](#code-smells-banidos)

## Commits

Usamos **Conventional Commits** — habilita changelog automático e leitura rápida
do histórico:

```text
feat: adiciona export de roteiro em PDF
fix: corrige escopo do retry na orquestração
refactor: extrai runtime para módulo dedicado
docs: documenta estratégia de failover de LLM
test: cobre timeout do serviço de câmbio
chore: atualiza pins de dependências
```

## Padrões de código

### Nomenclatura

- `snake_case` para funções e variáveis, `PascalCase` para classes,
  `UPPER_SNAKE` para constantes de módulo.
- Nomes revelam intenção: `itinerary_text`, nunca `data`, `tmp` ou `x`.

### Tipagem

- 100% das assinaturas públicas anotadas (`mypy --strict` garante).
- Sintaxe moderna: `X | None` (não `Optional[X]`), `list[str]` (não `List[str]`).
- `Any` só nas fronteiras com bibliotecas sem stubs (CrewAI, loguru).

### Docstrings

Padrão **Google**, com primeira linha imperativa. Decisões não óbvias citam o
item do PRD:

```python
def get_coordinates(self, location_name: str) -> tuple[float, float] | None:
    """Obtém as coordenadas (lat, lon) de um local.

    Ordem: cache Redis → Geoapify → Nominatim (fallback sem chave).

    Args:
        location_name: nome do local a resolver.

    Returns:
        Par ``(lat, lon)`` ou ``None`` quando não há resultado.
    """
```

Esses docstrings alimentam a [Referência de API](../reference/config.md) —
escrevê-los bem é o que mantém a documentação viva.

### Estrutura

- Funções curtas, responsabilidade única.
- Máximo ~3 níveis de indentação — prefira *early return* a aninhamento.
- Sem números ou strings mágicos: use constantes nomeadas
  (`MAX_EXTRACTED_LOCATIONS`) ou `Settings`.

### Code smells banidos

Todos foram erradicados na Fase 0. Reintroduzi-los reprova o PR:

| Smell | Por quê |
| ----- | ------- |
| `except: pass` silencioso | Esconde falha; impossibilita diagnóstico |
| Efeito colateral em `import` | Quebra testes e múltiplos workers |
| Singleton de módulo | Impede injeção de dependência |
| Mutar `os.environ` fora do runtime | Estado global imprevisível |
| Segredo em `str` puro | Vaza em `repr`, log e traceback — use `SecretStr` |
| Valor de negócio hardcoded | Moeda, idioma e modelo são configuração |
| Parsear saída de LLM com regex | Use schema Pydantic (structured output) |

### Fronteiras explícitas

- Dependências **injetadas** (parâmetro `settings`), nunca importadas de um
  singleton global.
- Recursos caros (LLMs, clientes HTTP) inicializados de forma **lazy**.
- Toda integração externa degrada graciosamente, com log.

## Testes

### Pirâmide

| Camada | Ferramenta | Escopo |
| ------ | ---------- | ------ |
| Unitários | pytest + pytest-mock | Domínio, 100% mockado |
| Integração | pytest | APIs reais sem chave |
| Contrato | schemathesis | OpenAPI (Fase 1) |
| E2E | Playwright | Frontend (Fase 2) |
| LLM evals | promptfoo/deepeval | Regressão de prompt (Fase 3) |

### Regras

- Padrão **AAA** (Arrange-Act-Assert), blocos separados por linha em branco.
- Nome descreve o comportamento: `test_<unidade>_<cenário>_<resultado>`.
  Exemplo real: `test_cache_disabled_when_redis_unreachable`.
- Todo caminho de erro tem teste: timeout, HTTP 5xx, resposta vazia, `None`.
- Bug corrigido ganha **teste de regressão** com comentário citando o bug.
- Fixtures compartilhadas em `conftest.py`.
- **Nunca** use chave real em teste — o fixture `isolate_secrets_from_env`
  remove as variáveis sensíveis automaticamente.

## Gates locais

O CI executa todos estes comandos. Rode os que se aplicam à sua alteração antes
de abrir o PR:

```bash
# Backend
uv run ruff check src/ tests/ scripts/ alembic/
uv run ruff format src/ tests/ scripts/ alembic/ --check
uv run mypy src/ --strict
uv run pytest tests/ --cov=src

# Frontend
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test:cov
npm run build
npm run e2e
```

## Documentação

- Páginas em `docs/`, navegação em `mkdocs.yml`.
- Decisão arquitetural nova → **novo ADR** em `docs/adr/`
  (ver [índice](../adr/index.md) para o formato).
- Diagramas em **Mermaid** dentro do próprio Markdown (versionável, sem binário).
- Rode `uv run mkdocs build --strict` antes do push: link quebrado reprova.
