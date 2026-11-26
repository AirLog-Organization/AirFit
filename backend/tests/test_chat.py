from airfit import chat
from airfit.life_indices import calculate
from airfit.outfit import recommend

WEATHER = {
    "temp": 14.6,
    "feelsLike": 13.2,
    "tempMin": 9.0,
    "tempMax": 19.4,
    "humidity": 55,
    "windSpeed": 3.1,
    "precipitation": 0,
}
AIR = {"pm10": {"value": 78, "grade": 2}, "pm25": {"value": 40, "grade": 3}}


def _conditions(weather=WEATHER, air=AIR) -> dict:
    return {
        "location": {"fullName": "서울특별시 노원구 월계1동"},
        "weather": weather,
        "air": air,
        "indices": calculate(weather, air, None),
        "outfit": recommend(weather, air, None),
    }


def test_context_lists_all_parts():
    text = chat.context(_conditions())

    assert "지역: 서울특별시 노원구 월계1동" in text
    assert "기온 15°, 체감 13°" in text
    assert "미세먼지 78 (보통), 초미세먼지 40 (나쁨)" in text
    assert "- 마스크: 권장," in text
    assert "옷차림: 쌀쌀해요." in text
    assert "일교차가 10도 이상이에요." in text


def test_context_marks_missing_parts():
    text = chat.context({"weather": None, "air": None, "indices": None, "outfit": None})

    assert "지역: 알 수 없는 지역" in text
    assert "날씨: 정보 없음" in text
    assert "대기질: 정보 없음" in text
    assert "- 외출: 정보 없음" in text
    assert "옷차림: 정보 없음" in text


def test_context_marks_missing_values():
    weather = {**WEATHER, "humidity": None}
    air = {"pm10": {"value": None, "grade": None}, "pm25": AIR["pm25"]}

    text = chat.context(_conditions(weather, air))

    assert "습도 정보 없음" in text
    assert "미세먼지 정보 없음 (정보 없음)" in text


def test_rule_answer_summarizes_outfit_tips_and_mask():
    conditions = _conditions()

    answer = chat.rule_answer(conditions)

    assert answer.startswith(conditions["outfit"]["summary"])
    assert "일교차가 10도 이상이에요." in answer
    assert conditions["indices"]["mask"]["summary"] in answer


def test_rule_answer_skips_mask_when_air_is_good():
    good_air = {"pm10": {"value": 20, "grade": 1}, "pm25": {"value": 8, "grade": 1}}

    answer = chat.rule_answer(_conditions(air=good_air))

    assert "마스크" not in answer


def test_rule_answer_without_weather():
    answer = chat.rule_answer(_conditions(weather=None))

    assert answer == "날씨 정보를 불러오지 못해 지금은 옷차림을 알려 드리기 어려워요."
