import json
import logging

from research_api.platform.logging import REDACTED, JsonFormatter, redact


def test_redacts_sensitive_keys_recursively() -> None:
    data = {"api_key": "abc", "nested": {"Authorization": "Bearer x", "ok": 1}, "items": [{"token": "t"}]}
    assert redact(data) == {
        "api_key": REDACTED,
        "nested": {"Authorization": REDACTED, "ok": 1},
        "items": [{"token": REDACTED}],
    }


def test_redacts_secret_looking_values_in_free_text() -> None:
    text = "calling with sk-ant-api03-ABCDEFGHIJKL and Bearer abcdefghijklmnop"
    redacted = redact(text)
    assert "sk-ant" not in redacted
    assert "abcdefghijklmnop" not in redacted


def test_redacts_database_url_credentials() -> None:
    assert redact("postgresql://user:s3cret@db:5432/x") == f"postgresql://{REDACTED}@db:5432/x"


def test_json_formatter_redacts_extras_and_message() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "key=sk-proj-ABCDEFGHIJKL", None, None)
    record.openai_api_key = "sk-proj-ZZZZZZZZZZZZ"
    out = json.loads(JsonFormatter().format(record))
    assert "sk-proj" not in json.dumps(out)
    assert out["context"]["openai_api_key"] == REDACTED
