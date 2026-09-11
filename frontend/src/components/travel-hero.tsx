import { Coins, Compass, MapPinned, Radio, Sparkles } from "lucide-react";
import Image from "next/image";

export function TravelHero() {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-border/80 bg-gradient-to-br from-surface via-surface-muted to-primary-subtle/30 p-6 shadow-sm sm:p-10 lg:p-14">
      {/* Elemento de iluminação decorativa de fundo */}
      <div
        className="pointer-events-none absolute -top-24 -right-24 size-96 rounded-full bg-primary/10 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-24 -left-24 size-80 rounded-full bg-accent/10 blur-3xl"
        aria-hidden
      />

      <div className="relative z-10 grid items-center gap-10 lg:grid-cols-12">
        {/* Chamada principal */}
        <div className="flex flex-col gap-5 lg:col-span-7">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/20 bg-surface/80 px-3.5 py-1.5 text-xs font-semibold text-primary backdrop-blur-md shadow-xs">
            <Sparkles className="size-3.5" aria-hidden />
            <span>Inteligência Artificial Especialista em Viagens</span>
          </div>

          <h1 className="text-4xl leading-[1.1] font-extrabold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
            Para onde a sua imaginação quer te levar hoje?
          </h1>

          <p className="max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Esqueça os roteiros genéricos de busca. Uma equipe de agentes
            inteligentes pesquisa os melhores pontos, calcula a logística real e
            desenha uma viagem inesquecível sob medida para o seu perfil.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Radio className="size-4 text-primary" aria-hidden />
              Acompanhamento em tempo real
            </span>
            <span className="flex items-center gap-1.5">
              <MapPinned className="size-4 text-primary" aria-hidden />
              Pontos geolocalizados no mapa
            </span>
            <span className="flex items-center gap-1.5">
              <Coins className="size-4 text-primary" aria-hidden />
              Transparência de custos e tokens
            </span>
          </div>
        </div>

        {/* Mosaico visual de inspiração fotográfica */}
        <div className="relative lg:col-span-5">
          <div className="grid grid-cols-2 gap-3.5 sm:gap-4">
            {/* Foto 1: Paisagem Marítima / Sol */}
            <div className="group relative aspect-[3/4] overflow-hidden rounded-2xl border border-white/20 shadow-md">
              <Image
                src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80"
                alt="Praia paradisíaca de águas cristalinas"
                fill
                priority
                sizes="(max-width: 768px) 50vw, 25vw"
                className="object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <div className="absolute right-3 bottom-3 left-3 text-white">
                <span className="text-[10px] uppercase tracking-wider text-white/80">
                  Praias & Ilhas
                </span>
                <p className="text-sm font-medium drop-shadow-sm">Paraísos Tropicais</p>
              </div>
            </div>

            {/* Coluna 2: Duas fotos empilhadas */}
            <div className="flex flex-col gap-3.5 sm:gap-4">
              <div className="group relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/20 shadow-md">
                <Image
                  src="https://images.unsplash.com/photo-1513581166391-887a96ddeafd?auto=format&fit=crop&w=600&q=80"
                  alt="Bondes e arquitetura histórica de Lisboa"
                  fill
                  priority
                  sizes="(max-width: 768px) 50vw, 25vw"
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                <div className="absolute right-3 bottom-3 left-3 text-white">
                  <p className="text-xs font-medium drop-shadow-sm">Charme Europeu</p>
                </div>
              </div>

              <div className="group relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/20 shadow-md">
                <Image
                  src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80"
                  alt="Tradição e modernidade em Tóquio"
                  fill
                  sizes="(max-width: 768px) 50vw, 25vw"
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                <div className="absolute right-3 bottom-3 left-3 text-white">
                  <p className="text-xs font-medium drop-shadow-sm">Ásia & Cultura</p>
                </div>
              </div>
            </div>
          </div>

          {/* Badge flutuante de equipe de IA */}
          <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 rounded-full border border-border bg-surface/95 px-4 py-2 text-xs font-medium text-foreground shadow-lg backdrop-blur-md">
            <Compass className="size-4 text-primary animate-spin" style={{ animationDuration: '12s' }} aria-hidden />
            <span>3 Agentes prontos para planejar sua viagem</span>
          </div>
        </div>
      </div>
    </section>
  );
}
