"""Rendering output versions to Markdown and HTML (FR-OUT-006). Quotes are emitted verbatim."""

from __future__ import annotations

import html
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import OutputBlockKind, OutputMode, QuoteSourceKind
from research_api.modules.outputs_integrity.schemas import Block, Quote
from research_api.modules.reference_governance import service as reference
from research_api.modules.sources_library import service as sources
from research_api.platform.errors import DomainError

K = OutputBlockKind
REFERENCES = {"en": "References", "fr": "Références", "ar": "المراجع"}
INTEGRITY = {"en": "Integrity", "fr": "Intégrité", "ar": "السلامة"}


@dataclass(frozen=True)
class Document:
    title: str
    language: str
    mode: OutputMode
    blocks: list[Block]
    version: int
    status: str
    integrity: str | None = None


def citation(session: Session, project_id: UUID, quote: Quote) -> str:
    """A human-readable source line for a quote; never invented, only read from the records."""
    try:
        if quote.source_kind is QuoteSourceKind.EXCERPT and quote.excerpt_id is not None:
            excerpt = sources.excerpt_in_project(session, project_id, quote.excerpt_id)
            edition = sources.get_edition(session, excerpt.edition_id)
            work = sources.get_work(session, edition.work_id)
            authors = ", ".join(work.authors)
            parts = [p for p in (authors, work.title, edition.edition_label, excerpt.location) if p]
            return ". ".join(parts)
        if quote.source_kind is QuoteSourceKind.QURAN and quote.quran_ref is not None:
            surah = int(quote.quran_ref.split(":")[0])
            first = int(quote.quran_ref.split(":")[1].split("-")[0])
            ayah = reference.get_ayat(session, surah, first)[0]
            return f"Qur'an {quote.quran_ref} ({ayah.surah_name}); {ayah.source_version}"
        if quote.source_kind is QuoteSourceKind.HADITH and quote.hadith_record_id is not None:
            record = reference.get_hadith(session, quote.hadith_record_id)
            return " · ".join(str(p) for p in (record.collection, record.book, record.number) if p)
    except DomainError:
        pass
    return "Source record unavailable"


def _citations(session: Session, project_id: UUID, doc: Document) -> list[str]:
    return [citation(session, project_id, b.quote) for b in doc.blocks if b.kind is K.QUOTE and b.quote is not None]


def markdown(session: Session, project_id: UUID, doc: Document) -> str:
    referenced = doc.mode is not OutputMode.READABLE
    audit = doc.mode is OutputMode.AUDIT
    lines = [f"# {doc.title}", ""]
    number = 0
    for block in doc.blocks:
        label = f" _[{block.label}]_" if referenced and block.label else ""
        trace = (
            "  \n  <sub>" + ", ".join(f"{t.entity_type}:{t.entity_id}" for t in block.trace) + "</sub>"
            if audit and block.trace
            else ""
        )
        if block.kind is K.HEADING:
            lines += ["#" * min((block.level or 2), 4) + " " + block.text, ""]
        elif block.kind is K.QUOTE and block.quote is not None:
            number += 1
            marker = f" [{number}]" if referenced else ""
            lines += [f"> {line}" for line in block.quote.text.split("\n")]
            lines += [f">{marker}{label}{trace}" if (marker or label or trace) else ">", ""]
        elif block.kind is K.LIST:
            lines += (
                ([label.strip(), ""] if label else []) + [f"- {item}" for item in (block.items or [])] + [trace, ""]
            )
        elif block.kind is K.CLAIM:
            lines += [f"**{block.text}**{label}{trace}", ""]
        else:
            lines += [f"{block.text}{label}{trace}", ""]
    citations = _citations(session, project_id, doc) if referenced else []
    if citations:
        lines += [f"## {REFERENCES.get(doc.language, REFERENCES['en'])}", ""]
        lines += [f"{i}. {c}" for i, c in enumerate(citations, start=1)] + [""]
    if _footer(doc):
        lines += [
            "---",
            f"{INTEGRITY.get(doc.language, 'Integrity')}: {doc.integrity} · v{doc.version} {doc.status}",
            "",
        ]
    return "\n".join(line for line in lines if line is not None).rstrip() + "\n"


def _footer(doc: Document) -> bool:
    """Audit copies always show integrity; others show it whenever the copy is not a verified, approved version."""
    if not doc.integrity:
        return False
    return doc.mode is OutputMode.AUDIT or doc.integrity != "VERIFIED" or doc.status != "APPROVED"


def _e(text: str) -> str:
    return html.escape(text, quote=False)


def html_document(session: Session, project_id: UUID, doc: Document) -> str:
    referenced = doc.mode is not OutputMode.READABLE
    audit = doc.mode is OutputMode.AUDIT
    direction = "rtl" if doc.language == "ar" else "ltr"
    body: list[str] = [f"<h1>{_e(doc.title)}</h1>"]
    number = 0
    for block in doc.blocks:
        label = f' <span class="label">[{_e(block.label)}]</span>' if referenced and block.label else ""
        trace = (
            '<small class="trace" dir="ltr">'
            + ", ".join(f"{_e(t.entity_type)}:{t.entity_id}" for t in block.trace)
            + "</small>"
            if audit and block.trace
            else ""
        )
        if block.kind is K.HEADING:
            level = min((block.level or 2), 4)
            body.append(f"<h{level}>{_e(block.text)}</h{level}>")
        elif block.kind is K.QUOTE and block.quote is not None:
            number += 1
            cls = ' class="quran"' if block.quote.source_kind is QuoteSourceKind.QURAN else ""
            lang = f' lang="{_e(block.quote.language)}"' if block.quote.language else ""
            marker = f"<sup>[{number}]</sup>" if referenced else ""
            text = "<br>".join(_e(line) for line in block.quote.text.split("\n"))
            body.append(f'<blockquote dir="auto"{lang}{cls}><p>{text}</p>{marker}{label}{trace}</blockquote>')
        elif block.kind is K.LIST:
            items = "".join(f'<li dir="auto">{_e(item)}</li>' for item in (block.items or []))
            body.append(f"{label}<ul>{items}</ul>{trace}")
        elif block.kind is K.CLAIM:
            body.append(f'<p dir="auto"><strong>{_e(block.text)}</strong>{label}{trace}</p>')
        else:
            body.append(f'<p dir="auto">{_e(block.text)}{label}{trace}</p>')
    citations = _citations(session, project_id, doc) if referenced else []
    if citations:
        body.append(f"<h2>{REFERENCES.get(doc.language, REFERENCES['en'])}</h2><ol>")
        body += [f'<li dir="auto">{_e(c)}</li>' for c in citations]
        body.append("</ol>")
    if _footer(doc):
        body.append(
            f"<hr><p>{INTEGRITY.get(doc.language, 'Integrity')}: {_e(doc.integrity or '')}"
            f" · v{doc.version} {_e(doc.status)}</p>"
        )
    style = (
        "body{font-family:system-ui,sans-serif;max-width:48rem;margin:2rem auto;padding:0 1rem;line-height:1.6}"
        "blockquote{border-inline-start:4px solid #888;margin:1rem 0;padding-inline-start:1rem}"
        ".quran{font-family:'Amiri Quran','Amiri',serif;font-size:1.3em}"
        ".label{color:#666}.trace{display:block;color:#888}"
    )
    return (
        f'<!doctype html>\n<html lang="{doc.language}" dir="{direction}"><head><meta charset="utf-8">'
        f"<title>{_e(doc.title)}</title><style>{style}</style></head><body>\n" + "\n".join(body) + "\n</body></html>\n"
    )
