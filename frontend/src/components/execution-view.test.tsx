import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExecutionView } from "@/components/execution-view";
import type { ExecutionDetail } from "@/lib/api/types";

const mocks = vi.hoisted(() => ({
  useQuery: vi.fn(),
  useExecutionStream: vi.fn(),
  rollback: vi.fn(),
  getExecution: vi.fn(),
  getGeoJson: vi.fn(),
  download: vi.fn(),
  push: vi.fn(),
}));
const { useQuery, useExecutionStream, rollback, push } = mocks;

vi.mock("@tanstack/react-query", () => ({ useQuery: mocks.useQuery }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: mocks.push }) }));
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));
vi.mock("@/lib/api/client", () => ({
  api: {
    rollback: mocks.rollback,
    getExecution: mocks.getExecution,
    getGeoJson: mocks.getGeoJson,
  },
}));
vi.mock("@/lib/hooks/use-execution-stream", () => ({
  useExecutionStream: mocks.useExecutionStream,
}));
vi.mock("@/components/agent-timeline", () => ({
  AgentTimeline: () => <div data-testid="timeline" />,
  StatusBadge: ({ status }: { status: string }) => <span>{status}</span>,
}));
vi.mock("@/components/cost-panel", () => ({ CostPanel: () => null }));
vi.mock("@/components/itinerary-map", () => ({
  ItineraryMap: ({ highlighted }: { highlighted?: string }) => (
    <div data-testid="map">{highlighted}</div>
  ),
}));
vi.mock("@/components/refine-panel", () => ({ RefinePanel: () => null }));
vi.mock("@/components/version-history", () => ({
  VersionHistory: ({ onRollback }: { onRollback: (id: string) => Promise<void> }) => (
    <button type="button" onClick={() => void onRollback("previous-version")}>
      Restaurar versão anterior
    </button>
  ),
}));
vi.mock("@/lib/export-markdown", () => ({
  downloadItineraryMarkdown: mocks.download,
}));

const INITIAL: ExecutionDetail = {
  id: "execution-1",
  status: "running",
  briefing: {
    origem: "São Paulo",
    destino: "Lisboa",
    dias: 3,
    interesses: "gastronomia",
    moeda: "EUR",
    idioma: "pt-BR",
  },
  created_at: "2026-08-02T12:00:00Z",
  finished_at: null,
  duration_seconds: null,
  itinerary_markdown: null,
  error: null,
  used_fallback: false,
  llm_gateway: null,
  cost: null,
  kind: "initial",
  version: null,
  parent_execution_id: null,
  root_execution_id: null,
  refine_instruction: null,
};

function stream(status: ExecutionDetail["status"], streamError?: string) {
  return {
    events: [],
    status,
    latest: undefined,
    connected: true,
    streamError,
  };
}

