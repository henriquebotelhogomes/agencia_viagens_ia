import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

/**
 * Fluxo completo: briefing → geração ao vivo → roteiro → export Markdown.
 *
 * Precisa da **API no ar** (stack local via `docker compose up` ou produção,
 * apontando `E2E_BASE_URL`). Por isso é opt-in via `E2E_API=1` — no CI a suíte
 * é pulada, pois o pipeline não tem API nem chaves de LLM:
 *
 * ```bash
 * E2E_API=1 npx playwright test e2e/generation.spec.ts
 * ```
 *
 * O timeout de 5min do config existe para este teste: uma geração real leva
 * ~2-3min até o roteiro aparecer.
 */
const COM_API = Boolean(process.env.E2E_API);

test.describe("Geração completa", () => {
  test.skip(!COM_API, "requer API no ar — rode com E2E_API=1");

  test("briefing → roteiro → export Markdown (FR-06)", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Saindo de").fill("Rio de Janeiro");
    await page.getByLabel("Destino").fill("Buenos Aires");
    await page.getByLabel("Dias").fill("3");
    await page
      .getByLabel("O que você quer aproveitar?")
      .fill("gastronomia e cultura");
    await page.getByRole("button", { name: /planejar roteiro/i }).click();

    // POST /v1/executions → 202 e a UI navega para a página da execução
    await page.waitForURL(/\/executions\//);

    // O botão só existe com o roteiro pronto — é o nosso "geração terminou".
    // Cold start do worker após restart do dyno leva ~3min (init do CrewAI +
    // litellm) antes dos ~70-90s da geração em si; 270s cobre esse pior caso.
    const botaoExport = page.getByRole("button", { name: /baixar roteiro/i });
    await expect(botaoExport).toBeVisible({ timeout: 270_000 });

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      botaoExport.click(),
    ]);

    expect(download.suggestedFilename()).toBe(
      "roteiro-buenos-aires-3-dias.md",
    );

    const caminho = await download.path();
    expect(caminho).toBeTruthy();
    const conteudo = readFileSync(caminho!, "utf-8");

    // Proveniência no cabeçalho e o roteiro da API na íntegra
    expect(conteudo).toContain("**Voyager — roteiros de viagem com IA**");
    expect(conteudo).toContain("Buenos Aires · 3 dias");
    expect(conteudo).toContain("saindo de Rio de Janeiro");
    expect(conteudo.split("---\n\n").length).toBeGreaterThan(1);
  });
});
