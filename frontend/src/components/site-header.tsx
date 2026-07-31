"use client";

import { Compass, Moon, Sun } from "lucide-react";
import Link from "next/link";

import { useTheme } from "@/components/theme-provider";
import { Button, buttonVariants } from "@/components/ui/button";

export function SiteHeader() {
  const { toggle } = useTheme();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-md font-medium tracking-tight"
        >
          <Compass className="size-5 text-primary" aria-hidden />
          <span className="font-display text-xl">Voyager</span>
        </Link>

        <nav className="flex items-center gap-1" aria-label="Principal">
          {/* Link estilizado como botão: `button > a` seria HTML inválido */}
          <Link
            href="/finops"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            Custos
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggle}
            aria-label="Alternar entre tema claro e escuro"
          >
            {/*
             * Os dois ícones ficam no DOM e o CSS mostra o correto. Assim o
             * botão não depende de saber o tema em JavaScript — evita render
             * extra e descompasso de hidratação.
             */}
            <Sun className="hidden size-5 dark:block" aria-hidden />
            <Moon className="size-5 dark:hidden" aria-hidden />
          </Button>
        </nav>
      </div>
    </header>
  );
}
