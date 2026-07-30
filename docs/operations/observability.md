# Observabilidade

Três camadas complementares: **logs** (o que aconteceu), **traces de LLM** (por
que a IA respondeu assim) e **métricas** (como o sistema se comporta no agregado).

## Logs

Configurados em `src/utils/logger.py`, com comportamento por ambiente:

=== "Produção"

    JSON estruturado em **stdout**, coletado pela plataforma. Sem arquivos —
    princípio 12-factor: log é stream, não arquivo.

    ```json
    {"text": "Roteiro salvo no cache do Redis.",
     "record": {"level": {"name": "INFO"}, "time": {...}, ...}}
    ```

    `diagnose=False` impede que valores de variáveis (potencialmente segredos)
    apareçam em tracebacks.

=== "Desenvolvimento"

    Console colorido + arquivo em `logs/app.log` com rotação de 10 MB e retenção
    de 10 dias. O arquivo alimenta o botão de download do playground Streamlit.

### O que é logado

| Evento | Nível |
| ------ | ----- |
| Cache configurado / indisponível | INFO / WARNING |
| Roteiro encontrado ou salvo no cache | INFO |
| Falha de gateway de LLM + acionamento de failover | WARNING |
| Falha de Geoapify, Tavily ou câmbio | WARNING |
| Erro crítico de orquestração | ERROR |

!!! success "Nenhuma exceção silenciosa"
    Todo `except` registra contexto. O padrão `except: pass` foi erradicado e é
    proibido pelo [guia de contribuição](../guides/contributing.md#code-smells-banidos).

## Traces de LLM (Langfuse)

Ativado automaticamente quando `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY`
estão configurados. Sem as chaves, o tracing é desligado e a aplicação segue.

Cada chamada de LLM gera uma observação com prompt, resposta, tokens, latência e
modelo utilizado.

### Como investigar um roteiro ruim

1. Abra o trace da execução no Langfuse.
2. Identifique qual agente produziu o output problemático.
3. Leia o **prompt exato** enviado — geralmente o problema está aí, não no modelo.
4. Verifique se houve **failover** (o modelo no trace difere do primário).
5. Confira os tokens: truncamento por limite de contexto aparece como
   `completion_tokens` no teto.

!!! warning "Limitações conhecidas"
    - **`totalCost` fica zero** para modelos do OpenCode Go: endpoint custom, sem
      tabela de preços no Langfuse. Os tokens são capturados; o custo vem do
      nosso cálculo (ver [FinOps](finops.md)).
    - O flush é assíncrono: um processo que encerra imediatamente após a chamada
      pode perder o trace. Em scripts curtos, aguarde alguns segundos.
    - As chaves são **vinculadas à região**. Host errado retorna 401 silencioso —
      `scripts/check_env.py` detecta.

## Traces de infraestrutura (OpenTelemetry)

Complementa o Langfuse com o que acontece **fora** das chamadas de LLM:
latência por rota HTTP, queries do SQLAlchemy, comandos Redis e o ciclo de
vida de cada job do worker.

| Aspecto | Como funciona |
| ------- | ------------- |
| Ativação | `OTEL_EXPORTER_OTLP_ENDPOINT` configurado; vazio = desligado, sem overhead |
| Inicialização | Explícita, em `src/telemetry.py` — nunca no import (invariante S1) |
| API | FastAPI instrumentado no `lifespan` (`service.name=voyager-api`) |
| Worker | Span raiz `generate_itinerary` por job, com `voyager.execution_id` e status final (`service.name=voyager-worker`) |
| Automáticos | SQLAlchemy e Redis instrumentados nos dois processos |
| Autenticação | `OTEL_EXPORTER_OTLP_HEADERS` (formato `chave=valor,...`), tratado como segredo |

Backends OTLP com free tier: Grafana Cloud, Honeycomb e New Relic (este último
incluso no GitHub Student Pack). Basta apontar o endpoint e os headers.

```bash
# Exemplo: Grafana Cloud
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-0.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <token>
```

## Métricas (próxima etapa)

Com traces ativos, as métricas derivadas entram na sequência:

| Métrica | Uso |
| ------- | --- |
| Latência p95 por rota | SLO de API (< 300ms nas rotas síncronas) |
| Duração da execução | SLO de geração (< 90s p95) |
| Profundidade da fila | Gatilho de autoscaling do worker |
| Taxa de erro por gateway de LLM | Detectar degradação de provedor |
| Taxa de acionamento de failover | Indicador de saturação do orçamento do Go |
| **Consumo do orçamento do Go** | **Alerta antes do teto de 5h** |
| Cache hit ratio | Eficácia do cache (meta > 30% em roteiros) |
| Custo por execução | FinOps |

Traces correlacionados por `request_id`, propagado do frontend até o worker.

## Diagnóstico rápido

```bash
# Todas as integrações estão saudáveis?
uv run python -m scripts.check_env

# A aplicação responde? (com o Streamlit rodando)
curl http://localhost:8501/_stcore/health
```