describe("ExecutionView", () => {
  beforeEach(() => {
    useQuery.mockReset();
    useExecutionStream.mockReset();
    rollback.mockReset();
    mocks.getExecution.mockReset();
    mocks.getGeoJson.mockReset();
    mocks.download.mockReset();
    push.mockReset();
    useQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => ({
      data: queryKey[0] === "geojson" ? { type: "FeatureCollection", features: [] } : INITIAL,
    }));
  });

  it("inclui a composição da execução na cobertura unitária", () => {
    const config = readFileSync("vitest.config.ts", "utf8");

    expect(config).not.toContain('"src/components/execution-view.tsx"');
  });

  it("só habilita o refetch do detalhe quando o stream termina", () => {
    useExecutionStream.mockReturnValue(stream("running"));

    render(<ExecutionView executionId={INITIAL.id} initial={INITIAL} />);

    expect(useQuery.mock.calls[0][0]).toMatchObject({
      queryKey: ["execution", INITIAL.id, "running"],
      enabled: false,
      staleTime: 0,
    });
  });

  it("mostra a falha persistida quando o stream termina em erro", () => {
    const failed = { ...INITIAL, status: "failed" as const, error: "Worker excedeu o timeout." };
    useExecutionStream.mockReturnValue(stream("failed", "Conexão interrompida"));
    useQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => ({
      data: queryKey[0] === "geojson" ? undefined : failed,
    }));

    render(<ExecutionView executionId={failed.id} initial={failed} />);

    expect(screen.getByText("Worker excedeu o timeout.")).toBeInTheDocument();
    expect(screen.getByText("Conexão interrompida")).toBeInTheDocument();
    expect(useQuery.mock.calls[0][0]).toMatchObject({ enabled: true, staleTime: Infinity });
  });

  it("consulta e mostra o mapa somente para uma execução bem-sucedida", () => {
    const succeeded = {
      ...INITIAL,
      status: "succeeded" as const,
      itinerary_markdown: "# Lisboa",
      version: 2,
    };
    useExecutionStream.mockReturnValue(stream("succeeded"));
    useQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => ({
      data:
        queryKey[0] === "geojson"
          ? { type: "FeatureCollection", features: [{ properties: { name: "Alfama" } }] }
          : succeeded,
    }));

    render(<ExecutionView executionId={succeeded.id} initial={succeeded} />);

    expect(useQuery.mock.calls[1][0]).toMatchObject({ enabled: true, staleTime: Infinity });
    expect(screen.getByTestId("map")).toBeInTheDocument();

    fireEvent.mouseEnter(screen.getByRole("button", { name: "Alfama" }));
    expect(screen.getByTestId("map")).toHaveTextContent("Alfama");
    fireEvent.mouseLeave(screen.getByRole("button", { name: "Alfama" }));
    expect(screen.getByTestId("map")).toBeEmptyDOMElement();
    fireEvent.focus(screen.getByRole("button", { name: "Alfama" }));
    expect(screen.getByTestId("map")).toHaveTextContent("Alfama");
    fireEvent.blur(screen.getByRole("button", { name: "Alfama" }));
    expect(screen.getByTestId("map")).toBeEmptyDOMElement();
  });

  it("executa as consultas terminais e exporta o roteiro carregado", async () => {
    const succeeded = {
      ...INITIAL,
      status: "succeeded" as const,
      itinerary_markdown: "# Lisboa",
    };
    useExecutionStream.mockReturnValue(stream("succeeded"));
    useQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => ({
      data: queryKey[0] === "geojson" ? undefined : succeeded,
    }));
    mocks.getExecution.mockResolvedValue(succeeded);
    mocks.getGeoJson.mockResolvedValue({ type: "FeatureCollection", features: [] });

    render(<ExecutionView executionId={succeeded.id} initial={succeeded} />);

    await useQuery.mock.calls[0][0].queryFn();
    await useQuery.mock.calls[1][0].queryFn();
    fireEvent.click(screen.getByRole("button", { name: /baixar roteiro/i }));

    expect(mocks.getExecution).toHaveBeenCalledWith(succeeded.id);
    expect(mocks.getGeoJson).toHaveBeenCalledWith(succeeded.id);
    expect(mocks.download).toHaveBeenCalledWith(succeeded);
  });

  it("cria o rollback e navega para a execução resultante", async () => {
    const succeeded = {
      ...INITIAL,
      status: "succeeded" as const,
      itinerary_markdown: "# Lisboa",
      version: 2,
    };
    useExecutionStream.mockReturnValue(stream("succeeded"));
    rollback.mockResolvedValue({ id: "rollback-3" });
    useQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => ({
      data: queryKey[0] === "geojson" ? undefined : succeeded,
    }));

    render(<ExecutionView executionId={succeeded.id} initial={succeeded} />);
    fireEvent.click(screen.getByRole("button", { name: "Restaurar versão anterior" }));

    await waitFor(() => {
      expect(rollback).toHaveBeenCalledWith("execution-1", "previous-version");
      expect(push).toHaveBeenCalledWith("/executions/rollback-3");
    });
  });
});
