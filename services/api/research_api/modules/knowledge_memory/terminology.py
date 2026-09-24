"""Canonical terminology (FR-TERM-001/002) and the translation integrity check (FR-TERM-003), Core §53.

Terms are library-wide and versioned; content is never edited. Anyone, including the AI,
may propose a term or a revision, but only a human with the Methodology Steward or
Constitutional Authority role approves the canonical form. Approving a version supersedes
the previously approved version of the same series.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind, LanguageCode, ProvenanceKind, TermStatus
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry
from research_api.modules.knowledge_memory import claim_strength as strength
from research_api.modules.knowledge_memory.models import Term
from research_api.modules.knowledge_memory.terminology_schemas import (
    DriftOut,
    StrengthProfileOut,
    TermDecision,
    TermFinding,
    TermIn,
    TermOut,
    TermRevision,
    TranslationCheckIn,
    TranslationCheckOut,
)
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError

S = TermStatus
ENTITY = "Term"


def _audit(
    session: Session,
    auth: Authorized,
    action: str,
    term: Term,
    new: dict[str, Any],
    *,
    previous: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            action=action,
            entity_type=ENTITY,
            entity_id=term.id,
            actor=auth.actor,
            previous_state=previous,
            new_state=new,
            reason=reason,
            ai_action=auth.ai_action,
        ),
    )


def _provenance(auth: Authorized) -> dict[str, Any]:
    kind = ProvenanceKind.AI_GENERATED if auth.principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    data: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        data["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    return data


def _content(data: TermIn) -> dict[str, Any]:
    return {
        "term": data.term,
        "original_language": data.original_language.value,
        "domain": data.domain,
        "definition": data.definition,
        "translations": data.translations.model_dump(exclude_none=True),
        "alternatives": [a.model_dump(mode="json", exclude_none=True) for a in data.alternatives],
        "retain_original": data.retain_original,
        "source_authority": data.source_authority,
    }


def _load(session: Session, term_id: UUID, *, lock: bool = False) -> Term:
    term = session.get(Term, term_id, with_for_update=lock)
    if term is None:
        raise NotFoundError("term not found")
    return term


def propose_term(
    session: Session, principal: Principal, data: TermIn, *, ai_action: AIActionRecord | None = None
) -> TermOut:
    auth = authorized(principal, "term.propose", ai_action=ai_action)
    term = Term(
        series_id=uuid4(),
        version_number=1,
        status=S.PROPOSED.value,
        provenance=_provenance(auth),
        **_content(data),
    )
    session.add(term)
    session.flush()
    _audit(session, auth, "term.propose", term, {"term": term.term, "domain": term.domain})
    return TermOut.model_validate(term)


def revise_term(session: Session, principal: Principal, term_id: UUID, data: TermRevision) -> TermOut:
    """Append a PROPOSED version; the approved version stays canonical until the new one is approved."""
    auth = authorized(principal, "term.revise")
    base = _load(session, term_id, lock=True)
    series = list(
        session.scalars(
            select(Term).where(Term.series_id == base.series_id).order_by(Term.version_number).with_for_update()
        )
    )
    for pending in (t for t in series if t.status == S.PROPOSED.value):
        pending.status = S.SUPERSEDED.value
    session.flush()
    term = Term(
        series_id=base.series_id,
        version_number=series[-1].version_number + 1,
        supersedes_id=base.id,
        status=S.PROPOSED.value,
        change_reason=data.change_reason,
        provenance=_provenance(auth),
        **_content(data),
    )
    session.add(term)
    session.flush()
    _audit(session, auth, "term.revise", term, {"version": term.version_number}, reason=data.change_reason)
    return TermOut.model_validate(term)


def _decide(session: Session, principal: Principal, term_id: UUID, data: TermDecision, approve: bool) -> TermOut:
    action = "term.approve" if approve else "term.reject"
    auth = authorized(principal, action)
    term = _load(session, term_id, lock=True)
    if term.status != S.PROPOSED.value:
        raise ConflictError(f"only PROPOSED terms can be decided; this one is {term.status}")
    if approve:
        current = session.scalars(
            select(Term).where(Term.series_id == term.series_id, Term.status == S.APPROVED.value).with_for_update()
        ).first()
        if current is not None:
            current.status = S.SUPERSEDED.value
            session.flush()
        term.approved_by = auth.actor.model_dump(mode="json", exclude_none=True)
        term.approved_at = utcnow()
    term.status = (S.APPROVED if approve else S.REJECTED).value
    session.flush()
    _audit(
        session, auth, action, term, {"status": term.status}, previous={"status": S.PROPOSED.value}, reason=data.reason
    )
    return TermOut.model_validate(term)


def approve_term(session: Session, principal: Principal, term_id: UUID, data: TermDecision) -> TermOut:
    return _decide(session, principal, term_id, data, approve=True)


def reject_term(session: Session, principal: Principal, term_id: UUID, data: TermDecision) -> TermOut:
    return _decide(session, principal, term_id, data, approve=False)


def list_terms(
    session: Session, *, domain: str | None = None, status: TermStatus | None = None, include_history: bool = False
) -> list[TermOut]:
    query = select(Term).order_by(Term.domain, Term.term, Term.version_number)
    if domain:
        query = query.where(Term.domain == domain)
    if status is not None:
        query = query.where(Term.status == status.value)
    elif not include_history:
        query = query.where(Term.status.in_([S.PROPOSED.value, S.APPROVED.value]))
    return [TermOut.model_validate(t) for t in session.scalars(query)]


def term_history(session: Session, term_id: UUID) -> list[TermOut]:
    series_id = _load(session, term_id).series_id
    rows = session.scalars(select(Term).where(Term.series_id == series_id).order_by(Term.version_number))
    return [TermOut.model_validate(t) for t in rows]


# --- translation integrity (FR-TERM-003, FR-OUT-002 steps 5-6) ---


def _profile_out(p: strength.Profile) -> StrengthProfileOut:
    return StrengthProfileOut(relation=p.relation, certainty=p.certainty, scope=p.scope, markers=p.markers)


def _contains(text: str, phrase: str, language: LanguageCode) -> bool:
    return strength.normalise(phrase, language).strip() in text


def _term_findings(session: Session, data: TranslationCheckIn) -> list[TermFinding]:
    source = strength.normalise(data.source_text, data.source_language)
    target = strength.normalise(data.translated_text, data.target_language)
    findings = []
    for term in list_terms(session, domain=data.domain, status=S.APPROVED):
        source_form = getattr(term.translations, data.source_language.value)
        if not source_form or not _contains(source, source_form, data.source_language):
            continue
        expected = [getattr(term.translations, data.target_language.value)]
        expected += [a.text for a in term.alternatives if a.language is data.target_language]
        if term.retain_original:
            expected.append(term.term)
        expected = [e for e in expected if e]
        found = any(_contains(target, e, data.target_language) for e in expected)
        message = (
            "Uses an approved rendering."
            if found
            else "The approved term is not rendered with an approved translation"
            + (" or kept in the original." if term.retain_original else ".")
        )
        findings.append(
            TermFinding(
                term_id=term.id,
                term=term.term,
                source_form=source_form,
                expected=expected,
                found=found,
                message=message,
            )
        )
    return findings


def check_translation(session: Session, data: TranslationCheckIn) -> TranslationCheckOut:
    source = strength.profile(data.source_text, data.source_language)
    translation = strength.profile(data.translated_text, data.target_language)
    drifts = strength.compare(source, translation)
    terms = _term_findings(session, data)
    return TranslationCheckOut(
        source_profile=_profile_out(source),
        translation_profile=_profile_out(translation),
        strength_drift=[DriftOut(**d.__dict__) for d in drifts],
        terminology=terms,
        passed=not drifts and all(t.found for t in terms),
    )
