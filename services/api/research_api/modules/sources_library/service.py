"""Public service for the source library and Hybrid Source Access.

Trust never rises implicitly: catalogued editions start METADATA_ONLY; only an
explicit, audited human reverification changes an edition's verification state
(FR-SRC-007/008); access responses carry the verification of their actual
access method (FR-HYBRID-004).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    AccessResponseForm,
    IngestionStatus,
    ProjectStatus,
    ProvenanceKind,
    SourceAccessMode,
    SourceAccessRequestStatus,
    SourceAssetKind,
    SourceLeadOrigin,
    SourceLeadState,
    SourceVerificationState,
    TextOrigin,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.project_workflow import lifecycle
from research_api.modules.project_workflow import service as projects
from research_api.modules.sources_library import rules
from research_api.modules.sources_library.models import (
    ProjectSource,
    SourceAccessRequest,
    SourceAsset,
    SourceChunk,
    SourceEdition,
    SourceExcerpt,
    SourceLead,
    SourcePage,
    SourceWork,
)
from research_api.modules.sources_library.schemas import (
    AccessRequestIn,
    AccessRequestOut,
    AccessResponseOut,
    AssetOut,
    CatalogIn,
    EditionOut,
    ExcerptOut,
    PageExcerptIn,
    ReverifyIn,
    SearchHit,
    SearchResponse,
    SourceLeadIn,
    SourceLeadOut,
    TextResponseIn,
    WorkOut,
)
from research_api.platform import jobs
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError
from research_api.platform.storage import get_store, safe_filename, validate_upload

INGEST_TASK = "sources.ingest_asset"
TEXT_BEARING = frozenset({SourceAssetKind.PDF, SourceAssetKind.LOCAL_TEXT})


def _audit(
    session: Session,
    auth: Authorized,
    action: str,
    *,
    entity_type: str,
    entity_id: UUID,
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
    auth: Authorized,
    event_type: str,
    *,
    entity_type: str,
    entity_id: UUID,
    project_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=auth.actor,
            payload=payload or {},
        ),
    )


def _editable_project(session: Session, project_id: UUID) -> None:
    project = projects.get_project(session, project_id)
    if ProjectStatus(project.status) not in lifecycle.EDITABLE:
        raise ConflictError(f"project is {project.status}; sources cannot be changed in this status")


# --- read models ---


def _asset_out(asset: SourceAsset) -> AssetOut:
    return AssetOut.model_validate(asset)


def _edition_out(session: Session, edition: SourceEdition) -> EditionOut:
    assets = list(
        session.scalars(
            select(SourceAsset).where(SourceAsset.edition_id == edition.id).order_by(SourceAsset.created_at)
        )
    )
    return EditionOut.model_validate(
        {
            **{c: getattr(edition, c) for c in EditionOut.model_fields if c not in {"assets", "available"}},
            "assets": [_asset_out(a) for a in assets],
            "available": any(a.available_in_environment for a in assets),
        }
    )


def _work_out(session: Session, work: SourceWork) -> WorkOut:
    editions = session.scalars(
        select(SourceEdition).where(SourceEdition.work_id == work.id).order_by(SourceEdition.created_at)
    )
    return WorkOut(
        id=work.id,
        title=work.title,
        authors=work.authors,
        original_language=work.original_language,
        authority_layer=work.authority_layer,
        identifiers=work.identifiers,
        editions=[_edition_out(session, e) for e in editions],
        created_at=work.created_at,
    )


def get_work(session: Session, work_id: UUID) -> WorkOut:
    work = session.get(SourceWork, work_id)
    if work is None:
        raise NotFoundError("source work not found")
    return _work_out(session, work)


def list_works(session: Session, *, project_id: UUID | None = None) -> list[WorkOut]:
    query = select(SourceWork).order_by(SourceWork.created_at.desc())
    if project_id is not None:
        query = query.join(ProjectSource, ProjectSource.work_id == SourceWork.id).where(
            ProjectSource.project_id == project_id
        )
    return [_work_out(session, w) for w in session.scalars(query)]


def _edition(session: Session, edition_id: UUID, *, lock: bool = False) -> SourceEdition:
    edition = session.get(SourceEdition, edition_id, with_for_update=lock)
    if edition is None:
        raise NotFoundError("source edition not found")
    return edition


def get_edition(session: Session, edition_id: UUID) -> EditionOut:
    return _edition_out(session, _edition(session, edition_id))


# --- catalog (FR-SRC-001..004) ---


def catalog(session: Session, principal: Principal, data: CatalogIn) -> WorkOut:
    """Catalog a work and edition; optionally record a non-digital holding and link to a project."""
    foundational = data.work.authority_layer in rules.FOUNDATIONAL_LAYERS
    # AI may never adopt foundational sources (FR-REFSRC-002).
    auth = authorized(principal, "source.catalog_foundational" if foundational else "source.catalog")
    if data.project_id is not None:
        _editable_project(session, data.project_id)

    work = SourceWork(
        title=data.work.title,
        authors=data.work.authors,
        original_language=data.work.original_language,
        authority_layer=data.work.authority_layer.value,
        identifiers=[i.model_dump() for i in data.work.identifiers],
        created_by_id=auth.actor.id,
    )
    session.add(work)
    session.flush()
    edition = SourceEdition(
        work_id=work.id,
        **data.edition.model_dump(exclude={"identifiers"}),
        identifiers=[i.model_dump() for i in data.edition.identifiers],
        verification_state=SourceVerificationState.METADATA_ONLY.value,
    )
    session.add(edition)
    session.flush()
    if data.holding is not None:
        session.add(
            SourceAsset(
                edition_id=edition.id,
                kind=SourceAssetKind.OTHER.value,
                access_mode=data.holding.access_mode,
                available_in_environment=False,
                holding_note=data.holding.note,
                ingestion_status=IngestionStatus.NOT_APPLICABLE.value,
            )
        )
    _audit(
        session,
        auth,
        "source.catalog",
        entity_type="SourceWork",
        entity_id=work.id,
        project_id=data.project_id,
        new={
            "title": work.title,
            "authority_layer": work.authority_layer,
            "edition_id": str(edition.id),
            "holding": data.holding.access_mode if data.holding else None,
        },
    )
    if data.project_id is not None:
        _link(session, auth, data.project_id, work.id)
    session.flush()
    return _work_out(session, work)


def _link(session: Session, auth: Authorized, project_id: UUID, work_id: UUID) -> None:
    if session.get(ProjectSource, (project_id, work_id)) is None:
        session.add(ProjectSource(project_id=project_id, work_id=work_id, added_by_id=auth.actor.id))
        _event(
            session, auth, "SourceAddedToProject", entity_type="SourceWork", entity_id=work_id, project_id=project_id
        )


def link_to_project(session: Session, principal: Principal, project_id: UUID, work_id: UUID) -> WorkOut:
    auth = authorized(principal, "source.catalog")
    _editable_project(session, project_id)
    work = session.get(SourceWork, work_id)
    if work is None:
        raise NotFoundError("source work not found")
    _link(session, auth, project_id, work_id)
    session.flush()
    return _work_out(session, work)


# --- assets ---


def _store_asset(
    session: Session,
    *,
    edition_id: UUID,
    data: bytes,
    filename: str | None,
    kind: SourceAssetKind | None,
    access_mode: SourceAccessMode,
    access_request_id: UUID | None = None,
) -> tuple[SourceAsset, UUID | None]:
    media_type = validate_upload(data)
    stored = get_store().put(data)
    asset_kind = kind or rules.kind_for_media(media_type)
    ingest = asset_kind in TEXT_BEARING
    asset = SourceAsset(
        edition_id=edition_id,
        kind=asset_kind.value,
        access_mode=access_mode.value,
        available_in_environment=True,
        sha256=stored.sha256,
        media_type=media_type,
        byte_size=stored.byte_size,
        storage_key=stored.key,
        original_filename=safe_filename(filename),
        text_origin=TextOrigin.NATIVE_DIGITAL.value if ingest else None,
        ingestion_status=(IngestionStatus.QUEUED if ingest else IngestionStatus.NOT_APPLICABLE).value,
        access_request_id=access_request_id,
    )
    session.add(asset)
    session.flush()
    job_id = None
    if ingest:
        job = jobs.create_job(session, INGEST_TASK, params={"asset_id": str(asset.id)})
        asset.ingestion_job_id = job.id
        job_id = job.id
    return asset, job_id


def upload_asset(
    session: Session, principal: Principal, edition_id: UUID, data: bytes, filename: str | None
) -> tuple[AssetOut, UUID | None]:
    """Store a digital asset. Returns the asset and the ingestion job to dispatch after commit.

    Uploading makes content available; it does not raise the edition's verification (FR-SRC-008).
    """
    auth = authorized(principal, "source.upload_asset")
    _edition(session, edition_id)
    asset, job_id = _store_asset(
        session,
        edition_id=edition_id,
        data=data,
        filename=filename,
        kind=None,
        access_mode=SourceAccessMode.DIRECT_DIGITAL,
    )
    _audit(
        session,
        auth,
        "source.upload_asset",
        entity_type="SourceAsset",
        entity_id=asset.id,
        new={"sha256": asset.sha256, "media_type": asset.media_type, "byte_size": asset.byte_size},
    )
    return _asset_out(asset), job_id


def get_asset(session: Session, asset_id: UUID) -> AssetOut:
    asset = session.get(SourceAsset, asset_id)
    if asset is None:
        raise NotFoundError("source asset not found")
    return _asset_out(asset)


def record_dispatch_failure(session: Session, asset_id: UUID, job_id: UUID, error: str) -> None:
    job = jobs.get_job(session, job_id, for_update=True)
    jobs.transition(job, jobs.JobState.FAILED, failure_kind=jobs.JobFailureKind.DISPATCH_FAILURE, error=error)
    asset = session.get(SourceAsset, asset_id)
    if asset is not None:
        asset.ingestion_status = IngestionStatus.FAILED.value


def reverify_edition(session: Session, principal: Principal, edition_id: UUID, data: ReverifyIn) -> EditionOut:
    """Explicit ReverificationEvent: the only way an edition's verification changes (FR-SRC-008)."""
    auth = authorized(principal, "source.reverify")
    edition = _edition(session, edition_id, lock=True)
    previous = edition.verification_state
    if previous == data.verification_state.value:
        raise ConflictError(f"edition is already {previous}")
    edition.verification_state = data.verification_state.value
    _audit(
        session,
        auth,
        "source.reverify",
        entity_type="SourceEdition",
        entity_id=edition.id,
        previous={"verification_state": previous},
        new={"verification_state": edition.verification_state, "method": data.method},
        reason=data.reason,
    )
    _event(
        session,
        auth,
        "SourceReverified",
        entity_type="SourceEdition",
        entity_id=edition.id,
        payload={"from": previous, "to": edition.verification_state, "method": data.method},
    )
    session.flush()
    return _edition_out(session, edition)


