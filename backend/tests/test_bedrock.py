from types import SimpleNamespace

from airfit import bedrock


def test_client_uses_lambda_region(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "ap-northeast-2")
    # 만들기만 하고 호출하지 않으므로 자격 증명은 가짜여도 된다
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    bedrock.client.cache_clear()
    try:
        client = bedrock.client()
        assert "bedrock-mantle.ap-northeast-2" in str(client.base_url)
        assert client.max_retries == 0
    finally:
        bedrock.client.cache_clear()


def test_model_defaults_to_haiku(monkeypatch):
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)

    assert bedrock.model() == "anthropic.claude-haiku-5-5"


def test_text_of_skips_thinking_blocks():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text="답"),
        ]
    )

    assert bedrock.text_of(response) == "답"
    assert bedrock.text_of(SimpleNamespace(content=[])) is None
