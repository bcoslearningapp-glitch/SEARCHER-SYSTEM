"""Cloud workspace adapters (FR-CLOUD-007, ADR-023).

An adapter stores and deletes staged payloads in a workspace outside the canonical database. It receives
only the bytes of explicitly selected items, never database credentials (FR-CLOUD-004), and it never reads
anything back into canonical state (FR-CLOUD-005).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from research_api.config import Settings

_KEY = re.compile(r"^[A-Za-z0-9-]{1,128}$")


class WorkspaceError(Exception):
    """The workspace could not store or delete content."""


class CloudWorkspaceAdapter(Protocol):
    name: str
    # Whether staged content leaves this installation. Disclosure policy applies whenever it does.
    remote: bool

    def put(self, key: str, payload: bytes) -> str:
        """Store a payload and return its reference in the workspace."""
        ...

    def delete(self, ref: str) -> None:
        """Remove a payload. Deleting a payload that is already gone is not an error."""
        ...

    def exists(self, ref: str) -> bool: ...


class LocalDirectoryAdapter:
    """Reference adapter: a sandboxed directory that stands in for a remote workspace.

    It is treated as remote for disclosure, so the same policy checks run as for a real provider.
    """

    name = "local-directory"
    remote = True

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path(self, key: str) -> Path:
        if not _KEY.fullmatch(key):
            raise WorkspaceError("invalid workspace key")
        path = (self.root / f"{key}.json").resolve()
        if path.parent != self.root:
            raise WorkspaceError("workspace key escapes the workspace root")
        return path

    def put(self, key: str, payload: bytes) -> str:
        path = self._path(key)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        except OSError as exc:
            raise WorkspaceError("the workspace could not store the payload") from exc
        return key

    def delete(self, ref: str) -> None:
        try:
            self._path(ref).unlink(missing_ok=True)
        except OSError as exc:
            raise WorkspaceError("the workspace could not delete the payload") from exc

    def exists(self, ref: str) -> bool:
        return self._path(ref).is_file()


def configured(settings: Settings) -> CloudWorkspaceAdapter | None:
    if settings.cloud_workspace_adapter == "local-directory":
        return LocalDirectoryAdapter(settings.cloud_workspace_root)
    return None