def list_excerpts(session: Session, edition_id: UUID) -> list[ExcerptOut]:
    _edition(session, edition_id)
    rows = session.scalars(
        select(SourceExcerpt).where(SourceExcerpt.edition_id == edition_id).order_by(SourceExcerpt.created_at)
    )
    return [ExcerptOut.model_validate(r) for r in rows]


# --- Hybrid Source Access (FR-HYBRID-001..004) ---


def create_access_request(
    session: Session, principal: Principal, project_id: UUID, data: AccessRequestIn
) -> AccessRequestOut:
    auth = authorized(principal, "source_access_request.create")
    _editable_project(session, project_id)
    edition = _edition(session, data.edition_id)
    request = SourceAccessRequest(
        project_id=project_id,
        edition_id=edition.id,
        reason=data.reason,
        requested_scope=data.requested_scope,
        surrounding_context=data.surrounding_context,
        acceptable_forms=[f.value for f in data.acceptable_forms],
        priority=data.priority.value,
        status=SourceAccessRequestStatus.OPEN.value,
        created_by_kind=auth.actor.kind.value,
        created_by_id=auth.actor.id,
    )
    session.add(request)
    session.flush()
    _link(session, auth, project_id, edition.work_id)
    _audit(
        session,
        auth,
        "source_access_request.create",
        entity_type="SourceAccessRequest",
        entity_id=request.id,
        project_id=project_id,
        new={"edition_id": str(edition.id), "scope": data.requested_scope, "forms": request.acceptable_forms},
    )
    _event(
        session,
        auth,
        "SourceAccessRequested",
        entity_type="SourceAccessRequest",
        entity_id=request.id,
        project_id=project_id,
        payload={"edition_id": str(edition.id), "priority": request.priority},
    )
    session.flush()
    return AccessRequestOut.model_validate(request)


