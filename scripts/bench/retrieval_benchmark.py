"""Multilingual retrieval benchmark for choosing the default embedding model (PRD §61, ADR-025, #65).

The fixtures hold ten neighbouring topics, each with a passage and a paraphrased question in English, French
and Arabic (`docs/evaluation/fixtures/retrieval.json`). A question's relevant passages are its topic's three
language versions, so the benchmark measures both same-language and cross-language retrieval.

For every model, and for a word-overlap baseline, it reports:
- recall@3: the share of a question's three relevant passages found in the top 3;
- MRR: the mean reciprocal rank of the first relevant passage;
- cross-lingual@5: the share of relevant passages in *other* languages found in the top 5;
- embedding throughput on this machine.

Usage (needs the `embeddings` extra and network access to download the models once):
    uv run --extra embeddings python scripts/bench/retrieval_benchmark.py \
        --models sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2,intfloat/multilingual-e5-large
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "fixtures" / "retrieval.json"
LANGS = ("en", "fr", "ar")


def load() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    passages, queries = [], []
    for topic in data["topics"]:
        for lang in LANGS:
            passages.append(
                {"id": f"{topic['id']}:{lang}", "topic": topic["id"], "lang": lang, "text": topic["passages"][lang]}
            )
            queries.append({"topic": topic["id"], "lang": lang, "text": topic["queries"][lang]})
    return passages, queries


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / ((math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))) or 1.0)


def score(rankings: list[list[dict[str, str]]], queries: list[dict[str, str]]) -> dict[str, Any]:
    recall3, rr, cross = [], [], []
    by_lang: dict[str, list[float]] = {lang: [] for lang in LANGS}
    for query, ranked in zip(queries, rankings, strict=True):
        relevant = [p for p in ranked if p["topic"] == query["topic"]]
        top3 = ranked[:3]
        recall3.append(sum(p["topic"] == query["topic"] for p in top3) / 3)
        first = next(i for i, p in enumerate(ranked, start=1) if p["topic"] == query["topic"])
        rr.append(1 / first)
        others = [p for p in relevant if p["lang"] != query["lang"]]
        top5 = {p["id"] for p in ranked[:5]}
        cross.append(sum(p["id"] in top5 for p in others) / len(others))
        by_lang[query["lang"]].append(1 / first)
    mean = lambda xs: round(sum(xs) / len(xs), 3)  # noqa: E731
    return {
        "recall@3": mean(recall3),
        "mrr": mean(rr),
        "cross_lingual@5": mean(cross),
        "mrr_by_query_language": {lang: mean(v) for lang, v in by_lang.items()},
    }


def rank(
    query_vectors: list[Any], passage_vectors: list[Any], passages: list[dict[str, str]], sim: Callable[..., float]
) -> list[list[dict[str, str]]]:
    return [
        [p for _, p in sorted(zip((sim(q, v) for v in passage_vectors), passages, strict=True), key=lambda t: -t[0])]
        for q in query_vectors
    ]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", text.casefold()) if len(t) > 2}


def lexical_baseline(passages: list[dict[str, str]], queries: list[dict[str, str]]) -> dict[str, Any]:
    """Word overlap (Jaccard) — what keyword search can do without shared vocabulary."""

    def jaccard(q: set[str], p: set[str]) -> float:
        return len(q & p) / (len(q | p) or 1)

    rankings = rank([_tokens(q["text"]) for q in queries], [_tokens(p["text"]) for p in passages], passages, jaccard)
    return {"model": "lexical-overlap-baseline", **score(rankings, queries)}


def model_result(
    name: str, passages: list[dict[str, str]], queries: list[dict[str, str]], cache: Path
) -> dict[str, Any]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))
    from research_api.platform.embeddings import FastEmbedProvider  # noqa: PLC0415

    started = time.perf_counter()
    provider = FastEmbedProvider(name, cache)
    loaded = time.perf_counter()
    passage_vectors = provider.embed_documents([p["text"] for p in passages])
    query_vectors = [provider.embed_query(q["text"]) for q in queries]
    embedded = time.perf_counter()
    rankings = rank(query_vectors, passage_vectors, passages, cosine)
    texts = len(passages) + len(queries)
    return {
        "model": name,
        "dimensions": len(passage_vectors[0]),
        **score(rankings, queries),
        "load_seconds": round(loaded - started, 1),
        "texts_per_second": round(texts / (embedded - loaded), 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--cache", type=Path, default=Path("./data/models"))
    parser.add_argument("--json", type=Path, help="also write results to this file")
    args = parser.parse_args()
    passages, queries = load()
    results = [lexical_baseline(passages, queries)]
    for name in [m.strip() for m in args.models.split(",") if m.strip()]:
        try:
            results.append(model_result(name, passages, queries, args.cache))
        except Exception as exc:  # noqa: BLE001 - one failing candidate must not stop the comparison
            results.append({"model": name, "error": str(exc)[:300]})
    lines = [
        f"Fixtures: {len(passages)} passages, {len(queries)} questions (en/fr/ar)",
        "",
        "| Model | Dims | recall@3 | MRR | cross-lingual@5 | MRR en/fr/ar | texts/s |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['model']} | — | error: {r['error']} | | | | |")
            continue
        langs = "/".join(str(r["mrr_by_query_language"][lang]) for lang in LANGS)
        lines.append(
            f"| {r['model']} | {r.get('dimensions', '—')} | {r['recall@3']} | {r['mrr']} | {r['cross_lingual@5']} "
            f"| {langs} | {r.get('texts_per_second', '—')} |"
        )
    print("\n".join(lines))
    if args.json:
        args.json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
