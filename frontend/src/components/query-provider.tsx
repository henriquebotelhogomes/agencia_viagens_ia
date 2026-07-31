"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/**
 * Provider do TanStack Query.
 *
 * O cliente nasce dentro de `useState` para que cada usuário tenha o seu — um
 * cliente criado no escopo do módulo seria compartilhado entre requisições no
 * servidor, misturando dados de pessoas diferentes.
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Erro de contrato ou 404 não melhora com nova tentativa
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
