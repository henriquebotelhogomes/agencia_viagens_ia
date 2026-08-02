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
  private readonly listeners = new Map<string, Set<(event: { data: string }) => void>>();

  constructor(readonly url: string) {
    MockEventSource.instances.push(this);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  addEventListener(event: string, listener: (event: { data: string }) => void) {
    const listeners = this.listeners.get(event) ?? new Set();
    listeners.add(listener);
    this.listeners.set(event, listeners);
  }

  removeEventListener(event: string, listener: (event: { data: string }) => void) {
    this.listeners.get(event)?.delete(listener);
  }

  /** Simula um evento SSE, inclusive os de tipo nomeado. */
  emit(event: string, payload: unknown) {
    const message = { data: JSON.stringify(payload) };
    if (event === "message") this.onmessage?.(message);
    this.listeners.get(event)?.forEach((listener) => listener(message));
  }
}

vi.stubGlobal("EventSource", MockEventSource);

export { MockEventSource };
