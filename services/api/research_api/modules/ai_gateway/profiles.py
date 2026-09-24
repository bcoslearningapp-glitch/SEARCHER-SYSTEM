"""Model profiles and provider selection (PRD §46.2, ADR-010).

A profile names a provider + model + effort + prices. Adapters are created
lazily from configured keys; a profile whose provider has no key is listed
but not usable, and the product keeps working without cloud AI (NFR-REL-001).
"""

from __future__ import annotations

from research_api.config import Settings
from research_api.modules.ai_gateway.base import AIProvider, ModelProfile, ProviderUnavailableError

_PROVIDERS: dict[str, AIProvider] = {}


def profiles(settings: Settings) -> dict[str, ModelProfile]:
    found = [
        ModelProfile(
            name="anthropic-default",
            provider="anthropic",
            model=settings.anthropic_model,
            effort=settings.anthropic_effort,
            max_tokens=settings.ai_max_output_tokens,
            input_usd_per_mtok=settings.anthropic_input_usd_per_mtok,
            output_usd_per_mtok=settings.anthropic_output_usd_per_mtok,
        ),
        ModelProfile(
            name="openai-default",
            provider="openai",
            model=settings.openai_model,
            effort=settings.openai_effort,
            max_tokens=settings.ai_max_output_tokens,
            input_usd_per_mtok=settings.openai_input_usd_per_mtok,
            output_usd_per_mtok=settings.openai_output_usd_per_mtok,
        ),
    ]
    if settings.ai_mock_enabled:
        # The mock keeps everything on this machine, so it is treated as a local provider.
        found.append(ModelProfile(name="mock", provider="mock", model="mock-structured-1", local=True))
    return {p.name: p for p in found}


def is_configured(settings: Settings, profile: ModelProfile) -> bool:
    if profile.provider == "anthropic":
        return settings.anthropic_api_key is not None
    if profile.provider == "openai":
        return settings.openai_api_key is not None
    return settings.ai_mock_enabled


def provider_for(settings: Settings, profile: ModelProfile) -> AIProvider:
    if not is_configured(settings, profile):
        raise ProviderUnavailableError(f"provider '{profile.provider}' is not configured")
    if profile.provider not in _PROVIDERS:
        _PROVIDERS[profile.provider] = _build(settings, profile.provider)
    return _PROVIDERS[profile.provider]


def _build(settings: Settings, provider: str) -> AIProvider:
    timeout = settings.ai_request_timeout_seconds
    if provider == "anthropic" and settings.anthropic_api_key is not None:
        from research_api.modules.ai_gateway.anthropic_adapter import AnthropicProvider  # noqa: PLC0415

        return AnthropicProvider(settings.anthropic_api_key.get_secret_value(), timeout=timeout)
    if provider == "openai" and settings.openai_api_key is not None:
        from research_api.modules.ai_gateway.openai_adapter import OpenAIProvider  # noqa: PLC0415

        return OpenAIProvider(settings.openai_api_key.get_secret_value(), timeout=timeout)
    from research_api.modules.ai_gateway.mock_adapter import MockProvider  # noqa: PLC0415

    return MockProvider(settings.ai_mock_mode)


def reset_cache() -> None:
    _PROVIDERS.clear()
