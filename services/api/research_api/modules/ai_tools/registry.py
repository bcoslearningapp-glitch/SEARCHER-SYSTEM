"""Tool registry and server-side enforcement (PRD §47).

A tool call is bound to a ToolContext built by the application, never by the
model: the project, the acting AI principal, the task's allow-list and the
provenance of the model step. Arguments are validated against the tool's
schema, which never contains a project id, so a model cannot reach another
project. Proposal tools act through domain services under the Policy Engine
(FR-AI-TOOL-005). Every call is logged, refused ones included.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any, Literal
from uuid import UUID, uuid4

import jsonschema
from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import SensitivityLevel
from research_api.modules.ai_tools.models import AIToolCall
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.platform.db import session_scope
from research_api.platform.errors import DomainError

ToolKind = Literal["READ", "PROPOSE", "EXTERNAL"]
OK, DENIED, INVALID, ERROR = "OK", "DENIED", "INVALID", "ERROR"


@dataclass(frozen=True)
class ToolContext:
    project_id: UUID
    sensitivity: SensitivityLevel
    principal: Principal
    requested_by: str
    allowed: frozenset[str]
    job_id: UUID | None = None
    profile: str | None = None
    ai_action: AIActionRecord | None = None

    def with_action(self, ai_action: AIActionRecord) -> ToolContext:
        """Bind the provenance of the model step whose output the next calls act on."""
        return replace(self, ai_action=ai_action)


Handler = Callable[[Session, ToolContext, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class Tool:
    name: str
    kind: ToolKind
    description: str
    input_schema: dict[str, Any]
    handler: Handler
    needs_ai_action: bool = False
    output_ids: Callable[[dict[str, Any]], list[str]] = field(default=lambda _out: [])

    def definition(self) -> dict[str, Any]:
        """Provider-neutral definition an adapter can map to its tool-use format."""
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolDeniedError(DomainError):
    status_code = 403
    code = "tool_denied"


class ToolInputError(DomainError):
    status_code = 422
    code = "tool_invalid_input"


TOOLS: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    if tool.name in TOOLS:
        raise ValueError(f"tool {tool.name} registered twice")
    schema = tool.input_schema
    if schema.get("additionalProperties") is not False or "project_id" in schema.get("properties", {}):
        raise ValueError(f"tool {tool.name}: schemas are closed and never take a project id")
    jsonschema.Draft202012Validator.check_schema(schema)
    TOOLS[tool.name] = tool
    return tool


def definitions(names: frozenset[str] | None = None) -> list[dict[str, Any]]:
    return [t.definition() for n, t in sorted(TOOLS.items()) if names is None or n in names]


def _write_independently(record: AIToolCall) -> None:
    with session_scope() as log_session:
        log_session.add(record)


# Replaceable for tests; production writes outside the caller's transaction.
write_log: Callable[[AIToolCall], None] = _write_independently


def _digest(output: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()


def invoke(session: Session, ctx: ToolContext, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool = TOOLS.get(name)
    record = AIToolCall(
        id=uuid4(),
        project_id=ctx.project_id,
        job_id=ctx.job_id,
        ai_request_id=UUID(ctx.ai_action.task_id) if ctx.ai_action and ctx.ai_action.task_id else None,
        tool=name[:80],
        kind=tool.kind if tool else "UNKNOWN",
        status=OK,
        arguments=arguments if isinstance(arguments, dict) else {"_raw": str(arguments)[:2000]},
        output_ids=[],
        principal_id=ctx.principal.id,
    )

    def refuse(status: str, error: DomainError) -> DomainError:
        record.status, record.reason = status, error.message
        write_log(record)
        return error

    if tool is None:
        raise refuse(DENIED, ToolDeniedError("unknown tool", tool=name))
    if name not in ctx.allowed:
        # The task's allow-list is enforced here, whatever the model asks for (QUALITY_GATES: 0 executed).
        raise refuse(DENIED, ToolDeniedError("tool not allowed for this task", tool=name))
    if tool.needs_ai_action and ctx.ai_action is None:
        raise refuse(DENIED, ToolDeniedError("proposals need the provenance of the model step", tool=name))
    errors = sorted(jsonschema.Draft202012Validator(tool.input_schema).iter_errors(arguments), key=str)
    if errors:
        raise refuse(INVALID, ToolInputError(f"invalid arguments: {errors[0].message}", tool=name))
    try:
        output = tool.handler(session, ctx, arguments)
    except PolicyViolationError as exc:
        raise refuse(DENIED, ToolDeniedError(str(exc), tool=name)) from exc
    except Exception as exc:
        # Domain refusals and provider failures alike leave an ERROR record, then propagate unchanged.
        record.status = ERROR
        record.reason = exc.message if isinstance(exc, DomainError) else f"{type(exc).__name__}: {exc}"[:2000]
        write_log(record)
        raise
    record.output_ids = tool.output_ids(output)
    record.output_sha256 = _digest(output)
    write_log(record)
    return output


def executed_calls(session: Session) -> list[tuple[str, UUID | None]]:
    """(tool, job id) for every call that ran, for the tool-authorization audit (QUALITY_GATES)."""
    rows = session.execute(select(AIToolCall.tool, AIToolCall.job_id).where(AIToolCall.status == OK))
    return [(tool, job_id) for tool, job_id in rows]
