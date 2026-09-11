"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  Download,
  MapPin,
  Timer,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AgentTimeline, StatusBadge } from "@/components/agent-timeline";
import { BookingPanel } from "@/components/booking-panel";
import { CostPanel } from "@/components/cost-panel";
import { ItineraryMap } from "@/components/itinerary-map";
import { PointPhotoShowcase } from "@/components/point-photo-showcase";
import { RefinePanel } from "@/components/refine-panel";
import { VersionHistory } from "@/components/version-history";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, Skeleton } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { type ExecutionDetail, isTerminal } from "@/lib/api/types";
import { getDestinationHeroImage } from "@/lib/destinations";
import { downloadItineraryMarkdown } from "@/lib/export-markdown";
import { downloadItineraryPdf } from "@/lib/export-pdf";
import { useExecutionStream } from "@/lib/hooks/use-execution-stream";
import { usePoiPhotos } from "@/lib/poi-photos";

interface ExecutionViewProps {
  executionId: string;
  /** Estado carregado no servidor — evita tela vazia no primeiro paint. */
  initial: ExecutionDetail;
}

export function ExecutionView({ executionId, initial }: ExecutionViewProps) {
  const router = useRouter();
  const { events, status, latest, streamError } = useExecutionStream(
    executionId,
    initial.status,
  );

  const finished = isTerminal(status);

  const { data: execution } = useQuery({
    queryKey: ["execution", executionId, status],
    queryFn: () => api.getExecution(executionId),
    initialData: initial,
    enabled: finished,
    staleTime: 0,
  });

  const { data: geojson } = useQuery({
    queryKey: ["geojson", executionId],
    queryFn: () => api.getGeoJson(executionId),
    enabled: status === "succeeded",
    staleTime: Infinity,
  });

  const poiNames = geojson?.features.map((f) => f.properties.name) ?? [];
  const { photos } = usePoiPhotos(poiNames, execution.briefing.destino);

  const [highlighted, setHighlighted] = useState<string>();
  const [exportFormat, setExportFormat] = useState<"md" | "pdf">("md");

  const handleExport = () => {
    if (exportFormat === "pdf") {
      downloadItineraryPdf(execution);
    } else {
      downloadItineraryMarkdown(execution);
    }
  };

  /** Rollback: cria nova versão e navega para ela. */
  const handleRollback = async (targetExecutionId: string) => {
    const rolledBack = await api.rollback(
      executionId,
      targetExecutionId,
    );
    router.push(`/executions/${rolledBack.id}`);
  };

  const handleFocusMap = (name: string) => {
    setHighlighted(name);
    const mapEl = document.getElementById("mapa-roteiro");
    if (mapEl) {
      mapEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const handleScrollToItinerary = (name: string) => {
    const markdownContainer = document.getElementById("roteiro-markdown-conteudo");
    if (markdownContainer) {
      const elements = markdownContainer.querySelectorAll(
        "h1, h2, h3, h4, p, li, strong, b",
      );
      const lowerName = name.toLowerCase();
      for (const el of Array.from(elements)) {
        if (el.textContent?.toLowerCase().includes(lowerName)) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.classList.add(
            "bg-primary-subtle",
            "transition-all",
            "duration-700",
            "rounded",
            "px-1",
          );
          setTimeout(() => {
            el.classList.remove("bg-primary-subtle");
          }, 2500);
          return;
        }
      }
      markdownContainer.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const heroImage = getDestinationHeroImage(execution.briefing.destino);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {/* Banner de cabeçalho imersivo */}
      <header className="relative overflow-hidden rounded-2xl border border-border shadow-md">
        <div className="relative aspect-[21/9] min-h-48 w-full sm:aspect-[24/7]">
          <Image
            src={heroImage}
            alt={execution.briefing.destino}
            fill
            priority
            sizes="(max-width: 1200px) 100vw, 1200px"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-black/20" />

          {/* Botão de retorno e ações superiores */}
          <div className="absolute top-4 right-4 left-4 flex items-center justify-between">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 rounded-full bg-black/40 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-md transition-colors hover:bg-black/60"
            >
              <ArrowLeft className="size-3.5" aria-hidden />
              <span>Voltar ao início</span>
            </Link>

            {status === "succeeded" && execution.itinerary_markdown ? (
              <div className="flex items-center gap-1.5 rounded-lg bg-white/95 p-1 backdrop-blur-md shadow-sm border border-slate-200">
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as "md" | "pdf")}
                  className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-bold text-slate-800 shadow-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                  aria-label="Formato de exportação"
                >
                  <option value="md">Markdown (.md)</option>
                  <option value="pdf">PDF (.pdf)</option>
                </select>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleExport}
                  className="h-7 px-3 text-xs font-bold shadow-xs flex items-center gap-1.5"
                  aria-label="Baixar roteiro"
                >
                  <Download className="size-3.5" aria-hidden />
                  <span>Baixar</span>
                </Button>
              </div>
            ) : null}
          </div>

          {/* Informações centrais no banner */}
          <div className="absolute right-4 bottom-4 left-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={status} />
                {execution.duration_seconds ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-black/40 px-2.5 py-0.5 text-xs text-white/90 backdrop-blur-md">
                    <Timer className="size-3" aria-hidden />
                    {execution.duration_seconds}s
                  </span>
                ) : null}
              </div>
              <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-white drop-shadow-sm sm:text-4xl">
                Roteiro para {execution.briefing.destino}
              </h1>
              <p className="mt-1 text-sm text-white/80 drop-shadow-xs">
                Saindo de {execution.briefing.origem} · Roteiro personalizado por
                agentes de IA
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Estado da geração anunciado a leitores de tela conforme muda */}
      <p aria-live="polite" className="sr-only">
        {latest?.message ?? "Preparando a geração do roteiro."}
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-[20rem_1fr]">
        <aside className="flex flex-col gap-6">
          <Card>
            <CardContent className="pt-5">
              <h2 className="mb-4 text-xs font-bold tracking-wider text-slate-700 uppercase">
                Progresso
              </h2>
              <AgentTimeline events={events} status={status} />
            </CardContent>
          </Card>

          {streamError ? (
            <p className="flex gap-2 rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
              <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {streamError}
            </p>
          ) : null}

          {geojson && geojson.features.length > 0 ? (
            <Card>
              <CardContent className="pt-5">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-xs font-bold tracking-wider text-slate-700 uppercase">
                    Pontos do roteiro
                  </h2>
                  <span className="rounded-full bg-primary-subtle px-2 py-0.5 text-[10px] font-bold text-primary">
                    {geojson.features.length} locais
                  </span>
                </div>
                <ul className="flex flex-col gap-2">
                  {geojson.features.map((feature) => {
                    const name = feature.properties.name;
                    const photo = photos[name];
                    return (
                      <li key={name}>
                        <button
                          type="button"
                          onMouseEnter={() => setHighlighted(name)}
                          onMouseLeave={() => setHighlighted(undefined)}
                          onFocus={() => setHighlighted(name)}
                          onBlur={() => setHighlighted(undefined)}
                          onClick={() => handleFocusMap(name)}
                          className="group flex w-full items-center gap-2.5 rounded-lg border border-border/70 bg-surface p-1.5 text-left text-sm transition-all hover:border-primary/50 hover:bg-surface-muted hover:shadow-xs"
                          title="Clique para localizar no mapa"
                        >
                          <div className="relative size-10 shrink-0 overflow-hidden rounded-md bg-surface-muted border border-border/50">
                            {photo?.imageUrl ? (
                              <Image
                                src={photo.imageUrl}
                                alt={name}
                                fill
                                sizes="40px"
                                className="object-cover transition-transform duration-300 group-hover:scale-110"
                              />
                            ) : (
                              <div className="flex size-full items-center justify-center bg-primary-subtle text-primary">
                                <MapPin className="size-4" />
                              </div>
                            )}
                          </div>
                          <div className="flex min-w-0 flex-1 flex-col">
                            <span className="truncate font-bold text-xs text-slate-900 group-hover:text-primary transition-colors">
                              {name}
                            </span>
                            {photo?.category ? (
                              <span className="text-[10px] font-medium text-slate-500">
                                {photo.category}
                              </span>
                            ) : null}
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          {status === "succeeded" && execution.itinerary_markdown ? (
            <>
              <RefinePanel executionId={executionId} />
              <VersionHistory
                executionId={executionId}
                currentVersion={execution.version ?? 1}
                onRollback={handleRollback}
              />
            </>
          ) : null}
        </aside>

        <div className="flex min-w-0 flex-col gap-8">
          {execution.cost ? <CostPanel cost={execution.cost} /> : null}

          {status === "failed" ? (
            <Card className="border-destructive/40">
              <CardContent className="pt-5">
                <h2 className="flex items-center gap-2 font-medium text-destructive">
                  <AlertTriangle className="size-4" aria-hidden />
                  A geração não foi concluída
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  {execution.error ??
                    "Algo falhou durante a orquestração dos agentes."}
                </p>
                <Link
                  href="/"
                  className={`${buttonVariants({ variant: "secondary", size: "sm" })} mt-4`}
                >
                  Tentar de novo
                </Link>
              </CardContent>
            </Card>
          ) : null}

          {execution.itinerary_markdown ? (
            <>
              {/* Central de Reservas & Onde Comprar Passagens e Hotéis */}
              <BookingPanel
                briefing={execution.briefing}
                itineraryMarkdown={execution.itinerary_markdown}
              />

              <Card className="border-border shadow-sm">
                <CardContent
                  id="roteiro-markdown-conteudo"
                  className="prose max-w-none p-6 sm:p-8 text-slate-900"
                >
                  <Markdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      a: ({ href, children, ...props }) => (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-bold text-primary underline decoration-primary/50 underline-offset-2 transition-colors hover:text-primary-hover hover:decoration-primary"
                          {...props}
                        >
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {execution.itinerary_markdown}
                  </Markdown>
                </CardContent>
              </Card>

              {/* Vitrine e Galeria Fotográfica Interativa dos Pontos */}
              {poiNames.length > 0 ? (
                <PointPhotoShowcase
                  photos={photos}
                  onFocusMap={handleFocusMap}
                  onScrollToItinerary={handleScrollToItinerary}
                />
              ) : null}

              {/* Mapa Geolocalizado dos Pontos com Popups Fotográficos */}
              {geojson ? (
                <div id="mapa-roteiro" className="h-96 scroll-mt-20">
                  <ItineraryMap
                    geojson={geojson}
                    highlighted={highlighted}
                    photos={photos}
                  />
                </div>
              ) : null}
            </>
          ) : status !== "failed" ? (
            <ItinerarySkeleton />
          ) : null}
        </div>
      </div>
    </div>
  );
}

/** Esqueleto do roteiro: dá forma ao que está por vir (specs/09 §6). */
function ItinerarySkeleton() {
  return (
    <Card>
      <CardContent className="flex flex-col gap-6 pt-6">
        {[0, 1, 2].map((day) => (
          <div key={day} className="flex flex-col gap-2.5">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-4/6" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
