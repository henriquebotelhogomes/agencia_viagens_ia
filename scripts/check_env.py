"""Diagnóstico do .env: valida cada chave contra a respectiva API.

Uso (a partir da raiz do projeto):
    uv run python -m scripts.check_env

Segurança: NUNCA imprime valores de chaves — apenas status por serviço.
"""

import io
import sys

import requests

from src.config import get_settings

# Console do Windows pode usar cp1252; força UTF-8 para acentos e símbolos
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TIMEOUT = 15.0


def _ok(name: str, detail: str = "") -> None:
    print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))


def _fail(name: str, detail: str) -> None:
    print(f"  [FAIL] {name} — {detail}")


def check_opencode() -> bool:
    """Valida a chave do OpenCode Go e a existência dos modelos dos tiers."""
    s = get_settings()
    if not s.opencode_api_key:
        _fail("OpenCode Go", "OPENCODE_API_KEY vazia")
        return False
    try:
        resp = requests.get(
            f"{s.OPENCODE_API_BASE}/models",
            headers={"Authorization": f"Bearer {s.opencode_api_key}"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            _fail(
                "OpenCode Go", f"HTTP {resp.status_code} em /models (chave inválida?)"
            )
            return False
        ids = {m.get("id", "") for m in resp.json().get("data", [])}
        _ok("OpenCode Go (chave)", f"{len(ids)} modelos disponíveis")
        all_ok = True
        for tier, model in [
            ("LLM_MODEL_FAST", s.LLM_MODEL_FAST),
            ("LLM_MODEL_FAST_TOOLS", s.LLM_MODEL_FAST_TOOLS),
        ]:
            if model in ids:
                _ok(f"  modelo {tier}", model)
            else:
                _fail(
                    f"  modelo {tier}",
                    f"'{model}' não existe no Go. Disponíveis: {sorted(ids)}",
                )
                all_ok = False
        return all_ok
    except requests.RequestException as e:
        _fail("OpenCode Go", f"erro de rede: {type(e).__name__}")
        return False


def check_openrouter() -> bool:
    """Valida a chave do OpenRouter e os IDs de modelo configurados."""
    s = get_settings()
    if not s.openrouter_api_key:
        _fail("OpenRouter", "OPENROUTER_API_KEY vazia")
        return False
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {s.openrouter_api_key}"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            _fail(
                "OpenRouter", f"HTTP {resp.status_code} em /auth/key (chave inválida?)"
            )
            return False
        info = resp.json().get("data", {})
        usage = info.get("usage", "?")
        _ok("OpenRouter (chave)", f"uso acumulado: US$ {usage}")

        # Lista pública de modelos para validar os IDs configurados
        models_resp = requests.get(
            "https://openrouter.ai/api/v1/models", timeout=TIMEOUT
        )
        ids = {m.get("id", "") for m in models_resp.json().get("data", [])}
        all_ok = True
        for tier, model in [
            ("LLM_MODEL_PRO", s.LLM_MODEL_PRO),
            ("LLM_FALLBACK_FAST", s.LLM_FALLBACK_FAST),
            ("LLM_FALLBACK_TOOLS", s.LLM_FALLBACK_TOOLS),
        ]:
            # Config usa prefixo litellm "openrouter/"; a API usa o ID puro
            bare = model.removeprefix("openrouter/")
            if bare in ids:
                _ok(f"  modelo {tier}", bare)
            else:
                similar = sorted(i for i in ids if "gemini" in i and "flash" in i)[:8]
                _fail(
                    f"  modelo {tier}",
                    f"'{bare}' NÃO existe no OpenRouter. "
                    f"Gemini flash disponíveis: {similar}",
                )
                all_ok = False
        return all_ok
    except requests.RequestException as e:
        _fail("OpenRouter", f"erro de rede: {type(e).__name__}")
        return False


def check_tavily() -> bool:
    """Valida a chave do Tavily com uma busca mínima (custa 1 crédito)."""
    s = get_settings()
    if not s.tavily_api_key:
        _fail("Tavily", "TAVILY_API_KEY vazia")
        return False
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {s.tavily_api_key}"},
            json={"query": "Paris tourism", "max_results": 1},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            _ok("Tavily", "busca de teste OK (1 crédito consumido)")
            return True
        _fail("Tavily", f"HTTP {resp.status_code} (chave inválida ou sem créditos?)")
        return False
    except requests.RequestException as e:
        _fail("Tavily", f"erro de rede: {type(e).__name__}")
        return False


def check_geoapify() -> bool:
    """Valida a chave do Geoapify com um geocode simples."""
    s = get_settings()
    if not s.geoapify_api_key:
        _fail("Geoapify", "GEOAPIFY_API_KEY vazia")
        return False
    try:
        resp = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={"text": "Paris, France", "limit": 1, "apiKey": s.geoapify_api_key},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("features"):
            coords = resp.json()["features"][0]["geometry"]["coordinates"]
            _ok("Geoapify", f"Paris geocodificada: lon/lat {coords}")
            return True
        _fail("Geoapify", f"HTTP {resp.status_code} (chave inválida?)")
        return False
    except requests.RequestException as e:
        _fail("Geoapify", f"erro de rede: {type(e).__name__}")
        return False


def check_langfuse() -> bool:
    """Valida o par de chaves do Langfuse via endpoint autenticado."""
    s = get_settings()
    if not s.langfuse_enabled:
        _fail("Langfuse", "chaves pública/secreta não configuradas")
        return False
    try:
        resp = requests.get(
            f"{s.LANGFUSE_HOST}/api/public/projects",
            auth=(s.langfuse_public_key, s.langfuse_secret_key),
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            projects = [p.get("name", "?") for p in resp.json().get("data", [])]
            _ok("Langfuse", f"autenticado; projeto(s): {projects}")
            return True
        _fail("Langfuse", f"HTTP {resp.status_code} (par de chaves ou host errados?)")
        return False
    except requests.RequestException as e:
        _fail("Langfuse", f"erro de rede: {type(e).__name__}")
        return False


def main() -> int:
    print("Diagnóstico do .env (nenhum segredo é exibido)\n")
    results = [
        check_opencode(),
        check_openrouter(),
        check_tavily(),
        check_geoapify(),
        check_langfuse(),
    ]
    print()
    if all(results):
        print("RESULTADO: todas as chaves válidas. OK")
        return 0
    print("RESULTADO: há pendências acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
