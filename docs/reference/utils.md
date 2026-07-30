# Utilitários

## Logging

Configuração de logging por ambiente:

| Ambiente | Saída |
| -------- | ----- |
| `production` | **JSON em stdout** (12-factor), sem arquivo, `diagnose=False` |
| demais | Console colorido + arquivo local com rotação |

!!! note "Por que `diagnose=False` em produção"
    O `diagnose` do loguru inclui **valores de variáveis** no traceback. Com
    segredos em memória, isso é vazamento em potencial — desligado em produção,
    complementando a proteção do `SecretStr`.

::: src.utils.logger
    options:
      show_root_heading: false

## Localização

Vocabulário de moeda e idioma usado nos prompts e na UI. Centralizar aqui é o que
permite parametrizar a localização sem espalhar strings pelo código.

Moedas suportadas: `BRL`, `USD`, `EUR`, `GBP`.
Idiomas suportados: `pt-BR`, `en-US`, `es-ES`.

Códigos desconhecidos degradam graciosamente — retornam o próprio código, que o
LLM ainda interpreta.

::: src.utils.localization
    options:
      show_root_heading: false
