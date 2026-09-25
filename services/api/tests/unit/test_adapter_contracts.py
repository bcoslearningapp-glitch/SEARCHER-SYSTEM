"""Adapter contract tests run in normal CI against the mock and reference implementations (PRD §73)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway.base import ModelProfile, WebResult, WebSearchRequest
from research_api.modules.ai_gateway.mock_adapter import MockProvider
from research_api.modules.cloud_workspace.adapters import LocalDirectoryAdapter
from tests.adapter_contracts import check_cloud_workspace, check_search_outage, check_search_provider

PROFILE = ModelProfile(name="mock", provider="mock", model="mock-1", effort="low")


@pytest.fixture
def web_results() -> Iterator[None]:
    mock_adapter.STATE.web_results["mentoring retention"] = [
        WebResult(url="https://example.org/study", title="Mentoring study", query="mentoring retention")
    ]
    yield
    mock_adapter.STATE.web_results.clear()
    mock_adapter.STATE.web_calls.clear()


def test_mock_provider_satisfies_the_search_contract(web_results: None) -> None:
    request = WebSearchRequest(queries=["mentoring retention", "second", "third"], max_searches=2)
    result = check_search_provider(MockProvider(), PROFILE, request)
    assert result.queries_run == ["mentoring retention", "second"]
    assert [r.url for r in result.results] == ["https://example.org/study"]


def test_mock_outage_is_an_error_not_an_empty_result() -> None:
    check_search_outage(MockProvider(mode="unavailable"), PROFILE, WebSearchRequest(queries=["q"], max_searches=1))


def test_local_directory_adapter_satisfies_the_workspace_contract(tmp_path: Path) -> None:
    adapter = LocalDirectoryAdapter(tmp_path / "ws")
    check_cloud_workspace(adapter, "contract-1", b'{"k": 1}')
    assert adapter.remote is True, "the reference adapter is treated as remote for disclosure"


def test_anthropic_adapter_satisfies_the_search_contract_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    from research_api.modules.ai_gateway.anthropic_adapter import AnthropicProvider  # noqa: PLC0415
    from tests.unit.test_anthropic_web_search import _message  # noqa: PLC0415

    reply = _message(
        [
            {"type": "server_tool_use", "id": "t1", "name": "web_search", "input": {"query": "mentoring retention"}},
            {
                "type": "web_search_tool_result",
                "tool_use_id": "t1",
                "content": [
                    {
                        "type": "web_search_result",
                        "url": "https://example.org/a",
                        "title": "A",
                        "encrypted_content": "x",
                    }
                ],
            },
        ]
    )
    provider = AnthropicProvider(api_key="offline-test")
    monkeypatch.setattr(provider, "_send", lambda **_: reply)
    profile = ModelProfile(name="anthropic-default", provider="anthropic", model="claude-opus-5")
    result = check_search_provider(provider, profile, WebSearchRequest(queries=["mentoring retention"], max_searches=1))
    assert [r.url for r in result.results] == ["https://example.org/a"]


def test_openai_adapter_declares_no_web_search_and_refuses_as_unavailable() -> None:
    from research_api.modules.ai_gateway.openai_adapter import OpenAIProvider  # noqa: PLC0415

    profile = ModelProfile(name="openai-default", provider="openai", model="gpt-5")
    check_search_provider(
        OpenAIProvider(api_key="offline-test"), profile, WebSearchRequest(queries=["q"], max_searches=1)
    )
