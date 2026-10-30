import pytest

from airfit.rule_engine import is_valid_condition, matches, metrics


def test_metrics_from_weather_air_and_hourly():
    weather = {
        "temp": 15.0,
        "feelsLike": 13.0,
        "tempMin": 8.0,
        "tempMax": 19.0,
        "humidity": 70,
        "windSpeed": 3.0,
        "precipitation": 0,
    }
    air = {"pm10": {"grade": 2}, "pm25": {"grade": 3}}
    hourly = [{"pop": 10}, {"pop": 40}]

    assert metrics(weather, air, hourly) == {
        "feelsLike": 13.0,
        "humidity": 70,
        "precipitation": 0,
        "dailyRange": 11.0,
        "rainChance": 40,
        "dustGrade": 3,
        "windSpeed": 3.0,
    }


def test_metrics_are_none_without_data():
    assert set(metrics(None, None, None).values()) == {None}


def test_feels_like_falls_back_to_temp():
    assert metrics({"temp": 20.0, "feelsLike": None}, None, None)["feelsLike"] == 20.0


@pytest.mark.parametrize(
    ("conditions", "expected"),
    [
        ([{"metric": "dustGrade", "gte": 3}], True),
        ([{"metric": "dustGrade", "gte": 4}], False),
        ([{"metric": "dustGrade", "gte": 3}, {"metric": "humidity", "lt": 60}], False),
        ([{"metric": "windSpeed", "gte": 1}], False),  # 값이 없으면 맞지 않는다
        ([], True),
    ],
)
def test_matches_requires_every_condition(conditions, expected):
    values = {"dustGrade": 3, "humidity": 70, "windSpeed": None}

    assert matches(conditions, values) is expected


@pytest.mark.parametrize(
    ("condition", "valid"),
    [
        ({"metric": "humidity", "gte": 80}, True),
        ({"metric": "feelsLike", "lt": 5.5}, True),
        ({"metric": "unknown", "gte": 1}, False),
        ({"metric": "humidity", "gt": 80}, False),
        ({"metric": "humidity", "gte": 80, "lt": 90}, False),
        ({"metric": "humidity", "gte": "80"}, False),
    ],
)
def test_is_valid_condition(condition, valid):
    assert is_valid_condition(condition) is valid
