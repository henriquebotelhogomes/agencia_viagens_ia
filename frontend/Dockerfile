# syntax=docker/dockerfile:1
# Imagem do frontend Next.js (ADR-0005).
#
#   deps    -> dependências, camada cacheável
#   builder -> build de produção
#   runtime -> saída standalone, non-root

############################################
# Estágio 1: deps
############################################
FROM node:22-alpine AS deps

WORKDIR /app

# Só os manifestos: a camada de dependências sobrevive a mudanças de código.
# `npm ci` quando o lock existe (build reproduzível); `npm install` como
# fallback quando o lock resolvido no host omite binários de outra plataforma
# — o SWC do Next tem pacotes específicos de OS/arch.
COPY package.json package-lock.json* ./
RUN npm ci --include=optional || npm install --no-audit --no-fund

############################################
# Estágio 2: builder
############################################
FROM node:22-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules node_modules
COPY . .

# A URL da API entra no bundle em tempo de build (`NEXT_PUBLIC_`), então precisa
# ser conhecida aqui — não em runtime.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

############################################
# Estágio 3: runtime
############################################
FROM node:22-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Usuário sem privilégios (CIS Docker Benchmark)
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# `standalone` embute apenas o necessário para rodar: imagem menor e sem
# node_modules completo.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
