"""Teste E2E manual da Fase 1 contra a stack real (docker compose).

Uso (com a stack no ar):
    uv run python -m scripts.e2e_smoke

NÃO é um teste automatizado: consome tokens de LLM reais. Serve para validar
a integração completa API → fila → worker → banco → SSE.
"""

import io
import json
import sys
import time
import urllib.error
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API = "http://localhost:8000"
BRIEFING = {
    "origem": "São Paulo, Brasil",
    "destino": "Lisboa, Portugal",
    "dias": 2,
    "interesses": "gastronomia",
    "moeda": "EUR",
    "idioma": "pt-BR",
}
POLL_TIMEOUT_SECONDS = 300


def _request(path: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else {}


def main() -> int:
    print("== 1. Criando execução ==")
    created = _request("/v1/executions", method="POST", body=BRIEFING)
    execution_id = created["id"]
    print(f"   id={execution_id} status={created['status']}")
    print(f"   stream={created['stream_url']}")

    print("\n== 2. Aguardando o worker processar ==")
    started = time.monotonic()
    detail: dict = {}
    while time.monotonic() - started < POLL_TIMEOUT_SECONDS:
        detail = _request(f"/v1/executions/{execution_id}")
        status = detail["status"]
        elapsed = int(time.monotonic() - started)
        print(f"   [{elapsed:>3}s] status={status}")
        if status in {"succeeded", "failed", "cancelled"}:
            break
        time.sleep(10)

    print("\n== 3. Resultado ==")
    print(f"   status: {detail.get('status')}")
    print(f"   duração: {detail.get('duration_seconds')}s")
    gateway = detail.get("llm_gateway")
    fallback = detail.get("used_fallback")
    print(f"   gateway: {gateway} (fallback={fallback})")
    cost = detail.get("cost", {})
    print(f"   tokens reais: {cost.get('total_tokens')}")
    print(f"   economia vs GPT-4o: US$ {cost.get('savings_usd', 0):.4f}")
    markdown = detail.get("itinerary_markdown") or ""
    print(f"   roteiro: {len(markdown)} chars")
    print(f"   contém EUR/€: {'EUR' in markdown or '€' in markdown}")
    if detail.get("error"):
        print(f"   ERRO: {detail['error'][:300]}")

    print("\n== 4. GeoJSON do mapa ==")
    geojson = _request(f"/v1/executions/{execution_id}/geojson")
    features = geojson.get("features", [])
    print(f"   locais geocodificados: {len(features)}")
    for feature in features[:5]:
        name = feature["properties"]["name"]
        lon, lat = feature["geometry"]["coordinates"]
        print(f"     - {name}: {lat:.4f}, {lon:.4f}")

    print("\n== 5. Idempotência ==")
    req = urllib.request.Request(
        f"{API}/v1/executions",
        data=json.dumps(BRIEFING).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "Idempotency-Key": "e2e-key"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        first = json.loads(resp.read())
    with urllib.request.urlopen(req, timeout=30) as resp:
        second = json.loads(resp.read())
    print(f"   mesma chave → mesmo id: {first['id'] == second['id']}")

    print("\n== 6. Erro RFC 9457 (404) ==")
    try:
        _request("/v1/executions/00000000-0000-0000-0000-000000000000")
    except urllib.error.HTTPError as e:
        problem = json.loads(e.read())
        print(f"   status={e.code} content-type={e.headers.get('content-type')}")
        print(f"   type={problem.get('type')}")

    ok = detail.get("status") == "succeeded"
    print(f"\nRESULTADO: {'SUCESSO' if ok else 'FALHA'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
