"""API Gateway HTTP API(payload 2.0) 진입점. 라우트는 기능을 붙이면서 늘린다."""

import base64
import binascii
import json
import logging

from airfit import cache, classify, kakao, llm_classify, outfit
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
# 옷장 추천 요청 제한. 옷 하나가 200바이트 안팎이라 200벌이어도 64KB 안에 든다
MAX_BODY_BYTES = 64 * 1024
MAX_WARDROBE_ITEMS = 200
MAX_ITEM_ID_LENGTH = 64
MAX_ITEM_NAME_LENGTH = 50


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


def _coordinates(lat, lon) -> tuple[float, float] | dict:
    """좌표를 숫자로 바꾼다. 잘못되면 400 응답을 돌려준다."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return _error(400, "invalid_params", "lat과 lon을 숫자로 함께 보내야 합니다.")
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return _error(400, "invalid_params", "국내 좌표만 조회할 수 있어요.")
    return lat, lon


def _conditions(params: dict) -> dict:
    coordinates = _coordinates(params.get("lat"), params.get("lon"))
    if isinstance(coordinates, dict):
        return coordinates
    try:
        return _response(200, get_conditions(*coordinates))
    except AllSourcesFailed:
        return _error(502, "upstream_error", "날씨와 대기질 정보를 잠시 불러오지 못했어요.")


def _json_body(event: dict) -> dict | None:
    raw = event.get("body") or ""
    try:
        data = base64.b64decode(raw) if event.get("isBase64Encoded") else raw.encode("utf-8")
        if len(data) > MAX_BODY_BYTES:
            return None
        body = json.loads(data)
    except (binascii.Error, UnicodeError, ValueError):
        return None
    return body if isinstance(body, dict) else None


def _is_wardrobe_item(item) -> bool:
    return (
        isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and 0 < len(item["id"]) <= MAX_ITEM_ID_LENGTH
        and item.get("category") in outfit.CATEGORIES
        and isinstance(item.get("name"), str)
        and 0 < len(item["name"].strip()) <= MAX_ITEM_NAME_LENGTH
        and item.get("thickness") in outfit.THICKNESSES
        and isinstance(item.get("waterproof"), bool)
    )


def _wardrobe_recommend(event: dict) -> dict:
    # 옷장은 개인 정보라 요청 본문은 로그에 남기지 않는다 (docs/outfit-rules.md "옷장 추천")
    body = _json_body(event)
    if body is None:
        return _error(400, "invalid_params", "요청 본문은 JSON 객체여야 합니다.")
    coordinates = _coordinates(body.get("lat"), body.get("lon"))
    if isinstance(coordinates, dict):
        return coordinates

    wardrobe = body.get("wardrobe")
    if not isinstance(wardrobe, list) or len(wardrobe) > MAX_WARDROBE_ITEMS:
        return _error(
            400, "invalid_params", f"wardrobe는 옷 {MAX_WARDROBE_ITEMS}벌까지의 목록이어야 합니다."
        )
    if not all(_is_wardrobe_item(item) for item in wardrobe):
        return _error(400, "invalid_params", "옷장에 형식이 맞지 않는 옷이 있어요.")

    try:
        conditions = get_conditions(*coordinates)
    except AllSourcesFailed:
        return _error(502, "upstream_error", "날씨와 대기질 정보를 잠시 불러오지 못했어요.")
    result = outfit.recommend_from_wardrobe(
        conditions["weather"], conditions["air"], conditions["hourly"], wardrobe
    )
    if result is None:
        return _error(502, "upstream_error", "날씨 정보를 잠시 불러오지 못해 추천할 수 없어요.")
    return _response(200, result)


def _wardrobe_classify(event: dict) -> dict:
    body = _json_body(event)
    if body is None:
        return _error(400, "invalid_params", "요청 본문은 JSON 객체여야 합니다.")
    name = body.get("name")
    if not isinstance(name, str) or not 0 < len(name.strip()) <= MAX_ITEM_NAME_LENGTH:
        return _error(
            400, "invalid_params", f"name은 1~{MAX_ITEM_NAME_LENGTH}자의 옷 이름이어야 합니다."
        )
    # source는 추정 방법. LLM(Bedrock)을 먼저 쓰고, 꺼져 있거나 실패하면 키워드 규칙을 쓴다
    result = llm_classify.classify(name)
    if result is not None:
        return _response(200, {**result, "source": "llm"})
    return _response(200, {**classify.classify(name), "source": "rules"})


def lambda_handler(event: dict, context) -> dict:
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    params = event.get("queryStringParameters") or {}

    if method == "POST" and path == "/api/wardrobe/recommend":
        return _wardrobe_recommend(event)
    if method == "POST" and path == "/api/wardrobe/classify":
        return _wardrobe_classify(event)
    if method != "GET":
        return _error(404, "not_found", "없는 경로입니다.")
    if path == "/api/health":
        return _response(200, {"status": "ok"})
    if path == "/api/regions":
        return _regions(params)
    if path == "/api/conditions":
        return _conditions(params)
    return _error(404, "not_found", "없는 경로입니다.")
