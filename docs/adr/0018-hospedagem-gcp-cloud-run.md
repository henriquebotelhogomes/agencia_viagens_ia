# ADR-0018 — Hospedagem: Google Cloud Run (Serverless Scale-to-Zero) em vez de Heroku

- **Status**: Aceita
- **Data**: 2026-09-11
- **Supersede**: [ADR-0015](0015-hospedagem-heroku.md)
- **Contexto do PRD**: D3

## Contexto e problema

O [ADR-0015](0015-hospedagem-heroku.md) adotou o **Heroku** utilizando crédito do GitHub Student Developer Pack (US$ 13/mês por 24 meses). No entanto, a operação no Heroku apresentou restrições e atritos práticos consideráveis:

1. **Dependência de créditos temporários:** O crédito de estudante é finito e requer acompanhamento de faturamento mensal para não gerar custos após o término.
2. **Fragilidade de autenticação CLI e deploys:** O Heroku descontinuou a autenticação pura por credenciais no Git/CLI, gerando timeouts frequentes no Git Credential Manager no Windows e invalidações de sessão inesperadas.
3. **Limitações do Container Stack:** O registry do Heroku não realiza cache de camadas de build e impõe manipulação complexa de manifests (`oci-mediatypes=false`), forçando compilações completas e mais lentas.
4. **Alinhamento com o ecossistema Google Cloud:** O usuário já possui infraestrutura e projetos ativos no Google Cloud Platform (`gcloud`), além de cota nativa de modelos Gemini.

## Decisão

Migrar a hospedagem de toda a stack para **Google Cloud Run** com **Google Cloud Build** e **Artifact Registry / Container Registry**, operando estritamente sob a política **Scale-to-Zero ($0/mês)** no Free Tier perpétuo do Google Cloud.

### Topologia no Google Cloud

| Componente | Serviço GCP | Configuração Serverless | Custo Operacional |
| ---------- | ----------- | ----------------------- | ----------------- |
| **API Backend** | Cloud Run (`voyager-api`) | 1 vCPU, 1 GiB RAM, `--min-instances=0`, `--max-instances=2`, porta 8000 | **US$ 0 / mês** (dentro dos 2M req/mês grátis) |
| **Worker Assíncrono** | Cloud Run / Job (`voyager-worker`) | 1 vCPU, 1 GiB RAM, `--min-instances=0`, comando `saq src.worker.settings.settings` | **US$ 0 / mês** (apenas sob demanda real) |
| **Frontend Next.js** | Cloud Run (`voyager-web`) | 1 vCPU, 512 MiB RAM, `--min-instances=0`, porta 3000 | **US$ 0 / mês** |
| **Build & Registry** | Cloud Build + Artifact Registry | Cache nativo de camadas Docker | Gratuito na cota mensal de build |

### Vantagens

- **Custo Zero Real e Perpétuo:** Graças ao `--min-instances=0`, quando não há acessos, nenhum recurso computacional permanece faturando.
- **Escalabilidade Elástica:** Suporta picos de requisições automaticamente sem risco de estouro de quota (limitado a `--max-instances=2` por segurança FinOps).
- **Zero Atrito de Credenciais:** Integração nativa e transparente via Google Cloud SDK (`gcloud`), já autenticado no ambiente de desenvolvimento.
- **Pipeline Declarativo:** Configuração centralizada em `cloudbuild.yaml` e automação em `scripts/deploy_gcp.ps1`.

## Consequências

- O script de deploy do Heroku (`scripts/deploy_heroku.ps1`) e o remote `heroku` foram inteiramente removidos do repositório.
- A documentação de deploy e os diagramas de infraestrutura foram atualizados para refletir o Google Cloud Run.
