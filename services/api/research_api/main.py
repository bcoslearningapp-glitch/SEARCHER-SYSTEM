"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_api import __version__
from research_api.config import get_settings
from research_api.modules.ai_gateway.router import router as ai_router
from research_api.modules.ai_reliability.router import router as reliability_router
from research_api.modules.ai_tools.router import router as tools_router
from research_api.modules.claims_evidence.router import lineage_router
from research_api.modules.claims_evidence.router import router as claims_router
from research_api.modules.cloud_workspace.router import router as workspace_router
from research_api.modules.design_experiments.experiment_router import router as experiments_router
from research_api.modules.design_experiments.router import router as design_router
from research_api.modules.governance_audit.decisions_router import router as decisions_router
from research_api.modules.governance_audit.router import router as audit_router
from research_api.modules.hypothesis_lab.router import router as hypotheses_router
from research_api.modules.knowledge_memory.router import router as knowledge_router
from research_api.modules.knowledge_memory.terminology_router import router as terminology_router
from research_api.modules.operational_constraints.router import router as constraints_router
from research_api.modules.outputs_integrity.router import router as outputs_router
from research_api.modules.portability.router import router as portability_router
from research_api.modules.project_workflow.attention import router as attention_router
from research_api.modules.project_workflow.router import router as projects_router
from research_api.modules.reference_governance.router import library as reference_router
from research_api.modules.reference_governance.router import reviews as reference_reviews_router
from research_api.modules.research_orchestrator.router import router as orchestrator_router
from research_api.modules.research_planning.router import router as planning_router
from research_api.modules.sources_library.router import library as sources_router
from research_api.modules.sources_library.router import project_sources as project_sources_router
from research_api.platform import health, system_router
from research_api.platform.errors import install_error_handlers
from research_api.platform.logging import configure_logging
from research_api.platform.security import BoundaryMiddleware


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
    app.add_middleware(BoundaryMiddleware, allowed_hosts=settings.allowed_hosts, allowed_origins=settings.cors_origins)
    app.include_router(health.router)
    app.include_router(system_router.router)
    app.include_router(audit_router)
    app.include_router(projects_router)
    app.include_router(decisions_router)
    app.include_router(attention_router)
    app.include_router(claims_router)
    app.include_router(lineage_router)
    app.include_router(hypotheses_router)
    app.include_router(design_router)
    app.include_router(experiments_router)
    app.include_router(knowledge_router)
    app.include_router(terminology_router)
    app.include_router(outputs_router)
    app.include_router(portability_router)
    app.include_router(workspace_router)
    app.include_router(reference_router)
    app.include_router(reference_reviews_router)
    app.include_router(constraints_router)
    app.include_router(sources_router)
    app.include_router(project_sources_router)
    app.include_router(ai_router)
    app.include_router(orchestrator_router)
    app.include_router(planning_router)
    app.include_router(tools_router)
    app.include_router(reliability_router)
    install_error_handlers(app)
    return app


app = create_app()
