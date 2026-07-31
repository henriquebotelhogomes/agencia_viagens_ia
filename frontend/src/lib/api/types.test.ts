import { describe, expect, it } from "vitest";

import {
  isTerminal,
  savingsPercent,
  tripBriefingSchema,
} from "@/lib/api/types";

describe("tripBriefingSchema", () => {
  const valid = {
    origem: "São Paulo, Brasil",
    destino: "Lisboa, Portugal",
    dias: 3,
    interesses: "gastronomia",
    moeda: "BRL",
    idioma: "pt-BR",
  };

  it("aceita um briefing completo", () => {
    expect(tripBriefingSchema.parse(valid)).toMatchObject(valid);
  });

  it("converte dias de string para número", () => {
    // O input de formulário sempre entrega string, mesmo com type="number"
    const parsed = tripBriefingSchema.parse({ ...valid, dias: "5" });

    expect(parsed.dias).toBe(5);
    expect(typeof parsed.dias).toBe("number");
  });

  it("remove espaços em volta dos textos", () => {
    const parsed = tripBriefingSchema.parse({
      ...valid,
      destino: "  Roma  ",
    });

    expect(parsed.destino).toBe("Roma");
  });

  it.each([
    ["dias abaixo do mínimo", { dias: 0 }],
    ["dias acima do máximo", { dias: 31 }],
    ["dias fracionários", { dias: 2.5 }],
    ["destino curto demais", { destino: "a" }],
    ["interesses vazios", { interesses: "" }],
    ["moeda não suportada", { moeda: "JPY" }],
    ["idioma não suportado", { idioma: "fr-FR" }],
  ])("rejeita %s", (_label, override) => {
    const result = tripBriefingSchema.safeParse({ ...valid, ...override });

    expect(result.success).toBe(false);
  });

  it("rejeita destino com apenas espaços", () => {
    const result = tripBriefingSchema.safeParse({ ...valid, destino: "   " });

    expect(result.success).toBe(false);
  });
});

describe("isTerminal", () => {
  it.each(["succeeded", "failed", "cancelled"] as const)(
    "considera %s terminal",
    (status) => {
      expect(isTerminal(status)).toBe(true);
    },
  );

  it.each(["queued", "running"] as const)("considera %s em curso", (status) => {
    expect(isTerminal(status)).toBe(false);
  });
});

describe("savingsPercent", () => {
  const base = {
    prompt_tokens: 100,
    completion_tokens: 50,
    total_tokens: 150,
    served_from_cache: false,
  };

  it("calcula o percentual sobre o custo de referência", () => {
    const percent = savingsPercent({
      ...base,
      cost_usd: 0.02,
      baseline_cost_usd: 0.2,
      savings_usd: 0.18,
    });

    expect(percent).toBeCloseTo(90);
  });

  it("devolve zero quando não há referência, em vez de dividir por zero", () => {
    const percent = savingsPercent({
      ...base,
      cost_usd: 0,
      baseline_cost_usd: 0,
      savings_usd: 0,
    });

    expect(percent).toBe(0);
  });
});
