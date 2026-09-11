import { Compass } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/90 backdrop-blur-md shadow-xs">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-md font-semibold tracking-tight text-foreground transition-opacity hover:opacity-90"
        >
          <Compass className="size-5.5 text-primary" aria-hidden />
          <span className="text-xl font-bold tracking-tight text-foreground">Voyager</span>
        </Link>

        <nav className="flex items-center gap-2" aria-label="Principal">
          {/* Link estilizado como botão: `button > a` seria HTML inválido */}
          <Link
            href="/finops"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            Custos
          </Link>
        </nav>
      </div>
    </header>
  );
}
