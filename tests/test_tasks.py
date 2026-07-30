"""Testes das tarefas e da localização de moeda/idioma (item S14 do PRD)."""

from unittest.mock import MagicMock

from src.tasks import TravelTasks
from src.utils.localization import currency_label, language_name

# ---------------------------------------------------------------------------
# Helpers de localização
# ---------------------------------------------------------------------------


def test_currency_label_known_and_unknown() -> None:
    assert currency_label("BRL") == "BRL (R$)"
    assert currency_label(" usd ") == "USD (US$)"
    # Código desconhecido: retorna normalizado, sem símbolo
    assert currency_label("jpy") == "JPY"


def test_language_name_known_and_unknown() -> None:
    assert language_name("pt-BR") == "português do Brasil"
    assert language_name("en-US") == "inglês (English)"
    # Código desconhecido: retorna como está (o LLM ainda entende)
    assert language_name("fr-FR") == "fr-FR"


# ---------------------------------------------------------------------------
# Tarefas parametrizadas por moeda/idioma
# ---------------------------------------------------------------------------


def _task_kwargs(mocker):
    """Patcheia ``Task`` e devolve função que captura os kwargs da criação."""
    task_cls = mocker.patch("src.tasks.Task")

    def get_kwargs():
        return task_cls.call_args.kwargs

    return get_kwargs


def test_logistics_task_uses_briefing_currency_and_language(mocker) -> None:
    get_kwargs = _task_kwargs(mocker)
    tasks = TravelTasks()

    tasks.calculate_logistics(
        MagicMock(), "Paris", 5, "São Paulo", moeda="USD", idioma="en-US"
    )

    kwargs = get_kwargs()
    assert "USD (US$)" in kwargs["description"]
    assert "inglês (English)" in kwargs["description"]
    assert "USD (US$)" in kwargs["expected_output"]
    # Nada de R$ hardcoded quando a moeda é outra
    assert "R$" not in kwargs["description"]
    assert "R$" not in kwargs["expected_output"]


def test_logistics_task_defaults_to_brl_and_ptbr(mocker) -> None:
    get_kwargs = _task_kwargs(mocker)
    tasks = TravelTasks()

    tasks.calculate_logistics(MagicMock(), "Paris", 5, "São Paulo")

    kwargs = get_kwargs()
    assert "BRL (R$)" in kwargs["description"]
    assert "português do Brasil" in kwargs["description"]


def test_itinerary_task_localized_and_days_interpolated(mocker) -> None:
    """Roteiro final respeita moeda/idioma e interpola os dias no output.

    Regressão: o texto original continha ``{dias}`` literal (não interpolado)
    no ``expected_output``.
    """
    get_kwargs = _task_kwargs(mocker)
    tasks = TravelTasks()

    tasks.compile_itinerary(
        MagicMock(), "Roma", 7, "história", moeda="EUR", idioma="es-ES"
    )

    kwargs = get_kwargs()
    assert "EUR (€)" in kwargs["description"]
    assert "espanhol (español)" in kwargs["expected_output"]
    assert "Cronograma de 7 dias" in kwargs["expected_output"]
    assert "{dias}" not in kwargs["expected_output"]


def test_research_task_respects_language(mocker) -> None:
    get_kwargs = _task_kwargs(mocker)
    tasks = TravelTasks()

    tasks.research_destination(MagicMock(), "Lisboa", "vinhos", idioma="en-US")

    kwargs = get_kwargs()
    assert "inglês (English)" in kwargs["description"]
    assert "inglês (English)" in kwargs["expected_output"]
