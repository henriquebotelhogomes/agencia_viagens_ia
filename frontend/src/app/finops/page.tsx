import type { Metadata } from "next";
import { Activity, Coins, Database, Sparkles, TrendingDown } from "lucide-react";

import { CostChart } from "@/components/cost-chart";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, api } from "@/lib/api/client";
import type { FinOpsSummary } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Custo operacional",
  description:
    "Quanto custa operar a geração de roteiros: tokens medidos, custo real e economia frente ao GPT-4o.",
};

// Números mudam a cada execução; 60s equilibra frescor e carga no banco
export const revalidate = 60;

const nf = new Intl.NumberFormat("pt-BR");

function formatUsd(value: number): string {
  if (value === 0) return "US$ 0";
  if (value < 0.01) return `US$ ${value.toFixed(4)}`;
  return `US$ ${value.toFixed(2)}`;
}

export default async function FinOpsPage() {
  let summary: FinOpsSummary | null = null;
  let error: string | undefined;

  try {
    summary = await api.finops(30);
  } catch (cause) {
    error =
      cause instanceof ApiError
        ? cause.message
        : "Não foi possível carregar os dados de custo.";
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <header className="flex flex-col gap-3 border-b border-border pb-8">
        <p className="text-sm font-medium tracking-wide text-primary uppercase">
          FinOps
        </p>
        <h1 className="text-3xl sm:text-4xl">Quanto custa operar isto</h1>
        <p className="max-w-2xl text-muted-foreground">
          Todos os valores vêm de tokens <strong>medidos</strong> pelo provedor a
          cada chamada — não de estimativa. A comparação usa o preço do GPT-4o
          para o mesmo volume.
        </p>
      </header>

      {error ? (
        <p
          role="alert"
          className="mt-8 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      ) : null}

      {summary ? (
        summary.executions === 0 ? (
          <EmptyState />
        ) : (
          <Dashboard summary={summary} />
        )
      ) : null}
    </div>
  );
}

function Dashboard({ summary }: { summary: FinOpsSummary }) {
  const savingsPercent =
    summary.baseline_cost_usd > 0
      ? (summary.savings_usd / summary.baseline_cost_usd) * 100
      : 0;

  const metrics = [
    {
      icon: Activity,
      label: "Roteiros gerados",
      value: nf.format(summary.executions),
      detail: `média de ${summary.avg_duration_seconds.toFixed(0)}s por geração`,
    },
    {
      icon: Sparkles,
      label: "Tokens consumidos",
      value: nf.format(summary.total_tokens),
      detail: `em ${summary.window_days} dias`,
    },
    {
      icon: Coins,
      label: "Custo total",
      value: formatUsd(summary.cost_usd),
      detail: `${formatUsd(summary.cost_usd / summary.executions)} por roteiro`,
    },
    {
      icon: TrendingDown,
      label: "Economia vs GPT-4o",
      value: `${savingsPercent.toFixed(0)}%`,
      detail: `${formatUsd(summary.savings_usd)} a menos`,
      highlight: true,
    },
    {
      icon: Database,
      label: "Aproveitamento de cache",
      value: `${(summary.cache_hit_ratio * 100).toFixed(0)}%`,
      detail: "roteiros servidos sem custo de LLM",
    },
  ];

  return (
    <>
      <dl className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map(({ icon: Icon, label, value, detail, highlight }) => (
          <Card key={label}>
            <CardContent className="pt-5">
              <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Icon className="size-3.5" aria-hidden />
                {label}
              </dt>
              <dd className="mt-2">
                <span
                  className={`font-display text-3xl ${highlight ? "text-primary" : ""}`}
                >
                  {value}
                </span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  {detail}
                </span>
              </dd>
            </CardContent>
          </Card>
        ))}
      </dl>

      {summary.daily.length > 1 ? (
        <Card className="mt-8">
          <CardContent className="pt-5">
            <h2 className="mb-5 text-sm font-medium tracking-wide text-muted-foreground uppercase">
              Consumo por dia
            </h2>
            <CostChart data={summary.daily} />
          </CardContent>
        </Card>
      ) : null}

      <Card className="mt-8">
        <CardContent className="pt-5">
          <h2 className="mb-4 text-sm font-medium tracking-wide text-muted-foreground uppercase">
            Execuções por resultado
          </h2>
          <dl className="flex flex-wrap gap-6">
            {Object.entries(summary.by_status).map(([status, count]) => (
              <div key={status}>
                <dt className="text-xs text-muted-foreground capitalize">
                  {STATUS_LABELS[status] ?? status}
                </dt>
                <dd className="font-display text-2xl">{nf.format(count)}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </>
  );
}

const STATUS_LABELS: Record<string, string> = {
  succeeded: "Concluídos",
  failed: "Falhos",
  cancelled: "Cancelados",
  running: "Em andamento",
  queued: "Na fila",
};

function EmptyState() {
  return (
    <div className="mt-12 rounded-lg border border-dashed border-border px-6 py-16 text-center">
      <p className="font-medium">Nenhum roteiro gerado ainda</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Os números aparecem aqui depois da primeira geração. Cada execução
        registra os tokens que consumiu.
      </p>
    </div>
  );
}
