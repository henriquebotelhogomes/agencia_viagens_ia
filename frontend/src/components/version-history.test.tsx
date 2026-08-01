import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VersionHistory } from "@/components/version-history";

const getVersions = vi.fn();

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    api: { ...actual.api, getVersions: (...args: unknown[]) => getVersions(...args) },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

const VERSIONS_RESPONSE = {
  root_execution_id: "root-1",
  current_version: 2,
  versions: [
    {
      id: "exec-1",
      version: 1,
      kind: "initial" as const,
      refine_instruction: null,
      status: "succeeded" as const,
      created_at: "2026-08-01T10:00:00Z",
      duration_seconds: 80,
    },
    {
      id: "exec-2",
      version: 2,
      kind: "refine" as const,
      refine_instruction: "mais museus",
      status: "succeeded" as const,
      created_at: "2026-08-01T11:00:00Z",
      duration_seconds: 90,
    },
  ],
};

describe("VersionHistory", () => {
  beforeEach(() => {
    getVersions.mockReset();
  });

  it("não renderiza quando há apenas uma versão", async () => {
    getVersions.mockResolvedValue({
      ...VERSIONS_RESPONSE,
      versions: [VERSIONS_RESPONSE.versions[0]],
    });

    const { container } = render(
      <VersionHistory
        executionId="exec-1"
        currentVersion={1}
        onRollback={vi.fn()}
      />,
      { wrapper },
    );

    // Aguarda a query resolver
    await vi.waitFor(() => {
      expect(getVersions).toHaveBeenCalled();
    });
    expect(container.innerHTML).toBe("");
  });

  it("lista as versões com badges de kind", async () => {
    getVersions.mockResolvedValue(VERSIONS_RESPONSE);

    render(
      <VersionHistory
        executionId="exec-2"
        currentVersion={2}
        onRollback={vi.fn()}
      />,
      { wrapper },
    );

    await screen.findByText("v1");
    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(screen.getByText("Inicial")).toBeInTheDocument();
    expect(screen.getByText("Refino")).toBeInTheDocument();
  });

  it("marca a versão atual", async () => {
    getVersions.mockResolvedValue(VERSIONS_RESPONSE);

    render(
      <VersionHistory
        executionId="exec-2"
        currentVersion={2}
        onRollback={vi.fn()}
      />,
      { wrapper },
    );

    await screen.findByText("(atual)");
  });

  it("mostra link 'Ver' para versões que não são a atual", async () => {
    getVersions.mockResolvedValue(VERSIONS_RESPONSE);

    render(
      <VersionHistory
        executionId="exec-2"
        currentVersion={2}
        onRollback={vi.fn()}
      />,
      { wrapper },
    );

    const link = await screen.findByText("Ver");
    expect(link).toHaveAttribute("href", "/executions/exec-1");
  });

  it("chama onRollback ao clicar em restaurar", async () => {
    getVersions.mockResolvedValue(VERSIONS_RESPONSE);
    const onRollback = vi.fn();

    render(
      <VersionHistory
        executionId="exec-2"
        currentVersion={2}
        onRollback={onRollback}
      />,
      { wrapper },
    );

    const button = await screen.findByTitle("Restaurar esta versão");
    fireEvent.click(button);

    expect(onRollback).toHaveBeenCalledWith("exec-1");
  });
});
