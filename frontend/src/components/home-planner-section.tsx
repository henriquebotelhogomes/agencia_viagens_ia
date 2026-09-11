"use client";

import { Coins, Compass, MapPinned, Radio } from "lucide-react";
import { useState } from "react";

import { BriefingForm } from "@/components/briefing-form";
import { DestinationShowcase } from "@/components/destination-showcase";
import type { Destination } from "@/lib/destinations";

const PILLARS = [
  {
    icon: Radio,
    title: "Acompanhe o raciocínio em tempo real",
    body: "Três agentes especializados colaboram passo a passo: o Guia Local descobre joias raras, a Logística calcula deslocamentos e o Arquiteto monta a narrativa diária.",
  },
  {
    icon: MapPinned,
    title: "Do roteiro textual para o mapa",
    body: "Todos os pontos turísticos, restaurantes e atrações sugeridos são geolocalizados e renderizados em um mapa interativo com MapLibre.",
  },
  {
    icon: Coins,
    title: "FinOps e transparência total de custos",
    body: "Veja exatamente a quantidade de tokens consumida por agente e a estimativa de custo de API para cada versão do seu roteiro.",
  },
];

export function HomePlannerSection() {
  const [selectedDestination, setSelectedDestination] =
    useState<Destination | null>(null);

  const handleSelectDestination = (destination: Destination) => {
    setSelectedDestination(destination);
    // Rola suavemente até o formulário de briefing
    const formElement = document.getElementById("planejador-formulario");
    if (formElement) {
      formElement.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="flex flex-col gap-16">
      {/* Vitrine Interativa de Destinos com Fotos */}
      <DestinationShowcase onSelectDestination={handleSelectDestination} />

      {/* Seção do Planejador com o Formulário de Briefing */}
      <section
        id="planejador-formulario"
        className="scroll-mt-24 rounded-3xl border border-border/80 bg-surface p-6 shadow-sm sm:p-10 lg:p-12"
        aria-labelledby="planejador-titulo"
      >
        <div className="grid items-start gap-12 lg:grid-cols-[1fr_30rem] lg:gap-16">
          <div className="flex flex-col gap-8">
            <div className="flex flex-col gap-4">
              <div className="inline-flex w-fit items-center gap-2 rounded-full bg-primary-subtle px-3 py-1 text-xs font-semibold text-primary">
                <Compass className="size-3.5" aria-hidden />
                <span>Configure o seu roteiro</span>
              </div>
              <h2
                id="planejador-titulo"
                className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl"
              >
                Planejamento sob medida por quem entende de viagem
              </h2>
              <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                Informe sua cidade de partida e o que você mais gosta de fazer.
                Nossos agentes usarão essas informações para montar uma
                experiência fluida, equilibrada e sem correrias desnecessárias.
              </p>
            </div>

            <dl className="flex flex-col gap-6 border-t border-border/60 pt-6">
              {PILLARS.map(({ icon: Icon, title, body }) => (
                <div key={title} className="flex flex-col gap-1">
                  <dt className="flex items-center gap-3 font-medium text-foreground">
                    <span
                      className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary-subtle text-primary shadow-xs"
                      aria-hidden
                    >
                      <Icon className="size-4.5" />
                    </span>
                    {title}
                  </dt>
                  <dd className="pl-12 text-sm text-muted-foreground">
                    {body}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="lg:sticky lg:top-24">
            <BriefingForm
              selectedDestination={selectedDestination}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
