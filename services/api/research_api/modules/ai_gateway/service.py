"""AI gateway service: the single path from domain code to a model (PRD §46-54, §64, ADR-010).

Every call is checked against the project's disclosure policy and budget,
logged as an append-only disclosure/usage record in its own transaction,
and its output is validated against the requested JSON Schema before any
caller can use it. Raw provider output never mutates canonical state here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import jsonschema
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from research_api.config import Settings, get_settings
from research_api.contracts.enums import SensitivityLevel
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_gateway import prompting
from research_api.modules.ai_gateway.base import (
    ModelProfile,
    ProviderError,
    ProviderOutputError,
    ProviderUnavailableError,
    StructuredRequest,
    StructuredResult,
    Usage,
    WebSearchRequest,
    WebSearchResult,
)
from research_api.modules.ai_gateway.models import AIRequestRecord, ProjectAIPolicy
from research_api.modules.ai_gateway.policy import cloud_disclosure
from research_api.modules.ai_gateway.schemas import AIPolicyOut, AIPolicyUpdate, AIRequestOut, ProfileOut
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry
from research_api.modules.project_workflow import service as projects
from research_api.platform.db import session_scope, utcnow
from research_api.platform.errors import RuleViolationError

SUCCEEDED, FAILED, BLOCKED = "SUCCEEDED", "FAILED", "BLOCKED"
STOPPED_RESOURCE_CONSTRAINT = "STOPPED_RESOURCE_CONSTRAINT"


class DisclosureBlockedError(RuleViolationError):
    code = "disclosure_blocked"


class ResourceConstraintError(RuleViolationError):
    """Budget exhausted: the task stops as STOPPED_RESOURCE_CONSTRAINT, never as complete (FR-COST-003)."""

    code = "stopped_resource_constraint"


@dataclass(frozen=True)
class CallContext:
    project_id: UUID
    sensitivity: SensitivityLevel
    principal_id: str
    entity_ids: list[UUID] = field(default_factory=list)


@dataclass(frozen=True)
class AIOutcome:
    result: StructuredResult
    request_record_id: UUID
    ai_action: AIActionRecord


def _write_independently(record: AIRequestRecord) -> None:
    with session_scope() as log_session:
        log_session.add(record)


# Replaceable for tests; production writes the log outside the caller's transaction.
write_log: Callable[[AIRequestRecord], None] = _write_independently


# -- profiles and policy ------------------------------------------------------


def list_profiles(settings: Settings | None = None) -> list[ProfileOut]:
    settings = settings or get_settings()
    return [
        ProfileOut(
            name=p.name,
            provider=p.provider,
            model=p.model,
            effort=p.effort,
            local=p.local,
            configured=registry.is_configured(settings, p),
            default=p.name == settings.ai_default_profile,
        )
        for p in registry.profiles(settings).values()
    ]


def _spent(session: Session, project_id: UUID) -> Decimal:
    total = session.scalar(
        select(func.coalesce(func.sum(AIRequestRecord.estimated_cost_usd), 0)).where(
            AIRequestRecord.project_id == project_id
        )
    )
    return Decimal(total or 0)


def _policy_out(session: Session, project_id: UUID, policy: ProjectAIPolicy | None) -> AIPolicyOut:
    return AIPolicyOut(
        project_id=project_id,
        cloud_consent=policy.cloud_consent if policy else False,
        allowed_profiles=list(policy.allowed_profiles) if policy else [],
        preferred_profile=policy.preferred_profile if policy else None,
        project_budget_usd=policy.project_budget_usd if policy else None,
        task_budget_usd=policy.task_budget_usd if policy else None,
        spent_usd=_spent(session, project_id),
    )


def get_policy(session: Session, project_id: UUID) -> AIPolicyOut:
    projects.get_project(session, project_id)
    return _policy_out(session, project_id, session.get(ProjectAIPolicy, project_id))


def update_policy(session: Session, principal: Principal, project_id: UUID, data: AIPolicyUpdate) -> AIPolicyOut:
    auth = authorized(principal, "ai_policy.update")
    projects.require_editable_project(session, project_id)
    known = set(registry.profiles(get_settings()))
    unknown = sorted({*data.allowed_profiles, *([data.preferred_profile] if data.preferred_profile else [])} - known)
    if unknown:
        raise RuleViolationError("unknown AI profile", profiles=unknown)
    if data.preferred_profile and data.allowed_profiles and data.preferred_profile not in data.allowed_profiles:
        raise RuleViolationError("preferred profile must be one of the allowed profiles")
    policy = session.get(ProjectAIPolicy, project_id, with_for_update=True)
    previous = _policy_out(session, project_id, policy).model_dump(mode="json", exclude={"spent_usd"})
    if policy is None:
        policy = ProjectAIPolicy(project_id=project_id)
        session.add(policy)
    policy.cloud_consent = data.cloud_consent
    policy.allowed_profiles = data.allowed_profiles
    policy.preferred_profile = data.preferred_profile
    policy.project_budget_usd = data.project_budget_usd
    policy.task_budget_usd = data.task_budget_usd
    policy.updated_by_id = principal.id
    session.flush()
    out = _policy_out(session, project_id, policy)
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="ai_policy.update",
            entity_type="ProjectAIPolicy",
            entity_id=project_id,
            actor=auth.actor,
            previous_state=previous,
            new_state=out.model_dump(mode="json", exclude={"spent_usd"}),
            reason=data.reason,
        ),
    )
    return out


def list_requests(session: Session, project_id: UUID, *, limit: int = 200) -> list[AIRequestOut]:
    projects.get_project(session, project_id)
    rows = session.scalars(
        select(AIRequestRecord)
        .where(AIRequestRecord.project_id == project_id)
        .order_by(AIRequestRecord.created_at.desc())
        .limit(limit)
    )
    return [AIRequestOut.model_validate(r, from_attributes=True) for r in rows]


# -- structured calls ----------------------------------------------------------


def _select_profile(settings: Settings, policy: ProjectAIPolicy | None, requested: str | None) -> ModelProfile:
    available = registry.profiles(settings)
    name = requested or (policy.preferred_profile if policy else None) or settings.ai_default_profile
    profile = available.get(name)
    if profile is None:
        raise RuleViolationError("unknown AI profile", profile=name)
    if policy and policy.allowed_profiles and name not in policy.allowed_profiles:
        raise DisclosureBlockedError("this project does not allow the requested AI profile", profile=name)
    return profile


def _worst_case_cost(profile: ModelProfile, request: StructuredRequest, chars: int) -> Decimal:
    # ~3 characters per token is a conservative upper bound for mixed Arabic/English text.
    estimate = profile.estimate_cost(Usage(chars // 3 + 1, min(request.max_tokens, profile.max_tokens)))
    return Decimal(str(estimate))


@dataclass
class _Attempt:
    """One logged AI call: the disclosure/usage record plus the settings and profile it runs under."""

    record: AIRequestRecord
    settings: Settings
    profile: ModelProfile

    def stop(self, status: str, kind: str, error: Exception) -> Exception:
        self.record.status, self.record.error_kind = status, kind
        write_log(self.record)
        return error

    def finish(self, usage: Usage, model: str, request_id: str | None) -> None:
        self.record.model = model
        self.record.input_tokens, self.record.output_tokens = usage.input_tokens, usage.output_tokens
        self.record.estimated_cost_usd = Decimal(str(round(self.profile.estimate_cost(usage), 6)))
        self.record.provider_request_id = request_id

    def ai_action(self, ctx: CallContext, provider: str, model: str) -> AIActionRecord:
        return AIActionRecord(
            provider=provider,
            model=model,
            template_version=self.record.template_version,
            supplied_entity_ids=ctx.entity_ids,
            task_id=str(self.record.id),
            timestamp=utcnow(),
        )


def _preflight(
    session: Session,
    ctx: CallContext,
    *,
    task: str,
    template_version: str,
    chars: int,
    profile_name: str | None,
    worst_case: Callable[[ModelProfile], Decimal],
) -> _Attempt:
    """Profile, disclosure (PRD §54) and budget checks (FR-COST-002/003). Every refusal is logged."""
    settings = get_settings()
    policy = session.get(ProjectAIPolicy, ctx.project_id)
    record = AIRequestRecord(
        id=uuid4(),
        project_id=ctx.project_id,
        task=task,
        template_version=template_version,
        profile=profile_name or "",
        provider="",
        model="",
        sensitivity=ctx.sensitivity.value,
        entity_ids=[str(e) for e in ctx.entity_ids],
        outbound_chars=0,
        principal_id=ctx.principal_id,
        disclosure_reason="",
    )

    def block(kind: str, reason: str, error: Exception) -> Exception:
        record.status, record.error_kind = BLOCKED, kind
        record.disclosure_reason = record.disclosure_reason or reason
        write_log(record)
        return error

    try:
        profile = _select_profile(settings, policy, profile_name)
    except RuleViolationError as exc:
        raise block(exc.code, exc.message, exc) from None
    record.profile, record.provider, record.model = profile.name, profile.provider, profile.model

    disclosure = cloud_disclosure(
        ctx.sensitivity, project_consent=bool(policy and policy.cloud_consent), provider_is_local=profile.local
    )
    record.disclosure_reason = disclosure.reason
    if not disclosure.allowed:
        raise block("disclosure_blocked", disclosure.reason, DisclosureBlockedError(disclosure.reason))

    worst = worst_case(profile)
    if policy and policy.task_budget_usd is not None and worst > policy.task_budget_usd:
        message = "task could exceed the per-task AI budget"
        error = ResourceConstraintError(message, estimate_usd=str(worst), budget_usd=str(policy.task_budget_usd))
        raise block(STOPPED_RESOURCE_CONSTRAINT, message, error)
    if policy and policy.project_budget_usd is not None:
        spent = _spent(session, ctx.project_id)
        if spent + worst > policy.project_budget_usd:
            message = "project AI budget would be exceeded"
            error = ResourceConstraintError(message, spent_usd=str(spent), budget_usd=str(policy.project_budget_usd))
            raise block(STOPPED_RESOURCE_CONSTRAINT, message, error)
    record.outbound_chars = chars
    return _Attempt(record, settings, profile)


def run_structured(
    session: Session, ctx: CallContext, request: StructuredRequest, *, profile_name: str | None = None
) -> AIOutcome:
    chars = prompting.outbound_chars(request)
    attempt = _preflight(
        session,
        ctx,
        task=request.task,
        template_version=request.template_version,
        chars=chars,
        profile_name=profile_name,
        worst_case=lambda p: _worst_case_cost(p, request, chars),
    )
    try:
        result = registry.provider_for(attempt.settings, attempt.profile).generate_structured(request, attempt.profile)
    except ProviderError as exc:
        raise attempt.stop(FAILED, exc.kind, exc) from exc
    attempt.finish(result.usage, result.model, result.request_id)
    attempt.record.served_by_fallback = result.served_by_fallback
    try:
        validate_output(result.data, request.output_schema)
    except ProviderOutputError as exc:
        raise attempt.stop(FAILED, exc.kind, exc) from exc
    attempt.record.status = SUCCEEDED
    write_log(attempt.record)
    return AIOutcome(result, attempt.record.id, attempt.ai_action(ctx, result.provider, result.model))


@dataclass(frozen=True)
class WebSearchOutcome:
    result: WebSearchResult
    request_record_id: UUID
    ai_action: AIActionRecord


WEB_SEARCH_TASK = "web_search"
_WEB_SEARCH_OVERHEAD_TOKENS = 4000  # runner prompt, result blocks and continuations per call


def run_web_search(
    session: Session, ctx: CallContext, request: WebSearchRequest, *, profile_name: str | None = None
) -> WebSearchOutcome:
    """Queries are outbound disclosure: same policy, budget and log as any other AI call (PRD §54)."""
    chars = sum(len(q) for q in request.queries)

    def worst(profile: ModelProfile) -> Decimal:
        usage = Usage(_WEB_SEARCH_OVERHEAD_TOKENS * 2, 2000, request.max_searches)
        return Decimal(str(profile.estimate_cost(usage)))

    attempt = _preflight(
        session,
        ctx,
        task=WEB_SEARCH_TASK,
        template_version=request.template_version,
        chars=chars,
        profile_name=profile_name,
        worst_case=worst,
    )
    provider = registry.provider_for(attempt.settings, attempt.profile) if _configured(attempt) else None
    try:
        if provider is None or not provider.capabilities().get("web_search"):
            raise ProviderUnavailableError(f"profile '{attempt.profile.name}' has no web search")
        result = provider.web_search(request, attempt.profile)
    except ProviderError as exc:
        raise attempt.stop(FAILED, exc.kind, exc) from exc
    attempt.finish(result.usage, result.model, result.request_id)
    attempt.record.status = SUCCEEDED
    write_log(attempt.record)
    return WebSearchOutcome(result, attempt.record.id, attempt.ai_action(ctx, result.provider, result.model))


def _configured(attempt: _Attempt) -> bool:
    return registry.is_configured(attempt.settings, attempt.profile)


def validate_output(data: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate before any caller may act on the output (CLAUDE.md: validate before mutation)."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        where = "/".join(str(p) for p in first.path) or "(root)"
        raise ProviderOutputError(f"structured output failed validation at {where}: {first.message}")
