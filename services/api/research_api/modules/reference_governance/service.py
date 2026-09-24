"""Public service: foundational library, Qur'an/Hadith retrieval, reference review (PRD §18-21, Core §4-9, §30-31).

Invariants enforced here and in the database:
- Only APPROVED foundational sources are served; approval is human (Constitutional Authority).
- SOURCE_TEXT content is copied server-side from the cited source; it is never client- or AI-authored.
- AI-authored entries are SYSTEM_SYNTHESIS only; approved interpretation must cite an approved source.
- NOT_IN_CONFLICT is a distinct judgment from REFERENCE_SUPPORTED; support needs sourced, direct/close grounds.
- Judgments are human and append-only; blocking reservations raise a blocking decision.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ActorRole,
    Directness,
    EvidenceTargetType,
    FoundationalSourceStatus,
    ProvenanceKind,
    QualityGateResult,
    QualityGateType,
    ReferenceAuthorityLayer,
    ReferenceJudgmentState,
    ReferenceReasoningLayer,
    ReservationType,
    RiskLevel,
)
from research_api.modules import targets
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal, system_principal
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    AuditEntry,
    DecisionCreate,
    GateFinding,
    ResearchEventEntry,
)
from research_api.modules.project_workflow import service as projects
from research_api.modules.reference_governance import quran_dataset
from research_api.modules.reference_governance.models import (
    FoundationalSource,
    HadithRecord,
    QuranAyah,
    QuranSurah,
    ReferenceEntry,
    ReferenceJudgmentRecord,
    ReferenceReview,
)
from research_api.modules.reference_governance.schemas import (
    ApproveIn,
    AyahOut,
    Divergence,
    EntryIn,
    EntryOut,
    FoundationalOut,
    FoundationalStageIn,
    HadithIn,
    HadithOut,
    JudgmentIn,
    JudgmentOut,
    ReferenceStanding,
    ReviewIn,
    ReviewOut,
)
from research_api.modules.sources_library import service as sources
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError
from research_api.platform.storage import validate_upload

L = ReferenceAuthorityLayer
HADITH_LAYERS = frozenset({L.SUNNAH, L.APPROVED_FOUNDATIONAL})
J = ReferenceJudgmentState


def _audit(
    session: Session,
    auth: Authorized,
    action: str,
    entity_type: str,
    entity_id: UUID,
    *,
    project_id: UUID | None = None,
    previous: dict[str, Any] | None = None,
    new: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=auth.actor,
            previous_state=previous,
            new_state=new,
            reason=reason,
            ai_action=auth.ai_action,
        ),
    )


def _event(
    session: Session,
    actor: Actor,
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    project_id: UUID | None,
    payload: dict[str, Any],
) -> None:
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            payload=payload,
        ),
    )


# --- foundational library (FR-REFSRC-001..004) ---


def _foundational_out(source: FoundationalSource) -> FoundationalOut:
    approved_by = (
        Actor.model_validate(
            {"kind": source.approved_by_kind, "id": source.approved_by_id, "role": "CONSTITUTIONAL_AUTHORITY"}
        )
        if source.approved_by_kind
        else None
    )
    return FoundationalOut(
        id=source.id,
        work_id=source.work_id,
        authority_layer=L(source.authority_layer),
        edition_version=source.edition_version,
        status=FoundationalSourceStatus(source.status),
        sha256=source.sha256,
        dataset_summary=source.dataset_summary,
        approved_by=approved_by,
        approved_at=source.approved_at,
    )


def _foundational_work_layer(session: Session, work_id: UUID) -> L:
    work = sources.get_work(session, work_id)
    if work.authority_layer not in {L.QURAN, L.SUNNAH, L.APPROVED_FOUNDATIONAL}:
        raise RuleViolationError("only QURAN, SUNNAH or APPROVED_FOUNDATIONAL works belong in the foundational library")
    return work.authority_layer


def stage_foundational(session: Session, principal: Principal, data: FoundationalStageIn) -> FoundationalOut:
    auth = authorized(principal, "reference.stage_foundational")
    layer = _foundational_work_layer(session, data.work_id)
    if layer is L.QURAN:
        raise RuleViolationError("the Qur'an is staged by importing its structured text dataset")
    source = FoundationalSource(
        work_id=data.work_id,
        authority_layer=layer.value,
        edition_version=data.edition_version,
        status=FoundationalSourceStatus.STAGED.value,
        sha256=data.sha256,
        staged_by_id=auth.actor.id,
    )
    session.add(source)
    session.flush()
    _audit(
        session,
        auth,
        "reference.stage_foundational",
        "FoundationalSource",
        source.id,
        new={"work_id": str(data.work_id), "version": data.edition_version},
    )
    return _foundational_out(source)


def stage_quran_dataset(
    session: Session, principal: Principal, work_id: UUID, edition_version: str, data: bytes
) -> FoundationalOut:
    """Import a Qur'an text dataset supplied by the Constitutional Authority. Nothing is served until approved."""
    auth = authorized(principal, "reference.stage_foundational")
    if _foundational_work_layer(session, work_id) is not L.QURAN:
        raise RuleViolationError("the work must be catalogued in the QURAN authority layer")
    validate_upload(data, allowed=frozenset({"text/plain"}))
    try:
        parsed = quran_dataset.parse(data)
    except quran_dataset.DatasetError as exc:
        raise RuleViolationError(f"dataset rejected: {exc}") from exc
    source = FoundationalSource(
        work_id=work_id,
        authority_layer=L.QURAN.value,
        edition_version=edition_version,
        status=FoundationalSourceStatus.STAGED.value,
        sha256=parsed.sha256,
        staged_by_id=auth.actor.id,
        dataset_summary={"surahs": parsed.surah_count, "ayat": len(parsed.ayat), "format": parsed.format},
    )
    session.add(source)
    session.flush()
    session.execute(
        insert(QuranSurah),
        [{"source_id": source.id, "surah_number": n, "name": name} for n, name in sorted(parsed.surah_names.items())],
    )
    session.execute(
        insert(QuranAyah),
        [{"source_id": source.id, "surah_number": s, "ayah_number": a, "text": t} for s, a, t in parsed.ayat],
    )
    _audit(
        session,
        auth,
        "reference.stage_foundational",
        "FoundationalSource",
        source.id,
        new={"layer": "QURAN", "version": edition_version, "sha256": parsed.sha256, **source.dataset_summary},
    )
    return _foundational_out(source)


