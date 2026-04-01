import io
import sys
from pathlib import Path

from loguru import logger

# Adiciona o diretório src ao path se necessário
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.utils.logger import add_streamlit_sink, setup_logger


class MockPlaceholder:
    def __init__(self):
        self.output = ""

    def code(self, content, language="text"):
        self.output = content


def test_logger_flow():
    # 1. Configura
    setup_logger()
    mock_st = MockPlaceholder()

    # 2. Adiciona Sink do Streamlit
    sink_id = add_streamlit_sink(mock_st)

    # 3. Loga algo
    test_msg = "Mensagem de Teste para o Agente"
    logger.info(test_msg)

    # 4. Verifica
    assert test_msg in mock_st.output
    print("✓ Loguru integration with Streamlit Sink working.")

    # 5. Testa Buffer do FinOps
    log_buffer = io.StringIO()
    buf_id = logger.add(log_buffer, format="{message}", level="INFO")

    another_msg = "Outra mensagem para FinOps"
    logger.info(another_msg)

    assert another_msg in log_buffer.getvalue()
    print("✓ Loguru integration with Resource Buffer working.")

    # 6. Cleanup
    logger.remove(sink_id)
    logger.remove(buf_id)
    print("✓ Cleanup successful.")


if __name__ == "__main__":
    try:
        test_logger_flow()
        print("\nSUCCESS: Logger infrastructure is robust.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        sys.exit(1)
