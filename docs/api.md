# AirFit API 명세 (초안)

> 상태: 초안. 팀 리뷰에서 "합의할 것" 항목을 정한 뒤 확정합니다.

브라우저는 이 API만 호출합니다. 에어코리아와 OpenWeatherMap(OWM)은 백엔드가 대신 호출하고 결과를 DynamoDB에 캐시하므로, 외부 API 키는 브라우저에 노출되지 않습니다.

## 공통 규칙

| 항목 | 규칙 |
| --- | --- |
| 도메인 | 프론트와 같은 도메인입니다. CloudFront가 `/api/*` 요청은 API Gateway로, 나머지는 S3의 프론트 빌드로 보냅니다. 프론트는 `/api/conditions`처럼 상대 경로로 호출합니다 |
| 경로 | 모든 API 경로는 `/api`로 시작합니다. 그 밖의 경로는 프론트 화면이 씁니다 |
| 버전 | 경로에 버전을 붙이지 않습니다. API를 쓰는 곳이 우리 프론트뿐이고 함께 배포되므로, 응답 구조가 바뀌면 같은 PR에서 프론트도 고칩니다 |
| 형식 | 요청과 응답 모두 JSON(UTF-8), 필드 이름은 camelCase |
| 시각 | ISO 8601, 한국 시간(`+09:00`). 예: `2026-10-27T14:00:00+09:00` |
| 단위 | 기온 °C, 풍속 m/s, 습도와 확률 %, 강수량 mm, 미세먼지 µg/m³, 오존 ppm |
| 인증 | 없음. 로그인과 사용자 데이터 저장은 하지 않습니다 |
| CORS | 같은 도메인이라 필요 없습니다. CloudFront를 붙이기 전까지만 API Gateway의 CORS 설정으로 `GET`을 허용합니다 |
| 로컬 개발 | Vite 개발 서버의 proxy로 `/api` 요청을 배포된 API(또는 `sam local start-api`)에 넘깁니다 |
| 값이 없을 때 | 필드를 빼지 않고 `null`로 보냅니다 |

### 에러 응답

```json
{ "error": "invalid_params", "message": "lat과 lon은 함께 보내야 합니다." }
```

`error`는 프론트가 분기에 쓰는 코드이고, `message`는 화면에 그대로 띄워도 되는 한국어 문장입니다.

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 필수 파라미터 누락, 형식 오류, 범위 밖 좌표 |
| 404 | `not_found` | 없는 경로 |
| 404 | `region_not_found` | 없는 지역 코드 |
| 502 | `upstream_error` | 외부 API가 모두 실패했고 캐시도 없음 |
| 500 | `internal_error` | 그 밖의 서버 오류 |

