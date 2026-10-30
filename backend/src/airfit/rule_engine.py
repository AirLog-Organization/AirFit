"""규칙 JSON(rules/*.json)을 날씨, 대기질 값에 적용하는 공통 부분. 옷차림과 생활지수가 함께 쓴다.

조건 하나는 {"metric": 값 이름, 비교 연산자: 기준값} 모양이고, 조건 목록은 모두 맞아야 한다.
"""

import json
import operator
from functools import cache
from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"
METRICS = {
    "feelsLike",
    "humidity",
    "precipitation",
    "dailyRange",
    "rainChance",
    "dustGrade",
    "windSpeed",
}
OPERATORS = {"gte": operator.ge, "lt": operator.lt}
RAIN_SLOTS = 4  # 3시간 간격 예보 4개 = 앞으로 12시간


@cache
def load_rules(name: str) -> dict:
    return json.loads((RULES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def feels_like(weather: dict | None) -> float | None:
    """체감온도. 없으면 기온으로 대신한다."""
    weather = weather or {}
    feels = weather.get("feelsLike")
    return weather.get("temp") if feels is None else feels


def _grade(air: dict | None, key: str) -> int | None:
    return ((air or {}).get(key) or {}).get("grade")


def metrics(weather: dict | None, air: dict | None, hourly: list | None) -> dict:
    """조건(when[].metric)에 쓰는 값. 계산할 수 없으면 None이고, 그 값을 쓰는 조건은 맞지 않는다."""
    weather = weather or {}
    temp_min, temp_max = weather.get("tempMin"), weather.get("tempMax")
    daily_range = None if temp_min is None or temp_max is None else temp_max - temp_min

    pops = [slot["pop"] for slot in (hourly or [])[:RAIN_SLOTS] if slot.get("pop") is not None]
    rain_chance = 100 if weather.get("precipitation") else max(pops, default=None)

    grades = [g for g in (_grade(air, "pm10"), _grade(air, "pm25")) if g is not None]
    return {
        "feelsLike": feels_like(weather),
        "humidity": weather.get("humidity"),
        "precipitation": weather.get("precipitation"),
        "dailyRange": daily_range,
        "rainChance": rain_chance,
        "dustGrade": max(grades, default=None),
        "windSpeed": weather.get("windSpeed"),
    }


def matches(conditions: list, values: dict) -> bool:
    """조건은 모두 맞아야 한다. 조건 하나는 metric과 비교 연산자(gte, lt) 하나로 이뤄진다."""
    for condition in conditions:
        value = values[condition["metric"]]
        (op,) = condition.keys() - {"metric"}
        if value is None or not OPERATORS[op](value, condition[op]):
            return False
    return True


def is_valid_condition(condition: dict) -> bool:
    """규칙 파일 검사용. metric 이름과 연산자, 숫자 기준값이 맞는지 본다."""
    ops = condition.keys() - {"metric"}
    if condition.get("metric") not in METRICS or len(ops) != 1:
        return False
    (op,) = ops
    return op in OPERATORS and isinstance(condition[op], int | float)
