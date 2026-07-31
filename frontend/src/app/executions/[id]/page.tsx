import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ExecutionView } from "@/components/execution-view";
import { QueryProvider } from "@/components/query-provider";
import { ApiError, api } from "@/lib/api/client";

interface PageProps {
  params: Promise<{ id: string }>;
}

export const metadata: Metadata = {
  title: "Gerando seu roteiro",
  // Execuções são efêmeras e específicas de um usuário: não indexar
  robots: { index: false, follow: false },
};

/**
 * Página da execução.
 *
 * Busca o estado inicial no servidor para que a primeira pintura já mostre o
 * briefing e o progresso — o cliente assume dali em diante, via SSE.
 */
export default async function ExecutionPage({ params }: PageProps) {
  const { id } = await params;

  let execution;
  try {
    execution = await api.getExecution(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  return (
    <QueryProvider>
      <ExecutionView executionId={id} initial={execution} />
    </QueryProvider>
  );
}
