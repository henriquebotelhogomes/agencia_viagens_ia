# Estratégia de testes

A pirâmide do projeto, do mais rápido e numeroso ao mais lento e caro.

## Backend (Python)

| Camada | Ferramenta | O que cobre |
| ------ | ---------- | ----------- |
| Unidade e serviço | pytest + pytest-asyncio | Config, runtime, cache, geocoding, fila, rate limiter, worker |
| API | httpx + SQLite em memória | Rotas, validação, RFC 9457, idempotência |
| Contrato | schemathesis | Gera requisições da OpenAPI e valida as respostas |

Gate de cobertura: **90%** (`fail_under` no `pyproject.toml`).

## Frontend (TypeScript)

| Camada | Ferramenta | O que cobre |
| ------ | ---------- | ----------- |
| Unidade | Vitest | Schemas Zod, hook de SSE, cliente da API |
| Componente | Vitest + Testing Library | Formulário, timeline, painel de custo, header |
| E2E | Playwright (desktop + mobile) | Navegação, validação, teclado, tema, rotas |

Gate de cobertura: **90%** (`vitest.config.ts`). Composição de tela, gráfico SVG
e mapa WebGL ficam fora da cobertura unitária — o valor deles está no E2E, que
roda num navegador real.

## Princípios

- **Sem chave real em teste, nunca.** Um fixture `autouse` remove segredos do
  ambiente antes de cada teste do backend; o frontend mocka `fetch` e
  `EventSource`.
- **Testar comportamento, não implementação.** Os testes buscam o que o usuário
  vê (papel, rótulo, texto), não a estrutura interna.
- **Cada bug corrigido vira teste.** A desambiguação de geocoding pelo destino,
  o 400 de corpo malformado e o UID arbitrário do Heroku têm, cada um, um teste
  que reprova a regressão.

## Testes E2E contra produção

O smoke E2E do backend roda o fluxo completo contra a stack real:

```bash
uv run python -m scripts.e2e_smoke --base-url https://voyager-ia-d97e5ffe11f1.herokuapp.com
```

O Playwright pode apontar para qualquer ambiente:

```bash
E2E_BASE_URL=https://sua-app.exemplo.com npm run e2e
```
