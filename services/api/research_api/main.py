"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_api import __version__
from research_api.config import get_settings
from research_api.modules.governance_audit.router import router as audit_router
from research_api.platform import health, system_router
from research_api.platform.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Product B — Integrated AI Research System", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(system_router.router)
    app.include_router(audit_router)
    return app


app = create_app()
