import pytest

from airfit.classify import classify, load_rules
from airfit.outfit import CATEGORIES


def test_rules_file_is_valid():
    rules = load_rules()

    assert set(rules["categories"]) == CATEGORIES
    assert set(rules["thickness"]) == {"thick", "thin"}
    keywords = [k for words in rules["categories"].values() for k in words]
    keywords += rules["thickness"]["thick"] + rules["thickness"]["thin"] + rules["waterproof"]
    # 공백을 지운 이름과 비교하므로 키워드에도 공백이 없어야 한다
    assert all(keyword and keyword == "".join(keyword.split()) for keyword in keywords)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("롱패딩", {"category": "outer", "thickness": "thick", "waterproof": False}),
        ("롱 패딩", {"category": "outer", "thickness": "thick", "waterproof": False}),
        ("반팔 티셔츠", {"category": "top", "thickness": "thin", "waterproof": False}),
        ("회색 니트", {"category": "top", "thickness": "medium", "waterproof": False}),
        ("기모 바지", {"category": "bottom", "thickness": "thick", "waterproof": False}),
        ("린넨 셔츠", {"category": "top", "thickness": "thin", "waterproof": False}),
        ("레인부츠", {"category": "shoes", "thickness": "medium", "waterproof": True}),
        ("방수 바람막이", {"category": "outer", "thickness": "medium", "waterproof": True}),
        ("털모자", {"category": "accessory", "thickness": "thick", "waterproof": False}),
    ],
)
def test_classifies_common_names(name, expected):
    assert classify(name) == expected


def test_longest_keyword_then_file_order_decides_category():
    # "후드"(상의)와 "집업"(겉옷)은 길이가 같아 규칙 파일에 먼저 적은 겉옷이 된다
    assert classify("후드집업")["category"] == "outer"
    # "레인"보다 긴 "레인부츠"가 맞아 신발이 된다
    assert classify("레인부츠")["category"] == "shoes"
    assert classify("후드티")["category"] == "top"


def test_unknown_name_has_no_category():
    assert classify("할머니가 주신 선물") == {
        "category": None,
        "thickness": "medium",
        "waterproof": False,
    }