def approve_foundational(session: Session, principal: Principal, source_id: UUID, data: ApproveIn) -> FoundationalOut:
    """Explicit adoption by the Constitutional Authority (FR-REFSRC-003/004).

    Approving a Qur'an text retires the previously approved one.
    """
    auth = authorized(principal, "reference.approve_foundational")
    source = session.get(FoundationalSource, source_id, with_for_update=True)
    if source is None:
        raise NotFoundError("foundational source not found")
    if source.status != FoundationalSourceStatus.STAGED.value:
        raise ConflictError(f"source is {source.status}; only STAGED sources can be approved")
    if source.authority_layer == L.QURAN.value:
        previous = session.scalars(
            select(FoundationalSource)
            .where(
                FoundationalSource.authority_layer == L.QURAN.value,
                FoundationalSource.status == FoundationalSourceStatus.APPROVED.value,
            )
            .with_for_update()
        ).first()
        if previous is not None:
            previous.status = FoundationalSourceStatus.RETIRED.value
            session.flush()
    source.status = FoundationalSourceStatus.APPROVED.value
    source.approved_by_kind = auth.actor.kind.value
    source.approved_by_id = auth.actor.id
    source.approved_at = utcnow()
    _audit(
        session,
        auth,
        "reference.approve_foundational",
        "FoundationalSource",
        source.id,
        previous={"status": FoundationalSourceStatus.STAGED.value},
        new={"status": source.status, "sha256": source.sha256},
        reason=data.reason,
    )
    _event(
        session,
        auth.actor,
        "FoundationalSourceApproved",
        "FoundationalSource",
        source.id,
        None,
        {"layer": source.authority_layer, "version": source.edition_version},
    )
    session.flush()
    return _foundational_out(source)


def list_foundational(session: Session) -> list[FoundationalOut]:
    rows = session.scalars(select(FoundationalSource).order_by(FoundationalSource.created_at))
    return [_foundational_out(s) for s in rows]


