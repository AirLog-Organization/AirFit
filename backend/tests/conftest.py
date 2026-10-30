import json
from pathlib import Path

import pytest

from airfit import upstream

FIXTURES = Path(__file__).parent / "fixtures"

# 외부 API 경로 끝부분 → 2026-10-29 "월계동"으로 실제 호출해 저장한 응답
ROUTES = {
    "search/address.json": "kakao_search_address",
    "coord2regioncode.json": "kakao_coord2regioncode",
    "transcoord.json": "kakao_transcoord",
    "/weather": "openweather_current",
    "/forecast": "openweather_forecast",
    "getNearbyMsrstnList": "airkorea_nearby_station",
    "getMsrstnAcctoRltmMesureDnsty": "airkorea_realtime_measure",
}


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def api_keys(monkeypatch):
    for key in ("KAKAO_REST_API_KEY", "OPENWEATHER_API_KEY", "AIRKOREA_SERVICE_KEY"):
        monkeypatch.setenv(key, "test-key")


@pytest.fixture
def fake_upstream(monkeypatch):
    """외부 API 호출을 fixtures 응답으로 바꾼다. overrides로 경로별 응답이나 예외를 바꾼다."""
    overrides: dict = {}
    calls: list = []

    def get_json(url, params, headers=None):
        calls.append((url, params))
        for suffix, name in ROUTES.items():
            if url.endswith(suffix):
                result = overrides.get(suffix, load_fixture(name))
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(upstream, "get_json", get_json)
    return overrides, calls
