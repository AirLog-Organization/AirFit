import pytest

from airfit.outfit import CATEGORIES, load_rules, recommend
from airfit.rule_engine import is_valid_condition


def _weather(**overrides) -> dict:
    weather = {
        "temp": 15.0,
        "feelsLike": 15.0,
        "tempMin": 12.0,
        "tempMax": 18.0,
        "windSpeed": 2.0,
        "precipitation": 0,
    }
    return {**weather, **overrides}


def _air(pm10: int | None = 1, pm25: int | None = 1) -> dict:
    return {"pm10": {"value": 20, "grade": pm10}, "pm25": {"value": 10, "grade": pm25}}


def _names(outfit: dict) -> list[str]:
    return [item["name"] for item in outfit["items"]]


def test_rules_file_is_valid():
    rules = load_rules()
    bands = rules["bands"]

    assert bands[-1]["min"] is None
    mins = [band["min"] for band in bands[:-1]]
    assert all(m is not None for m in mins)
    assert mins == sorted(mins, reverse=True)
    for band in bands:
        assert band["summary"]
        assert band["items"]
    for tip in rules["tips"]:
        assert tip["when"]
        assert all(is_valid_condition(condition) for condition in tip["when"])
        assert tip["text"]
    all_items = [item for band in bands for item in band["items"]] + [
        item for tip in rules["tips"] for item in tip.get("items", [])
    ]
    assert {item["category"] for item in all_items} <= CATEGORIES


@pytest.mark.parametrize(
    ("feels", "expected"),
    [
        (30, "반바지"),
        (28, "반바지"),
        (27.9, "면바지"),
        (20, "얇은 가디건"),
        (19.9, "맨투맨"),
        (12, "가벼운 재킷"),
        (9, "트렌치코트"),
        (5, "코트"),
        (4.9, "패딩"),
        (-10, "패딩"),
    ],
)
def test_band_is_chosen_by_feels_like(feels, expected):
    outfit = recommend(_weather(feelsLike=feels, tempMin=feels, tempMax=feels))

    assert expected in _names(outfit)


def test_result_has_api_shape():
    outfit = recommend(_weather())

    assert set(outfit) == {"summary", "items", "tips"}
    assert all(set(item) == {"category", "name"} for item in outfit["items"])


def test_uses_temp_when_feels_like_is_missing():
    outfit = recommend(_weather(feelsLike=None, temp=30))

    assert "반바지" in _names(outfit)


@pytest.mark.parametrize(
    "weather", [None, {}, _weather(feelsLike=None, temp=None)], ids=["none", "empty", "no-temp"]
)
def test_no_recommendation_without_temperature(weather):
    assert recommend(weather) is None


@pytest.mark.parametrize(("temp_min", "tip_shown"), [(8.0, True), (8.1, False)])
def test_daily_range_tip(temp_min, tip_shown):
    outfit = recommend(_weather(tempMin=temp_min, tempMax=18.0))

    assert any("일교차" in tip for tip in outfit["tips"]) is tip_shown


def test_daily_range_tip_skipped_without_min_max():
    outfit = recommend(_weather(tempMin=None))

    assert outfit["tips"] == []


@pytest.mark.parametrize(
    ("pops", "precipitation", "tip_shown"),
    [
        ([10, 60, 0, 0], 0, True),
        ([10, 59, 0, 0], 0, False),
        ([0, 0, 0, 0, 90], 0, False),  # 12시간 뒤의 비는 지금 옷차림에 넣지 않는다
        ([], 0.4, True),  # 지금 비가 오면 예보와 상관없이 우산
    ],
)
def test_rain_tip_adds_umbrella(pops, precipitation, tip_shown):
    hourly = [{"pop": pop} for pop in pops]
    outfit = recommend(_weather(precipitation=precipitation), hourly=hourly)

    assert ("우산" in _names(outfit)) is tip_shown
    assert any("우산" in tip for tip in outfit["tips"]) is tip_shown


@pytest.mark.parametrize(
    ("air", "tip_shown"),
    [
        (_air(pm10=2, pm25=3), True),
        (_air(pm10=4, pm25=None), True),
        (_air(pm10=2, pm25=2), False),
        (_air(pm10=None, pm25=None), False),
        (None, False),
    ],
)
def test_dust_tip_adds_mask(air, tip_shown):
    outfit = recommend(_weather(), air=air)

    assert ("보건용 마스크" in _names(outfit)) is tip_shown


@pytest.mark.parametrize(
    ("wind", "feels", "tip_shown"),
    [
        (7.0, 15.0, True),
        (6.9, 15.0, False),
        (None, 15.0, False),
        (7.0, 19.9, True),
        (7.0, 20.0, False),  # 선선한 날부터는 바람이 불어도 춥다는 팁을 붙이지 않는다
        (9.0, 30.0, False),
    ],
)
def test_wind_tip_only_when_it_feels_cool(wind, feels, tip_shown):
    outfit = recommend(_weather(windSpeed=wind, feelsLike=feels))

    assert any("바람" in tip for tip in outfit["tips"]) is tip_shown


def test_changing_result_does_not_change_rules():
    first = recommend(_weather())
    first["items"][0]["name"] = "바뀐 이름"

    assert recommend(_weather())["items"][0]["name"] != "바뀐 이름"
