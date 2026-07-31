# O bootstrap precede os imports de domínio: o CrewAI captura `REDIS_URL` em
# tempo de import (ver src/bootstrap.py).
from src.bootstrap import isolate_redis_from_third_parties

isolate_redis_from_third_parties()

import io  # noqa: E402

import folium  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from src.crew_builder import CrewBuilder  # noqa: E402
from src.runtime import configure_llm_runtime  # noqa: E402
from src.services.cache_service import get_cache_service  # noqa: E402
from src.services.finance_service import FinanceService  # noqa: E402
from src.services.geocoding_service import GeocodingService  # noqa: E402
from src.utils.localization import (  # noqa: E402
    CURRENCY_SYMBOLS,
    LANGUAGE_NAMES,
    currency_label,
    language_name,
)
from src.utils.logger import LOG_DIR, add_streamlit_sink, setup_logger  # noqa: E402

# Configuração do Logger Centralizado
logger = setup_logger()

# Inicialização explícita do runtime (LiteLLM, chaves, Redis) — item S1 do PRD
configure_llm_runtime()
logger.info("Aplicação Iniciada.")

# Configuração da Página
st.set_page_config(
    page_title="Agência de Viagens IA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Inicialização de Serviços (Singletons de facto dentro do contexto do Streamlit)
@st.cache_resource
def get_geocoding_service():
    # Cache Redis de geocoding (PRD D10): TTL longo p/ coordenadas de atrações
    return GeocodingService(cache=get_cache_service())


@st.cache_resource
def get_finance_service():
    return FinanceService()


geo_service = get_geocoding_service()
fin_service = get_finance_service()
cache_service = get_cache_service()


# Funções Auxiliares de Cache
@st.cache_data
def get_itinerary_map_data(itinerary_str: str, destino: str = ""):
    locais_objs = geo_service.process_itinerary_locations(itinerary_str, destino)
    # Convertemos para dicionários para evitar erros de serialização (Pickle)
    return [
        {"name": loc.name, "lat": loc.lat, "lon": loc.lon}
        for loc in locais_objs
        if loc.lat and loc.lon
    ]


# Interface Principal
st.title("✈️ Agência de Viagens Inteligente")

# Barra Lateral: Ferramentas e Logs
with st.sidebar:
    st.header("🛠️ Utilitários")
    try:
        log_path = LOG_DIR / "app.log"
        if log_path.exists():
            with log_path.open("rb") as f:
                st.download_button(
                    label="📥 Baixar Logs Completos (.log)",
                    data=f,
                    file_name="agencia_viagens_ia.log",
                    mime="text/plain",
                    use_container_width=True,
                )
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar logs: {e}")

st.markdown("""
Esta equipe de Agentes de IA utiliza **Agentic RAG** para planejar sua viagem,
pesquisando dados em tempo real e otimizando custos.
""")

# Formulário de Entrada
with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        origem = st.text_input(
            "📍 Local de Origem", placeholder="Ex: São Paulo, Brasil"
        )
        destino = st.text_input("🌍 Destino", placeholder="Ex: Paris, França")
    with col2:
        dias = st.number_input("📅 Duração (Dias)", min_value=1, max_value=30, value=5)
        interesses = st.text_input(
            "🎭 Interesses", placeholder="Ex: Museus, gastronomia, parques..."
        )

    # Localização do roteiro (item S14 do PRD / FR-10)
    col3, col4 = st.columns(2)
    with col3:
        moeda = st.selectbox(
            "💱 Moeda",
            options=list(CURRENCY_SYMBOLS.keys()),
            index=0,
            format_func=currency_label,
        )
    with col4:
        idioma = st.selectbox(
            "🌐 Idioma do Roteiro",
            options=list(LANGUAGE_NAMES.keys()),
            index=0,
            format_func=language_name,
        )

    submitted = st.form_submit_button(
        "🚀 Planejar Roteiro Profissional", use_container_width=True
    )

if submitted:
    if not destino or not origem:
        st.warning("Por favor, preencha a Origem e o Destino para continuar.")
    else:
        st.divider()
        st.subheader("🛠️ Orquestração de Agentes em Tempo Real")

        # Verifica cache
        cached_itinerary = cache_service.get_cached_itinerary(
            origem, destino, dias, interesses, moeda=moeda, idioma=idioma
        )

        if cached_itinerary:
            st.success("⚡ Roteiro recuperado do Cache instantaneamente!")
            final_itinerary = cached_itinerary
            token_usage = None  # sem execução de LLM — custo zero
            logs_for_finops = "✨ Custos FinOps: $0.00 (Servido diretamente do Cache)"
        else:
            # Container para Logs Vivos
            log_expander = st.expander(
                "Ver 'Raciocínio' dos Agentes (Live)", expanded=True
            )
            log_placeholder = log_expander.empty()

            # Captura de logs via Loguru Sink (Streamlit + Buffer para FinOps)
            log_buffer = io.StringIO()

            log_sink_id = add_streamlit_sink(log_placeholder)
            buffer_sink_id = logger.add(log_buffer, format="{message}", level="INFO")

            logger.info(f"Iniciando planejamento para {destino}...")

            final_itinerary = None
            token_usage = None
            try:
                with st.spinner(f"A equipe está mapeando {destino}..."):
                    trip_crew = CrewBuilder(
                        destino=destino,
                        dias=dias,
                        origem=origem,
                        interesses=interesses,
                        moeda=moeda,
                        idioma=idioma,
                    )
                    final_itinerary = trip_crew.run()
                    # Tokens reais da execução (item S4 do PRD)
                    token_usage = getattr(final_itinerary, "token_usage", None)
                    if final_itinerary:
                        cache_service.save_itinerary(
                            origem,
                            destino,
                            dias,
                            interesses,
                            str(final_itinerary),
                            moeda=moeda,
                            idioma=idioma,
                        )
            except Exception as e:
                logger.error(f"Erro crítico na orquestração: {e}")
                st.error(f"Erro na orquestração: {e}")
            finally:
                # Remove os sinks para não vazar logs na próxima rodada
                logger.remove(log_sink_id)
                logger.remove(buffer_sink_id)
                logs_for_finops = log_buffer.getvalue()
                logger.info("Processamento Finalizado.")

        if final_itinerary:
            st.success("Roteiro Finalizado! ✨")
            roteiro_str = str(final_itinerary)

            tab1, tab2, tab3 = st.tabs(
                ["🗺️ Seu Roteiro", "📍 Mapa de Atrações", "💰 Auditoria FinOps"]
            )

            # ABA 1: ROTEIRO
            with tab1:
                st.markdown(roteiro_str)
                st.download_button(
                    "📥 Exportar para Markdown",
                    data=roteiro_str,
                    file_name=f"Roteiro_{destino}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            # ABA 2: MAPA INTERATIVO
            with tab2:
                st.markdown(f"### Locais Sugeridos em {destino}")

                with st.spinner("Geolocalizando pontos turísticos..."):
                    try:
                        # Busca coordenadas do destino central
                        dest_coords = geo_service.get_coordinates(destino)

                        if dest_coords:
                            m = folium.Map(location=dest_coords, zoom_start=13)

                            # Marcador Central
                            folium.Marker(
                                dest_coords,
                                popup=f"<b>{destino}</b>",
                                icon=folium.Icon(color="red", icon="star"),
                            ).add_to(m)

                            # Processa locais do roteiro
                            # (com cache para não repetir chamadas caras)
                            locais = get_itinerary_map_data(roteiro_str, destino)

                            if locais:
                                for loc in locais:
                                    folium.Marker(
                                        [loc["lat"], loc["lon"]],
                                        popup=f"<b>{loc['name']}</b>",
                                        icon=folium.Icon(
                                            color="blue", icon="info-sign"
                                        ),
                                    ).add_to(m)

                                st.info(
                                    f"📍 {len(locais)} locais mapeados com sucesso."
                                )

                            st_folium(m, width="100%", height=500, returned_objects=[])
                        else:
                            st.warning(
                                "Não foi possível carregar o mapa para este destino."
                            )
                    except Exception as e:
                        st.error(f"Erro ao processar mapa: {e}")

            # ABA 3: FINOPS
            with tab3:
                st.markdown("### 📊 Análise de Custos e Performance")

                # Preferência: tokens REAIS da execução (S4); heurística só como
                # último recurso (ex.: roteiro servido do cache)
                try:
                    if token_usage is not None:
                        stats = fin_service.estimate_costs_from_usage(
                            prompt_tokens=getattr(token_usage, "prompt_tokens", 0),
                            completion_tokens=getattr(
                                token_usage, "completion_tokens", 0
                            ),
                        )
                        st.caption(
                            f"✅ Tokens reais da execução: "
                            f"{int(stats['total_tokens'])} "
                            "(medidos pelo CrewAI, não estimados)."
                        )
                    else:
                        stats = fin_service.estimate_costs(logs_for_finops)
                        st.caption(
                            "Sem execução de LLM nesta rodada (cache) — "
                            "valores estimados por heurística."
                        )
                except Exception as e:
                    logger.warning(f"Erro no cálculo FinOps: {e}")
                    stats = fin_service.estimate_costs("")

                st.success(
                    f"💡 **Economia:** Com o stack OpenCode Go + OpenRouter, você "
                    f"economizou **${stats['savings']:.4f}** comparado ao GPT-4o."
                )

                st.caption("""
                *Nota: o comparativo usa os preços públicos por 1M de tokens do
                GPT-4o vs. o stack atual. O trace completo (por agente/chamada)
                fica no Langfuse.*
                """)
