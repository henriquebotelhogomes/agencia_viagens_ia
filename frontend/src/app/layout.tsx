import type { Metadata, Viewport } from "next";
import { Instrument_Serif, Inter } from "next/font/google";

import { ThemeProvider } from "@/components/theme-provider";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

/**
 * Inter para interface, Instrument Serif para títulos.
 *
 * O par sans + serif dá o tom editorial pedido em specs/09 §3 e evita a
 * aparência de dashboard genérico. `display: "swap"` troca a fonte assim que
 * carrega, sem bloquear a primeira pintura.
 */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-display",
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
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fdfcfa" },
    { media: "(prefers-color-scheme: dark)", color: "#1a1715" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        {/*
         * Aplica o tema antes da primeira pintura. Sem isso, quem usa tema
         * escuro vê um flash branco a cada carregamento — o React só hidrata
         * depois do HTML já estar na tela.
         */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('voyager-theme')||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');if(t==='dark')document.documentElement.classList.add('dark')}catch(e){}`,
          }}
        />
      </head>
      <body className={`${inter.variable} ${display.variable} antialiased`}>
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
