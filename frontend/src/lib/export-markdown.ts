/**
 * Export do roteiro em Markdown (FR-06).
 *
 * O documento é montado e baixado **100% no cliente**: a API já entrega o
 * roteiro pronto (`itinerary_markdown`), então não há razão para envolver o
 * servidor num download que o navegador resolve com um Blob. O PDF (Q5) fica
 * para fase posterior.
 */
import type { ExecutionDetail } from "@/lib/api/types";

/**
 * Slug seguro para nome de arquivo.
 *
 * Remove acentos e reduz qualquer sequência não alfanumérica a um hífen —
 * destinos como "São Paulo" viram `sao-paulo`, e "NYC / EUA" vira `nyc-eua`.
 * Limitado a 60 caracteres para o nome total caber nos limites de filesystem.
 */
export function slugify(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/, "");
}

/** Nome do arquivo baixado, ex.: `roteiro-buenos-aires-5-dias.md`. */
export function exportFileName(execution: ExecutionDetail): string {
  const { destino, dias } = execution.briefing;
  const partes = [
    "roteiro",
    slugify(destino),
    `${dias}-${dias === 1 ? "dia" : "dias"}`,
  ].filter(Boolean);
  return `${partes.join("-")}.md`;
}

/** Data ISO curta (AAAA-MM-DD) — determinística, sem depender de locale/ICU. */
function shortDate(iso: string | null): string {
  return (iso ?? "").slice(0, 10) || "data desconhecida";
}

/**
 * Documento final do export.
 *
 * O roteiro da API já traz título, tabela de custos e cronograma; aqui só
 * acrescentamos o bloco de **proveniência** (quem gerou, quando, com que
 * briefing) — essencial quando o arquivo é compartilhado fora da aplicação.
 */
export function buildExportDocument(execution: ExecutionDetail): string {
  const briefing = execution.briefing;
  const cabecalho = [
    "> **Voyager — roteiros de viagem com IA**",
    `> ${briefing.destino} · ${briefing.dias} ${briefing.dias === 1 ? "dia" : "dias"} · saindo de ${briefing.origem} · custos em ${briefing.moeda}`,
    `> Gerado em ${shortDate(execution.finished_at ?? execution.created_at)}`,
  ].join("\n");

  return `${cabecalho}\n\n---\n\n${execution.itinerary_markdown ?? ""}\n`;
}

/**
 * Dispara o download do roteiro como arquivo `.md`.
 *
 * Padrão Blob + âncora efêmera: funciona em todos os navegadores evergreen
 * sem abrir nova aba. O `revokeObjectURL` síncrono após o `click()` é seguro
 * porque o navegador enfileira o download durante o próprio clique.
 */
export function downloadItineraryMarkdown(execution: ExecutionDetail): void {
  const blob = new Blob([buildExportDocument(execution)], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = exportFileName(execution);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
