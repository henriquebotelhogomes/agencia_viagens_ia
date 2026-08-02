import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BriefingForm } from "@/components/briefing-form";
import { ApiError } from "@/lib/api/client";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const createExecution = vi.fn();

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    api: { ...actual.api, createExecution: (...args: unknown[]) => createExecution(...args) },
  };
});

/** Web Crypto não existe no jsdom; simulamos uma chave aleatória por envio. */
function stubCrypto() {
  vi.stubGlobal("crypto", {
    randomUUID: vi.fn(() => "request-uuid-123"),
  });
}

async function preencher(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Saindo de"), "São Paulo, Brasil");
  await user.type(screen.getByLabelText("Destino"), "Lisboa, Portugal");
  await user.type(
    screen.getByLabelText("O que você quer aproveitar?"),
    "gastronomia",
  );
}

describe("BriefingForm", () => {
  beforeEach(() => {
    push.mockReset();
    createExecution.mockReset();
    stubCrypto();
  });

  it("envia o briefing e navega para a execução criada", async () => {
    const user = userEvent.setup();
    createExecution.mockResolvedValue({
      id: "abc-123",
      status: "queued",
      stream_url: "/stream",
    });
    render(<BriefingForm />);

    await preencher(user);
    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/executions/abc-123");
    });
    const [briefing] = createExecution.mock.calls[0];
    expect(briefing).toMatchObject({
      origem: "São Paulo, Brasil",
      destino: "Lisboa, Portugal",
      dias: 3,
      moeda: "BRL",
    });
  });

  it("envia uma chave de idempotência aleatória por envio", async () => {
    const user = userEvent.setup();
    createExecution.mockResolvedValue({ id: "x", status: "queued", stream_url: "" });
    render(<BriefingForm />);

    await preencher(user);
    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    await waitFor(() => {
      expect(createExecution.mock.calls[0][1]).toBe("request-uuid-123");
    });
  });

  it("reutiliza a chave ao repetir o mesmo briefing após uma falha", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("crypto", {
      randomUUID: vi
        .fn()
        .mockReturnValueOnce("first-request-uuid")
        .mockReturnValueOnce("second-request-uuid"),
    });
    createExecution
      .mockRejectedValueOnce(new ApiError("Serviço indisponível", 503))
      .mockResolvedValueOnce({ id: "retry-ok", status: "queued", stream_url: "" });
    render(<BriefingForm />);

    await preencher(user);
    const submit = screen.getByRole("button", { name: /planejar roteiro/i });
    await user.click(submit);
    await screen.findByRole("alert");
    await user.click(submit);

    await waitFor(() => expect(push).toHaveBeenCalledWith("/executions/retry-ok"));
    expect(createExecution.mock.calls.map((call) => call[1])).toEqual([
      "first-request-uuid",
      "first-request-uuid",
    ]);
  });

  it("bloqueia o envio e mostra erro quando falta o destino", async () => {
    const user = userEvent.setup();
    render(<BriefingForm />);

    await user.type(screen.getByLabelText("Saindo de"), "São Paulo");
    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    expect(await screen.findByText("informe o destino")).toBeInTheDocument();
    expect(createExecution).not.toHaveBeenCalled();
  });

  it("associa a mensagem de erro ao campo, para o leitor de tela", async () => {
    const user = userEvent.setup();
    render(<BriefingForm />);

    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    const destino = screen.getByLabelText("Destino");
    await waitFor(() => {
      expect(destino).toHaveAttribute("aria-invalid", "true");
    });
    const errorId = destino.getAttribute("aria-describedby");
    expect(errorId).toBeTruthy();
    expect(document.getElementById(errorId!.split(" ").pop()!)).toHaveTextContent(
      "informe o destino",
    );
  });

  it("acrescenta o interesse escolhido no chip", async () => {
    const user = userEvent.setup();
    render(<BriefingForm />);

    await user.click(screen.getByRole("button", { name: "+ gastronomia" }));
    await user.click(screen.getByRole("button", { name: "+ natureza" }));

    expect(screen.getByLabelText("O que você quer aproveitar?")).toHaveValue(
      "gastronomia, natureza",
    );
  });

  it("não duplica um interesse já presente", async () => {
    const user = userEvent.setup();
    render(<BriefingForm />);

    await user.click(screen.getByRole("button", { name: "+ história" }));
    await user.click(screen.getByRole("button", { name: "+ história" }));

    expect(screen.getByLabelText("O que você quer aproveitar?")).toHaveValue(
      "história",
    );
  });

  it("mostra a mensagem da API quando a cota é excedida", async () => {
    const user = userEvent.setup();
    createExecution.mockRejectedValue(
      new ApiError("Limite de 5 execuções por hora atingido.", 429, {
        type: "rate-limit",
        title: "Limite",
        status: 429,
        detail: "Limite de 5 execuções por hora atingido.",
        retry_after: 1800,
      }),
    );
    render(<BriefingForm />);

    await preencher(user);
    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Limite de 5 execuções por hora");
    // Informar quanto falta é mais útil que só dizer "tente mais tarde"
    expect(alerta).toHaveTextContent("aguarde 30 min");
    expect(push).not.toHaveBeenCalled();
  });

  it("mostra mensagem amigável em erro inesperado, sem stack trace", async () => {
    const user = userEvent.setup();
    createExecution.mockRejectedValue(new TypeError("boom interno"));
    render(<BriefingForm />);

    await preencher(user);
    await user.click(screen.getByRole("button", { name: /planejar roteiro/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Algo deu errado");
    expect(alerta).not.toHaveTextContent("boom interno");
  });
});
