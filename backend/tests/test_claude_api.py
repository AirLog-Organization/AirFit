from types import SimpleNamespace

from airfit import claude_api


def test_client_uses_anthropic_api_without_retries(monkeypatch):
    # 만들기만 하고 호출하지 않으므로 키는 가짜여도 된다
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    claude_api.client.cache_clear()
    try:
        client = claude_api.client()
        assert "api.anthropic.com" in str(client.base_url)
        assert client.max_retries == 0
    finally:
        claude_api.client.cache_clear()


def test_configured_only_with_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert claude_api.configured() is False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    assert claude_api.configured() is False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert claude_api.configured() is True


def test_model_defaults_to_haiku(monkeypatch):
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    assert claude_api.model() == "claude-haiku-5-5"

    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    assert claude_api.model() == "claude-sonnet-5-5"


def test_text_of_skips_thinking_blocks():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text="답"),
        ]
    )

    assert claude_api.text_of(response) == "답"
    assert claude_api.text_of(SimpleNamespace(content=[])) is None


def test_sdk_is_imported_when_the_module_loads():
    # 요청 중에 SDK를 불러오면 Lambda 제한 시간을 넘기므로, 모듈을 불러올 때 이미 들어 있어야 한다
    assert claude_api.Anthropic.__module__.startswith("anthropic")
