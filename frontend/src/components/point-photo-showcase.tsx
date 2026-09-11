"use client";

import { ArrowRight, Camera, ExternalLink, MapPin, Sparkles } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { PointDetailModal } from "@/components/point-detail-modal";
import { Card, CardContent } from "@/components/ui/card";
import type { PoiPhotoInfo } from "@/lib/poi-photos";

interface PointPhotoShowcaseProps {
  photos: Record<string, PoiPhotoInfo>;
  onFocusMap?: (name: string) => void;
  onScrollToItinerary?: (name: string) => void;
}

export function PointPhotoShowcase({
  photos,
  onFocusMap,
  onScrollToItinerary,
}: PointPhotoShowcaseProps) {
  const [selectedPoint, setSelectedPoint] = useState<PoiPhotoInfo | null>(null);
  const pointList = Object.values(photos);

  if (pointList.length === 0) return null;

  return (
    <section className="flex flex-col gap-4" aria-labelledby="vitrine-pontos-titulo">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-primary-subtle px-3 py-0.5 text-xs font-semibold text-primary">
            <Camera className="size-3.5" aria-hidden />
            <span>Galeria das Atrações</span>
          </div>
          <h2
            id="vitrine-pontos-titulo"
            className="mt-1.5 text-xl font-bold tracking-tight text-slate-900 sm:text-2xl"
          >
            Fotos dos Pontos de Interesse
          </h2>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Explore visualmente as atrações sugeridas pela equipe de agentes.
          </p>
        </div>
      </div>

      {/* Grid / Carrossel Horizontal de Fotos */}
      <div className="no-scrollbar -mx-4 flex gap-4 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-2 lg:grid-cols-4 sm:overflow-visible sm:px-0">
        {pointList.map((point) => (
          <article
            key={point.name}
            className="group relative flex w-64 shrink-0 flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md sm:w-auto"
          >
            {/* Foto da Atração */}
            <div
              className="relative aspect-[4/3] w-full cursor-pointer overflow-hidden bg-surface-muted"
              onClick={() => setSelectedPoint(point)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  setSelectedPoint(point);
                }
              }}
              aria-label={`Ampliar foto de ${point.name}`}
            >
              <Image
                src={point.imageUrl}
                alt={point.name}
                fill
                sizes="(max-width: 640px) 250px, (max-width: 1024px) 50vw, 25vw"
                className="object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

              {/* Badge de Categoria */}
              <div className="absolute top-2.5 left-2.5">
                <span className="rounded-full bg-white/95 px-2 py-0.5 text-[10px] font-bold text-slate-900 shadow-xs backdrop-blur-md">
                  {point.category}
                </span>
              </div>

              {/* Dica de ampliação */}
              <div className="absolute top-2.5 right-2.5 opacity-0 transition-opacity group-hover:opacity-100">
                <span className="flex size-6 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-xs">
                  <ExternalLink className="size-3" />
                </span>
              </div>
            </div>

            {/* Detalhes do Ponto */}
            <div className="flex flex-1 flex-col justify-between p-3.5">
              <div>
                <h3
                  className="line-clamp-1 font-bold text-sm text-slate-900 transition-colors group-hover:text-primary cursor-pointer"
                  onClick={() => setSelectedPoint(point)}
                >
                  {point.name}
                </h3>
                {point.description ? (
                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-600">
                    {point.description}
                  </p>
                ) : null}
              </div>

              {/* Botões de Ação Rápida */}
              <div className="mt-3 flex items-center gap-1.5 border-t border-border/60 pt-2.5">
                {onFocusMap ? (
                  <button
                    type="button"
                    onClick={() => onFocusMap(point.name)}
                    className="flex flex-1 items-center justify-center gap-1 rounded-md bg-primary-subtle py-1.5 text-xs font-semibold text-primary transition-colors hover:bg-primary hover:text-white"
                    title="Localizar ponto no mapa"
                  >
                    <MapPin className="size-3" />
                    <span>Mapa</span>
                  </button>
                ) : null}

                {onScrollToItinerary ? (
                  <button
                    type="button"
                    onClick={() => onScrollToItinerary(point.name)}
                    className="flex flex-1 items-center justify-center gap-1 rounded-md border border-border bg-surface py-1.5 text-xs font-medium text-slate-700 transition-colors hover:border-primary hover:text-primary"
                    title="Ver no texto do roteiro"
                  >
                    <span>Roteiro</span>
                    <ArrowRight className="size-3" />
                  </button>
                ) : null}
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* Modal para ver a foto expandida */}
      <PointDetailModal
        point={selectedPoint}
        onClose={() => setSelectedPoint(null)}
        onFocusMap={onFocusMap}
        onScrollToItinerary={onScrollToItinerary}
      />
    </section>
  );
}
