# Backend image for the API, the worker and one-shot migrations (single codebase, ADR-001).
FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv==0.12.18

# PostgreSQL 16 client tools for backup/restore (#58). They must match the server's major version, so they come
# from the PostgreSQL project's apt repository rather than the distribution default.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates postgresql-common \
    && /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

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
# Local semantic retrieval is opt-in (ADR-025): build with --build-arg WITH_EMBEDDINGS=1 to add the extra.
ARG WITH_EMBEDDINGS=0
RUN uv sync --frozen --no-dev --all-packages --no-install-workspace $([ "$WITH_EMBEDDINGS" = 1 ] && echo --all-extras)

COPY packages/research-core-contracts packages/research-core-contracts
COPY services/api services/api
COPY services/worker services/worker
RUN uv sync --frozen --no-dev --all-packages $([ "$WITH_EMBEDDINGS" = 1 ] && echo --all-extras)

RUN useradd --system --uid 10001 --home /app app \
    && mkdir -p /data/storage /data/cloud-workspace /data/backups /data/models \
    && chown -R app /data
USER app

ENV STORAGE_ROOT=/data/storage
WORKDIR /app/services/api
EXPOSE 8000
CMD ["uvicorn", "research_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
