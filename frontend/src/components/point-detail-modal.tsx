"use client";

import { ArrowRight, MapPin, X } from "lucide-react";
import Image from "next/image";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import type { PoiPhotoInfo } from "@/lib/poi-photos";

interface PointDetailModalProps {
  point: PoiPhotoInfo | null;
  onClose: () => void;
  onFocusMap?: (name: string) => void;
  onScrollToItinerary?: (name: string) => void;
}

export function PointDetailModal({
  point,
  onClose,
  onFocusMap,
  onScrollToItinerary,
}: PointDetailModalProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    if (point) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [point, onClose]);

  if (!point) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-ponto-titulo"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative flex w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Botão de Fechar */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Fechar modal"
          className="absolute top-3 right-3 z-10 flex size-8 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-md transition-transform hover:scale-110"
        >
          <X className="size-4" />
        </button>

        {/* Imagem Ampliada */}
        <div className="relative aspect-video w-full overflow-hidden bg-surface-muted">
          <Image
            src={point.imageUrl}
            alt={point.name}
            fill
            sizes="(max-width: 768px) 100vw, 600px"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
          <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-white">
            <span className="rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-bold text-slate-900 backdrop-blur-md">
              {point.category}
            </span>
            {point.source === "wikipedia" ? (
              <span className="text-[10px] text-white/80">
                Fonte: Wikipedia & Wikimedia
              </span>
            ) : null}
          </div>
        </div>

        {/* Conteúdo Textual */}
        <div className="flex flex-col gap-4 p-5 sm:p-6">
          <div>
            <h3
              id="modal-ponto-titulo"
              className="text-2xl font-bold tracking-tight text-slate-900"
            >
              {point.name}
            </h3>
            {point.description ? (
              <p className="mt-2 text-sm leading-relaxed text-slate-700">
                {point.description}
              </p>
            ) : null}
          </div>

          {/* Ações Inteligentes */}
          <div className="mt-2 flex flex-wrap gap-2.5 border-t border-border pt-4">
            {onFocusMap ? (
              <Button
                type="button"
                variant="primary"
                size="sm"
                className="flex-1 font-semibold"
                onClick={() => {
                  onFocusMap(point.name);
                  onClose();
                }}
              >
                <MapPin className="size-4 mr-1.5" />
                Localizar no mapa
              </Button>
            ) : null}

            {onScrollToItinerary ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="flex-1 font-semibold"
                onClick={() => {
                  onScrollToItinerary(point.name);
                  onClose();
                }}
              >
                <span>Ver no roteiro</span>
                <ArrowRight className="size-4 ml-1.5" />
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
