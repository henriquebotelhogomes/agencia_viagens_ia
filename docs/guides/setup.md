# Setup local

## Pré-requisitos

| Ferramenta | Versão | Observação |
| ---------- | ------ | ---------- |
| Python | 3.12+ | fixado em `.python-version` |
| [uv](https://docs.astral.sh/uv/) | recente | única fonte de dependências |
| Docker | opcional | para rodar via container |

## 1. Clonar e instalar

```bash
git clone https://github.com/henriquebotelhogomes/agencia_viagens_ia.git
cd agencia_viagens_ia
uv sync --group dev
```

!!! warning "Não use `pip install -r requirements.txt`"
    O `requirements.txt` foi removido: `pyproject.toml` + `uv.lock` são a
    **única** fonte de verdade das dependências. Isso evita drift entre dois
    arquivos (ver [ADR-0013](../adr/0013-documentacao-viva.md) para o princípio
    de fonte única aplicado à documentação).

## 2. Configurar as chaves

```bash
cp .env.example .env    # PowerShell: Copy-Item .env.example .env
```

Preencha o `.env` com as chaves dos serviços. Onde obter cada uma:

| Variável | Serviço | Free tier |
| -------- | ------- | --------- |
| `OPENCODE_API_KEY` | [OpenCode Zen](https://opencode.ai/) → Go | assinatura US$ 10/mês |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai/keys) | 1.000 req/dia com ≥ US$ 10 em créditos |
| `TAVILY_API_KEY` | [Tavily](https://app.tavily.com/) | 1.000 créditos/mês |
| `GEOAPIFY_API_KEY` | [Geoapify](https://myprojects.geoapify.com/) | 3.000 req/dia |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | [Langfuse Cloud](https://cloud.langfuse.com/) | 50k observações/mês |

!!! danger "Região do Langfuse"
    Use o host da região onde o projeto foi criado
    (`https://cloud.langfuse.com` para EU, `https://us.cloud.langfuse.com` para
    US). O host errado retorna **401** mesmo com as chaves corretas.

### Validar a configuração

O projeto tem um diagnóstico que testa cada chave contra a API real, **sem
exibir segredos**:

```bash
uv run python -m scripts.check_env
```

Saída esperada:

```text
[PASS] OpenCode Go (chave) — 23 modelos disponíveis
[PASS]   modelo LLM_MODEL_FAST — deepseek-v4-flash
[PASS] OpenRouter (chave) — uso acumulado: US$ ...
[PASS] Tavily — busca de teste OK (1 crédito consumido)
[PASS] Geoapify — Paris geocodificada: lon/lat [...]
[PASS] Langfuse — autenticado; projeto(s): [...]

RESULTADO: todas as chaves válidas. OK
```

O script também **valida os IDs dos modelos** contra o catálogo dos provedores —
útil porque modelos são descontinuados com frequência.

## 3. Rodar a aplicação

=== "Stack completa (recomendado)"

    ```bash
    docker compose up --build
    ```

    Sobe PostgreSQL, Redis, API, worker e frontend. Abra o produto em
    <http://localhost:3000>; a documentação interativa da API está em
    <http://localhost:8000/docs>.

=== "Serviços da aplicação"

    ```bash
    docker compose up --build api worker frontend
    ```

    Sobe os três serviços da aplicação e suas dependências (PostgreSQL e Redis)
    com `APP_ENV=local`.

## 4. Rodar os gates de qualidade

```bash
uv run ruff check src/ tests/ scripts/ alembic/          # lint
uv run ruff format src/ tests/ scripts/ alembic/ --check # estilo
uv run mypy src/ --strict                       # tipagem
uv run pytest tests/ --cov=src                  # testes + cobertura (mín. 90%)

cd frontend
npm ci
npm run typecheck
npm run lint
npm run test:cov
npm run build
npm run e2e
```

Instale os hooks de pre-commit para receber esse feedback antes do push:

```bash
uv run pre-commit install
```

## 5. Documentação (esta página)

```bash
uv sync --group docs
uv run mkdocs serve      # http://localhost:8000, com hot reload
uv run mkdocs build --strict   # o mesmo gate que roda no CI
```

## Serviços opcionais

Redis é **opcional** — sem `REDIS_URL` a aplicação funciona com o cache
desativado (degradação graciosa). Para habilitar:

```bash
docker run -d -p 6379:6379 redis:7-alpine
# depois, no .env:
# REDIS_URL=redis://localhost:6379/0
```

Com Redis ativo você ganha cache de roteiros e de geocoding (TTL de 30 dias).

## Problemas comuns

??? question "`uv sync` falha com 'Acesso negado' no Windows"
    Algum processo (normalmente o language server do IDE) mantém locks em
    arquivos do `.venv`. Feche o editor ou repita o comando — cada tentativa
    avança um pouco. Em último caso, remova o diretório do pacote problemático
    dentro de `.venv/Lib/site-packages` e rode `uv sync` de novo.

??? question "Testes fazendo chamadas de rede reais"
    Não deveria acontecer: o `conftest.py` tem um fixture `autouse` que remove
    as variáveis sensíveis do ambiente antes de cada teste. Isso é necessário
    porque o CrewAI executa `load_dotenv()` no import, contaminando
    `os.environ` com o `.env` local.

??? question "A crew falha com erro de LLM"
    Rode `uv run python -m scripts.check_env`. Se o OpenCode Go estiver no teto
    de orçamento, a aplicação faz failover automático para o OpenRouter — veja
    [Estratégia de LLM](../architecture/llm-strategy.md).
