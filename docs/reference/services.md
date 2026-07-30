# Serviços

Serviços de domínio, todos com **`Settings` injetável** e **degradação graciosa**.

## Cache

Cache de roteiros em Redis. Sem `REDIS_URL`, ou com o Redis inacessível, todas as
operações se tornam no-ops — a aplicação continua funcionando.

!!! info "Chave sensível à localização"
    A chave inclui moeda e idioma, além de origem/destino/dias/interesses. Sem
    isso, um roteiro em pt-BR/BRL poderia ser servido para quem pediu en-US/USD.

::: src.services.cache_service
    options:
      show_root_heading: false

## Geocoding

Extração de locais do roteiro (LLM com schema Pydantic) e resolução de
coordenadas. Ordem: **cache Redis → Geoapify → Nominatim**.

!!! warning "Defesa contra prompt injection"
    O texto do roteiro contém conteúdo vindo de busca web, portanto é tratado
    como **dado não confiável**: vai delimitado por `<roteiro>` com instrução
    explícita de ignorar comandos, e a saída é validada contra `LocationList`.
    O teto de locais também é aplicado **em código**, não apenas no prompt.

::: src.services.geocoding_service
    options:
      show_root_heading: false

## Finanças (FinOps)

Câmbio (frankfurter.app, sem chave) e cálculo de custo de LLM.

| Método | Fonte dos dados | Quando usar |
| ------ | --------------- | ----------- |
| `estimate_costs_from_usage` | **Tokens reais** do `CrewOutput` | Sempre que houver execução |
| `estimate_costs` | Heurística por volume de log | Apenas cache hit (custo real é zero) |

::: src.services.finance_service
    options:
      show_root_heading: false
