# 02 — Especificação Funcional

Define **o que** o SaaS faz, do ponto de vista do usuário e do sistema. Independente de
tecnologia (o "como" está em [`03`](./03-technical-spec.md) e [`04`](./04-architecture.md)).

## 1. Visão de capacidades (mapa de features)

```
Voyager AI
├── Conta & Acesso
│   ├── Cadastro / Login (OIDC: Google, e-mail)
│   ├── Workspaces (multi-tenant) e papéis (RBAC)
│   └── Billing & planos
├── Planejamento de Roteiro
│   ├── Briefing de viagem (formulário inteligente)
│   ├── Orquestração multiagente (streaming de progresso)
│   ├── Roteiro estruturado (dia a dia)
│   ├── Estimativa de custos (FinOps de viagem)
│   ├── Mapa interativo com proveniência
│   └── Revisão & refinamento (chat / ajustes)
├── Biblioteca
│   ├── Histórico de roteiros
│   ├── Versões e comparação
│   └── Favoritos / pastas
├── Exportação & Compartilhamento
│   ├── Markdown / PDF
│   ├── Link público (somente leitura)
│   └── Exportar para calendário (.ics)
├── Confiança & Transparência
│   ├── Fontes citadas por item
│   ├── Painel de raciocínio dos agentes
│   └── Feedback de qualidade (👍/👎 + motivo)
└── Operação (interno)
    ├── Painel FinOps (custo por roteiro/tenant)
    ├── Observabilidade (traces/métricas)
    └── Administração de modelos e limites
```

## 2. Requisitos funcionais (FR)

### 2.1 Conta, acesso e tenancy
- **FR-01** O sistema DEVE permitir cadastro/login via OIDC (Google) e e-mail/senha.
- **FR-02** Todo usuário DEVE pertencer a ≥1 **workspace**; dados são isolados por workspace.
- **FR-03** O sistema DEVE suportar papéis: `owner`, `admin`, `member`, `viewer` (RBAC).
- **FR-04** O sistema DEVE aplicar **limites por plano** (ex.: roteiros/mês, modelos disponíveis).

### 2.2 Briefing de viagem
- **FR-10** O usuário DEVE informar: **origem**, **destino**, **duração (dias)** e **interesses**.
- **FR-11** O sistema DEVERIA aceitar parâmetros opcionais: orçamento-alvo, estilo (econômico/
  conforto/luxo), ritmo (relaxado/intenso), datas, nº de viajantes, restrições (mobilidade,
  alimentação), moeda de exibição.
- **FR-12** O sistema DEVE validar entradas (origem/destino não vazios, duração 1–30) e dar
  feedback claro de erro.
- **FR-13** O sistema DEVERIA sugerir destinos/interesses (autocomplete) para reduzir atrito.

### 2.3 Orquestração e geração
- **FR-20** Ao submeter, o sistema DEVE iniciar uma **execução assíncrona** (job) e retornar um
  identificador rastreável.
- **FR-21** O sistema DEVE **transmitir progresso em tempo real** (etapas dos agentes) via streaming.
- **FR-22** A orquestração DEVE envolver, no mínimo, os papéis:
  - **Guia Local** — descobre atrações/restaurantes relevantes aos interesses.
  - **Gerente de Logística** — estima custos (voo, hospedagem, alimentação, transporte local).
  - **Arquiteto de Roteiros** — compila o cronograma final coeso.
- **FR-23** O sistema DEVE acionar **fallback** de modelo/provedor automaticamente em falha,
  sem expor erro cru ao usuário.
- **FR-24** O sistema DEVE consultar o **cache** antes de executar; em acerto, retorna
  instantaneamente sinalizando custo ~zero.
- **FR-25** O sistema DEVE permitir **cancelar** uma execução em andamento.

### 2.4 Resultado: roteiro
- **FR-30** O roteiro DEVE conter: título, resumo, **cronograma dia a dia** (manhã/tarde/noite),
  **tabela de custos** detalhada na moeda escolhida, e **dicas**.
- **FR-31** Cada item relevante (atração, restaurante, hotel) DEVERIA carregar **proveniência**
  (fonte/origem da informação).
