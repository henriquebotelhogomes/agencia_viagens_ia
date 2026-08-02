"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
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

export function BriefingForm() {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string>();
  const idempotencyKeys = useRef(new Map<string, string>());

  const {
    register,
    handleSubmit,
    setValue,
    getValues,
    formState: { errors, isSubmitting },
    // Três genéricos: campos crus, contexto e o tipo já validado que chega ao
    // handler. Necessário porque `dias` é coagido de string para número.
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
      // A chave é aleatória por navegador, mas é mantida para um retry deste
      // mesmo briefing após falha transitória. Nunca é compartilhada entre
      // usuários que preencheram os mesmos campos.
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
    <Card className="shadow-md">
      <CardContent className="pt-5">
        {/* A chamada a handleSubmit fica no handler (não no render): onSubmit
            lê o ref de idempotência, e a regra react-hooks/refs veta passar
            ao render uma função que possa ler ref. */}
        <form
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
          className="flex flex-col gap-5"
        >
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
