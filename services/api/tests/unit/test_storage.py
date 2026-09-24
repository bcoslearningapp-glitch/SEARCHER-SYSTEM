from pathlib import Path

import pytest

from research_api.config import get_settings
from research_api.platform.storage import (
    LocalObjectStore,
    StorageError,
    TooLargeError,
    UnsupportedMediaError,
    safe_filename,
    sniff_media_type,
    validate_upload,
)
from tests.pdf_fixtures import make_pdf


def test_content_addressed_and_idempotent(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path)
    first = store.put(b"hello")
    second = store.put(b"hello")
    assert first == second
    assert first.key.startswith("sha256/")
    assert store.read(first.key) == b"hello"


@pytest.mark.parametrize(
    "key", ["../../etc/passwd", "sha256/aa/bb/../../../x", "/etc/passwd", "sha256/zz/zz/" + "0" * 64]
)
def test_rejects_keys_outside_the_sandbox(tmp_path: Path, key: str) -> None:
    with pytest.raises(StorageError):
        LocalObjectStore(tmp_path).read(key)


def test_detects_tampered_objects(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path)
    obj = store.put(b"original")
    path = tmp_path / obj.key
    path.chmod(0o644)
    path.write_bytes(b"tampered")
    with pytest.raises(StorageError, match="integrity"):
        store.read(obj.key)


def test_media_is_sniffed_not_trusted() -> None:
    assert sniff_media_type(make_pdf(["x"])) == "application/pdf"
    assert sniff_media_type("نص عربي".encode()) == "text/plain"
    assert sniff_media_type(b"\x7fELF\x02\x01\x00") is None


def test_rejects_executables_empty_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(UnsupportedMediaError):
        validate_upload(b"MZ\x90\x00\x03\x00")
    with pytest.raises(UnsupportedMediaError):
        validate_upload(b"")
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 4)
    with pytest.raises(TooLargeError):
        validate_upload(b"too large")


def test_safe_filename_strips_paths_and_controls() -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("C:\\Users\\x\\book.pdf") == "book.pdf"
    assert safe_filename("a\x00b.pdf") == "ab.pdf"
    assert safe_filename("..") is None
