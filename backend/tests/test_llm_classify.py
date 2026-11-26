import json
import logging
from types import SimpleNamespace

import pytest

from airfit import llm_classify


class FakeMessages:
    def __init__(self, text=None, stop_reason="end_turn", error=None):
        self.text, self.stop_reason, self.error = text, stop_reason, error
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        content = [SimpleNamespace(type="thinking", thinking="")]
        if self.text is not None:
            content.append(SimpleNamespace(type="text", text=self.text))
        return SimpleNamespace(stop_reason=self.stop_reason, content=content)


def _client(**kwargs):
    return SimpleNamespace(messages=FakeMessages(**kwargs))


def _json(category="outer", thickness="thick", waterproof=False) -> str:
    return json.dumps({"category": category, "thickness": thickness, "waterproof": waterproof})


def test_returns_classification_and_sends_schema():
    client = _client(text=_json())

    assert llm_classify.classify("  롱패딩 ", client=client) == {
        "category": "outer",
        "thickness": "thick",
        "waterproof": False,
    }
    call = client.messages.calls[0]
    assert call["model"] == "anthropic.claude-haiku-5-5"
    assert call["messages"] == [{"role": "user", "content": "롱패딩"}]
    assert call["output_config"]["format"]["schema"] == llm_classify.SCHEMA
    assert call["output_config"]["effort"] == "low"


def test_model_can_be_overridden(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-5-5")
    client = _client(text=_json())

    llm_classify.classify("코트", client=client)

    assert client.messages.calls[0]["model"] == "anthropic.claude-sonnet-5-5"


def test_unknown_category_becomes_none():
    client = _client(text=_json(category="unknown", thickness="medium"))

    assert llm_classify.classify("선물", client=client)["category"] is None


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        _json(category="hat"),
        _json(thickness="heavy"),
        json.dumps({"category": "top", "thickness": "thin", "waterproof": "yes"}),
        json.dumps({"category": "top", "thickness": "thin"}),
        None,
    ],
)
def test_invalid_output_returns_none(text):
    assert llm_classify.classify("셔츠", client=_client(text=text)) is None


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_unfinished_response_returns_none(stop_reason):
    client = _client(text=_json(), stop_reason=stop_reason)

    assert llm_classify.classify("셔츠", client=client) is None


def test_call_failure_returns_none_without_logging_the_name(caplog):
    client = _client(error=RuntimeError("bad request for 비밀 옷 이름"))

    with caplog.at_level(logging.DEBUG):
        assert llm_classify.classify("비밀 옷 이름", client=client) is None

    assert "RuntimeError" in caplog.text
    assert "비밀 옷 이름" not in caplog.text


def test_disabled_by_default_and_never_builds_a_client(monkeypatch):
    monkeypatch.delenv("LLM_CLASSIFY", raising=False)
    monkeypatch.setattr(llm_classify, "_client", lambda: pytest.fail("must not build a client"))

    assert llm_classify.enabled() is False
    assert llm_classify.classify("코트") is None


def test_enabled_uses_bedrock_client(monkeypatch):
    client = _client(text=_json())
    monkeypatch.setenv("LLM_CLASSIFY", "enabled")
    monkeypatch.setattr(llm_classify, "_client", lambda: client)

    assert llm_classify.classify("코트")["category"] == "outer"
    assert len(client.messages.calls) == 1


def test_schema_matches_wardrobe_values():
    properties = llm_classify.SCHEMA["properties"]

    assert set(properties["category"]["enum"]) == {
        "outer",
        "top",
        "bottom",
        "shoes",
        "accessory",
        llm_classify.UNKNOWN,
    }
    assert set(properties["thickness"]["enum"]) == {"thin", "medium", "thick"}
    assert llm_classify.SCHEMA["additionalProperties"] is False
