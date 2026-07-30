# 08 — Segurança, Privacidade e Compliance

Segurança tratada como requisito de design, não como camada final. Cobre o produto SaaS
multi-tenant e os riscos específicos de aplicações com LLM.

## 1. Modelo de ameaças (resumo STRIDE)

| Ameaça | Exemplo no contexto | Mitigação |
|--------|---------------------|-----------|
| **Spoofing** | Acesso a workspace alheio | OIDC + JWT validado + sessões seguras |
| **Tampering** | Alterar roteiro/cota de outro tenant | RBAC + RLS + validação server-side |
| **Repudiation** | Negar ação sensível | Audit log imutável correlacionado por `trace_id` |
| **Information disclosure** | Vazamento de PII/segredos | Criptografia, redaction, secret manager |
| **Denial of Service** | Abuso de geração (custo) | Rate limit, cotas, circuit breaker, captcha |
| **Elevation of privilege** | `member` agindo como `admin` | Autorização checada por recurso, deny-by-default |
| **Prompt injection** | Conteúdo web malicioso manipula agente | Isolamento de ferramentas, validação de saída |

## 2. Autenticação e autorização

- **AuthN:** OIDC/OAuth2 (Google + e-mail). Tokens **JWT** de curta duração + refresh
  rotacionado. MFA opcional (planos Business).
- **AuthZ:** **RBAC** (`owner/admin/member/viewer`), **deny-by-default**, checagem por
  recurso na API.
- **Multi-tenancy:** isolamento por `workspace_id` em toda query, reforçado por
  **PostgreSQL Row-Level Security (RLS)** — defesa em profundidade contra bug de query.

## 3. Proteção de dados

- **Em trânsito:** TLS 1.2+ obrigatório (HSTS).
- **Em repouso:** criptografia no banco e no object storage.
- **Segredos:** **nunca** no código/repositório. Hoje há `.env` local + `sync:false` no
  `render.yaml` (bom começo). Evoluir para **secret manager** com rotação.
- **Classificação de dados:** briefings podem conter PII (origem/datas/preferências);
  tratados como **confidenciais**.

## 4. Privacidade (LGPD/GDPR)

- **Base legal e consentimento** explícitos para processamento e uso de dados.
- **Direitos do titular:** exportar e **excluir** dados (right to be forgotten) — modelado
  como operação de domínio.
- **Minimização:** coletar só o necessário; retenção definida e expurgo automático.
- **Sub-processadores:** providers de LLM (Groq/Google) e busca (Serper) documentados;
  preferir endpoints que **não treinem** com os dados enviados.
- **Residência de dados:** considerar região de processamento conforme público-alvo.

## 5. Segurança específica de LLM (OWASP Top 10 for LLM)

| Risco | Mitigação |
|-------|-----------|
| **Prompt Injection** (direto/indireto via conteúdo web) | Separar instruções de conteúdo; tratar resultado de ferramentas como **não confiável**; validar/saneamento de saída; limitar ações dos agentes (sem efeitos colaterais perigosos). |
| **Insecure Output Handling** | Renderizar Markdown com **sanitização** (sem HTML/JS arbitrário); escapar conteúdo no frontend. |
| **Sensitive Information Disclosure** | Redaction de PII em prompts/logs/traces; não enviar segredos a LLM. |
| **Model Denial of Service / custo** | Limites de tokens/iterações, rate limit, budgets por tenant. |
| **Excessive Agency** | Ferramentas com escopo mínimo; sem execução de código/efeitos colaterais não revisados. |
| **Data poisoning de fontes** | Proveniência registrada; priorizar fontes confiáveis. |

## 6. Segurança de aplicação (AppSec)

- **Validação de entrada** estrita (Pydantic) em todas as bordas.
- **Proteções web:** CSRF (para sessões cookie), CORS restrito, headers de segurança
  (CSP, HSTS, X-Content-Type-Options), proteção contra XSS no render de Markdown.
- **Rate limiting / anti-abuso** por IP, usuário e workspace.
- **Idempotência** em operações que geram custo (evita cobrança/execução duplicada).

## 7. Segurança da cadeia de suprimento (Supply Chain)

- **Scan de dependências** (CVEs) no CI — Python (`uv`/pip-audit) e JS (`pnpm audit`),
  com **bloqueio de PR** para vulnerabilidades altas/críticas.
- **SAST** (ex.: CodeQL/Bandit/Semgrep) e **secret scanning** no repositório.
- **Lockfiles** versionados (`uv.lock`, `pnpm-lock.yaml`) → builds reprodutíveis.
- **Imagens base mínimas** (já usa imagem do `uv`); scan de imagem de container.
- **SBOM** gerado no pipeline (boa prática que impressiona avaliadores).

## 8. Segurança de infraestrutura

- **Menor privilégio** em credenciais de serviço (DB, storage, providers).
- **Rede:** serviços internos não expostos publicamente; Redis/DB em rede privada
  (o `render.yaml` já usa rede interna para Redis — manter o princípio).
- **IaC revisado** (Terraform) — mudanças de infra passam por PR.
- **Backups** criptografados e testados (restore drills).

## 9. Auditoria e resposta a incidentes

- **Audit log** de ações sensíveis (login, mudança de plano, exclusão de dados, acesso
  admin), correlacionado por `trace_id` e imutável.
- **Runbook de incidente** e processo de **disclosure** (`SECURITY.md`).
- **Rotação de chaves** documentada (API keys de LLM, segredos de app).

## 10. Checklist de segurança (Definition of Secure)

- [ ] AuthN/AuthZ e RLS aplicados em todo endpoint sensível.
- [ ] Segredos fora do código; rotação possível.
- [ ] TLS + criptografia em repouso.
- [ ] Rate limiting + cotas + idempotência em rotas de custo.
- [ ] Sanitização de saída de LLM/Markdown.
- [ ] Scan de deps/SAST/secret scanning verdes no CI.
- [ ] Fluxos de exportação/exclusão de dados (LGPD) implementados.
- [ ] Audit log e runbook de incidente existentes.

> A postura de segurança é verificada continuamente; métricas de scan e incidentes
> entram nos painéis de [`06-observability.md`](./06-observability.md).

