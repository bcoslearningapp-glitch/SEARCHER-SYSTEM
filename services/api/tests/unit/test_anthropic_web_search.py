"""Anthropic web-search result parsing against SDK types (no network)."""

from __future__ import annotations

from typing import Any

from anthropic.types.beta import BetaMessage

from research_api.modules.ai_gateway.anthropic_adapter import _collect
from research_api.modules.ai_gateway.base import WebResult


def _message(content: list[dict[str, Any]]) -> BetaMessage:
    return BetaMessage.model_validate(
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5",
            "content": content,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def test_results_are_attributed_to_their_query_and_errors_are_not_results() -> None:
    message = _message(
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
                        "page_age": "2 days",
                    }
                ],
            },
            {"type": "server_tool_use", "id": "t2", "name": "web_search", "input": {"query": "pay progression"}},
            {
                "type": "web_search_tool_result",
                "tool_use_id": "t2",
                "content": {"type": "web_search_tool_result_error", "error_code": "unavailable"},
            },
            {"type": "text", "text": "DONE"},
        ]
    )
    results: list[WebResult] = []
    queries: list[str] = []
    failed: list[str] = []
    _collect(message, results, queries, failed)
    assert results == [WebResult("https://example.org/a", "A", "mentoring retention", "2 days")]
    assert queries == ["mentoring retention", "pay progression"]
    assert failed == ["pay progression"]
