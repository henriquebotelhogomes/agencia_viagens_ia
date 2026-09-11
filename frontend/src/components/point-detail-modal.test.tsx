import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PointDetailModal } from "@/components/point-detail-modal";
import type { PoiPhotoInfo } from "@/lib/poi-photos";

const MOCK_POINT: PoiPhotoInfo = {
  name: "Torre de Belém",
  imageUrl: "https://images.unsplash.com/photo-1507525428034",
  description: "Monumento histórico fortificado às margens do Rio Tejo.",
  category: "Cultura & História",
  source: "wikipedia",
};

describe("PointDetailModal", () => {
  it("não renderiza nada se point for null", () => {
    const { container } = render(
      <PointDetailModal point={null} onClose={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renderiza detalhes do ponto turístico", () => {
    render(<PointDetailModal point={MOCK_POINT} onClose={vi.fn()} />);

    expect(screen.getByText("Torre de Belém")).toBeInTheDocument();
    expect(
      screen.getByText(/monumento histórico fortificado/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Cultura & História")).toBeInTheDocument();
    expect(screen.getByText(/fonte: wikipedia/i)).toBeInTheDocument();
  });

  it("renderiza ponto com source curated e sem descrição", () => {
    const curatedPoint: PoiPhotoInfo = {
      name: "Ponto Curado",
      imageUrl: "https://images.unsplash.com/photo-1507525428034",
      category: "Praia",
      source: "curated",
    };
    render(<PointDetailModal point={curatedPoint} onClose={vi.fn()} />);

    expect(screen.getByText("Ponto Curado")).toBeInTheDocument();
    expect(screen.queryByText(/fonte: wikipedia/i)).not.toBeInTheDocument();
  });

  it("chama onClose ao clicar no botão de fechar", async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(<PointDetailModal point={MOCK_POINT} onClose={handleClose} />);

    const closeBtn = screen.getByLabelText(/fechar modal/i);
    await user.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("chama onClose ao pressionar Escape e ignora outras teclas", () => {
    const handleClose = vi.fn();
    render(<PointDetailModal point={MOCK_POINT} onClose={handleClose} />);

    fireEvent.keyDown(window, { key: "Enter" });
    expect(handleClose).not.toHaveBeenCalled();

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("chama onFocusMap e onScrollToItinerary ao clicar nos botões de ação", async () => {
    const user = userEvent.setup();
    const handleFocusMap = vi.fn();
    const handleScroll = vi.fn();
    const handleClose = vi.fn();

    render(
      <PointDetailModal
        point={MOCK_POINT}
        onClose={handleClose}
        onFocusMap={handleFocusMap}
        onScrollToItinerary={handleScroll}
      />,
    );

    const mapBtn = screen.getByRole("button", { name: /localizar no mapa/i });
    await user.click(mapBtn);
    expect(handleFocusMap).toHaveBeenCalledWith("Torre de Belém");
    expect(handleClose).toHaveBeenCalled();

    const scrollBtn = screen.getByRole("button", { name: /ver no roteiro/i });
    await user.click(scrollBtn);
    expect(handleScroll).toHaveBeenCalledWith("Torre de Belém");
  });
});
