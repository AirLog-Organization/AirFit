import logging

import pytest

from airfit import llm_chat
from airfit.handler import MAX_CHAT_MESSAGE_LENGTH
from airfit.upstream import UpstreamError
from test_wardrobe_api import _post


def _chat(**overrides):
    body = {"lat": 37.6199, "lon": 127.063, "message": "오늘 뭐 입어?", **overrides}
    return _post(body, path="/api/chat")


def test_rule_answer_when_llm_is_off(fake_upstream):
    status, body = _chat()

    assert status == 200
    assert body["source"] == "rules"
    assert body["answer"]


def test_llm_answer_when_available(fake_upstream, monkeypatch):
    seen = {}

    def fake_answer(question, conditions):
        seen["question"], seen["conditions"] = question, conditions
        return "가벼운 재킷을 챙기세요."

    monkeypatch.setattr(llm_chat, "answer", fake_answer)

    status, body = _chat()

    assert status == 200
    assert body == {"answer": "가벼운 재킷을 챙기세요.", "source": "llm"}
    assert seen["question"] == "오늘 뭐 입어?"
    assert seen["conditions"]["weather"] is not None


def test_falls_back_to_rules_when_llm_fails(fake_upstream, monkeypatch):
    monkeypatch.setattr(llm_chat, "answer", lambda question, conditions: None)

    status, body = _chat()

    assert status == 200
    assert body["source"] == "rules"


@pytest.mark.parametrize(
    "message", [None, "", "   ", "가" * (MAX_CHAT_MESSAGE_LENGTH + 1), 123, ["질문"]]
)
def test_rejects_bad_message(fake_upstream, message):
    status, body = _chat(message=message)

    assert status == 400
    assert body["error"] == "invalid_params"


def test_rejects_bad_coordinates(fake_upstream):
    status, body = _chat(lat=51.5, lon=-0.1)

    assert status == 400
    assert body["error"] == "invalid_params"


def test_rejects_non_object_body(fake_upstream):
    status, _ = _post("[]", path="/api/chat")

    assert status == 400


def test_all_sources_failed_returns_502(fake_upstream):
    overrides, _ = fake_upstream
    overrides["/weather"] = UpstreamError("down")
    overrides["transcoord.json"] = UpstreamError("down")

    status, body = _chat()

    assert status == 502
    assert body["error"] == "upstream_error"


def test_question_is_not_written_to_logs(fake_upstream, caplog):
    overrides, _ = fake_upstream
    overrides["getNearbyMsrstnList"] = UpstreamError("down")

    with caplog.at_level(logging.DEBUG):
        status, _ = _chat(message="비밀스러운 질문")

    assert status == 200
    assert caplog.records
    assert "비밀스러운 질문" not in caplog.text
