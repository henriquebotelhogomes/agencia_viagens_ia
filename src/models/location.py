from pydantic import BaseModel, Field


class Location(BaseModel):
    name: str = Field(..., description="Nome do local (atração, restaurante ou hotel)")
    lat: float | None = Field(None, description="Latitude do local")
    lon: float | None = Field(None, description="Longitude do local")
    type: str = Field("marker", description="Tipo de marcador no mapa")


class LocationList(BaseModel):
    locations: list[Location] = Field(default_factory=list, max_length=10)
