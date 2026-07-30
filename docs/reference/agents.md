# Agentes, tarefas e orquestração

A camada de IA do produto: quem são os agentes, o que cada um faz e como a
execução é coordenada.

## Fluxo

```python
from src.crew_builder import CrewBuilder
from src.runtime import configure_llm_runtime

configure_llm_runtime()

crew = CrewBuilder(
    destino="Roma, Itália",
    dias=3,
    origem="São Paulo, Brasil",
    interesses="história e gastronomia",
    moeda="EUR",
    idioma="pt-BR",
)
resultado = crew.run()          # com failover automático de gateway
tokens = resultado.token_usage  # base do FinOps
```

## Orquestração

::: src.crew_builder
    options:
      show_root_heading: false

## Agentes

Cada agente recebe o LLM do tier adequado à sua tarefa — ver
[Estratégia de LLM](../architecture/llm-strategy.md).

::: src.agents
    options:
      show_root_heading: false

## Tarefas

Os prompts são **parametrizados por moeda e idioma**: nenhum valor de negócio
fica hardcoded.

::: src.tasks
    options:
      show_root_heading: false

## Modelos de domínio

::: src.models.location
    options:
      show_root_heading: false
