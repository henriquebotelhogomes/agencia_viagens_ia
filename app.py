import io

import folium
import streamlit as st
from streamlit_folium import st_folium

# Importações do Projeto
from src.crew_builder import CrewBuilder
from src.services.finance_service import FinanceService
from src.services.geocoding_service import GeocodingService
from src.utils.logger import add_streamlit_sink, setup_logger

# Configuração do Logger Centralizado
logger = setup_logger()
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
    return GeocodingService()


@st.cache_resource
def get_finance_service():
    return FinanceService()


geo_service = get_geocoding_service()
fin_service = get_finance_service()


# Funções Auxiliares de Cache
@st.cache_data
def get_itinerary_map_data(itinerary_str: str):
    return geo_service.process_itinerary_locations(itinerary_str)


# Interface Principal
st.title("✈️ Agência de Viagens Inteligente")
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

    submitted = st.form_submit_button(
        "🚀 Planejar Roteiro Profissional", use_container_width=True
    )

if submitted:
    if not destino or not origem:
        st.warning("Por favor, preencha a Origem e o Destino para continuar.")
    else:
        st.divider()
        st.subheader("🛠️ Orquestração de Agentes em Tempo Real")

        # Container para Logs Vivos
        log_expander = st.expander("Ver 'Raciocínio' dos Agentes (Live)", expanded=True)
        log_placeholder = log_expander.empty()

        # Captura de logs via Loguru Sink (Streamlit + Buffer para FinOps)
        import io

        log_buffer = io.StringIO()

        log_sink_id = add_streamlit_sink(log_placeholder)
        buffer_sink_id = logger.add(log_buffer, format="{message}", level="INFO")

        logger.info(f"Iniciando planejamento para {destino}...")

        final_itinerary = None
        try:
            with st.spinner(f"A equipe está mapeando {destino}..."):
                trip_crew = CrewBuilder(
                    destino=destino, dias=dias, origem=origem, interesses=interesses
                )
                final_itinerary = trip_crew.run()
        except Exception as e:
            logger.error(f"Erro na orquestração: {str(e)}")
            st.error(f"Erro na orquestração: {str(e)}")
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

                            # Processa locais do roteiro (com cache para não repetir chamadas caras)
                            locais = get_itinerary_map_data(roteiro_str)

                            if locais:
                                for loc in locais:
                                    folium.Marker(
                                        [loc.lat, loc.lon],
                                        popup=f"<b>{loc.name}</b>",
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

                # Agora as estatísticas podem vir do logger ou continuar via logs textuais refinados
                # Como a decisão foi manter agregado, vamos manter a lógica, mas agora capturando de forma mais limpa
                current_logs = (
                    log_placeholder.get_label()
                    if hasattr(log_placeholder, "get_label")
                    else "Logs indisponíveis"
                )
                stats = fin_service.estimate_costs(current_logs)
                # NOTA: Como o log_placeholder sumiu ao fim, precisamos garantir o acesso ao texto.
                # Vamos ajustar a lógica para o FinanceService processar os logs do arquivo se necessário.

                # Agora usamos o buffer capturado especificamente para esta rodada
                try:
                    stats = fin_service.estimate_costs(logs_for_finops)
                except Exception as e:
                    logger.warning(f"Erro no cálculo FinOps: {e}")
                    stats = fin_service.estimate_costs("")

                st.success(
                    f"💡 **Economia Realizada:** Ao usar Llama 3 via Groq, você economizou "
                    f"**${stats['savings']:.4f}** comparado ao GPT-4o."
                )

                st.caption("""
                *Nota: Os custos são baseados em heurísticas de volume de tokens.
                Os valores do Groq refletem os preços atuais por 1M de tokens.*
                """)
