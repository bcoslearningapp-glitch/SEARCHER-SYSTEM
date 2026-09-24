"""Anthropic adapter. The only place that imports the Anthropic SDK (PRD §46.1)."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from anthropic.types.beta import BetaMessageParam, BetaOutputConfigParam, BetaThinkingConfigAdaptiveParam

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
)

logger = logging.getLogger(__name__)

# Server-side refusal fallback: on a policy decline the API re-runs the request on a
# fallback model inside the same call (enabled by default for current models).
FALLBACK_BETA = "server-side-fallback-2026-07-01"


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

    def healthcheck(self, profile: ModelProfile) -> bool:
        try:
            self._client.models.retrieve(profile.model)
        except anthropic.APIError:
            logger.warning("Anthropic healthcheck failed", exc_info=True)
            return False
        return True

    def capabilities(self) -> dict[str, bool]:
        return {"structured_output": True, "tool_use": True, "long_context": True}
