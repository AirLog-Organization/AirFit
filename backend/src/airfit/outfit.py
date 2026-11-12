"""옷차림 추천. 기준값은 rules/outfit.json에 두고, 여기서는 날씨와 대기질 값에 적용만 한다.

기준과 근거는 docs/outfit-rules.md에 정리한다.
"""

from airfit import rule_engine

CATEGORIES = {"outer", "top", "bottom", "shoes", "accessory"}
# 옷장 항목의 두께. 구간별 wear에 이 값으로 맞는 두께를 적는다
THICKNESSES = {"thin", "medium", "thick"}


def load_rules() -> dict:
    return rule_engine.load_rules("outfit")


def _band(feels: float) -> dict:
    # 구간은 높은 온도부터 적혀 있고, 마지막 구간(min: null)이 나머지를 모두 받는다
    return next(b for b in load_rules()["bands"] if b["min"] is None or feels >= b["min"])


def recommend(weather: dict | None, air: dict | None = None, hourly: list | None = None):
    """체감온도 구간으로 기본 옷차림을 고르고, 조건에 맞는 팁과 소품을 덧붙인다.

    날씨가 없으면 추천하지 않는다(None). 대기질이나 예보가 없으면 그 조건의 팁만 빠진다.
    """
    feels = rule_engine.feels_like(weather)
    if feels is None:
        return None

    rules = load_rules()
    band = _band(feels)
    items = [dict(item) for item in band["items"]]
    tips = []

    values = rule_engine.metrics(weather, air, hourly)
    for tip in rules["tips"]:
        if rule_engine.matches(tip["when"], values):
            tips.append(tip["text"])
            items.extend(dict(item) for item in tip.get("items", []))

    return {"summary": band["summary"], "items": items, "tips": tips}


def _pick(wardrobe: list, category: str, thicknesses: list[str]) -> dict | None:
    """두께 선호 순서대로 처음 맞는 옷. 같은 두께면 옷장에 먼저 등록한 옷을 고른다."""
    for thickness in thicknesses:
        for item in wardrobe:
            if item.get("category") == category and item.get("thickness") == thickness:
                return item
    return None


def recommend_from_wardrobe(
    weather: dict | None,
    air: dict | None = None,
    hourly: list | None = None,
    wardrobe: list | None = None,
):
    """옷장(브라우저에만 저장된 옷 목록)에서 구간의 wear에 맞는 겉옷, 상의, 하의를 고른다.

    고른 옷에는 옷장 항목의 id를 붙인다. 맞는 옷이 없는 종류는 일반 추천의 옷을 id 없이 넣고,
    신발, 소품, 팁은 일반 추천을 그대로 쓴다. 날씨가 없으면 None.
    """
    base = recommend(weather, air, hourly)
    if base is None:
        return None

    band = _band(rule_engine.feels_like(weather))
    wardrobe = wardrobe or []
    items = []
    for category, thicknesses in band["wear"].items():
        picked = _pick(wardrobe, category, thicknesses)
        if picked is not None:
            items.append({"id": picked["id"], "category": category, "name": picked["name"]})
        else:
            items.extend(dict(item) for item in band["items"] if item["category"] == category)
    items.extend(item for item in base["items"] if item["category"] not in band["wear"])

    return {"summary": base["summary"], "items": items, "tips": base["tips"]}
