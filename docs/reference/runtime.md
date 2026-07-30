# Runtime

Inicialização **explícita** do processo. Este módulo existe para que nenhum
módulo de domínio precise mutar estado global durante o `import`.

!!! danger "Regra invariante"
    Importar qualquer módulo de `src/` **não pode** alterar `os.environ` nem
    configurar bibliotecas globalmente. Existe um teste que roda em subprocesso
    limpo e falha se essa regra for violada.

## Uso

Todo entrypoint (Streamlit hoje; API e worker na Fase 1) chama uma vez, no início:

```python
from src.runtime import configure_llm_runtime

settings = configure_llm_runtime()   # idempotente
```

O que a função faz, em ordem:

1. **Verifica o Redis** — se `REDIS_URL` aponta para um host inacessível, remove
   a variável do ambiente. Necessário porque litellm e CrewAI leem `REDIS_URL`
   diretamente para habilitar cache próprio, e um host quebrado causa falha no
   meio da orquestração.
2. **Exporta chaves** para as variáveis que os SDKs esperam, **sem sobrescrever**
   valores já presentes no ambiente.
3. **Configura o litellm** — desativa cache interno, ativa `drop_params` e liga o
   callback do Langfuse quando as chaves existem.

::: src.runtime
    options:
      show_root_heading: false
      members:
        - configure_llm_runtime
        - reset_runtime_state

## Telemetria (OpenTelemetry)

Mesma filosofia do runtime: inicialização explícita, idempotente e com
degradação graciosa — sem `OTEL_EXPORTER_OTLP_ENDPOINT`, é um no-op. A API
instrumenta o FastAPI no `lifespan`; o worker abre um span raiz por job.
Detalhes de operação em [Observabilidade](../operations/observability.md).

::: src.telemetry
    options:
      show_root_heading: false
      members:
        - configure_telemetry
        - get_tracer
        - reset_telemetry_state
