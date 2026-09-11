"use client";

import { ArrowRight, Clock, MapPin, Sparkles } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  type Destination,
  DESTINATION_CATEGORIES,
  POPULAR_DESTINATIONS,
} from "@/lib/destinations";

interface DestinationShowcaseProps {
  onSelectDestination: (destination: Destination) => void;
}

export function DestinationShowcase({
  onSelectDestination,
}: DestinationShowcaseProps) {
  const [activeCategory, setActiveCategory] = useState<string>("todos");

  const filteredDestinations =
    activeCategory === "todos"
      ? POPULAR_DESTINATIONS
      : POPULAR_DESTINATIONS.filter(
          (dest) => dest.category === activeCategory,
        );

  return (
    <section className="flex flex-col gap-8 py-8" aria-labelledby="destinos-titulo">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-accent-subtle px-3 py-1 text-xs font-semibold text-accent">
            <Sparkles className="size-3.5" aria-hidden />
            Inspire-se para a sua jornada
          </div>
          <h2
            id="destinos-titulo"
            className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl"
          >
            Destinos que despertam o desejo de viajar
          </h2>
          <p className="mt-1 text-base text-muted-foreground">
            Escolha uma cidade abaixo para preencher o roteiro com sugestões de
            dias e atrações em 1 clique.
          </p>
        </div>
      </div>

      {/* Filtros por Categoria */}
      <div
        className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0"
        role="tablist"
        aria-label="Categorias de destinos"
      >
        {DESTINATION_CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveCategory(cat.id)}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-xs font-medium transition-all ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "border border-border bg-surface text-muted-foreground hover:border-primary/50 hover:text-foreground"
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Grid de Destinos */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {filteredDestinations.map((dest) => (
          <article
            key={dest.id}
            className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all duration-300 hover:-translate-y-1.5 hover:shadow-lg"
          >
            {/* Imagem do Destino */}
            <div className="relative aspect-[4/3] w-full overflow-hidden bg-surface-muted">
              <Image
                src={dest.imageUrl}
                alt={dest.name}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                className="object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />

              {/* Badges Flutuantes */}
              <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                {dest.badge ? (
                  <span className="rounded-full bg-white/95 px-2.5 py-0.5 text-[11px] font-bold text-slate-900 shadow-xs backdrop-blur-md">
                    {dest.badge}
                  </span>
                ) : null}
              </div>

              <div className="absolute right-3 bottom-3 left-3 flex items-center justify-between text-xs text-white">
                <span className="inline-flex items-center gap-1 font-medium drop-shadow-sm">
                  <MapPin className="size-3.5 text-accent" aria-hidden />
                  {dest.country}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-black/40 px-2 py-0.5 text-[11px] backdrop-blur-sm">
                  <Clock className="size-3" aria-hidden />
                  {dest.suggestedDays} dias
                </span>
              </div>
            </div>

            {/* Conteúdo Textual */}
            <div className="flex flex-1 flex-col justify-between p-4">
              <div className="flex flex-col gap-1.5">
                <h3 className="text-xl font-medium tracking-tight text-foreground">
                  {dest.name}
                </h3>
                <p className="line-clamp-2 text-xs text-muted-foreground">
                  {dest.tagline}
                </p>

                {/* Destaques */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {dest.highlights.slice(0, 2).map((highlight) => (
                    <span
                      key={highlight}
                      className="rounded bg-surface-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                    >
                      {highlight}
                    </span>
                  ))}
                </div>
              </div>

              {/* Ação Interativa com 1 Clique */}
              <div className="mt-4 border-t border-border/60 pt-3">
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  className="w-full justify-between font-bold text-white shadow-sm transition-all hover:bg-primary-hover hover:shadow-md"
                  onClick={() => onSelectDestination(dest)}
                >
                  <span className="font-semibold text-white">Planejar este destino</span>
                  <ArrowRight
                    className="size-4 text-white transition-transform group-hover:translate-x-1"
                    aria-hidden
                  />
                </Button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
