![Tests](https://github.com/henriquebotelhogomes/agencia_viagens_ia/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Linter: Ruff](https://img.shields.io/badge/linter-ruff-red.svg)
![Types: Mypy](https://img.shields.io/badge/types-mypy%20(strict)-green.svg)

# ✈️ Agência de Viagens Multiagentes com IA (Agentic RAG)

Um sistema de planejamento de viagens totalmente autônomo, construído com arquitetura de múltiplos agentes de Inteligência Artificial. O projeto orquestra especialistas virtuais para pesquisar, calcular custos, gerar roteiros e mapear atrações geograficamente em tempo real.

## 🎯 Destaques Técnicos (Para Recrutadores e Tech Leads)

Este projeto foi desenvolvido com foco em Engenharia de IA e Maturidade de Software, indo muito além de chamadas simples de API:

* **Orquestração Multiagente**: Utilização do ```CrewAI``` para dividir tarefas complexas entre 3 agentes especializados (Pesquisador, Analista Financeiro e Redator), evitando alucinações e garantindo precisão.

* **Extração Pós-Processamento (NLP)**: Uso do ```LangChain``` para extrair entidades geográficas (nomes de locais) de textos não-estruturados (Markdown) e convertê-los em JSON validado para plotagem.

* **Integração Geoespacial Automática**: Conversão de endereços em coordenadas (```Geopy```) e renderização de mapas interativos (```Folium```) em tempo real.

* **Auditoria de Custos (FinOps)**: Implementação de um painel nativo que calcula o consumo exato de tokens (Input/Output) e demonstra a viabilidade económica da aplicação, comparando os custos do modelo Open-Source (Llama 3 via Groq) com modelos proprietários.

* **Arquitetura Limpa**: Separação de responsabilidades clara entre Interface (```app.py```), Configuração de Agentes (```agents.py```) e Definição de Tarefas (```tasks.py```).

## ✨ Funcionalidades

1. **Roteiro Personalizado**: Geração de um itinerário dia a dia com base no destino, origem, duração e interesses específicos do usuário.

2. **Pesquisa em Tempo Real**: Agentes conectados à internet via ```Serper API``` para buscar preços e atrações atualizadas.

3. **Mapa Interativo**: Mapeamento automático (Pins) de todos os hotéis, restaurantes e pontos turísticos sugeridos no roteiro.

4. **Exportação**: Opção de download do roteiro em formato Markdown (```.md```).

5. **Logs em Tempo Real**: Observabilidade total do "raciocínio" da IA exibido diretamente na interface (Streaming do Console).

## 🏗️ Como a Arquitetura Funciona

O projeto utiliza um processo Sequencial de agentes:

1. 🕵️‍♂️ **Guia Local (Pesquisador)**: Focado em buscar atrações locais e restaurantes autênticos que fujam de armadilhas para turistas.

2. 📊 **Analista de Custos (Logística)**: Recolhe estimativas de voos e hotéis para garantir que o roteiro é financeiramente realista.

3. ✍️ **Arquiteto de Roteiros (Editor Final)**: Sintetiza as pesquisas brutas num documento Markdown elegante, conciso e bem formatado.

## 🛠️ Tecnologias Utilizadas

* **Frontend**:  [Streamlit](https://streamlit.io/) + Streamlit-Folium

* **Framework de Agentes**: [CrewAI](https://www.crewai.com/)

* **LLM (Raciocínio)**: Llama 3.3 70B (Via [Groq API](https://groq.com/) para inferência ultra-rápida)

* **LLM (Extração de Dados)**: Llama 3.1 8B + [LangChain](https://www.langchain.com/)

* **Ferramenta de Busca**: Google Search (Via [Serper.dev](https://serper.dev/))

* **Geolocalização**: Geopy (Nominatim) + [Folium](https://python-visualization.github.io/folium/)

## 🚀 Como Executar o Projeto Localmente

**Pré-requisitos**

* Python 3.10 ou superior.

* Chave de API do **Groq** (Gratuita).

* Chave de API do **Serper.dev** (Gratuita para os primeiros 2500 requests).

## Instalação

1. Clone este repositório:
```
git clone [https://github.com/SEU_USUARIO/agencia-viagens-ia.git](https://github.com/SEU_USUARIO/agencia-viagens-ia.git)
cd agencia-viagens-ia
```

2. Crie e ative um ambiente virtual:
```
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

3. Instale as dependências necessárias:
```
pip install -r requirements.txt
```

4. Configure as Variáveis de Ambiente:
Crie um arquivo chamado .env na raiz do projeto e adicione as suas chaves:
```
GROQ_API_KEY=sua_chave_groq_aqui
SERPER_API_KEY=sua_chave_serper_aqui
```

5. Execute a aplicação:
```
streamlit run app.py
```

O sistema estará disponível no seu navegador em ```http://localhost:8501```.