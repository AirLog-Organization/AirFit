import base64
import json
import logging

import pytest

from airfit.handler import MAX_WARDROBE_ITEMS, lambda_handler
from airfit.upstream import UpstreamError

WARDROBE = [
    {"id": "w1", "category": "outer", "name": "바람막이", "thickness": "thin", "waterproof": True},
    {
        "id": "w2",
        "category": "top",
        "name": "회색 니트",
        "thickness": "medium",
        "waterproof": False,
    },
    {
        "id": "w3",
        "category": "bottom",
        "name": "청바지",
        "thickness": "medium",
        "waterproof": False,
    },
]


def _post(body, path: str = "/api/wardrobe/recommend", base64_encoded: bool = False):
    raw = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    if base64_encoded:
        raw = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    event = {
        "rawPath": path,
        "body": raw,
        "isBase64Encoded": base64_encoded,
        "requestContext": {"http": {"method": "POST"}},
    }
    response = lambda_handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def _body(**overrides) -> dict:
    return {"lat": 37.6199, "lon": 127.063, "wardrobe": WARDROBE, **overrides}


def test_recommends_from_wardrobe_with_ids(fake_upstream):
    status, body = _post(_body())

    assert status == 200
    assert set(body) == {"summary", "items", "tips"}
    ids = {item.get("id") for item in body["items"]} - {None}
    assert ids <= {"w1", "w2", "w3"}
    assert ids  # 옷장 옷이 하나 이상 골라진다


def test_accepts_base64_body(fake_upstream):
    status, _ = _post(_body(), base64_encoded=True)

    assert status == 200


def test_empty_wardrobe_returns_general_items(fake_upstream):
    status, body = _post(_body(wardrobe=[]))

    assert status == 200
    assert all("id" not in item for item in body["items"])


@pytest.mark.parametrize("raw", ["", "not json", "[1, 2]", '"text"'])
def test_rejects_non_object_body(fake_upstream, raw):
    status, body = _post(raw)

    assert status == 400
    assert body["error"] == "invalid_params"


@pytest.mark.parametrize(
    ("lat", "lon"), [(None, 127.0), ("abc", 127.0), (51.5, -0.1), (True, 127.0)]
)
def test_rejects_bad_coordinates(fake_upstream, lat, lon):
    status, body = _post(_body(lat=lat, lon=lon))

    assert status == 400
    assert body["error"] == "invalid_params"


def test_rejects_wardrobe_that_is_not_a_list_or_too_long(fake_upstream):
    too_many = [{**WARDROBE[0], "id": f"w{i}"} for i in range(MAX_WARDROBE_ITEMS + 1)]

    assert _post(_body(wardrobe={"id": "w1"}))[0] == 400
    assert _post(_body(wardrobe=None))[0] == 400
    assert _post(_body(wardrobe=too_many))[0] == 400


@pytest.mark.parametrize(
    "item",
    [
        {**WARDROBE[0], "category": "hat"},
        {**WARDROBE[0], "thickness": "heavy"},
        {**WARDROBE[0], "waterproof": "yes"},
        {**WARDROBE[0], "name": "   "},
        {**WARDROBE[0], "name": "가" * 51},
        {**WARDROBE[0], "id": ""},
        {key: value for key, value in WARDROBE[0].items() if key != "id"},
        "바람막이",
    ],
)
def test_rejects_malformed_items(fake_upstream, item):
    status, body = _post(_body(wardrobe=[item]))

    assert status == 400
    assert body["error"] == "invalid_params"


def test_rejects_too_large_body(fake_upstream):
    status, _ = _post(json.dumps(_body()) + " " * (64 * 1024))

    assert status == 400


def test_weather_failure_returns_502(fake_upstream):
    overrides, _ = fake_upstream
    overrides["/weather"] = UpstreamError("down")

    status, body = _post(_body())

    assert status == 502
    assert body["error"] == "upstream_error"


def test_wardrobe_is_not_written_to_logs(fake_upstream, caplog):
    overrides, _ = fake_upstream
    overrides["getNearbyMsrstnList"] = UpstreamError("down")

    with caplog.at_level(logging.DEBUG):
        status, _ = _post(_body())

    assert status == 200
    assert caplog.records  # 대기질 실패 로그는 남는다
    assert "회색 니트" not in caplog.text
    assert "w2" not in caplog.text


def test_other_methods_and_paths_are_not_found(fake_upstream):
    event = {"rawPath": "/api/wardrobe/recommend", "requestContext": {"http": {"method": "GET"}}}

    assert lambda_handler(event, None)["statusCode"] == 404
    assert _post(_body(), path="/api/conditions")[0] == 404


def test_all_sources_failed_returns_502(fake_upstream):
    overrides, _ = fake_upstream
    overrides["/weather"] = UpstreamError("down")
    overrides["transcoord.json"] = UpstreamError("down")

    status, body = _post(_body())

    assert status == 502
    assert body["error"] == "upstream_error"
