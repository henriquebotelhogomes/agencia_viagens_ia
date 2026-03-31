import json
import re
import time
from typing import List, Optional, cast

from geopy.geocoders import Nominatim
from langchain_groq import ChatGroq

from src.config import settings
from src.models.location import Location


class GeocodingService:
    def __init__(self) -> None:
        self.geolocator = Nominatim(user_agent=settings.user_agent)
        self.llm_extractor = ChatGroq(
            api_key=settings.groq_api_key,  # type: ignore
            model=settings.model_extractor,
            temperature=0,
        )

    def extract_locations(self, itinerary_text: str) -> List[str]:
        """
        Usa LLM para extrair nomes de locais de um texto em Markdown.
        """
        prompt = f"""
        Você é um assistente de extração de dados geográficos.
        Analise o roteiro de viagem abaixo e extraia os nomes das principais atrações,
        restaurantes ou hotéis sugeridos.
        Retorne APENAS um array JSON válido (strings simples).
        No máximo 8 locais mais relevantes.

        Roteiro:
        {itinerary_text}

        Resposta esperada: ["Local 1", "Local 2"]
        """

        try:
            response = self.llm_extractor.invoke(prompt)
            content = cast(str, response.content)

            # Extração simples de JSON do corpo da resposta
            match = re.search(r"\[.*?\]", content, re.DOTALL)
            if match:
                return cast(List[str], json.loads(match.group(0)))
            return []
        except Exception:
            return []

    def get_coordinates(self, location_name: str) -> Optional[tuple[float, float]]:
        """
        Obtém as coordenadas (lat, lon) de um local usando Nominatim.
        Respeita o rate limiting da API gratuita.
        """
        try:
            time.sleep(settings.geocoding_delay)
            location = self.geolocator.geocode(location_name)
            if location:
                return (cast(float, location.latitude), cast(float, location.longitude))
        except Exception:
            pass
        return None

    def process_itinerary_locations(self, itinerary_text: str) -> List[Location]:
        """
        Fluxo completo: extrai nomes de locais e busca coordenadas.
        """
        names = self.extract_locations(itinerary_text)
        results = []

        for name in names:
            coords = self.get_coordinates(name)
            if coords:
                results.append(
                    Location(name=name, lat=coords[0], lon=coords[1], type="marker")
                )
        return results
