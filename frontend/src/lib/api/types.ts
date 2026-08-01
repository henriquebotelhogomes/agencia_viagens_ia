/**
 * Contratos da API de roteiros.
 *
 * Espelham os schemas Pydantic de `src/api/schemas.py`. O Zod aqui não é
 * decorativo: valida a resposta em runtime, então uma mudança de contrato no
 * backend falha de forma explícita em vez de virar `undefined` na renderização.
 */
import { z } from "zod";

export const CURRENCIES = ["BRL", "USD", "EUR", "GBP"] as const;
export const LANGUAGES = ["pt-BR", "en-US", "es-ES"] as const;

export const EXECUTION_STATUSES = [
  "queued",
  "running",
  "succeeded",
  "failed",
  "cancelled",
] as const;

export type ExecutionStatus = (typeof EXECUTION_STATUSES)[number];

export const EXECUTION_KINDS = ["initial", "refine", "rollback"] as const;

export type ExecutionKind = (typeof EXECUTION_KINDS)[number];

/** Estados em que não há mais atualização a esperar. */
export const TERMINAL_STATUSES: readonly ExecutionStatus[] = [
  "succeeded",
  "failed",
  "cancelled",
];

export const isTerminal = (status: ExecutionStatus): boolean =>
  TERMINAL_STATUSES.includes(status);

// ---------------------------------------------------------------------------
// Entrada
// ---------------------------------------------------------------------------

/**
 * Briefing da viagem. Os limites replicam as validações do backend para que o
 * usuário receba o erro antes da requisição (FR-01).
 */
export const tripBriefingSchema = z.object({
  origem: z.string().trim().min(2, "informe a cidade de origem").max(120),
  destino: z.string().trim().min(2, "informe o destino").max(120),
  dias: z.coerce.number().int().min(1).max(30),
  interesses: z.string().trim().min(3, "descreva ao menos um interesse").max(500),
  moeda: z.enum(CURRENCIES),
  idioma: z.enum(LANGUAGES),
});

export type TripBriefing = z.infer<typeof tripBriefingSchema>;

/**
 * Formato **antes** da coerção — `dias` chega do `input` como string.
 *
 * O react-hook-form precisa dos dois tipos: um para os campos, outro para o que
 * o handler recebe depois de validado.
 */
export type TripBriefingInput = z.input<typeof tripBriefingSchema>;

// ---------------------------------------------------------------------------
// Saída
// ---------------------------------------------------------------------------

export const executionCreatedSchema = z.object({
  id: z.string(),
  status: z.enum(EXECUTION_STATUSES),
  stream_url: z.string(),
});

export type ExecutionCreated = z.infer<typeof executionCreatedSchema>;

export const costSummarySchema = z.object({
  prompt_tokens: z.number(),
  completion_tokens: z.number(),
  total_tokens: z.number(),
  cost_usd: z.number(),
  baseline_cost_usd: z.number(),
  savings_usd: z.number(),
  served_from_cache: z.boolean(),
});

export type CostSummary = z.infer<typeof costSummarySchema>;

export const executionDetailSchema = z.object({
  id: z.string(),
  status: z.enum(EXECUTION_STATUSES),
  briefing: tripBriefingSchema,
  created_at: z.string(),
  finished_at: z.string().nullable(),
  duration_seconds: z.number().nullable(),
  itinerary_markdown: z.string().nullable(),
  error: z.string().nullable(),
  used_fallback: z.boolean(),
  llm_gateway: z.string().nullable(),
  cost: costSummarySchema.nullable(),
  // Linhagem de versões (FR-40/FR-41)
  kind: z.enum(EXECUTION_KINDS).default("initial"),
  version: z.number().nullable().default(null),
  parent_execution_id: z.string().nullable().default(null),
  root_execution_id: z.string().nullable().default(null),
  refine_instruction: z.string().nullable().default(null),
});

export type ExecutionDetail = z.infer<typeof executionDetailSchema>;

/**
 * Percentual economizado frente ao custo de referência (GPT-4o).
 *
 * Derivado no cliente: o backend entrega os valores absolutos e não o
 * percentual, evitando duplicar a regra em dois lugares.
 */
export function savingsPercent(cost: CostSummary): number {
  if (cost.baseline_cost_usd <= 0) return 0;
  return (cost.savings_usd / cost.baseline_cost_usd) * 100;
}

export const progressEventSchema = z.object({
  execution_id: z.string(),
  status: z.enum(EXECUTION_STATUSES),
  message: z.string(),
  step: z.string().nullable(),
  at: z.string(),
});

export type ProgressEvent = z.infer<typeof progressEventSchema>;

/** Feature do GeoJSON entregue pela API (ADR-0009: só dados, sem render). */
export const geoFeatureSchema = z.object({
  type: z.literal("Feature"),
  geometry: z.object({
    type: z.literal("Point"),
    coordinates: z.tuple([z.number(), z.number()]),
  }),
  properties: z.object({ name: z.string() }).passthrough(),
});

export const geoJsonSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(geoFeatureSchema),
});

export type GeoJson = z.infer<typeof geoJsonSchema>;
export type GeoFeature = z.infer<typeof geoFeatureSchema>;

export const healthSchema = z.object({
  status: z.enum(["ok", "degraded"]),
  version: z.string(),
  environment: z.string(),
  dependencies: z.record(z.string(), z.boolean()),
});

export type Health = z.infer<typeof healthSchema>;

export const localizationOptionsSchema = z.object({
  currencies: z.record(z.string(), z.string()),
  languages: z.record(z.string(), z.string()),
});

export type LocalizationOptions = z.infer<typeof localizationOptionsSchema>;

/** Envelope de erro RFC 9457 servido pela API. */
export const problemDetailSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number(),
  detail: z.string(),
  instance: z.string().optional(),
  retry_after: z.number().optional(),
});

export type ProblemDetail = z.infer<typeof problemDetailSchema>;

// ---------------------------------------------------------------------------
// FinOps
// ---------------------------------------------------------------------------

export const finOpsDailyPointSchema = z.object({
  date: z.string(),
  total_tokens: z.number(),
  cost_usd: z.number(),
  executions: z.number(),
});

export const finOpsSummarySchema = z.object({
  window_days: z.number(),
  executions: z.number(),
  total_tokens: z.number(),
  cost_usd: z.number(),
  baseline_cost_usd: z.number(),
  savings_usd: z.number(),
  cache_hit_ratio: z.number(),
  avg_duration_seconds: z.number(),
  by_status: z.record(z.string(), z.number()),
  daily: z.array(finOpsDailyPointSchema),
});

export type FinOpsSummary = z.infer<typeof finOpsSummarySchema>;
export type FinOpsDailyPoint = z.infer<typeof finOpsDailyPointSchema>;

// ---------------------------------------------------------------------------
// Versionamento (FR-40 / FR-41)
// ---------------------------------------------------------------------------

export const versionSummarySchema = z.object({
  id: z.string(),
  version: z.number(),
  kind: z.enum(EXECUTION_KINDS),
  refine_instruction: z.string().nullable(),
  status: z.enum(EXECUTION_STATUSES),
  created_at: z.string(),
  duration_seconds: z.number().nullable(),
});

export type VersionSummary = z.infer<typeof versionSummarySchema>;

export const versionListSchema = z.object({
  root_execution_id: z.string(),
  current_version: z.number(),
  versions: z.array(versionSummarySchema),
});

export type VersionList = z.infer<typeof versionListSchema>;
