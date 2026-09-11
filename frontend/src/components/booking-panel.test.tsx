import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BookingPanel } from "./booking-panel";
import type { TripBriefing } from "@/lib/api/types";

describe("BookingPanel", () => {
  const briefing: TripBriefing = {
    origem: "São Paulo",
    destino: "Lisboa",
    dias: 5,
    interesses: "Cultura e Gastronomia",
    moeda: "EUR",
    idioma: "pt-BR",
  };

  it("renderiza os links com hotel e companhia aérea específicos extraídos do roteiro", () => {
    const markdownWithEntities = `
# Lisboa em 3 dias

| Item | Descrição | Tarifa | Total |
|---|---|---|---|
| **Voo** | **TAP Air Portugal** (ida e volta) | € 1.200 | € 1.200 |
| **Hotel** | **NH Lisboa Campo Grande** - 4 estrelas | € 75 | € 225 |
`;

    render(
      <BookingPanel
        briefing={briefing}
        itineraryMarkdown={markdownWithEntities}
      />,
    );

    // Deve destacar o hotel específico e a companhia específica
    expect(
      screen.getByText(/comprar passagem: tap air portugal/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/reservar no nh lisboa campo grande/i),
    ).toBeInTheDocument();

    const flightLink = screen.getByRole("link", {
      name: /comprar passagem: tap air portugal/i,
    });
    const flightHref = decodeURIComponent(flightLink.getAttribute("href") ?? "");
    expect(flightHref).toContain("TAP Air Portugal");

    const hotelLink = screen.getByRole("link", {
      name: /reservar no nh lisboa campo grande/i,
    });
    const hotelHref = decodeURIComponent(hotelLink.getAttribute("href") ?? "");
    expect(hotelHref).toContain("NH Lisboa Campo Grande");
  });

  it("renderiza opções padrão de busca quando não há entidades específicas no markdown", () => {
    render(<BookingPanel briefing={briefing} />);

    expect(
      screen.getByRole("heading", { name: /central de compra/i }),
    ).toBeInTheDocument();

    const flightLink = screen.getByRole("link", {
      name: /comprar passagem aérea/i,
    });
    expect(flightLink).toBeInTheDocument();

    const hotelLink = screen.getByRole("link", {
      name: /reservar hotel em lisboa/i,
    });
    expect(hotelLink).toBeInTheDocument();
  });
});