def _approved_quran(session: Session) -> FoundationalSource:
    source = session.scalars(
        select(FoundationalSource).where(
            FoundationalSource.authority_layer == L.QURAN.value,
            FoundationalSource.status == FoundationalSourceStatus.APPROVED.value,
        )
    ).first()
    if source is None:
        raise NotFoundError(
            "no approved Qur'an source is configured; the Constitutional Authority must import and approve one"
        )
    return source


def get_ayat(session: Session, surah: int, first: int, last: int | None = None) -> list[AyahOut]:
    """Exact text from the approved dataset only (FR-QURAN-001/002)."""
    source = _approved_quran(session)
    last = first if last is None else last
    if last < first:
        raise RuleViolationError("ayah range is reversed")
    name = session.get(QuranSurah, (source.id, surah))
    rows = list(
        session.scalars(
            select(QuranAyah)
            .where(
                QuranAyah.source_id == source.id,
                QuranAyah.surah_number == surah,
                QuranAyah.ayah_number >= first,
                QuranAyah.ayah_number <= last,
            )
            .order_by(QuranAyah.ayah_number)
        )
    )
    if name is None or len(rows) != last - first + 1:
        raise NotFoundError(
            f"{surah}:{first}" + (f"-{last}" if last != first else "") + " is not in the approved source"
        )
    return [
        AyahOut(
            surah_number=surah,
            surah_name=name.name,
            ayah_number=r.ayah_number,
            text=r.text,
            source_id=source.id,
            source_version=source.edition_version,
            source_sha256=source.sha256,
        )
        for r in rows
    ]


def _parse_quran_ref(ref: str) -> tuple[int, int, int]:
    surah, ayat = ref.split(":")
    first, _, last = ayat.partition("-")
    return int(surah), int(first), int(last or first)


def add_hadith(session: Session, principal: Principal, source_id: UUID, data: HadithIn) -> HadithOut:
    auth = authorized(principal, "reference.enter_hadith")
    source = session.get(FoundationalSource, source_id)
    if source is None:
        raise NotFoundError("foundational source not found")
    if L(source.authority_layer) not in HADITH_LAYERS or source.status != FoundationalSourceStatus.APPROVED.value:
        raise RuleViolationError("hadith records belong to an APPROVED Sunnah or approved foundational source")
    record = HadithRecord(foundational_source_id=source.id, entered_by_id=auth.actor.id, **data.model_dump())
    try:
        with session.begin_nested():
            session.add(record)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError(
            f"number {data.number} already exists in numbering scheme '{data.numbering_scheme}' for this source"
        ) from exc
    _audit(
        session,
        auth,
        "reference.enter_hadith",
        "HadithRecord",
        record.id,
        new={"collection": record.collection, "number": record.number, "scheme": record.numbering_scheme},
    )
    return HadithOut.model_validate(record)


def get_hadith(session: Session, record_id: UUID) -> HadithOut:
    record = session.get(HadithRecord, record_id)
    if record is None:
        raise NotFoundError("hadith record not found")
    return HadithOut.model_validate(record)


# --- reference review (FR-REF-001..006) ---


def _review(session: Session, project_id: UUID, review_id: UUID) -> ReferenceReview:
    review = session.get(ReferenceReview, review_id)
    if review is None or review.project_id != project_id:
        raise NotFoundError("reference review not found")
    return review


def _judgment_out(record: ReferenceJudgmentRecord) -> JudgmentOut:
    return JudgmentOut(
        id=record.id,
        review_id=record.review_id,
        state=J(record.state),
        directness=Directness(record.directness),
        reservation_type=ReservationType(record.reservation_type) if record.reservation_type else None,
        divergence=Divergence.model_validate(record.divergence) if record.divergence else None,
        rationale=record.rationale,
        judged_by=Actor.model_validate(
            {"kind": record.judged_by_kind, "id": record.judged_by_id, "role": record.judged_by_role}
        ),
        decision_id=record.decision_id,
        created_at=record.created_at,
    )


