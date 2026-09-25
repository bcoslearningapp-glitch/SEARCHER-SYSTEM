"""Semantic retrieval over source chunks (PRD §23, §61, ADR-025).

Embeddings are derived data. They are written after ingestion, rebuilt by backfill, deleted with their
chunks, and never exported in a Research Core Package. Retrieval only finds candidates; it never
adjudicates (Core §39), and a chunk is never a quotation authority.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from research_api.modules.sources_library.models import SourceChunk, SourceChunkEmbedding
from research_api.platform.embeddings import EmbeddingProvider, EmbeddingUnavailableError

logger = logging.getLogger(__name__)
BATCH = 64
# Reciprocal rank fusion constant (Cormack et al., 2009): damps the weight of the very top ranks.
RRF_K = 60


def _missing(provider: EmbeddingProvider) -> Select[tuple[SourceChunk]]:
    embedded = select(SourceChunkEmbedding.chunk_id).where(SourceChunkEmbedding.model == provider.model)
    return select(SourceChunk).where(SourceChunk.id.not_in(embedded)).order_by(SourceChunk.id)


def _store(session: Session, provider: EmbeddingProvider, chunks: Sequence[SourceChunk]) -> int:
    if not chunks:
        return 0
    vectors = provider.embed_documents([c.text for c in chunks])
    rows = [
        {"chunk_id": c.id, "model": provider.model, "dimensions": len(v), "embedding": v}
        for c, v in zip(chunks, vectors, strict=True)
    ]
    session.execute(insert(SourceChunkEmbedding).values(rows).on_conflict_do_nothing())
    return len(rows)


def embed_asset(session: Session, provider: EmbeddingProvider, asset_id: UUID) -> int:
    """Embed an asset's chunks that have no vector yet for the provider's model."""
    chunks = list(session.scalars(_missing(provider).where(SourceChunk.asset_id == asset_id)))
    return sum(_store(session, provider, chunks[i : i + BATCH]) for i in range(0, len(chunks), BATCH))


def index_after_ingestion(session: Session, provider: EmbeddingProvider | None, asset_id: UUID) -> int | None:
    """Best effort. A failure never fails ingestion: lexical search works, and backfill catches up later."""
    if provider is None:
        return None
    try:
        with session.begin_nested():
            return embed_asset(session, provider, asset_id)
    except EmbeddingUnavailableError:
        logger.warning("semantic indexing skipped for asset %s: embedding provider unavailable", asset_id)
    except Exception:
        logger.exception("semantic indexing failed for asset %s; run the embeddings backfill", asset_id)
    return None


def backfill(session: Session, provider: EmbeddingProvider, *, limit: int | None = None) -> int:
    """Embed every chunk that lacks a vector for the provider's model, in batches."""
    done = 0
    while limit is None or done < limit:
        size = BATCH if limit is None else min(BATCH, limit - done)
        chunks = list(session.scalars(_missing(provider).limit(size)))
        if not chunks:
            break
        done += _store(session, provider, chunks)
        session.flush()
    return done


def coverage(session: Session, provider: EmbeddingProvider) -> tuple[int, int]:
    """(chunks embedded with the provider's model, all chunks)."""
    embedded = session.scalar(
        select(func.count()).select_from(SourceChunkEmbedding).where(SourceChunkEmbedding.model == provider.model)
    )
    total = session.scalar(select(func.count()).select_from(SourceChunk))
    return int(embedded or 0), int(total or 0)


def nearest(session: Session, provider: EmbeddingProvider, query: str, scoped: Any, limit: int) -> list[Any]:
    """(chunk, edition_id, work_id, title, distance) nearest to the query within the scoped assets."""
    vector = provider.embed_query(query)
    distance = SourceChunkEmbedding.embedding.cosine_distance(vector)
    return list(
        session.execute(
            select(SourceChunk, scoped.c.edition_id, scoped.c.work_id, scoped.c.title, distance.label("distance"))
            .join(SourceChunkEmbedding, SourceChunkEmbedding.chunk_id == SourceChunk.id)
            .join(scoped, scoped.c.id == SourceChunk.asset_id)
            .where(SourceChunkEmbedding.model == provider.model)
            .order_by(distance)
            .limit(limit)
        ).all()
    )


@dataclass(frozen=True)
class Fused:
    chunk_id: UUID
    score: float
    lexical_rank: int | None
    semantic_rank: int | None


def fuse(lexical: Sequence[UUID], semantic: Sequence[UUID], limit: int) -> list[Fused]:
    """Reciprocal rank fusion of two ranked lists of chunk ids."""
    scores: dict[UUID, float] = {}
    ranks: dict[UUID, list[int | None]] = {}
    for position, chunk_id in enumerate(lexical, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + position)
        ranks.setdefault(chunk_id, [None, None])[0] = position
    for position, chunk_id in enumerate(semantic, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + position)
        ranks.setdefault(chunk_id, [None, None])[1] = position
    ordered = sorted(scores, key=lambda c: (-scores[c], ranks[c][0] or RRF_K * 10, ranks[c][1] or RRF_K * 10))
    return [Fused(c, scores[c], ranks[c][0], ranks[c][1]) for c in ordered[:limit]]
