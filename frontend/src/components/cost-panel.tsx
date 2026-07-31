import { Coins, Database, Sparkles, TrendingDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { type CostSummary, savingsPercent } from "@/lib/api/types";

/** Formata valores muito pequenos sem virar "$0.00". */
function formatUsd(value: number): string {
  if (value === 0) return "US$ 0";
  if (value < 0.01) return `US$ ${value.toFixed(4)}`;
  return `US$ ${value.toFixed(2)}`;
}

const formatTokens = (value: number) =>
  new Intl.NumberFormat("pt-BR").format(value);

/**
 * Custo real da execução (specs/09 §5.6 — FinOps visível).
 *
 * Os números vêm medidos do provedor, não estimados: o worker registra os tokens
 * que a chamada de LLM efetivamente consumiu.
 */
export function CostPanel({ cost }: { cost: CostSummary }) {
  const percent = savingsPercent(cost);

  const metrics = [
    {
      icon: Sparkles,
      label: "Tokens consumidos",
      value: formatTokens(cost.total_tokens),
      detail: `${formatTokens(cost.prompt_tokens)} entrada · ${formatTokens(cost.completion_tokens)} saída`,
    },
    {
      icon: Coins,
      label: "Custo desta geração",
      value: formatUsd(cost.cost_usd),
      detail: "medido, não estimado",
    },
    {
      icon: TrendingDown,
      label: "Economia vs GPT-4o",
      value: `${percent.toFixed(0)}%`,
      detail: `${formatUsd(cost.savings_usd)} a menos que ${formatUsd(cost.baseline_cost_usd)}`,
      highlight: true,
    },
  ];

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium tracking-wide text-muted-foreground uppercase">
            Custo da operação
          </h2>
          {cost.served_from_cache ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-subtle px-2.5 py-0.5 text-xs font-medium text-accent">
              <Database className="size-3" aria-hidden />
              servido do cache
            </span>
          ) : null}
        </div>

        <dl className="grid gap-4 sm:grid-cols-3">
          {metrics.map(({ icon: Icon, label, value, detail, highlight }) => (
            <div key={label} className="flex flex-col gap-1">
              <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Icon className="size-3.5" aria-hidden />
                {label}
              </dt>
              <dd>
                <span
                  className={`font-display text-2xl ${highlight ? "text-primary" : ""}`}
                >
                  {value}
                </span>
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {detail}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
