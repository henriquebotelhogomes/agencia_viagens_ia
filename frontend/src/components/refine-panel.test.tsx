import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RefinePanel } from "@/components/refine-panel";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const refine = vi.fn();

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    api: { ...actual.api, refine: (...args: unknown[]) => refine(...args) },
  };
});

describe("RefinePanel", () => {
  beforeEach(() => {
    push.mockReset();
    refine.mockReset();
  });

  it("renderiza o formulário com textarea e botão", () => {
    render(<RefinePanel executionId="exec-123" />);

    expect(
      screen.getByLabelText("Instrução de refinamento"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /refinar/i })).toBeInTheDocument();
  });

  it("valida instrução vazia e não envia", async () => {
    render(<RefinePanel executionId="exec-123" />);

    fireEvent.submit(screen.getByLabelText("Instrução de refinamento").closest("form")!);

    await waitFor(() => {
      expect(
        screen.getByText("Descreva o que deseja mudar"),
      ).toBeInTheDocument();
    });
    expect(refine).not.toHaveBeenCalled();
  });

  it("valida instrução acima de 1000 caracteres", async () => {
    render(<RefinePanel executionId="exec-123" />);

    const textarea = screen.getByLabelText("Instrução de refinamento");
    fireEvent.change(textarea, { target: { value: "a".repeat(1001) } });
    fireEvent.submit(textarea.closest("form")!);

    await waitFor(() => {
      expect(
        screen.getByText("Máximo de 1000 caracteres"),
      ).toBeInTheDocument();
    });
    expect(refine).not.toHaveBeenCalled();
  });

  it("envia a instrução e navega para a nova execução", async () => {
    refine.mockResolvedValue({ id: "child-456", status: "queued", stream_url: "" });
    render(<RefinePanel executionId="exec-123" />);

    const textarea = screen.getByLabelText("Instrução de refinamento");
    fireEvent.change(textarea, { target: { value: "Inclua mais museus" } });
    fireEvent.submit(textarea.closest("form")!);

    await waitFor(
      () => {
        expect(refine).toHaveBeenCalledWith("exec-123", "Inclua mais museus");
      },
      { timeout: 3000 },
    );
    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/executions/child-456");
    });
  });

  it("mostra erro da API sem navegar", async () => {
    refine.mockRejectedValue(new Error("Limite excedido"));
    render(<RefinePanel executionId="exec-123" />);

    const textarea = screen.getByLabelText("Instrução de refinamento");
    fireEvent.change(textarea, { target: { value: "mude algo" } });
    fireEvent.submit(textarea.closest("form")!);

    await waitFor(
      () => {
        expect(screen.getByText("Limite excedido")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(push).not.toHaveBeenCalled();
  });
});
