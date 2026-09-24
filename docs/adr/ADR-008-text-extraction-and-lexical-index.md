# ADR-008: Text extraction with pypdf, page-anchored chunks, PostgreSQL full-text index
Status: Accepted
Date: 2026-09-24

Context:
PRD §17 defines the ingestion pipeline (fingerprint, extraction, page anchoring, text-origin tagging, chunking, indexing). §81 requires an ADR for the source parsing/OCR stack. Arabic, English and French must work; the embedding model must be benchmarked before choosing (PRD §61), so semantic search is out of scope for Phase 1.

Decision:
- Extraction: `pypdf` (pure Python, BSD) for native PDF text per page; UTF-8 text files split pages on form feed. EPUB and images are stored but not extracted yet.
- OCR is not performed in v0. Pages with fewer than 20 extracted characters are flagged `needs_ocr`; text origin is recorded as `NATIVE_DIGITAL`. When OCR is added, its output must be tagged `OCR_EXTRACTED` and can never be an exact quote until verified (enforced by a CHECK constraint on `source_excerpts`).
- Storage: `source_pages` (asset, page number, text) and `source_chunks` (asset, page number, char span, text). Chunks are ~1200 characters with ~200 overlap, split on whitespace. They are derived data: re-ingestion replaces them; originals never change.
- Lexical index: a stored `tsvector` generated column with the `simple` configuration (language-neutral, no stemming, safe for mixed Arabic/Latin text) and a GIN index; queries use `websearch_to_tsquery`.
- Ingestion runs as a durable background job (`sources.ingest_asset`, ADR-003); failures mark the asset `FAILED` and the job `APPLICATION_ERROR`, never "no text".
- Search responses state their scope and number of searched assets and report `NO_RELEVANT_EVIDENCE_FOUND` rather than implying absence of evidence beyond that scope; they are marked as non-authoritative for quotation.

Alternatives considered:
- pdfminer.six / PyMuPDF: better layout fidelity; PyMuPDF is AGPL. Revisit with a benchmark on Arabic PDFs.
- Language-specific text search configs: better recall per language but wrong for mixed-language corpora without per-chunk language detection.

Consequences:
- Scanned PDFs are searchable only after OCR is added (future ADR).
- The chunk table can later gain a pgvector embedding column once an embedding model is benchmarked.

Research Core impact: Chunks are discovery units, not quotation authorities (FR-INGEST-004); text origin is explicit (Core §28).

Migration impact: Migration 0004 adds derived tables only.
