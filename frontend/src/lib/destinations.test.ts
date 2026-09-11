import { describe, expect, it } from "vitest";

import {
  POPULAR_DESTINATIONS,
  getDestinationHeroImage,
} from "@/lib/destinations";

describe("destinations", () => {
  it("contém destinos populares estruturados", () => {
    expect(POPULAR_DESTINATIONS.length).toBeGreaterThan(0);
    const lisboa = POPULAR_DESTINATIONS.find((d) => d.id === "lisboa");
    expect(lisboa).toBeDefined();
    expect(lisboa?.name).toBe("Lisboa, Portugal");
  });

  it("retorna imagem do destino quando encontrado", () => {
    const img = getDestinationHeroImage("Lisboa");
    expect(img).toContain("images.unsplash.com");
  });

  it("retorna imagem de fallback quando destino é desconhecido", () => {
    const fallbackImg = getDestinationHeroImage("Cidade Totalmente Inexistente");
    expect(fallbackImg).toBe(
      "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80",
    );
  });
});