def list_access_requests(
    session: Session, project_id: UUID, *, status: SourceAccessRequestStatus | None = None
) -> list[AccessRequestOut]:
    query = select(SourceAccessRequest).where(SourceAccessRequest.project_id == project_id)
    if status is not None:
        query = query.where(SourceAccessRequest.status == status.value)
    return [AccessRequestOut.model_validate(r) for r in session.scalars(query.order_by(SourceAccessRequest.created_at))]


def _open_request(session: Session, project_id: UUID, request_id: UUID) -> SourceAccessRequest:
    request = session.get(SourceAccessRequest, request_id, with_for_update=True)
    if request is None or request.project_id != project_id:
        raise NotFoundError("access request not found")
    if request.status not in {
        SourceAccessRequestStatus.OPEN.value,
        SourceAccessRequestStatus.PARTIALLY_FULFILLED.value,
    }:
        raise ConflictError(f"access request is {request.status}")
    return request


def _check_form(request: SourceAccessRequest, form: AccessResponseForm) -> None:
    if form.value not in request.acceptable_forms:
        raise RuleViolationError(f"{form.value} is not an accepted response form for this request")


def _after_response(
    session: Session,
    auth: Authorized,
    request: SourceAccessRequest,
    form: AccessResponseForm,
    fulfills: bool,
    **ids: str,
) -> None:
    previous = request.status
    request.status = (
        SourceAccessRequestStatus.FULFILLED if fulfills else SourceAccessRequestStatus.PARTIALLY_FULFILLED
    ).value
    _audit(
        session,
        auth,
        "source_access_request.respond",
        entity_type="SourceAccessRequest",
        entity_id=request.id,
        project_id=request.project_id,
        previous={"status": previous},
        new={"status": request.status, "form": form.value, **ids},
    )
    _event(
        session,
        auth,
        "SourceAccessResponded",
        entity_type="SourceAccessRequest",
        entity_id=request.id,
        project_id=request.project_id,
        payload={"form": form.value, **ids},
    )


