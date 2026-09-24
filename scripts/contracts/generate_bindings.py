"""Generate Python and TypeScript enum bindings from the canonical contracts.

Usage:
    python scripts/contracts/generate_bindings.py          # write bindings
    python scripts/contracts/generate_bindings.py --check  # fail if stale

The JSON Schema in packages/research-core-contracts is the single source of
truth; generated files must never be edited by hand.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import PY_ENUMS_PATH, REPO_ROOT, TS_ENUMS_PATH, load_enums, load_manifest

HEADER = "GENERATED FILE - DO NOT EDIT. Source: packages/research-core-contracts/schema/enums.schema.json"


def render_python() -> str:
    manifest = load_manifest()
    lines = [
        f'"""{HEADER}',
        "",
        "Regenerate with: python scripts/contracts/generate_bindings.py",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        f'RESEARCH_CORE_VERSION = "{manifest["research_core_version"]}"',
        f'CONTRACT_SCHEMA_VERSION = "{manifest["schema_version"]}"',
    ]
    for name, spec in load_enums().items():
        lines += ["", "", f"class {name}(StrEnum):", f'    """{spec["description"]}"""', ""]
        for value in spec["enum"]:
            member = value.upper()
            lines.append(f'    {member} = "{value}"')
    return "\n".join(lines) + "\n"


def render_typescript() -> str:
    manifest = load_manifest()
    lines = [
        f"// {HEADER}",
        "// Regenerate with: python scripts/contracts/generate_bindings.py",
        "",
        f'export const RESEARCH_CORE_VERSION = "{manifest["research_core_version"]}";',
        f'export const CONTRACT_SCHEMA_VERSION = "{manifest["schema_version"]}";',
    ]
    for name, spec in load_enums().items():
        values = ", ".join(f'"{v}"' for v in spec["enum"])
        lines += [
            "",
            f"/** {spec['description']} */",
            f"export const {name}Values = [{values}] as const;",
            f"export type {name} = (typeof {name}Values)[number];",
        ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()

    outputs: dict[Path, str] = {PY_ENUMS_PATH: render_python(), TS_ENUMS_PATH: render_typescript()}
    stale = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(path.relative_to(REPO_ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path.relative_to(REPO_ROOT)}")
    if stale:
        for path in stale:
            print(f"STALE: {path} (run python scripts/contracts/generate_bindings.py)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
