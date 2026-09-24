"""Ingestion end to end in the worker: PDF -> page anchors -> chunks -> search (issue #6)."""

from uuid import UUID

from sqlalchemy import select

from research_api.contracts.enums import ActorKind
from research_api.modules.governance_audit.principal import Principal, local_owner
from research_api.modules.sources_library import service
from research_api.modules.sources_library.models import SourceAsset, SourcePage
from research_api.modules.sources_library.schemas import CatalogIn
from research_api.platform import jobs
from research_api.platform.db import session_scope
from research_worker import tasks
from tests.pdf_fixtures import make_pdf

OWNER: Principal = local_owner()
assert OWNER.kind is ActorKind.HUMAN


def _upload(data: bytes, filename: str) -> tuple[UUID, UUID]:
    with session_scope() as session:
        work = service.catalog(session, OWNER, CatalogIn.model_validate({"work": {"title": "Test work"}}))
        asset, job_id = service.upload_asset(session, OWNER, work.editions[0].id, data, filename)
        assert job_id is not None
        return asset.id, job_id


def test_pdf_ingestion_keeps_page_anchors_and_is_searchable() -> None:
    pdf = make_pdf(["Introduction to apprenticeship.", "Mentoring declines sharply in the second year."])
    asset_id, job_id = _upload(pdf, "study.pdf")
    assert tasks.ingest_asset(str(job_id)) == "SUCCEEDED"

    with session_scope() as session:
        asset = session.get(SourceAsset, asset_id)
        assert asset is not None and asset.ingestion_status == "COMPLETE"
        pages = session.scalars(
            select(SourcePage).where(SourcePage.asset_id == asset_id).order_by(SourcePage.page_number)
        ).all()
        assert [p.page_number for p in pages] == [1, 2]
        assert "Mentoring declines" in pages[1].text
        job = jobs.get_job(session, job_id)
        assert job.result == {"pages": 2, "chunks": 2, "pages_needing_ocr": 0}

        result = service.search(session, "mentoring second year")
        hit = next(h for h in result.hits if h.asset_id == asset_id)
        assert hit.page_number == 2
        assert result.outcome == "RESULTS_FOUND"
        assert result.quotation_authority is False

        nothing = service.search(session, "zzqxnonexistentterm")
        assert nothing.outcome == "NO_RELEVANT_EVIDENCE_FOUND"
        assert nothing.searched_assets >= 1


def test_corrupt_pdf_fails_job_and_marks_asset() -> None:
    asset_id, job_id = _upload(b"%PDF-1.4\nthis is not really a pdf", "broken.pdf")
    assert tasks.ingest_asset(str(job_id)) == "FAILED"
    with session_scope() as session:
        asset = session.get(SourceAsset, asset_id)
        assert asset is not None and asset.ingestion_status == "FAILED"
        assert jobs.get_job(session, job_id).failure_kind == "APPLICATION_ERROR"
