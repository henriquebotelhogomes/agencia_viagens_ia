# 00 — Glossário e Convenções

Define termos, siglas e convenções usados em toda a documentação para evitar
ambiguidade.

## Convenções de escrita

- **MUST / DEVE**: requisito obrigatório.
- **SHOULD / DEVERIA**: recomendação forte; desvios exigem justificativa.
- **MAY / PODE**: opcional.
- Datas e versões seguem ISO 8601 (`AAAA-MM-DD`).
- Moeda padrão de exibição ao usuário final: configurável por workspace (default `BRL`).

## Nome de produto

Ao longo dos specs, o produto SaaS é referido como **Voyager AI** (nome de trabalho).
O repositório de origem é `agencia_viagens_ia`.

## Glossário técnico

| Termo | Definição |
|-------|-----------|
| **Agente** | Persona de IA com papel, objetivo e ferramentas (ex.: Guia Local, Gerente de Logística, Arquiteto de Roteiros). |
| **Crew / Orquestração** | Conjunto de agentes coordenados que executam tarefas em sequência ou paralelo para produzir um roteiro. |
| **Roteiro (Itinerary)** | Artefato final: plano de viagem dia a dia, com custos, mapa e recomendações. |
| **FinOps** | Disciplina de controle de custo operacional, aqui aplicada ao custo de tokens de LLM por requisição/tenant. |
| **LLM** | Large Language Model (ex.: Llama 3.3 via Groq, Gemini). |
| **Provider / Provedor** | Serviço que hospeda o LLM (Groq, Google, OpenAI...). |
| **Fallback** | Modelo/provedor alternativo acionado quando o primário falha. |
| **RAG** | Retrieval-Augmented Generation — geração apoiada por recuperação de dados externos. |
| **Tool / Ferramenta** | Capacidade externa que um agente invoca (ex.: busca web via Serper, geocoding). |
| **Token** | Unidade de processamento de LLM; base de custo. |
| **Tenant / Workspace** | Unidade de isolamento lógico de dados de um cliente (multi-tenant). |
| **SSE** | Server-Sent Events — streaming unidirecional servidor→cliente. |
| **SLO / SLI / SLA** | Objetivo / Indicador / Acordo de nível de serviço. |
| **OTel** | OpenTelemetry — padrão de observabilidade (traces, metrics, logs). |
| **ADR** | Architecture Decision Record — registro de decisão arquitetural. |
| **Idempotência** | Propriedade de uma operação produzir o mesmo efeito se repetida. |
| **Backpressure** | Mecanismo de controle de carga para proteger serviços a jusante. |

## Personas de referência (resumo)

| Persona | Descrição | Necessidade-chave |
|---------|-----------|-------------------|
| **Viajante independente** | Planeja viagens sozinho, valoriza tempo. | Roteiro confiável e rápido. |
| **Agente de viagens (PME)** | Profissional que monta roteiros para clientes. | Produtividade e marca branca. |
| **Recrutador técnico** | Avalia o projeto como portfólio. | Evidência de maturidade de engenharia. |

> Detalhamento das personas em [`01-product-vision.md`](./01-product-vision.md).

