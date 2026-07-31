import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Concatena classes resolvendo conflitos do Tailwind.
 *
 * `twMerge` garante que a última classe vença quando duas competem pela mesma
 * propriedade — necessário para componentes que aceitam `className` de fora.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
