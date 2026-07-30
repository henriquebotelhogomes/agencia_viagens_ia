"""Schemas de request e response da API (contratos públicos).

Estes modelos são a fronteira entre o cliente e o domínio: validam a entrada e
controlam exatamente o que sai. A OpenAPI é gerada a partir daqui.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.db.models import ExecutionStatus
from src.utils.localization import (
    CURRENCY_SYMBOLS,
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    LANGUAGE_NAMES,
)

CurrencyCode = Literal["BRL", "USD", "EUR", "GBP"]
LanguageCode = Literal["pt-BR", "en-US", "es-ES"]


class TripBriefing(BaseModel):
    """Entrada do usuário para gerar um roteiro (FR-01)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "origem": "São Paulo, Brasil",
                    "destino": "Roma, Itália",
                    "dias": 3,
                    "interesses": "história e gastronomia",
                    "moeda": "EUR",
                    "idioma": "pt-BR",
                }
            ]
        }
    )

    origem: Annotated[str, Field(min_length=2, max_length=200)]
    destino: Annotated[str, Field(min_length=2, max_length=200)]
    dias: Annotated[int, Field(ge=1, le=30)]
    interesses: Annotated[str, Field(max_length=500)] = ""
    moeda: CurrencyCode = DEFAULT_CURRENCY  # type: ignore[assignment]
    idioma: LanguageCode = DEFAULT_LANGUAGE  # type: ignore[assignment]

    @field_validator("origem", "destino", "interesses")
    @classmethod
    def strip_text(cls, value: str) -> str:
        """Normaliza espaços das entradas textuais."""
        return value.strip()

    def fingerprint(self) -> str:
        """Hash determinístico do briefing.

        Habilita idempotência e reuso de cache. Moeda e idioma entram no hash:
        o mesmo destino em moedas diferentes é um roteiro diferente.
        """
        raw = "|".join(
            [
                self.origem.lower(),
                self.destino.lower(),
                str(self.dias),
                self.interesses.lower(),
                self.moeda.upper(),
                self.idioma.lower(),
            ]
        )
        return hashlib.sha256(raw.encode()).hexdigest()


class CostSummary(BaseModel):
    """Custo de LLM de uma execução (FR-07, item S4)."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    baseline_cost_usd: float = 0.0
    savings_usd: float = 0.0
    served_from_cache: bool = False


class ExecutionCreated(BaseModel):
    """Resposta do aceite de uma execução (`202 Accepted`)."""

    id: uuid.UUID
    status: ExecutionStatus
    stream_url: str = Field(
        description="Endpoint SSE para acompanhar o progresso em tempo real."
    )


class ExecutionDetail(BaseModel):
    """Estado completo de uma execução."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ExecutionStatus
    briefing: TripBriefing
    itinerary_markdown: str | None = None
    error: str | None = None
    llm_gateway: str | None = None
    used_fallback: bool = False
    duration_seconds: float | None = None
    cost: CostSummary = Field(default_factory=CostSummary)
    created_at: datetime
    finished_at: datetime | None = None


class GeoJSONFeatureCollection(BaseModel):
    """Locais do roteiro em GeoJSON, para o mapa (FR-05)."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]] = Field(default_factory=list)


class ProgressEvent(BaseModel):
    """Evento de progresso publicado pelo worker e transmitido via SSE (FR-03)."""

    execution_id: uuid.UUID
    status: ExecutionStatus
    message: str
    # Etapa atual (ex.: "guia_local", "logistica", "arquiteto")
    step: str | None = None
    at: datetime


class HealthStatus(BaseModel):
    """Resultado do healthcheck da API."""

    status: Literal["ok", "degraded"]
    version: str
    environment: str
    dependencies: dict[str, bool]


class LocalizationOptions(BaseModel):
    """Moedas e idiomas suportados — permite ao frontend montar os seletores."""

    currencies: dict[str, str] = Field(default_factory=lambda: dict(CURRENCY_SYMBOLS))
    languages: dict[str, str] = Field(default_factory=lambda: dict(LANGUAGE_NAMES))


class ProblemDetailResponse(BaseModel):
    """Envelope de erro no padrão RFC 9457 (`application/problem+json`).

    Modelo **documentacional**: descreve na OpenAPI o formato que os handlers
    de erro realmente produzem. Campos adicionais específicos do problema
    (ex.: `retry_after`, `errors`) são permitidos pelo padrão.
    """

    model_config = ConfigDict(extra="allow")

    type: str = Field(description="URI estável que identifica o tipo de problema")
    title: str = Field(description="Resumo curto do tipo de problema")
    status: int = Field(description="Código HTTP da resposta")
    detail: str = Field(description="Explicação específica desta ocorrência")
    instance: str | None = Field(default=None, description="Caminho da requisição")
