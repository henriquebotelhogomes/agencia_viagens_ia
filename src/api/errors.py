"""Erros da API no padrão RFC 9457 (`application/problem+json`).

Toda falha exposta ao cliente segue o mesmo envelope, com `type` estável para
consumo programático e `detail` legível para humanos.
"""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_CONTENT_TYPE = "application/problem+json"
# Base dos identificadores de tipo de problema (URI estável, não resolvível)
PROBLEM_TYPE_BASE = "https://voyager.ai/problems"


class ProblemDetail(Exception):  # noqa: N818 - nome definido pela RFC 9457
    """Erro de domínio serializável como `problem+json` (RFC 9457).

    Args:
        status_code: código HTTP da resposta.
        title: resumo curto e estável do tipo de problema.
        detail: explicação específica desta ocorrência.
        problem_type: sufixo do identificador (`type`); usa `about:blank` se vazio.
        extra: campos adicionais específicos do problema.
    """

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        problem_type: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.problem_type = (
            f"{PROBLEM_TYPE_BASE}/{problem_type}" if problem_type else "about:blank"
        )
        self.extra = extra or {}

    def to_dict(self, instance: str | None = None) -> dict[str, Any]:
        """Serializa no formato RFC 9457."""
        body: dict[str, Any] = {
            "type": self.problem_type,
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }
        if instance:
            body["instance"] = instance
        body.update(self.extra)
        return body


class ExecutionNotFound(ProblemDetail):
    """Execução inexistente."""

    def __init__(self, execution_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Execução não encontrada",
            detail=f"Não existe execução com o identificador '{execution_id}'.",
            problem_type="execution-not-found",
        )


class RateLimitExceeded(ProblemDetail):
    """Cliente excedeu a cota de execuções (FR-09)."""

    def __init__(self, limit: int, retry_after_seconds: int) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            title="Limite de requisições excedido",
            detail=(
                f"Limite de {limit} execuções por hora atingido. "
                f"Tente novamente em {retry_after_seconds} segundos."
            ),
            problem_type="rate-limit-exceeded",
            extra={"limit": limit, "retry_after": retry_after_seconds},
        )


class ServiceUnavailable(ProblemDetail):
    """Dependência essencial indisponível (banco ou fila)."""

    def __init__(self, dependency: str) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Serviço temporariamente indisponível",
            detail=f"A dependência '{dependency}' não está disponível.",
            problem_type="service-unavailable",
            extra={"dependency": dependency},
        )


def _problem_response(problem: ProblemDetail, request: Request) -> JSONResponse:
    headers = {}
    if isinstance(problem, RateLimitExceeded):
        headers["Retry-After"] = str(problem.extra["retry_after"])
    return JSONResponse(
        status_code=problem.status_code,
        content=problem.to_dict(instance=str(request.url.path)),
        media_type=PROBLEM_CONTENT_TYPE,
        headers=headers or None,
    )


async def problem_detail_handler(
    request: Request, exc: Exception
) -> JSONResponse:  # pragma: no cover - registrado no app
    """Converte ``ProblemDetail`` em resposta `problem+json`."""
    assert isinstance(exc, ProblemDetail)
    return _problem_response(exc, request)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Converte ``HTTPException`` do Starlette para o envelope RFC 9457."""
    assert isinstance(exc, StarletteHTTPException)
    problem = ProblemDetail(
        status_code=exc.status_code,
        title="Erro na requisição",
        detail=str(exc.detail),
    )
    return _problem_response(problem, request)


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Converte erro de validação do Pydantic para o envelope RFC 9457."""
    assert isinstance(exc, RequestValidationError)
    problem = ProblemDetail(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Requisição inválida",
        detail="Um ou mais campos do briefing são inválidos.",
        problem_type="validation-error",
        extra={"errors": _serialize_validation_errors(exc)},
    )
    return _problem_response(problem, request)


def _serialize_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Extrai campo e mensagem de cada erro, sem expor a entrada recebida."""
    return [
        {
            "field": ".".join(str(part) for part in error.get("loc", ())),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,  # noqa: ARG001 - detalhe interno nunca é exposto ao cliente
) -> JSONResponse:
    """Rede de segurança: nunca vaza stack trace nem detalhe interno."""
    problem = ProblemDetail(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Erro interno",
        detail="Ocorreu um erro inesperado ao processar a requisição.",
        problem_type="internal-error",
    )
    return _problem_response(problem, request)
