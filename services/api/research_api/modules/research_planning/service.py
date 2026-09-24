"""Research planning service (PRD §22-24, §31, ADR-012).

Plans are versioned per question. Every search, local or web, leaves an
append-only audit record whose outcome keeps "nothing found" apart from
failure, inaccessibility and insufficient coverage (FR-WEB-004). Sufficiency is
a human, decision-relative judgment that stores the coverage it was based on.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ProvenanceKind,
    ResearchOutcomeKind,
    ResearchTrack,
    SufficiencyResult,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.project_workflow import service as projects
from research_api.modules.research_planning.models import ResearchPlan, SearchRecord, SufficiencyAssessment
from research_api.modules.research_planning.schemas import (
    LocalSearchIn,
    LocalSearchOut,
    PlanIn,
    PlanOut,
    PlanOverview,
    PlanRevision,
    SearchRecordOut,
    SufficiencyIn,
    SufficiencyOut,
    TrackCoverage,
)
from research_api.modules.sources_library import service as sources
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

ACTIVE, SUPERSEDED = "ACTIVE", "SUPERSEDED"
LOCAL_LIBRARY, WEB = "local_library", "web"
COMPLETED = frozenset({ResearchOutcomeKind.RESULTS_FOUND, ResearchOutcomeKind.NO_RELEVANT_EVIDENCE_FOUND})
COUNTER_TRACKS = (ResearchTrack.CHALLENGE, ResearchTrack.ALTERNATIVE_EXPLANATION)
PLAN = "ResearchPlan"


def _audit(
    session: Session, auth: Authorized, action: str, project_id: UUID, entity_type: str, entity_id: UUID, **new: Any
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=auth.actor,
            new_state=new or None,
            ai_action=auth.ai_action,
        ),
    )


def _event(
    session: Session, auth: Authorized, event_type: str, project_id: UUID, entity_id: UUID, **payload: Any
) -> None:
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event_type,
            entity_type=PLAN,
            entity_id=entity_id,
            actor=auth.actor,
            payload=payload,
        ),
    )


# -- plans ----------------------------------------------------------------------------


def _plan(session: Session, project_id: UUID, plan_id: UUID, *, lock: bool = False) -> ResearchPlan:
    plan = session.get(ResearchPlan, plan_id, with_for_update=lock)
    if plan is None or plan.project_id != project_id:
        raise NotFoundError("research plan not found", plan_id=str(plan_id))
    return plan


def _plan_row(auth: Authorized, project_id: UUID, data: PlanIn, **extra: Any) -> ResearchPlan:
    return ResearchPlan(
        project_id=project_id,
        status=ACTIVE,
        question=data.question.strip(),
        decision_served=data.decision_served.strip(),
        question_type=data.question_type.value,
        risk_impact=data.risk_impact,
        desired_evidence_types=data.desired_evidence_types,
        languages=data.languages,
        tracks=[t.model_dump(mode="json") for t in data.tracks],
        sufficiency_criteria=data.sufficiency_criteria,
        max_web_searches=data.max_web_searches,
        provenance={
            "kind": (
                ProvenanceKind.AI_GENERATED if auth.actor.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
            ).value,
            "actor": auth.actor.model_dump(mode="json", exclude_none=True),
        },
        **extra,
    )


def create_plan(session: Session, principal: Principal, project_id: UUID, data: PlanIn) -> PlanOut:
    auth = authorized(principal, "research_plan.create")
    projects.require_editable_project(session, project_id)
    plan = _plan_row(auth, project_id, data, series_id=uuid4(), version_number=1)
    session.add(plan)
    session.flush()
    _audit(session, auth, "research_plan.create", project_id, PLAN, plan.id, question=plan.question)
    _event(session, auth, "ResearchPlanCreated", project_id, plan.id, question_type=plan.question_type)
    return PlanOut.model_validate(plan)


def revise_plan(session: Session, principal: Principal, project_id: UUID, plan_id: UUID, data: PlanRevision) -> PlanOut:
    """New version; the previous one is kept and marked SUPERSEDED, never edited."""
    auth = authorized(principal, "research_plan.revise")
    projects.require_editable_project(session, project_id)
    current = _plan(session, project_id, plan_id, lock=True)
    if current.status != ACTIVE:
        raise ConflictError("only the active version of a plan can be revised", plan_id=str(plan_id))
    current.status = SUPERSEDED
    session.flush()
    plan = _plan_row(
        auth,
        project_id,
        data,
        series_id=current.series_id,
        version_number=current.version_number + 1,
        supersedes_id=current.id,
        change_reason=data.change_reason,
    )
    session.add(plan)
    session.flush()
    _audit(
        session,
        auth,
        "research_plan.revise",
        project_id,
        PLAN,
        plan.id,
        supersedes=str(current.id),
        reason=data.change_reason,
    )
    return PlanOut.model_validate(plan)


def list_plans(session: Session, project_id: UUID) -> list[PlanOut]:
    projects.get_project(session, project_id)
    rows = session.scalars(
        select(ResearchPlan)
        .where(ResearchPlan.project_id == project_id, ResearchPlan.status == ACTIVE)
        .order_by(ResearchPlan.created_at)
    )
    return [PlanOut.model_validate(r) for r in rows]


def get_plan(session: Session, project_id: UUID, plan_id: UUID) -> PlanOut:
    return PlanOut.model_validate(_plan(session, project_id, plan_id))


def _series_ids(session: Session, plan: ResearchPlan) -> list[UUID]:
    return list(session.scalars(select(ResearchPlan.id).where(ResearchPlan.series_id == plan.series_id)))


def _records(session: Session, plan: ResearchPlan) -> list[SearchRecord]:
    return list(
        session.scalars(
            select(SearchRecord)
            .where(SearchRecord.plan_id.in_(_series_ids(session, plan)))
            .order_by(SearchRecord.performed_at)
        )
    )


def _coverage(records: list[SearchRecord]) -> list[TrackCoverage]:
    coverage = []
    for track in ResearchTrack:
        runs = [r for r in records if r.track == track.value]
        last = ResearchOutcomeKind(runs[-1].outcome) if runs else None
        coverage.append(
            TrackCoverage(
                track=track,
                searches=len(runs),
                searched=any(ResearchOutcomeKind(r.outcome) in COMPLETED for r in runs),
                last_outcome=last,
                execution_failed=last is ResearchOutcomeKind.RESEARCH_EXECUTION_FAILURE,
            )
        )
    return coverage


def _web_used(records: list[SearchRecord]) -> int:
    """Queries actually sent to a web provider count against the plan's search budget."""
    return sum(len(r.queries) for r in records if r.provider == WEB and r.ai_request_id is not None)


