# Multi-stage production image for the SvelteKit web application.

FROM node:22-slim AS builder

ENV CI=true
WORKDIR /build

RUN corepack enable

COPY package.json ./
COPY pnpm-lock.yaml ./pnpm-lock.yaml
RUN pnpm fetch

COPY . .
RUN pnpm install --frozen-lockfile --offline && pnpm build

FROM node:22-slim AS runtime

ENV NODE_ENV=production \
    PORT=3000

RUN corepack enable
RUN groupadd --system app && useradd --system --gid app app
WORKDIR /srv

# adapter-vercel targets Vercel serverless; the container runtime serves the
# built application through Vite's preview server for parity.
COPY --from=builder /build /srv

USER app

EXPOSE 3000
CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "3000"]
