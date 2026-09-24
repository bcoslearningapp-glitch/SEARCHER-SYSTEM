"""Structural validation of an imported Qur'an dataset. Fixtures are synthetic placeholders, never real text."""

import pytest

from research_api.modules.reference_governance.quran_dataset import DatasetError, parse

VALID = (
    "# synthetic test fixture - not Qur'anic text\n"
    "@surah|1|Placeholder Surah One\n"
    "@surah|2|Placeholder Surah Two\n"
    "1|1|PLACEHOLDER-1-1 نص تجريبي\n"
    "1|2|PLACEHOLDER-1-2  trailing  \n"
    "2|1|PLACEHOLDER-2-1\n"
)


def test_valid_dataset_is_parsed_and_fingerprinted() -> None:
    parsed = parse(VALID.encode())
    assert parsed.surah_count == 2
    assert len(parsed.ayat) == 3
    assert len(parsed.sha256) == 64


def test_text_is_preserved_byte_for_byte() -> None:
    parsed = parse(VALID.encode())
    assert parsed.ayat[1][2] == "PLACEHOLDER-1-2  trailing  ", "no trimming or normalization"
    assert parsed.ayat[0][2] == "PLACEHOLDER-1-1 نص تجريبي"


@pytest.mark.parametrize(
    ("dataset", "message"),
    [
        ("@surah|1|S\n1|1|a\n1|1|b\n", "duplicate"),
        ("@surah|1|S\n1|1|a\n1|3|b\n", "contiguous"),
        ("1|1|a\n", "missing '@surah"),
        ("@surah|115|S\n115|1|a\n", "outside 1-114"),
        ("@surah|1|S\nx|1|a\n", "not a number"),
        ("@surah|1|S\n1|1|   \n", "empty ayah text"),
        ("# only comments\n", "no ayat"),
    ],
)
def test_structural_errors_are_rejected(dataset: str, message: str) -> None:
    with pytest.raises(DatasetError, match=message):
        parse(dataset.encode())


def test_non_utf8_is_rejected() -> None:
    with pytest.raises(DatasetError, match="UTF-8"):
        parse(b"\xff\xfe\x00bad")