def respond_with_text(
    session: Session, principal: Principal, project_id: UUID, request_id: UUID, data: TextResponseIn
) -> AccessResponseOut:
    auth = authorized(principal, "source_access_request.respond")
    request = _open_request(session, project_id, request_id)
    form = AccessResponseForm(data.form)
    _check_form(request, form)
    trust = rules.trust_for_text_response(form)
    excerpt = SourceExcerpt(
        edition_id=request.edition_id,
        location=data.location,
        text=data.text,
        language=data.language,
        text_origin=trust.text_origin.value,
        verification_state=trust.verification.value,
        is_exact_quote=trust.is_exact_quote,
        access_request_id=request.id,
        provenance={
            "kind": ProvenanceKind.HUMAN_INPUT.value,
            "actor": auth.actor.model_dump(mode="json", exclude_none=True),
        },
    )
    session.add(excerpt)
    session.flush()
    _after_response(session, auth, request, form, data.fulfills_request, excerpt_id=str(excerpt.id))
    session.flush()
    return AccessResponseOut(
        request=AccessRequestOut.model_validate(request), excerpt=ExcerptOut.model_validate(excerpt)
    )


def respond_with_file(
    session: Session,
    principal: Principal,
    project_id: UUID,
    request_id: UUID,
    *,
    form: AccessResponseForm,
    data: bytes,
    filename: str | None,
    fulfills: bool,
) -> tuple[AccessResponseOut, UUID | None]:
    auth = authorized(principal, "source_access_request.respond")
    if form not in rules.FILE_FORMS:
        raise RuleViolationError(f"{form.value} is not a file response form")
    request = _open_request(session, project_id, request_id)
    _check_form(request, form)
    media_type = validate_upload(data)
    kind, mode = rules.asset_for_file_response(form, media_type)
    asset, job_id = _store_asset(
        session,
        edition_id=request.edition_id,
        data=data,
        filename=filename,
        kind=kind,
        access_mode=mode,
        access_request_id=request.id,
    )
    _after_response(session, auth, request, form, fulfills, asset_id=str(asset.id))
    session.flush()
    return AccessResponseOut(request=AccessRequestOut.model_validate(request), asset=_asset_out(asset)), job_id


