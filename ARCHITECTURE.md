### System Topology & Monorepo Layout

The repository uses a Turborepo monorepo architecture with an offline-first containerized local toolchain and distinct production deployment targets: Vercel for the SvelteKit frontend, Koyeb for the Python FastAPI service, and Turso for the distributed edge SQLite database.

```
text-analysis-service/
├── .github/
│   └── workflows/
│       ├── api-ci.yml
│       └── web-ci.yml
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── router.py
│   │   │   │   │   ├── sentiment.py
│   │   │   │   │   ├── readability.py
│   │   │   │   └── history.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── algorithms/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── syllables.py
│   │   │   │   │   ├── readability_indexes.py
│   │   │   │   │   └── sentiment_lexicon.py
│   │   │   │   ├── security.py
│   │   │   │   └── errors.py
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── common.py
│   │   │       ├── sentiment.py
│   │   │       ├── readability.py
│   │   │       └── document.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_sentiment.py
│   │   │   └── test_readability.py
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uvicorn_entry.py
│   └── web/
│       ├── src/
│       │   ├── app.d.ts
│       │   ├── app.html
│       │   ├── app.css
│       │   ├── lib/
│       │   │   ├── api/
│       │   │   │   ├── client.ts
│       │   │   │   └── endpoints.ts
│       │   │   ├── components/
│       │   │   │   ├── layout/
│       │   │   │   │   ├── EditorialHeader.svelte
│       │   │   │   │   └── EditorialFooter.svelte
│       │   │   │   ├── sentiment/
│       │   │   │   │   ├── SentimentBreakdown.svelte
│       │   │   │   │   └── EmotionSpectrum.svelte
│       │   │   │   ├── readability/
│       │   │   │   │   ├── GradeBandCard.svelte
│       │   │   │   │   ├── MetricGrid.svelte
│       │   │   │   │   └── SentenceHighlighter.svelte
│       │   │   │   └── ui/
│       │   │   │       ├── EditorialButton.svelte
│       │   │   │       ├── EditorialTextarea.svelte
│       │   │   │       ├── MetricGauge.svelte
│       │   │   │       ├── PaperCard.svelte
│       │   │   │       └── StatusBadge.svelte
│       │   │   ├── stores/
│       │   │   │   ├── analysisStore.svelte.ts
│       │   │   │   └── historyStore.svelte.ts
│       │   │   └── types/
│       │   │       └── index.ts
│       │   └── routes/
│       │       ├── +layout.svelte
│       │       ├── +layout.ts
│       │       ├── +page.svelte
│       │       ├── history/
│       │       │   ├── +page.svelte
│       │       │   └── +page.ts
│       │       └── [documentId]/
│       │           ├── +page.svelte
│       │           └── +page.ts
│       ├── static/
│       │   └── favicon.png
│       ├── Dockerfile
│       ├── package.json
│       ├── svelte.config.js
│       ├── tsconfig.json
│       └── vite.config.ts
├── docker/
│   ├── docker-compose.yml
│   └── sqld/
│       └── init.sql
├── packages/
│   ├── shared-types/
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── sentiment.ts
│   │   │   ├── readability.ts
│   │   │   └── document.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── ui-tokens/
│   │   ├── src/
│   │   │   └── index.css
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── tsconfig/
│       ├── base.json
│       ├── sveltekit.json
│       └── package.json
├── .editorconfig
├── .gitignore
├── .npmrc
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── README.md
└── turbo.json
```

### Toolchain Specification

- Monorepo Manager: Turborepo (`latest`)
- Package Manager: `pnpm` (`latest`) in strict mode (`shamefully-hoist=false`, `strict-peer-dependencies=true`)
- Web Application Framework: SvelteKit (`latest`) with Svelte 5 Runes (`$state`, `$derived`, `$effect`, `$props`)
- SvelteKit Adapter: `@sveltejs/adapter-vercel` (`latest`) configured for edge/serverless deployment targets
- Build Engine: Vite (`latest`)
- Styling Engine: Tailwind CSS v4 (`latest`) using the native `@theme` CSS layer configuration
- TypeScript: TypeScript (`latest`) with configuration:
  - `strict`: true
  - `noImplicitAny`: true
  - `strictNullChecks`: true
  - `strictFunctionTypes`: true
  - `strictBindCallApply`: true
  - `strictPropertyInitialization`: true
  - `noImplicitThis`: true
  - `alwaysStrict`: true
  - `noUnusedLocals`: true
  - `noUnusedParameters`: true
  - `noImplicitReturns`: true
  - `noFallthroughCasesInSwitch`: true
  - `noUncheckedIndexedAccess`: true
