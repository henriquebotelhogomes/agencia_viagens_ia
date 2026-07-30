# Configuração

Toda a configuração da aplicação vem de variáveis de ambiente via
**Pydantic Settings** — fonte única, tipada e validada.

!!! tip "Segredos como `SecretStr`"
    As nove chaves de API são declaradas como `SecretStr`, o que impede que
    vazem em `repr()`, logs ou tracebacks. Use as **propriedades em minúsculo**
    (ex.: `settings.tavily_api_key`) para obter o valor em texto puro no ponto
    de uso.

## Como obter a configuração

```python
from src.config import get_settings

settings = get_settings()   # memoizado; mesma instância em todo o processo
```

Em testes, use `get_settings.cache_clear()` ou instancie diretamente com
`Settings(_env_file=None, ...)` para isolamento.

::: src.config
    options:
      show_root_heading: false
      members:
        - Settings
        - get_settings
