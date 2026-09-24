"""Anthropic adapter. The only place that imports the Anthropic SDK (PRD §46.1)."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from anthropic.types.beta import (
    BetaMessage,
    BetaMessageParam,
    BetaOutputConfigParam,
    BetaThinkingConfigAdaptiveParam,
    BetaWebSearchTool20260209Param,
)

from research_api.modules.ai_gateway import prompting
from research_api.modules.ai_gateway.base import (
    ModelProfile,
    ProviderError,
    ProviderOutputError,
    ProviderRefusalError,
    ProviderUnavailableError,
    StructuredRequest,
    StructuredResult,
    Usage,
    WebResult,
    WebSearchRequest,
    WebSearchResult,
)

logger = logging.getLogger(__name__)

# Server-side refusal fallback: on a policy decline the API re-runs the request on a
# fallback model inside the same call (enabled by default for current models).
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_CONTINUATIONS = 3
SEARCH_RUNNER_PROMPT = (
    "You run web searches for a research application. Call the web_search tool once for each query in the "
    "user message, using the query text as given. Do not answer, summarise or add queries. When all searches "
    "are done, reply with the single word DONE."
)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, *, timeout: float = 300.0, max_retries: int = 2) -> None:
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=max_retries)

    def generate_structured(self, request: StructuredRequest, profile: ModelProfile) -> StructuredResult:
        messages: list[BetaMessageParam] = [{"role": "user", "content": prompting.user_prompt(request)}]
        thinking: BetaThinkingConfigAdaptiveParam = {"type": "adaptive"}
        output_config: BetaOutputConfigParam = {
            "effort": profile.effort,  # type: ignore[typeddict-item]
            "format": {"type": "json_schema", "schema": request.output_schema},
        }
        try:
            response = self._client.beta.messages.create(
                model=profile.model,
                max_tokens=min(request.max_tokens, profile.max_tokens),
                system=prompting.system_prompt(request),
                messages=messages,
                thinking=thinking,
                output_config=output_config,
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError) as exc:
            raise ProviderUnavailableError(f"Anthropic unavailable: {type(exc).__name__}") from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise ProviderUnavailableError("Anthropic credentials were rejected") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"Anthropic request failed with status {exc.status_code}") from exc

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None) if response.stop_details else None
            raise ProviderRefusalError(f"model declined the request (category: {category})")
        if response.stop_reason == "max_tokens":
            raise ProviderOutputError("output was truncated at max_tokens")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise ProviderOutputError("no structured output returned")
        try:
            data: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderOutputError("structured output was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderOutputError("structured output must be a JSON object")
        iterations = getattr(response.usage, "iterations", None) or []
        return StructuredResult(
            data=data,
            provider=self.name,
            model=response.model,
            usage=Usage(response.usage.input_tokens, response.usage.output_tokens),
            request_id=getattr(response, "_request_id", None),
            served_by_fallback=any(getattr(i, "type", None) == "fallback_message" for i in iterations),
        )

    def web_search(self, request: WebSearchRequest, profile: ModelProfile) -> WebSearchResult:
        """Provider-native search. Only direct calls, so every result block comes back to us unfiltered."""
        tool: BetaWebSearchTool20260209Param = {
            "type": "web_search_20260209",
            "name": "web_search",
            "max_uses": request.max_searches,
            "allowed_callers": ["direct"],
        }
        queries = "\n".join(f"- {q}" for q in request.queries[: request.max_searches])
        messages: list[BetaMessageParam] = [{"role": "user", "content": f"Queries:\n{queries}"}]
        output_config: BetaOutputConfigParam = {"effort": "low"}
        results: list[WebResult] = []
        queries_run: list[str] = []
        failed: list[str] = []
        searches = input_tokens = output_tokens = 0
        response: BetaMessage | None = None
        for _ in range(MAX_CONTINUATIONS + 1):
            response = self._send(
                model=profile.model,
                max_tokens=2000,
                system=SEARCH_RUNNER_PROMPT,
                messages=messages,
                tools=[tool],
                output_config=output_config,
            )
            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens
            if response.usage.server_tool_use is not None:
                searches += response.usage.server_tool_use.web_search_requests
            _collect(response, results, queries_run, failed)
            if response.stop_reason != "pause_turn":
                break
            # Resume the server-side loop: resend with the paused assistant turn (no extra user message).
            messages = [messages[0], {"role": "assistant", "content": response.content}]
        if response is not None and response.stop_reason == "refusal":
            raise ProviderRefusalError("model declined to run the searches")
        if queries_run and len(failed) == len(queries_run):
            raise ProviderUnavailableError("every web search failed")
        return WebSearchResult(
            results=results,
            queries_run=queries_run,
            provider=self.name,
            model=response.model if response is not None else profile.model,
            usage=Usage(input_tokens, output_tokens, searches),
            request_id=getattr(response, "_request_id", None),
            failed_queries=failed,
        )

    def _send(self, **params: Any) -> BetaMessage:
        try:
            message: BetaMessage = self._client.beta.messages.create(**params)
            return message
        except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError) as exc:
            raise ProviderUnavailableError(f"Anthropic unavailable: {type(exc).__name__}") from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise ProviderUnavailableError("Anthropic credentials were rejected") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"Anthropic request failed with status {exc.status_code}") from exc

    def healthcheck(self, profile: ModelProfile) -> bool:
        try:
            self._client.models.retrieve(profile.model)
        except anthropic.APIError:
            logger.warning("Anthropic healthcheck failed", exc_info=True)
            return False
        return True

    def capabilities(self) -> dict[str, bool]:
        return {"structured_output": True, "tool_use": True, "long_context": True, "web_search": True}


def _collect(response: BetaMessage, results: list[WebResult], queries_run: list[str], failed: list[str]) -> None:
    queries: dict[str, str] = {}
    for block in response.content:
        if block.type == "server_tool_use" and block.name == "web_search":
            text = str(block.input.get("query", ""))
            queries[block.id] = text
            queries_run.append(text)
        elif block.type == "web_search_tool_result":
            query: str | None = queries.get(block.tool_use_id)
            if isinstance(block.content, list):
                results.extend(WebResult(r.url, r.title, query, r.page_age) for r in block.content)
            else:
                logger.warning("web search error: %s", block.content.error_code)
                failed.append(query or block.tool_use_id)
