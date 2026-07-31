import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentTimeline, StatusBadge } from "@/components/agent-timeline";
import type { ExecutionStatus, ProgressEvent } from "@/lib/api/types";

function event(step: string, message = "trabalhando"): ProgressEvent {
  return {
    execution_id: "id",
    status: "running",
    step,
    message,
    at: new Date().toISOString(),
  };
}

describe("AgentTimeline", () => {
  it("lista todas as etapas do processo", () => {
    render(<AgentTimeline events={[]} status="queued" />);

    const lista = screen.getByRole("list", { name: "Etapas da geração" });
    expect(lista.querySelectorAll("li")).toHaveLength(4);
  });

  it("mostra a mensagem do servidor na etapa em andamento", () => {
    render(
      <AgentTimeline
        events={[event("orquestracao", "Guia local pesquisando…")]}
        status="running"
      />,
    );

    expect(screen.getByText("Guia local pesquisando…")).toBeInTheDocument();
  });

  it("usa o texto padrão da etapa quando ela ainda não começou", () => {
    render(<AgentTimeline events={[]} status="queued" />);

    expect(
      screen.getByText("Se alguém já pediu algo parecido, reaproveitamos."),
    ).toBeInTheDocument();
  });

  it("deriva o progresso do último evento, não da contagem", () => {
    // Uma reconexão do SSE perde os eventos anteriores; o estado das etapas
    // precisa vir do passo atual, senão a timeline "volta no tempo".
    render(<AgentTimeline events={[event("geocoding")]} status="running" />);

    const itens = screen.getAllByRole("listitem");
    // Cache e orquestração ficam concluídos mesmo sem seus eventos na lista
    expect(itens[0].textContent).toContain("Consultando roteiros anteriores");
    expect(itens[2].textContent).toContain("Localizando os pontos no mapa");
  });

  it("marca a etapa corrente como falha quando a execução falha", () => {
    const { container } = render(
      <AgentTimeline events={[event("orquestracao")]} status="failed" />,
    );

    // A etapa que falhou recebe a cor de destaque de erro
    expect(container.querySelector(".text-destructive")).not.toBeNull();
  });
});

describe("StatusBadge", () => {
  it.each([
    ["queued", "Na fila"],
    ["running", "Gerando"],
    ["succeeded", "Concluído"],
    ["failed", "Falhou"],
    ["cancelled", "Cancelado"],
  ])("traduz %s para o público", (status, label) => {
    render(<StatusBadge status={status as ExecutionStatus} />);

    expect(screen.getByText(label)).toBeInTheDocument();
  });
});
