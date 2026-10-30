"""GET /api/conditions 응답 조립. 지역명, 날씨, 대기질은 서로 의존하지 않아 병렬로 부른다."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from airfit import airkorea, kakao, openweather
from airfit.timeutil import KST
from airfit.upstream import UpstreamError

logger = logging.getLogger(__name__)

SOURCES = ["에어코리아", "OpenWeatherMap"]
INDEX_KEYS = ["outing", "mask", "ventilation", "laundry"]


class AllSourcesFailed(Exception):
    pass


def _air(lat: float, lon: float) -> dict | None:
    return airkorea.fetch_air(*kakao.to_tm(lat, lon))


def _weather(lat: float, lon: float) -> tuple[dict, list]:
    return openweather.summarize(*openweather.fetch(lat, lon))


def _result(future, source: str, warnings: list | None, message: str):
    try:
        return future.result()
    except (UpstreamError, KeyError, IndexError, TypeError, ValueError):
        logger.exception("%s 조회 실패", source)
        if warnings is not None:
            warnings.append({"source": source, "message": message})
        return None


def get_conditions(lat: float, lon: float) -> dict:
    warnings: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        region_future = pool.submit(kakao.region_name, lat, lon)
        weather_future = pool.submit(_weather, lat, lon)
        air_future = pool.submit(_air, lat, lon)

        region = _result(region_future, "region", None, "")
        weather_result = _result(
            weather_future, "weather", warnings, "날씨 정보를 잠시 불러오지 못했어요."
        )
        air = _result(air_future, "air", warnings, "대기질 정보를 잠시 불러오지 못했어요.")

    if air is None and not any(w["source"] == "air" for w in warnings):
        warnings.append({"source": "air", "message": "근처 측정소에 대기질 정보가 없어요."})
    if weather_result is None and air is None:
        raise AllSourcesFailed

    weather, hourly = weather_result or (None, None)
    region = region or {"name": None, "fullName": None, "regionCode": None}
    return {
        "location": {**region, "lat": lat, "lon": lon},
        "weather": weather,
        "air": air,
        # 산출 기준(docs/life-indices.md)이 정해지면 채운다
        "indices": dict.fromkeys(INDEX_KEYS),
        "outfit": None,
        "hourly": hourly,
        "warnings": warnings,
        "meta": {
            "fetchedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "cached": False,
            "sources": SOURCES,
        },
    }
