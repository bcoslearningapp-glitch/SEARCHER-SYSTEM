"""Deterministic local provider for tests, CI and demos (GITHUB_SETUP §14: CI uses mocks).

It is never selected unless explicitly enabled (ADR-010). Responders are
registered per task; `mode` simulates outages and malformed output.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from research_api.modules.ai_gateway import prompting
from research_api.modules.ai_gateway.base import (
    ModelProfile,
    ProviderOutputError,
    ProviderUnavailableError,
    StructuredRequest,
    StructuredResult,
    Usage,
)

Responder = Callable[[StructuredRequest], dict[str, Any]]


@dataclass
class MockState:
    mode: Literal["ok", "unavailable", "invalid"] = "ok"
    responders: dict[str, Responder] = field(default_factory=dict)
    calls: list[StructuredRequest] = field(default_factory=list)


STATE = MockState()


def register(task: str, responder: Responder) -> None:
    STATE.responders[task] = responder


class MockProvider:
    name = "mock"

    def __init__(self, mode: Literal["ok", "unavailable", "invalid"] = "ok") -> None:
        self._configured_mode = mode

    def _mode(self) -> str:
        # A mode set in-process (tests) overrides the configured one (AI_MOCK_MODE).
        return STATE.mode if STATE.mode != "ok" else self._configured_mode

    def generate_structured(self, request: StructuredRequest, profile: ModelProfile) -> StructuredResult:
        STATE.calls.append(request)
        mode = self._mode()
        if mode == "unavailable":
            raise ProviderUnavailableError("mock provider is simulating an outage")
        responder = STATE.responders.get(request.task)
        if mode == "invalid" or responder is None:
            raise ProviderOutputError(f"mock has no valid output for task '{request.task}'")
        chars = prompting.outbound_chars(request)
        return StructuredResult(
            data=responder(request), provider=self.name, model=profile.model, usage=Usage(chars // 4, 200)
        )

    def healthcheck(self, profile: ModelProfile) -> bool:
        return self._mode() != "unavailable"

    def capabilities(self) -> dict[str, bool]:
        return {"structured_output": True, "tool_use": False, "long_context": True}
