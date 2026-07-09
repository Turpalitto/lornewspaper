# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS deps

WORKDIR /app
COPY --link package.json package-lock.json ./
RUN npm ci --only=production && npm cache clean --force


FROM node:22-alpine AS builder

WORKDIR /app
COPY --link package.json package-lock.json ./
RUN npm ci
COPY --link tsconfig.json next.config.ts postcss.config.mjs eslint.config.mjs ./
COPY --link lib/ ./lib/
COPY --link components/ ./components/
COPY --link hooks/ ./hooks/
COPY --link public/ ./public/
COPY --link app/ ./app/

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build


FROM node:22-alpine AS runner

RUN addgroup -S app && adduser -S -G app app

WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder --chown=app:app /app/.next/standalone .
COPY --from=builder --chown=app:app /app/.next/static ./.next/static

USER app

EXPOSE 3000

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
