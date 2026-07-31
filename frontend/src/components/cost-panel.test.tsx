import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CostPanel } from "@/components/cost-panel";
import type { CostSummary } from "@/lib/api/types";

const cost: CostSummary = {
  prompt_tokens: 15058,
  completion_tokens: 6109,
  total_tokens: 21167,
  cost_usd: 0.0134,
  baseline_cost_usd: 0.1668,
  savings_usd: 0.1534,
  served_from_cache: false,
};

describe("CostPanel", () => {
  it("mostra os tokens com separador de milhar", () => {
    render(<CostPanel cost={cost} />);

    // 21167 sem formatação é ilegível num painel
    expect(screen.getByText("21.167")).toBeInTheDocument();
  });

  it("detalha a divisão entre entrada e saída", () => {
    render(<CostPanel cost={cost} />);

    expect(screen.getByText(/15\.058 entrada/)).toBeInTheDocument();
    expect(screen.getByText(/6\.109 saída/)).toBeInTheDocument();
  });

  it("usa duas casas para custos acima de um centavo", () => {
    render(<CostPanel cost={cost} />);

    expect(screen.getByText("US$ 0.01")).toBeInTheDocument();
  });

  it("usa quatro casas quando o custo fica abaixo de um centavo", () => {
    // Com duas casas, uma geração de US$ 0,0089 apareceria como "US$ 0.01" e
    // perderia a ordem de grandeza real.
    render(<CostPanel cost={{ ...cost, cost_usd: 0.0089 }} />);

    expect(screen.getByText("US$ 0.0089")).toBeInTheDocument();
  });

  it("calcula o percentual de economia", () => {
    render(<CostPanel cost={cost} />);

    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("não mostra o selo de cache quando a geração foi real", () => {
    render(<CostPanel cost={cost} />);

    expect(screen.queryByText(/servido do cache/)).not.toBeInTheDocument();
  });

  it("sinaliza quando o roteiro veio do cache", () => {
    render(<CostPanel cost={{ ...cost, served_from_cache: true }} />);

    expect(screen.getByText(/servido do cache/)).toBeInTheDocument();
  });

  it("mostra zero sem casas decimais quando não houve custo", () => {
    render(
      <CostPanel
        cost={{
          ...cost,
          cost_usd: 0,
          baseline_cost_usd: 0,
          savings_usd: 0,
          served_from_cache: true,
        }}
      />,
    );

    expect(screen.getAllByText("US$ 0").length).toBeGreaterThan(0);
    // Sem referência, não há percentual a apresentar
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
