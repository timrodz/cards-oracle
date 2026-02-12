# ──────────────────────────────────────────────
# Stage 1: Install dependencies with bun
# ──────────────────────────────────────────────
FROM oven/bun:1 AS deps

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# ──────────────────────────────────────────────
# Stage 2: Build the Next.js application
# ──────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# ──────────────────────────────────────────────
# Stage 3: Slim production runtime
# ──────────────────────────────────────────────
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE ${PORT}

CMD ["node", "server.js"]
