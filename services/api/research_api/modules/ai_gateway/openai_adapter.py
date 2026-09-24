"""OpenAI adapter. The only place that imports the OpenAI SDK (PRD §46.1)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import openai
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionReasoningEffort,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params import ResponseFormatJSONSchema
from openai.types.shared_params.response_format_json_schema import JSONSchema

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
_REASONING_EFFORT: dict[str, ChatCompletionReasoningEffort] = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "high",
    "max": "high",
}


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, *, timeout: float = 300.0, max_retries: int = 2) -> None:
        self._client = openai.OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)

    def generate_structured(self, request: StructuredRequest, profile: ModelProfile) -> StructuredResult:
        schema_name = re.sub(r"[^a-zA-Z0-9_-]", "_", request.task)[:64]
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=prompting.system_prompt(request)),
            ChatCompletionUserMessageParam(role="user", content=prompting.user_prompt(request)),
        ]
        response_format = ResponseFormatJSONSchema(
            type="json_schema",
            json_schema=JSONSchema(name=schema_name, schema=request.output_schema, strict=True),
        )
        effort: ChatCompletionReasoningEffort = _REASONING_EFFORT.get(profile.effort, "medium")
        try:
            response = self._client.chat.completions.create(
                model=profile.model,
                messages=messages,
                response_format=response_format,
                max_completion_tokens=min(request.max_tokens, profile.max_tokens),
                reasoning_effort=effort,
            )
        except (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError) as exc:
            raise ProviderUnavailableError(f"OpenAI unavailable: {type(exc).__name__}") from exc
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            raise ProviderUnavailableError("OpenAI credentials were rejected") from exc
        except openai.APIStatusError as exc:
            raise ProviderError(f"OpenAI request failed with status {exc.status_code}") from exc

        choice = response.choices[0]
        if choice.finish_reason == "content_filter" or choice.message.refusal:
            raise ProviderRefusalError("model declined the request")
        if choice.finish_reason == "length":
            raise ProviderOutputError("output was truncated")
        try:
            data: Any = json.loads(choice.message.content or "")
        except json.JSONDecodeError as exc:
            raise ProviderOutputError("structured output was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ProviderOutputError("structured output must be a JSON object")
        usage = response.usage
        return StructuredResult(
            data=data,
            provider=self.name,
            model=response.model,
            usage=Usage(usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0),
            request_id=getattr(response, "_request_id", None),
        )

    def healthcheck(self, profile: ModelProfile) -> bool:
        try:
            self._client.models.retrieve(profile.model)
        except openai.APIError:
            logger.warning("OpenAI healthcheck failed", exc_info=True)
            return False
        return True

    def capabilities(self) -> dict[str, bool]:
        return {"structured_output": True, "tool_use": True, "long_context": True}