외부 API 중 **하나만** 실패하면 에러로 끝내지 않고 200으로 응답합니다. 실패한 쪽 필드는 `null`이 되고, `warnings`에 이유가 담깁니다([부분 실패](#부분-실패) 참고).

## 엔드포인트 한눈에 보기

| 메서드 | 경로 | 내용 | 단계 |
| --- | --- | --- | --- |
| GET | `/api/health` | 상태 확인 | 구현됨 |
| GET | `/api/regions` | 시·군·구 검색 | 1단계 |
| GET | `/api/conditions` | 날씨, 대기질, 생활지수 (2단계부터 옷차림 추천과 시간대별 예보 포함) | 1단계 |
| POST | `/api/wardrobe/recommend` | 옷장 안에서 코디 추천 | 3단계 |
| POST | `/api/wardrobe/classify` | 한 줄 입력을 옷 속성으로 분류 (LLM) | 도전 |
| POST | `/api/chat` | 옷장 기반 챗봇 (LLM) | 도전 |

---

## GET /api/health

배포 확인과 시연 전 콜드 스타트 예열용입니다.

```json
{ "status": "ok" }
```

---

## GET /api/regions

지역 검색 화면의 자동완성에 씁니다. 시·군·구 목록은 백엔드에 JSON 파일로 들어 있어 외부 API를 호출하지 않습니다.

### 파라미터

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `q` | 예 | 검색어, 1자 이상. 시·도 또는 시·군·구 이름의 일부 (예: `강남`, `수원`) |
| `limit` | 아니요 | 최대 개수, 기본 10, 최대 30 |

### 응답 200

```json
{
  "regions": [
    {
      "code": "11680",
      "name": "강남구",
      "fullName": "서울특별시 강남구",
      "lat": 37.5172,
      "lon": 127.0473
    }
  ]
}
```

| 필드 | 설명 |
| --- | --- |
| `code` | 시·군·구 5자리 코드(행정표준코드). `/api/conditions`의 `region`에 그대로 넘깁니다 |
| `name` | 짧은 이름, 카드 제목용 |
| `fullName` | 시·도를 붙인 이름, 목록 표시용 |
| `lat`, `lon` | 대표 좌표(WGS84). 날씨 조회와 가까운 측정소 찾기에 씁니다 |

결과가 없으면 `regions`가 빈 배열입니다(404 아님).

---

## GET /api/conditions

메인 화면 한 번에 필요한 데이터를 모두 돌려줍니다. 카드마다 따로 호출하지 않도록 하나로 묶었습니다.

### 파라미터

위치는 둘 중 하나로 지정합니다. 둘 다 오면 `region`이 우선합니다.

| 이름 | 설명 |
| --- | --- |
| `lat`, `lon` | 브라우저 위치(WGS84). 국내 범위(위도 33~39, 경도 124~132) 밖이면 400 |
| `region` | `/api/regions`의 `code`. 위치 권한을 거부했을 때 씁니다 |

### 응답 200

```json
{
  "location": {
    "name": "강남구",
    "fullName": "서울특별시 강남구",
    "regionCode": "11680",
    "lat": 37.5172,
    "lon": 127.0473
  },
  "weather": {
    "observedAt": "2026-10-27T14:00:00+09:00",
    "temp": 14.2,
    "feelsLike": 12.8,
    "tempMin": 9.1,
    "tempMax": 16.4,
    "humidity": 48,
    "windSpeed": 3.4,
    "clouds": 20,
    "precipitation": 0,
    "condition": { "code": 801, "main": "Clouds", "description": "구름 조금" }
  },
  "air": {
    "measuredAt": "2026-10-27T14:00:00+09:00",
    "station": { "name": "강남구", "distanceKm": 1.2 },
    "pm10": { "value": 42, "grade": 2 },
    "pm25": { "value": 23, "grade": 2 },
    "o3": { "value": 0.031, "grade": 1 },
    "khai": { "value": 68, "grade": 2 }
  },
  "indices": {
    "outing":      { "grade": 1, "label": "좋음", "summary": "산책하기 좋은 날이에요." },
    "mask":        { "grade": 2, "label": "선택", "summary": "민감군은 마스크를 챙기세요." },
    "ventilation": { "grade": 1, "label": "좋음", "summary": "10분 이상 창문을 열어 두세요." },
    "laundry":     { "grade": 1, "label": "좋음", "summary": "바람이 있어 잘 말라요." }
  },
  "outfit": null,
  "hourly": null,
  "warnings": [],
  "meta": {
    "fetchedAt": "2026-10-27T14:07:12+09:00",
    "cached": true,
    "sources": ["에어코리아", "OpenWeatherMap"]
  }
}
```

### `location`

`region`으로 조회하면 그 지역이 그대로 들어갑니다. 좌표로 조회하면 시·군·구 목록에서 가장 가까운 대표 좌표의 지역 이름을 붙이고, `lat`과 `lon`은 요청 값을 그대로 돌려줍니다.

### `weather` (출처: OWM 현재 날씨)

| 필드 | 설명 |
| --- | --- |
| `observedAt` | OWM 관측 시각 |
| `temp`, `feelsLike` | 기온, 체감온도 |
| `tempMin`, `tempMax` | 오늘 최저, 최고 기온. 옷차림 추천에 씁니다 |
| `humidity`, `clouds` | 습도, 구름양(%) |
| `windSpeed` | 풍속 |
| `precipitation` | 최근 1시간 강수량(비와 눈 합산), 없으면 0 |
| `condition.code` | OWM 날씨 코드. 프론트는 이 코드로 아이콘을 고릅니다 |
| `condition.main`, `condition.description` | 날씨 분류(영문), 한국어 설명 |

### `air` (출처: 에어코리아 실시간 측정)

| 필드 | 설명 |
| --- | --- |
| `measuredAt` | 측정 시각. 에어코리아는 1시간 단위라 날씨보다 늦을 수 있습니다 |
| `station` | 요청 위치에서 가장 가까운 측정소와 거리 |
| `pm10`, `pm25`, `o3` | 항목별 측정값과 등급 |
| `khai` | 통합대기환경지수(CAI) |
| `grade` | 에어코리아 등급 그대로: 1 좋음, 2 보통, 3 나쁨, 4 매우나쁨 |

측정소 점검 등으로 항목 하나만 비면 그 항목의 `value`와 `grade`가 `null`입니다.

### `indices` (생활지수)

네 지수 모두 같은 모양입니다. 산출 기준은 [`life-indices.md`](life-indices.md)에 따로 정리합니다.

| 필드 | 설명 |
| --- | --- |
| `grade` | 1~4. **1이 가장 좋고 4가 가장 나쁩니다.** 프론트는 이 값으로 카드 색을 정합니다 |
| `label` | 등급 이름. 지수마다 다르므로 서버가 내려 주는 값을 그대로 표시합니다 |
| `summary` | 카드에 띄울 한 문장 |

키 이름과 등급 이름(예시이며 `life-indices.md`에서 확정):

| 키 | 지수 | grade 1 | grade 2 | grade 3 | grade 4 |
| --- | --- | --- | --- | --- | --- |
| `outing` | 외출 | 좋음 | 보통 | 주의 | 자제 |
| `mask` | 마스크 | 불필요 | 선택 | 권장 | 필수 |
| `ventilation` | 환기 | 좋음 | 보통 | 짧게 | 자제 |
| `laundry` | 빨래 | 좋음 | 보통 | 실내 건조 | 불가 |

계산에 필요한 데이터가 빠지면 그 지수는 `null`입니다. 예를 들어 대기질 조회에 실패하면 `mask`와 `ventilation`이 `null`이 됩니다.

### `outfit` (2단계, 옷장 없는 규칙 기반 추천)

1단계에서는 항상 `null`입니다. 규칙 파일(JSON) 구조가 정해지면 아래 모양으로 채웁니다.

```json
{
  "summary": "얇은 니트에 가벼운 겉옷이 좋아요.",
  "items": [
    { "category": "outer", "name": "가벼운 재킷" },
    { "category": "top", "name": "얇은 니트" },
    { "category": "bottom", "name": "긴 바지" }
  ],
  "tips": ["일교차가 7도 이상이에요. 겉옷을 챙기세요."]
}
```

`category`는 `outer`, `top`, `bottom`, `shoes`, `accessory` 중 하나입니다. 3단계 옷장 등록에서도 같은 값을 씁니다.

### `hourly` (2단계, 시간대별 그래프)

1단계에서는 항상 `null`입니다. OWM 무료 예보가 3시간 간격이라, 앞으로 24시간을 3시간 간격 8개로 내려 줍니다.

```json
[
  { "time": "2026-10-27T15:00:00+09:00", "temp": 15.1, "feelsLike": 14.0, "pop": 10, "precipitation": 0, "conditionCode": 801 }
]
```

`pop`은 강수 확률(%)입니다. 미세먼지는 시간별 예보 수치가 없어 그래프에 넣지 않습니다.

### 부분 실패

외부 API 하나가 실패하고 캐시도 없을 때는 받은 쪽만 채워 200으로 응답합니다.

```json
{
  "weather": { "...": "..." },
  "air": null,
  "indices": { "outing": { "...": "..." }, "mask": null, "ventilation": null, "laundry": { "...": "..." } },
  "warnings": [{ "source": "air", "message": "대기질 정보를 잠시 불러오지 못했어요." }]
}
```

`warnings[].source`는 `weather` 또는 `air`입니다. 둘 다 실패하면 502 `upstream_error`입니다.

### 캐시

| 데이터 | 캐시 키 | 유효 시간 |
| --- | --- | --- |
| 날씨 | 좌표를 소수 둘째 자리(약 1km)로 반올림한 값 | 10분 |
| 대기질 | 측정소 이름 | 10분 |
| 가까운 측정소 | 좌표를 소수 둘째 자리로 반올림한 값 | 30일 |

`meta.cached`는 날씨와 대기질이 모두 캐시에서 나왔을 때 `true`입니다. `meta.sources`는 이용약관의 출처 표기용이므로 화면 하단에 표시해 주세요.

---

## 3단계 이후 (개요)

요청 형태만 미리 정해 둡니다. 세부 필드는 해당 단계에서 이 문서에 채웁니다.

### POST /api/wardrobe/recommend

옷장은 브라우저에만 저장하고, 추천을 요청할 때만 본문으로 보냅니다. 서버는 저장하지 않고 요청 본문을 로그에 남기지 않습니다.

```json
{
  "region": "11680",
  "wardrobe": [
    { "id": "a1", "category": "top", "name": "회색 니트", "thickness": "medium", "color": "gray", "waterproof": false }
  ]
}
```

`thickness`는 `thin`, `medium`, `thick` 중 하나입니다. 응답은 `outfit`과 같은 모양에 `items[].id`(옷장 항목 id)가 붙습니다.

### POST /api/wardrobe/classify, POST /api/chat (도전)

Bedrock을 호출합니다. 입력 길이 제한과 요청 제한을 두고, LLM이 실패하면 `/api/wardrobe/recommend`의 규칙 기반 결과로 대체합니다.

---

## 합의할 것

리뷰에서 정해 주세요. 정해지면 이 절을 지우고 본문에 반영합니다.

1. **`/api/conditions` 하나로 묶을지.** 이 초안은 날씨, 대기질, 지수, 추천을 한 번에 보냅니다. 카드별 로딩 상태가 필요하면 나눌 수도 있지만, 호출 수와 콜드 스타트가 늘어납니다. (프론트 @hwi-cafe)
2. **지수 등급 이름과 `grade` 방향.** 1이 좋음, 4가 나쁨으로 통일했습니다. (전원)
3. **`outfit` 구조와 `category` 값.** 옷차림 규칙 JSON을 설계하는 쪽에 맞춥니다. (규칙 @KxxgHx)
4. **지역 단위.** 시·군·구로 시작합니다. 읍·면·동까지 내려갈지는 1단계 결과를 보고 정합니다.
