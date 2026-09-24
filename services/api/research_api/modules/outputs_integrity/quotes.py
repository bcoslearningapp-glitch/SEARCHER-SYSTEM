"""Protected exact quotes: the text in an output must equal its source, byte for byte (FR-OUT-003)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import QuoteSourceKind
from research_api.modules.outputs_integrity.schemas import Quote
from research_api.modules.reference_governance import service as reference
from research_api.modules.sources_library import service as sources
from research_api.platform.errors import DomainError


def source_text(session: Session, project_id: UUID, quote: Quote) -> str | None:
    """The authoritative text for a quote, or None when the source cannot be resolved here."""
    try:
        if quote.source_kind is QuoteSourceKind.EXCERPT and quote.excerpt_id is not None:
            excerpt = sources.excerpt_in_project(session, project_id, quote.excerpt_id)
            return excerpt.text if excerpt.is_exact_quote else None
        if quote.source_kind is QuoteSourceKind.QURAN and quote.quran_ref is not None:
            return reference.quran_text(session, quote.quran_ref)
        if quote.source_kind is QuoteSourceKind.HADITH and quote.hadith_record_id is not None:
            return reference.hadith_text(session, quote.hadith_record_id)
    except DomainError:
        return None
    return None


def mismatch(session: Session, project_id: UUID, quote: Quote) -> str | None:
    """A reason the quote is not faithful, or None if it matches its source exactly."""
    expected = source_text(session, project_id, quote)
    if expected is None:
        return "the quoted source cannot be resolved as an exact, verified text in this project"
    if quote.text != expected:
        return "the quoted text differs from its source; exact quotes cannot be edited"
    return None
