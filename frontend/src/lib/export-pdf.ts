/**
 * Export do roteiro em PDF (impressão formatada / salvar como PDF).
 *
 * Gera um documento A4 estilizado, com cabeçalho de marca, metadados do briefing,
 * tipografia refinada e regras de quebra de página (print-color-adjust, page-break-inside).
 */
import type { ExecutionDetail } from "@/lib/api/types";
import { slugify } from "@/lib/export-markdown";

/**
 * Converte Markdown básico em HTML simples (usado como fallback quando
 * o elemento DOM renderizado não estiver disponível).
 */
export function simpleMarkdownToHtml(markdown: string): string {
  if (!markdown) return "";

  return markdown
    .split("\n\n")
    .map((block) => {
      const trimmed = block.trim();
      if (!trimmed) return "";

      if (trimmed.startsWith("### ")) {
        return `<h3>${escapeHtml(trimmed.slice(4))}</h3>`;
      }
      if (trimmed.startsWith("## ")) {
        return `<h2>${escapeHtml(trimmed.slice(3))}</h2>`;
      }
      if (trimmed.startsWith("# ")) {
        return `<h1>${escapeHtml(trimmed.slice(2))}</h1>`;
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        const items = trimmed
          .split("\n")
          .map((line) => line.replace(/^[-*]\s+/, ""))
          .map((item) => `<li>${formatInline(item)}</li>`)
          .join("");
        return `<ul>${items}</ul>`;
      }
      if (trimmed.startsWith("> ")) {
        return `<blockquote>${formatInline(trimmed.replace(/^>\s+/gm, ""))}</blockquote>`;
      }

      return `<p>${formatInline(trimmed)}</p>`;
    })
    .join("\n");
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatInline(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

/**
 * Monta o documento HTML completo pronto para impressão / PDF em folha A4.
 */
export function buildPdfDocumentHtml(
  execution: ExecutionDetail,
  renderedBodyHtml?: string,
): string {
  const briefing = execution.briefing;
  const contentHtml =
    renderedBodyHtml || simpleMarkdownToHtml(execution.itinerary_markdown ?? "");
  const dataGeracao = execution.finished_at
    ? new Date(execution.finished_at).toLocaleDateString("pt-BR")
    : new Date().toLocaleDateString("pt-BR");

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Roteiro - ${escapeHtml(briefing.destino)} (${briefing.dias} dias)</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 16mm 18mm 16mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #0f172a;
      background: #ffffff;
      line-height: 1.6;
      font-size: 10.5pt;
      margin: 0;
      padding: 0;
    }
    .header {
      border-bottom: 2.5px solid #0284c7;
      padding-bottom: 14px;
      margin-bottom: 22px;
    }
    .brand-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .brand {
      font-size: 11pt;
      font-weight: 800;
      color: #0284c7;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .badge-status {
      background: #e0f2fe;
      color: #0369a1;
      font-size: 8.5pt;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 9999px;
    }
    .title {
      font-size: 22pt;
      font-weight: 800;
      color: #0f172a;
      margin: 6px 0 10px 0;
      line-height: 1.2;
    }
    .meta-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .pill {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      padding: 3px 9px;
      border-radius: 9999px;
      font-size: 8.5pt;
      font-weight: 600;
      color: #334155;
    }
    .pill-highlight {
      background: #fef3c7;
      border-color: #fcd34d;
      color: #92400e;
    }
    .content {
      color: #1e293b;
    }
    .content h1, .content h2, .content h3, .content h4 {
      color: #0f172a;
      page-break-after: avoid;
      break-after: avoid;
    }
    .content h1 {
      font-size: 16pt;
      font-weight: 800;
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 6px;
      margin-top: 26px;
      margin-bottom: 12px;
    }
    .content h2 {
      font-size: 13pt;
      font-weight: 700;
      color: #0369a1;
      margin-top: 20px;
      margin-bottom: 8px;
    }
    .content h3 {
      font-size: 11pt;
      font-weight: 700;
      margin-top: 16px;
      margin-bottom: 6px;
    }
    .content p {
      margin: 8px 0;
    }
    .content table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 9.5pt;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .content th, .content td {
      border: 1px solid #cbd5e1;
      padding: 7px 10px;
      text-align: left;
    }
    .content th {
      background: #f1f5f9;
      font-weight: 700;
      color: #0f172a;
    }
    .content tr:nth-child(even) {
      background: #f8fafc;
    }
    .content ul, .content ol {
      padding-left: 22px;
      margin: 8px 0;
    }
    .content li {
      margin-bottom: 4px;
    }
    .content blockquote {
      border-left: 3px solid #0284c7;
      margin: 12px 0;
      padding: 6px 14px;
      background: #f0f9ff;
      color: #0369a1;
      font-style: italic;
    }
    .footer {
      margin-top: 36px;
      padding-top: 12px;
      border-top: 1px solid #e2e8f0;
      font-size: 8pt;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      page-break-before: auto;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand-container">
      <div class="brand">Voyager AI · Inteligência em Viagens</div>
      <div class="badge-status">Roteiro Oficial</div>
    </div>
    <div class="title">Roteiro para ${escapeHtml(briefing.destino)}</div>
    <div class="meta-pills">
      <span class="pill">Origem: <strong>${escapeHtml(briefing.origem)}</strong></span>
      <span class="pill">Duração: <strong>${briefing.dias} ${briefing.dias === 1 ? "dia" : "dias"}</strong></span>
      <span class="pill">Moeda: <strong>${escapeHtml(briefing.moeda)}</strong></span>
      ${briefing.interesses ? `<span class="pill pill-highlight">Interesses: <strong>${escapeHtml(briefing.interesses)}</strong></span>` : ""}
      <span class="pill">Gerado em: <strong>${dataGeracao}</strong></span>
    </div>
  </div>

  <div class="content">
    ${contentHtml}
  </div>

  <div class="footer">
    <span>Gerado por Voyager AI — Agência de Viagens Inteligente</span>
    <span>Arquivo gerado para impressão e PDF</span>
  </div>
</body>
</html>`;
}

/**
 * Dispara o diálogo de impressão / salvar como PDF no navegador.
 *
 * Utiliza um iframe oculto isolado contendo o documento A4 renderizado,
 * garantindo tipografia vetorial nítida sem poluir a interface do usuário.
 */
export function downloadItineraryPdf(execution: ExecutionDetail): void {
  if (typeof document === "undefined") return;

  const contentElement = document.getElementById("roteiro-markdown-conteudo");
  const renderedHtml = contentElement?.innerHTML;

  const iframe = document.createElement("iframe");
  iframe.style.position = "fixed";
  iframe.style.right = "0";
  iframe.style.bottom = "0";
  iframe.style.width = "0";
  iframe.style.height = "0";
  iframe.style.border = "none";
  iframe.title = `Roteiro ${slugify(execution.briefing.destino)}`;

  document.body.appendChild(iframe);

  const doc = iframe.contentWindow?.document;
  if (!doc) {
    iframe.remove();
    // Fallback caso iframe não seja acessível
    window.print();
    return;
  }

  doc.open();
  doc.write(buildPdfDocumentHtml(execution, renderedHtml));
  doc.close();

  iframe.contentWindow?.focus();

  setTimeout(() => {
    try {
      iframe.contentWindow?.print();
    } catch {
      window.print();
    } finally {
      setTimeout(() => {
        iframe.remove();
      }, 1500);
    }
  }, 250);
}
