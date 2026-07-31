"""Testes do bootstrap do processo (src/bootstrap.py).

Cobre a regressão de produção que motivou o módulo: o CrewAI lê ``REDIS_URL``
numa constante de módulo, então a limpeza precisa acontecer **antes** do import.
"""

import os
import subprocess
import sys

from src.bootstrap import isolate_redis_from_third_parties


def test_remove_redis_url_com_tls(mocker) -> None:
    """URL `rediss://` sai do ambiente para não ser capturada por terceiros."""
    mocker.patch.dict(os.environ, {"REDIS_URL": "rediss://:pw@host:26770"}, clear=True)

    removed = isolate_redis_from_third_parties()

    assert removed is True
    assert "REDIS_URL" not in os.environ


def test_preserva_redis_url_sem_tls(mocker) -> None:
    """Sem TLS, as bibliotecas conectam normalmente — nada a fazer."""
    mocker.patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}, clear=True)

    removed = isolate_redis_from_third_parties()

    assert removed is False
    assert os.environ["REDIS_URL"] == "redis://localhost:6379/0"


def test_sem_redis_url_configurada(mocker) -> None:
    mocker.patch.dict(os.environ, {}, clear=True)

    assert isolate_redis_from_third_parties() is False


def test_crewai_nao_ve_redis_url_com_tls_no_worker() -> None:
    """Regressão de produção (2026-07-30): ordem de import do worker.

    O CrewAI define ``_REDIS_URL = os.environ.get("REDIS_URL")`` no import de
    ``crewai/utilities/lock_store.py`` e, se houver valor, usa
    ``portalocker.RedisLock`` — que constrói o próprio cliente Redis, sem a
    configuração de certificado. Com o Heroku Key-Value Store (`rediss://` com
    certificado self-signed), todo ``kickoff()`` morria em
    ``CERTIFICATE_VERIFY_FAILED``.

    Este teste roda num subprocesso limpo, com ``REDIS_URL`` de TLS no
    ambiente, e verifica que após importar o módulo do worker o CrewAI **não**
    enxergou a variável. Reprova se alguém reordenar os imports.
    """
    script = (
        "import src.worker.settings;"
        "from crewai.utilities import lock_store;"
        "print('CREWAI_REDIS_URL=', repr(lock_store._REDIS_URL));"
        "print('REDIS_AVAILABLE=', lock_store._redis_available())"
    )
    env = {
        **os.environ,
        "REDIS_URL": "rediss://:senha@host.compute.amazonaws.com:26770",
        # Evita que o worker tente construir a fila no import do módulo
        "QUEUE_NAME": "voyager",
    }

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    assert "CREWAI_REDIS_URL= None" in result.stdout, result.stdout
    assert "REDIS_AVAILABLE= False" in result.stdout, result.stdout
