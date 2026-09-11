import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchPoiPhoto, inferCategory, usePoiPhotos } from "@/lib/poi-photos";

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

  it("retorna Geral para locais genéricos", () => {
    expect(inferCategory("Passeio Aleatório")).toBe("Geral");
  });
});

describe("fetchPoiPhoto", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("retorna foto da Wikipedia quando a API responde com sucesso", async () => {
    const mockResponse = {
      ok: true,
      json: async () => ({
        thumbnail: { source: "https://upload.wikimedia.org/cristo.jpg" },
        extract: "O Cristo Redentor é uma estátua de Jesus Cristo no Rio.",
      }),
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

    const photo = await fetchPoiPhoto("Cristo Redentor", "Rio de Janeiro");
    expect(photo.source).toBe("wikipedia");
    expect(photo.imageUrl).toBe("https://upload.wikimedia.org/cristo.jpg");
    expect(photo.description).toContain("Cristo Redentor");
  });

  it("usa foto temática de fallback quando a Wikipedia falha ou não tem imagem", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
      }),
    );

    const photo = await fetchPoiPhoto("Praia Secreta Inexistente", "Florianópolis");
    expect(photo.source).toBe("curated");
    expect(photo.category).toBe("Praia");
    expect(photo.imageUrl).toContain("images.unsplash.com");
  });

  it("tenta busca com sufixo do destino quando a busca direta falha", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 404 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          thumbnail: { source: "https://upload.wikimedia.org/louvre.jpg" },
          extract: "Museu do Louvre em Paris.",
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const photo = await fetchPoiPhoto("Louvre", "Paris, França");
    expect(photo.source).toBe("wikipedia");
    expect(photo.imageUrl).toBe("https://upload.wikimedia.org/louvre.jpg");
  });

  it("lê do sessionStorage se a foto já estiver salva", async () => {
    const cachedData: PoiPhotoInfo = {
      name: "Parque Ibirapuera",
      imageUrl: "https://upload.wikimedia.org/ibi.jpg",
      category: "Natureza & Parques",
      source: "wikipedia",
    };
    sessionStorage.setItem(
      "poi_photo_parque ibirapuera::são paulo",
      JSON.stringify(cachedData),
    );

    const photo = await fetchPoiPhoto("Parque Ibirapuera", "São Paulo");
    expect(photo.imageUrl).toBe("https://upload.wikimedia.org/ibi.jpg");
  });
});

describe("usePoiPhotos hook", () => {
  it("retorna lista vazia e loading falso quando poiNames é vazio", () => {
    const { result } = renderHook(() => usePoiPhotos([]));
    expect(result.current.photos).toEqual({});
    expect(result.current.loading).toBe(false);
  });

  it("carrega as fotos dos pontos fornecidos", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          thumbnail: { source: "https://upload.wikimedia.org/foto.jpg" },
          extract: "Descrição do ponto",
        }),
      }),
    );

    const { result } = renderHook(() =>
      usePoiPhotos(["Museu de Arte"], "São Paulo"),
    );

    await waitFor(() => {
      expect(result.current.photos["Museu de Arte"]).toBeDefined();
    });

    expect(result.current.photos["Museu de Arte"].imageUrl).toBe(
      "https://upload.wikimedia.org/foto.jpg",
    );
  });
});
