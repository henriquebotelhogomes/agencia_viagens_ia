import sys
from pathlib import Path

from loguru import logger

# Configuração de Caminhos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Formato Profissional
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger():
    """
    Configura o logger padrão da aplicação.
    Remove o handler padrão (stdout) e adiciona um com formatação customizada
    e um arquivo de log persistente com rotação.
    """
    # Remove configurações anteriores para evitar duplicidade
    logger.remove()

    # Adiciona saída para Console (Terminal) com Cores
    logger.add(sys.stderr, format=LOG_FORMAT, level="INFO", colorize=True)

    # Adiciona persistência em arquivo (Rotação de 10MB / Retenção de 10 dias)
    logger.add(
        LOG_DIR / "app.log",
        rotation="10 MB",
        retention="10 days",
        format=LOG_FORMAT,
        level="DEBUG",
        encoding="utf-8",
    )

    return logger


class StreamlitSink:
    """
    Sink customizado para integrar o Loguru com o Streamlit.
    Ele atualiza um placeholder ou o session_state em tempo real.
    """

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.logs = []

    def write(self, message):
        # O Loguru envia a mensagem já formatada
        self.logs.append(message)
        # Mantém apenas os últimos 5000 caracteres 
        # para não estourar a memória do browser
        log_text = "".join(self.logs)[-5000:]
        self.placeholder.code(log_text, language="text")


def add_streamlit_sink(placeholder):
    """
    Adiciona um sink dinâmico para o Streamlit.
    Útil para exibir o raciocínio dos agentes na UI.
    """
    sink = StreamlitSink(placeholder)
    return logger.add(sink.write, format="{message}", level="INFO")
