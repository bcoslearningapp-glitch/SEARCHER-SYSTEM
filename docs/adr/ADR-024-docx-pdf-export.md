# ADR-024: DOCX and PDF export
Status: Accepted
Date: 2026-09-25

Context:
PRD Phase 5 asks for Markdown, HTML, DOCX and PDF export, and FR-OUT-006 applies to all four. Markdown and HTML are done (ADR-021). DOCX and PDF raise three constraints:
- Arabic must be shaped and laid out right to left, and mixed with Latin text.
- Exact quotes, including Qur'an text, are immutable protected content. The export must never alter them, and that must be checkable.
- The renderer must run in the modular monolith and in CI, with no system services, network fonts or headless browser.

Decision:
- **DOCX: python-docx.**
  - Text is stored as Unicode runs. Paragraphs whose first strong character is right-to-left get `w:bidi`, and runs containing Arabic get `w:rtl`. The complex-script font is Amiri, or Amiri Quran for Qur'an quotes.
  - Each quote line is its own paragraph in the Quote style.
  - After rendering, the file is read back. Every quote line must appear as a paragraph exactly; otherwise the export fails and nothing is returned.
- **PDF: fpdf2 with HarfBuzz text shaping (uharfbuzz).**
  - fpdf2 runs the Unicode bidi algorithm and shapes Arabic through HarfBuzz.
  - Each paragraph is aligned by its own direction; text with no strong character follows the document language.
  - List numbers and bullets are drawn as separate cells on the leading side, because fpdf2's line layout otherwise places a leading marker on the left of Arabic text.
  - A PDF stores shaped glyphs, and text extraction may reorder neutral characters. So each PDF embeds `quotes.json` (a PDF file attachment) with the exact text and SHA-256 of every quote. Tests check it, together with extraction of single-direction lines.
- **Fonts: Amiri 1.003 (SIL Open Font License 1.1)** is bundled in `research_api/assets/fonts` with its licence: Amiri Regular and Bold for body text, and Amiri Quran for Qur'an quotes.
  - Amiri covers Arabic and Latin, including French diacritics.
  - The owner may set `EXPORT_QURAN_FONT_PATH` to a publisher font whose licence they have checked, as with the web reading font. It is never committed.
- **Same content as the other formats.** Both renderers consume one element list built from the output version, using the same rules as the Markdown export:
  - labels and traces by mode;
  - quote numbering;
  - references built from records;
  - the integrity footer when a copy is not a verified, approved version.
- **Endpoint.** The existing export endpoint accepts `format=docx|pdf`, and the web proxy route and output page offer the downloads.

Alternatives considered:
- WeasyPrint or headless Chromium for PDF. Both are heavier system dependencies (Pango/Cairo, or a browser in the API image).
- ReportLab needs separate reshaping and bidi libraries for Arabic.
- LibreOffice conversion from DOCX is a large system dependency with non-deterministic layout.

Consequences:
- New Python dependencies, all with wheels:
  - python-docx (MIT);
  - fpdf2 (LGPL-3.0, used unmodified as a library);
  - uharfbuzz (Apache-2.0).
  About 1 MB of fonts is added.
- PDF text extraction by third-party tools may show mixed-direction lines out of order. The embedded `quotes.json` is the machine-readable record of exact quotes.
- DOCX does not embed fonts. A reader without Amiri sees a fallback font, but the text is unchanged.
