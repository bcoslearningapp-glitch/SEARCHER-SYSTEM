"""The registry refuses tool definitions that could let a model widen its own scope."""

from __future__ import annotations

from typing import Any

import pytest

from research_api.modules.ai_tools import tools as _tools  # noqa: F401 - registers the tools
from research_api.modules.ai_tools.registry import TOOLS, Tool, register


def _noop(*_args: Any) -> dict[str, Any]:
    return {}


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "properties": {}},
        {"type": "object", "properties": {"project_id": {"type": "string"}}, "additionalProperties": False},
    ],
)
def test_open_or_project_scoped_schemas_are_rejected(schema: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="never take a project id"):
        register(Tool("bad_tool", "READ", "x", schema, _noop))
    assert "bad_tool" not in TOOLS


def test_every_proposal_tool_requires_model_provenance() -> None:
    for tool in TOOLS.values():
        if tool.kind == "PROPOSE":
            assert tool.needs_ai_action, tool.name
