"""외부 API 응답의 DynamoDB 캐시. CACHE_TABLE이 없으면(로컬, 테스트) 매번 원본을 부른다.

캐시가 실패해도 응답은 원본으로 이어가야 하므로 DynamoDB 오류는 로그만 남긴다.
"""

import json
import logging
import os
import time
from collections.abc import Callable
from contextvars import ContextVar
from functools import cache as _once

logger = logging.getLogger(__name__)

# 요청 하나에서 캐시를 못 쓰고 원본을 부른 키. meta.cached 계산용
_misses: ContextVar[list[str] | None] = ContextVar("cache_misses", default=None)


@_once
def _table():
    import boto3  # Lambda 런타임에 기본으로 있다. 캐시를 안 쓰는 로컬에서는 불러오지 않는다

    return boto3.resource("dynamodb").Table(os.environ["CACHE_TABLE"])


def track_misses() -> list[str]:
    """지금 context에서 원본을 부른 키를 모을 목록을 만든다."""
    misses: list[str] = []
    _misses.set(misses)
    return misses


def _get(key: str):
    item = _table().get_item(Key={"pk": key}).get("Item")
    if item is None or item["expiresAt"] <= time.time():
        return None
    return item


def get_or_fetch(key: str, ttl_seconds: int, fetch: Callable):
    """캐시에 있으면 그 값을, 없으면 fetch() 결과를 저장하고 돌려준다.

    fetch의 예외는 그대로 올리고 저장하지 않는다.
    """
    if os.environ.get("CACHE_TABLE"):
        try:
            item = _get(key)
            if item is not None:
                return json.loads(item["value"])
        except Exception:
            logger.warning("캐시 읽기 실패: %s", key, exc_info=True)

    misses = _misses.get()
    if misses is not None:
        misses.append(key)
    value = fetch()

    if os.environ.get("CACHE_TABLE"):
        try:
            # DynamoDB는 float를 받지 않아 JSON 문자열로 넣는다
            _table().put_item(
                Item={
                    "pk": key,
                    "value": json.dumps(value, ensure_ascii=False),
                    "expiresAt": int(time.time()) + ttl_seconds,
                }
            )
        except Exception:
            logger.warning("캐시 쓰기 실패: %s", key, exc_info=True)
    return value
