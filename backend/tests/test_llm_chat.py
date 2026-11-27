import logging

import pytest

from airfit import claude_api, llm_chat
from test_chat import _conditions
from test_llm_classify import _client


def test_answers_with_todays_context():
    client = _client(text="  얇은 니트에 가벼운 재킷을 걸치세요.  ")
    conditions = _conditions()

    answer = llm_chat.answer(" 오늘 뭐 입어? ", conditions, client=client)

    assert answer == "얇은 니트에 가벼운 재킷을 걸치세요."
    call = client.messages.calls[0]
    assert call["model"] == claude_api.DEFAULT_MODEL
    assert call["messages"] == [{"role": "user", "content": "오늘 뭐 입어?"}]
    assert call["system"].startswith(llm_chat.SYSTEM)
    assert "지역: 서울특별시 노원구 월계1동" in call["system"]
    assert call["output_config"] == {"effort": "low"}


@pytest.mark.parametrize("text", [None, "   ", "가" * (llm_chat.MAX_ANSWER_CHARS + 1)])
def test_empty_or_too_long_answer_returns_none(text):
    assert llm_chat.answer("오늘 뭐 입어?", _conditions(), client=_client(text=text)) is None


def test_answer_at_length_limit_is_kept():
    text = "가" * llm_chat.MAX_ANSWER_CHARS

    assert llm_chat.answer("질문", _conditions(), client=_client(text=text)) == text


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_unfinished_response_returns_none(stop_reason):
    client = _client(text="답", stop_reason=stop_reason)

    assert llm_chat.answer("질문", _conditions(), client=client) is None


def test_call_failure_returns_none_without_logging_the_question(caplog):
    client = _client(error=RuntimeError("bad request: 비밀 질문"))

    with caplog.at_level(logging.DEBUG):
        assert llm_chat.answer("비밀 질문", _conditions(), client=client) is None

    assert "RuntimeError" in caplog.text
    assert "비밀 질문" not in caplog.text


def test_disabled_by_default_and_never_builds_a_client(monkeypatch):
    monkeypatch.delenv("LLM_CHAT", raising=False)
    monkeypatch.setattr(claude_api, "client", lambda: pytest.fail("must not build a client"))

    assert llm_chat.enabled() is False
    assert llm_chat.answer("질문", _conditions()) is None


def test_enabled_uses_claude_client(monkeypatch):
    client = _client(text="우산을 챙기세요.")
    monkeypatch.setenv("LLM_CHAT", "enabled")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(claude_api, "client", lambda: client)

    assert llm_chat.answer("비 와?", _conditions()) == "우산을 챙기세요."


def test_enabled_without_api_key_stays_off(monkeypatch):
    monkeypatch.setenv("LLM_CHAT", "enabled")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(claude_api, "client", lambda: pytest.fail("must not build a client"))

    assert llm_chat.enabled() is False
    assert llm_chat.answer("질문", _conditions()) is None
