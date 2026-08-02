# Contribuindo

Obrigado pelo interesse! Este projeto usa **padrões verificados por ferramenta**:
se o CI passa, o código está no padrão.

## Início rápido

```bash
uv sync --group dev
cp .env.example .env          # preencha as chaves
uv run python -m scripts.check_env   # valida as integrações
uv run pre-commit install     # feedback antes do push
```

## Antes de abrir um PR

```bash
uv run ruff check src/ tests/ scripts/ alembic/
uv run ruff format src/ tests/ scripts/ alembic/ --check
uv run mypy src/ --strict
uv run pytest tests/ --cov=src
uv run mkdocs build --strict    # requer: uv sync --group docs

cd frontend
npm ci
npm run typecheck
npm run lint
npm run test:cov
npm run build
npm run e2e
```

## Definition of Done

- [ ] Tem teste (de regressão, se for correção de bug)
- [ ] Todos os gates acima passam
- [ ] Cobertura ≥ 90%
- [ ] Erros tratados com log estruturado (nunca `except: pass`)
- [ ] Documentação atualizada **no mesmo PR**
- [ ] Título do commit em [Conventional Commits](https://www.conventionalcommits.org/pt-br/)

## Documentação completa

O guia detalhado — nomenclatura, tipagem, docstrings, code smells banidos,
regras de teste — está na documentação técnica:

📖 **[Guia de contribuição](docs/guides/contributing.md)**

Outros pontos de partida úteis:

| Documento | Conteúdo |
| --------- | -------- |
| [Setup local](docs/guides/setup.md) | Ambiente, chaves, troubleshooting |
| [Arquitetura](docs/architecture/overview.md) | Visão geral e diagramas C4 |
| [ADRs](docs/adr/index.md) | Decisões arquiteturais e trade-offs |
| [`PRD.md`](PRD.md) | Escopo, decisões de produto e roadmap |

## Reportando problemas

Abra uma issue com: comportamento esperado, comportamento observado, passos para
reproduzir e a saída de `uv run python -m scripts.check_env` (o script **não**
expõe segredos).
