import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import { ThemeProvider } from "@/components/theme-provider";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

/**
 * Inter com pesos completos para máxima legibilidade e caracteres encorpados.
 */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Voyager — roteiros de viagem por agentes de IA",
    template: "%s · Voyager",
  },
  description:
    "Roteiros de viagem gerados por uma equipe de agentes de IA, com custos transparentes e mapa dos pontos sugeridos.",
  openGraph: {
    type: "website",
    title: "Voyager — roteiros de viagem por agentes de IA",
    description:
      "Três agentes pesquisam, calculam custos e montam seu roteiro. Você acompanha o raciocínio em tempo real.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#f8fafc",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider>
          {/* Atalho para quem navega por teclado pular direto ao conteúdo */}
          <a
            href="#conteudo"
            className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
          >
            Pular para o conteúdo
          </a>
          <SiteHeader />
          <main id="conteudo">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
