from pydantic import BaseModel, Field
from typing import List, Optional

class Location(BaseModel):
    name: str = Field(..., description="Nome do local (atração, restaurante ou hotel)")
    lat: Optional[float] = Field(None, description="Latitude do local")
    lon: Optional[float] = Field(None, description="Longitude do local")
    type: str = Field("marker", description="Tipo de marcador no mapa")

class LocationList(BaseModel):
    locations: List[Location] = Field(default_factory=list, max_length=10)
