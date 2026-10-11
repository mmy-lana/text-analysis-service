# Multi-stage production image for the FastAPI text analysis service.

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install \
    fastapi uvicorn[standard] pydantic pydantic-settings libsql-client

FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN groupadd --system app && useradd --system --gid app app
WORKDIR /srv

COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY uvicorn_entry.py ./

# Guarantee world-readable application code regardless of build-host umask.
RUN chmod -R a+rX /srv

USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/docs')" || exit 1

CMD ["python", "-m", "uvicorn", "uvicorn_entry:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
