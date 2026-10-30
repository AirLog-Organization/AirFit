"""GET /api/conditions 응답 조립. 지역명, 날씨, 대기질은 서로 의존하지 않아 병렬로 부른다."""

import contextvars
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from airfit import airkorea, cache, kakao, life_indices, openweather, outfit
from airfit.timeutil import KST
from airfit.upstream import UpstreamError

logger = logging.getLogger(__name__)

SOURCES = ["에어코리아", "OpenWeatherMap"]

# 캐시 키의 좌표 자릿수. 소수 2자리는 약 1km, 3자리는 약 100m
# 측정값은 매시 갱신되고 15분쯤 늦게 올라온다. 측정소 목록과 행정동은 거의 바뀌지 않는다
WEATHER_TTL = 10 * 60
REALTIME_TTL = 15 * 60
STATIONS_TTL = 7 * 24 * 3600
REGION_TTL = 30 * 24 * 3600


class AllSourcesFailed(Exception):
    pass


def _region(lat: float, lon: float) -> dict | None:
    return cache.get_or_fetch(
        f"region#{lat:.3f},{lon:.3f}", REGION_TTL, lambda: kakao.region_name(lat, lon)
    )


def _realtime(station_name: str) -> dict | None:
    return cache.get_or_fetch(
        f"realtime#{station_name}", REALTIME_TTL, lambda: airkorea.realtime(station_name)
    )


def _air(lat: float, lon: float) -> dict | None:
    stations = cache.get_or_fetch(
        f"stations#{lat:.2f},{lon:.2f}",
        STATIONS_TTL,
        lambda: airkorea.nearby_stations(*kakao.to_tm(lat, lon)),
    )
    return airkorea.find_air(stations, _realtime)


def _weather(lat: float, lon: float) -> tuple[dict, list]:
    # 요약은 지금 시각 기준이라 원본 응답을 캐시하고 요약은 매번 한다
    current, forecast = cache.get_or_fetch(
        f"weather#{lat:.2f},{lon:.2f}", WEATHER_TTL, lambda: openweather.fetch(lat, lon)
    )
    return openweather.summarize(current, forecast)


def _submit(pool: ThreadPoolExecutor, fn, *args):
    # 작업 thread에서도 캐시 miss 기록이 이 요청의 목록에 쌓이도록 context를 넘긴다
    return pool.submit(contextvars.copy_context().run, fn, *args)


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
    misses = cache.track_misses()
    with ThreadPoolExecutor(max_workers=3) as pool:
        region_future = _submit(pool, _region, lat, lon)
        weather_future = _submit(pool, _weather, lat, lon)
        air_future = _submit(pool, _air, lat, lon)

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
        # 필요한 값이 없는 지수만 None. 기준은 docs/life-indices.md
        "indices": life_indices.calculate(weather, air, hourly),
        # 날씨가 없으면 None. 기준은 docs/outfit-rules.md
        "outfit": outfit.recommend(weather, air, hourly),
        "hourly": hourly,
        "warnings": warnings,
        "meta": {
            "fetchedAt": datetime.now(KST).isoformat(timespec="seconds"),
            # 외부 API를 하나도 부르지 않고 캐시만으로 만든 응답이면 True
            "cached": not misses,
            "sources": SOURCES,
        },
    }
