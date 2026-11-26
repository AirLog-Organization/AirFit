import pytest

from test_wardrobe_api import _post


def test_classifies_name():
    status, body = _post({"name": "롱패딩"}, path="/api/wardrobe/classify")

    assert status == 200
    assert body == {
        "category": "outer",
        "thickness": "thick",
        "waterproof": False,
        "source": "rules",
    }


def test_unknown_name_returns_null_category():
    status, body = _post({"name": "선물 받은 것"}, path="/api/wardrobe/classify")

    assert status == 200
    assert body["category"] is None


@pytest.mark.parametrize("name", [None, "", "   ", "가" * 51, 123, ["패딩"]])
def test_rejects_bad_name(name):
    status, body = _post({"name": name}, path="/api/wardrobe/classify")

    assert status == 400
    assert body["error"] == "invalid_params"


def test_rejects_non_object_body():
    status, _ = _post("[]", path="/api/wardrobe/classify")

    assert status == 400


def test_does_not_call_external_apis(fake_upstream):
    _, calls = fake_upstream

    _post({"name": "레인부츠"}, path="/api/wardrobe/classify")

    assert calls == []
