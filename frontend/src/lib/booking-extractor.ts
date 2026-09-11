/**
 * Extrai entidades específicas de transporte e hospedagem do roteiro em Markdown.
 *
 * Permite que a Central de Reservas gere deep-links diretos para o hotel exato
 * e para a companhia aérea exata recomendados pela IA, sem que o usuário precise
 * pesquisar do zero na plataforma.
 */

export interface ExtractedBookingInfo {
  hotelName?: string;
  hotelStars?: string;
  transportCompany?: string;
  transportModal?: string;
}

export function extractBookingEntities(markdown: string): ExtractedBookingInfo {
  if (!markdown) return {};

  const info: ExtractedBookingInfo = {};

  // 1. Tentar extrair hotel da tabela ou do texto
  // Exemplo: | **Hotel** | **NH Lisboa Campo Grande** – 4 estrelas...
  const hotelTableMatch = markdown.match(
    /\|\s*\*{0,2}Hotel\*{0,2}\s*\|\s*\*{0,2}([^|\n–—]+)\*{0,2}/i,
  );
  if (hotelTableMatch && hotelTableMatch[1]) {
    const raw = hotelTableMatch[1].replace(/\*\*/g, "").trim();
    if (raw && !raw.toLowerCase().includes("hospedagem")) {
      info.hotelName = raw;
    }
  }

  // Fallback para hotel no texto: "hospedagem é o **NH Lisboa Campo Grande**" ou "hotel **X**"
  if (!info.hotelName) {
    const textHotelMatch = markdown.match(
      /(?:hospedagem|hotel|pousada)(?:\s+(?:é|recomendado|sugerido|será))?\s+(?:o|no|na)?\s*\*\*([^*]+)\*\*/i,
    );
    if (textHotelMatch && textHotelMatch[1]) {
      info.hotelName = textHotelMatch[1].trim();
    }
  }

  // Extrair estrelas se houver (ex: "4 estrelas")
  const starsMatch = markdown.match(/(\d)\s*estrelas/i);
  if (starsMatch) {
    info.hotelStars = `${starsMatch[1]} estrelas`;
  }

  // 2. Tentar extrair companhia de transporte/voo
  // Exemplo: | **Voo** | **TAP Air Portugal** (ida e volta...
  const flightTableMatch = markdown.match(
    /\|\s*\*{0,2}(?:Voo|Transporte)\*{0,2}\s*\|\s*\*{0,2}([^|\n(–—]+)\*{0,2}/i,
  );
  if (flightTableMatch && flightTableMatch[1]) {
    const raw = flightTableMatch[1].replace(/\*\*/g, "").trim();
    if (raw && !raw.toLowerCase().includes("transporte") && !raw.toLowerCase().includes("ida e volta")) {
      info.transportCompany = raw;
    }
  }

  // Fallback para companhia no texto: "companhia **TAP Air Portugal**" ou "voo pela **X**"
  if (!info.transportCompany) {
    const textCompanyMatch = markdown.match(
      /(?:voo|companhia|voar|viajar)\s+(?:pela|pelo|com|na)\s+\*\*([^*]+)\*\*/i,
    );
    if (textCompanyMatch && textCompanyMatch[1]) {
      info.transportCompany = textCompanyMatch[1].trim();
    }
  }

  return info;
}
