import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PointPhotoShowcase } from "@/components/point-photo-showcase";
import type { PoiPhotoInfo } from "@/lib/poi-photos";

const MOCK_PHOTOS: Record<string, PoiPhotoInfo> = {
  "Praia de Copacabana": {
    name: "Praia de Copacabana",
    imageUrl: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
    description: "Famosa praia da zona sul do Rio de Janeiro.",
    category: "Praia",
    source: "wikipedia",
  },
  "Confeitaria Colombo": {
    name: "Confeitaria Colombo",
    imageUrl: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5",
    description: "Histórica confeitaria no centro.",
    category: "Gastronomia",
    source: "wikipedia",
  },
};

describe("PointPhotoShowcase", () => {
  it("não renderiza nada quando não há fotos", () => {
    const { container } = render(<PointPhotoShowcase photos={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it("renderiza a galeria com os pontos e categorias", () => {
    render(<PointPhotoShowcase photos={MOCK_PHOTOS} />);

    expect(
      screen.getByRole("heading", { name: /fotos dos pontos de interesse/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Praia de Copacabana")).toBeInTheDocument();
    expect(screen.getByText("Confeitaria Colombo")).toBeInTheDocument();
    expect(screen.getByText("Praia")).toBeInTheDocument();
    expect(screen.getByText("Gastronomia")).toBeInTheDocument();
  });

  it("chama onFocusMap ao clicar no botão Mapa", async () => {
    const user = userEvent.setup();
    const handleFocusMap = vi.fn();
    render(
      <PointPhotoShowcase
        photos={MOCK_PHOTOS}
        onFocusMap={handleFocusMap}
      />,
    );

    const mapButtons = screen.getAllByRole("button", { name: /mapa/i });
    await user.click(mapButtons[0]);

    expect(handleFocusMap).toHaveBeenCalledWith("Praia de Copacabana");
  });

  it("chama onScrollToItinerary ao clicar no botão Roteiro", async () => {
    const user = userEvent.setup();
    const handleScroll = vi.fn();
    render(
      <PointPhotoShowcase
        photos={MOCK_PHOTOS}
        onScrollToItinerary={handleScroll}
      />,
    );

    const roteiroButtons = screen.getAllByRole("button", { name: /roteiro/i });
    await user.click(roteiroButtons[0]);

    expect(handleScroll).toHaveBeenCalledWith("Praia de Copacabana");
  });
});