def _review_out(session: Session, review: ReferenceReview) -> ReviewOut:
    entries = session.scalars(
        select(ReferenceEntry).where(ReferenceEntry.review_id == review.id).order_by(ReferenceEntry.created_at)
    )
    judgments = [
        _judgment_out(j)
        for j in session.scalars(
            select(ReferenceJudgmentRecord)
            .where(ReferenceJudgmentRecord.review_id == review.id)
            .order_by(ReferenceJudgmentRecord.created_at)
        )
    ]
    return ReviewOut(
        id=review.id,
        project_id=review.project_id,
        target_type=EvidenceTargetType(review.target_type),
        target_id=review.target_id,
        question=review.question,
        analytical_category=review.analytical_category,
        entries=[EntryOut.model_validate(e) for e in entries],
        judgments=judgments,
        current_judgment=judgments[-1] if judgments else None,
        created_at=review.created_at,
    )


def create_review(session: Session, principal: Principal, project_id: UUID, data: ReviewIn) -> ReviewOut:
    auth = authorized(principal, "reference.review_create")
    projects.require_editable_project(session, project_id)
    targets.require(session, project_id, data.target_type, data.target_id)
    review = ReferenceReview(
        project_id=project_id,
        target_type=data.target_type.value,
        target_id=data.target_id,
        question=data.question,
        analytical_category=data.analytical_category.value,
    )
    session.add(review)
    session.flush()
    _audit(
        session,
        auth,
        "reference.review_create",
        "ReferenceReview",
        review.id,
        project_id=project_id,
        new={
            "target_type": review.target_type,
            "target_id": str(review.target_id),
            "category": review.analytical_category,
        },
    )
    return _review_out(session, review)


def get_review(session: Session, project_id: UUID, review_id: UUID) -> ReviewOut:
    return _review_out(session, _review(session, project_id, review_id))


def list_reviews(
    session: Session, project_id: UUID, *, target_type: EvidenceTargetType | None = None, target_id: UUID | None = None
) -> list[ReviewOut]:
    query = select(ReferenceReview).where(ReferenceReview.project_id == project_id)
    if target_type is not None and target_id is not None:
        query = query.where(ReferenceReview.target_type == target_type.value, ReferenceReview.target_id == target_id)
    return [_review_out(session, r) for r in session.scalars(query.order_by(ReferenceReview.created_at))]


def _approved_foundational_works(session: Session) -> set[UUID]:
    return set(
        session.scalars(
            select(FoundationalSource.work_id).where(
                FoundationalSource.status == FoundationalSourceStatus.APPROVED.value
            )
        )
    )


