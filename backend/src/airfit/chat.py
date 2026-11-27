"""챗봇 답의 재료. /api/conditions 응답(지역, 날씨, 대기질, 생활지수, 옷차림)을 글로 요약한다.

LLM(llm_chat.py)에 넘길 오늘 정보와, LLM을 쓸 수 없을 때 돌려줄 규칙 기반 답을 만든다.
"""

AIR_GRADES = {1: "좋음", 2: "보통", 3: "나쁨", 4: "매우나쁨"}
INDEX_NAMES = {"outing": "외출", "mask": "마스크", "ventilation": "환기", "laundry": "빨래"}


def _number(value, unit: str) -> str:
    return "정보 없음" if value is None else f"{round(value)}{unit}"


def _weather(weather: dict | None) -> str:
    if not weather:
        return "날씨: 정보 없음"
    return (
        f"날씨: 기온 {_number(weather.get('temp'), '°')}, "
        f"체감 {_number(weather.get('feelsLike'), '°')}, "
        f"최저 {_number(weather.get('tempMin'), '°')} / "
        f"최고 {_number(weather.get('tempMax'), '°')}, "
        f"습도 {_number(weather.get('humidity'), '%')}, "
        f"바람 {_number(weather.get('windSpeed'), 'm/s')}, "
        f"최근 1시간 강수 {weather.get('precipitation') or 0}mm"
    )


def _air(air: dict | None) -> str:
    if not air:
        return "대기질: 정보 없음"
    parts = []
    for key, name in (("pm10", "미세먼지"), ("pm25", "초미세먼지")):
        value = (air.get(key) or {}).get("value")
        grade = AIR_GRADES.get((air.get(key) or {}).get("grade"), "정보 없음")
        parts.append(f"{name} {'정보 없음' if value is None else value} ({grade})")
    return "대기질: " + ", ".join(parts)


def _indices(indices: dict | None) -> str:
    lines = []
    for key, name in INDEX_NAMES.items():
        index = (indices or {}).get(key)
        lines.append(
            f"- {name}: {index['label']}, {index['summary']}" if index else f"- {name}: 정보 없음"
        )
    return "생활지수:\n" + "\n".join(lines)


def _outfit(outfit: dict | None) -> str:
    if not outfit:
        return "옷차림: 정보 없음"
    names = ", ".join(item["name"] for item in outfit["items"])
    tips = " ".join(outfit["tips"]) or "없음"
    return f"옷차림: {outfit['summary']} 추천 옷: {names}. 팁: {tips}"


def context(conditions: dict) -> str:
    """LLM에 넘길 오늘 정보. 값이 없는 부분은 "정보 없음"으로 적어 지어내지 않게 한다."""
    place = (conditions.get("location") or {}).get("fullName") or "알 수 없는 지역"
    return "\n".join(
        [
            f"지역: {place}",
            _weather(conditions.get("weather")),
            _air(conditions.get("air")),
            _indices(conditions.get("indices")),
            _outfit(conditions.get("outfit")),
        ]
    )


def rule_answer(conditions: dict) -> str:
    """LLM을 쓸 수 없을 때의 답. 질문 내용과 관계없이 오늘의 옷차림과 주의할 점을 요약한다."""
    outfit = conditions.get("outfit")
    if not outfit:
        return "날씨 정보를 불러오지 못해 지금은 옷차림을 알려 드리기 어려워요."
    sentences = [outfit["summary"], *outfit["tips"]]
    mask = (conditions.get("indices") or {}).get("mask")
    if mask and mask["grade"] >= 2:
        sentences.append(mask["summary"])
    return " ".join(sentences)
