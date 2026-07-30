# ADR-0004 — Autenticação

- **Status**: Aceita
- **Data**: 2026-07-29
- **Contexto do PRD**: D4

## Contexto e problema

A demo é pública e cada execução consome tokens de LLM pagos. Sem controle,
qualquer visitante (ou bot) pode gerar custo ilimitado. Autenticação resolveria,
mas custa semanas de trabalho e não demonstra nada tecnicamente interessante que
o resto do projeto já não demonstre.

## Opções consideradas

### 1. Adiar autenticação (rate limiting por IP)

- ✅ MVP público sem barreira de entrada — melhor para demonstração
- ✅ Zero trabalho de auth; foco no que diferencia o projeto
- ❌ Rate limit por IP é contornável (VPN, IPv6 rotativo)
- ❌ Sem histórico por usuário

### 2. Clerk (auth gerenciada)

- ✅ Login Google/e-mail em horas; free tier generoso
- ❌ Lock-in e custo ao escalar
- ❌ Adiciona fricção: o recrutador precisaria criar conta para ver a demo

### 3. Auth.js v5 + JWT próprio

- ✅ Controle total, zero custo, padrão de mercado
- ❌ 1-2 semanas de trabalho + superfície de segurança para manter
- ❌ Mesma fricção de cadastro da opção 2

## Decisão

**Adiar autenticação.** O MVP é público, com estas mitigações obrigatórias:

| Mitigação | Estado |
| --------- | ------ |
| Rate limiting por IP (Redis) | ⏳ Fase 1 |
| Teto diário de custo de LLM | ⏳ Fase 1 |
| Kill switch para desabilitar geração | ⏳ Fase 1 |
| Cache de roteiros (reduz execuções) | ✅ ativo |
| Tiers baratos como default | ✅ ativo |

A variável `RATE_LIMIT_EXECUTIONS_PER_HOUR` já existe na configuração,
aguardando a implementação da API.

## Consequências

### Positivas

- Demo acessível em um clique — decisivo para quem avalia o projeto.
- Nenhum dado pessoal identificado é armazenado, o que simplifica LGPD/GDPR
  substancialmente.
- Semanas de trabalho realocadas para observabilidade, testes e arquitetura.

### Negativas

- **Risco de abuso residual**: rate limit por IP é contornável. O teto diário de
  custo é a proteção real — sem ele, a exposição é financeira.
- Sem histórico por usuário: cada visita começa do zero.
- Quando (e se) auth entrar, será retrofit. O impacto é contido porque a
  arquitetura já é desacoplada, mas o modelo de dados precisará de `user_id`.

!!! danger "Dependência crítica"
    Enquanto o teto diário de custo não estiver implementado, **não** expor a
    demo publicamente sem monitoramento ativo do consumo.
