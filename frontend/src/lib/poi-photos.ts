"use client";

import { useEffect, useState } from "react";

export interface PoiPhotoInfo {
  name: string;
  imageUrl: string;
  description?: string;
  category: string;
  source: "wikipedia" | "curated";
}

/**
 * Fotos temáticas de altíssima qualidade do Unsplash para fallback
 * quando o ponto não possuir artigo ou foto na Wikipedia.
 */
const CATEGORY_FALLBACK_PHOTOS: Record<string, string[]> = {
  Praia: [
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=800&q=80",
  ],
  Gastronomia: [
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
  ],
  "Natureza & Parques": [
    "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=800&q=80",
  ],
  "Cultura & História": [
    "https://images.unsplash.com/photo-1513584684374-8bab748fbf90?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80",
  ],
  "Vida Noturna & Bares": [
    "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80",
  ],
  Geral: [
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=800&q=80",
  ],
};

/**
 * Identifica a categoria da atração turística com base em palavras-chave no nome.
 */
export function inferCategory(name: string): string {
  const lower = name.toLowerCase();

  if (
    lower.includes("praia") ||
    lower.includes("beach") ||
    lower.includes("orla") ||
    lower.includes("arpoador") ||
    lower.includes("copacabana") ||
    lower.includes("ipanema") ||
    lower.includes("leblon") ||
    /\bmar\b/.test(lower) ||
    lower.includes("beira-mar")
  ) {
    return "Praia";
  }

  if (
    lower.includes("restaurante") ||
    lower.includes("confeitaria") ||
    lower.includes("café") ||
    lower.includes("bar") ||
    lower.includes("adega") ||
    lower.includes("bistrô") ||
    lower.includes("pizzaria") ||
    lower.includes("churrascaria") ||
    lower.includes("mercado") ||
    lower.includes("culinária") ||
    lower.includes("gastronomia")
  ) {
    return lower.includes("bar") || lower.includes("adega")
      ? "Vida Noturna & Bares"
      : "Gastronomia";
  }

  if (
    lower.includes("parque") ||
    lower.includes("jardim") ||
    lower.includes("floresta") ||
    lower.includes("montanha") ||
    lower.includes("morro") ||
    lower.includes("pedra") ||
    lower.includes("mirante") ||
    lower.includes("trilha") ||
    lower.includes("cachoeira")
  ) {
    return "Natureza & Parques";
  }

  if (
    lower.includes("museu") ||
    lower.includes("teatro") ||
    lower.includes("igreja") ||
    lower.includes("catedral") ||
    lower.includes("castelo") ||
    lower.includes("palácio") ||
    lower.includes("centro histórico") ||
    lower.includes("monumento") ||
    lower.includes("lapa") ||
    lower.includes("santa teresa")
  ) {
    return "Cultura & História";
  }

  return "Geral";
}

// Cache em memória de fotos já resolvidas na sessão
const memoryCache = new Map<string, PoiPhotoInfo>();

/**
 * Normaliza o título para consulta na Wikipedia.
 */
function normalizeTitleForWiki(name: string): string {
  return name
    .trim()
    .replace(/[–—]/g, "-")
    .replace(/\s+/g, "_");
}

/**
 * Busca foto oficial e resumo cultural na Wikipedia REST API,
 * com fallback inteligente para fotos temáticas do Unsplash.
 */
export async function fetchPoiPhoto(
  name: string,
  destination = "",
): Promise<PoiPhotoInfo> {
  const cacheKey = `${name.toLowerCase()}::${destination.toLowerCase()}`;
  if (memoryCache.has(cacheKey)) {
    return memoryCache.get(cacheKey)!;
  }

  // Tenta ler do sessionStorage no navegador
  if (typeof window !== "undefined") {
    try {
      const stored = sessionStorage.getItem(`poi_photo_${cacheKey}`);
      if (stored) {
        const parsed = JSON.parse(stored) as PoiPhotoInfo;
        memoryCache.set(cacheKey, parsed);
        return parsed;
      }
    } catch {
      // Ignora erro de acesso ao storage
    }
  }

  const category = inferCategory(name);
  let photoInfo: PoiPhotoInfo | null = null;

  // 1. Tenta buscar na Wikipedia em Português
  const cleanName = normalizeTitleForWiki(name);
  try {
    const wikiUrl = `https://pt.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(cleanName)}`;
    const response = await fetch(wikiUrl, {
      headers: { "Accept-Language": "pt-BR,pt;q=0.9" },
    });

    if (response.ok) {
      const data = await response.json();
      const imageUrl = data.thumbnail?.source || data.originalimage?.source;
      if (imageUrl) {
        photoInfo = {
          name,
          imageUrl,
          description: data.extract
            ? data.extract.slice(0, 160) + (data.extract.length > 160 ? "…" : "")
            : undefined,
          category,
          source: "wikipedia",
        };
      }
    }
  } catch {
    // Falha silenciosa de rede, segue para fallback
  }

  // 2. Se não encontrou, tenta com sufixo do destino ou Wikipedia em Inglês
  if (!photoInfo && destination) {
    try {
      const nameWithCity = normalizeTitleForWiki(`${name} ${destination.split(",")[0]}`);
      const wikiUrl = `https://pt.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(nameWithCity)}`;
      const response = await fetch(wikiUrl);
      if (response.ok) {
        const data = await response.json();
        const imageUrl = data.thumbnail?.source || data.originalimage?.source;
        if (imageUrl) {
          photoInfo = {
            name,
            imageUrl,
            description: data.extract
              ? data.extract.slice(0, 160) + (data.extract.length > 160 ? "…" : "")
              : undefined,
            category,
            source: "wikipedia",
          };
        }
      }
    } catch {
      // Falha silenciosa
    }
  }

  // 3. Fallback: Foto temática de alta resolução do Unsplash
  if (!photoInfo) {
    const fallbacks = CATEGORY_FALLBACK_PHOTOS[category] || CATEGORY_FALLBACK_PHOTOS.Geral;
    // Seleção determinística baseada no nome para consistência entre renders
    const hash = name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const selectedFallback = fallbacks[hash % fallbacks.length];

    photoInfo = {
      name,
      imageUrl: selectedFallback,
      description: `Atração turística em destaque para sua viagem.`,
      category,
      source: "curated",
    };
  }

  // Salva no cache
  memoryCache.set(cacheKey, photoInfo);
  if (typeof window !== "undefined") {
    try {
      sessionStorage.setItem(`poi_photo_${cacheKey}`, JSON.stringify(photoInfo));
    } catch {
      // Ignora erro de cota de storage
    }
  }

  return photoInfo;
}

/**
 * Hook React para carregar e sincronizar fotos de uma lista de atrações.
 */
export function usePoiPhotos(poiNames: string[], destination = "") {
  const [photos, setPhotos] = useState<Record<string, PoiPhotoInfo>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!poiNames || poiNames.length === 0) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);

    Promise.all(
      poiNames.map(async (name) => {
        const info = await fetchPoiPhoto(name, destination);
        return { name, info };
      }),
    ).then((results) => {
      if (!isMounted) return;
      const map: Record<string, PoiPhotoInfo> = {};
      for (const res of results) {
        map[res.name] = res.info;
      }
      setPhotos(map);
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [poiNames.join(","), destination]);

  return { photos, loading };
}
