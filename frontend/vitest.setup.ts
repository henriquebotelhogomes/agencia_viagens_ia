import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Desmonta a árvore entre testes: sem isso, um teste vê o DOM do anterior
afterEach(() => {
  cleanup();
});

/**
 * `EventSource` não existe no jsdom.
 *
 * O dublê registra os handlers e permite ao teste disparar eventos manualmente,
 * o que dá controle sobre a ordem e o conteúdo das mensagens SSE.
 */
class MockEventSource {
  static instances: MockEventSource[] = [];
  static readonly CLOSED = 2;

  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;

  constructor(readonly url: string) {
    MockEventSource.instances.push(this);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  /** Simula uma mensagem do servidor. */
  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

vi.stubGlobal("EventSource", MockEventSource);

export { MockEventSource };
