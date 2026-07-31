"use client";

import {
  LngLatBounds,
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  Popup,
  type StyleSpecification,
} from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { GeoJson } from "@/lib/api/types";

import "maplibre-gl/dist/maplibre-gl.css";

/**
 * Estilo raster do OpenStreetMap.
 *
 * Evita depender de chave de API de provedor de tiles vetoriais: o mapa
 * funciona sem nenhuma credencial, coerente com a decisão de não adicionar
 * dependências pagas ao portfólio (ADR-0009).
 */
const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution:
        '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

interface ItineraryMapProps {
  geojson: GeoJson;
  /** Nome do local destacado (sincroniza com o hover no roteiro). */
  highlighted?: string;
}

/**
 * Mapa dos pontos do roteiro.
 *
 * Renderização 100% client-side a partir do GeoJSON da API (ADR-0009: o servidor
 * produz dados, o cliente decide como desenhar).
 */
export function ItineraryMap({ geojson, highlighted }: ItineraryMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Map<string, Marker>>(new Map());

  useEffect(() => {
    if (!containerRef.current || geojson.features.length === 0) return;

    // Cópia local: o cleanup não pode confiar em `markersRef.current`, que pode
    // ter mudado quando ele roda (aviso do react-hooks/exhaustive-deps).
    const markers = markersRef.current;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: OSM_STYLE,
      center: geojson.features[0].geometry.coordinates,
      zoom: 11,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new NavigationControl({ showCompass: false }));

    // Enquadra todos os pontos, com folga para não colar nas bordas
    const bounds = new LngLatBounds();
    for (const feature of geojson.features) {
      bounds.extend(feature.geometry.coordinates);
    }
    map.fitBounds(bounds, { padding: 56, maxZoom: 14, duration: 0 });

    for (const feature of geojson.features) {
      const name = feature.properties.name;
      const marker = new Marker({ color: "#c2542a" })
        .setLngLat(feature.geometry.coordinates)
        .setPopup(new Popup({ offset: 24, closeButton: false }).setText(name))
        .addTo(map);
      markers.set(name, marker);
    }

    return () => {
      markers.clear();
      map.remove();
      mapRef.current = null;
    };
  }, [geojson]);

  // Destaque sincronizado: abre o popup do item sob o cursor no roteiro
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !highlighted) return;

    const marker = markersRef.current.get(highlighted);
    if (!marker) return;

    marker.togglePopup();
    map.easeTo({ center: marker.getLngLat(), duration: 400 });

    return () => {
      if (marker.getPopup()?.isOpen()) marker.togglePopup();
    };
  }, [highlighted]);

  if (geojson.features.length === 0) {
    return (
      <div className="flex h-full min-h-64 items-center justify-center rounded-lg border border-border bg-surface-muted px-6 text-center text-sm text-muted-foreground">
        Nenhum ponto foi geolocalizado neste roteiro.
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      role="application"
      aria-label={`Mapa com ${geojson.features.length} pontos do roteiro`}
      className="h-full min-h-64 w-full overflow-hidden rounded-lg border border-border"
    />
  );
}
