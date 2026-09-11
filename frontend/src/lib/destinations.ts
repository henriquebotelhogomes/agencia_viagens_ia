export interface Destination {
  id: string;
  name: string;
  country: string;
  tagline: string;
  category: "todos" | "praia" | "cultura" | "gastronomia" | "natureza" | "romantico";
  categoryLabel: string;
  imageUrl: string;
  badge?: string;
  suggestedDays: number;
  currency: "BRL" | "USD" | "EUR" | "GBP";
  interests: string[];
  highlights: string[];
}

export const DESTINATION_CATEGORIES = [
  { id: "todos", label: "Todos os Destinos" },
  { id: "praia", label: "Praias & Ilhas" },
  { id: "cultura", label: "História & Cultura" },
  { id: "gastronomia", label: "Gastronomia" },
  { id: "natureza", label: "Natureza & Ecoturismo" },
  { id: "romantico", label: "Romance & Charme" },
] as const;

export const POPULAR_DESTINATIONS: Destination[] = [
  {
    id: "lisboa",
    name: "Lisboa, Portugal",
    country: "Portugal",
    tagline: "Colinas históricas, bondes clássicos, miradouros e pastéis de Belém quentinhos.",
    category: "cultura",
    categoryLabel: "Cultura & Charme",
    imageUrl:
      "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?auto=format&fit=crop&w=1000&q=80",
    badge: "Mais Procurado",
    suggestedDays: 4,
    currency: "EUR",
    interests: ["gastronomia", "história", "arte e museus", "arquitetura"],
    highlights: ["Torre de Belém", "Bairro Alfama", "Miradouro de Santa Luzia"],
  },
  {
    id: "rio",
    name: "Rio de Janeiro, Brasil",
    country: "Brasil",
    tagline: "O encontro épico entre praias douradas, floresta tropical e o Cristo Redentor.",
    category: "praia",
    categoryLabel: "Praias & Paisagens",
    imageUrl:
      "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?auto=format&fit=crop&w=1000&q=80",
    badge: "Favorito Nacional",
    suggestedDays: 5,
    currency: "BRL",
    interests: ["praias", "natureza", "vida noturna", "gastronomia"],
    highlights: ["Pão de Açúcar", "Ipanema & Copacabana", "Pôr do sol no Arpoador"],
  },
  {
    id: "toquio",
    name: "Tóquio, Japão",
    country: "Japão",
    tagline: "Fusão mágica entre templos milenares, neon futurista e o melhor da culinária mundial.",
    category: "cultura",
    categoryLabel: "Tradição & Futuro",
    imageUrl:
      "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1000&q=80",
    badge: "Tendência",
    suggestedDays: 7,
    currency: "USD",
    interests: ["gastronomia", "arte e museus", "arquitetura", "compras"],
    highlights: ["Templo Senso-ji", "Cruzamento de Shibuya", "Jardins Shinjuku"],
  },
  {
    id: "roma",
    name: "Roma, Itália",
    country: "Itália",
    tagline: "Museu a céu aberto: o imponente Coliseu, fontes renascentistas e massas divinas.",
    category: "gastronomia",
    categoryLabel: "História & Gastronomia",
    imageUrl:
      "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1000&q=80",
    badge: "Clássico Eterno",
    suggestedDays: 5,
    currency: "EUR",
    interests: ["história", "gastronomia", "arquitetura", "arte e museus"],
    highlights: ["Coliseu & Fórum", "Fontana di Trevi", "Bairro Trastevere"],
  },
  {
    id: "machu-picchu",
    name: "Cusco & Machu Picchu, Peru",
    country: "Peru",
    tagline: "Montanhas místicas nos Andes, ruínas incas lendárias e culinária premiada.",
    category: "natureza",
    categoryLabel: "Aventura & Mistério",
    imageUrl:
      "https://images.unsplash.com/photo-1526392060635-9d6019884377?auto=format&fit=crop&w=1000&q=80",
    badge: "Aventura Épica",
    suggestedDays: 6,
    currency: "USD",
    interests: ["história", "natureza", "gastronomia"],
    highlights: ["Santuário Machu Picchu", "Vale Sagrado", "Plaza de Armas"],
  },
  {
    id: "paris",
    name: "Paris, França",
    country: "França",
    tagline: "A elegância da Torre Eiffel, galerias do Louvre e passeios às margens do Rio Sena.",
    category: "romantico",
    categoryLabel: "Romance & Arte",
    imageUrl:
      "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=80",
    badge: "Icônico",
    suggestedDays: 5,
    currency: "EUR",
    interests: ["arte e museus", "gastronomia", "arquitetura", "compras"],
    highlights: ["Torre Eiffel", "Museu do Louvre", "Basílica de Sacré-Cœur"],
  },
  {
    id: "santorini",
    name: "Santorini, Grécia",
    country: "Grécia",
    tagline: "Falésias com vilas brancas, mar azul cobalto e o pôr do sol mais aplaudido do mundo.",
    category: "praia",
    categoryLabel: "Ilhas Paradisíacas",
    imageUrl:
      "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=1000&q=80",
    badge: "Paraíso Azul",
    suggestedDays: 4,
    currency: "EUR",
    interests: ["praias", "gastronomia", "natureza"],
    highlights: ["Vila de Oia", "Passeio de Catamarã", "Red Beach"],
  },
  {
    id: "bariloche",
    name: "Bariloche, Argentina",
    country: "Argentina",
    tagline: "Lagos azuis espelhados, montanhas andinas, florestas de conto de fadas e chocolates.",
    category: "natureza",
    categoryLabel: "Lagos & Montanhas",
    imageUrl:
      "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=80",
    badge: "Patagônia",
    suggestedDays: 4,
    currency: "USD",
    interests: ["natureza", "gastronomia", "compras"],
    highlights: ["Circuito Chico", "Cerro Campanario", "Rua das Chocolaterias"],
  },
];

export function getDestinationHeroImage(destinationName: string): string {
  const normalized = destinationName.toLowerCase();
  const matched = POPULAR_DESTINATIONS.find((d) =>
    normalized.includes(d.name.toLowerCase().split(",")[0].trim()),
  );
  if (matched) return matched.imageUrl;

  return "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80";
}
