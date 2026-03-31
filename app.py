import streamlit as st
import sys
import io
import folium
from streamlit_folium import st_folium

# Importações do Projeto
from src.config import settings
from src.crew_builder import CrewBuilder
from src.services.geocoding_service import GeocodingService
from src.services.finance_service import FinanceService

# Configuração da Página
st.set_page_config(
    page_title="Agência de Viagens IA", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="collapsed"
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
        origem = st.text_input("📍 Local de Origem", placeholder="Ex: São Paulo, Brasil")
        destino = st.text_input("🌍 Destino", placeholder="Ex: Paris, França")
    with col2:
        dias = st.number_input("📅 Duração (Dias)", min_value=1, max_value=30, value=5)
        interesses = st.text_input("🎭 Interesses", placeholder="Ex: Museus, gastronomia, parques...")

    submitted = st.form_submit_button("🚀 Planejar Roteiro Profissional", use_container_width=True)

if submitted:
    if not destino or not origem:
        st.warning("Por favor, preencha a Origem e o Destino para continuar.")
    else:
        st.divider()
        st.subheader("🛠️ Orquestração de Agentes em Tempo Real")

        # Container para Logs Vivos
        log_expander = st.expander("Ver 'Raciocínio' dos Agentes (Live)", expanded=True)
        log_placeholder = log_expander.empty()

        # Captura de logs para exibição em tempo real
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        final_itinerary = None
        try:
            with st.spinner(f"A equipe está mapeando {destino}..."):
                trip_crew = CrewBuilder(
                    destino=destino, 
                    dias=dias, 
                    origem=origem, 
                    interesses=interesses
                )
                final_itinerary = trip_crew.run()
        except Exception as e:
            st.error(f"Erro na orquestração: {str(e)}")
        finally:
            sys.stdout = old_stdout
            logs = mystdout.getvalue()
            if logs:
                log_placeholder.code(logs[-5000:], language="text")

        if final_itinerary:
            st.success("Roteiro Finalizado! ✨")
            roteiro_str = str(final_itinerary)

            tab1, tab2, tab3 = st.tabs([
                "🗺️ Seu Roteiro", 
                "📍 Mapa de Atrações", 
                "💰 Auditoria FinOps"
            ])

            # ABA 1: ROTEIRO
            with tab1:
                st.markdown(roteiro_str)
                st.download_button(
                    "📥 Exportar para Markdown", 
                    data=roteiro_str,
                    file_name=f"Roteiro_{destino}.md", 
                    mime="text/markdown", 
                    use_container_width=True
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
                                icon=folium.Icon(color="red", icon="star")
                            ).add_to(m)

                            # Processa locais do roteiro (com cache para não repetir chamadas caras)
                            locais = get_itinerary_map_data(roteiro_str)
                            
                            if locais:
                                for loc in locais:
                                    folium.Marker(
                                        [loc.lat, loc.lon],
                                        popup=f"<b>{loc.name}</b>",
                                        icon=folium.Icon(color="blue", icon="info-sign")
                                    ).add_to(m)
                                
                                st.info(f"📍 {len(locais)} locais mapeados com sucesso.")
                            
                            st_folium(m, width="100%", height=500, returned_objects=[])
                        else:
                            st.warning("Não foi possível carregar o mapa para este destino.")
                    except Exception as e:
                        st.error(f"Erro ao processar mapa: {e}")

            # ABA 3: FINOPS
            with tab3:
                st.markdown("### 📊 Análise de Custos e Performance")
                
                stats = fin_service.estimate_costs(logs)
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Tokens Estimados", f"{int(stats['total_tokens']):,}")
                col_b.metric("Custo no Groq", f"${stats['custo_groq']:.4f}")
                col_c.metric("Custo no GPT-4o", f"${stats['custo_gpt4o']:.4f}")
                
                st.success(
                    f"💡 **Economia Realizada:** Ao usar Llama 3 via Groq, você economizou "
                    f"**${stats['savings']:.4f}** comparado ao GPT-4o."
                )
                
                st.caption("""
                *Nota: Os custos são baseados em heurísticas de volume de tokens. 
                Os valores do Groq refletem os preços atuais por 1M de tokens.*
                """)