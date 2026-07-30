# 05 — Requisitos Não Funcionais (NFRs)

NFRs são o que separa um protótipo de um produto. Cada requisito é **mensurável** e
ligado a uma estratégia nos documentos [`06`](./06-observability.md),
[`07`](./07-performance-scalability.md) e [`08`](./08-security.md).

## 1. Confiabilidade e disponibilidade

| ID | Requisito | Alvo |
|----|-----------|------|
| NFR-AV-01 | Disponibilidade da API (mensal) | ≥ 99.5% (v1) → 99.9% (maduro) |
| NFR-AV-02 | Degradação graciosa de subcomponentes (cache, geocoding, 1 provider LLM) | Sem indisponibilidade total |
| NFR-AV-03 | Recuperação de execução após falha de worker | Retomada/idempotente, sem custo duplicado |
| NFR-AV-04 | RPO / RTO (dados de roteiros) | RPO ≤ 24h, RTO ≤ 1h |

## 2. Performance (SLOs)

| ID | Métrica | Alvo |
|----|---------|------|
| NFR-PF-01 | Latência de API CRUD (p95) | < 300 ms |
| NFR-PF-02 | Time-to-first-token/progresso da execução (p95) | < 3 s |
| NFR-PF-03 | Geração completa de roteiro (p95) | < 45 s (sem cache) |
| NFR-PF-04 | Resposta de cache-hit (p95) | < 500 ms |
| NFR-PF-05 | Web Vitals (LCP / INP / CLS) | LCP < 2.5 s, INP < 200 ms, CLS < 0.1 |

> Estratégias para atingir esses números em [`07-performance-scalability.md`](./07-performance-scalability.md).

## 3. Escalabilidade

| ID | Requisito |
|----|-----------|
| NFR-SC-01 | API e Workers DEVEM escalar **horizontalmente** e sem estado. |
| NFR-SC-02 | Workers DEVEM autoescalar por **profundidade de fila**. |
| NFR-SC-03 | O sistema DEVE suportar picos de tráfego com **backpressure** (fila + rate limit) sem degradar a API. |
| NFR-SC-04 | Banco DEVE suportar leitura escalável (réplicas) para biblioteca/relatórios. |

## 4. Custo e eficiência (FinOps)

| ID | Requisito | Alvo |
|----|-----------|------|
| NFR-FO-01 | Custo de LLM por roteiro DEVE ser medido por execução. | Rastreável 100% |
| NFR-FO-02 | % de roteiros servidos por cache | ≥ 30% (maduro) |
| NFR-FO-03 | Custo médio de LLM por roteiro (tier free) | Meta de margem definida por plano |
| NFR-FO-04 | Alertas de custo por tenant/dia | Acionáveis |

## 5. Segurança e privacidade

| ID | Requisito |
|----|-----------|
| NFR-SE-01 | Autenticação OIDC/OAuth2; autorização RBAC; isolamento multi-tenant (RLS). |
| NFR-SE-02 | Criptografia em trânsito (TLS 1.2+) e em repouso. |
| NFR-SE-03 | Segredos fora do código; rotação suportada. |
| NFR-SE-04 | Conformidade com LGPD/GDPR (consentimento, exportação, exclusão). |
| NFR-SE-05 | Dependências sem CVEs críticas/altas conhecidas (scan no CI). |

> Detalhes em [`08-security.md`](./08-security.md).

## 6. Observabilidade

| ID | Requisito |
|----|-----------|
| NFR-OB-01 | Tracing distribuído (OTel) cobrindo request → execução → chamadas de LLM. |
| NFR-OB-02 | Logs estruturados (JSON) correlacionados por `trace_id`/`request_id`. |
| NFR-OB-03 | Métricas RED/USE + métricas de LLM (tokens, custo, fallback). |
| NFR-OB-04 | Alertas baseados em SLO com error budget. |

> Detalhes em [`06-observability.md`](./06-observability.md).

## 7. Manutenibilidade

| ID | Requisito | Alvo |
|----|-----------|------|
| NFR-MN-01 | Cobertura de testes (núcleo de domínio) | ≥ 80% |
| NFR-MN-02 | Lint/format/type-check obrigatórios no CI | Ruff + mypy (já presentes) |
| NFR-MN-03 | Tempo de pipeline CI | < 10 min |
| NFR-MN-04 | Documentação de API sempre atualizada | OpenAPI gerado |
| NFR-MN-05 | Arquitetura documentada (ADRs) | [`11`](./11-risks-assumptions-decisions.md) |

## 8. Portabilidade e operação

| ID | Requisito |
|----|-----------|
| NFR-OP-01 | Aplicação 100% containerizada; build reprodutível. |
| NFR-OP-02 | Infra como código (IaC); ambientes reproduzíveis. |
| NFR-OP-03 | Deploys automatizados com rollback. |
| NFR-OP-04 | Provider-agnostic de LLM (sem lock-in). |

## 9. Acessibilidade e UX

| ID | Requisito |
|----|-----------|
| NFR-UX-01 | WCAG 2.1 AA. |
| NFR-UX-02 | Responsivo (mobile-first). |
| NFR-UX-03 | i18n PT-BR / EN. |
| NFR-UX-04 | Feedback de progresso em < 1 s após ação do usuário. |

## 10. Qualidade de IA (específico de LLM)

| ID | Requisito |
|----|-----------|
| NFR-AI-01 | Taxa de feedback negativo "informação incorreta" monitorada e com meta de redução. |
| NFR-AI-02 | Avaliação amostral automatizada (groundedness/relevância) sobre execuções. |
| NFR-AI-03 | Proveniência (fontes) presente em ≥ X% dos itens factuais. |

## 11. Matriz de prioridade (MoSCoW por fase)

| NFR | MVP | Beta | GA |
|-----|-----|------|----|
| Disponibilidade 99.5% | Should | Must | Must |
| Tracing OTel + LLM | Must | Must | Must |
| Multi-tenant + RBAC | Should | Must | Must |
| Cache semântico | Could | Should | Must |
| FinOps custo real | Should | Must | Must |
| WCAG AA | Should | Must | Must |
| Autoscaling por fila | Could | Should | Must |