- Backend Application Engine: Python (`latest` 3.12+ runtime)
  - Framework: FastAPI (`latest`)
  - Server Engine: Uvicorn (`latest`) with uvloop
  - Data Validation: Pydantic v2 (`latest`)
- Local Database Engine: `sqld` (`latest`) containerized Turso SQLite protocol emulator for zero-dependency offline local development

### Global Data Layer

1. Database Strategy:
   - Development (Offline): Containerized `sqld` running over WebSocket/HTTP at `http://127.0.0.1:8080` with mock authentication tokens.
   - Production: Turso Managed LibSQL distributed edge cluster.
   - Python Backend Client: `libsql` (`latest`, official Rust-backed Python bindings) connecting via `libsql.connect(url=settings.database_url, auth_token=settings.database_auth_token)` loaded from `apps/api/app/config.py` using `pydantic-settings` (`Settings` model reading environment variables `DATABASE_URL` and `DATABASE_AUTH_TOKEN`).
   - SvelteKit Frontend Client: Stateless direct consumption of the Koyeb FastAPI backend; direct database query capabilities reserved exclusively for backend workers.

2. Frontend Global State Layer:
   - Svelte 5 reactive Runes encapsulating business logic in dedicated `.svelte.ts` modules.
   - Native browser Cache API / IndexedDB fallback for offline caching of analyzed documents.

3. Base API Conventions:
   - Protocol: HTTP/2 REST with full asynchronous pipeline execution (`async def`).
   - JSON Transport Case: Canonical camelCase across wire boundaries. Inbound payloads accept both snake_case and camelCase via `populate_by_name=True`; outbound JSON responses strictly emit camelCase via `to_camel` alias generator.
   - CRUD Operations: Explicit support for `DELETE /api/v1/history/{document_id}` matching allowed CORS verbs.
   - Documentation Endpoints: Automatic OpenAPI 3.1 schemas exposed at `/docs` (Swagger UI) and `/redoc` (ReDoc).
   - Base Route Prefix: `/api/v1`.

### Security, Network & Operational Constraints

1. Authentication & Authorization:
   - API Gatekeeper: Cryptographic API token verification using `X-API-Key` headers for rate limit governance.
   - Token Scopes: Read-only, Analyze, Full-Admin.
   - Fallback: Anonymous tier allows 20 requests per hour tracked by client IP hashing (SHA-256 with rotating salt).

2. Rate Limiting:
   - In-memory sliding-window token bucket implemented via FastAPI middleware with optional Redis bridge.
   - Rate Limit Headers:
     - `X-RateLimit-Limit`
     - `X-RateLimit-Remaining`
     - `X-RateLimit-Reset`

3. Error Boundaries & RFC Compliance:
   - All errors formatted according to RFC 7807 (Problem Details for HTTP APIs).
   - FastAPI global handlers capture `RequestValidationError`, `HTTPException`, and uncaught `Exception`.
   - SvelteKit `+error.svelte` boundaries isolate failure domains to document viewing panes without breaking app shells.

4. Cross-Origin Resource Sharing (CORS):
   - Strict origins allowed: Production Vercel domain, local staging (`http://localhost:5173`), local preview (`http://localhost:4173`).
   - Allowed headers: `Content-Type`, `X-API-Key`, `Authorization`.
   - Allowed methods: `GET`, `POST`, `DELETE`, `OPTIONS`.

5. Content Security Policy (CSP):
   - Strict directives enforcing local scripts, zero remote eval, locked style-src hashes, and restricted frame-ancestors.
