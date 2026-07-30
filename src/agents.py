"""Fábrica de agentes da equipe de viagens.

Estratégia de LLM (PRD D2 / §2.2): **OpenCode Go como gateway primário** dos
tiers baratos (endpoint OpenAI-compatible) com **failover para o OpenRouter** —
o orçamento do Go é compartilhado com o uso pessoal de coding, então a demo
nunca pode bloquear nele. O tier `pro` roda no OpenRouter.

O failover é **explícito na camada da aplicação** (``use_fallback=True``), não via
parâmetro ``fallbacks`` do litellm: o CrewAI 1.x usa providers *nativos* (SDK do
provedor) para prefixos conhecidos como ``openai/``, e esse caminho não aceita
opções exclusivas do litellm. Quem orquestra o retry é o ``CrewBuilder``.

Nada é configurado no import (item S1 do PRD): a configuração global do LiteLLM
e a exportação de chaves ficam em ``src.runtime.configure_llm_runtime``. Os LLMs
e as ferramentas são criados sob demanda, de forma memoizada por instância.
"""

from typing import Any

from crewai import LLM, Agent

from src.config import Settings, get_settings
from src.utils.localization import DEFAULT_CURRENCY, currency_label

# Modelo do Go usado como reserva do tier `pro`
GO_PRO_MODEL = "glm-5.2"


class TravelAgents:
    """Cria os agentes com os LLMs do gateway ativo.

    Args:
        settings: configuração injetada (usa a padrão quando omitida).
        use_fallback: quando ``True``, todos os tiers usam o OpenRouter —
            acionado pelo ``CrewBuilder`` após falha do gateway primário.
    """

    def __init__(
        self, settings: Settings | None = None, *, use_fallback: bool = False
    ) -> None:
        self.settings = settings or get_settings()
        # Sem chave do Go, o OpenRouter é o único caminho possível
        self.use_fallback = use_fallback or not self.settings.opencode_enabled
        self._llm_fast: Any | None = None
        self._llm_fast_tools: Any | None = None
        self._llm_pro: Any | None = None
        self._search_tool: Any | None = None

    # ------------------------------------------------------------------
    # Blocos de configuração por gateway
    # ------------------------------------------------------------------
    def _go_model(self, model: str) -> dict[str, Any]:
        """Kwargs para um modelo servido pelo OpenCode Go."""
        return {
            # Prefixo "openai/" -> provider nativo OpenAI-compatible do CrewAI
            "model": f"openai/{model}",
            "api_key": self.settings.opencode_api_key,
            "api_base": self.settings.OPENCODE_API_BASE,
        }

    def _openrouter_model(self, model: str) -> dict[str, Any]:
        """Kwargs para um modelo do OpenRouter (fallback / tier `pro`)."""
        return {
            "model": model,  # já vem prefixado com "openrouter/" da config
            "api_key": self.settings.openrouter_api_key,
        }

    # ------------------------------------------------------------------
    # Tiers de LLM (PRD §2.2)
    # ------------------------------------------------------------------
    @property
    def llm_fast(self) -> Any:
        """Tier `fast`: Go (deepseek) ou OpenRouter (gemini) em failover."""
        if self._llm_fast is None:
            kwargs = (
                self._openrouter_model(self.settings.LLM_FALLBACK_FAST)
                if self.use_fallback
                else self._go_model(self.settings.LLM_MODEL_FAST)
            )
            self._llm_fast = LLM(**kwargs, temperature=0.2)
        return self._llm_fast

    @property
    def llm_fast_tools(self) -> Any:
        """Tier `fast-tools`: exige function calling confiável (Tavily)."""
        if self._llm_fast_tools is None:
            kwargs = (
                self._openrouter_model(self.settings.LLM_FALLBACK_TOOLS)
                if self.use_fallback
                else self._go_model(self.settings.LLM_MODEL_FAST_TOOLS)
            )
            self._llm_fast_tools = LLM(**kwargs, temperature=0.2)
        return self._llm_fast_tools

    @property
    def llm_pro(self) -> Any:
        """Tier `pro`: OpenRouter (gemini pago); Go (glm) no failover."""
        if self._llm_pro is None:
            kwargs = (
                self._go_model(GO_PRO_MODEL)
                if self.use_fallback and self.settings.opencode_enabled
                else self._openrouter_model(self.settings.LLM_MODEL_PRO)
            )
            self._llm_pro = LLM(**kwargs, temperature=0.3)
        return self._llm_pro

    @property
    def search_tool(self) -> Any:
        """Busca web otimizada para agentes — Tavily (PRD D11)."""
        if self._search_tool is None:
            from crewai_tools import TavilySearchTool

            self._search_tool = TavilySearchTool(
                api_key=self.settings.tavily_api_key,
                max_results=5,
            )
        return self._search_tool

    # ------------------------------------------------------------------
    # Agentes
    # ------------------------------------------------------------------
    def local_expert(self) -> Agent:
        return Agent(
            role="Guia Local",
            goal=(
                "Fornecer informações detalhadas sobre {destino} baseadas em "
                "{interesses}."
            ),
            backstory=(
                "Um guia local experiente que conhece todos os segredos de {destino}."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm_fast,
            max_iter=3,
        )

    def logistics_manager(self, moeda: str = DEFAULT_CURRENCY) -> Agent:
        moeda_txt = currency_label(moeda)
        return Agent(
            role="Gerente de Logística",
            goal=(
                f"Estimar custos detalhados em {moeda_txt} para a viagem "
                "em {destino}."
            ),
            backstory=(
                "Analista financeiro especializado em turismo. "
                "Você não aceita valores genéricos. "
                "Você busca sempre nomes de companhias aéreas reais, "
                "nomes de hotéis com suas estrelas "
                "e detalha as refeições (café, almoço, jantar) "
                "para compor o custo diário. "
                f"Tudo deve ser calculado e exibido em {moeda_txt}."
            ),
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast_tools,
            max_iter=3,
        )

    def itinerary_architect(self) -> Agent:
        return Agent(
            role="Arquiteto de Roteiros",
            goal="Criar roteiro de {dias} dias em {destino}.",
            backstory=(
                "Arquiteto de roteiros premium com redundância de "
                "modelos (Plano A, B e C)."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm_pro,
            max_iter=3,
        )
