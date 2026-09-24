from itertools import pairwise

import pytest

from research_api.contracts.enums import AccessResponseForm as F
from research_api.contracts.enums import SourceAccessMode, SourceAssetKind, SourceVerificationState, TextOrigin
from research_api.modules.sources_library import ingestion, rules


def test_exact_text_is_researcher_supplied_exact() -> None:
    trust = rules.trust_for_text_response(F.EXACT_TEXT)
    assert trust.verification is SourceVerificationState.RESEARCHER_SUPPLIED_EXACT
    assert trust.is_exact_quote


@pytest.mark.parametrize("form", [F.RESEARCHER_SUMMARY, F.RESEARCHER_ATTESTATION])
def test_summaries_are_reported_content_never_quotes(form: F) -> None:
    trust = rules.trust_for_text_response(form)
    assert trust.verification is SourceVerificationState.RESEARCHER_REPORTED_SOURCE_CONTENT
    assert not trust.is_exact_quote


def test_page_images_are_researcher_mediated_scans() -> None:
    assert rules.asset_for_file_response(F.PAGE_IMAGES, "image/png") == (
        SourceAssetKind.SCAN,
        SourceAccessMode.RESEARCHER_MEDIATED,
    )


def test_ocr_is_never_exact_unless_verified() -> None:
    assert not rules.exact_quote_allowed(TextOrigin.OCR_EXTRACTED, SourceVerificationState.UNVERIFIED)
    assert rules.exact_quote_allowed(TextOrigin.OCR_EXTRACTED, SourceVerificationState.MACHINE_VERIFIED)
    assert rules.exact_quote_allowed(TextOrigin.NATIVE_DIGITAL, SourceVerificationState.UNVERIFIED)


def test_chunks_cover_text_with_overlap_and_no_empty_spans() -> None:
    text = " ".join(f"word{i}" for i in range(1000))
    spans = ingestion.chunk_text(text, size=200, overlap=50)
    assert spans[0][0] == 0
    assert spans[-1][1] == len(text)
    assert all(end > start for start, end in spans)
    assert all(b_start < a_end for (_, a_end), (b_start, _) in pairwise(spans))
    assert ingestion.chunk_text("") == []


def test_plain_text_pages_split_on_form_feed() -> None:
    pages = ingestion.extract_pages("text/plain", b"page one\fpage two")
    assert [(p.page_number, p.text) for p in pages] == [(1, "page one"), (2, "page two")]
