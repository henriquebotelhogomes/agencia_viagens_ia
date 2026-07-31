import { describe, expect, it, vi } from "vitest";

import {
  type ExecutionDetail,
  executionDetailSchema,
} from "@/lib/api/types";
import {
  buildExportDocument,
  downloadItineraryMarkdown,
  exportFileName,
  slugify,
} from "@/lib/export-markdown";

/** Execução de exemplo, válida pelo schema — o export nunca vê dado solto. */
function makeExecution(
  overrides: Partial<ExecutionDetail> = {},
): ExecutionDetail {
  return executionDetailSchema.parse({
    id: "5b1f0f5e-4f21-4b0f-8f3a-9d0a1b2c3d4e",
    status: "succeeded",
    briefing: {
      origem: "Rio de Janeiro",
      destino: "Buenos Aires",
      dias: 5,
      interesses: "gastronomia e cultura",
      moeda: "EUR",
      idioma: "pt-BR",
    },
    created_at: "2026-07-29T14:00:00Z",
    finished_at: "2026-07-29T14:03:05Z",
    duration_seconds: 185,
    itinerary_markdown: "# 5 dias em Buenos Aires\n\nRoteiro completo.",
    error: null,
    used_fallback: false,
    llm_gateway: "openrouter",
    cost: null,
    ...overrides,
  });
}

describe("slugify", () => {
  it("remove acentos e espaços", () => {
    expect(slugify("São Paulo")).toBe("sao-paulo");
  });

  it("reduz pontuação e barras a um único hífen", () => {
    expect(slugify("NYC / EUA!!")).toBe("nyc-eua");
  });

  it("não deixa hífens nas bordas", () => {
    expect(slugify("--Lisboa--")).toBe("lisboa");
  });

  it("devolve vazio quando não sobra nada aproveitável", () => {
    expect(slugify("!!!")).toBe("");
  });

  it("limita a 60 caracteres sem hífen final", () => {
    const longo = "a".repeat(58) + "-x-y";
    expect(slugify(longo)).toHaveLength(60);
    expect(slugify(longo).endsWith("-")).toBe(false);
  });
});

describe("exportFileName", () => {
  it("combina destino e duração no plural", () => {
    expect(exportFileName(makeExecution())).toBe(
      "roteiro-buenos-aires-5-dias.md",
    );
  });

  it("usa o singular para viagens de um dia", () => {
    const execution = makeExecution();
    execution.briefing.dias = 1;
    expect(exportFileName(execution)).toBe("roteiro-buenos-aires-1-dia.md");
  });

  it("omite o destino quando o slug não sobrevive à sanitização", () => {
    const execution = makeExecution();
    execution.briefing.destino = "???";
    expect(exportFileName(execution)).toBe("roteiro-5-dias.md");
  });
});

describe("buildExportDocument", () => {
  it("abre com a proveniência do roteiro", () => {
    const documento = buildExportDocument(makeExecution());

    expect(documento).toContain("> **Voyager — roteiros de viagem com IA**");
    expect(documento).toContain(
      "> Buenos Aires · 5 dias · saindo de Rio de Janeiro · custos em EUR",
    );
    expect(documento).toContain("> Gerado em 2026-07-29");
  });

  it("preserva o roteiro da API na íntegra, após o separador", () => {
    const documento = buildExportDocument(makeExecution());

    // Tudo depois do PRIMEIRO separador é o conteúdo original — mesmo que o
    // roteiro gerado pelo LLM também contenha "---" no meio.
    const separador = "\n\n---\n\n";
    const indice = documento.indexOf(separador);
    expect(indice).toBeGreaterThan(0);
    expect(documento.slice(indice + separador.length)).toBe(
      "# 5 dias em Buenos Aires\n\nRoteiro completo.\n",
    );
  });

  it("usa a data de criação quando a execução não registrou término", () => {
    const documento = buildExportDocument(
      makeExecution({ finished_at: null }),
    );

    expect(documento).toContain("> Gerado em 2026-07-29");
  });
});

describe("downloadItineraryMarkdown", () => {
  it("gera um Blob de Markdown e dispara o download com o nome do arquivo", () => {
    const createObjectURL = vi.fn<(blob: Blob) => string>(() => "blob:fake");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });

    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    try {
      downloadItineraryMarkdown(makeExecution());

      expect(createObjectURL).toHaveBeenCalledTimes(1);
      expect(createObjectURL.mock.calls[0][0].type).toBe(
        "text/markdown;charset=utf-8",
      );

      const link = click.mock.instances[0] as HTMLAnchorElement;
      expect(link.download).toBe("roteiro-buenos-aires-5-dias.md");
      expect(link.href).toContain("blob:");
      // Âncora efêmera: entrou no DOM para o clique funcionar e saiu em seguida
      expect(document.body.contains(link)).toBe(false);

      expect(revokeObjectURL).toHaveBeenCalledWith("blob:fake");
    } finally {
      click.mockRestore();
      vi.unstubAllGlobals();
    }
  });

  it("o conteúdo baixado é o documento com proveniência", async () => {
    // jsdom não implementa `createObjectURL`; o dublê captura o Blob para
    // validar o conteúdo de ponta a ponta, como um download de verdade.
    const createObjectURL = vi.fn<(blob: Blob) => string>(() => "blob:fake");
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL: vi.fn(),
    });
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    try {
      const execution = makeExecution();
      downloadItineraryMarkdown(execution);

      const blob = createObjectURL.mock.calls[0][0];
      expect(await blob.text()).toBe(buildExportDocument(execution));
    } finally {
      click.mockRestore();
      vi.unstubAllGlobals();
    }
  });
});
