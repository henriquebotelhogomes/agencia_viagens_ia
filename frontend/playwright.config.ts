import { defineConfig, devices } from "@playwright/test";

/**
 * Testes de ponta a ponta.
 *
 * Rodam contra a aplicação servida de verdade e uma API real (local ou em
 * produção). Cobrem o que o jsdom não alcança: navegação entre rotas, mapa em
 * WebGL, streaming SSE e comportamento de teclado no navegador.
 */
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  // Uma geração de roteiro leva ~2min; o padrão de 30s reprovaria por engano
  timeout: 5 * 60 * 1000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  // Sobe o servidor só quando ninguém apontou para um ambiente externo
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run dev",
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
