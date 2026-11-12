from airfit.outfit import recommend, recommend_from_wardrobe


def _weather(feels: float = 15.0, **overrides) -> dict:
    weather = {
        "temp": feels,
        "feelsLike": feels,
        "tempMin": feels - 3,
        "tempMax": feels + 3,
        "windSpeed": 2.0,
        "precipitation": 0,
    }
    return {**weather, **overrides}


def _cloth(
    id: str, category: str, thickness: str, name: str | None = None, waterproof: bool = False
) -> dict:
    return {
        "id": id,
        "category": category,
        "name": name or id,
        "thickness": thickness,
        "waterproof": waterproof,
    }


def _by_category(outfit: dict) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for item in outfit["items"]:
        result.setdefault(item["category"], []).append(item)
    return result


def test_picks_matching_thickness_and_keeps_wardrobe_id():
    # 체감 15도(12~16도 구간): 겉옷 thin, medium / 상의 thin, medium / 하의 medium
    wardrobe = [
        _cloth("a1", "top", "thick", "두꺼운 니트"),
        _cloth("a2", "top", "medium", "맨투맨"),
        _cloth("a3", "bottom", "medium", "청바지"),
        _cloth("a4", "outer", "medium", "트렌치코트"),
    ]

    items = _by_category(recommend_from_wardrobe(_weather(), wardrobe=wardrobe))

    assert items["top"] == [{"id": "a2", "category": "top", "name": "맨투맨"}]
    assert items["bottom"] == [{"id": "a3", "category": "bottom", "name": "청바지"}]
    assert items["outer"] == [{"id": "a4", "category": "outer", "name": "트렌치코트"}]


def test_prefers_thickness_listed_first():
    wardrobe = [_cloth("m", "outer", "medium"), _cloth("t", "outer", "thin")]

    items = _by_category(recommend_from_wardrobe(_weather(15.0), wardrobe=wardrobe))

    assert items["outer"][0]["id"] == "t"


def test_same_thickness_uses_first_registered():
    wardrobe = [_cloth("first", "bottom", "medium"), _cloth("second", "bottom", "medium")]

    items = _by_category(recommend_from_wardrobe(_weather(), wardrobe=wardrobe))

    assert items["bottom"][0]["id"] == "first"


def test_missing_category_falls_back_to_general_item_without_id():
    wardrobe = [_cloth("hot", "top", "thick")]  # 30도에는 맞지 않는 두께

    items = _by_category(recommend_from_wardrobe(_weather(30.0), wardrobe=wardrobe))

    assert items["top"] == [{"category": "top", "name": "반팔 티셔츠"}]
    assert "outer" not in items


def test_shoes_accessories_and_tips_come_from_general_recommendation():
    weather = _weather(2.0, precipitation=0.5)
    wardrobe = [_cloth("p", "outer", "thick", "롱패딩")]

    outfit = recommend_from_wardrobe(weather, wardrobe=wardrobe)
    general = recommend(weather)

    assert outfit["summary"] == general["summary"]
    assert outfit["tips"] == general["tips"]
    names = [item["name"] for item in outfit["items"]]
    assert "롱패딩" in names
    assert "패딩" not in names
    assert {"목도리", "우산"} <= set(names)


def test_empty_wardrobe_matches_general_items():
    weather = _weather(10.0)

    outfit = recommend_from_wardrobe(weather, wardrobe=[])

    def key(item):
        return (item["category"], item["name"])

    assert sorted(outfit["items"], key=key) == sorted(recommend(weather)["items"], key=key)


def test_items_without_category_or_thickness_are_ignored():
    wardrobe = [{"id": "x", "name": "이름만 있는 옷"}, {"id": "y", "category": "top"}]

    outfit = recommend_from_wardrobe(_weather(), wardrobe=wardrobe)

    assert all("id" not in item for item in outfit["items"])


def test_rules_file_has_valid_waterproof_rule():
    from airfit.outfit import load_rules
    from airfit.rule_engine import is_valid_condition

    rule = load_rules()["waterproof"]

    assert rule["when"]
    assert all(is_valid_condition(condition) for condition in rule["when"])
    assert set(rule["categories"]) <= {"outer", "shoes"}


def test_rain_prefers_waterproof_outer_within_same_thickness():
    wardrobe = [
        _cloth("plain", "outer", "thin", "가디건"),
        _cloth("rain", "outer", "thin", "바람막이", waterproof=True),
    ]

    sunny = _by_category(recommend_from_wardrobe(_weather(), wardrobe=wardrobe))
    rainy = _by_category(
        recommend_from_wardrobe(_weather(), hourly=[{"pop": 70}], wardrobe=wardrobe)
    )

    assert sunny["outer"][0]["id"] == "plain"
    assert rainy["outer"][0]["id"] == "rain"


def test_rain_does_not_override_thickness_preference():
    # 15도에서는 thin이 먼저라, 방수인 medium보다 thin 겉옷을 고른다
    wardrobe = [
        _cloth("thin", "outer", "thin"),
        _cloth("rain", "outer", "medium", waterproof=True),
    ]

    outfit = recommend_from_wardrobe(_weather(), hourly=[{"pop": 70}], wardrobe=wardrobe)

    assert _by_category(outfit)["outer"][0]["id"] == "thin"


def test_rain_uses_waterproof_shoes_from_wardrobe():
    wardrobe = [
        _cloth("sneakers", "shoes", "thin", "운동화"),
        _cloth("boots", "shoes", "thin", "레인부츠", waterproof=True),
    ]

    rainy = recommend_from_wardrobe(_weather(25.0, precipitation=0.3), wardrobe=wardrobe)
    sunny = recommend_from_wardrobe(_weather(25.0), wardrobe=wardrobe)

    assert _by_category(rainy)["shoes"] == [
        {"id": "boots", "category": "shoes", "name": "레인부츠"}
    ]
    # 맑은 날 신발은 지금처럼 일반 추천을 쓴다
    assert _by_category(sunny)["shoes"] == [{"category": "shoes", "name": "운동화"}]


def test_no_recommendation_without_weather():
    assert recommend_from_wardrobe(None, wardrobe=[_cloth("a", "top", "thin")]) is None
