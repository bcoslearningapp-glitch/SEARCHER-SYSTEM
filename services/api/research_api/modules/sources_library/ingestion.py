"""Source ingestion (PRD §17, ADR-008): fingerprint check, page-anchored text extraction, chunking.

Runs in the worker. Extraction is deterministic; OCR is not performed in v0, so
pages without a text layer are flagged `needs_ocr` instead of silently empty.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

from pypdf import PdfReader
from sqlalchemy import delete
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import IngestionStatus, TextOrigin
from research_api.modules.sources_library import semantic
from research_api.modules.sources_library.models import SourceAsset, SourceChunk, SourcePage
from research_api.platform import embeddings
from research_api.platform.storage import get_store

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MIN_TEXT_CHARS = 20


class IngestionError(Exception):
    pass


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


def extract_pages(media_type: str, data: bytes) -> list[PageText]:
    if media_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            return [PageText(i + 1, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages)]
        except Exception as exc:
            raise IngestionError(f"could not read PDF: {exc}") from exc
    if media_type == "text/plain":
        text = data.decode("utf-8")
        # Form feed is the conventional page break in plain text.
        return [PageText(i + 1, part.strip()) for i, part in enumerate(text.split("\f"))]
    raise IngestionError(f"no text extractor for {media_type}")


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[tuple[int, int]]:
    """Split into overlapping [start, end) spans, preferring whitespace boundaries."""
    if not text:
        return []
    spans: list[tuple[int, int]] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + size, length)
        if end < length:
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        spans.append((start, end))
        if end >= length:
            break
        next_start = max(end - overlap, start + 1)
        # Do not start mid-word.
        space = text.find(" ", next_start, end)
        start = space + 1 if space != -1 else next_start
    return spans


def ingest_asset(session: Session, asset_id: Any) -> dict[str, Any]:
    asset = session.get(SourceAsset, asset_id, with_for_update=True)
    if asset is None:
        raise IngestionError(f"asset {asset_id} not found")
    if not asset.storage_key or not asset.media_type:
        raise IngestionError("asset has no stored content")
    asset.ingestion_status = IngestionStatus.RUNNING.value
    data = get_store().read(asset.storage_key)  # verifies the sha256 fingerprint
    pages = extract_pages(asset.media_type, data)

    # Re-ingestion replaces derived rows only; the original asset is untouched.
    session.execute(delete(SourceChunk).where(SourceChunk.asset_id == asset.id))
    session.execute(delete(SourcePage).where(SourcePage.asset_id == asset.id))

    chunk_count = 0
    needs_ocr = 0
    for page in pages:
        flagged = len(page.text) < MIN_TEXT_CHARS
        needs_ocr += flagged
        session.add(
            SourcePage(
                asset_id=asset.id,
                page_number=page.page_number,
                text=page.text,
                text_origin=TextOrigin.NATIVE_DIGITAL.value,
                needs_ocr=flagged,
            )
        )
        for index, (start, end) in enumerate(chunk_text(page.text)):
            session.add(
                SourceChunk(
                    asset_id=asset.id,
                    page_number=page.page_number,
                    chunk_index=index,
                    char_start=start,
                    char_end=end,
                    text=page.text[start:end],
                )
            )
            chunk_count += 1
    asset.ingestion_status = IngestionStatus.COMPLETE.value
    asset.text_origin = TextOrigin.NATIVE_DIGITAL.value
    session.flush()
    embedded = semantic.index_after_ingestion(session, embeddings.configured(get_settings()), asset.id)
    logger.info("ingested asset %s: %d pages, %d chunks", asset.id, len(pages), chunk_count)
    return {"pages": len(pages), "chunks": chunk_count, "pages_needing_ocr": needs_ocr, "embedded": embedded}


def mark_failed(session: Session, asset_id: Any) -> None:
    asset = session.get(SourceAsset, asset_id)
    if asset is not None:
        asset.ingestion_status = IngestionStatus.FAILED.value
