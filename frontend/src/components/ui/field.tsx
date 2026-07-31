import type {
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import { useId } from "react";

import { cn } from "@/lib/utils";

/**
 * Campos de formulário com acessibilidade embutida.
 *
 * O componente `Field` gera o `id` e amarra label, descrição e erro via
 * `aria-describedby`/`aria-invalid` — o leitor de tela anuncia o problema junto
 * do campo, em vez de deixar a mensagem solta na tela (WCAG 3.3.1/3.3.2).
 */

const controlClasses = cn(
  "w-full rounded-md border border-input bg-surface px-3 py-2.5 text-sm",
  "placeholder:text-muted-foreground",
  "transition-colors duration-[--duration-fast]",
  "hover:border-muted-foreground/40",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "aria-[invalid=true]:border-destructive",
);

export function Label({
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-sm font-medium text-foreground", className)}
      {...props}
    />
  );
}

interface FieldProps {
  label: string;
  /** Texto de apoio, exibido abaixo do rótulo. */
  hint?: string;
  error?: string;
  /** Recebe os atributos de acessibilidade já resolvidos. */
  children: (props: {
    id: string;
    "aria-describedby": string | undefined;
    "aria-invalid": boolean;
  }) => ReactNode;
}

export function Field({ label, hint, error, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {hint ? (
        <p id={hintId} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {children({
        id,
        "aria-describedby": describedBy,
        "aria-invalid": Boolean(error),
      })}
      {error ? (
        // `role="alert"` faz o leitor de tela anunciar assim que o erro aparece
        <p id={errorId} role="alert" className="text-xs text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function Input({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(controlClasses, className)} {...props} />;
}

export function Textarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(controlClasses, "min-h-24 resize-y", className)}
      {...props}
    />
  );
}

/**
 * `select` nativo, deliberadamente.
 *
 * Um dropdown custom exigiria replicar navegação por teclado, leitura de tela e
 * o comportamento de roda nativo do mobile. O nativo já entrega tudo isso.
 */
export function Select({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(controlClasses, "appearance-none pr-9", className)}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E\")",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 0.6rem center",
        backgroundSize: "1.1rem",
      }}
      {...props}
    />
  );
}
