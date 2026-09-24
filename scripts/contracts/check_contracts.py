"""Validate the Research Core contract package.

Checks:
1. every schema is a valid JSON Schema (draft 2020-12);
2. every example under examples/valid validates against its target;
3. every example under examples/invalid is rejected by its target;
4. enum values are unique, UPPER_SNAKE (except LanguageCode) and non-empty;
5. no AI-provider-specific vocabulary leaks into the contracts (PRD §59).

Example directories are named "<schema-file-stem>" or "<schema-file-stem>.<$defs name>".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from _common import CONTRACTS_DIR, EXAMPLES_DIR, SCHEMA_DIR, load_enums, load_json, load_manifest

PROVIDER_TERMS = re.compile(r"\b(openai|anthropic|gpt-|claude-|gemini)\b", re.IGNORECASE)
UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def build_registry() -> tuple[Registry, dict[str, Any]]:
    schemas: dict[str, Any] = {}
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = load_json(path)
        schemas[path.name] = schema
        resource = Resource.from_contents(schema)
        resources.append((schema["$id"], resource))
        resources.append((path.name, resource))
    return Registry().with_resources(resources), schemas


def validator_for(target: str, registry: Registry, schemas: dict[str, Any]) -> Draft202012Validator:
    stem, _, definition = target.partition(".")
    schema = schemas[f"{stem}.schema.json"]
    ref_schema: dict[str, Any] = {"$ref": schema["$id"] + (f"#/$defs/{definition}" if definition else "")}
    return Draft202012Validator(ref_schema, registry=registry, format_checker=FormatChecker())


def main() -> int:
    errors: list[str] = []
    registry, schemas = build_registry()

    manifest = load_manifest()
    listed = {Path(p).name for p in manifest["schemas"]}
    if listed != set(schemas):
        errors.append(f"manifest schemas {sorted(listed)} != files {sorted(schemas)}")

    for name, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001 - report every schema error
            errors.append(f"{name}: invalid schema: {exc}")

    for name, spec in load_enums().items():
        values = spec.get("enum", [])
        if not values:
            errors.append(f"enum {name} is empty")
        if len(values) != len(set(values)):
            errors.append(f"enum {name} has duplicate values")
        if name != "LanguageCode":
            bad = [v for v in values if not UPPER_SNAKE.match(v)]
            if bad:
                errors.append(f"enum {name} has non UPPER_SNAKE values: {bad}")

    for path in sorted(CONTRACTS_DIR.rglob("*.json")):
        if PROVIDER_TERMS.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(CONTRACTS_DIR)}: contains AI-provider-specific vocabulary")

    counts = {"valid": 0, "invalid": 0}
    for kind in ("valid", "invalid"):
        for target_dir in sorted((EXAMPLES_DIR / kind).iterdir()):
            validator = validator_for(target_dir.name, registry, schemas)
            for example in sorted(target_dir.glob("*.json")):
                counts[kind] += 1
                problems = list(validator.iter_errors(load_json(example)))
                rel = example.relative_to(CONTRACTS_DIR)
                if kind == "valid" and problems:
                    errors.append(f"{rel}: expected valid, got: {problems[0].message}")
                if kind == "invalid" and not problems:
                    errors.append(f"{rel}: expected rejection but it validated")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    valid, invalid = counts["valid"], counts["invalid"]
    print(f"contracts OK: {len(schemas)} schemas, {valid} valid and {invalid} invalid examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
