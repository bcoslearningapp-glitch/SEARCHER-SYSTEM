# ADR-025: Semantic retrieval with a local, benchmarked embedding model
Status: Accepted
Date: 2026-09-25

Context:
- PRD §61 asks for:
  - a full-text index **and a vector index**;
  - an embedding implementation that is **abstracted**;
  - a default that supports Arabic, French and English well;
  - a **local** option, preferred where practical to minimise disclosure;
  - a model **benchmarked rather than assumed**.
- PRD §23 lists semantic retrieval next to lexical retrieval, and PRD §70 sets a vector-search target of < 2 s.
- ADR-008 shipped lexical search only and left embeddings for later (#65).

Decision:
- **Abstraction** (`platform/embeddings.py`): an `EmbeddingProvider` has `embed_documents`, `embed_query` and a `local` flag. The retrieval code knows only this interface.
- **Only a local provider is offered.** The `fastembed` provider runs an ONNX model on the machine, so no source or query text leaves it. The library is shared across projects of different sensitivity, so a cloud embedding provider would disclose restricted content outside any project's disclosure policy. None is offered.
- **Opt-in and lean by default:**
  - `EMBEDDING_PROVIDER` is `none` by default, and search stays lexical, exactly as before.
  - fastembed and its runtime (onnxruntime, tokenizers) are an optional `embeddings` extra. The image includes them only when built with `WITH_EMBEDDINGS=1`.
  - Model weights download once into `EMBEDDING_CACHE_DIR` (the `models` volume).
- **Storage:** `source_chunk_embeddings` holds one row per chunk and model: the vector (pgvector) and its dimension count. Rows are deleted with their chunk by cascade on re-ingestion.
  - Vectors are derived data: not exported in Research Core Packages, and rebuilt by backfill.
  - Several models can coexist while the default is switched.
- **Indexing:**
  - After ingestion, the worker embeds the new chunks. This is best effort: a failure is logged and never fails ingestion.
  - `python -m research_api.ops.embeddings backfill|status` catches up after enabling a provider or changing the model.
- **Search** (`GET /api/v1/sources/search?mode=`):
  - `lexical` is the ADR-008 path;
  - `semantic` ranks by cosine distance;
  - `hybrid` fuses the top 50 of each by reciprocal rank fusion (k = 60);
  - `auto`, the default, is hybrid when a provider is available and lexical otherwise.

  Every caller uses `auto`: the Library page, research-plan local search, and the AI tool `search_sources`. So they all gain semantic recall once the provider is enabled. Results remain discovery only (`quotation_authority: false`). The response states the `mode` used, and the Library page shows it.
- **Choosing the model.** `scripts/bench/retrieval_benchmark.py` runs every fastembed multilingual candidate over synthetic fixtures (`docs/evaluation/fixtures/retrieval.json`), next to a word-overlap baseline:
  - ten neighbouring topics;
  - passages and paraphrased questions in en/fr/ar.

  It reports recall@3, MRR, cross-lingual@5 and throughput. The `embedding-benchmark` workflow runs it on GitHub runners, which can download the models. The default `EMBEDDING_MODEL` is set from its results (below).

Benchmark results:
See the `embedding-benchmark` run on the PR that introduced this ADR. The default model and its numbers are recorded here once that run completes.

Consequences:
- Exact search over pgvector needs no ANN index at personal-library scale (~16k chunks). An HNSW index per model can be added if libraries grow much larger.
- Enabling semantic retrieval is an operator step:
  1. build with `WITH_EMBEDDINGS=1`;
  2. set `EMBEDDING_PROVIDER=fastembed`;
  3. allow one model download;
  4. run the backfill.

  The owner decides whether to enable it by default (#28).
- The ingestion worker needs more CPU when embeddings are on. The benchmark reports throughput per model.
