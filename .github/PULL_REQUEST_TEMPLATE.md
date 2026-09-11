## 📌 Descrição das Alterações

<!-- Forneça um resumo claro e conciso das alterações implementadas e a motivação por trás delas. -->

### Tipo de Mudança
- [ ] 🐛 Correção de bug (*bug fix*)
- [ ] ✨ Nova funcionalidade (*new feature*)
- [ ] ⚡ Otimização de performance / FinOps
- [ ] ♻️ Refatoração de código
- [ ] 📝 Atualização de documentação / ADR
- [ ] 🧪 Adição ou melhoria de testes
- [ ] 🚀 CI/CD / DevOps / Docker / Infraestrutura

---

## 🎯 Componentes Afetados
- [ ] Backend API (`src/api/`)
- [ ] Worker / Agentes (`src/worker/`, `src/services/`)
- [ ] Modelos de Banco de Dados / Migrations (`src/db/`, `alembic/`)
- [ ] Frontend Next.js (`frontend/`)
- [ ] Pipeline CI/CD / Docker / Workflows (`.github/`)

---

## 🧪 Checklist de Verificação de Qualidade (Definition of Done)

- [ ] `uv run ruff check src/ tests/ scripts/ alembic/` executado com sucesso (zero erros).
- [ ] `uv run ruff format src/ tests/ scripts/ alembic/ --check` validado.
- [ ] `uv run mypy src/ --strict` aprovado com tipagem 100% estrita.
- [ ] `uv run pytest tests/ --cov=src` com cobertura mantida $\ge 90\%$.
- [ ] Frontend (se aplicável): `npm run typecheck`, `npm run lint` e `npm run test:cov` aprovados com cobertura $\ge 85\%$.
- [ ] Documentação ou ADR atualizados em `docs/` se houver alteração de arquitetura ou comportamento.
- [ ] Nenhuma credencial ou segredo introduzido no repositório.
