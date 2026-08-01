# ADR-0017 — Versionamento de roteiro (linhagem, rollback append-only, diff client-side)

- **Status:** Aceita
- **Data:** 2026-08-01
- **Contexto:** FR-40 (refinamento) e FR-41 (versionamento)

## Contexto e problema

O usuário precisa refinar um roteiro gerado (instrução livre) e transitar entre
versões (histórico + rollback). O modelo precisa:

1. Preservar o histórico completo (imutável) para auditoria e comparação.
2. Ser simples de consultar (listar versões de uma linhagem).
3. Não exigir LLM para rollback (operação instantânea e sem custo).
4. Manter a coerência com a arquitetura existente (fila inalterada, worker
   ramifica por tipo de execução).

## Decisão

### Modelo de linhagem

Cada refine/rollback cria uma nova `Execution` filha com:

- `kind` (`initial` | `refine` | `rollback`)
- `parent_execution_id` → base imediata (pai no refine, alvo no rollback)
- `root_execution_id` → raiz da linhagem (para listar todas as versões com
  `WHERE id == root OR root_execution_id == root`)
- `refine_instruction` → texto livre do usuário (ou "Restaurada a versão N")

`Itinerary.version` = `max(versão da linhagem) + 1`.

### Rollback append-only

"Restaurar versão X" **copia** o `content_markdown` + `locations_geojson` de X
para uma nova versão. Sem LLM, sem geocoding, sem custo. O histórico é imutável:
nenhuma versão é sobrescrita ou apagada.

### Diff no cliente

O frontend busca os dois markdowns (versão atual e anterior) e difere com
`diffLines` do jsdiff. Coerente com a filosofia do projeto (export Markdown
também é 100% client-side). Sem endpoint novo de diff.

### Fila inalterada

`enqueue_generation` passa apenas `execution_id`. O worker lê
`execution.kind` persistido e ramifica:

- `INITIAL` → fluxo atual (cache → crew → geocoding)
- `REFINE` → crew completa com contexto (sem cache)
- `ROLLBACK` → cópia instantânea

## Alternativas descartadas

| Alternativa | Motivo da rejeição |
|---|---|
| Tabela separada `itinerary_versions` | Duplica a relação 1:1 execution↔itinerary; consulta de linhagem mais complexa |
| Diff server-side (endpoint `/diff`) | Adiciona latência e complexidade; o diff de markdown é trivial no cliente |
| Rollback destrutivo (sobrescrever) | Perde histórico; inviabiliza auditoria e comparação |
| Refine parcial (só arquiteto) | Não pesquisa dados novos; resultado inferior |

## Consequências

- **Positivas:** histórico imutável, rollback O(1), sem endpoint de diff,
  modelo de linhagem simples (2 FKs self-referenciais).
- **Negativas:** refine com crew completa dobra custo/tempo por versão (~80s);
  rollback copia geojson mesmo que desatualizado (aceitável: o mapa é derivado
  do markdown).
- **Riscos:** linhagens muito longas (>20 versões) podem tornar a consulta de
  versões lenta — mitigável com índice composto se necessário.
