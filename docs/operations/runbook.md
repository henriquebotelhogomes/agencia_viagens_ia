# Runbook

Procedimentos para os incidentes mais prováveis. Cada seção tem **sintoma →
diagnóstico → ação**.

## Diagnóstico inicial (sempre)

```bash
uv run python -m scripts.check_env
```

Valida todas as integrações contra as APIs reais, sem expor segredos. Resolve ou
localiza a maioria dos problemas em segundos.

---

## Geração de roteiro falhando

### Sintoma
Erro na orquestração; nenhum roteiro é produzido.

### Diagnóstico

1. `scripts/check_env.py` — as chaves de LLM estão válidas?
2. Nos logs, procure `Gateway primário de LLM falhou` — o failover foi acionado?
3. No console do OpenCode, verifique se o orçamento atingiu o teto (US$ 12/5h).
4. No Langfuse, abra o último trace e veja o erro exato do provedor.

### Ação

| Causa | Ação |
| ----- | ---- |
| Teto do Go atingido | Nenhuma — o failover cobre. Se o OpenRouter também falhar, verifique os créditos |
| Créditos do OpenRouter esgotados | Recarregar em openrouter.ai |
| Modelo descontinuado | `check_env.py` aponta; atualizar `LLM_MODEL_*` no `.env` |
| Ambos os gateways fora | Aguardar; sem alternativa configurada |

---

## Mapa sem pins

### Sintoma
Roteiro gerado, mas nenhum local aparece no mapa.

### Diagnóstico

1. A extração retornou locais? Procure no log
   `Extração de locais falhou` ou `resposta do LLM sem objeto JSON`.
2. O geocoding falhou? Procure `Geoapify falhou` ou `sem resultado`.
3. `check_env.py` valida a chave do Geoapify.

### Ação

- **Extração vazia**: normal se o roteiro não citar locais nomeados. Se recorrente,
  o modelo do tier `fast` pode estar com dificuldade de structured output —
  teste trocar `LLM_MODEL_FAST`.
- **Cota do Geoapify esgotada** (3.000/dia): o sistema **não** cai para Nominatim
  automaticamente quando há chave configurada. Remova temporariamente
  `GEOAPIFY_API_KEY` para usar o fallback, ou aguarde a renovação.

---

## Cache não funciona

### Sintoma
Roteiros idênticos são regerados; custo desnecessário.

### Diagnóstico

Procure no log de inicialização:

- `🟢 Redis Cache Service configurado com sucesso.` → cache ativo
- `🔴 Redis inacessível. Cache desativado` → problema de conexão
- Nenhuma das duas → `REDIS_URL` não configurada

### Ação

1. Confirme a `REDIS_URL` no ambiente.
2. Teste a conectividade: `redis-cli -u $REDIS_URL ping`.
3. Lembre-se: a chave inclui **moeda e idioma** — briefings iguais com moedas
   diferentes são cache miss legítimo.

!!! note
    Cache indisponível **não** é incidente crítico: a aplicação funciona sem ele,
    apenas mais caro e lento.

---

## Traces não aparecem no Langfuse

### Sintoma
Execuções acontecem, mas o Langfuse está vazio.

### Diagnóstico

| Verificação | Como |
| ----------- | ---- |
| Chaves configuradas? | `check_env.py` |
| **Região correta?** | Host errado retorna **401** — causa mais comum |
| Callback ativo? | Log deve conter `🔭 Langfuse habilitado para tracing de LLM` |
| Processo encerrou rápido? | O flush é assíncrono; scripts curtos perdem o trace |

### Ação

- Ajuste `LANGFUSE_HOST` para a região das chaves (`us.cloud.langfuse.com` ou
  `cloud.langfuse.com`).
- Em scripts, aguarde alguns segundos antes de encerrar o processo.

---

## Custo acima do esperado

### Sintoma
Consumo do OpenCode Go ou dos créditos do OpenRouter crescendo rápido.

### Diagnóstico

1. Painel FinOps: quantos tokens por execução?
2. Langfuse: alguma execução com número anormal de chamadas (loop de agente)?
3. Cache hit ratio está baixo?

### Ação

1. **Imediato**: reduza `RATE_LIMIT_EXECUTIONS_PER_HOUR`; se necessário, derrube
   o serviço até entender a causa.
2. Verifique se o `max_iter=3` dos agentes está intacto — loops de raciocínio são
   a principal causa de estouro.
3. Confirme que o tier `pro` não está sendo usado nos agentes de volume.

---

## Aplicação não sobe

### Sintoma
Container ou serviço reinicia; healthcheck falha.

### Diagnóstico

```bash
# Healthcheck da API
curl http://localhost:8000/health

# Imports do domínio funcionam?
docker run --rm voyager-ai python -c "import src.crew_builder, src.runtime; print('ok')"
```

### Ação

- **Erro de configuração**: `Settings` falha rápido em variável inválida — leia a
  mensagem do Pydantic, ela indica o campo.
- **Falha de import**: normalmente versão de dependência; confirme que a imagem
  foi construída com o `uv.lock` atual.
- **Cold start no plano Eco do Heroku**: a primeira requisição após o
  adormecimento pode levar segundos. Não é incidente.
