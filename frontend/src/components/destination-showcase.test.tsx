import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DestinationShowcase } from "@/components/destination-showcase";

describe("DestinationShowcase", () => {
  it("renderiza o título da vitrine e destinos populares", () => {
    render(<DestinationShowcase onSelectDestination={vi.fn()} />);

    expect(
      screen.getByRole("heading", {
        name: /destinos que despertam o desejo de viajar/i,
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Lisboa, Portugal")).toBeInTheDocument();
    expect(screen.getByText("Rio de Janeiro, Brasil")).toBeInTheDocument();
  });

  it("filtra destinos ao clicar em uma categoria", async () => {
    const user = userEvent.setup();
    render(<DestinationShowcase onSelectDestination={vi.fn()} />);

    const tabPraia = screen.getByRole("tab", { name: /praias & ilhas/i });
    await user.click(tabPraia);

    // Destinos de praia devem estar presentes
    expect(screen.getByText("Rio de Janeiro, Brasil")).toBeInTheDocument();
    expect(screen.getByText("Santorini, Grécia")).toBeInTheDocument();

    // Destino estritamente cultural (ex: Tóquio) não deve aparecer na aba praia
    expect(screen.queryByText("Tóquio, Japão")).not.toBeInTheDocument();
  });

  it("chama onSelectDestination ao clicar no botão de planejar", async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();
    render(<DestinationShowcase onSelectDestination={handleSelect} />);

    const buttons = screen.getAllByRole("button", {
      name: /planejar este destino/i,
    });
    await user.click(buttons[0]);

    expect(handleSelect).toHaveBeenCalledTimes(1);
    expect(handleSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "lisboa",
        name: "Lisboa, Portugal",
        currency: "EUR",
      }),
    );
  });
});
