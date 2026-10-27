"""API Gateway HTTP API(payload 2.0) 진입점. 라우트는 기능을 붙이면서 늘린다."""

import json


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def lambda_handler(event: dict, context) -> dict:
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]

    if method == "GET" and path == "/v1/health":
        return _response(200, {"status": "ok"})
    return _response(404, {"error": "not_found"})
