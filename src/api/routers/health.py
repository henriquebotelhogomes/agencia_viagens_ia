"""Rotas de saúde e metadados da API."""

from fastapi import APIRouter

from src.api.deps import SettingsDep
from src.api.schemas import HealthStatus, LocalizationOptions

router = APIRouter(tags=["meta"])

# Versão exposta na OpenAPI e no healthcheck
API_VERSION = "1.0.0"


@router.get("/health", response_model=HealthStatus, summary="Healthcheck")
async def health(settings: SettingsDep) -> HealthStatus:
    """Reporta a saúde da API e a configuração das dependências.

    Retorna `degraded` quando uma dependência essencial (banco ou fila) não está
    configurada — o serviço responde, mas não consegue aceitar execuções.
    """
    dependencies = {
        "database": settings.database_enabled,
        "queue": settings.cache_enabled,
        "llm_primary": settings.opencode_enabled,
        "llm_fallback": settings.openrouter_enabled,
        "tracing": settings.langfuse_enabled,
    }
    essential_ok = dependencies["database"] and dependencies["queue"]
    return HealthStatus(
        status="ok" if essential_ok else "degraded",
        version=API_VERSION,
        environment=settings.APP_ENV,
        dependencies=dependencies,
    )


@router.get(
    "/v1/localization",
    response_model=LocalizationOptions,
    summary="Moedas e idiomas suportados",
)
async def localization() -> LocalizationOptions:
    """Lista as opções de localização aceitas no briefing (FR-10).

    Permite que o frontend monte os seletores sem duplicar a lista.
    """
    return LocalizationOptions()
