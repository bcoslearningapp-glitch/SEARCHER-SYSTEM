"""Validate payloads against the canonical Research Core JSON Schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from research_api.config import get_settings


def _schema_dir() -> Path:
    return get_settings().contracts_dir / "schema"


@lru_cache(maxsize=1)
def _registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    schemas: dict[str, dict[str, Any]] = {}
    resources = []
    for path in sorted(_schema_dir().glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas[path.name.removesuffix(".schema.json")] = schema
        resource = Resource.from_contents(schema)
        resources.append((schema["$id"], resource))
        resources.append((path.name, resource))
    return Registry().with_resources(resources), schemas


def contract_errors(target: str, payload: Any) -> list[str]:
    """Return validation messages for `payload` against `target`.

    `target` is "<schema stem>" or "<schema stem>.<$defs name>", e.g. "event.AuditEvent".
    """
    registry, schemas = _registry()
    stem, _, definition = target.partition(".")
    base_id = schemas[stem]["$id"]
    ref = base_id + (f"#/$defs/{definition}" if definition else "")
    validator = Draft202012Validator({"$ref": ref}, registry=registry, format_checker=FormatChecker())
    return [error.message for error in validator.iter_errors(payload)]
