"use client";

import { Check, Loader2, X } from "lucide-react";

import { Badge } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ExecutionStatus, ProgressEvent } from "@/lib/api/types";

/**
 * Etapas do job na ordem em que o worker as percorre.
 *
 * Os identificadores vêm de `src/worker/tasks.py` (STEP_*). Manter o rótulo aqui
 * e não no backend é deliberado: texto de interface é responsabilidade da UI.
 */
const STEPS = [
  {
    id: "cache",
    label: "Consultando roteiros anteriores",
    detail: "Se alguém já pediu algo parecido, reaproveitamos.",
  },
  {
    id: "orquestracao",
    label: "Agentes trabalhando",
    detail: "Guia local pesquisa, logística calcula, arquiteto monta.",
  },
  {
    id: "geocoding",
    label: "Localizando os pontos no mapa",
    detail: "Cada lugar sugerido ganha coordenadas.",
  },
  {
    id: "concluido",
    label: "Roteiro pronto",
    detail: "",
  },
] as const;

type StepState = "pending" | "active" | "done" | "failed";

interface AgentTimelineProps {
  events: ProgressEvent[];
  status: ExecutionStatus;
}

/**
 * Linha do tempo das etapas da geração (specs/09 §5.3).
 *
 * O estado de cada etapa é derivado do índice da etapa atual — assim uma
 * reconexão do SSE (que perde os eventos anteriores) ainda mostra o progresso
 * correto, em vez de zerar a lista.
 */
export function AgentTimeline({ events, status }: AgentTimelineProps) {
  const currentStep = events.at(-1)?.step ?? "cache";
  const currentIndex = Math.max(
    STEPS.findIndex((step) => step.id === currentStep),
    0,
  );
  const failed = status === "failed" || status === "cancelled";

  return (
    <ol className="flex flex-col gap-1" aria-label="Etapas da geração">
      {STEPS.map((step, index) => {
        const state: StepState = failed
          ? index === currentIndex
            ? "failed"
            : index < currentIndex
              ? "done"
              : "pending"
          : status === "succeeded" || index < currentIndex
            ? "done"
            : index === currentIndex
              ? "active"
              : "pending";

        const message =
          state === "active"
            ? events.findLast((event) => event.step === step.id)?.message
            : undefined;

        return (
          <li key={step.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <StepMarker state={state} />
              {index < STEPS.length - 1 ? (
                <span
                  className={cn(
                    "w-px flex-1 transition-colors",
                    state === "done" ? "bg-primary/40" : "bg-border",
                  )}
                  aria-hidden
                />
              ) : null}
            </div>

            <div className={cn("pb-5", index === STEPS.length - 1 && "pb-0")}>
              <p
                className={cn(
                  "text-sm font-medium transition-colors",
                  state === "pending" && "text-muted-foreground",
                  state === "failed" && "text-destructive",
                )}
              >
                {step.label}
              </p>
              {message ?? step.detail ? (
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {message ?? step.detail}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function StepMarker({ state }: { state: StepState }) {
  const base = "flex size-6 shrink-0 items-center justify-center rounded-full";

  if (state === "done") {
    return (
      <span className={cn(base, "bg-primary text-primary-foreground")} aria-hidden>
        <Check className="size-3.5" />
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className={cn(base, "bg-primary-subtle text-primary")} aria-hidden>
        <Loader2 className="size-3.5 animate-spin" />
      </span>
    );
  }
  if (state === "failed") {
    return (
      <span
        className={cn(base, "bg-destructive text-destructive-foreground")}
        aria-hidden
      >
        <X className="size-3.5" />
      </span>
    );
  }
  return (
    <span className={cn(base, "border border-border bg-surface")} aria-hidden />
  );
}

/** Rótulo do estado da execução, com a cor correspondente. */
export function StatusBadge({ status }: { status: ExecutionStatus }) {
  const config: Record<
    ExecutionStatus,
    { label: string; variant: "neutral" | "primary" | "success" | "destructive" }
  > = {
    queued: { label: "Na fila", variant: "neutral" },
    running: { label: "Gerando", variant: "primary" },
    succeeded: { label: "Concluído", variant: "success" },
    failed: { label: "Falhou", variant: "destructive" },
    cancelled: { label: "Cancelado", variant: "neutral" },
  };
  const { label, variant } = config[status];
  return <Badge variant={variant}>{label}</Badge>;
}