def cancel_access_request(
    session: Session, principal: Principal, project_id: UUID, request_id: UUID, reason: str
) -> AccessRequestOut:
    auth = authorized(principal, "source_access_request.cancel")
    request = _open_request(session, project_id, request_id)
    previous = request.status
    request.status = SourceAccessRequestStatus.CANCELLED.value
    _audit(
        session,
        auth,
        "source_access_request.cancel",
        entity_type="SourceAccessRequest",
        entity_id=request.id,
        project_id=project_id,
        previous={"status": previous},
        new={"status": request.status},
        reason=reason,
    )
    session.flush()
    return AccessRequestOut.model_validate(request)


# --- Source leads (Core §27) ---


def create_lead(session: Session, principal: Principal, project_id: UUID, data: SourceLeadIn) -> SourceLeadOut:
    auth = authorized(principal, "source_lead.create")
    _editable_project(session, project_id)
    lead = SourceLead(
        project_id=project_id,
        statement=data.statement,
        suspected_author=data.suspected_author,
        suspected_work_id=data.suspected_work_id,
        status=SourceLeadState.SOURCE_LEAD.value,
        created_by_id=auth.actor.id,
    )
    session.add(lead)
    session.flush()
    _audit(
        session,
        auth,
        "source_lead.create",
        entity_type="SourceLead",
        entity_id=lead.id,
        project_id=project_id,
        new={"statement": lead.statement},
    )
    return SourceLeadOut.model_validate(lead)


def create_web_lead(
    session: Session,
    principal: Principal,
    project_id: UUID,
    *,
    url: str,
    title: str,
    query: str | None,
    search_record_id: UUID,
    ai_action: AIActionRecord | None = None,
) -> SourceLeadOut | None:
    """A web result becomes a lead to catalogue and verify, never evidence (FR-WEB-003). None if already a lead."""
    auth = authorized(principal, "source_lead.create", ai_action=ai_action)
    _editable_project(session, project_id)
    existing = session.scalar(
        select(SourceLead.id).where(
            SourceLead.project_id == project_id,
            SourceLead.url == url,
            SourceLead.status == SourceLeadState.SOURCE_LEAD.value,
        )
    )
    if existing is not None:
        return None
    lead = SourceLead(
        project_id=project_id,
        statement=f"Web result for “{query}”: {title}" if query else f"Web result: {title}",
        status=SourceLeadState.SOURCE_LEAD.value,
        created_by_id=auth.actor.id,
        origin=SourceLeadOrigin.WEB_SEARCH.value,
        url=url,
        title=title,
        search_record_id=search_record_id,
        provenance={
            "kind": ProvenanceKind.SOURCE_DERIVED.value,
            "actor": auth.actor.model_dump(mode="json", exclude_none=True),
            **({"ai_action": ai_action.model_dump(mode="json", exclude_none=True)} if ai_action else {}),
        },
    )
    session.add(lead)
    session.flush()
    _audit(
        session,
        auth,
        "source_lead.create",
        entity_type="SourceLead",
        entity_id=lead.id,
        project_id=project_id,
        new={"origin": lead.origin, "url": url},
    )
    return SourceLeadOut.model_validate(lead)


def list_leads(session: Session, project_id: UUID) -> list[SourceLeadOut]:
    rows = session.scalars(
        select(SourceLead).where(SourceLead.project_id == project_id).order_by(SourceLead.created_at)
    )
    return [SourceLeadOut.model_validate(r) for r in rows]


