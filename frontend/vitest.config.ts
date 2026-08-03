import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

/**
 * Testes de unidade e de componente.
 *
 * O ambiente é `jsdom` porque os componentes tocam DOM (formulário, foco,
 * classes de tema). Testes E2E ficam no Playwright, com navegador real.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // O Playwright tem os próprios arquivos; o Vitest não deve tentar rodá-los
    exclude: ["node_modules/**", "e2e/**", ".next/**"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        // Server Components async: a cobertura significativa vem do Playwright,
        // que exercita a rota de verdade contra a API.
        "src/app/**",
        // Primitivos de estilo, sem lógica: o valor está no design QA visual.
        "src/components/ui/**",
        // MapLibre exige WebGL, indisponível no jsdom — coberto no E2E.
        "src/components/itinerary-map.tsx",
        // Wrapper de provider sem regra própria.
        "src/components/query-provider.tsx",
        // Gráfico SVG: o valor está no fluxo real, exercitado pelo Playwright.
        "src/components/cost-chart.tsx",
        "**/*.d.ts",
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
      },
    },
  },
});
