import pytest

from airfit.life_indices import KEYS, calculate, load_rules
from airfit.rule_engine import METRICS, is_valid_condition


def _weather(**overrides) -> dict:
    weather = {
        "temp": 18.0,
        "feelsLike": 18.0,
        "tempMin": 14.0,
        "tempMax": 21.0,
        "humidity": 45,
        "windSpeed": 2.0,
        "precipitation": 0,
    }
    return {**weather, **overrides}


def _air(pm10: int | None = 1, pm25: int | None = 1) -> dict:
    return {"pm10": {"value": 20, "grade": pm10}, "pm25": {"value": 10, "grade": pm25}}


def _grades(weather=None, air=None, hourly=None) -> dict:
    result = calculate(weather or _weather(), air or _air(), hourly)
    return {key: index and index["grade"] for key, index in result.items()}


def test_rules_file_is_valid():
    rules = load_rules()

    assert set(rules) == set(KEYS)
    for rule in rules.values():
        assert len(rule["labels"]) == 4
        assert rule["default"]
        assert set(rule["requires"]) <= METRICS
        grades = [candidate["grade"] for candidate in rule["rules"]]
        assert all(2 <= grade <= 4 for grade in grades)
        # 나쁜 등급부터 적어야 처음 맞는 규칙이 가장 나쁜 등급이 된다
        assert grades == sorted(grades, reverse=True)
        for candidate in rule["rules"]:
            assert candidate["when"]
            assert all(is_valid_condition(condition) for condition in candidate["when"])
            assert candidate["summary"]


def test_clear_day_is_good_everywhere():
    result = calculate(_weather(), _air(), [{"pop": 0}])

    assert result == {
        "outing": {"grade": 1, "label": "좋음", "summary": "산책하기 좋은 날이에요."},
        "mask": {"grade": 1, "label": "불필요", "summary": "마스크 없이 다녀도 괜찮아요."},
        "ventilation": {"grade": 1, "label": "좋음", "summary": "10분 이상 창문을 열어 두세요."},
        "laundry": {"grade": 1, "label": "좋음", "summary": "햇볕과 바람에 잘 말라요."},
    }


@pytest.mark.parametrize(
    ("pm10", "pm25", "expected"),
    [
        (1, 1, {"outing": 1, "mask": 1, "ventilation": 1, "laundry": 1}),
        (2, 1, {"outing": 1, "mask": 2, "ventilation": 2, "laundry": 1}),
        (2, 3, {"outing": 3, "mask": 3, "ventilation": 3, "laundry": 3}),
        (4, None, {"outing": 4, "mask": 4, "ventilation": 4, "laundry": 3}),
    ],
)
def test_dust_grade_uses_worse_of_pm10_and_pm25(pm10, pm25, expected):
    assert _grades(air=_air(pm10, pm25)) == expected


def test_label_follows_grade():
    result = calculate(_weather(), _air(3, 3), None)

    assert result["mask"]["label"] == "권장"
    assert result["ventilation"]["label"] == "짧게"
    assert result["laundry"]["label"] == "실내 건조"


@pytest.mark.parametrize(("feels", "grade"), [(33.0, 3), (32.9, 1), (-10.0, 1), (-10.1, 3)])
def test_outing_heat_and_cold(feels, grade):
    assert _grades(weather=_weather(feelsLike=feels))["outing"] == grade


def test_rain_lowers_outing_laundry_and_ventilation():
    raining = _grades(weather=_weather(precipitation=0.5))
    forecast = _grades(hourly=[{"pop": 70}])

    assert raining == {"outing": 2, "mask": 1, "ventilation": 2, "laundry": 4}
    assert forecast == {"outing": 2, "mask": 1, "ventilation": 1, "laundry": 3}


@pytest.mark.parametrize(
    ("humidity", "feels", "grade"),
    [(45, 18.0, 1), (60, 18.0, 2), (79, 18.0, 2), (80, 18.0, 3), (45, 4.9, 2)],
)
def test_laundry_humidity_and_cold(humidity, feels, grade):
    weather = _weather(humidity=humidity, feelsLike=feels)

    assert _grades(weather=weather)["laundry"] == grade


def test_worst_matching_rule_wins():
    # 비(4)와 습도(3)가 함께 맞으면 더 나쁜 비 규칙의 문구를 쓴다
    result = calculate(_weather(precipitation=1.0, humidity=90), _air(), None)

    assert result["laundry"]["grade"] == 4
    assert result["laundry"]["summary"] == "비나 눈이 와서 밖에 널 수 없어요."


def test_missing_air_drops_mask_and_ventilation_only():
    result = calculate(_weather(), None, None)

    assert result["mask"] is None
    assert result["ventilation"] is None
    assert result["outing"]["grade"] == 1
    assert result["laundry"]["grade"] == 1


def test_missing_weather_drops_outing_and_laundry():
    result = calculate(None, _air(3, 3), None)

    assert result["outing"] is None
    assert result["laundry"] is None
    assert result["mask"]["grade"] == 3
    assert result["ventilation"]["grade"] == 3