def web_budget_remaining(session: Session, project_id: UUID, plan_id: UUID) -> int | None:
    plan = _plan(session, project_id, plan_id)
    if plan.max_web_searches is None:
        return None
    return max(plan.max_web_searches - _web_used(_records(session, plan)), 0)


def overview(session: Session, project_id: UUID, plan_id: UUID) -> PlanOverview:
    plan = _plan(session, project_id, plan_id)
    versions = session.scalars(
        select(ResearchPlan).where(ResearchPlan.series_id == plan.series_id).order_by(ResearchPlan.version_number)
    )
    records = _records(session, plan)
    history = list(
        session.scalars(
            select(SufficiencyAssessment)
            .where(SufficiencyAssessment.plan_id.in_(_series_ids(session, plan)))
            .order_by(SufficiencyAssessment.assessed_at)
        )
    )
    return PlanOverview(
        plan=PlanOut.model_validate(plan),
        versions=[PlanOut.model_validate(v) for v in versions],
        coverage=_coverage(records),
        web_searches_used=_web_used(records),
        searches=[SearchRecordOut.model_validate(r) for r in reversed(records)],
        current_sufficiency=SufficiencyOut.model_validate(history[-1]) if history else None,
        sufficiency_history=[SufficiencyOut.model_validate(h) for h in reversed(history)],
    )


# -- search audit -----------------------------------------------------------------------


