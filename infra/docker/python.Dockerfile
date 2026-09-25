# Backend image for the API, the worker and one-shot migrations (single codebase, ADR-001).
FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv==0.12.18

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependency layer: only lockfile and manifests, so code edits do not bust the cache.
COPY pyproject.toml uv.lock .python-version ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/worker/pyproject.toml services/worker/pyproject.toml
RUN uv sync --frozen --no-dev --all-packages --no-install-workspace

COPY packages/research-core-contracts packages/research-core-contracts
COPY services/api services/api
COPY services/worker services/worker
RUN uv sync --frozen --no-dev --all-packages

RUN useradd --system --uid 10001 --home /app app \
    && mkdir -p /data/storage /data/cloud-workspace \
    && chown -R app /data
USER app

ENV STORAGE_ROOT=/data/storage
WORKDIR /app/services/api
EXPOSE 8000
CMD ["uvicorn", "research_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
