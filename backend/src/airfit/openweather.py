"""OpenWeather 현재 날씨와 5일 예보. 날씨 설명은 영어로 받고 프론트가 condition code로 매칭한다."""

import os
from datetime import datetime

from airfit import upstream
from airfit.timeutil import KST, from_unix

BASE_URL = "https://api.openweathermap.org/data/2.5"
HOURLY_COUNT = 8  # 3시간 간격 8개 = 앞으로 24시간


def _params(lat: float, lon: float) -> dict:
    return {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "en",
        "appid": os.environ["OPENWEATHER_API_KEY"],
    }


def fetch(lat: float, lon: float) -> tuple[dict, dict]:
    current = upstream.get_json(f"{BASE_URL}/weather", _params(lat, lon))
    forecast = upstream.get_json(f"{BASE_URL}/forecast", _params(lat, lon))
    return current, forecast


def _precipitation(item: dict, period: str) -> float:
    rain = item.get("rain", {}).get(period, 0)
    snow = item.get("snow", {}).get(period, 0)
    return round(rain + snow, 2)


def summarize(current: dict, forecast: dict, now: datetime | None = None) -> tuple[dict, list]:
    """현재 날씨와 예보를 API 응답의 weather, hourly 모양으로 줄인다."""
    today = (now or datetime.now(KST)).astimezone(KST).date()
    temp = current["main"]["temp"]

    # 예보는 지금 이후 구간만 오므로 "지금부터 오늘 밤까지"의 최저, 최고가 된다
    today_temps = [temp] + [
        item["main"]["temp"] for item in forecast["list"] if from_unix(item["dt"]).date() == today
    ]
    condition = current["weather"][0]

    weather = {
        "observedAt": from_unix(current["dt"]).isoformat(),
        "temp": temp,
        "feelsLike": current["main"]["feels_like"],
        "tempMin": min(today_temps),
        "tempMax": max(today_temps),
        "humidity": current["main"]["humidity"],
        "windSpeed": current["wind"]["speed"],
        "clouds": current["clouds"]["all"],
        "precipitation": _precipitation(current, "1h"),
        "isDay": condition["icon"].endswith("d"),
        "condition": {
            "code": condition["id"],
            "main": condition["main"],
            "description": condition["description"],
        },
    }
    hourly = [
        {
            "time": from_unix(item["dt"]).isoformat(),
            "temp": item["main"]["temp"],
            "feelsLike": item["main"]["feels_like"],
            "pop": round(item["pop"] * 100),
            "precipitation": _precipitation(item, "3h"),
            "conditionCode": item["weather"][0]["id"],
            "isDay": item["sys"]["pod"] == "d",
        }
        for item in forecast["list"][:HOURLY_COUNT]
    ]
    return weather, hourly
