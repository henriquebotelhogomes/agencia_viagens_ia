# Runtime

Inicialização **explícita** do processo. Este módulo existe para que nenhum
módulo de domínio precise mutar estado global durante o `import`.

!!! danger "Regra invariante"
    Importar qualquer módulo de `src/` **não pode** alterar `os.environ` nem
    configurar bibliotecas globalmente. Existe um teste que roda em subprocesso
    limpo e falha se essa regra for violada.

## Bootstrap — a exceção necessária

Algumas bibliotecas leem o ambiente em **tempo de import**, guardando o valor
numa constante de módulo. Para essas, `configure_llm_runtime()` chega tarde: o
valor já foi capturado.

O caso concreto: o CrewAI faz
`_REDIS_URL = os.environ.get("REDIS_URL")` em `crewai/utilities/lock_store.py`
e, havendo valor, usa `portalocker.RedisLock` com um cliente Redis próprio — sem
a configuração de certificado que provedores gerenciados exigem. Em produção,
**toda** geração de roteiro morria em `CERTIFICATE_VERIFY_FAILED`
([ADR-0015](../adr/0015-hospedagem-heroku.md)).

```python
# Primeiras linhas do entrypoint, acima dos imports de domínio
from src.bootstrap import isolate_redis_from_third_parties

isolate_redis_from_third_parties()
```

A variável é **movida** para `APP_REDIS_URL`, que `Settings` lê com precedência
— a aplicação mantém o Redis, apenas as bibliotecas de terceiros deixam de
enxergá-lo.

::: src.bootstrap
    options:
      show_root_heading: false
      members:
        - isolate_redis_from_third_parties

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
