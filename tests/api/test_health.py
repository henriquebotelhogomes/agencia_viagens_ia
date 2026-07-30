"""Testes de metadados, saúde e contrato da OpenAPI."""

from httpx import AsyncClient

from src.api.errors import PROBLEM_CONTENT_TYPE


async def test_health_reports_ok_with_dependencies(client: AsyncClient) -> None:
    """Com banco e fila configurados, a saúde é `ok`."""
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dependencies"]["database"] is True
    assert body["dependencies"]["queue"] is True
    assert body["environment"] == "local"


async def test_health_reports_degraded_without_database(
    client: AsyncClient, api_settings, mocker
) -> None:
    """Sem dependência essencial, reporta `degraded` (mas responde 200)."""
    mocker.patch.object(
        type(api_settings), "database_enabled", property(lambda self: False)
    )

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


async def test_localization_lists_supported_options(client: AsyncClient) -> None:
    """As opções de moeda e idioma vêm do módulo de localização (FR-10)."""
    response = await client.get("/v1/localization")

    assert response.status_code == 200
    body = response.json()
    assert body["currencies"]["BRL"] == "R$"
    assert "pt-BR" in body["languages"]
    assert set(body["currencies"]) == {"BRL", "USD", "EUR", "GBP"}


async def test_openapi_schema_is_generated(client: AsyncClient) -> None:
    """A OpenAPI é publicada e cobre as rotas do MVP."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Voyager AI API"
    paths = schema["paths"]
    assert "/v1/executions" in paths
    assert "/v1/executions/{execution_id}" in paths
    assert "/v1/executions/{execution_id}/stream" in paths
    assert "/v1/executions/{execution_id}/geojson" in paths
    # O aceite assíncrono precisa estar documentado como 202
    assert "202" in paths["/v1/executions"]["post"]["responses"]


async def test_unknown_route_returns_problem_json(client: AsyncClient) -> None:
    """Rota inexistente também segue o envelope RFC 9457."""
    response = await client.get("/v1/rota-que-nao-existe")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_CONTENT_TYPE)
    body = response.json()
    assert body["status"] == 404
    assert body["instance"] == "/v1/rota-que-nao-existe"
