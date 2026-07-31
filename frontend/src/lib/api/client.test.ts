import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "@/lib/api/client";

const briefing = {
  origem: "São Paulo",
  destino: "Lisboa",
  dias: 3,
  interesses: "gastronomia",
  moeda: "BRL" as const,
  idioma: "pt-BR" as const,
};

function jsonResponse(body: unknown, status = 200, contentType = "application/json") {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": contentType },
  });
}

describe("api client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("valida a resposta contra o schema", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ id: "abc", status: "queued", stream_url: "/s" }),
    );

    const created = await api.createExecution(briefing);

    expect(created.id).toBe("abc");
  });

  it("rejeita resposta fora do contrato em vez de propagar undefined", async () => {
    // Um campo faltando viraria `undefined` na renderização, com erro distante
    // da causa; falhar aqui aponta o problema real.
    fetchMock.mockResolvedValue(jsonResponse({ id: "abc" }));

    await expect(api.createExecution(briefing)).rejects.toThrow();
  });

  it("envia o cabeçalho de idempotência quando informado", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ id: "abc", status: "queued", stream_url: "/s" }),
    );

    await api.createExecution(briefing, "chave-123");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["Idempotency-Key"]).toBe("chave-123");
  });

  it("omite o cabeçalho de idempotência quando não há chave", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ id: "abc", status: "queued", stream_url: "/s" }),
    );

    await api.createExecution(briefing);

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["Idempotency-Key"]).toBeUndefined();
  });

  it("traduz o envelope RFC 9457 em ApiError com a mensagem do servidor", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          type: "https://voyager.ai/problems/rate-limit-exceeded",
          title: "Limite excedido",
          status: 429,
          detail: "Limite de 5 execuções por hora atingido.",
          retry_after: 1800,
        },
        429,
        "application/problem+json",
      ),
    );

    const error = await api.createExecution(briefing).catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe("Limite de 5 execuções por hora atingido.");
    expect(error.isRateLimited).toBe(true);
    expect(error.retryAfterSeconds).toBe(1800);
  });

  it("degrada quando o erro não segue o padrão (proxy, gateway)", async () => {
    fetchMock.mockResolvedValue(
      new Response("<html>502 Bad Gateway</html>", { status: 502 }),
    );

    const error = await api.getExecution("id").catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(502);
    // Mensagem apresentável, não o HTML cru do proxy
    expect(error.message).toContain("502");
    expect(error.message).not.toContain("<html>");
  });

  it("transforma falha de rede em mensagem acionável", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const error = await api.health().catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(0);
    expect(error.message).toContain("conexão");
  });

  it("aceita 204 sem corpo no cancelamento", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(api.cancelExecution("id")).resolves.toBeUndefined();
  });

  it("monta a URL do stream a partir do identificador", () => {
    expect(api.streamUrl("abc-123")).toContain("/v1/executions/abc-123/stream");
  });

  it("repassa a janela de dias ao endpoint de custos", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        window_days: 7,
        executions: 0,
        total_tokens: 0,
        cost_usd: 0,
        baseline_cost_usd: 0,
        savings_usd: 0,
        cache_hit_ratio: 0,
        avg_duration_seconds: 0,
        by_status: {},
        daily: [],
      }),
    );

    await api.finops(7);

    expect(fetchMock.mock.calls[0][0]).toContain("days=7");
  });
});
