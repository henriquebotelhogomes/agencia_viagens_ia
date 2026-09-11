import { describe, expect, it } from "vitest";

import { inferCategory } from "@/lib/poi-photos";

describe("inferCategory", () => {
  it("identifica corretamente praias", () => {
    expect(inferCategory("Praia de Copacabana")).toBe("Praia");
    expect(inferCategory("Arpoador Beach")).toBe("Praia");
    expect(inferCategory("Orla de Ipanema")).toBe("Praia");
  });

  it("identifica corretamente gastronomia e cafés", () => {
    expect(inferCategory("Confeitaria Colombo")).toBe("Gastronomia");
    expect(inferCategory("Restaurante Marius Degustare")).toBe("Gastronomia");
    expect(inferCategory("Café Lamas")).toBe("Gastronomia");
  });

  it("identifica corretamente bares e vida noturna", () => {
    expect(inferCategory("Bar do Mineiro")).toBe("Vida Noturna & Bares");
    expect(inferCategory("Adega Pérola")).toBe("Vida Noturna & Bares");
  });

  it("identifica parques e natureza", () => {
    expect(inferCategory("Jardim Botânico")).toBe("Natureza & Parques");
    expect(inferCategory("Parque Nacional da Tijuca")).toBe("Natureza & Parques");
    expect(inferCategory("Mirante Dona Marta")).toBe("Natureza & Parques");
  });

  it("identifica pontos históricos e culturais", () => {
    expect(inferCategory("Arcos da Lapa")).toBe("Cultura & História");
    expect(inferCategory("Museu do Amanhã")).toBe("Cultura & História");
    expect(inferCategory("Teatro Municipal")).toBe("Cultura & História");
  });
});
