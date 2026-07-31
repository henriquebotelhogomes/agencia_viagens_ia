"""Bootstrap do processo — executado **antes** dos imports de domínio.

Existe por um motivo específico: bibliotecas de terceiros que leem o ambiente
em **tempo de import**. Para essas, `configure_llm_runtime` já é tarde demais —
quando ela roda, o valor já foi capturado numa constante de módulo.

Este é o único lugar do projeto autorizado a mutar `os.environ` fora de uma
função chamada explicitamente pelo entrypoint, e a ordem de chamada importa.
"""

import os

from loguru import logger

# Prefixo de URL Redis com TLS. Provedores gerenciados (Heroku Key-Value Store)
# usam certificado self-signed nesse esquema.
_TLS_SCHEME = "rediss://"

# Nome privado da aplicação. `Settings` o aceita com precedência sobre
# `REDIS_URL`, então mover a variável não tira o Redis da aplicação — apenas o
# esconde de bibliotecas que leem o ambiente por conta própria.
APP_REDIS_ENV = "APP_REDIS_URL"

# Nome privado da aplicação. `Settings` aceita este nome com precedência sobre
# `REDIS_URL`, então mover a variável não tira o Redis da aplicação — apenas o
# esconde de bibliotecas que leem o ambiente por conta própria.
APP_REDIS_ENV = "APP_REDIS_URL"


def isolate_redis_from_third_parties() -> bool:
    """Move ``REDIS_URL`` para um nome privado quando a conexão exige TLS permissivo.

    O CrewAI lê ``REDIS_URL`` numa constante de módulo em
    ``crewai/utilities/lock_store.py`` e, se ela existir, usa
    ``portalocker.RedisLock`` para sincronizar o storage de task outputs. Esse
    lock constrói o próprio cliente Redis, **sem** a configuração de
    certificado — e todo `kickoff()` morria com ``CERTIFICATE_VERIFY_FAILED``
    contra o Heroku Key-Value Store (regressão real de produção, 2026-07-30).

    A variável é **movida**, não descartada: ``Settings`` lê
    ``APP_REDIS_URL`` com precedência, e a aplicação continua conectando pela
    fábrica em :mod:`src.services.redis_client`, que trata o TLS. O CrewAI volta
    ao ``portalocker.Lock`` local, adequado para um processo por dyno.

    Deve ser chamada **antes** de qualquer import que alcance o CrewAI.

    Returns:
        ``True`` se a variável foi movida.
    """
    url = os.environ.get("REDIS_URL", "")
    if not url.startswith(_TLS_SCHEME):
        return False

    os.environ.setdefault(APP_REDIS_ENV, url)
    os.environ.pop("REDIS_URL", None)
    logger.info(
        f"Bootstrap: REDIS_URL movida para {APP_REDIS_ENV} (TLS self-signed). "
        "Bibliotecas de terceiros usarão locks locais; o Redis da aplicação segue "
        "ativo pela fábrica de clientes."
    )
    return True
