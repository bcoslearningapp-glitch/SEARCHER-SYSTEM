"""Reusable contract checks for adapter interfaces (PRD §73 contract tests).

Every implementation of an interface must satisfy the same checks. CI runs them against the mock or
reference implementation, and the protected provider-contract workflow runs them against live providers.
"""

from __future__ import annotations

from typing import Any

import pytest

from research_api.modules.ai_gateway.base import (
    AIProvider,
    ModelProfile,
    ProviderError,
    ProviderUnavailableError,
    WebSearchRequest,
    WebSearchResult,
)
from research_api.modules.cloud_workspace.adapters import CloudWorkspaceAdapter, WorkspaceError


def check_search_provider(provider: AIProvider, profile: ModelProfile, request: WebSearchRequest) -> WebSearchResult:
    """SearchProvider contract (FR-WEB-001..003, ADR-012).

    - a provider that does not declare web search refuses as unavailable, never as "no results";
    - a result is attributed, bounded by the request, and contains only http(s) links with titles.
    """
    if not provider.capabilities().get("web_search"):
        with pytest.raises(ProviderUnavailableError):
            provider.web_search(request, profile)
        return WebSearchResult(results=[], queries_run=[], provider=provider.name, model=profile.model)
    result = provider.web_search(request, profile)
    assert isinstance(result, WebSearchResult)
    assert result.provider == provider.name
    assert result.model
    assert len(result.queries_run) <= request.max_searches, "the search budget is respected"
    assert set(result.failed_queries) <= set(request.queries) | set(result.queries_run)
    for hit in result.results:
        assert hit.url.startswith(("http://", "https://")), hit.url
        assert hit.title.strip() or hit.url
    assert min(result.usage.input_tokens, result.usage.output_tokens, result.usage.web_search_requests) >= 0
    return result


def check_search_outage(provider: AIProvider, profile: ModelProfile, request: WebSearchRequest) -> None:
    """An outage is a provider error, never an empty result that could read as 'nothing found' (PRD §72)."""
    with pytest.raises(ProviderError):
        provider.web_search(request, profile)


def check_cloud_workspace(adapter: CloudWorkspaceAdapter, key: str, payload: bytes) -> dict[str, Any]:
    """CloudWorkspaceAdapter contract (FR-CLOUD-004..007, ADR-023)."""
    assert adapter.name and isinstance(adapter.remote, bool)
    ref = adapter.put(key, payload)
    assert isinstance(ref, str) and ref, "put returns a reference"
    assert adapter.exists(ref)
    adapter.delete(ref)
    assert not adapter.exists(ref)
    adapter.delete(ref)  # deleting what is already gone is not an error
    for bad in ("../escape", "a/b", "", "x" * 129):
        with pytest.raises(WorkspaceError):
            adapter.put(bad, payload)
    return {"ref": ref}
