"""외부 API 호출 공통 처리. Lambda 의존성을 늘리지 않으려고 표준 라이브러리만 쓴다."""

import json
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SECONDS = 3


class UpstreamError(Exception):
    """외부 API 호출 실패. 메시지에 키가 섞이지 않도록 URL은 담지 않는다."""


def get_json(url: str, params: dict, headers: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}", headers=headers or {}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise UpstreamError(f"{urllib.parse.urlsplit(url).netloc} HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise UpstreamError(f"{urllib.parse.urlsplit(url).netloc} {type(e).__name__}") from None
