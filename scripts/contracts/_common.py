"""Shared helpers for Research Core contract tooling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "packages" / "research-core-contracts"
SCHEMA_DIR = CONTRACTS_DIR / "schema"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"

PY_ENUMS_PATH = REPO_ROOT / "services" / "api" / "research_api" / "contracts" / "enums.py"
TS_ENUMS_PATH = REPO_ROOT / "apps" / "web" / "src" / "lib" / "contracts" / "enums.ts"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest() -> dict[str, Any]:
    manifest: dict[str, Any] = load_json(CONTRACTS_DIR / "manifest.json")
    return manifest


def load_enums() -> dict[str, dict[str, Any]]:
    enums: dict[str, dict[str, Any]] = load_json(SCHEMA_DIR / "enums.schema.json")["$defs"]
    return enums
