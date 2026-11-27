"""옷 이름으로 옷장 항목의 종류, 두께, 방수 여부를 추정한다. 키워드는 rules/wardrobe_classify.json.

옷장 등록 화면에서 이름을 적으면 나머지 칸을 미리 채워 주려는 용도다. 추정이 틀릴 수 있으므로
사용자가 화면에서 고칠 수 있어야 하고, 기준은 docs/outfit-rules.md "옷 분류"에 정리한다.
"""

from airfit import rule_engine


def load_rules() -> dict:
    return rule_engine.load_rules("wardrobe_classify")


def _normalize(name: str) -> str:
    # "롱 패딩"과 "롱패딩"을 같게 보려고 공백을 지운다
    return "".join(name.split()).lower()


def _longest_match(text: str, keywords: list[str]) -> int:
    return max((len(keyword) for keyword in keywords if keyword in text), default=0)


def _category(text: str, categories: dict[str, list[str]]) -> str | None:
    # "레인부츠"(신발)처럼 짧은 키워드("레인")보다 긴 키워드가 더 정확하므로 가장 긴 키워드가 맞은
    # 종류를 고른다. "후드집업"처럼 길이가 같으면 규칙 파일에 먼저 적은 종류(겉옷)를 고른다
    best, best_length = None, 0
    for category, keywords in categories.items():
        length = _longest_match(text, keywords)
        if length > best_length:
            best, best_length = category, length
    return best


def _thickness(text: str, rules: dict[str, list[str]]) -> str:
    thick = _longest_match(text, rules["thick"])
    thin = _longest_match(text, rules["thin"])
    if thick == thin == 0:
        return "medium"
    return "thick" if thick >= thin else "thin"


def classify(name: str) -> dict:
    """{category, thickness, waterproof}. 종류를 알 수 없으면 category는 None이다."""
    rules = load_rules()
    text = _normalize(name)
    return {
        "category": _category(text, rules["categories"]),
        "thickness": _thickness(text, rules["thickness"]),
        "waterproof": any(keyword in text for keyword in rules["waterproof"]),
    }
