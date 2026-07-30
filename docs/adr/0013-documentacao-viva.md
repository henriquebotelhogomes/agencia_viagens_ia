# ADR-0013 — Documentação viva

- **Status**: Aceita (implementada)
- **Data**: 2026-07-29
- **Contexto do PRD**: D13

## Contexto e problema

O projeto tinha `README.md`, `walkthrough.md`, `PRD.md` e um diretório `specs/`
com 12 documentos. Conteúdo bom, mas com dois problemas:

1. **Não navegável**: entender a arquitetura exigia abrir múltiplos arquivos
   Markdown no GitHub, sem índice, busca ou hierarquia.
2. **Risco de apodrecer**: nada garantia que a documentação acompanhasse o
   código. Documentação desatualizada é pior que ausente — induz a erro.

Havia também um requisito específico: **demonstrar** maturidade de engenharia
([ADR-0001](0001-posicionamento.md)). Documentação técnica navegável e atualizada
é um dos sinais mais fortes nesse sentido.

## Opções consideradas

### 1. MkDocs + Material + mkdocstrings

- ✅ Padrão de fato do ecossistema Python (FastAPI, Pydantic, uv e Ruff usam)
- ✅ Markdown puro — sem linguagem de marcação nova para aprender
- ✅ `mkdocstrings` gera a referência de API **dos docstrings do código**
- ✅ Busca embutida, tema profissional, deploy trivial no GitHub Pages
- ❌ Um `mkdocs.yml` e um grupo de dependências a manter

### 2. Sphinx

- ✅ Padrão histórico do Python, extremamente poderoso
- ❌ reStructuredText tem curva de aprendizado
- ❌ Visual datado sem investimento em tema

### 3. Docusaurus

- ✅ Excelente para produtos, versionamento de docs nativo
- ❌ Stack Node paralela só para documentação
- ❌ Não gera referência de API Python

### 4. Wiki externa (Notion, GitBook)

- ✅ Edição fácil, colaborativa
- ❌ **Viola o princípio central**: documentação fora do repositório nunca é
  revisada no mesmo PR do código — é o caminho garantido para apodrecer

### 5. Manter apenas os Markdowns soltos

- ❌ Não resolve navegabilidade nem o risco de desatualização

## Decisão

**MkDocs + tema Material + mkdocstrings**, com a documentação em `docs/` e
publicação automática no GitHub Pages.

A "vivacidade" é garantida por **processo, não por disciplina**:

| Mecanismo | Efeito |
| --------- | ------ |
| `mkdocstrings` lê docstrings | Referência de API se atualiza sozinha |
| `mkdocs build --strict` no CI | Link quebrado ou referência órfã reprova o build |
| Definition of Done | "Documentação atualizada no mesmo PR" é critério de aceite |
| Deploy automático em `master` | Sem etapa manual que possa ser esquecida |

Divisão de responsabilidades entre artefatos:

- **`PRD.md`** — artefato de produto: decisões, escopo, checklist de execução
- **`specs/`** — especificações originais de produto e arquitetura
- **`docs/`** — visão técnica navegável; ADRs fazem a ponte com o PRD
- **Docstrings** — fonte da referência de API

## Consequências

### Positivas

- Documentação navegável com busca, hierarquia e tema profissional.
- Referência de API sempre sincronizada com o código.
- Pressão positiva por docstrings de qualidade — eles agora têm consumidor visível.
- ADRs preservam o *porquê* das decisões, incluindo o que foi descartado.

### Negativas

- Mais um gate no CI (custa ~30s de build).
- Risco de **duplicação** entre `PRD.md`, `specs/` e `docs/`. Mitigado pela
  divisão de responsabilidades acima, mas exige disciplina para não repetir
  conteúdo.
- O grupo `docs` adiciona ~15 dependências ao ambiente de desenvolvimento
  (isoladas em grupo próprio, não instaladas por padrão).
- A documentação em português limita a audiência internacional — decisão
  consciente, alinhada ao público-alvo atual.
