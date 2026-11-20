# The frontend image (AD-17), after Next.js's `with-docker` example, on node:24-alpine. The build context is the
# repository root (docker-compose.yml), so the shared `content/` is in reach; only named paths are copied.

FROM node:24-alpine AS deps
WORKDIR /repo/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:24-alpine AS builder
WORKDIR /repo/frontend
COPY --from=deps /repo/frontend/node_modules ./node_modules
COPY frontend/package.json frontend/package-lock.json frontend/next.config.mjs frontend/jsconfig.json ./
COPY frontend/scripts/ ./scripts/
COPY frontend/app/ ./app/
COPY frontend/components/ ./components/
COPY frontend/lib/ ./lib/
COPY frontend/public/ ./public/
# The shared text (`content/`, AD-12) when present; Story 1.3 adds it. run-next.mjs copies it into
# frontend/content before `next build`. The bracket glob matches nothing until then, and the always-present
# package.json keeps the instruction valid.
COPY frontend/package.json conten[t]/ /repo/content/
RUN rm -f /repo/content/package.json && npm run build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /repo/frontend/public ./public
COPY --from=builder --chown=nextjs:nodejs /repo/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/frontend/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
