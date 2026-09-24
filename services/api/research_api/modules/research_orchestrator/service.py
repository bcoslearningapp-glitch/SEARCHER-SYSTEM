"""Research Orchestrator (PRD §48, ADR-011).

Humans launch AI tasks; each runs as a durable background job. The model only
returns schema-validated structured output, and every change to canonical
state goes through the owning domain service with an AI principal and full
provenance, so it lands as DRAFT / UNCONFIRMED / CANDIDATE for a human to judge.
A failing task rolls back as a whole (NFR-REL-003); its disclosure log and, for
"Challenge this", an explicit execution-failure track record survive.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    EvidenceRole,
    EvidenceTargetType,
    ResearchOutcomeKind,
    ResearchTrack,
    SensitivityLevel,
)
from research_api.modules import targets
from research_api.modules.ai_gateway import service as gateway
from research_api.modules.ai_gateway.base import ProviderOutputError, Section, StructuredRequest
from research_api.modules.ai_tools import registry as tool_registry
from research_api.modules.ai_tools import tools as ai_tools
from research_api.modules.ai_tools.registry import ToolContext
from research_api.modules.claims_evidence import service as claims
from research_api.modules.claims_evidence.schemas import TrackRunIn
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal, ai_principal, system_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.hypothesis_lab import service as hypotheses
from research_api.modules.project_workflow import service as projects
from research_api.modules.research_orchestrator import templates
from research_api.modules.research_orchestrator.templates import Template
from research_api.modules.research_planning import service as planning
from research_api.platform import jobs
from research_api.platform.errors import RuleViolationError

logger = logging.getLogger(__name__)

WORKER_TASK = "orchestrator.run"
KIND_PREFIX = "orchestrator."
AI = ai_principal("research_orchestrator")
SYSTEM = system_principal("research_orchestrator")

TaskName = Literal["draft_problem_frame", "detect_assumptions", "challenge", "web_search"]
CHALLENGEABLE = frozenset({EvidenceTargetType.CLAIM, EvidenceTargetType.HYPOTHESIS})
MAX_ASSUMPTIONS = 8
MAX_CHALLENGE_QUERIES = 4
MAX_ALTERNATIVES = 3
MAX_QUERIES_PER_ALTERNATIVE = 3
HITS_PER_QUERY = 5
MAX_PASSAGES = 12
PASSAGE_CHARS = 2000
MAX_COMPETING = 3
MAX_WEB_QUERIES = 8
COUNTER_TRACKS = (ResearchTrack.CHALLENGE, ResearchTrack.ALTERNATIVE_EXPLANATION)
_CHALLENGING_ROLES = frozenset({EvidenceRole.CONTRADICTS, EvidenceRole.LIMITS, EvidenceRole.QUALIFIES})


class AITaskIn(BaseModel):
    task: TaskName
    target_type: EvidenceTargetType | None = None
    target_id: UUID | None = None
    profile: str | None = None
    # web_search
    plan_id: UUID | None = None
    track: ResearchTrack | None = None
    question: str | None = None
    queries: list[str] = Field(default_factory=list, max_length=MAX_WEB_QUERIES)
    languages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _task_inputs(self) -> AITaskIn:
        if self.task == "challenge":
            if self.target_type is None or self.target_id is None:
                raise ValueError("challenge needs target_type and target_id")
            if self.target_type not in CHALLENGEABLE:
                raise ValueError("challenge supports claims and hypotheses")
        if self.task == "web_search":
            self.queries = [q.strip() for q in self.queries if q.strip()]
            if not self.queries:
                raise ValueError("web_search needs at least one query")
            if self.plan_id is None and not (self.question or "").strip():
                raise ValueError("web_search needs a plan_id or a question")
        return self


# -- launching -------------------------------------------------------------------


def launch(session: Session, principal: Principal, project_id: UUID, data: AITaskIn) -> jobs.BackgroundJob:
    """Create the durable job. The router commits and dispatches (the worker must see the row)."""
    authorized(principal, "ai_task.launch")
    projects.require_editable_project(session, project_id)
    if data.target_type is not None and data.target_id is not None:
        targets.require(session, project_id, data.target_type, data.target_id)
    params: dict[str, Any] = {
        "task": data.task,
        "profile": data.profile,
        "requested_by": principal.id,
        "target_type": data.target_type.value if data.target_type else None,
        "target_id": str(data.target_id) if data.target_id else None,
    }
    if data.task == "web_search":
        # Resolve the question now so the audit record always states what was being researched.
        question = planning.question_for(session, project_id, data.plan_id, data.question)
        params |= {
            "plan_id": str(data.plan_id) if data.plan_id else None,
            "track": data.track.value if data.track else None,
            "question": question,
            "queries": data.queries,
            "languages": data.languages,
        }
    return jobs.create_job(session, KIND_PREFIX + data.task, params=params, project_id=project_id)


def list_tasks(session: Session, project_id: UUID, *, limit: int = 50) -> list[jobs.JobOut]:
    projects.get_project(session, project_id)
    rows = session.scalars(
        select(jobs.BackgroundJob)
        .where(jobs.BackgroundJob.project_id == project_id, jobs.BackgroundJob.kind.startswith(KIND_PREFIX))
        .order_by(jobs.BackgroundJob.created_at.desc())
        .limit(limit)
    )
    return [jobs.JobOut.model_validate(r) for r in rows]


# -- job body ----------------------------------------------------------------------


def run(session: Session, job: jobs.BackgroundJob) -> dict[str, Any]:
    if job.project_id is None:
        raise RuleViolationError("orchestrator jobs belong to a project")
    task = job.params["task"]
    runner = _TASKS.get(task)
    if runner is None:
        raise RuleViolationError("unknown orchestrator task", task=task)
    return runner(session, job, job.project_id)


def on_failure(session: Session, job: jobs.BackgroundJob) -> None:
    """A failed or stopped search is recorded as such: failure is never 'no evidence' (Core §72)."""
    if job.project_id is None:
        return
    outcome = (
        ResearchOutcomeKind.STOPPED_RESOURCE_CONSTRAINT
        if job.failure_kind == jobs.JobFailureKind.STOPPED_RESOURCE_CONSTRAINT.value
        else ResearchOutcomeKind.RESEARCH_EXECUTION_FAILURE
    )
    if job.params.get("task") == "web_search":
        _record_web_failure(session, job, outcome)
        return
    if job.params.get("task") != "challenge":
        return
    target_type = EvidenceTargetType(job.params["target_type"])
    target_id = UUID(job.params["target_id"])
    for track in COUNTER_TRACKS:
        claims.record_track_run(
            session,
            SYSTEM,
            job.project_id,
            TrackRunIn(
                target_type=target_type,
                target_id=target_id,
                track=track,
                outcome=outcome,
                scope=f"Challenge this (job {job.id}) did not complete: {job.failure_kind}",
            ),
        )


def _context(
    session: Session, job: jobs.BackgroundJob, project_id: UUID, entity_ids: list[UUID]
) -> gateway.CallContext:
    project = projects.get_project(session, project_id)
    return gateway.CallContext(
        project_id=project_id,
        sensitivity=SensitivityLevel(project.sensitivity),
        principal_id=str(job.params.get("requested_by") or "unknown"),
        entity_ids=entity_ids,
    )


# Each task may use only these tools, whatever a model asks for (FR-AI-TOOL-003..005).
TASK_TOOLS: dict[str, frozenset[str]] = {
    "draft_problem_frame": frozenset({"get_project_state", "draft_problem_frame"}),
    "detect_assumptions": frozenset({"get_project_state", "propose_assumption"}),
    "challenge": frozenset({"search_sources", "read_passages", "propose_evidence", "propose_hypothesis"}),
    "web_search": frozenset({"search_external_web"}),
}


def _tools(session: Session, job: jobs.BackgroundJob, project_id: UUID) -> ToolContext:
    project = projects.get_project(session, project_id)
    return ToolContext(
        project_id=project_id,
        sensitivity=SensitivityLevel(project.sensitivity),
        principal=AI,
        requested_by=str(job.params.get("requested_by") or "unknown"),
        allowed=TASK_TOOLS[job.params["task"]],
        job_id=job.id,
        profile=job.params.get("profile"),
    )


def _call(
    session: Session, ctx: gateway.CallContext, template: Template, sections: list[Section], profile: str | None
) -> gateway.AIOutcome:
    request = StructuredRequest(
        task=template.task,
        template_version=template.version,
        instructions=template.instructions,
        sections=sections,
        output_schema=template.output_schema,
    )
    try:
        return gateway.run_structured(session, ctx, request, profile_name=profile)
    except ProviderOutputError:
        # One retry, then surface (FR-ORCH-002). Nothing has been written yet.
        logger.info("retrying %s after invalid structured output", template.task)
        return gateway.run_structured(session, ctx, request, profile_name=profile)


def _frame_context(session: Session, project_id: UUID) -> Section | None:
    frames = projects.list_frames(session, project_id)
    if not frames:
        return None
    latest = max(frames, key=lambda f: f.version_number)
    body = "\n".join(f"{k}: {v}" for k, v in latest.content.model_dump().items() if v)
    return Section("context", f"Problem Frame v{latest.version_number} ({latest.status.value})", body)


# -- draft Problem Frame ----------------------------------------------------------------


def _draft_problem_frame(session: Session, job: jobs.BackgroundJob, project_id: UUID) -> dict[str, Any]:
    if ai_tools.open_researcher_draft(session, project_id):
        # Checked before spending on a model call; the tool enforces it again at write time.
        raise RuleViolationError("a researcher's draft is open; AI will not overwrite it")
    tctx = _tools(session, job, project_id)
    state = tool_registry.invoke(session, tctx, "get_project_state", {})
    sections = [
        Section("user_input", "Project title", state["title"]),
        Section("user_input", f"Project input ({state['input_type']})", state["initial_input"]),
    ]
    if state["current_question"]:
        sections.append(Section("context", "Current question", state["current_question"]))
    outcome = _call(
        session,
        _context(session, job, project_id, [project_id]),
        templates.DRAFT_PROBLEM_FRAME,
        sections,
        job.params.get("profile"),
    )
    cleaned = {
        k: [x.strip() for x in v if x.strip()] if isinstance(v, list) else str(v).strip()
        for k, v in outcome.result.data.items()
    }
    jobs.raise_if_cancelled(session, job)
    return tool_registry.invoke(
        session, tctx.with_action(outcome.ai_action), "draft_problem_frame", {"content": cleaned}
    )


# -- detect assumptions -----------------------------------------------------------------


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text).strip().casefold()


def _detect_assumptions(session: Session, job: jobs.BackgroundJob, project_id: UUID) -> dict[str, Any]:
    tctx = _tools(session, job, project_id)
    state = tool_registry.invoke(session, tctx, "get_project_state", {})
    existing = claims.list_assumptions(session, project_id)
    sections = [Section("user_input", "Project input", state["initial_input"])]
    frame = _frame_context(session, project_id)
    if frame is not None:
        sections.append(frame)
    claim_list = claims.list_claims(session, project_id)
    if claim_list:
        sections.append(Section("context", "Claims", "\n".join(f"- {c.statement}" for c in claim_list)))
    hypothesis_list = hypotheses.list_hypotheses(session, project_id)
    if hypothesis_list:
        sections.append(
            Section("context", "Hypotheses", "\n".join(f"- {h.content.statement}" for h in hypothesis_list))
        )
    if existing:
        sections.append(
            Section("context", "Assumptions already recorded", "\n".join(f"- {a.statement}" for a in existing))
        )
    ids = [project_id, *(c.id for c in claim_list), *(h.id for h in hypothesis_list)]
    outcome = _call(
        session,
        _context(session, job, project_id, ids),
        templates.DETECT_ASSUMPTIONS,
        sections,
        job.params.get("profile"),
    )
    jobs.raise_if_cancelled(session, job)
    propose = tctx.with_action(outcome.ai_action)
    seen = {_normalize(a.statement) for a in existing}
    created: list[str] = []
    for item in outcome.result.data["assumptions"][:MAX_ASSUMPTIONS]:
        key = _normalize(item["statement"])
        if not key or key in seen:
            continue
        seen.add(key)
        args = {"statement": item["statement"].strip(), "criticality": item["criticality"]}
        created.append(tool_registry.invoke(session, propose, "propose_assumption", args)["assumption_id"])
    return {"assumption_ids": created, "proposed": len(outcome.result.data["assumptions"])}


# -- Challenge this -----------------------------------------------------------------------


def _or_query(query: str) -> str:
    """Keyword queries match any term; ranking favours passages matching more of them."""
    words = [w for w in re.findall(r"\w+", query) if len(w) > 2]
    return " or ".join(words) if words else query


def _target_statement(session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID) -> str:
    if target_type is EvidenceTargetType.HYPOTHESIS:
        h = hypotheses.get_hypothesis(session, project_id, target_id)
        return h.content.statement + (f"\nContext: {h.content.context}" if h.content.context else "")
    return claims.get_claim(session, project_id, target_id).statement


@dataclass
class _Challenge:
    """Working state of one "Challenge this" run."""

    tools: ToolContext
    target_type: EvidenceTargetType
    target_id: UUID
    statement: str
    challenge_queries: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    alternative_queries: list[str] = field(default_factory=list)
    passages: list[dict[str, Any]] = field(default_factory=list)
    scope: str = "project library"
    searched_assets: int = 0
    found: dict[ResearchTrack, bool] = field(default_factory=lambda: dict.fromkeys(COUNTER_TRACKS, False))
    evidence_ids: list[str] = field(default_factory=list)
    competing_ids: list[str] = field(default_factory=list)

    @property
    def project_id(self) -> UUID:
        return self.tools.project_id


def _challenge(session: Session, job: jobs.BackgroundJob, project_id: UUID) -> dict[str, Any]:
    target_type = EvidenceTargetType(job.params["target_type"])
    target_id = UUID(job.params["target_id"])
    profile = job.params.get("profile")
    statement = _target_statement(session, project_id, target_type, target_id)
    run = _Challenge(_tools(session, job, project_id), target_type, target_id, statement)
    ctx = _context(session, job, project_id, [target_id])

    plan = _call(
        session,
        ctx,
        templates.PLAN_CHALLENGE,
        [Section("context", "Statement under challenge", run.statement)],
        profile,
    )
    _apply_plan(run, plan.result.data)
    _search(session, run)
    assessment = None
    if run.passages:
        assessment = _call(session, ctx, templates.ASSESS_PASSAGES, _passage_sections(run), profile)
    jobs.raise_if_cancelled(session, job)

    if assessment is not None:
        _propose_candidates(session, run, assessment)
    _record_tracks(session, run, (assessment or plan).ai_action)
    if assessment is not None and target_type is EvidenceTargetType.HYPOTHESIS:
        _propose_competitors(session, run, assessment)
    return {
        "queries": [*run.challenge_queries, *run.alternative_queries],
        "passages_considered": len(run.passages),
        "searched_assets": run.searched_assets,
        "evidence_candidate_ids": run.evidence_ids,
        "competing_hypothesis_ids": run.competing_ids,
        "tracks": {t.value: run.found[t] for t in COUNTER_TRACKS},
    }


def _apply_plan(run: _Challenge, data: dict[str, Any]) -> None:
    run.challenge_queries = [q for q in data["challenge_queries"] if q.strip()][:MAX_CHALLENGE_QUERIES]
    run.alternatives = [a for a in data["alternative_explanations"] if a["statement"].strip()][:MAX_ALTERNATIVES]
    run.alternative_queries = [
        q for a in run.alternatives for q in a["queries"][:MAX_QUERIES_PER_ALTERNATIVE] if q.strip()
    ]


def _search(session: Session, run: _Challenge) -> None:
    hits: dict[str, dict[str, Any]] = {}
    for query in [*run.challenge_queries, *run.alternative_queries]:
        found = tool_registry.invoke(
            session, run.tools, "search_sources", {"query": _or_query(query)[:300], "limit": HITS_PER_QUERY}
        )
        run.scope, run.searched_assets = found["scope"], found["searched_assets"]
        for hit in found["hits"]:
            hits.setdefault(hit["chunk_id"], hit)
    top = sorted(hits.values(), key=lambda h: -h["rank"])[:MAX_PASSAGES]
    if top:
        read = tool_registry.invoke(session, run.tools, "read_passages", {"chunk_ids": [h["chunk_id"] for h in top]})
        by_id = {p["chunk_id"]: p for p in read["passages"]}
        run.passages = [by_id[h["chunk_id"]] for h in top if h["chunk_id"] in by_id]


def _passage_sections(run: _Challenge) -> list[Section]:
    framing = (
        run.statement
        + "\n\nAlternative explanations:\n"
        + "\n".join(f"[{i}] {a['statement']}" for i, a in enumerate(run.alternatives))
    )
    return [Section("context", "Statement under challenge", framing)] + [
        Section(
            "retrieved_source",
            f"{p['work_title']}, p. {p['page_number']}",
            p["text"][:PASSAGE_CHARS],
            source_id=f"P{i}",
        )
        for i, p in enumerate(run.passages)
    ]


def _track_for(run: _Challenge, role: EvidenceRole, alternative_index: int) -> ResearchTrack | None:
    if 0 <= alternative_index < len(run.alternatives):
        return ResearchTrack.ALTERNATIVE_EXPLANATION
    if role in _CHALLENGING_ROLES:
        return ResearchTrack.CHALLENGE
    if role is EvidenceRole.SUPPORTS:
        return ResearchTrack.SUPPORT
    return None


def _propose_candidates(session: Session, run: _Challenge, assessment: gateway.AIOutcome) -> None:
    by_id = {f"P{i}": p for i, p in enumerate(run.passages)}
    propose = run.tools.with_action(assessment.ai_action)
    for candidate in assessment.result.data["candidates"]:
        passage = by_id.get(candidate["passage_id"])
        if passage is None:
            continue  # the model referred to a passage it was not given
        role = EvidenceRole(candidate["role"])
        track = _track_for(run, role, candidate["alternative_index"])
        args: dict[str, Any] = {
            "target_type": run.target_type.value,
            "target_id": str(run.target_id),
            "role": role.value,
            "finding": candidate["finding"].strip() or "See passage.",
            "chunk_id": passage["chunk_id"],
        }
        if track is not None:
            args["track"] = track.value
        run.evidence_ids.append(tool_registry.invoke(session, propose, "propose_evidence", args)["evidence_id"])
        if track in run.found:
            run.found[track] = True


def _record_tracks(session: Session, run: _Challenge, ai_action: AIActionRecord) -> None:
    """Bounded outcomes per counter track (Core §41, §72): what was searched, and what came of it."""
    queries = {
        ResearchTrack.CHALLENGE: run.challenge_queries,
        ResearchTrack.ALTERNATIVE_EXPLANATION: run.alternative_queries,
    }
    for track in COUNTER_TRACKS:
        if run.searched_assets == 0:
            outcome = ResearchOutcomeKind.INSUFFICIENT_SEARCH_COVERAGE
        elif run.found[track]:
            outcome = ResearchOutcomeKind.RESULTS_FOUND
        else:
            outcome = ResearchOutcomeKind.NO_RELEVANT_EVIDENCE_FOUND
        claims.record_track_run(
            session,
            AI,
            run.project_id,
            TrackRunIn(
                target_type=run.target_type,
                target_id=run.target_id,
                track=track,
                outcome=outcome,
                scope=f"{run.scope}: lexical search over {run.searched_assets} ingested source file(s)",
                queries=queries[track],
            ),
            ai_action=ai_action,
        )


def _propose_competitors(session: Session, run: _Challenge, assessment: gateway.AIOutcome) -> None:
    """Strong alternative explanations become competing hypotheses in SIGNAL state (FR-BIAS-003)."""
    strong = {
        s["alternative_index"]
        for s in assessment.result.data["alternative_support"]
        if s["strength"] == "STRONG" and 0 <= s["alternative_index"] < len(run.alternatives)
    }
    propose = run.tools.with_action(assessment.ai_action)
    for index in sorted(strong)[:MAX_COMPETING]:
        args = {
            "statement": run.alternatives[index]["statement"].strip(),
            "context": f"Alternative explanation raised by Challenge this against: {run.statement}"[:4000],
            "competes_with": str(run.target_id),
            "note": "Proposed by Challenge this",
        }
        run.competing_ids.append(tool_registry.invoke(session, propose, "propose_hypothesis", args)["hypothesis_id"])


# -- web search ---------------------------------------------------------------------------


def _record_web_failure(session: Session, job: jobs.BackgroundJob, outcome: ResearchOutcomeKind) -> None:
    params = job.params
    assert job.project_id is not None  # noqa: S101 - orchestrator jobs always carry a project
    planning.record_search(
        session,
        SYSTEM,
        job.project_id,
        provider=planning.WEB,
        question=params["question"],
        queries=params["queries"],
        outcome=outcome,
        result_count=0,
        scope=f"web search (job {job.id}) did not complete: {job.error}",
        plan_id=UUID(params["plan_id"]) if params.get("plan_id") else None,
        track=ResearchTrack(params["track"]) if params.get("track") else None,
        languages=params.get("languages") or [],
    )


def _web_search(session: Session, job: jobs.BackgroundJob, project_id: UUID) -> dict[str, Any]:
    """External search through the controlled tool; results become source leads only (FR-WEB-003)."""
    params = job.params
    args: dict[str, Any] = {"queries": params["queries"], "languages": params.get("languages") or []}
    for key in ("plan_id", "track", "question"):
        if params.get(key):
            args[key] = params[key]
    found = tool_registry.invoke(session, _tools(session, job, project_id), "search_external_web", args)
    jobs.raise_if_cancelled(session, job)
    return {
        "search_record_id": found["search_record_id"],
        "outcome": found["outcome"],
        "results": len(found["results"]),
        "lead_ids": found["lead_ids"],
    }


_TASKS = {
    "draft_problem_frame": _draft_problem_frame,
    "detect_assumptions": _detect_assumptions,
    "challenge": _challenge,
    "web_search": _web_search,
}