def add_entry(
    session: Session,
    principal: Principal,
    project_id: UUID,
    review_id: UUID,
    data: EntryIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> EntryOut:
    auth = authorized(principal, "reference.entry_add", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    review = _review(session, project_id, review_id)
    layer = data.layer
    is_ai = principal.kind is ActorKind.AI
    if is_ai and layer is not ReferenceReasoningLayer.SYSTEM_SYNTHESIS:
        raise RuleViolationError(
            "AI contributions are SYSTEM_SYNTHESIS; they are never source text, approved "
            "interpretation or practical judgment (FR-REF-006)"
        )

    content = data.content
    if layer is ReferenceReasoningLayer.SOURCE_TEXT:
        refs = [r for r in (data.source_excerpt_id, data.quran_ref, data.hadith_record_id) if r is not None]
        if len(refs) != 1:
            raise RuleViolationError("source text must cite exactly one of: excerpt, Qur'an reference, hadith record")
        # Content is copied from the source itself, never typed (Core §29-31).
        if data.quran_ref is not None:
            surah, first, last = _parse_quran_ref(data.quran_ref)
            content = "\n".join(a.text for a in get_ayat(session, surah, first, last))
        elif data.hadith_record_id is not None:
            content = get_hadith(session, data.hadith_record_id).exact_text
        elif data.source_excerpt_id is not None:
            content = sources.get_excerpt(session, data.source_excerpt_id).text
    elif layer is ReferenceReasoningLayer.APPROVED_INTERPRETATION:
        if data.source_excerpt_id is None:
            raise RuleViolationError("an approved interpretation must cite an excerpt from an approved source")
        work = sources.work_ids_for_excerpts(session, [data.source_excerpt_id]).get(data.source_excerpt_id)
        if work is None or work not in _approved_foundational_works(session):
            raise RuleViolationError(
                "the cited interpretation source is not approved in the foundational library; "
                "record it as SYSTEM_SYNTHESIS or have it approved first"
            )
    if not content or not content.strip():
        raise RuleViolationError("entry content is required")

    kind = (
        ProvenanceKind.AI_GENERATED
        if is_ai
        else (
            ProvenanceKind.SOURCE_DERIVED
            if layer is ReferenceReasoningLayer.SOURCE_TEXT
            else ProvenanceKind.HUMAN_INPUT
        )
    )
    provenance: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if ai_action is not None:
        provenance["ai_action"] = ai_action.model_dump(mode="json", exclude_none=True)
    entry = ReferenceEntry(
        review_id=review.id,
        layer=layer.value,
        content=content,
        source_excerpt_id=data.source_excerpt_id,
        quran_ref=data.quran_ref,
        hadith_record_id=data.hadith_record_id,
        provenance=provenance,
    )
    session.add(entry)
    session.flush()
    _audit(
        session,
        auth,
        "reference.entry_add",
        "ReferenceEntry",
        entry.id,
        project_id=project_id,
        new={"layer": entry.layer, "review_id": str(review.id)},
    )
    return EntryOut.model_validate(entry)


SOURCED_LAYERS = {ReferenceReasoningLayer.SOURCE_TEXT.value, ReferenceReasoningLayer.APPROVED_INTERPRETATION.value}


def judge(session: Session, principal: Principal, project_id: UUID, review_id: UUID, data: JudgmentIn) -> JudgmentOut:
    """Human reference judgment (FR-REF-002..005). Earlier judgments remain as history."""
    auth = authorized(principal, "reference.judge")
    projects.require_editable_project(session, project_id)
    review = _review(session, project_id, review_id)
    layers = set(session.scalars(select(ReferenceEntry.layer).where(ReferenceEntry.review_id == review.id)))
    if data.state is J.REFERENCE_SUPPORTED:
        if ReferenceReasoningLayer.SOURCE_TEXT.value not in layers:
            raise RuleViolationError(
                "REFERENCE_SUPPORTED requires cited source text; absence of conflict is "
                "NOT_IN_CONFLICT, not support (Core §8)"
            )
        if data.directness not in {Directness.DIRECT, Directness.CLOSE}:
            raise RuleViolationError("REFERENCE_SUPPORTED requires DIRECT or CLOSE grounding")
    if data.state is J.REFERENCE_CONSISTENT and not layers & SOURCED_LAYERS:
        raise RuleViolationError("REFERENCE_CONSISTENT requires source text or an approved interpretation")
    if (data.state is J.RESERVED) != (data.reservation_type is not None):
        raise RuleViolationError("a reservation type is required exactly when the judgment is RESERVED")
    if data.divergence is not None and data.state is not J.RESERVED:
        raise RuleViolationError("interpretation divergence must be recorded as RESERVED until resolved (Core §9)")

    actor = auth.actor
    decision_id = None
    if data.reservation_type is ReservationType.BLOCKING_RESERVATION:
        # Created before the append-only judgment row so the link is written once.
        decision = governance.create_decision(
            session,
            system_principal("reference_governance"),
            project_id,
            DecisionCreate(
                question=f"Blocking reference reservation: {review.question}",
                options=["Lift the reservation", "Keep the reservation", "Require modification of the proposal"],
                rationale=data.rationale,
                required_role=data.divergence.required_authority if data.divergence else ActorRole.PROJECT_LEAD,
                blocking=True,
                subject_type="ReferenceReview",
                subject_id=review.id,
            ),
        )
        decision_id = decision.id
    record = ReferenceJudgmentRecord(
        review_id=review.id,
        state=data.state.value,
        directness=data.directness.value,
        reservation_type=data.reservation_type.value if data.reservation_type else None,
        divergence=data.divergence.model_dump(mode="json") if data.divergence else None,
        rationale=data.rationale,
        judged_by_kind=actor.kind.value,
        judged_by_id=actor.id,
        judged_by_role=actor.role.value if actor.role else None,
        decision_id=decision_id,
    )
    session.add(record)
    session.flush()
    if decision_id is not None:
        _event(
            session,
            actor,
            "ReferenceReservationRaised",
            "ReferenceReview",
            review.id,
            project_id,
            {"judgment_id": str(record.id), "decision_id": str(decision_id), "divergence": data.divergence is not None},
        )
    _audit(
        session,
        auth,
        "reference.judge",
        "ReferenceJudgment",
        record.id,
        project_id=project_id,
        new={"state": record.state, "directness": record.directness, "reservation": record.reservation_type},
        reason=data.rationale,
    )
    _event(
        session,
        actor,
        "ReferenceJudgmentRecorded",
        "ReferenceReview",
        review.id,
        project_id,
        {"state": record.state, "target_type": review.target_type, "target_id": str(review.target_id)},
    )
    session.flush()
    return _judgment_out(record)


# --- Reference Gate (Core §60) ---

RISK_WITHOUT_REVIEW = {
    RiskLevel.L1_EXPLORATORY: QualityGateResult.PASS_WITH_RESERVATIONS,
    RiskLevel.L2_APPLIED: QualityGateResult.NEEDS_HUMAN_DECISION,
    RiskLevel.L3_HIGH_IMPACT: QualityGateResult.BLOCKED,
    RiskLevel.L4_CRITICAL: QualityGateResult.BLOCKED,
}
_SEVERITY = [
    QualityGateResult.BLOCKED,
    QualityGateResult.NEEDS_HUMAN_DECISION,
    QualityGateResult.PASS_WITH_RESERVATIONS,
    QualityGateResult.PASS,
]


def reference_standing(
    session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID, *, record: bool = False
) -> ReferenceStanding:
    """Reference Gate for a target: judged from the latest judgment of each review (risk-aware)."""
    project = projects.get_project(session, project_id)
    risk = RiskLevel(project.risk_level)
    reviews = list_reviews(session, project_id, target_type=target_type, target_id=target_id)
    latest = [r.current_judgment for r in reviews if r.current_judgment is not None]
    findings: list[GateFinding] = []
    if not latest:
        findings.append(
            GateFinding(
                code="reference.not_reviewed",
                severity=RISK_WITHOUT_REVIEW[risk],
                message="No reference judgment has been recorded.",
            )
        )
    for judgment in latest:
        if judgment.state is J.REJECTED:
            findings.append(
                GateFinding(
                    code="reference.rejected",
                    severity=QualityGateResult.BLOCKED,
                    message=f"Reference judgment REJECTED: {judgment.rationale}",
                )
            )
        elif judgment.state is J.RESERVED and judgment.reservation_type is ReservationType.BLOCKING_RESERVATION:
            findings.append(
                GateFinding(
                    code="reference.blocking_reservation",
                    severity=QualityGateResult.BLOCKED,
                    message=f"Blocking reservation: {judgment.rationale}",
                )
            )
        elif judgment.state is J.REQUIRES_MODIFICATION:
            findings.append(
                GateFinding(
                    code="reference.requires_modification",
                    severity=QualityGateResult.NEEDS_HUMAN_DECISION,
                    message=f"Requires modification: {judgment.rationale}",
                )
            )
        elif judgment.state is J.RESERVED:
            findings.append(
                GateFinding(
                    code="reference.non_blocking_reservation",
                    severity=QualityGateResult.PASS_WITH_RESERVATIONS,
                    message=f"Non-blocking reservation: {judgment.rationale}",
                )
            )
    result = next((s for s in _SEVERITY if any(f.severity is s for f in findings)), QualityGateResult.PASS)
    gate = None
    if record:
        gate = governance.record_gate_evaluation(
            session,
            gate=QualityGateType.REFERENCE,
            result=result,
            risk_level=risk,
            findings=findings,
            project_id=project_id,
            subject_type=target_type.value,
            subject_id=target_id,
        )
    return ReferenceStanding(
        result=result, findings=[f.model_dump(mode="json") for f in findings], latest_judgments=latest, gate=gate
    )


def quran_text(session: Session, ref: str) -> str:
    """Exact approved text for a reference like '2:255' or '1:1-7' (for protected quotes in outputs)."""
    surah, first, last = _parse_quran_ref(ref)
    return "\n".join(a.text for a in get_ayat(session, surah, first, last))


def hadith_text(session: Session, record_id: UUID) -> str:
    return get_hadith(session, record_id).exact_text
