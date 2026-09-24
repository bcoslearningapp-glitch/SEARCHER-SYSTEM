from pydantic import SecretStr

from research_api.config import Settings


def test_provider_keys_are_optional() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.anthropic_api_key is None
    assert settings.openai_api_key is None


def test_secrets_never_render_in_repr() -> None:
    settings = Settings(_env_file=None, anthropic_api_key=SecretStr("sk-ant-secret-value"))  # type: ignore[call-arg]
    assert "sk-ant-secret-value" not in repr(settings)
    assert "sk-ant-secret-value" not in str(settings.model_dump())
