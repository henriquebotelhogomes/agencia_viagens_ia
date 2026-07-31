"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FinOpsDailyPoint } from "@/lib/api/types";

const nf = new Intl.NumberFormat("pt-BR");

/** Formata a data ISO como "31/07", suficiente para o eixo. */
function shortDate(iso: unknown): string {
  if (typeof iso !== "string") return "";
  const [, month, day] = iso.split("-");
  return day && month ? `${day}/${month}` : iso;
}

/**
 * Consumo de tokens por dia.
 *
 * Área em vez de barras: a leitura pretendida é a tendência do consumo ao longo
 * do tempo, não a comparação entre dias isolados.
 */
export function CostChart({ data }: { data: FinOpsDailyPoint[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="tokens" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.28} />
              <stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={shortDate}
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            stroke="var(--border)"
          />
          <YAxis
            tickFormatter={(value) =>
              Number(value) >= 1000
                ? `${Math.round(Number(value) / 1000)}k`
                : String(value)
            }
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            stroke="var(--border)"
            width={44}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "0.5rem",
              fontSize: "0.8rem",
            }}
            labelFormatter={shortDate}
            formatter={(value) => [`${nf.format(Number(value))} tokens`, "consumo"]}
          />
          <Area
            type="monotone"
            dataKey="total_tokens"
            stroke="var(--primary)"
            strokeWidth={2}
            fill="url(#tokens)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
