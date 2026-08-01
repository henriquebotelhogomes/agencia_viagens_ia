"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api/client";

const refineSchema = z.object({
  instruction: z
    .string()
    .trim()
    .min(1, "Descreva o que deseja mudar")
    .max(1000, "Máximo de 1000 caracteres"),
});

type RefineForm = z.infer<typeof refineSchema>;

interface RefinePanelProps {
  executionId: string;
}

/**
 * Painel de refinamento (FR-40): textarea + botão "Refinar".
 *
 * Valida com Zod (1-1000 chars), chama `api.refine` e navega para a nova
 * execução (reusa o streaming existente).
 */
export function RefinePanel({ executionId }: RefinePanelProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RefineForm>({
    resolver: zodResolver(refineSchema),
  });

  const onSubmit = async (data: RefineForm) => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await api.refine(executionId, data.instruction);
      router.push(`/executions/${created.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao iniciar o refinamento.",
      );
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardContent className="pt-5">
        <h2 className="mb-3 text-sm font-medium tracking-wide text-muted-foreground uppercase">
          Refinar roteiro
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <textarea
            {...register("instruction")}
            placeholder="Ex.: Inclua mais opções vegetarianas, troque o hotel por um mais central…"
            rows={3}
            className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
            aria-label="Instrução de refinamento"
          />
          {errors.instruction ? (
            <p className="text-xs text-destructive">
              {errors.instruction.message}
            </p>
          ) : null}
          {error ? (
            <p className="text-xs text-destructive">{error}</p>
          ) : null}
          <Button type="submit" size="sm" disabled={submitting}>
            {submitting ? "Iniciando…" : "Refinar"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
