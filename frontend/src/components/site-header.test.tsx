import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { SiteHeader } from "@/components/site-header";

afterEach(() => {
  document.documentElement.classList.remove("dark");
  localStorage.clear();
});

describe("SiteHeader", () => {
  it("leva para a página inicial pela marca", () => {
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: /voyager/i })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("oferece acesso ao painel de custos", () => {
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Custos" })).toHaveAttribute(
      "href",
      "/finops",
    );
  });

  it("alterna o tema no documento e guarda a preferência", async () => {
    const user = userEvent.setup();
    render(<SiteHeader />);

    await user.click(screen.getByRole("button", { name: /alternar entre tema/i }));

    expect(document.documentElement).toHaveClass("dark");
    // Persistir evita que a escolha se perca na próxima visita
    expect(localStorage.getItem("voyager-theme")).toBe("dark");

    await user.click(screen.getByRole("button", { name: /alternar entre tema/i }));

    expect(document.documentElement).not.toHaveClass("dark");
    expect(localStorage.getItem("voyager-theme")).toBe("light");
  });

  it("descreve o botão de tema para leitores de tela", () => {
    render(<SiteHeader />);

    // Ícone sozinho não comunica nada a quem usa leitor de tela
    expect(
      screen.getByRole("button", { name: /alternar entre tema claro e escuro/i }),
    ).toBeInTheDocument();
  });
});
