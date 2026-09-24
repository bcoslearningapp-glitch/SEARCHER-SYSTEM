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
        ("1|1|a\n", "missing surah name"),
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


def _kfgqpc(records: list[dict[str, object]]) -> bytes:
    import json  # noqa: PLC0415

    return json.dumps(records, ensure_ascii=False).encode("utf-8-sig")


def _record(surah: int, ayah: int, text: str, name: str = "سورة تجريبية ") -> dict[str, object]:
    # Same shape as KFGQPC developer data (e.g. warshData_v10.json); the text is a synthetic placeholder.
    return {
        "id": ayah,
        "jozz": 1,
        "page": "1",
        "sura_no": surah,
        "sura_name_en": "Placeholder",
        "sura_name_ar": name,
        "line_start": 1,
        "line_end": 1,
        "aya_no": ayah,
        "aya_text": text,
    }


def test_kfgqpc_json_is_imported_as_published() -> None:
    data = _kfgqpc([_record(1, 1, "PLACEHOLDER-1-1\xa0"), _record(1, 2, "PLACEHOLDER-1-2\xa0"), _record(2, 1, "P-2-1")])
    parsed = parse(data)
    assert parsed.format == "kfgqpc-json"
    assert parsed.surah_count == 2 and len(parsed.ayat) == 3
    assert parsed.ayat[0][2] == "PLACEHOLDER-1-1\xa0", "publisher spacing is kept exactly"
    assert parsed.surah_names[1] == "سورة تجريبية"
    import hashlib  # noqa: PLC0415

    assert parsed.sha256 == hashlib.sha256(data).hexdigest(), "fingerprint is the publisher's file"


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ([_record(1, 2, "x")], "not contiguous"),
        ([_record(1, 1, "x"), _record(1, 1, "y")], "duplicate"),
        ([_record(1, 1, "  ")], "empty ayah text"),
        ([_record(115, 1, "x")], "outside 1-114"),
        ([{"sura_no": 1, "aya_no": 1}], "missing 'aya_text'"),
        ([{**_record(1, 1, "x", name=""), "sura_name_en": ""}], "sura_name_ar"),
    ],
)
def test_kfgqpc_structural_errors_are_rejected(records: list[dict[str, object]], message: str) -> None:
    with pytest.raises(DatasetError, match=message):
        parse(_kfgqpc(records))


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(DatasetError, match="invalid JSON"):
        parse(b'[{"sura_no": 1,')
