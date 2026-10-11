# The Manuscript Review: Text Sentiment & Readability Service

An offline-first linguistic complexity and emotional valence evaluation service. Combines a SvelteKit editorial broadsheet workbench with a Python FastAPI computational engine and containerized Turso edge SQLite (`sqld`).

---

## Features

- Sentiment Analysis:
  - Polarity compound score (-1.0 to +1.0) and subjectivity ratio.
  - Plutchik eight-vector emotional radar (Joy, Sadness, Anger, Fear, Trust, Surprise, Disgust, Anticipation).
  - Sentence-level decomposition and opposing-valence divergence detection.
- Readability Metrics:
  - Flesch Reading Ease (0-100 scale).
  - Flesch-Kincaid Grade Level, Gunning Fog Index, Coleman-Liau Index, SMOG Index, and Automated Readability Index (ARI).
  - CEFR educational equivalence grading (A1 through C2).
  - Reading velocity (estimated silent reading and speaking durations).
- Sentence Friction Map:
  - Inline sentence highlighter classifying clear prose, dense passages (<50 ease), and overlong sentences (30+ words).
- Archival & Persistence:
  - Atomic multi-table persistence in LibSQL edge SQLite.
  - Multitenant isolation via authenticated `X-API-Key` or anonymous `X-Session-ID` HMAC hashing.
  - Seamless offline mode using client-side IndexedDB caching.
- Integrated Reader's Field Guide:
  - Built-in modal documenting metric formulas, scale interpretation, and editorial standards.

---

## System Architecture & Ports

- Frontend Web Workbench: SvelteKit 5 Runes on `http://localhost:5173` (or auto-assigned `5174`)
- Backend Computational Engine: Python 3.12 FastAPI on `http://localhost:8005` (container port 8000)
- Edge Database: Containerized LibSQL Server (`sqld`) on `http://localhost:8080` (HTTP) and `8081` (gRPC)
- OpenAPI Documentation: Swagger UI at `http://localhost:8005/docs`

---

## Prerequisites

- Node.js >= 22
- pnpm >= 9
- Docker Desktop (daemon must be active)

---

## Quickstart (Offline Local Development)

### 1. Environment Setup

Copy the example environment configuration into the repository root:

```bash
cp .env.example .env
```

Ensure the following default values are present in your `.env`:

```env
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174","http://localhost:4173"]
DATABASE_URL=http://sqld:8080
DATABASE_AUTH_TOKEN=
PUBLIC_API_BASE_URL=http://localhost:8005
```

### 2. Start the Backend & Database (Docker)

Launch the isolated backend stack:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Verify the database and API are healthy:

```bash
curl -i http://localhost:8005/health
```

Expected response:

```json
{"status":"ok","database":true}
```

### 3. Install Dependencies & Launch Frontend

Install monorepo dependencies:

```bash
pnpm install
```

Start the SvelteKit development server:

```bash
pnpm dev
```

Open the URL shown in your terminal (typically `http://localhost:5173` or `http://localhost:5174`) in your browser.

---

## API Endpoints Overview

All backend endpoints are prefixed with `/api/v1`:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sentiment/analyze` | Single-text sentiment, subjectivity, and Plutchik emotion vectors |
| POST | `/api/v1/sentiment/batch` | Bounded concurrent batch sentiment evaluation (up to 50 texts) |
| POST | `/api/v1/readability/analyze` | Single-text readability grading and sentence complexity breakdown |
| POST | `/api/v1/readability/batch` | Bounded concurrent batch readability evaluation (up to 50 texts) |
| POST | `/api/v1/history` | Evaluates and persists a document under caller tenancy |
| GET | `/api/v1/history` | Paginated archive list with keyword search and session isolation |
| GET | `/api/v1/history/{document_id}` | Retrieve a persisted document and its complete evaluation |
| DELETE | `/api/v1/history/{document_id}` | Atomically remove a persisted document and associated evaluations |
| GET | `/health` | Service and database connectivity check |

Interactive OpenAPI documentation and schema inspection are available at:
`http://localhost:8005/docs`

---

## Automated Verification

### Backend Tests (Pytest)

Run unit and integration suites directly inside the running API container:

```bash
docker compose -f docker/docker-compose.yml exec api pytest
```

Or run locally (if a local Python 3.12 virtual environment is configured):

```bash
python3 -m pytest apps/api/tests
```

### End-to-End Headless Chrome Tests (Playwright)

Run the Playwright test suite to verify mobile responsive viewports (360px, 390px, 430px, 768px, 1280px), modal interactions, and offline fallback caching:

```bash
pnpm --filter web exec playwright test
```

---

## Repository Layout

```
text-analysis-service/
├── apps/
│   ├── api/                  # Python FastAPI service
│   │   ├── app/
│   │   │   ├── api/v1/       # Routers: sentiment, readability, history
│   │   │   ├── core/         # Algorithms, security, rate limiting, error handling
│   │   │   ├── models/       # Pydantic schemas (snake_case/camelCase mapped)
│   │   │   ├── database.py   # Asynchronous LibSQL facade
│   │   │   └── main.py       # ASGI entrypoint and lifespan events
│   │   ├── tests/            # Pytest integration suites
│   │   └── Dockerfile
│   └── web/                  # SvelteKit 5 frontend application
│       ├── src/
│       │   ├── lib/          # UI primitives, stores, and API clients
│       │   └── routes/       # Pages: Workbench, Archive, Document View
│       ├── tests/            # Playwright end-to-end browser tests
│       └── Dockerfile
├── docker/
│   ├── docker-compose.yml    # Offline-first orchestration (sqld + api)
│   └── sqld/init.sql         # LibSQL database schema DDL
├── packages/
│   ├── shared-types/         # Shared TypeScript DTO contracts
│   ├── tsconfig/             # Shared TypeScript configurations
│   └── ui-tokens/            # Shared Tailwind v4 tokens
├── package.json              # Monorepo root manifest
├── pnpm-workspace.yaml
└── turbo.json
```

---

## Stopping the Local Stack

To shut down the background containers:

```bash
docker compose -f docker/docker-compose.yml down
```

To purge local database volume data:

```bash
docker compose -f docker/docker-compose.yml down -v
```
