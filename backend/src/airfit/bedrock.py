"""Amazon Bedrock의 Claude 호출 공통 부분. 옷 분류(llm_classify)와 챗봇(llm_chat)이 함께 쓴다."""

import os
from functools import cache

DEFAULT_MODEL = "anthropic.claude-haiku-5-5"
# Lambda 제한 시간(10초) 안에 규칙으로 대신할 여유를 남긴다
TIMEOUT_SECONDS = 5.0


def model() -> str:
    """BEDROCK_MODEL_ID 환경 변수로 바꿀 수 있다."""
    return os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL)


@cache
def client():
    # 쓰지 않는 로컬과 테스트에서는 SDK를 불러오지 않는다
    from anthropic import AnthropicBedrockMantle

    # 리전은 Lambda가 넣어 주는 AWS_REGION을 쓴다
    return AnthropicBedrockMantle(timeout=TIMEOUT_SECONDS, max_retries=0)


def text_of(response) -> str | None:
    """응답에서 첫 텍스트 블록. 생각(thinking) 블록은 건너뛴다."""
    return next((block.text for block in response.content if block.type == "text"), None)
