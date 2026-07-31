"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, MapPin, Timer } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AgentTimeline, StatusBadge } from "@/components/agent-timeline";
import { CostPanel } from "@/components/cost-panel";
import { ItineraryMap } from "@/components/itinerary-map";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, Skeleton } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { type ExecutionDetail, isTerminal } from "@/lib/api/types";
import { useExecutionStream } from "@/lib/hooks/use-execution-stream";

interface ExecutionViewProps {
  executionId: string;
  /** Estado carregado no servidor — evita tela vazia no primeiro paint. */
  initial: ExecutionDetail;
}

export function ExecutionView({ executionId, initial }: ExecutionViewProps) {
  const { events, status, latest, streamError } = useExecutionStream(
    executionId,
    initial.status,
  );

  const finished = isTerminal(status);

  /**
   * Detalhe da execução. Só busca de novo quando o stream indica que terminou —
   * enquanto roda, quem informa o progresso é o SSE, sem polling.
   */
  const { data: execution } = useQuery({
    queryKey: ["execution", executionId, status],
    queryFn: () => api.getExecution(executionId),
    initialData: initial,
    enabled: finished,
    staleTime: finished ? Infinity : 0,
  });

  const { data: geojson } = useQuery({
    queryKey: ["geojson", executionId],
    queryFn: () => api.getGeoJson(executionId),
    enabled: status === "succeeded",
    staleTime: Infinity,
  });

  const [highlighted, setHighlighted] = useState<string>();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <Link
        href="/"
        className={buttonVariants({ variant: "ghost", size: "sm" })}
      >
        <ArrowLeft aria-hidden />
        Novo roteiro
      </Link>

      <header className="mt-4 flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
        <div>
          <p className="text-xs tracking-wide text-muted-foreground uppercase">
            {execution.briefing.dias}{" "}
            {execution.briefing.dias === 1 ? "dia" : "dias"} ·{" "}
            {execution.briefing.moeda}
          </p>
          <h1 className="mt-1 text-3xl sm:text-4xl">
            {execution.briefing.destino}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            saindo de {execution.briefing.origem}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {execution.duration_seconds ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <Timer className="size-3.5" aria-hidden />
              {execution.duration_seconds.toFixed(0)}s
            </span>
          ) : null}
          <StatusBadge status={status} />
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
              <h2 className="mb-4 text-sm font-medium tracking-wide text-muted-foreground uppercase">
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
                <h2 className="mb-3 text-sm font-medium tracking-wide text-muted-foreground uppercase">
                  Pontos do roteiro
                </h2>
                <ul className="flex flex-col gap-1">
                  {geojson.features.map((feature) => (
                    <li key={feature.properties.name}>
                      <button
                        type="button"
                        onMouseEnter={() =>
                          setHighlighted(feature.properties.name)
                        }
                        onFocus={() => setHighlighted(feature.properties.name)}
                        onMouseLeave={() => setHighlighted(undefined)}
                        onBlur={() => setHighlighted(undefined)}
                        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors hover:bg-surface-muted"
                      >
                        <MapPin
                          className="size-3.5 shrink-0 text-primary"
                          aria-hidden
                        />
                        {feature.properties.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}
        </aside>

        <div className="flex min-w-0 flex-col gap-6">
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
              <Card>
                <CardContent className="prose prose-stone dark:prose-invert max-w-none pt-5">
                  <Markdown remarkPlugins={[remarkGfm]}>
                    {execution.itinerary_markdown}
                  </Markdown>
                </CardContent>
              </Card>

              {geojson ? (
                <div className="h-96">
                  <ItineraryMap geojson={geojson} highlighted={highlighted} />
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
