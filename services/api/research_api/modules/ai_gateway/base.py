"""Provider-neutral AI interface (PRD §46.1). Nothing here knows about a specific vendor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

SectionKind = Literal["context", "retrieved_source", "user_input", "tool_result"]


@dataclass(frozen=True)
class Section:
    """A labelled block of prompt context (FR-PROMPT-003). Retrieved sources are always untrusted."""

    kind: SectionKind
    title: str
    content: str
    source_id: str | None = None

    @property
    def untrusted(self) -> bool:
        return self.kind in ("retrieved_source", "tool_result")


@dataclass(frozen=True)
class StructuredRequest:
    task: str
    template_version: str
    instructions: str
    sections: list[Section]
    output_schema: dict[str, Any]
    max_tokens: int = 16000


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class StructuredResult:
    data: dict[str, Any]
    provider: str
    model: str
    usage: Usage = field(default_factory=Usage)
    request_id: str | None = None
    served_by_fallback: bool = False


@dataclass(frozen=True)
class ModelProfile:
    """Configurable model choice; model ids are configuration, never product logic (PRD §46.2)."""

    name: str
    provider: Literal["anthropic", "openai", "mock"]
    model: str
    effort: str = "high"
    max_tokens: int = 16000
    input_usd_per_mtok: float = 0.0
    output_usd_per_mtok: float = 0.0
    local: bool = False  # True only for providers that keep data on this machine

    def estimate_cost(self, usage: Usage) -> float:
        return (usage.input_tokens * self.input_usd_per_mtok + usage.output_tokens * self.output_usd_per_mtok) / 1e6


class ProviderError(Exception):
    """Base for failures on the provider side; distinct from application errors (PRD §72)."""

    kind = "PROVIDER_ERROR"


class ProviderUnavailableError(ProviderError):
    """Network failure, outage, rate limit after retries, or no provider configured."""


class ProviderRefusalError(ProviderError):
    kind = "PROVIDER_REFUSAL"


class ProviderOutputError(ProviderError):
    """Output was truncated or not valid for the requested schema."""

    kind = "INVALID_STRUCTURED_OUTPUT"


class AIProvider(Protocol):
    name: str

    def generate_structured(self, request: StructuredRequest, profile: ModelProfile) -> StructuredResult: ...

    def healthcheck(self, profile: ModelProfile) -> bool: ...

    def capabilities(self) -> dict[str, bool]: ...
