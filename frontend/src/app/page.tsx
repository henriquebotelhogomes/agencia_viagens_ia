import { HomePlannerSection } from "@/components/home-planner-section";
import { TravelHero } from "@/components/travel-hero";

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-14 px-4 py-8 sm:px-6 sm:py-12">
      {/* Hero Visual Imersivo com Fotos e Chamada Inspiradora */}
      <TravelHero />

      {/* Seção Interativa com Vitrine de Destinos e Formulário Inteligente */}
      <HomePlannerSection />
    </div>
  );
}
