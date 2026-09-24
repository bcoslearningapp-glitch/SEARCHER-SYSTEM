"""Pure source-trust rules (Core §24-28, FR-HYBRID-003/004, FR-INGEST-003)."""

from __future__ import annotations

from dataclasses import dataclass

from research_api.contracts.enums import (
    AccessResponseForm as F,
)
from research_api.contracts.enums import (
    ReferenceAuthorityLayer,
    SourceAccessMode,
    SourceAssetKind,
    SourceVerificationState,
    TextOrigin,
)

FOUNDATIONAL_LAYERS = frozenset(
    {ReferenceAuthorityLayer.QURAN, ReferenceAuthorityLayer.SUNNAH, ReferenceAuthorityLayer.APPROVED_FOUNDATIONAL}
)

# Holdings recorded at catalog time. Metadata never implies availability (Core §24).
UNAVAILABLE_HOLDINGS = frozenset(
    {SourceAccessMode.PHYSICAL, SourceAccessMode.RESTRICTED, SourceAccessMode.RESEARCHER_MEDIATED}
)


@dataclass(frozen=True)
class TextResponseTrust:
    verification: SourceVerificationState
    text_origin: TextOrigin
    is_exact_quote: bool


def trust_for_text_response(form: F) -> TextResponseTrust:
    """Verification reflects the actual access method, never more (FR-HYBRID-004)."""
    if form is F.EXACT_TEXT:
        return TextResponseTrust(SourceVerificationState.RESEARCHER_SUPPLIED_EXACT, TextOrigin.HUMAN_TRANSCRIBED, True)
    if form in (F.RESEARCHER_SUMMARY, F.RESEARCHER_ATTESTATION):
        return TextResponseTrust(
            SourceVerificationState.RESEARCHER_REPORTED_SOURCE_CONTENT, TextOrigin.HUMAN_TRANSCRIBED, False
        )
    raise ValueError(f"{form} is a file response, not a text response")


FILE_FORMS = frozenset({F.PAGE_IMAGES, F.DIGITAL_ASSET})


def asset_for_file_response(form: F, media_type: str) -> tuple[SourceAssetKind, SourceAccessMode]:
    if form is F.PAGE_IMAGES:
        kind = SourceAssetKind.SCAN if media_type.startswith("image/") else SourceAssetKind.PDF
        return kind, SourceAccessMode.RESEARCHER_MEDIATED
    if form is F.DIGITAL_ASSET:
        return kind_for_media(media_type), SourceAccessMode.DIRECT_DIGITAL
    raise ValueError(f"{form} is a text response, not a file response")


def kind_for_media(media_type: str) -> SourceAssetKind:
    return {
        "application/pdf": SourceAssetKind.PDF,
        "text/plain": SourceAssetKind.LOCAL_TEXT,
        "application/epub+zip": SourceAssetKind.EPUB,
        "image/png": SourceAssetKind.IMAGE,
        "image/jpeg": SourceAssetKind.IMAGE,
    }.get(media_type, SourceAssetKind.OTHER)


def exact_quote_allowed(text_origin: TextOrigin, verification: SourceVerificationState) -> bool:
    """OCR text is never an exact quote until checked (Core §28, FR-INGEST-003)."""
    if text_origin is TextOrigin.OCR_EXTRACTED:
        return verification in {
            SourceVerificationState.MACHINE_VERIFIED,
            SourceVerificationState.RESEARCHER_SUPPLIED_EXACT,
        }
    return True
