"""에어코리아 근접 측정소와 실시간 측정값. 서비스키는 공공데이터포털의 Decoding 값을 쓴다."""

import os

from airfit import upstream
from airfit.timeutil import from_airkorea
from airfit.upstream import UpstreamError

BASE_URL = "https://apis.data.go.kr/B552584"


def _params(**extra) -> dict:
    return {"serviceKey": os.environ["AIRKOREA_SERVICE_KEY"], "returnType": "json", **extra}


def _items(data: dict) -> list[dict]:
    # 오류도 HTTP 200에 items: null로 오므로, 빈 결과로 캐시되지 않게 resultCode로 실패를 가른다
    code = data["response"]["header"]["resultCode"]
    if code == "03":  # NODATA_ERROR
        return []
    if code != "00":
        raise UpstreamError(f"에어코리아 resultCode {code}")
    return data["response"]["body"]["items"] or []


def nearby_stations(tm_x: float, tm_y: float) -> list[dict]:
    """가까운 순으로 정렬된 측정소 목록."""
    data = upstream.get_json(
        f"{BASE_URL}/MsrstnInfoInqireSvc/getNearbyMsrstnList",
        _params(tmX=tm_x, tmY=tm_y, ver="1.1"),
    )
    return _items(data)


def realtime(station_name: str) -> dict | None:
    data = upstream.get_json(
        f"{BASE_URL}/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty",
        _params(stationName=station_name, dataTerm="DAILY", numOfRows=1, pageNo=1, ver="1.3"),
    )
    items = _items(data)
    return items[0] if items else None


def _number(value: str | None, cast=int):
    # 점검이나 통신장애면 "-" 또는 빈 값이 온다
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def _pollutant(item: dict, value_key: str, grade_key: str, flag_key: str | None, cast=int):
    if flag_key and item.get(flag_key):
        return {"value": None, "grade": None}
    return {"value": _number(item.get(value_key), cast), "grade": _number(item.get(grade_key))}


def summarize(station: dict, item: dict) -> dict:
    """측정소와 측정값을 API 응답의 air 모양으로 줄인다. 등급은 1시간 기준을 쓴다."""
    return {
        "measuredAt": from_airkorea(item["dataTime"]).isoformat(),
        "station": {"name": station["stationName"], "distanceKm": station["tm"]},
        "pm10": _pollutant(item, "pm10Value", "pm10Grade1h", "pm10Flag"),
        "pm25": _pollutant(item, "pm25Value", "pm25Grade1h", "pm25Flag"),
        "o3": _pollutant(item, "o3Value", "o3Grade", "o3Flag", float),
        "khai": _pollutant(item, "khaiValue", "khaiGrade", None),
    }


def fetch_air(tm_x: float, tm_y: float) -> dict | None:
    return find_air(nearby_stations(tm_x, tm_y))


def find_air(stations: list[dict], get_realtime=realtime) -> dict | None:
    """가까운 측정소부터 미세먼지 값이 있는 곳을 찾는다. 모두 비어 있으면 None."""
    for station in stations:
        item = get_realtime(station["stationName"])
        if item is None:
            continue
        air = summarize(station, item)
        if air["pm10"]["value"] is not None or air["pm25"]["value"] is not None:
            return air
    return None
