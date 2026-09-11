import { expect, test } from "@playwright/test";

/**
 * Fluxo público: chegar, entender e pedir um roteiro.
 *
 * Não depende de API disponível — valida a experiência até o envio, incluindo
 * validação, acessibilidade por teclado e tema. A geração completa fica no
 * arquivo `generation.spec.ts`, que precisa da API no ar.
 */

test.describe("Página inicial", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("apresenta a proposta e o formulário", async ({ page }) => {
    await expect(
      page.getByRole("heading", { level: 1 }),
    ).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Destino", exact: true })).toBeVisible();
    await expect(
      page.getByRole("button", { name: /planejar roteiro/i }),
    ).toBeVisible();
  });

  test("tem título e descrição para busca", async ({ page }) => {
    await expect(page).toHaveTitle(/Voyager/);
    const description = page.locator('meta[name="description"]');
    await expect(description).toHaveAttribute("content", /roteiros de viagem/i);
  });

  test("impede envio incompleto e explica o que falta", async ({ page }) => {
    await page.getByRole("button", { name: /planejar roteiro/i }).click();

    await expect(page.getByText("informe o destino")).toBeVisible();
    // Nada de navegar com formulário inválido
    await expect(page).toHaveURL("/");
  });

  test("preenche interesses pelos atalhos", async ({ page }) => {
    await page.getByRole("button", { name: "+ gastronomia" }).click();
    await page.getByRole("button", { name: "+ natureza" }).click();

    await expect(page.getByLabel("O que você quer aproveitar?")).toHaveValue(
      "gastronomia, natureza",
    );
  });

  test("é navegável por teclado até o envio", async ({ page }) => {
    // Primeiro Tab deve revelar o atalho de pular para o conteúdo
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: /pular para o conteúdo/i })).toBeFocused();

    await page.getByRole("textbox", { name: "Saindo de", exact: true }).focus();
    await page.keyboard.type("São Paulo");
    await page.keyboard.press("Tab");
    await page.keyboard.type("Roma");

    await expect(page.getByRole("textbox", { name: "Destino", exact: true })).toHaveValue("Roma");
  });

  test("não registra erro no console", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });

    await page.reload();
    await page.waitForLoadState("networkidle");

    expect(errors).toEqual([]);
  });
});

test.describe("Painel de custos", () => {
  test("abre pelo menu e explica a origem dos números", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Custos" }).click();

    await expect(page).toHaveURL(/\/finops$/);
    await expect(
      page.getByRole("heading", { level: 1, name: /quanto custa operar/i }),
    ).toBeVisible();
    await expect(page.getByText(/tokens.*medidos/i)).toBeVisible();
  });
});
