import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TravelHero } from "@/components/travel-hero";

describe("TravelHero", () => {
  it("renderiza o título heroico, badges e informações principais", () => {
    render(<TravelHero />);

    expect(
      screen.getByRole("heading", {
        name: /para onde a sua imaginação quer te levar hoje\?/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/uma equipe de agentes inteligentes pesquisa os melhores pontos/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/acompanhamento em tempo real/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/pontos geolocalizados no mapa/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/transparência de custos e tokens/i),
    ).toBeInTheDocument();
  });
});