def _open_lead(session: Session, project_id: UUID, lead_id: UUID) -> SourceLead:
    lead = session.get(SourceLead, lead_id, with_for_update=True)
    if lead is None or lead.project_id != project_id:
        raise NotFoundError("source lead not found")
    if lead.status != SourceLeadState.SOURCE_LEAD.value:
        raise ConflictError(f"source lead is already {lead.status}")
    return lead


def verify_lead(
    session: Session, principal: Principal, project_id: UUID, lead_id: UUID, excerpt_id: UUID
) -> SourceLeadOut:
    """A lead becomes VERIFIED only by pointing at actual source content (Core §27)."""
    auth = authorized(principal, "source_lead.resolve")
    lead = _open_lead(session, project_id, lead_id)
    excerpt = session.get(SourceExcerpt, excerpt_id)
    if excerpt is None:
        raise NotFoundError("excerpt not found")
    lead.status = SourceLeadState.VERIFIED.value
    lead.verified_by_excerpt_id = excerpt.id
    _audit(
        session,
        auth,
        "source_lead.resolve",
        entity_type="SourceLead",
        entity_id=lead.id,
        project_id=project_id,
        previous={"status": SourceLeadState.SOURCE_LEAD.value},
        new={"status": lead.status, "excerpt_id": str(excerpt.id)},
    )
    session.flush()
    return SourceLeadOut.model_validate(lead)


def discard_lead(session: Session, principal: Principal, project_id: UUID, lead_id: UUID, reason: str) -> SourceLeadOut:
    auth = authorized(principal, "source_lead.resolve")
    lead = _open_lead(session, project_id, lead_id)
    lead.status = SourceLeadState.DISCARDED.value
    _audit(
        session,
        auth,
        "source_lead.resolve",
        entity_type="SourceLead",
        entity_id=lead.id,
        project_id=project_id,
        previous={"status": SourceLeadState.SOURCE_LEAD.value},
        new={"status": lead.status},
        reason=reason,
    )
    session.flush()
    return SourceLeadOut.model_validate(lead)


# --- lexical search over ingested chunks (Core §38-39) ---


def search(session: Session, query: str, *, project_id: UUID | None = None, limit: int = 20) -> SearchResponse:
    tsquery = func.websearch_to_tsquery("simple", query)
    assets = (
        select(SourceAsset.id, SourceEdition.id.label("edition_id"), SourceWork.id.label("work_id"), SourceWork.title)
        .join(SourceEdition, SourceEdition.id == SourceAsset.edition_id)
        .join(SourceWork, SourceWork.id == SourceEdition.work_id)
        .where(SourceAsset.ingestion_status == IngestionStatus.COMPLETE.value)
    )
    if project_id is not None:
        projects.get_project(session, project_id)
        assets = assets.join(ProjectSource, ProjectSource.work_id == SourceWork.id).where(
            ProjectSource.project_id == project_id
        )
    scoped = assets.subquery()
    searched = session.scalar(select(func.count()).select_from(scoped)) or 0
    rank = func.ts_rank_cd(SourceChunk.tsv, tsquery)
    rows = session.execute(
        select(
            SourceChunk,
            scoped.c.edition_id,
            scoped.c.work_id,
            scoped.c.title,
            rank.label("rank"),
            func.ts_headline("simple", SourceChunk.text, tsquery, "MaxWords=35, MinWords=15").label("snippet"),
        )
        .join(scoped, scoped.c.id == SourceChunk.asset_id)
        .where(SourceChunk.tsv.op("@@")(tsquery))
        .order_by(rank.desc(), SourceChunk.page_number)
        .limit(limit)
    ).all()
    hits = [
        SearchHit(
            chunk_id=chunk.id,
            asset_id=chunk.asset_id,
            edition_id=edition_id,
            work_id=work_id,
            work_title=title,
            page_number=chunk.page_number,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
            snippet=snippet,
            rank=float(score),
        )
        for chunk, edition_id, work_id, title, score, snippet in rows
    ]
    return SearchResponse(
        query=query,
        outcome="RESULTS_FOUND" if hits else "NO_RELEVANT_EVIDENCE_FOUND",
        scope=f"project {project_id} library" if project_id else "entire local library",
        searched_assets=searched,
        hits=hits,
    )


