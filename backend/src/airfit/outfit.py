"""옷차림 추천. 기준값은 rules/outfit.json에 두고, 여기서는 날씨와 대기질 값에 적용만 한다.

기준과 근거는 docs/outfit-rules.md에 정리한다.
"""

from airfit import rule_engine

CATEGORIES = {"outer", "top", "bottom", "shoes", "accessory"}


def load_rules() -> dict:
    return rule_engine.load_rules("outfit")


def recommend(weather: dict | None, air: dict | None = None, hourly: list | None = None):
    """체감온도 구간으로 기본 옷차림을 고르고, 조건에 맞는 팁과 소품을 덧붙인다.

    날씨가 없으면 추천하지 않는다(None). 대기질이나 예보가 없으면 그 조건의 팁만 빠진다.
    """
    feels = rule_engine.feels_like(weather)
    if feels is None:
        return None

    rules = load_rules()
    # 구간은 높은 온도부터 적혀 있고, 마지막 구간(min: null)이 나머지를 모두 받는다
    band = next(b for b in rules["bands"] if b["min"] is None or feels >= b["min"])
    items = [dict(item) for item in band["items"]]
    tips = []

    values = rule_engine.metrics(weather, air, hourly)
    for tip in rules["tips"]:
        if rule_engine.matches(tip["when"], values):
            tips.append(tip["text"])
            items.extend(dict(item) for item in tip.get("items", []))

    return {"summary": band["summary"], "items": items, "tips": tips}
