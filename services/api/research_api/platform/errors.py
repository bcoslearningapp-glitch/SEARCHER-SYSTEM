"""Domain error types and their HTTP mapping.

Domain services raise these; routers never translate errors by hand.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from research_api.modules.ai_gateway.base import (
    ProviderError,
    ProviderOutputError,
    ProviderRefusalError,
    ProviderUnavailableError,
)
from research_api.modules.governance_audit.policy import PolicyViolationError


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "domain_error"

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(DomainError):
    """The request is valid but conflicts with current state (illegal transition, immutability)."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class RuleViolationError(DomainError):
    """A methodology rule blocks the action (e.g. a BLOCKED quality gate)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "rule_violation"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(ProviderError)
    async def _provider(_: Request, exc: ProviderError) -> JSONResponse:
        # Provider failures are distinct from application errors (PRD §72); no provider text is echoed.
        if isinstance(exc, ProviderUnavailableError):
            code, status_code = "provider_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(exc, ProviderRefusalError):
            code, status_code = "provider_refusal", status.HTTP_422_UNPROCESSABLE_CONTENT
        elif isinstance(exc, ProviderOutputError):
            code, status_code = "invalid_structured_output", status.HTTP_502_BAD_GATEWAY
        else:
            code, status_code = "provider_error", status.HTTP_502_BAD_GATEWAY
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": code, "message": str(exc), "details": {"kind": exc.kind}}},
        )

    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError) -> JSONResponse:
        # Constraint names are stable and safe to expose; values and SQL are not echoed.
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "conflict",
                    "message": "the change conflicts with existing records",
                    "details": {"constraint": constraint},
                }
            },
        )

    @app.exception_handler(PolicyViolationError)
    async def _policy(_: Request, exc: PolicyViolationError) -> JSONResponse:
        decision = exc.decision
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "policy_denied",
                    "message": decision.reason,
                    "details": {"action": decision.action, "requires_approval": decision.requires_approval},
                }
            },
        )
