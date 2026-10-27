import json

from airfit.handler import lambda_handler


def _event(path: str, method: str = "GET") -> dict:
    return {"rawPath": path, "requestContext": {"http": {"method": method}}}


def test_health_returns_ok():
    response = lambda_handler(_event("/api/health"), None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "ok"}


def test_unknown_route_returns_404():
    response = lambda_handler(_event("/api/nope"), None)

    assert response["statusCode"] == 404
