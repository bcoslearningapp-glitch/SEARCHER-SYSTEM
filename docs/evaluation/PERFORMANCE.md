# Performance benchmark (PRD §70)

`scripts/bench/benchmark.py` (#57) runs against a live stack and uses only the Python standard library. It works in three steps:
1. It seeds a deterministic synthetic corpus of multilingual (ar/fr/en) text sources through the public API.
2. It waits for background ingestion to finish.
3. It measures the PRD §70 targets and exits non-zero if any p95 misses its target.

```bash
python scripts/bench/benchmark.py --works 1000 --pages 5 --runs 30   # seed and measure
python scripts/bench/benchmark.py --measure-only <project-id> --runs 60   # re-measure an already seeded project
```

## Results, 2026-09-25

**Machine:** 4 vCPU, 15 GB RAM, Linux x86_64. PostgreSQL 16 (pgvector image) and Redis run in Docker. The API (uvicorn, 1 process), the Celery worker and Next.js (`next start`) run as local processes.

**Corpus:** 1,000 works × ~5 pages, about 15,800 indexed chunks. All 1,000 text assets were ingested: upload took 27.6 s, and ingestion finished 4.4 s after the last upload.

Steady state, 60 runs per measure:

| Measure | p50 | p95 | Target (PRD §70) | |
|---|---|---|---|---|
| Full-text search, whole library | 75 ms | 128 ms | < 1 s | pass |
| Project page (desk) | 69 ms | 85 ms | < 2 s | pass |
| Project Sources page (1,000 linked works) | 737 ms | 897 ms | < 2 s | pass |
| Library page (1,000 works) | 621 ms | 691 ms | < 2 s | pass |
| State change: create claim | 10 ms | 13 ms | < 500 ms | pass |
| State change: add note | 6 ms | 9 ms | < 500 ms | pass |
| Vector search | — | — | < 2 s | not measured: there is no vector index yet (#65) |

## Findings

- **Fixed: N+1 queries in the library listing.** The first run found the Library page at 2.06 s and the Sources page at 1.5–1.8 s with 1,000 works. The cause was two extra queries per work to load editions and assets. `list_works` now batch-loads them in two queries. The API list fell from ~1.5 s to ~0.1–0.2 s and the pages to the table above. A regression test caps the query count (`integration/test_library_performance.py`).
- **Search right after bulk ingestion.** Straight after ingesting 1,000 works, the first searches reached p95 921 ms and max 1.06 s; steady state is 128 ms. This matches PostgreSQL merging the GIN index's pending list (`fastupdate`) on the first queries after a large insert. It is transient and within target at p95. If it matters for larger libraries, run `VACUUM ANALYZE source_chunks` after bulk imports, or turn `fastupdate` off on the index.
- **Page size.** The Sources and Library pages render every work. They are within target at 1,000 works, but they are the pages that will slow down first. Pagination is the next step if libraries grow much larger.
- **Background work.** Ingestion and AI tasks run as background jobs with visible status (PRD §70). The benchmark only waits on ingestion status; it does not block on it.
