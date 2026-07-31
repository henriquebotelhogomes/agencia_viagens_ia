import io
import json

from loguru import logger

from src.config import Settings
from src.utils.logger import setup_logger


def test_dynamic_sink_receives_messages() -> None:
    """Sinks dinâmicos (ex.: buffer do FinOps) recebem as mensagens logadas."""
    setup_logger()

    log_buffer = io.StringIO()
    buf_id = logger.add(log_buffer, format="{message}", level="INFO")

    message = "Mensagem de teste para o buffer"
    logger.info(message)

    assert message in log_buffer.getvalue()

    logger.remove(buf_id)


def test_production_logs_are_json_on_stdout(capsys) -> None:
    """Em produção, os logs saem como JSON estruturado em stdout (S9)."""
    prod_settings = Settings(_env_file=None, APP_ENV="production")
    setup_logger(prod_settings)

    logger.info("mensagem estruturada")

    captured = capsys.readouterr()
    # Cada linha é um objeto JSON válido com o campo padrão do loguru
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert "mensagem estruturada" in payload["text"]
    assert payload["record"]["level"]["name"] == "INFO"

    # Restaura o modo de desenvolvimento para não afetar outros testes
    setup_logger(Settings(_env_file=None))


def test_setup_logger_survives_unwritable_log_dir(mocker) -> None:
    """Diretório de log sem permissão não derruba a aplicação.

    Regressão: o container roda como usuário non-root (item S10 do PRD) e não
    pode criar `/app/logs` — antes, isso causava `PermissionError` no startup.
    """
    mocker.patch(
        "pathlib.Path.mkdir",
        side_effect=PermissionError("Permission denied"),
    )

    result = setup_logger(Settings(_env_file=None))

    assert result is logger  # configurou e seguiu, só com console
    logger.info("segue funcionando sem arquivo")

    setup_logger(Settings(_env_file=None))
