"""생활지수(외출, 마스크, 환기, 빨래). 기준값은 rules/life_indices.json에 두고 여기서는 적용만 한다.

기준과 근거는 docs/life-indices.md에 정리한다.
"""

from airfit import rule_engine

KEYS = ("outing", "mask", "ventilation", "laundry")


def load_rules() -> dict:
    return rule_engine.load_rules("life_indices")


def _index(rule: dict, values: dict) -> dict | None:
    # 판단에 꼭 필요한 값이 없으면 지수를 내지 않는다 (예: 대기질 실패 시 마스크, 환기)
    if any(values[metric] is None for metric in rule["requires"]):
        return None

    grade, summary = 1, rule["default"]
    # 규칙은 나쁜 등급부터 적혀 있어서 처음 맞는 규칙이 등급을 정한다
    for candidate in rule["rules"]:
        if rule_engine.matches(candidate["when"], values):
            grade, summary = candidate["grade"], candidate["summary"]
            break
    return {"grade": grade, "label": rule["labels"][grade - 1], "summary": summary}


def calculate(weather: dict | None, air: dict | None, hourly: list | None) -> dict:
    """지수 4개를 {grade, label, summary} 또는 None으로 돌려준다. grade는 1이 가장 좋다."""
    values = rule_engine.metrics(weather, air, hourly)
    rules = load_rules()
    return {key: _index(rules[key], values) for key in KEYS}
