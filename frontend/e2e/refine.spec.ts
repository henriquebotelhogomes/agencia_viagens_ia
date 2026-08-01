import { expect, test } from "@playwright/test";

/**
 * Fluxo de refinamento: geração → refine → nova versão → diff visível.
 *
 * Assim como `generation.spec.ts`, precisa da API no ar e é opt-in via
 * `E2E_API=1`. Caro (~2 gerações reais), portanto não roda no CI padrão:
 *
 * ```bash
 * E2E_API=1 npx playwright test e2e/refine.spec.ts
 * ```
 */
const COM_API = Boolean(process.env.E2E_API);

test.describe("Refinamento de roteiro", () => {
  test.skip(!COM_API, "requer API no ar — rode com E2E_API=1");

  test("geração → refine → nova versão (FR-40/FR-41)", async ({ page }) => {
    // 1. Gera o roteiro inicial
    await page.goto("/");
    await page.getByLabel("Saindo de").fill("São Paulo");
    await page.getByLabel("Destino").fill("Lisboa");
    await page.getByLabel("Dias").fill("2");
    await page
      .getByLabel("O que você quer aproveitar?")
      .fill("cultura e gastronomia");
    await page.getByRole("button", { name: /planejar roteiro/i }).click();

    await page.waitForURL(/\/executions\//);

    // Aguarda a geração terminar (botão de export aparece)
    await expect(
      page.getByRole("button", { name: /baixar roteiro/i }),
    ).toBeVisible({ timeout: 270_000 });

    // 2. Painel de refine visível
    const painelRefine = page.getByText("Refinar roteiro");
    await expect(painelRefine).toBeVisible();

    // 3. Envia a instrução de refine
    await page
      .getByLabel("Instrução de refinamento")
      .fill("Inclua uma opção de passeio noturno");
    await page.getByRole("button", { name: /^refinar$/i }).click();

    // 4. Navega para a nova execução (refine)
    await page.waitForURL(/\/executions\//);

    // 5. Aguarda o refine terminar
    await expect(
      page.getByRole("button", { name: /baixar roteiro/i }),
    ).toBeVisible({ timeout: 270_000 });

    // 6. Histórico de versões visível (2 versões)
    await expect(page.getByText(/versões \(2\)/i)).toBeVisible();

    // 7. Badge "Refino" presente
    await expect(page.getByText("Refino")).toBeVisible();
  });
});
