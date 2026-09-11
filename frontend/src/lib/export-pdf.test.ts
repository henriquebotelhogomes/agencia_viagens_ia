import { describe, expect, it, vi, beforeEach } from "vitest";
import { type ExecutionDetail, executionDetailSchema } from "@/lib/api/types";
import {
  buildPdfDocumentHtml,
  downloadItineraryPdf,
  simpleMarkdownToHtml,
} from "./export-pdf";

function makeExecution(override?: Partial<ExecutionDetail>): ExecutionDetail {
  return executionDetailSchema.parse({
    id: "exec-test-pdf",
    status: "succeeded",
    version: 1,
    created_at: "2026-09-10T12:00:00Z",
    finished_at: "2026-09-10T12:05:00Z",
    duration_seconds: 300,
    briefing: {
      origem: "Belo Horizonte",
      destino: "Salvador",
      dias: 4,
      interesses: "Cultural e Praias",
      moeda: "BRL",
      idioma: "pt-BR",
    },
    itinerary_markdown: "# Roteiro Salvador\n\n## Dia 1\n\n- Pelourinho\n- Elevador Lacerda",
    error: null,
    cost: null,
    used_fallback: false,
    llm_gateway: "openrouter",
    ...override,
  });
}

describe("simpleMarkdownToHtml", () => {
  it("converte títulos h1, h2, h3", () => {
    expect(simpleMarkdownToHtml("# Título 1")).toContain("<h1>Título 1</h1>");
    expect(simpleMarkdownToHtml("## Título 2")).toContain("<h2>Título 2</h2>");
    expect(simpleMarkdownToHtml("### Título 3")).toContain("<h3>Título 3</h3>");
  });

  it("converte listas e formatações inline", () => {
    const html = simpleMarkdownToHtml("- Item **negrito**\n- Item *itálico*");
    expect(html).toContain("<ul>");
    expect(html).toContain("<strong>negrito</strong>");
    expect(html).toContain("<em>itálico</em>");
  });

  it("converte blockquotes", () => {
    const html = simpleMarkdownToHtml("> Aviso importante");
    expect(html).toContain("<blockquote>Aviso importante</blockquote>");
  });

  it("retorna string vazia para entrada vazia", () => {
    expect(simpleMarkdownToHtml("")).toBe("");
  });
});

describe("buildPdfDocumentHtml", () => {
  it("monta o documento completo com metadados do briefing e conteúdo", () => {
    const execution = makeExecution();
    const html = buildPdfDocumentHtml(execution);

    expect(html).toContain("<!DOCTYPE html>");
    expect(html).toContain("Salvador");
    expect(html).toContain("Belo Horizonte");
    expect(html).toContain("4 dias");
    expect(html).toContain("Cultural e Praias");
    expect(html).toContain("Pelourinho");
    expect(html).toContain("@page");
  });

  it("usa renderedBodyHtml se fornecido", () => {
    const execution = makeExecution();
    const customHtml = "<div class='custom-rendered'>Conteúdo Renderizado</div>";
    const html = buildPdfDocumentHtml(execution, customHtml);

    expect(html).toContain(customHtml);
  });
});

describe("downloadItineraryPdf", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("cria iframe e dispara a impressão", () => {
    const execution = makeExecution();
    const printSpy = vi.fn();
    const focusSpy = vi.fn();

    const mockIframe = document.createElement("iframe");
    const mockDoc = {
      open: vi.fn(),
      write: vi.fn(),
      close: vi.fn(),
    };

    Object.defineProperty(mockIframe, "contentWindow", {
      value: {
        document: mockDoc,
        print: printSpy,
        focus: focusSpy,
      },
      writable: true,
    });

    vi.spyOn(document, "createElement").mockReturnValue(mockIframe);
    const appendChildSpy = vi.spyOn(document.body, "appendChild");

    downloadItineraryPdf(execution);

    expect(appendChildSpy).toHaveBeenCalled();
    expect(mockDoc.open).toHaveBeenCalled();
    expect(mockDoc.write).toHaveBeenCalled();
    expect(mockDoc.close).toHaveBeenCalled();

    vi.advanceTimersByTime(300);
    expect(printSpy).toHaveBeenCalled();
  });
});
