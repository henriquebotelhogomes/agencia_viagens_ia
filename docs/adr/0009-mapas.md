# ADR-0009 — Mapas

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D9

## Contexto e problema

O mapa era gerado com **folium** + **streamlit-folium**: o servidor Python monta
o HTML de um mapa Leaflet e o injeta na página. Isso funciona como demonstração,
mas tem limites claros:

- **Renderização no servidor**: cada interação exige round-trip; sem interação
  fluida (pan, zoom, clique em marcador com painel lateral).
- **Acoplamento**: a UI depende de uma biblioteca Python, impedindo a separação
  entre frontend e backend.
- **Performance**: HTML inteiro do mapa transferido a cada re-render.

## Opções consideradas

### 1. MapLibre GL JS

- ✅ Open-source (fork do Mapbox GL antes da mudança de licença), sem lock-in
- ✅ Renderização WebGL: performático com muitos marcadores
- ✅ Aceita qualquer fonte de tiles (inclusive gratuitas)
- ❌ Exige o frontend JS pronto ([ADR-0005](0005-frontend.md))

### 2. Mapbox GL JS

- ✅ Ecossistema e documentação excelentes
- ❌ Licença proprietária desde a v2; exige token e tem cobrança por load
- ❌ ToS exige exibir atribuição e usar tiles do Mapbox

### 3. Leaflet (client-side)

- ✅ Simples, leve, muito difundido
- ❌ Sem WebGL: degrada com muitos marcadores e camadas
- ❌ Menos recursos modernos (3D, clustering nativo performático)

### 4. Manter folium/streamlit-folium

- ❌ Não resolve nenhuma das limitações; morre junto com o Streamlit

## Decisão

**MapLibre GL JS** no frontend.

O backend passa a entregar apenas **GeoJSON** (`GET /v1/itineraries/{id}/geojson`);
a renderização é 100% client-side. Isso mantém o contrato limpo: o servidor
produz dados, o cliente decide como desenhar.

## Consequências

### Positivas

- Interação fluida: pan, zoom, clustering e popups sem round-trip.
- Contrato de API agnóstico de biblioteca — trocar MapLibre por outra lib não
  afeta o backend.
- `folium` e `streamlit-folium` saem das dependências Python quando o Streamlit
  for aposentado.

### Negativas

- Depende do frontend Next.js estar pronto — até então, o mapa continua em folium.
- Necessário escolher um provedor de tiles (OpenFreeMap, MapTiler free tier ou
  self-host). Decisão adiada para a Fase 2, com atenção ao ToS e a limites de uso.
- Mapas WebGL têm custo de bundle no cliente (~200 KB gzip) — aceitável, mas
  entra no orçamento de performance do Lighthouse.
