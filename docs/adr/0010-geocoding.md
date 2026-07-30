# ADR-0010 — Geocoding

- **Status**: Aceita (implementada)
- **Data**: 2026-07-29
- **Contexto do PRD**: D10, S6

## Contexto e problema

O geocoding usava o **Nominatim público** (OpenStreetMap) via `geopy`. Dois
problemas graves:

1. **Violação de ToS**: a política de uso do Nominatim público
   [proíbe uso sistemático/produtivo](https://operations.osmfoundation.org/policies/nominatim/)
   e limita a **1 requisição por segundo**.
2. **Bloqueio da thread**: para respeitar o limite, o código tinha
   `time.sleep(1.1)` **por local**. Com 8 locais, isso significava ~9 segundos de
   thread parada — inviável sob concorrência.

## Opções consideradas

| Opção | Free tier | Avaliação |
| ----- | --------- | --------- |
| **Geoapify** | 3.000 req/dia | ✅ Sem cartão, base OSM, batch API |
| LocationIQ | 5.000 req/dia | Equivalente; rate de 2 req/s no free |
| Mapbox Geocoding | 100k req/mês | Exige cartão; ToS obriga usar mapa Mapbox |
| Google Geocoding | US$ 200/mês em crédito | Melhor precisão, mas cartão + ToS restritivo + lock-in |
| Nominatim + cache | grátis | Continua violando ToS em produção |
| Photon self-host | grátis | Controle total, mas exige infraestrutura |

## Decisão

**Geoapify** como provider primário, com **cache Redis de TTL longo (30 dias)**.

O **Nominatim permanece como fallback** para quando não há chave configurada —
degradação graciosa, mantendo o projeto funcional sem credenciais.

Ordem de resolução:

```text
cache Redis → Geoapify → Nominatim (só sem chave)
```

## Consequências

### Positivas

- `time.sleep` eliminado do caminho primário.
- Cache com TTL de 30 dias: coordenadas de atrações turísticas não mudam, o hit
  ratio esperado é alto (> 80%), o que torna a cota de 3.000/dia folgada.
- ToS respeitado.
- Validado com execução real: 4 locais extraídos de um roteiro e geocodificados
  corretamente (Louvre em `48.8611, 2.3380`).

### Negativas

- Uma chave a mais para gerenciar (mitigado pelo `scripts/check_env.py`).
- `geopy` continua como dependência enquanto o Nominatim for fallback — dívida
  técnica registrada para remoção futura.
- O cache introduz possibilidade de dado desatualizado por até 30 dias; aceitável
  para coordenadas geográficas.
