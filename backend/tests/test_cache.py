import json
import time

import pytest

from airfit import cache
from airfit.upstream import UpstreamError
from test_api import _get


class FakeTable:
    """DynamoDB Table의 get_item, put_item만 흉내 낸다."""

    def __init__(self):
        self.items: dict[str, dict] = {}
        self.fail = False

    def get_item(self, Key):
        if self.fail:
            raise RuntimeError("dynamodb down")
        item = self.items.get(Key["pk"])
        return {"Item": item} if item else {}

    def put_item(self, Item):
        if self.fail:
            raise RuntimeError("dynamodb down")
        self.items[Item["pk"]] = Item


@pytest.fixture
def table(monkeypatch):
    fake = FakeTable()
    monkeypatch.setenv("CACHE_TABLE", "test-cache")
    monkeypatch.setattr(cache, "_table", lambda: fake)
    return fake


def test_conditions_second_call_uses_cache(fake_upstream, table):
    _, calls = fake_upstream

    _, first = _get("/api/conditions", lat="37.6199", lon="127.0630")
    upstream_calls = len(calls)
    _, second = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert first["meta"]["cached"] is False
    assert second["meta"]["cached"] is True
    assert len(calls) == upstream_calls
    assert second["air"] == first["air"]
    assert second["weather"] == first["weather"]
    assert second["location"] == first["location"]


def test_conditions_nearby_coordinates_share_weather_and_stations(fake_upstream, table):
    _, calls = fake_upstream
    _get("/api/conditions", lat="37.6199", lon="127.0630")
    calls.clear()

    # 소수 2자리가 같으면 날씨와 측정소는 캐시, 행정동(3자리)만 새로 부른다
    _, body = _get("/api/conditions", lat="37.6211", lon="127.0612")

    assert [url.rsplit("/", 1)[-1] for url, _ in calls] == ["coord2regioncode.json"]
    assert body["meta"]["cached"] is False


def test_expired_entry_is_fetched_again(fake_upstream, table):
    _, calls = fake_upstream
    _get("/api/regions", q="월계동")
    for item in table.items.values():
        item["expiresAt"] = int(time.time()) - 1

    _get("/api/regions", q="월계동")

    assert sum(url.endswith("search/address.json") for url, _ in calls) == 2


def test_regions_cached_by_query(fake_upstream, table):
    _, calls = fake_upstream

    _, first = _get("/api/regions", q="월계동")
    _, second = _get("/api/regions", q="월계동")

    assert second == first
    assert sum(url.endswith("search/address.json") for url, _ in calls) == 1
    assert json.loads(table.items["regions#월계동"]["value"]) == first["regions"]


def test_cache_failure_falls_back_to_upstream(fake_upstream, table):
    table.fail = True

    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 200
    assert body["air"] is not None
    assert body["meta"]["cached"] is False


def test_upstream_failure_is_not_cached(fake_upstream, table):
    overrides, _ = fake_upstream
    overrides["/forecast"] = UpstreamError("down")

    _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert not any(key.startswith("weather#") for key in table.items)


def test_airkorea_error_code_is_not_cached(fake_upstream, table):
    overrides, _ = fake_upstream
    overrides["getNearbyMsrstnList"] = {
        "response": {
            "header": {"resultCode": "22", "resultMsg": "LIMITED_NUMBER_OF_SERVICE_REQUESTS"},
            "body": {"items": None},
        }
    }

    _, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert body["air"] is None
    assert not any(key.startswith("stations#") for key in table.items)


def test_without_table_env_cache_is_skipped(fake_upstream, monkeypatch):
    monkeypatch.delenv("CACHE_TABLE", raising=False)
    monkeypatch.setattr(cache, "_table", lambda: pytest.fail("table must not be used"))

    _, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert body["meta"]["cached"] is False
