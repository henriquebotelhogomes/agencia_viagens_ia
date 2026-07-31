import { Coins, MapPinned, Radio } from "lucide-react";

import { BriefingForm } from "@/components/briefing-form";

const PILLARS = [
  {
    icon: Radio,
    title: "Você vê o trabalho acontecendo",
    body: "Três agentes pesquisam, calculam custos e montam o roteiro. O progresso chega em tempo real, etapa por etapa.",
  },
  {
    icon: Coins,
    title: "Custo na mesa, não escondido",
    body: "Cada roteiro mostra os tokens consumidos e quanto custaria no GPT-4o. Transparência de operação, não marketing.",
  },
  {
    icon: MapPinned,
    title: "Do texto para o mapa",
    body: "Os lugares sugeridos são geolocalizados e desenhados num mapa interativo, prontos para o seu planejamento.",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-20">
      <div className="grid items-start gap-12 lg:grid-cols-[1fr_28rem] lg:gap-16">
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-5">
            <p className="text-sm font-medium tracking-wide text-primary uppercase">
              Roteiros por agentes de IA
            </p>
            <h1 className="max-w-xl text-4xl leading-[1.05] sm:text-5xl lg:text-6xl">
              Sua próxima viagem,
              <br />
              planejada por uma equipe
              <br />
              <span className="text-primary">que mostra o trabalho.</span>
            </h1>
            <p className="max-w-lg text-lg text-muted-foreground">
              Diga para onde vai e o que gosta. Um guia local, um analista de
              logística e um arquiteto de roteiros trabalham juntos — e você
              acompanha cada passo, com o custo à vista.
            </p>
          </div>

          <dl className="flex flex-col gap-6 border-t border-border pt-8">
            {PILLARS.map(({ icon: Icon, title, body }) => (
              <div key={title} className="flex gap-4">
                <span
                  className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-md bg-primary-subtle text-primary"
                  aria-hidden
                >
                  <Icon className="size-4.5" />
                </span>
                <div>
                  <dt className="font-medium">{title}</dt>
                  <dd className="mt-1 text-sm text-muted-foreground">{body}</dd>
                </div>
              </div>
            ))}
          </dl>
        </div>

        <div className="lg:sticky lg:top-24">
          <BriefingForm />
        </div>
      </div>
    </div>
  );
}
