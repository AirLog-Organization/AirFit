"""API Gateway HTTP API(payload 2.0) 진입점. 라우트는 기능을 붙이면서 늘린다."""

import json
import logging

from airfit import cache, kakao
from airfit.conditions import AllSourcesFailed, get_conditions
from airfit.upstream import UpstreamError

logger = logging.getLogger(__name__)

# 국내 범위 밖 좌표는 Kakao, 에어코리아 모두 결과가 없다
LAT_RANGE = (33.0, 39.0)
LON_RANGE = (124.0, 132.0)
# 한글 200~300자 사이에서 Kakao가 400을 돌려준다. 주소 검색어로는 100자면 충분하다
MAX_QUERY_LENGTH = 100
# 주소 검색 결과는 행정구역이 바뀔 때만 달라진다
REGIONS_TTL = 7 * 24 * 3600


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _error(status: int, code: str, message: str) -> dict:
    return _response(status, {"error": code, "message": message})


def _regions(params: dict) -> dict:
    query = params.get("q", "").strip()
    if not query:
        return _error(400, "invalid_params", "검색어(q)를 입력해 주세요.")
    if len(query) > MAX_QUERY_LENGTH:
        return _error(400, "invalid_params", f"검색어는 {MAX_QUERY_LENGTH}자까지 입력할 수 있어요.")
    try:
        regions = cache.get_or_fetch(
            f"regions#{query}", REGIONS_TTL, lambda: kakao.search_regions(query)
        )
        return _response(200, {"regions": regions})
    except UpstreamError:
        logger.exception("지역 검색 실패")
        return _error(502, "upstream_error", "지역 검색에 잠시 실패했어요.")


def _conditions(params: dict) -> dict:
    try:
        lat, lon = float(params["lat"]), float(params["lon"])
    except (KeyError, ValueError):
        return _error(400, "invalid_params", "lat과 lon을 숫자로 함께 보내야 합니다.")
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return _error(400, "invalid_params", "국내 좌표만 조회할 수 있어요.")
    try:
        return _response(200, get_conditions(lat, lon))
    except AllSourcesFailed:
        return _error(502, "upstream_error", "날씨와 대기질 정보를 잠시 불러오지 못했어요.")


def lambda_handler(event: dict, context) -> dict:
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    params = event.get("queryStringParameters") or {}

    if method != "GET":
        return _error(404, "not_found", "없는 경로입니다.")
    if path == "/api/health":
        return _response(200, {"status": "ok"})
    if path == "/api/regions":
        return _regions(params)
    if path == "/api/conditions":
        return _conditions(params)
    return _error(404, "not_found", "없는 경로입니다.")
