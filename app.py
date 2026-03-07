import streamlit as st
import os
import sys
import io
import json
import re
import time
from dotenv import load_dotenv

# Bibliotecas para o Mapa Interativo
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# LangChain para a Extração Pós-Processamento
from langchain_groq import ChatGroq

# Importa o orquestrador que liga os agentes e as tarefas
from src.crew_builder import TravelCrew

# Carrega as variáveis de ambiente
load_dotenv()

st.set_page_config(page_title="Agência de Viagens IA", page_icon="✈️", layout="wide")

if not os.getenv("GROQ_API_KEY") or not os.getenv("SERPER_API_KEY"):
    st.error("⚠️ Falta configurar as variáveis de ambiente. Verifique o seu ficheiro `.env`.")
    st.stop()

st.title("✈️ Roteiro de Viagens com Multiagentes (CrewAI)")
st.markdown(
    "Uma equipa de Inteligência Artificial irá pesquisar na web, calcular custos e gerar um roteiro de viagem personalizado com mapeamento automático.")

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        origem = st.text_input("📍 Local de Origem", placeholder="Ex: Lisboa, Portugal")
        destino = st.text_input("🌍 Destino", placeholder="Ex: Quioto, Japão")
    with col2:
        dias = st.number_input("📅 Duração (Dias)", min_value=1, max_value=30, value=5)
        interesses = st.text_input("🎭 Interesses", placeholder="Ex: Culinária local, templos, arte...")

    submitted = st.form_submit_button("🚀 Iniciar Planeamento", use_container_width=True)

if submitted:
    if not destino or not origem:
        st.warning("Por favor, preencha pelo menos a Origem e o Destino.")
    else:
        st.divider()
        st.subheader("🛠️ Os Agentes estão a trabalhar...")

        log_expander = st.expander("Ver Pensamento dos Agentes (Live Logs)", expanded=True)
        log_placeholder = log_expander.empty()

        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        final_itinerary = None

        try:
            with st.spinner("A equipa de IA está a pesquisar voos, atrações e preços..."):
                trip_crew = TravelCrew(destino=destino, dias=dias, origem=origem, interesses=interesses)
                final_itinerary = trip_crew.run()

        except Exception as e:
            st.error(f"Ocorreu um erro durante a orquestração: {e}")
        finally:
            sys.stdout = old_stdout
            logs = mystdout.getvalue()
            if logs:
                log_placeholder.code(logs[-4000:] + "\n\n[... Fim dos Logs Processados ...]", language="text")

        if final_itinerary:
            st.success("Roteiro Finalizado com Sucesso! 🎉")
            roteiro_str = str(final_itinerary)

            tab1, tab2, tab3 = st.tabs(["🗺️ O Seu Roteiro", "📍 Mapa Interativo", "💰 Painel FinOps (Custos)"])

            # ABA 1: ROTEIRO
            with tab1:
                st.markdown(roteiro_str)
                st.download_button("📥 Descarregar Roteiro (Markdown)", data=roteiro_str,
                                   file_name=f"Roteiro_{destino}.md", mime="text/markdown", use_container_width=True)

            # ABA 2: MAPA INTERATIVO (COM MÚLTIPLOS PINOS)
            with tab2:
                st.markdown(f"### Explorar as sugestões em: {destino}")

                with st.spinner("A extrair locais do roteiro e a gerar o mapa (isto pode demorar alguns segundos)..."):
                    try:
                        geolocator = Nominatim(user_agent="agencia_viagens_ia_portfolio")
                        location = geolocator.geocode(destino)

                        if location:
                            # 1. Cria o mapa centrado no destino
                            m = folium.Map(location=[location.latitude, location.longitude], zoom_start=12)

                            # Adiciona o Ponto Central (Destino)
                            folium.Marker(
                                [location.latitude, location.longitude],
                                popup=f"<b>Centro de {destino}</b>",
                                icon=folium.Icon(color="red", icon="star")
                            ).add_to(m)

                            # 2. Usa um LLM rápido para extrair a lista de locais do texto do Roteiro
                            llm_extractor = ChatGroq(
                                api_key=os.getenv("GROQ_API_KEY"),
                                model="llama-3.1-8b-instant",
                                temperature=0
                            )

                            prompt_extracao = f"""
                            Você é um assistente de extração de dados. Analise o roteiro abaixo e extraia os nomes das principais atrações, restaurantes ou hotéis sugeridos.
                            Retorne APENAS um array JSON válido com no máximo 6 locais.
                            Exemplo de formato: ["Museu do Louvre, Paris", "Torre Eiffel, Paris"]

                            Roteiro:
                            {roteiro_str}
                            """

                            resposta = llm_extractor.invoke(prompt_extracao)

                            # 3. Faz o Parsing do JSON devolvido pelo LLM
                            locais_extraidos = []
                            try:
                                match = re.search(r'\[.*?\]', resposta.content, re.DOTALL)
                                if match:
                                    locais_extraidos = json.loads(match.group(0))
                            except json.JSONDecodeError:
                                st.warning("Não foi possível processar a lista de locais automaticamente.")

                            # 4. Adiciona cada local ao Mapa
                            if locais_extraidos:
                                st.info(
                                    f"📍 Foram identificados {len(locais_extraidos)} locais para visitar. A geolocalizar...")

                                # Barra de progresso opcional para melhor UX
                                progresso = st.progress(0)
                                for i, local in enumerate(locais_extraidos):
                                    try:
                                        # Pausa obrigatória de 1 segundo (Regra da API gratuita Nominatim/OpenStreetMap)
                                        time.sleep(1.1)

                                        loc_coords = geolocator.geocode(local)
                                        if loc_coords:
                                            folium.Marker(
                                                [loc_coords.latitude, loc_coords.longitude],
                                                popup=f"<b>{local}</b>",
                                                icon=folium.Icon(color="blue", icon="info-sign")
                                            ).add_to(m)
                                    except Exception:
                                        pass  # Ignora se não encontrar as coordenadas daquele local específico

                                    # Atualiza barra de progresso
                                    progresso.progress((i + 1) / len(locais_extraidos))

                                progresso.empty()  # Remove a barra ao terminar

                            # Renderiza o mapa completo
                            st_folium(m, width=800, height=450, returned_objects=[])
                        else:
                            st.info("📍 Mapa indisponível: Não foi possível localizar as coordenadas iniciais.")
                    except Exception as e:
                        st.error(f"Erro ao carregar o serviço de mapas: {e}")

            # ABA 3: FINOPS
            with tab3:
                st.markdown("### Auditoria de Consumo de Tokens (FinOps)")
                try:
                    total_tokens = len(str(logs)) // 3 + 2500
                    prompt_tokens = int(total_tokens * 0.8)
                    completion_tokens = int(total_tokens * 0.2)

                    custo_gpt4 = (prompt_tokens / 1_000_000 * 5.00) + (completion_tokens / 1_000_000 * 15.00)
                    custo_groq = (prompt_tokens / 1_000_000 * 0.59) + (completion_tokens / 1_000_000 * 0.79)

                    colA, colB, colC = st.columns(3)
                    colA.metric("Tokens Processados", f"{total_tokens:,}")
                    colB.metric("Custo no Groq", f"${custo_groq:.4f}")
                    colC.metric("Custo no GPT-4o", f"${custo_gpt4:.4f}")
                    st.success(
                        f"💸 **Poupança:** Ao optar pelo modelo open-source via Groq, poupou **${(custo_gpt4 - custo_groq):.4f}** nesta pesquisa.")
                except:
                    st.info("Estatísticas não disponíveis para esta execução.")