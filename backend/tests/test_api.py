import json
from datetime import datetime

from airfit import airkorea, openweather
from airfit.handler import lambda_handler
from airfit.timeutil import KST, from_airkorea
from airfit.upstream import UpstreamError
from conftest import load_fixture


def _get(path: str, **params) -> tuple[int, dict]:
    event = {
        "rawPath": path,
        "queryStringParameters": params or None,
        "requestContext": {"http": {"method": "GET"}},
    }
    response = lambda_handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def test_regions_returns_candidates(fake_upstream):
    status, body = _get("/api/regions", q="월계동")

    assert status == 200
    assert body["regions"][0] == {
        "code": "1135010200",
        "name": "월계동",
        "fullName": "서울 노원구 월계동",
        "lat": 37.6199191869583,
        "lon": 127.062987742987,
    }
    assert len(body["regions"]) == 5


def test_regions_requires_query(fake_upstream):
    status, body = _get("/api/regions", q="  ")

    assert status == 400
    assert body["error"] == "invalid_params"


def test_regions_rejects_long_query(fake_upstream):
    _, calls = fake_upstream

    status, body = _get("/api/regions", q="가" * 101)

    assert status == 400
    assert body["error"] == "invalid_params"
    assert calls == []


def test_regions_upstream_failure(fake_upstream):
    overrides, _ = fake_upstream
    overrides["search/address.json"] = UpstreamError("down")

    status, body = _get("/api/regions", q="월계동")

    assert status == 502
    assert body["error"] == "upstream_error"


def test_conditions_combines_all_sources(fake_upstream):
    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 200
    assert body["location"]["name"] == "노원구 월계1동"
    assert body["location"]["lat"] == 37.6199
    assert body["weather"]["condition"]["code"] == 500
    assert body["air"]["station"] == {"name": "화랑로", "distanceKm": 1.1}
    assert body["air"]["pm10"] == {"value": 43, "grade": 2}
    assert body["air"]["pm25"] == {"value": 15, "grade": 1}
    assert len(body["hourly"]) == 8
    assert set(body["outfit"]) == {"summary", "items", "tips"}
    assert body["outfit"]["items"]
    assert set(body["indices"]) == {"outing", "mask", "ventilation", "laundry"}
    assert all(set(index) == {"grade", "label", "summary"} for index in body["indices"].values())
    # fixture는 비가 오는 날(code 500)이라 빨래는 밖에 널 수 없다
    assert body["indices"]["laundry"]["grade"] == 4
    assert body["indices"]["mask"]["label"] == "선택"  # PM10 보통(2)
    assert body["warnings"] == []


def test_conditions_validates_coordinates(fake_upstream):
    assert _get("/api/conditions", lat="37.6")[0] == 400
    assert _get("/api/conditions", lat="abc", lon="127")[0] == 400
    assert _get("/api/conditions", lat="51.5", lon="-0.1")[0] == 400


def test_conditions_partial_failure_keeps_weather(fake_upstream):
    overrides, _ = fake_upstream
    overrides["getNearbyMsrstnList"] = UpstreamError("down")

    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 200
    assert body["air"] is None
    assert body["weather"] is not None
    assert body["outfit"] is not None  # 대기질이 없으면 미세먼지 팁만 빠진다
    assert body["indices"]["mask"] is None
    assert body["indices"]["ventilation"] is None
    assert body["indices"]["outing"] is not None
    assert body["warnings"][0]["source"] == "air"


def test_conditions_without_weather_has_no_outfit(fake_upstream):
    overrides, _ = fake_upstream
    overrides["/weather"] = UpstreamError("down")

    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 200
    assert body["weather"] is None
    assert body["outfit"] is None
    assert body["indices"]["outing"] is None
    assert body["indices"]["laundry"] is None
    assert body["indices"]["mask"] is not None
    assert body["warnings"][0]["source"] == "weather"


