import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { VersionDiff } from "@/components/version-diff";

describe("VersionDiff", () => {
  it("marca linhas adicionadas com cor verde", () => {
    const { container } = render(
      <VersionDiff oldMarkdown={"Dia 1: Museu"} newMarkdown={"Dia 1: Museu\nDia 2: Praia"} />,
    );

    const added = container.querySelector(".text-green-800");
    expect(added).not.toBeNull();
    expect(added!.textContent).toContain("Dia 2: Praia");
    expect(added!.textContent).toContain("+");
  });

  it("marca linhas removidas com cor vermelha", () => {
    const { container } = render(
      <VersionDiff oldMarkdown={"Dia 1: Museu\nDia 2: Praia"} newMarkdown={"Dia 1: Museu"} />,
    );

    const removed = container.querySelector(".text-red-800");
    expect(removed).not.toBeNull();
    expect(removed!.textContent).toContain("Dia 2: Praia");
    expect(removed!.textContent).toContain("-");
  });

  it("mantém linhas inalteradas sem cor de diff", () => {
    const { container } = render(
      <VersionDiff oldMarkdown={"Dia 1: Museu"} newMarkdown={"Dia 1: Museu"} />,
    );

    const spans = container.querySelectorAll("pre span");
    expect(spans.length).toBeGreaterThan(0);
    for (const span of spans) {
      expect(span.className).not.toContain("green");
      expect(span.className).not.toContain("red");
    }
  });

  it("renderiza região acessível com label descritivo", () => {
    render(<VersionDiff oldMarkdown="a" newMarkdown="b" />);

    expect(
      screen.getByRole("region", {
        name: "Diferenças entre versões do roteiro",
      }),
    ).toBeInTheDocument();
  });

  it("trata textos vazios sem erro", () => {
    render(<VersionDiff oldMarkdown="" newMarkdown="" />);

    expect(screen.getByRole("region")).toBeInTheDocument();
  });
});
