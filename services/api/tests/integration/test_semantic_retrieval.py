"""Semantic and hybrid retrieval (issue #65, PRD §23, §61, ADR-025).

A deterministic test embedder stands in for the local model. It maps a few multilingual synonyms to shared
concepts, which is enough to show semantic retrieval finding what lexical search misses. It exists only here;
the product ships no fake embedder.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from research_api.modules.sources_library import ingestion, semantic
from research_api.modules.sources_library.models import SourceChunkEmbedding
from research_api.platform import embeddings, queue

CONCEPTS = {
    "mentoring": 0, "mentor": 0, "guidance": 0, "tutorat": 0, "encadrement": 0, "التوجيه": 0, "الإرشاد": 0,
    "retention": 1, "dropout": 1, "abandon": 1, "rétention": 1, "الاستبقاء": 1, "التسرب": 1,
    "irrigation": 2, "water": 2, "eau": 2, "الري": 2, "المياه": 2,
}  # fmt: skip
DIMENSIONS = 8


class ConceptEmbedder:
    """Bag of concepts, normalised. Unknown words land in a hashed bucket so unrelated text is not zero."""

    name = "test-concepts"
    model = "test/concepts-v1"
    local = True

    def __init__(self) -> None:
        self.documents = 0

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * DIMENSIONS
        for word in text.casefold().replace(".", " ").replace(",", " ").split():
            vec[CONCEPTS.get(word, 3 + sum(map(ord, word)) % (DIMENSIONS - 3))] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents += len(texts)
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


@pytest.fixture
def embedder(monkeypatch: MonkeyPatch) -> Iterator[ConceptEmbedder]:
    provider = ConceptEmbedder()
    monkeypatch.setattr(embeddings, "configured", lambda settings: provider)
    yield provider


def _source(client: TestClient, session: Session, pid: str, title: str, text: str) -> str:
    work = client.post("/api/v1/sources", json={"work": {"title": title}, "project_id": pid}).json()
    asset = client.post(
        f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
        files={"file": (f"{title}.txt", text.encode(), "text/plain")},
    ).json()
    ingestion.ingest_asset(session, UUID(asset["id"]))
    return str(asset["id"])


def _project(client: TestClient) -> str:
    return str(
        client.post("/api/v1/projects", json={"title": "S", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )


def _search(client: TestClient, pid: str, q: str, mode: str = "auto") -> dict[str, Any]:
    response = client.get("/api/v1/sources/search", params={"q": q, "project_id": pid, "mode": mode})
    assert response.status_code == 200, response.text
    return dict(response.json())


def test_without_a_provider_search_stays_lexical(client: TestClient, session: Session) -> None:
    pid = _project(client)
    _source(client, session, pid, "Cohort", "Mentoring declines in the second year.")
    result = _search(client, pid, "mentoring")
    assert result["mode"] == "lexical" and result["hits"]
    refused = client.get("/api/v1/sources/search", params={"q": "mentoring", "mode": "semantic"})
    assert refused.status_code == 422
    assert session.scalar(select(func.count()).select_from(SourceChunkEmbedding)) == 0


def test_ingestion_embeds_chunks_and_semantic_search_crosses_languages(
    client: TestClient, session: Session, embedder: ConceptEmbedder
) -> None:
    pid = _project(client)
    arabic = _source(client, session, pid, "Arabic study", "التوجيه يقلل التسرب في السنة الثانية")
    _source(client, session, pid, "Irrigation", "Irrigation water schedules for dry farms")
    assert embedder.documents >= 2
    stored = session.scalar(select(func.count()).select_from(SourceChunkEmbedding))
    assert stored and stored >= 2

    lexical = _search(client, pid, "mentoring retention", mode="lexical")
    assert lexical["hits"] == [], "no shared words: keyword search cannot find the Arabic passage"
    found = _search(client, pid, "mentoring retention", mode="semantic")
    assert found["mode"] == "semantic"
    assert found["hits"][0]["asset_id"] == arabic, "the concept match ranks first across languages"
    assert found["quotation_authority"] is False


def test_hybrid_fuses_lexical_and_semantic_rankings(
    client: TestClient, session: Session, embedder: ConceptEmbedder
) -> None:
    pid = _project(client)
    english = _source(client, session, pid, "Report", "Mentoring and retention in apprenticeships")
    arabic = _source(client, session, pid, "Arabic study", "التوجيه يقلل التسرب في السنة الثانية")
    _source(client, session, pid, "Irrigation", "Irrigation water schedules for dry farms")
    result = _search(client, pid, "mentoring retention")
    assert result["mode"] == "hybrid", "auto becomes hybrid when a provider is configured"
    ranked = [h["asset_id"] for h in result["hits"]]
    assert ranked[0] == english, "found by both rankings, so it leads"
    assert arabic in ranked, "found by meaning alone, still included"


def test_reingestion_replaces_vectors_and_backfill_catches_up(
    client: TestClient, session: Session, embedder: ConceptEmbedder
) -> None:
    pid = _project(client)
    asset = _source(client, session, pid, "Cohort", "Mentoring declines in the second year.")
    count = select(func.count()).select_from(SourceChunkEmbedding)
    before = session.scalar(count)
    ingestion.ingest_asset(session, UUID(asset))
    assert session.scalar(count) == before, "old vectors go with their chunks; new ones replace them"

    session.execute(SourceChunkEmbedding.__table__.delete())
    assert semantic.backfill(session, embedder) >= 1
    assert semantic.backfill(session, embedder) == 0, "nothing left to embed"


def test_an_embedding_failure_never_fails_ingestion(
    client: TestClient, session: Session, monkeypatch: MonkeyPatch
) -> None:
    class Broken(ConceptEmbedder):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            raise RuntimeError("model crashed")

    monkeypatch.setattr(embeddings, "configured", lambda settings: Broken())
    pid = _project(client)
    asset = _source(client, session, pid, "Cohort", "Mentoring declines in the second year.")
    status = client.get(f"/api/v1/sources/assets/{asset}").json()["ingestion_status"]
    assert status == "COMPLETE"
    assert _search(client, pid, "mentoring", mode="lexical")["hits"]


def test_rank_fusion_orders_by_combined_reciprocal_rank() -> None:
    a, b, c, d = (UUID(int=i) for i in range(1, 5))
    fused = semantic.fuse([a, b, c], [c, d, a], limit=4)
    assert [f.chunk_id for f in fused][:2] == [a, c], "items in both lists outrank items in one"
    assert {f.chunk_id for f in fused} == {a, b, c, d}
    assert fused[0].lexical_rank == 1 and fused[0].semantic_rank == 3
