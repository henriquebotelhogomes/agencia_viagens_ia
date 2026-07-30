# 01 — Visão de Produto

## 1. Resumo executivo

**Voyager AI** é uma plataforma SaaS que transforma uma intenção de viagem
("5 dias em Lisboa com foco em gastronomia e história, saindo de São Paulo")
em um **roteiro acionável, confiável e auditável**: cronograma dia a dia, estimativa
de custos realista, mapa interativo e fontes verificáveis — gerado por uma equipe de
**agentes de IA especializados** que pesquisam dados reais em tempo real.

O diferencial não é "mais uma IA de viagem". É **confiabilidade e transparência**:
cada recomendação é rastreável até sua fonte, cada execução tem custo e latência
medidos, e o sistema degrada com elegância quando um provedor falha.

## 2. O problema

Planejar viagem é um processo **fragmentado e de baixa confiança**:

- O usuário pula entre dezenas de abas (voos, hotéis, mapas, blogs).
- IAs genéricas **alucinam** horários, preços e locais já fechados.
- Não há **rastreabilidade**: o usuário não sabe de onde veio cada sugestão.
- Roteiros prontos da internet são genéricos e desatualizados.

Para profissionais (agentes de viagem PME), o custo é ainda maior: montar um roteiro
personalizado consome horas de trabalho manual repetitivo.

## 3. Proposta de valor

> **"Do desejo ao roteiro confiável em minutos — com fontes, custos e mapa, não achismos."**

| Pilar | Como entregamos |
|-------|-----------------|
| **Confiável** | Agentes pesquisam dados reais (busca web), com citação de fontes e validação geográfica. |
| **Transparente** | Cada execução expõe raciocínio, fontes, custo (FinOps) e tempo. |
| **Rápido & barato** | Cache semântico + LLMs de baixo custo (Groq) reduzem latência e custo por roteiro. |
| **Resiliente** | Cadeia de fallback entre provedores evita indisponibilidade. |
| **Acionável** | Saída estruturada: cronograma, tabela de custos, mapa, export (PDF/Markdown/Calendar). |

## 4. Diferenciação (por que ganhamos)

1. **Multiagente especializado** em vez de um único prompt gigante → menos alucinação,
   melhor separação de responsabilidades.
2. **Observabilidade de IA de primeira classe** (tracing por agente, custo por token,
   avaliação de qualidade) — raro em produtos concorrentes e **altamente valorizado por
   recrutadores**.
3. **Rastreabilidade fonte-a-recomendação**: cada item do roteiro carrega proveniência.
4. **Arquitetura desacoplada e assíncrona** que suporta roteiros longos com streaming
   de progresso, não um "spinner que trava".
5. **Marca branca / API-first**: permite que agências de viagem incorporem o motor.

## 5. Público-alvo e personas

### Segmentos
- **B2C** — viajantes independentes (foco inicial / aquisição orgânica).
- **B2B (PME)** — agências de viagem boutique e criadores de conteúdo de viagem.
- **B2B2C / API** — plataformas que embutem planejamento via API.

### Personas

**Bruna — Viajante independente (B2C)**
- 29 anos, planeja 2–4 viagens/ano, valoriza tempo e experiências autênticas.
- *Dor:* horas pesquisando, medo de roteiro inviável.
- *Ganho:* roteiro pronto, confiável, exportável para o calendário.

**Carlos — Agente de viagens (B2B, PME)**
- Dono de agência boutique, monta roteiros sob medida manualmente.
- *Dor:* baixa produtividade, retrabalho.
- *Ganho:* gera rascunhos personalizados em minutos, com sua marca.

**Marina — Recrutadora/Eng. Manager (avaliadora do portfólio)**
- *Dor:* portfólios que são só "wrappers de API".
- *Ganho:* evidência clara de arquitetura, operação e cuidado de produto.

## 6. Jobs to be Done (JTBD)

- "Quando eu **decido viajar**, quero **um roteiro viável e personalizado** para
  **não perder horas pesquisando e não ser surpreendido na viagem**."
- "Quando eu **atendo um cliente**, quero **gerar um rascunho profissional rápido**
  para **focar no relacionamento, não na digitação**."

## 7. Métricas de sucesso (North Star + suporte)

- **North Star:** *Roteiros úteis gerados por semana* (com sinal de qualidade — ver abaixo).
- **Ativação:** % de usuários que geram ≥1 roteiro e exportam/salvam.
- **Qualidade:** taxa de aprovação do roteiro (👍/👎), taxa de alucinação detectada.
- **Eficiência (FinOps):** custo médio de LLM por roteiro; % servido por cache.
- **Retenção:** roteiros por usuário/mês; W4 retention.
- **Confiabilidade:** disponibilidade, p95 de latência, taxa de fallback acionado.

## 8. Modelo de monetização

| Plano | Público | Inclui |
|-------|---------|--------|
| **Free** | B2C aquisição | N roteiros/mês, modelos rápidos, export Markdown. |
| **Pro** | B2C/power user | Roteiros ilimitados (fair-use), export PDF/Calendar, modelos premium, histórico. |
| **Business** | Agências (PME) | Marca branca, multiusuário, workspaces, prioridade de fila. |
| **API / Usage-based** | B2B2C | Cobrança por roteiro/token + SLA. |

Alavancas de margem: **cache semântico**, **roteamento de modelos** (modelo barato por
padrão, premium sob demanda) e **limites por plano** — tudo mensurável via FinOps.

## 9. Princípios de produto

1. **Confiança acima de tudo** — preferimos dizer "não sei" a alucinar.
2. **Transparência radical** — mostre fontes, custo e raciocínio.
3. **Degradação graciosa** — nunca um erro cru na cara do usuário.
4. **Velocidade percebida** — streaming de progresso, não telas congeladas.
5. **Privacidade por padrão** — dados de viagem são sensíveis.

## 10. Não-objetivos (por ora)

- Não somos uma **OTA** (não vendemos/reservamos voos e hotéis na v1).
- Não competimos em **inventário de preços em tempo real** com GDS na v1
  (estimativas realistas, com integração futura).
- Não fazemos rede social de viagens.

