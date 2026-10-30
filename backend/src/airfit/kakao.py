"""Kakao 로컬 API. 좌표는 x가 경도, y가 위도다."""

import os

from airfit import upstream

BASE_URL = "https://dapi.kakao.com/v2/local"


def _headers() -> dict:
    return {"Authorization": f"KakaoAK {os.environ['KAKAO_REST_API_KEY']}"}


def search_regions(query: str, size: int = 10) -> list[dict]:
    data = upstream.get_json(
        f"{BASE_URL}/search/address.json",
        {"query": query, "analyze_type": "similar", "size": size},
        _headers(),
    )
    return [
        {
            # 행정동 후보는 b_code가 빈 문자열이라 h_code로 대신한다
            "code": (doc.get("address") or {}).get("b_code")
            or (doc.get("address") or {}).get("h_code")
            or None,
            "name": doc["address_name"].split()[-1],
            "fullName": doc["address_name"],
            "lat": float(doc["y"]),
            "lon": float(doc["x"]),
        }
        for doc in data["documents"]
    ]


def region_name(lat: float, lon: float) -> dict | None:
    """좌표의 행정동 이름. 행정동 결과가 없으면 None."""
    data = upstream.get_json(
        f"{BASE_URL}/geo/coord2regioncode.json", {"x": lon, "y": lat}, _headers()
    )
    for doc in data["documents"]:
        if doc["region_type"] == "H":
            parts = [doc["region_2depth_name"], doc["region_3depth_name"]]
            return {
                # 바다는 "서해"처럼 1단계 이름만 오므로 전체 이름으로 대신한다
                "name": " ".join(p for p in parts if p) or doc["address_name"],
                "fullName": doc["address_name"],
                "regionCode": doc["code"],
            }
    return None


def to_tm(lat: float, lon: float) -> tuple[float, float]:
    """WGS84 좌표를 에어코리아 측정소 조회용 TM 좌표로 바꾼다."""
    data = upstream.get_json(
        f"{BASE_URL}/geo/transcoord.json",
        {"x": lon, "y": lat, "input_coord": "WGS84", "output_coord": "TM"},
        _headers(),
    )
    doc = data["documents"][0]
    return doc["x"], doc["y"]
