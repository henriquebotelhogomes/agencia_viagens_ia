# C4 nível 1 — Contexto

Quem usa o sistema e de quais serviços externos ele depende.

```mermaid
graph TB
    U["👤 Viajante<br/><i>usuário final</i>"]
    U -->|"informa briefing e<br/>recebe roteiro"| S

    S["🎯 <b>Voyager AI</b><br/><i>Planejamento de viagens<br/>com IA multiagente</i>"]

    S -->|"gera texto<br/>tier fast/tools"| GO["OpenCode Go<br/><i>gateway de LLM primário</i>"]
    S -->|"gera texto tier pro<br/>e failover"| OR["OpenRouter<br/><i>gateway de LLM</i>"]
    S -->|"pesquisa preços<br/>e informações"| TV["Tavily<br/><i>busca web p/ agentes</i>"]
    S -->|"resolve coordenadas"| GA["Geoapify<br/><i>geocoding</i>"]
    S -->|"converte moedas"| FR["Frankfurter<br/><i>câmbio (BCE)</i>"]
    S -->|"envia traces<br/>de LLM"| LF["Langfuse Cloud<br/><i>observabilidade de LLM</i>"]

    style S fill:#3f51b5,color:#fff
    style U fill:#616161,color:#fff
```

## Atores

| Ator | Descrição |
| ---- | --------- |
| **Viajante** | Informa origem, destino, duração, interesses, moeda e idioma; recebe roteiro, mapa e auditoria de custos. Sem autenticação no MVP ([ADR-0004](../adr/0004-autenticacao.md)). |

## Dependências externas

| Serviço | Papel | Se ficar indisponível |
| ------- | ----- | --------------------- |
| **OpenCode Go** | LLM primário dos tiers baratos | Failover automático para OpenRouter |
| **OpenRouter** | LLM do tier `pro` e rede de segurança | Execução falha (propagada ao usuário) |
| **Tavily** | Busca web do agente de Logística | Agente perde a ferramenta; roteiro fica genérico |
| **Geoapify** | Coordenadas dos locais | Fallback para Nominatim (OSM público) |
| **Frankfurter** | Taxas de câmbio | Retorna `None`, com log; fluxo continua |
| **Langfuse** | Traces, tokens e custo | Tracing desativado; aplicação segue |
| **Redis** *(opcional)* | Cache de roteiros e geocoding | Cache desativado; tudo recalculado |

!!! success "Nenhuma dependência externa é ponto único de falha crítico"
    Todo serviço externo tem fallback ou degradação graciosa documentada. A
    única exceção consciente é o par de gateways de LLM — se **ambos** caírem,
    não há roteiro a gerar.

## Fronteira de dados

O briefing do usuário (origem, destino, datas implícitas, interesses) é
**dado pessoal** sob LGPD/GDPR quando associado a um indivíduo. No MVP:

- Não há autenticação, portanto nenhum briefing é vinculado a identidade.
- Prompts trafegam para os gateways de LLM (EUA/UE/Singapura). O OpenCode Go
  opera com **zero-retention** — providers não treinam com os dados.
- Retenção de cache: 24h para roteiros, 30 dias para coordenadas.
