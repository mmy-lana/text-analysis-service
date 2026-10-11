import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.errors import register_exception_handlers
from app.core.ratelimit import GLOBAL_WINDOW_STORE, RateLimitMiddleware
from app.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.batch_semaphore = asyncio.Semaphore(10)
    try:
        await database.connect()
    except OSError:
        # Degrade gracefully when the database is unreachable at boot; the
        # get_database dependency retries lazily on the first request.
        pass
    try:
        yield
    finally:
        await database.disconnect()


app = FastAPI(
    title="Text Sentiment & Readability API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "X-Session-ID", "Authorization"],
)

app.include_router(api_v1_router, prefix="/api/v1")

app.add_middleware(RateLimitMiddleware, store=GLOBAL_WINDOW_STORE)

register_exception_handlers(app)


@app.get("/health", tags=["Operations"])
async def healthcheck() -> dict[str, str | bool]:
    healthy = await database.healthcheck()
    return {"status": "ok" if healthy else "degraded", "database": healthy}
