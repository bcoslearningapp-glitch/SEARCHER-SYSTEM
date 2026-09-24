"""Parse and validate an approved Qur'an text dataset (FR-QURAN-001).

The system never produces Qur'anic text; it only imports a dataset supplied by
the Constitutional Authority. Accepted format (UTF-8, Tanzil-compatible):

    # comment lines are ignored
    @surah|<surah number>|<surah name>
    <surah number>|<ayah number>|<exact ayah text>

Validation is structural only (numbering, uniqueness, contiguity, non-empty
text, names present). Content correctness is the approving authority's call.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

MAX_SURAH = 114


class DatasetError(ValueError):
    pass


@dataclass
class ParsedDataset:
    sha256: str
    surah_names: dict[int, str] = field(default_factory=dict)
    ayat: list[tuple[int, int, str]] = field(default_factory=list)

    @property
    def surah_count(self) -> int:
        return len({s for s, _, _ in self.ayat})


def parse(data: bytes) -> ParsedDataset:
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetError("dataset must be UTF-8 text") from exc
    parsed = ParsedDataset(sha256=hashlib.sha256(data).hexdigest())
    seen: set[tuple[int, int]] = set()
    for line_no, raw in enumerate(content.splitlines(), start=1):
        line = raw.rstrip("\r")
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("@surah|"):
            _parse_name(line, line_no, parsed)
        else:
            _parse_ayah(line, line_no, parsed, seen)
    _check_structure(parsed)
    return parsed


def _parse_name(line: str, line_no: int, parsed: ParsedDataset) -> None:
    parts = line.split("|", 2)
    if len(parts) != 3 or not parts[2].strip():
        raise DatasetError(f"line {line_no}: malformed surah name line")
    number = _int(parts[1], line_no)
    _check_surah(number, line_no)
    parsed.surah_names[number] = parts[2].strip()


def _parse_ayah(line: str, line_no: int, parsed: ParsedDataset, seen: set[tuple[int, int]]) -> None:
    parts = line.split("|", 2)
    if len(parts) != 3:
        raise DatasetError(f"line {line_no}: expected 'surah|ayah|text'")
    surah, ayah = _int(parts[0], line_no), _int(parts[1], line_no)
    _check_surah(surah, line_no)
    if ayah < 1:
        raise DatasetError(f"line {line_no}: ayah numbers start at 1")
    text = parts[2]
    if not text.strip():
        raise DatasetError(f"line {line_no}: empty ayah text")
    if (surah, ayah) in seen:
        raise DatasetError(f"line {line_no}: duplicate {surah}:{ayah}")
    seen.add((surah, ayah))
    # Stored exactly as supplied: no normalization, trimming or re-encoding (FR-QURAN-003).
    parsed.ayat.append((surah, ayah, text))


def _check_structure(parsed: ParsedDataset) -> None:
    if not parsed.ayat:
        raise DatasetError("dataset contains no ayat")
    by_surah: dict[int, list[int]] = {}
    for surah, ayah, _ in parsed.ayat:
        by_surah.setdefault(surah, []).append(ayah)
    for surah, numbers in by_surah.items():
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            raise DatasetError(f"surah {surah}: ayah numbering is not contiguous from 1")
        if surah not in parsed.surah_names:
            raise DatasetError(f"surah {surah}: missing '@surah|{surah}|<name>' line")


def _int(value: str, line_no: int) -> int:
    try:
        return int(value.strip())
    except ValueError as exc:
        raise DatasetError(f"line {line_no}: '{value}' is not a number") from exc


def _check_surah(number: int, line_no: int) -> None:
    if not 1 <= number <= MAX_SURAH:
        raise DatasetError(f"line {line_no}: surah number {number} is outside 1-{MAX_SURAH}")
