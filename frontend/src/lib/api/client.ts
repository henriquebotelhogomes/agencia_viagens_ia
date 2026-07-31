/**
 * Cliente HTTP da API de roteiros.
 *
 * Duas responsabilidades: falar com a API e traduzir falha em algo que a UI
 * saiba apresentar. Erros chegam no envelope RFC 9457 — a mensagem exibida ao
 * usuário vem do campo `detail`, nunca de um stack trace (specs/09 §6).
 */
import {
  type ExecutionCreated,
  type ExecutionDetail,
  type FinOpsSummary,
  type GeoJson,
  type Health,
  type LocalizationOptions,
  type ProblemDetail,
  type TripBriefing,
  executionCreatedSchema,
  executionDetailSchema,
  finOpsSummarySchema,
  geoJsonSchema,
  healthSchema,
  localizationOptionsSchema,
  problemDetailSchema,
} from "./types";

/** Base da API. Em produção vem do ambiente; em dev, o padrão local. */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

/** Erro com informação suficiente para a UI decidir o que mostrar. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly problem?: ProblemDetail,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** Cota de execuções esgotada (FR-09) — a UI sugere aguardar. */
  get isRateLimited(): boolean {
    return this.status === 429;
  }

  /** Segundos até liberar, quando a API informa. */
  get retryAfterSeconds(): number | undefined {
    return this.problem?.retry_after;
  }
}

async function request<T>(
  path: string,
  schema: { parse: (data: unknown) => T },
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    // Falha de rede: a API pode estar dormindo (dynos Eco adormecem)
    throw new ApiError(
      "Não foi possível falar com o serviço. Verifique sua conexão e tente novamente.",
      0,
      undefined,
    );
  }

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return schema.parse(undefined);
  }

  return schema.parse(await response.json());
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const problem = problemDetailSchema.parse(await response.json());
    return new ApiError(problem.detail, response.status, problem);
  } catch {
    // Resposta fora do padrão RFC 9457 (proxy, gateway, HTML de erro)
    return new ApiError(
      `O serviço respondeu com erro ${response.status}.`,
      response.status,
    );
  }
}

export const api = {
  health: () => request("/health", healthSchema, { cache: "no-store" }),

  localization: () =>
    request("/v1/localization", localizationOptionsSchema, {
      // Moedas e idiomas mudam raramente: vale cachear no servidor
      next: { revalidate: 3600 },
    } as RequestInit),

  /**
   * Cria a execução e devolve o identificador para acompanhar o progresso.
   *
   * @param idempotencyKey Repetir a mesma chave devolve a execução original,
   *   evitando cobrança dupla se o usuário reenviar o formulário.
   */
  createExecution: (briefing: TripBriefing, idempotencyKey?: string) =>
    request<ExecutionCreated>("/v1/executions", executionCreatedSchema, {
      method: "POST",
      body: JSON.stringify(briefing),
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
    }),

  getExecution: (id: string) =>
    request<ExecutionDetail>(`/v1/executions/${id}`, executionDetailSchema, {
      cache: "no-store",
    }),

  getGeoJson: (id: string) =>
    request<GeoJson>(`/v1/executions/${id}/geojson`, geoJsonSchema, {
      cache: "no-store",
    }),

  cancelExecution: (id: string) =>
    request<void>(
      `/v1/executions/${id}/cancel`,
      { parse: () => undefined },
      { method: "POST" },
    ),

  /** URL do fluxo SSE de progresso, consumida por `EventSource`. */
  streamUrl: (id: string) => `${API_BASE_URL}/v1/executions/${id}/stream`,

  finops: (days = 30) =>
    request<FinOpsSummary>(`/v1/finops?days=${days}`, finOpsSummarySchema, {
      cache: "no-store",
    }),
};

export type {
  ExecutionCreated,
  ExecutionDetail,
  FinOpsSummary,
  GeoJson,
  Health,
  LocalizationOptions,
};
