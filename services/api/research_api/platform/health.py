"""Liveness/readiness endpoints.

Readiness covers only local dependencies. Cloud AI availability is reported
separately and never makes the product "not ready": the project must stay
usable when providers are down (NFR-REL-001, Scenario H).
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

import redis
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from research_api import __version__
from research_api.config import Settings, get_settings
from research_api.contracts.enums import CONTRACT_SCHEMA_VERSION, RESEARCH_CORE_VERSION
from research_api.platform.db import DBSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

ComponentStatus = Literal["ok", "unavailable"]


class Liveness(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = __version__
    research_core_version: str = RESEARCH_CORE_VERSION
    contract_schema_version: str = CONTRACT_SCHEMA_VERSION


class Readiness(BaseModel):
    status: Literal["ready", "degraded", "unavailable"]
    database: ComponentStatus
    queue: ComponentStatus
    ai_providers_configured: list[str]


@router.get("/health/live", response_model=Liveness)
def live() -> Liveness:
    return Liveness()


@router.get("/health/ready", response_model=Readiness)
def ready(
    response: Response,
    session: DBSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Readiness:
    database: ComponentStatus = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness: database check failed")
        database = "unavailable"

    queue: ComponentStatus = "ok"
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
    except Exception:
        logger.warning("readiness: queue check failed", exc_info=True)
        queue = "unavailable"

    providers = [
        name
        for name, key in (("anthropic", settings.anthropic_api_key), ("openai", settings.openai_api_key))
        if key is not None and key.get_secret_value()
    ]

    if database != "ok":
        overall: Literal["ready", "degraded", "unavailable"] = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif queue != "ok":
        overall = "degraded"
    else:
        overall = "ready"
    return Readiness(status=overall, database=database, queue=queue, ai_providers_configured=providers)
