"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api/client";
import {
  type ExecutionStatus,
  type ProgressEvent,
  isTerminal,
  progressEventSchema,
} from "@/lib/api/types";

/** Etapas conhecidas do job, na ordem em que o worker as executa. */
export const STEPS = ["cache", "orquestracao", "geocoding", "concluido"] as const;
export type Step = (typeof STEPS)[number];

interface UseExecutionStreamResult {
  events: ProgressEvent[];
  status: ExecutionStatus;
  /** Última mensagem recebida — o que a UI mostra como "acontecendo agora". */
  latest: ProgressEvent | undefined;
  /** `true` enquanto a conexão SSE está aberta. */
  connected: boolean;
  /** Preenchido quando a conexão cai e não há mais o que tentar. */
  streamError: string | undefined;
}

/**
 * Acompanha o progresso de uma execução via Server-Sent Events (FR-03).
 *
 * O `EventSource` reconecta sozinho em queda de rede, então não há retry
 * manual aqui. O que fazemos é fechar a conexão em estado terminal — sem isso,
 * o navegador ficaria reabrindo um stream que a API encerrou.
 *
 * @param executionId Execução a acompanhar.
 * @param initialStatus Estado já conhecido (evita piscar "queued" ao recarregar).
 */
export function useExecutionStream(
  executionId: string,
  initialStatus: ExecutionStatus = "queued",
): UseExecutionStreamResult {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [status, setStatus] = useState<ExecutionStatus>(initialStatus);
  const [connected, setConnected] = useState(false);
  const [streamError, setStreamError] = useState<string>();
  const [streamExecutionId, setStreamExecutionId] = useState(executionId);

  // A navegação entre execuções reutiliza este componente cliente; não deixe
  // os eventos/status da execução anterior aparecerem no roteiro novo. O reset
  // durante a renderização evita uma pintura intermediária com dados obsoletos.
  if (streamExecutionId !== executionId) {
    setStreamExecutionId(executionId);
    setEvents([]);
    setStatus(initialStatus);
    setConnected(false);
    setStreamError(undefined);
  }

  useEffect(() => {
    // Execução já finalizada: nada a transmitir
    if (isTerminal(initialStatus)) {
      return;
    }

    const source = new EventSource(api.streamUrl(executionId));

    source.onopen = () => {
      setConnected(true);
      setStreamError(undefined);
    };

    // O backend emite `event: progress`; `onmessage` só recebe o evento SSE
    // padrão `message`, portanto não acompanha este fluxo nomeado.
    const handleProgress = (message: MessageEvent<string>) => {
      let data: unknown;
      try {
        data = JSON.parse(message.data);
      } catch {
        return;
      }
      const parsed = progressEventSchema.safeParse(data);
      if (!parsed.success) {
        // Evento fora do contrato: ignora em vez de derrubar a tela
        return;
      }

      const event = parsed.data;
      setEvents((current) => [...current, event]);
      setStatus(event.status);

      if (isTerminal(event.status)) {
        source.close();
        setConnected(false);
      }
    };
    source.addEventListener("progress", handleProgress);

    source.onerror = () => {
      setConnected(false);
      // `CLOSED` significa que o navegador desistiu de reconectar
      if (source.readyState === EventSource.CLOSED) {
        setStreamError(
          "A conexão de progresso caiu. O roteiro continua sendo gerado — recarregue para ver o resultado.",
        );
      }
    };

    return () => {
      source.removeEventListener("progress", handleProgress);
      source.close();
    };
  }, [executionId, initialStatus]);

  return {
    events,
    status,
    latest: events.at(-1),
    connected,
    streamError,
  };
}
