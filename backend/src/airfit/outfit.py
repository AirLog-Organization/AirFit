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


def _pick(
    wardrobe: list, category: str, thicknesses: list[str], waterproof_first: bool = False
) -> dict | None:
    """두께 선호 순서대로 처음 맞는 옷. 같은 두께면 옷장에 먼저 등록한 옷을 고른다.

    waterproof_first면 같은 두께 안에서 방수 옷을 먼저 고른다.
    """
    for thickness in thicknesses:
        matches = [
            item
            for item in wardrobe
            if item.get("category") == category and item.get("thickness") == thickness
        ]
        if waterproof_first:
            # sorted는 순서가 안정적이라 방수 옷끼리, 아닌 옷끼리는 등록 순서가 유지된다
            matches = sorted(matches, key=lambda item: not item.get("waterproof"))
        if matches:
            return matches[0]
    return None


def _wardrobe_item(item: dict, category: str) -> dict:
    return {"id": item["id"], "category": category, "name": item["name"]}


def recommend_from_wardrobe(
    weather: dict | None,
    air: dict | None = None,
    hourly: list | None = None,
    wardrobe: list | None = None,
):
    """옷장(브라우저에만 저장된 옷 목록)에서 구간의 wear에 맞는 겉옷, 상의, 하의를 고른다.

    고른 옷에는 옷장 항목의 id를 붙인다. 맞는 옷이 없는 종류는 일반 추천의 옷을 id 없이 넣고,
    신발, 소품, 팁은 일반 추천을 그대로 쓴다. 비 소식이 있으면(규칙의 waterproof.when)
    방수 겉옷을 먼저 고르고, 옷장에 방수 신발이 있으면 일반 추천 신발 대신 넣는다.
    날씨가 없으면 None.
    """
    base = recommend(weather, air, hourly)
    if base is None:
        return None

    rules = load_rules()
    band = _band(rule_engine.feels_like(weather))
    wardrobe = wardrobe or []
    values = rule_engine.metrics(weather, air, hourly)
    rainy = rule_engine.matches(rules["waterproof"]["when"], values)
    waterproof_categories = set(rules["waterproof"]["categories"]) if rainy else set()

    items = []
    for category, thicknesses in band["wear"].items():
        picked = _pick(wardrobe, category, thicknesses, category in waterproof_categories)
        if picked is not None:
            items.append(_wardrobe_item(picked, category))
        else:
            items.extend(dict(item) for item in band["items"] if item["category"] == category)
    rest = [item for item in base["items"] if item["category"] not in band["wear"]]

    # 신발은 두께로 고르지 않으므로, 비 올 때 방수 신발만 옷장에서 고른다
    shoes = next(
        (item for item in wardrobe if item.get("category") == "shoes" and item.get("waterproof")),
        None,
    )
    if "shoes" in waterproof_categories and shoes is not None:
        rest = [item for item in rest if item["category"] != "shoes"]
        rest.insert(0, _wardrobe_item(shoes, "shoes"))

    return {"summary": base["summary"], "items": items + rest, "tips": base["tips"]}
