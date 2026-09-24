"""Architecture guards for CLAUDE.md invariants.

- Provider SDKs are imported only inside modules/ai_gateway (PRD §46.1).
- Domain modules never import another module's `models` (PRD §58).
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "research_api"
PROVIDER_SDKS = {"anthropic", "openai"}


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _python_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def test_provider_sdks_only_in_ai_gateway() -> None:
    offenders = []
    for path in _python_files():
        if "ai_gateway" in path.parts:
            continue
        for name in _imports(path):
            if name.split(".")[0] in PROVIDER_SDKS:
                offenders.append(f"{path.relative_to(PACKAGE)} imports {name}")
    assert offenders == []


def test_modules_do_not_reach_into_other_modules_models() -> None:
    offenders = []
    modules_dir = PACKAGE / "modules"
    for path in _python_files():
        if modules_dir not in path.parents:
            continue
        own = path.relative_to(modules_dir).parts[0]
        for name in _imports(path):
            parts = name.split(".")
            is_module_import = parts[:2] == ["research_api", "modules"] and len(parts) >= 4
            if is_module_import and parts[2] != own and parts[3] == "models":
                offenders.append(f"{path.relative_to(PACKAGE)} imports {name}")
    assert offenders == []
