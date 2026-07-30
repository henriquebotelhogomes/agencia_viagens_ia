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

## Métricas (planejado — Fase 1)

Com a API e o worker, entram OpenTelemetry e as métricas de plataforma:

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