def record_search(
    session: Session,
    principal: Principal,
    project_id: UUID,
    *,
    provider: str,
    question: str,
    queries: list[str],
    outcome: ResearchOutcomeKind,
    result_count: int,
    scope: str,
    plan_id: UUID | None = None,
    track: ResearchTrack | None = None,
    languages: list[str] | None = None,
    exclusions: str | None = None,
    ai_request_id: UUID | None = None,
    ai_action: AIActionRecord | None = None,
) -> SearchRecordOut:
    auth = authorized(principal, "search.record", ai_action=ai_action)
    if outcome is ResearchOutcomeKind.RESULTS_FOUND and result_count < 1:
        raise RuleViolationError("RESULTS_FOUND needs at least one result")
    record = SearchRecord(
        project_id=project_id,
        plan_id=plan_id,
        track=track.value if track else None,
        question=question,
        provider=provider,
        queries=queries,
        languages=languages or [],
        outcome=outcome.value,
        result_count=result_count,
        scope=scope,
        exclusions=exclusions,
        ai_request_id=ai_request_id,
        actor=auth.actor.model_dump(mode="json", exclude_none=True),
        provenance={"ai_action": ai_action.model_dump(mode="json", exclude_none=True)} if ai_action else None,
    )
    session.add(record)
    session.flush()
    _audit(
        session, auth, "search.record", project_id, "SearchRecord", record.id, provider=provider, outcome=outcome.value
    )
    return SearchRecordOut.model_validate(record)


def question_for(session: Session, project_id: UUID, plan_id: UUID | None, question: str | None) -> str:
    if plan_id is not None:
        return _plan(session, project_id, plan_id).question
    if not question or not question.strip():
        raise RuleViolationError("a search needs a plan or a question")
    return question.strip()


def local_search(session: Session, principal: Principal, project_id: UUID, data: LocalSearchIn) -> LocalSearchOut:
    """The project library is searched before any external research (FR-RET-001)."""
    projects.require_editable_project(session, project_id)
    question = question_for(session, project_id, data.plan_id, data.question)
    hits: dict[UUID, dict[str, Any]] = {}
    searched = 0
    scope = "project library"
    for query in data.queries:
        response = sources.search(session, query, project_id=project_id, limit=20)
        searched, scope = response.searched_assets, response.scope
        for hit in response.hits:
            hits.setdefault(hit.chunk_id, hit.model_dump(mode="json"))
    if searched == 0:
        outcome = ResearchOutcomeKind.INSUFFICIENT_SEARCH_COVERAGE
    elif hits:
        outcome = ResearchOutcomeKind.RESULTS_FOUND
    else:
        outcome = ResearchOutcomeKind.NO_RELEVANT_EVIDENCE_FOUND
    record = record_search(
        session,
        principal,
        project_id,
        provider=LOCAL_LIBRARY,
        question=question,
        queries=data.queries,
        outcome=outcome,
        result_count=len(hits),
        scope=f"{scope}: lexical search over {searched} ingested source file(s)",
        plan_id=data.plan_id,
        track=data.track,
        languages=data.languages,
    )
    return LocalSearchOut(records=[record], hits=list(hits.values()))


# -- sufficiency ------------------------------------------------------------------------


def assess_sufficiency(
    session: Session, principal: Principal, project_id: UUID, plan_id: UUID, data: SufficiencyIn
) -> SufficiencyOut:
    """Human judgment, relative to the decision the plan serves (FR-SUFF-001). Stores the coverage it relied on."""
    auth = authorized(principal, "sufficiency.assess")
    projects.require_editable_project(session, project_id)
    plan = _plan(session, project_id, plan_id)
    if plan.status != ACTIVE:
        raise ConflictError("assess sufficiency against the active plan version")
    records = _records(session, plan)
    coverage = _coverage(records)
    unsearched = [c.track.value for c in coverage if c.track in COUNTER_TRACKS and not c.searched]
    if data.result is SufficiencyResult.SUFFICIENTLY_ANSWERED and unsearched:
        # Depth may vary; the counter-evidence search may not be skipped (FR-BIAS-004, Core §41).
        raise RuleViolationError("counter-evidence search is not complete", unsearched_tracks=unsearched)
    assessment = SufficiencyAssessment(
        project_id=project_id,
        plan_id=plan.id,
        decision_served=plan.decision_served,
        result=data.result.value,
        considerations=data.considerations,
        rationale=data.rationale,
        recommend_experiment=data.recommend_experiment,
        signals={
            "coverage": [c.model_dump(mode="json") for c in coverage],
            "search_record_ids": [str(r.id) for r in records],
        },
        assessed_by=auth.actor.model_dump(mode="json", exclude_none=True),
    )
    session.add(assessment)
    session.flush()
    _audit(
        session,
        auth,
        "sufficiency.assess",
        project_id,
        "SufficiencyAssessment",
        assessment.id,
        result=data.result.value,
    )
    _event(session, auth, "SufficiencyAssessed", project_id, plan.id, result=data.result.value)
    return SufficiencyOut.model_validate(assessment)
