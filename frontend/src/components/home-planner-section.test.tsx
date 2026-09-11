import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { HomePlannerSection } from "@/components/home-planner-section";

// Mock do next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("HomePlannerSection", () => {
  beforeEach(() => {
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it("renderiza a seção com os pilares, a vitrine de destinos e o formulário", () => {
    render(<HomePlannerSection />);

    expect(
      screen.getByText(/acompanhe o raciocínio em tempo real/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/do roteiro textual para o mapa/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/finops e transparência total de custos/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /planejamento sob medida por quem entende de viagem/i,
      }),
    ).toBeInTheDocument();
  });

  it("seleciona um destino popular ao clicar na vitrine", async () => {
    const user = userEvent.setup();
    render(<HomePlannerSection />);

    // Clica no botão "Planejar este destino" do primeiro card (Lisboa)
    const planejarButtons = screen.getAllByRole("button", {
      name: /planejar este destino/i,
    });
    await user.click(planejarButtons[0]);

    // O input de destino do formulário deve ser preenchido com Lisboa
    const destinoInput = screen.getByLabelText("Destino") as HTMLInputElement;
    expect(destinoInput.value).toBe("Lisboa, Portugal");
  });
});