# --- excerpts from ingested text (exact-quote protection, Core §29, FR-INGEST-004) ---


def create_page_excerpt(
    session: Session,
    principal: Principal,
    asset_id: UUID,
    data: PageExcerptIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> ExcerptOut:
    """Chunks are discovery units; quotes come from the exact page span of the stored source.

    The text is copied server-side from the extracted page. Native digital text from a
    checksummed asset is MACHINE_VERIFIED; OCR text can be excerpted but never as an
    exact quote until verified (DB check).
    """
    auth = authorized(principal, "source.excerpt", ai_action=ai_action)
    asset = session.get(SourceAsset, asset_id)
    if asset is None:
        raise NotFoundError("source asset not found")
    page = session.scalars(
        select(SourcePage).where(SourcePage.asset_id == asset_id, SourcePage.page_number == data.page_number)
    ).first()
    if page is None:
        raise NotFoundError("page not ingested for this asset", page_number=data.page_number)
    if data.char_end > len(page.text) or data.char_start >= data.char_end:
        raise RuleViolationError("span is outside the page text", page_length=len(page.text))
    span = page.text[data.char_start : data.char_end]
    if data.expected_text is not None and data.expected_text != span:
        raise RuleViolationError("quoted text does not match the source span exactly; quotes are never edited")
    origin = TextOrigin(page.text_origin)
    verification = (
        SourceVerificationState.MACHINE_VERIFIED
        if origin is TextOrigin.NATIVE_DIGITAL and asset.sha256
        else SourceVerificationState.UNVERIFIED
    )
    if data.is_exact_quote and not rules.exact_quote_allowed(origin, verification):
        raise RuleViolationError("OCR text cannot be an exact quote until verified (Core §28)")
    excerpt = SourceExcerpt(
        edition_id=asset.edition_id,
        asset_id=asset.id,
        location=f"p. {data.page_number}, chars {data.char_start}-{data.char_end}",
        text=span,
        text_origin=origin.value,
        verification_state=verification.value,
        is_exact_quote=data.is_exact_quote,
        provenance={
            "kind": ProvenanceKind.SOURCE_DERIVED.value,
            "actor": auth.actor.model_dump(mode="json", exclude_none=True),
            "derived_from": [str(asset.id)],
        },
    )
    session.add(excerpt)
    session.flush()
    _audit(
        session,
        auth,
        "source.excerpt",
        entity_type="SourceExcerpt",
        entity_id=excerpt.id,
        new={"asset_id": str(asset.id), "location": excerpt.location, "exact": excerpt.is_exact_quote},
    )
    return ExcerptOut.model_validate(excerpt)


def get_excerpt(session: Session, excerpt_id: UUID) -> ExcerptOut:
    excerpt = session.get(SourceExcerpt, excerpt_id)
    if excerpt is None:
        raise NotFoundError("excerpt not found")
    return ExcerptOut.model_validate(excerpt)


def work_ids_for_excerpts(session: Session, excerpt_ids: list[UUID]) -> dict[UUID, UUID]:
    """Map excerpts to their SourceWork, for evidence independence analysis."""
    if not excerpt_ids:
        return {}
    rows = session.execute(
        select(SourceExcerpt.id, SourceEdition.work_id)
        .join(SourceEdition, SourceEdition.id == SourceExcerpt.edition_id)
        .where(SourceExcerpt.id.in_(excerpt_ids))
    )
    return {excerpt_id: work_id for excerpt_id, work_id in rows}


def require_work(session: Session, work_id: UUID) -> None:
    if session.get(SourceWork, work_id) is None:
        raise NotFoundError("source work not found", work_id=str(work_id))


def chunk_texts(session: Session, chunk_ids: list[UUID]) -> dict[UUID, str]:
    """Full text of discovery chunks, for analysis only. Quotes still come from page spans."""
    if not chunk_ids:
        return {}
    rows = session.execute(select(SourceChunk.id, SourceChunk.text).where(SourceChunk.id.in_(chunk_ids))).all()
    return {chunk_id: text for chunk_id, text in rows}
