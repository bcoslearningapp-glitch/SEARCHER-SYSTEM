"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_api import __version__
from research_api.config import get_settings
from research_api.modules.claims_evidence.router import router as claims_router
from research_api.modules.governance_audit.decisions_router import router as decisions_router
from research_api.modules.governance_audit.router import router as audit_router
from research_api.modules.project_workflow.attention import router as attention_router
from research_api.modules.project_workflow.router import router as projects_router
from research_api.modules.sources_library.router import library as sources_router
from research_api.modules.sources_library.router import project_sources as project_sources_router
from research_api.platform import health, system_router
from research_api.platform.errors import install_error_handlers
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
    app.include_router(projects_router)
    app.include_router(decisions_router)
    app.include_router(attention_router)
    app.include_router(claims_router)
    app.include_router(sources_router)
    app.include_router(project_sources_router)
    install_error_handlers(app)
    return app


app = create_app()
