import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "@/components/site-header";

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
});