- **FR-32** O sistema DEVE renderizar um **mapa interativo** com os locais geolocalizados.
- **FR-33** O sistema DEVE expor um **painel de raciocínio** opcional (transparência).

### 2.5 Refinamento ✅
- **FR-40** O usuário DEVERIA poder **refinar** o roteiro via instruções (“mais barato”,
  “menos caminhada”, “troque o dia 3 por praias”) gerando uma **nova versão**.
- **FR-41** O sistema DEVE manter **versões** e permitir comparar/voltar.

> **Entregue** (v1.26): refine reexecuta a crew completa com contexto; versionamento
> com linhagem (root/parent), rollback append-only, diff client-side (jsdiff).
> Ver [ADR-0017](../docs/adr/0017-versionamento-roteiro.md).

### 2.6 Biblioteca, export e compartilhamento
- **FR-50** Roteiros DEVEM ser **salvos** automaticamente e listados na biblioteca do workspace.
- **FR-51** O sistema DEVE exportar em **Markdown** e **PDF**; DEVERIA exportar **.ics** (calendário).
- **FR-52** O usuário DEVERIA gerar um **link público somente-leitura** (revogável).

### 2.7 Confiança e feedback
- **FR-60** O usuário DEVE poder dar feedback (👍/👎 + motivo) por roteiro e por item.
- **FR-61** O sistema DEVE registrar feedback para avaliação de qualidade (ver [`06`](./06-observability.md)).

### 2.8 Operação (telas internas)
- **FR-70** Admins DEVEM acessar **painel FinOps**: custo por roteiro, por tenant, por modelo.
- **FR-71** Admins DEVERIAM ajustar **roteamento de modelos** e **limites** sem deploy.

## 3. Fluxos principais (happy path)

### 3.1 Gerar roteiro
```
Usuário preenche briefing
   → valida entradas
   → consulta cache (hit? retorna)
   → cria job assíncrono
   → agentes executam (stream de progresso)
        Guia Local → Logística → Arquiteto
   → geocoding dos locais
   → persiste roteiro + métricas (custo, latência, fontes)
   → exibe roteiro + mapa + FinOps
   → coleta feedback
```

### 3.2 Refinar roteiro
```
Usuário abre roteiro → "ajustar" → instrução
   → cria nova execução com contexto da versão anterior
   → gera versão N+1 → diff/compare → salvar/descartar
```

## 4. Regras de negócio

- **RB-01** Cache key = hash determinístico de (origem, destino, dias, interesses, +parâmetros
  relevantes) por workspace; TTL configurável (default 24h).
- **RB-02** Roteiro servido do cache **não** consome cota de geração do plano.
- **RB-03** Moeda de custos exibida conforme preferência do workspace; conversão registrada.
- **RB-04** Execução excedendo limite de tempo/tokens é **interrompida** com resultado parcial
  e aviso claro.
- **RB-05** Feedback negativo com motivo "informação incorreta" marca o roteiro para revisão de
  qualidade (amostragem).

## 5. Estados de uma execução

`QUEUED → RUNNING → (PARTIAL) → SUCCEEDED | FAILED | CANCELLED`

- `PARTIAL`: resultado utilizável apesar de uma etapa degradada (ex.: mapa indisponível).
- Cada transição é **observável** (evento + trace).

## 6. Tratamento de erros (UX de falha)

| Cenário | Comportamento |
|---------|---------------|
| Provedor LLM indisponível | Fallback automático; se todos falharem, mensagem amigável + retry. |
| Cache/Redis fora | Degrada para execução normal (sem cache), sem erro ao usuário. |
| Geocoding falha | Roteiro entregue sem mapa, com aviso não-bloqueante. |
| Entrada inválida | Validação inline antes de submeter. |
| Timeout | Resultado parcial + opção de continuar/retomar. |

## 7. Acessibilidade e i18n (funcional)

- Interface DEVE ser **acessível** (WCAG 2.1 AA) — ver [`09`](./09-frontend-ux.md).
- Conteúdo DEVERIA suportar **PT-BR** e **EN** na v1; moeda/locale por workspace.

## 8. Rastreabilidade FR → Roadmap

A priorização e o faseamento de cada FR estão em [`10-roadmap.md`](./10-roadmap.md).