def test_conditions_all_failed(fake_upstream):
    overrides, _ = fake_upstream
    overrides["/weather"] = UpstreamError("down")
    overrides["transcoord.json"] = UpstreamError("down")

    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 502
    assert body["error"] == "upstream_error"


def test_conditions_without_region_name(fake_upstream):
    overrides, _ = fake_upstream
    overrides["coord2regioncode.json"] = UpstreamError("down")

    status, body = _get("/api/conditions", lat="37.6199", lon="127.0630")

    assert status == 200
    assert body["location"]["name"] is None


def test_conditions_at_sea_uses_full_name(fake_upstream):
    overrides, _ = fake_upstream
    # 2026-10-30 (36.0, 124.0)으로 실제 호출한 응답
    sea = {
        "region_type": "H",
        "code": "90009",
        "address_name": "서해",
        "region_1depth_name": "",
        "region_2depth_name": "",
        "region_3depth_name": "",
    }
    overrides["coord2regioncode.json"] = {"documents": [{**sea, "region_type": "B"}, sea]}

    status, body = _get("/api/conditions", lat="36.0", lon="124.0")

    assert status == 200
    assert body["location"]["name"] == "서해"
    assert body["location"]["fullName"] == "서해"


def test_air_skips_station_with_missing_values(fake_upstream):
    overrides, calls = fake_upstream
    broken = load_fixture("airkorea_realtime_measure")
    broken["response"]["body"]["items"][0].update(
        pm10Value="-", pm25Value="-", pm10Flag="통신장애", pm25Flag="통신장애"
    )
    overrides["getMsrstnAcctoRltmMesureDnsty"] = broken

    assert airkorea.fetch_air(205491.3, 457510.2) is None
    assert sum("getMsrstnAcctoRltmMesureDnsty" in url for url, _ in calls) == 3


def test_flagged_pollutant_becomes_null():
    item = load_fixture("airkorea_realtime_measure")["response"]["body"]["items"][0]
    item["pm25Flag"] = "점검및교정"
    station = {"stationName": "화랑로", "tm": 1.1}

    air = airkorea.summarize(station, item)

    assert air["pm25"] == {"value": None, "grade": None}
    assert air["pm10"]["value"] == 43


def test_weather_range_covers_next_24_hours():
    current = load_fixture("openweather_current")
    forecast = load_fixture("openweather_forecast")

    weather, hourly = openweather.summarize(current, forecast)

    temps = [current["main"]["temp"], *(item["main"]["temp"] for item in forecast["list"][:8])]
    assert weather["tempMin"] == min(temps)
    assert weather["tempMax"] == max(temps)
    assert hourly[0]["time"].endswith("+09:00")
    assert 0 <= hourly[0]["pop"] <= 100


def test_weather_range_at_night_includes_tomorrow():
    # 22시 조회: 오늘 남은 예보가 없어도 내일 낮 기온까지 범위에 들어가야 한다 (#35)
    current = load_fixture("openweather_current")
    current["main"]["temp"] = 6.8
    forecast = load_fixture("openweather_forecast")
    start = int(datetime(2026, 11, 1, 22, 0, tzinfo=KST).timestamp())
    temps = [6.0, 5.1, 4.6, 5.9, 11.2, 15.98, 13.4, 9.0]
    for index, (item, temp) in enumerate(zip(forecast["list"], temps, strict=False)):
        item["dt"] = start + index * 3 * 3600
        item["main"]["temp"] = temp

    weather, hourly = openweather.summarize(current, forecast)

    assert weather["tempMin"] == 4.6
    assert weather["tempMax"] == 15.98
    assert max(hour["temp"] for hour in hourly) == weather["tempMax"]


def test_weather_precipitation_defaults_to_zero():
    current = load_fixture("openweather_current")
    current.pop("rain", None)

    weather, _ = openweather.summarize(current, load_fixture("openweather_forecast"))

    assert weather["precipitation"] == 0


def test_airkorea_midnight_is_next_day():
    assert from_airkorea("2026-10-29 24:00") == datetime(2026, 10, 30, 0, 0, tzinfo=KST)
