import { type VariantProps, cva } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * Botão do design system.
 *
 * Altura mínima de 44px nas variantes `md`/`lg`: alvo de toque confortável em
 * telas pequenas (WCAG 2.5.5 e specs/09 §1 — mobile-first).
 */
const buttonVariants = cva(
  cn(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium",
    "transition-colors duration-[--duration-fast]",
    "disabled:pointer-events-none disabled:opacity-50",
    "[&_svg]:size-4 [&_svg]:shrink-0",
  ),
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground shadow-sm hover:bg-primary-hover",
        secondary:
          "bg-surface text-foreground border border-border shadow-sm hover:bg-surface-muted",
        ghost: "text-foreground hover:bg-surface-muted",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:opacity-90",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-9 px-3 text-sm",
        md: "h-11 px-5 text-sm",
        lg: "h-12 px-7 text-base",
        icon: "size-11",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { buttonVariants };
