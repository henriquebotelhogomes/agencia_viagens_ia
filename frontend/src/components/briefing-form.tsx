"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2, Sparkles, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { ApiError, api } from "@/lib/api/client";
import {
  CURRENCIES,
  LANGUAGES,
  type TripBriefing,
  type TripBriefingInput,
  tripBriefingSchema,
} from "@/lib/api/types";
import type { Destination } from "@/lib/destinations";

const CURRENCY_LABELS: Record<(typeof CURRENCIES)[number], string> = {
  BRL: "Real (R$)",
  USD: "Dólar (US$)",
  EUR: "Euro (€)",
  GBP: "Libra (£)",
};

const LANGUAGE_LABELS: Record<(typeof LANGUAGES)[number], string> = {
  "pt-BR": "Português",
  "en-US": "English",
  "es-ES": "Español",
};

/** Sugestões que reduzem o atrito de começar do zero. */
const INTEREST_CHIPS = [
  "gastronomia",
  "história",
  "arte e museus",
  "vida noturna",
  "natureza",
  "arquitetura",
  "compras",
  "praias",
];

export interface BriefingFormProps {
  selectedDestination?: Destination | null;
  onClearDestination?: () => void;
}

export function BriefingForm({
  selectedDestination,
  onClearDestination,
}: BriefingFormProps = {}) {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string>();
  const idempotencyKeys = useRef(new Map<string, string>());

  const {
    register,
    handleSubmit,
    setValue,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<TripBriefingInput, unknown, TripBriefing>({
    resolver: zodResolver(tripBriefingSchema),
    defaultValues: {
      origem: "",
      destino: "",
      dias: 3,
      interesses: "",
      moeda: "BRL",
      idioma: "pt-BR",
    },
  });

  // Atualiza os campos quando um destino sugerido é selecionado
  useEffect(() => {
    if (selectedDestination) {
      setValue("destino", selectedDestination.name, { shouldValidate: true });
      setValue("dias", selectedDestination.suggestedDays, {
        shouldValidate: true,
      });
      setValue("moeda", selectedDestination.currency, { shouldValidate: true });
      setValue("interesses", selectedDestination.interests.join(", "), {
        shouldValidate: true,
      });
    }
  }, [selectedDestination, setValue]);

  /** Acrescenta o interesse ao campo, sem duplicar o que já está lá. */
  const addChip = (chip: string) => {
    const current = getValues("interesses").trim();
    if (current.toLowerCase().includes(chip.toLowerCase())) return;
    setValue("interesses", current ? `${current}, ${chip}` : chip, {
      shouldValidate: true,
    });
  };

  const onSubmit = async (briefing: TripBriefing) => {
    setSubmitError(undefined);
    try {
      const briefingKey = JSON.stringify(briefing);
      const idempotencyKey =
        idempotencyKeys.current.get(briefingKey) ?? crypto.randomUUID();
      idempotencyKeys.current.set(briefingKey, idempotencyKey);
      const created = await api.createExecution(briefing, idempotencyKey);
      router.push(`/executions/${created.id}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setSubmitError(
          error.isRateLimited && error.retryAfterSeconds
            ? `${error.message} (aguarde ${Math.ceil(error.retryAfterSeconds / 60)} min)`
            : error.message,
        );
        return;
      }
      setSubmitError("Algo deu errado ao enviar o briefing. Tente novamente.");
    }
  };

  return (
    <Card className="border-border shadow-md">
      <CardContent className="pt-5">
        <form
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
          className="flex flex-col gap-5"
        >
          {selectedDestination ? (
            <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary-subtle px-3.5 py-2.5 text-xs text-primary">
              <div className="flex items-center gap-2">
                <Sparkles className="size-4 shrink-0 text-primary" aria-hidden />
                <span>
                  Destino selecionado: <strong>{selectedDestination.name}</strong> ({selectedDestination.suggestedDays} dias sugeridos)
                </span>
              </div>
              {onClearDestination ? (
                <button
                  type="button"
                  onClick={onClearDestination}
                  className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
                >
                  <X className="size-3" aria-hidden />
                  Limpar
                </button>
              ) : null}
            </div>
          ) : null}

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Saindo de" error={errors.origem?.message}>
              {(a11y) => (
                <Input
                  {...a11y}
                  {...register("origem")}
                  placeholder="São Paulo, Brasil"
                  autoComplete="address-level2"
                />
              )}
            </Field>

            <Field label="Destino" error={errors.destino?.message}>
              {(a11y) => (
                <Input
                  {...a11y}
                  {...register("destino")}
                  placeholder="Lisboa, Portugal"
                />
              )}
            </Field>
          </div>

          <div className="grid gap-5 sm:grid-cols-3">
            <div>
              <Field label="Dias" error={errors.dias?.message}>
                {(a11y) => (
                  <Input
                    {...a11y}
                    {...register("dias")}
                    type="number"
                    min={1}
                    max={30}
                    inputMode="numeric"
                  />
                )}
              </Field>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {[3, 5, 7, 10].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setValue("dias", d, { shouldValidate: true })}
                    className="rounded border border-border/80 px-1.5 py-0.5 text-[10px] text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                  >
                    {d}d
                  </button>
                ))}
              </div>
            </div>

            <Field label="Moeda" error={errors.moeda?.message}>
              {(a11y) => (
                <Select {...a11y} {...register("moeda")}>
                  {CURRENCIES.map((code) => (
                    <option key={code} value={code}>
                      {CURRENCY_LABELS[code]}
                    </option>
                  ))}
                </Select>
              )}
            </Field>

            <Field label="Idioma do roteiro" error={errors.idioma?.message}>
              {(a11y) => (
                <Select {...a11y} {...register("idioma")}>
                  {LANGUAGES.map((code) => (
                    <option key={code} value={code}>
                      {LANGUAGE_LABELS[code]}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
          </div>

          <Field
            label="O que você quer aproveitar?"
            hint="Quanto mais específico, melhor o roteiro."
            error={errors.interesses?.message}
          >
            {(a11y) => (
              <Textarea
                {...a11y}
                {...register("interesses")}
                placeholder="gastronomia local, museus de arte moderna, caminhadas ao pôr do sol"
              />
            )}
          </Field>

          <div className="flex flex-wrap gap-2">
            {INTEREST_CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => addChip(chip)}
                className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
              >
                + {chip}
              </button>
            ))}
          </div>

          {submitError ? (
            <p
              role="alert"
              className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {submitError}
            </p>
          ) : null}

          <Button type="submit" size="lg" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" aria-hidden />
                Enviando…
              </>
            ) : (
              <>
                Planejar roteiro
                <ArrowRight aria-hidden />
              </>
            )}
          </Button>

          <p className="text-center text-xs text-muted-foreground">
            A geração leva cerca de 90 segundos. Você acompanha cada etapa.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
