import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useExecutionStream } from "@/lib/hooks/use-execution-stream";
import { MockEventSource } from "../../../vitest.setup";

const EXECUTION_ID = "3f9a1c2e-0000-4000-8000-000000000000";

function progress(status: string, step: string, message = "andando") {
  return {
    execution_id: EXECUTION_ID,
    status,
    step,
    message,
    at: new Date().toISOString(),
  };
}

describe("useExecutionStream", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
  });

  it("abre o stream da execução informada", () => {
    renderHook(() => useExecutionStream(EXECUTION_ID));

    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toContain(EXECUTION_ID);
    expect(MockEventSource.instances[0].url).toContain("/stream");
  });

  it("não abre stream para execução já finalizada", () => {
    // Recarregar a página de um roteiro pronto não deve reconectar
    renderHook(() => useExecutionStream(EXECUTION_ID, "succeeded"));

    expect(MockEventSource.instances).toHaveLength(0);
  });

  it("acumula eventos e expõe o último", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.emit("progress", progress("running", "cache", "consultando cache"));
    source.emit(
      "progress",
      progress("running", "orquestracao", "agentes trabalhando"),
    );

    await waitFor(() => {
      expect(result.current.events).toHaveLength(2);
    });
    expect(result.current.latest?.message).toBe("agentes trabalhando");
    expect(result.current.status).toBe("running");
  });

  it("fecha a conexão ao receber estado terminal", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.emit("progress", progress("succeeded", "concluido", "pronto"));

    await waitFor(() => {
      expect(result.current.status).toBe("succeeded");
    });
    // Sem fechar, o navegador reabriria um stream que a API já encerrou
    expect(source.readyState).toBe(MockEventSource.CLOSED);
    expect(result.current.connected).toBe(false);
  });

  it("descarta evento fora do contrato sem quebrar", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.emit("progress", { status: "isso-nao-existe" });
    source.emit("progress", progress("running", "cache"));

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1);
    });
  });

  it("marca conexão ativa ao abrir", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));

    MockEventSource.instances[0].onopen?.();

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });
  });

  it("avisa quando o navegador desiste de reconectar", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.readyState = MockEventSource.CLOSED;
    source.onerror?.();

    await waitFor(() => {
      expect(result.current.streamError).toContain("recarregue");
    });
  });

  it("não avisa em erro transitório, porque o EventSource reconecta só", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.readyState = 0; // CONNECTING
    source.onerror?.();

    await waitFor(() => {
      expect(result.current.connected).toBe(false);
    });
    expect(result.current.streamError).toBeUndefined();
  });

  it("fecha o stream ao desmontar", () => {
    const { unmount } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    unmount();

    expect(source.readyState).toBe(MockEventSource.CLOSED);
  });

  it("descarta JSON malformado sem interromper o stream", async () => {
    const { result } = renderHook(() => useExecutionStream(EXECUTION_ID));
    const source = MockEventSource.instances[0];

    source.emit("progress", "{not valid JSON");
    source.emit("progress", progress("running", "cache"));

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1);
    });
  });

  it("limpa o estado anterior ao acompanhar outra execuÃ§Ã£o", async () => {
    const secondId = "4f9a1c2e-0000-4000-8000-000000000000";
    const { result, rerender } = renderHook(
      ({ id }) => useExecutionStream(id),
      { initialProps: { id: EXECUTION_ID } },
    );
    MockEventSource.instances[0].emit(
      "progress",
      progress("running", "orquestracao"),
    );
    await waitFor(() => expect(result.current.events).toHaveLength(1));

    rerender({ id: secondId });

    await waitFor(() => {
      expect(result.current.events).toEqual([]);
      expect(result.current.status).toBe("queued");
    });
  });
});
