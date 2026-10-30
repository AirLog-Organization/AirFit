"""옷차림 추천. 기준값은 rules/outfit.json에 두고, 여기서는 날씨와 대기질 값에 적용만 한다.

기준과 근거는 docs/outfit-rules.md에 정리한다.
"""

import json
import operator
from functools import cache
from pathlib import Path

RULES_PATH = Path(__file__).parent / "rules" / "outfit.json"
CATEGORIES = {"outer", "top", "bottom", "shoes", "accessory"}
METRICS = {"feelsLike", "dailyRange", "rainChance", "dustGrade", "windSpeed"}
OPERATORS = {"gte": operator.ge, "lt": operator.lt}
RAIN_SLOTS = 4  # 3시간 간격 예보 4개 = 앞으로 12시간


@cache
def load_rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _grade(air: dict | None, key: str) -> int | None:
    return ((air or {}).get(key) or {}).get("grade")


def _metrics(feels: float, weather: dict, air: dict | None, hourly: list | None) -> dict:
    """팁 조건(when[].metric)에 쓰는 값. 계산할 수 없으면 None이고, 그 팁은 건너뛴다."""
    temp_min, temp_max = weather.get("tempMin"), weather.get("tempMax")
    daily_range = None if temp_min is None or temp_max is None else temp_max - temp_min

    pops = [slot["pop"] for slot in (hourly or [])[:RAIN_SLOTS] if slot.get("pop") is not None]
    rain_chance = 100 if weather.get("precipitation") else max(pops, default=None)

    grades = [g for g in (_grade(air, "pm10"), _grade(air, "pm25")) if g is not None]
    return {
        "feelsLike": feels,
        "dailyRange": daily_range,
        "rainChance": rain_chance,
        "dustGrade": max(grades, default=None),
        "windSpeed": weather.get("windSpeed"),
    }


def _matches(conditions: list, metrics: dict) -> bool:
    """조건은 모두 맞아야 한다. 조건 하나는 metric과 비교 연산자(gte, lt) 하나로 이뤄진다."""
    for condition in conditions:
        value = metrics[condition["metric"]]
        (op,) = condition.keys() - {"metric"}
        if value is None or not OPERATORS[op](value, condition[op]):
            return False
    return True


def recommend(weather: dict | None, air: dict | None = None, hourly: list | None = None):
    """체감온도 구간으로 기본 옷차림을 고르고, 조건에 맞는 팁과 소품을 덧붙인다.

    날씨가 없으면 추천하지 않는다(None). 대기질이나 예보가 없으면 그 조건의 팁만 빠진다.
    """
    if not weather:
        return None
    feels = weather.get("feelsLike")
    if feels is None:
        feels = weather.get("temp")
    if feels is None:
        return None

    rules = load_rules()
    # 구간은 높은 온도부터 적혀 있고, 마지막 구간(min: null)이 나머지를 모두 받는다
    band = next(b for b in rules["bands"] if b["min"] is None or feels >= b["min"])
    items = [dict(item) for item in band["items"]]
    tips = []

    metrics = _metrics(feels, weather, air, hourly)
    for tip in rules["tips"]:
        if _matches(tip["when"], metrics):
            tips.append(tip["text"])
            items.extend(dict(item) for item in tip.get("items", []))

    return {"summary": band["summary"], "items": items, "tips": tips}
