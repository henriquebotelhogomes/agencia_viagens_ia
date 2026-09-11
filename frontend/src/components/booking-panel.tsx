"use client";

import {
  Building2,
  CheckCircle2,
  ExternalLink,
  Hotel,
  MapPin,
  Plane,
  Ticket,
  Train,
} from "lucide-react";
import type { TripBriefing } from "@/lib/api/types";
import { extractBookingEntities } from "@/lib/booking-extractor";
import { slugify } from "@/lib/export-markdown";
import { Card, CardContent } from "@/components/ui/card";

interface BookingPanelProps {
  briefing: TripBriefing;
  itineraryMarkdown?: string | null;
}

export function BookingPanel({
  briefing,
  itineraryMarkdown,
}: BookingPanelProps) {
  const { origem, destino } = briefing;

  const entities = extractBookingEntities(itineraryMarkdown ?? "");
  const hotelName = entities.hotelName;
  const transportCompany = entities.transportCompany;

  const origemEncoded = encodeURIComponent(origem);
  const destinoEncoded = encodeURIComponent(destino);
  const origemSlug = slugify(origem);
  const destinoSlug = slugify(destino);

  // Consulta do voo específico com a companhia identificada
  const flightQuery = transportCompany
    ? `passagens de ${origem} para ${destino} ${transportCompany}`
    : `passagens de ${origem} para ${destino}`;
  const flightUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(flightQuery)}`;

  // Consulta do hotel específico com o nome identificado
  const hotelQuery = hotelName ? `${hotelName} ${destino}` : destino;
  const bookingHotelUrl = `https://www.booking.com/searchresults.pt-br.html?ss=${encodeURIComponent(hotelQuery)}`;
  const googleHotelsUrl = `https://www.google.com/travel/hotels/${destinoEncoded}?q=${encodeURIComponent(hotelQuery)}`;

  return (
    <Card className="border-border shadow-sm overflow-hidden no-print">
      <div className="border-b border-border/80 bg-slate-50/90 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-extrabold tracking-tight text-slate-900 uppercase flex items-center gap-2">
              <Ticket className="size-4 text-primary" aria-hidden />
              Central de Compra de Passagens & Reservas Diretas
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Acesse os links diretos para comprar as passagens e reservar o
              hotel especificados pelos agentes de IA para o seu roteiro.
            </p>
          </div>
          <span className="rounded-full bg-primary-subtle px-3 py-1 text-[11px] font-bold text-primary flex items-center gap-1">
            <CheckCircle2 className="size-3" />
            Links Diretos
          </span>
        </div>
      </div>

      <CardContent className="p-6 grid gap-6 md:grid-cols-2">
        {/* Coluna 1: Passagens de Avião, Trem e Ônibus */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 pb-1 border-b border-slate-200">
            <Plane className="size-4 text-primary" aria-hidden />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Passagens: Voo, Trem & Ônibus
            </h3>
          </div>

          <div className="flex flex-col gap-2.5">
            {/* Opção em Destaque: Voo/Companhia recomendada */}
            <a
              href={flightUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col gap-1.5 rounded-lg border-2 border-primary/40 bg-primary-subtle/30 p-3 transition-all hover:border-primary hover:bg-primary-subtle/60 hover:shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex size-7 items-center justify-center rounded-md bg-primary text-white">
                    <Plane className="size-4" aria-hidden />
                  </div>
                  <span className="text-xs font-extrabold text-slate-900 group-hover:text-primary transition-colors">
                    {transportCompany
                      ? `Comprar Passagem: ${transportCompany}`
                      : `Comprar Passagem Aérea`}
                  </span>
                </div>
                <span className="rounded-full bg-primary px-2 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider">
                  Recomendado
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-700">
                Trecho: <strong>{origem}</strong> ➔ <strong>{destino}</strong>
                {transportCompany ? ` pela ${transportCompany}` : ""}.
              </p>
              <div className="flex items-center justify-between text-[10px] font-bold text-primary pt-1">
                <span>Abrir cotação direta no Google Flights</span>
                <ExternalLink className="size-3.5" aria-hidden />
              </div>
            </a>

            {/* Opção Multimodal (Trens e Ônibus) */}
            <a
              href={`https://www.rome2rio.com/pt/map/${origemEncoded}/${destinoEncoded}`}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 transition-all hover:border-primary hover:bg-slate-50 hover:shadow-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 transition-colors group-hover:bg-primary-subtle group-hover:text-primary">
                  <Train className="size-4" aria-hidden />
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                      Rome2Rio (Trem, Ônibus e Avião)
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-semibold text-slate-600">
                      Multimodal
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 truncate">
                    Compara rotas de ferrovias, ônibus rodoviários e voos
                  </span>
                </div>
              </div>
              <ExternalLink
                className="size-3.5 shrink-0 text-slate-400 group-hover:text-primary transition-colors ml-2"
                aria-hidden
              />
            </a>

            {/* Passagens de Ônibus */}
            <a
              href={`https://www.clickbus.com.br/onibus/${origemSlug}/${destinoSlug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 transition-all hover:border-primary hover:bg-slate-50 hover:shadow-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 transition-colors group-hover:bg-primary-subtle group-hover:text-primary">
                  <Ticket className="size-4" aria-hidden />
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                      ClickBus
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-semibold text-slate-600">
                      Rodoviário
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 truncate">
                    Passagens de ônibus de {origem} para {destino}
                  </span>
                </div>
              </div>
              <ExternalLink
                className="size-3.5 shrink-0 text-slate-400 group-hover:text-primary transition-colors ml-2"
                aria-hidden
              />
            </a>
          </div>
        </div>

        {/* Coluna 2: Diárias de Hotel & Hospedagem */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 pb-1 border-b border-slate-200">
            <Hotel className="size-4 text-primary" aria-hidden />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Hospedagem: Hotel & Diárias
            </h3>
          </div>

          <div className="flex flex-col gap-2.5">
            {/* Opção em Destaque: Hotel recomendado */}
            <a
              href={bookingHotelUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col gap-1.5 rounded-lg border-2 border-primary/40 bg-primary-subtle/30 p-3 transition-all hover:border-primary hover:bg-primary-subtle/60 hover:shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex size-7 items-center justify-center rounded-md bg-primary text-white">
                    <Building2 className="size-4" aria-hidden />
                  </div>
                  <span className="text-xs font-extrabold text-slate-900 group-hover:text-primary transition-colors">
                    {hotelName
                      ? `Reservar no ${hotelName}`
                      : `Reservar Hotel em ${destino}`}
                  </span>
                </div>
                <span className="rounded-full bg-primary px-2 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider">
                  Hotel Indicado
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-700">
                {hotelName ? (
                  <>
                    Diárias para <strong>{hotelName}</strong> em {destino}
                    {entities.hotelStars ? ` (${entities.hotelStars})` : ""}.
                  </>
                ) : (
                  `Buscar hotéis recomendados em ${destino}.`
                )}
              </p>
              <div className="flex items-center justify-between text-[10px] font-bold text-primary pt-1">
                <span>Ver quartos e tarifas no Booking.com</span>
                <ExternalLink className="size-3.5" aria-hidden />
              </div>
            </a>

            {/* Comparador de Preços (Google Hotels) */}
            <a
              href={googleHotelsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 transition-all hover:border-primary hover:bg-slate-50 hover:shadow-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 transition-colors group-hover:bg-primary-subtle group-hover:text-primary">
                  <Hotel className="size-4" aria-hidden />
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                      Google Hotels
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-semibold text-slate-600">
                      Comparar Sites
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 truncate">
                    {hotelName
                      ? `Compara tarifas do ${hotelName} em todos os sites`
                      : `Compara tarifas de hotéis em ${destino}`}
                  </span>
                </div>
              </div>
              <ExternalLink
                className="size-3.5 shrink-0 text-slate-400 group-hover:text-primary transition-colors ml-2"
                aria-hidden
              />
            </a>

            {/* Airbnb */}
            <a
              href={`https://www.airbnb.com.br/s/${destinoEncoded}/homes`}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 transition-all hover:border-primary hover:bg-slate-50 hover:shadow-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 transition-colors group-hover:bg-primary-subtle group-hover:text-primary">
                  <MapPin className="size-4" aria-hidden />
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                      Airbnb
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-semibold text-slate-600">
                      Temporada
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 truncate">
                    Casas e apartamentos por temporada em {destino}
                  </span>
                </div>
              </div>
              <ExternalLink
                className="size-3.5 shrink-0 text-slate-400 group-hover:text-primary transition-colors ml-2"
                aria-hidden
              />
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
