# API 명세

AirFit 백엔드(Lambda)가 제공하는 API입니다. 브라우저는 이 API만 호출하고, 에어코리아, OpenWeather, Kakao, Anthropic API는 백엔드가 대신 호출합니다. 그래서 외부 API 키가 브라우저에 노출되지 않습니다.

응답 예시는 2026-11-27에 배포 사이트에서 서울 노원구 월계1동 좌표(`lat=37.62`, `lon=127.06`)로 실제 호출한 결과이고, 길면 일부를 줄였습니다.

## 공통 규칙

| 항목 | 규칙 |
| --- | --- |
| 주소 | 프론트와 같은 도메인입니다. CloudFront가 `/api/*` 요청은 API Gateway로, 나머지는 S3의 프론트 빌드로 보냅니다. 프론트는 `/api/conditions`처럼 상대 경로로 호출합니다 |
| 경로 | 모든 API 경로는 `/api`로 시작하고, 버전을 붙이지 않습니다. API를 쓰는 곳이 우리 프론트뿐이고 함께 배포되므로, 응답 모양이 바뀌면 같은 PR에서 프론트도 고칩니다 |
| 형식 | 요청과 응답 모두 JSON(UTF-8), 필드 이름은 camelCase |
| 시각 | ISO 8601, 한국 시간(`+09:00`). 예: `2026-11-27T15:00:00+09:00` |
| 단위 | 기온 °C, 풍속 m/s, 습도, 구름양, 강수 확률 %, 강수량 mm, 미세먼지 µg/m³, 오존 ppm |
| 좌표 | WGS84 위도(`lat`), 경도(`lon`). 국내 범위(위도 33~39, 경도 124~132)만 받습니다 |
| 인증 | 없습니다. 로그인이 없고, 사용자 데이터(옷장, 질문)를 서버에 저장하지 않습니다 |
| 값이 없을 때 | 필드를 빼지 않고 `null`로 보냅니다 |
| 요청 수 제한 | API 전체에 초당 평균 20, 순간 40. 넘으면 API Gateway가 429로 응답합니다 |

### 오류 응답

백엔드가 만든 오류는 모두 같은 모양입니다.

```json
{ "error": "invalid_params", "message": "국내 좌표만 조회할 수 있어요." }
```

`error`는 프론트가 분기에 쓰는 코드이고, `message`는 화면에 그대로 띄워도 되는 한국어 문장입니다.

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 필수 값 누락, 형식 오류, 국내가 아닌 좌표, 길이 제한 초과 |
| 502 | `upstream_error` | 외부 API를 받지 못해 응답을 만들 수 없음 |

아래 두 경우는 API Gateway가 Lambda를 부르기 전에 응답해서, 모양이 `{ "message": "..." }`입니다.

| 상태 | 본문 | 언제 |
| --- | --- | --- |
| 404 | `{ "message": "Not Found" }` | 등록되지 않은 경로, 또는 경로는 있지만 메서드가 다름(예: `POST /api/health`) |
| 429 | `{ "message": "Too Many Requests" }` | 요청 수 제한 초과 |

라우트는 `backend/template.yaml`의 `Events`에 메서드별로 등록되어 있습니다. `handler.py`의 404 `not_found`는 템플릿과 코드가 어긋났을 때를 위한 안전장치라 평소에는 나오지 않습니다.

## 엔드포인트 한눈에 보기

| 메서드 | 경로 | 내용 | 자세한 기준 |
| --- | --- | --- | --- |
| GET | [`/api/health`](#get-apihealth) | 상태 확인 | |
| GET | [`/api/regions`](#get-apiregions) | 지역 검색 | [external-apis.md](external-apis.md) |
| GET | [`/api/conditions`](#get-apiconditions) | 날씨, 대기질, 생활지수, 옷차림, 시간대별 예보 | [life-indices.md](life-indices.md), [outfit-rules.md](outfit-rules.md) |
| POST | [`/api/wardrobe/recommend`](#post-apiwardroberecommend) | 옷장 안에서 오늘 입을 옷 추천 | [outfit-rules.md "옷장 추천"](outfit-rules.md#옷장-추천) |
| POST | [`/api/wardrobe/classify`](#post-apiwardrobeclassify) | 옷 이름으로 종류, 두께, 방수 추정 | [outfit-rules.md "옷 분류"](outfit-rules.md#옷-분류) |
| POST | [`/api/chat`](#post-apichat) | 오늘 날씨와 옷차림 질문에 답하는 챗봇 | [chat.md](chat.md) |

---

## GET /api/health

배포 확인과 시연 전 콜드 스타트 예열용입니다. 외부 API를 부르지 않습니다.

```json
{ "status": "ok" }
```

---

## GET /api/regions

지역 검색 화면에서 씁니다. Kakao 주소 검색 결과를 7일 동안 캐시합니다.

### 파라미터

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `q` | 예 | 검색어. 앞뒤 공백을 뺀 1~100자. 시·도, 시·군·구, 읍·면·동 이름 (예: `월계`, `노원구 월계동`) |

### 응답 200

```http
GET /api/regions?q=월계
```

```json
{
  "regions": [
    {
      "code": "1135010200",
      "name": "월계동",
      "fullName": "서울 노원구 월계동",
      "lat": 37.6199191869583,
      "lon": 127.062987742987
    },
    {
      "code": "1135056000",
      "name": "월계1동",
      "fullName": "서울 노원구 월계1동",
      "lat": 37.6198903481106,
      "lon": 127.063001311172
    }
  ]
}
```

| 필드 | 설명 |
| --- | --- |
| `code` | 10자리 법정동 코드. 행정동 후보는 행정동 코드. 표시와 구분용이고 다른 API에는 넘기지 않습니다 |
| `name` | 주소의 마지막 단어. 카드 제목용 |
| `fullName` | 전체 주소. 목록 표시용 |
| `lat`, `lon` | 지역의 좌표. 이 값으로 `/api/conditions`를 부릅니다 |

최대 10개이고, 결과가 없으면 `regions`가 빈 배열입니다(404 아님).

### 오류

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | `q`가 없거나 비었음, 100자를 넘음 |
| 502 | `upstream_error` | Kakao 주소 검색 실패 |

---

## GET /api/conditions

메인 화면에 필요한 데이터를 한 번에 돌려줍니다. 지역명, 날씨, 대기질은 서로 의존하지 않아 백엔드가 병렬로 조회합니다.

### 파라미터

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `lat`, `lon` | 예 | 조회할 좌표. 브라우저 위치 또는 `/api/regions` 결과의 좌표 |

### 응답 200

```http
GET /api/conditions?lat=37.62&lon=127.06
```

```json
{
  "location": {
    "name": "노원구 월계1동",
    "fullName": "서울특별시 노원구 월계1동",
    "regionCode": "1135056000",
    "lat": 37.62,
    "lon": 127.06
  },
  "weather": {
    "observedAt": "2026-11-27T15:37:43+09:00",
    "temp": 15.91,
    "feelsLike": 15.2,
    "tempMin": 6.87,
    "tempMax": 15.91,
    "humidity": 63,
    "windSpeed": 3.09,
    "clouds": 75,
    "precipitation": 0,
    "isDay": true,
    "condition": { "code": 721, "main": "Haze", "description": "haze" }
  },
  "air": {
    "measuredAt": "2026-11-27T15:00:00+09:00",
    "station": { "name": "화랑로", "distanceKm": 1.1 },
    "pm10": { "value": 83, "grade": 3 },
    "pm25": { "value": 35, "grade": 2 },
    "o3": { "value": 0.044, "grade": 2 },
    "khai": { "value": 73, "grade": 2 }
  },
  "indices": {
    "outing": { "grade": 3, "label": "주의", "summary": "미세먼지가 나빠요. 밖에 오래 있지 마세요." },
    "mask": { "grade": 3, "label": "권장", "summary": "미세먼지가 나빠요. 보건용 마스크(KF80 이상)를 쓰세요." },
    "ventilation": { "grade": 3, "label": "짧게", "summary": "미세먼지가 나빠요. 요리한 뒤에만 짧게 환기하세요." },
    "laundry": { "grade": 3, "label": "실내 건조", "summary": "미세먼지가 나빠요. 실내에서 말리세요." }
  },
  "outfit": {
    "summary": "쌀쌀해요. 가벼운 재킷을 걸치세요.",
    "items": [
      { "category": "outer", "name": "가벼운 재킷" },
      { "category": "top", "name": "긴팔 티셔츠" },
      { "category": "bottom", "name": "청바지" },
      { "category": "accessory", "name": "보건용 마스크" }
    ],
    "tips": ["미세먼지가 나빠요. 보건용 마스크(KF80 이상)를 쓰세요."]
  },
  "hourly": [
    {
      "time": "2026-11-27T18:00:00+09:00",
      "temp": 14.85,
      "feelsLike": 14.09,
      "pop": 20,
      "precipitation": 0.14,
      "conditionCode": 500,
      "isDay": false
    }
  ],
  "warnings": [],
  "meta": {
    "fetchedAt": "2026-11-27T15:37:43+09:00",
    "cached": false,
    "sources": ["에어코리아", "OpenWeatherMap"]
  }
}
```

### `location`

좌표의 행정동입니다(Kakao 좌표 → 행정구역). `lat`, `lon`은 요청 값을 그대로 돌려줍니다. 지역명을 받지 못하면 `name`, `fullName`, `regionCode`가 `null`이고, 나머지 응답은 그대로 옵니다.

### `weather` (OpenWeather 현재 날씨와 예보)

| 필드 | 설명 |
| --- | --- |
| `observedAt` | 관측 시각 |
| `temp`, `feelsLike` | 기온, 체감온도 |
| `tempMin`, `tempMax` | **앞으로 24시간**의 최저, 최고 기온. 현재 기온과 `hourly` 8개 구간으로 계산합니다(#35) |
| `humidity`, `clouds` | 습도, 구름양 |
| `windSpeed` | 풍속 |
| `precipitation` | 최근 1시간 강수량(비와 눈 합산). 없으면 0 |
| `isDay` | 낮이면 `true`. 프론트가 아이콘을 고를 때 씁니다 |
| `condition.code` | OpenWeather 날씨 코드 |
| `condition.main`, `condition.description` | 날씨 분류와 설명(영문) |

### `air` (에어코리아 실시간 측정)

가까운 측정소부터 차례로 보고, 미세먼지나 초미세먼지 값이 있는 첫 측정소를 씁니다.

| 필드 | 설명 |
| --- | --- |
| `measuredAt` | 측정 시각. 1시간 단위라 날씨보다 늦을 수 있습니다 |
| `station` | 쓴 측정소 이름과 요청 좌표에서의 거리(km) |
| `pm10`, `pm25`, `o3` | 미세먼지, 초미세먼지, 오존의 측정값과 등급 |
| `khai` | 통합대기환경지수(CAI) |
| `grade` | 에어코리아 등급 그대로: 1 좋음, 2 보통, 3 나쁨, 4 매우나쁨 |

측정소 점검 등으로 항목 하나만 비면 그 항목의 `value`와 `grade`가 `null`입니다.

### `indices` (생활지수)

`outing`(외출), `mask`(마스크), `ventilation`(환기), `laundry`(빨래) 네 개이고 모양이 같습니다.

| 필드 | 설명 |
| --- | --- |
| `grade` | 1~4. 1이 가장 좋고 4가 가장 나쁩니다. 프론트는 이 값으로 카드 색을 정합니다 |
| `label` | 등급 이름. 지수마다 달라서 서버가 내려 주는 값을 그대로 표시합니다 |
| `summary` | 카드에 띄울 한 문장 |

계산에 필요한 값이 없으면 그 지수만 `null`입니다. 등급 기준과 등급 이름은 [life-indices.md](life-indices.md)에 있습니다.

### `outfit` (옷장 없는 규칙 기반 추천)

| 필드 | 설명 |
| --- | --- |
| `summary` | 한 줄 요약 |
| `items` | 추천 옷. `category`는 `outer`, `top`, `bottom`, `shoes`, `accessory` 중 하나 |
| `tips` | 일교차, 비, 바람, 미세먼지 같은 보조 안내 |

날씨를 받지 못하면 `null`입니다. 기준은 [outfit-rules.md](outfit-rules.md)에 있습니다.

### `hourly` (시간대별 예보)

OpenWeather 무료 예보가 3시간 간격이라, 앞으로 24시간을 3시간 간격 8개로 내려 줍니다. 날씨를 받지 못하면 `null`입니다.

| 필드 | 설명 |
| --- | --- |
| `time` | 구간 시작 시각 |
| `temp`, `feelsLike` | 기온, 체감온도 |
| `pop` | 강수 확률(%) |
| `precipitation` | 3시간 강수량(비와 눈 합산) |
| `conditionCode`, `isDay` | 날씨 코드, 낮 여부 |

미세먼지는 시간별 예보 수치가 없어 넣지 않습니다.

### `warnings` (부분 실패)

날씨와 대기질 중 **하나만** 실패하면 오류로 끝내지 않고, 받은 쪽만 채워 200으로 응답합니다. 실패한 쪽은 `null`이고, 그 값이 필요한 지수와 추천도 `null`이 됩니다.

```json
{
  "air": null,
  "indices": { "outing": { "...": "..." }, "mask": null, "ventilation": null, "laundry": { "...": "..." } },
  "warnings": [{ "source": "air", "message": "대기질 정보를 잠시 불러오지 못했어요." }]
}
```

| `source` | `message` |
| --- | --- |
| `weather` | 날씨 정보를 잠시 불러오지 못했어요. |
| `air` | 대기질 정보를 잠시 불러오지 못했어요. |
| `air` | 근처 측정소에 대기질 정보가 없어요. |

둘 다 실패하면 502 `upstream_error`입니다.

### `meta`

| 필드 | 설명 |
| --- | --- |
| `fetchedAt` | 이 응답을 만든 시각 |
| `cached` | 외부 API를 하나도 부르지 않고 DynamoDB 캐시만으로 만든 응답이면 `true` |
| `sources` | 데이터 출처. 이용 조건에 따라 화면 하단에 표시합니다 |

캐시 유지 시간(날씨 10분, 측정값 15분 등)은 [external-apis.md "캐시"](external-apis.md#캐시)에 있습니다.

### 오류

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | `lat`, `lon`이 없거나 숫자가 아님, 국내가 아닌 좌표 |
| 502 | `upstream_error` | 날씨와 대기질을 모두 받지 못함 |

---

## POST /api/wardrobe/recommend

브라우저에 저장한 옷장에서 오늘 입을 옷을 고릅니다. 옷장은 추천을 요청할 때만 본문으로 보내고, 서버는 저장하지 않으며 요청 본문을 로그에 남기지 않습니다.

```http
POST /api/wardrobe/recommend
Content-Type: application/json

{
  "lat": 37.62,
  "lon": 127.06,
  "wardrobe": [
    { "id": "a1", "category": "outer", "name": "경량 패딩", "thickness": "medium", "waterproof": false },
    { "id": "a2", "category": "top", "name": "회색 니트", "thickness": "medium", "waterproof": false },
    { "id": "a3", "category": "bottom", "name": "청바지", "thickness": "medium", "waterproof": false }
  ]
}
```

```json
{
  "summary": "쌀쌀해요. 가벼운 재킷을 걸치세요.",
  "items": [
    { "id": "a1", "category": "outer", "name": "경량 패딩" },
    { "id": "a2", "category": "top", "name": "회색 니트" },
    { "id": "a3", "category": "bottom", "name": "청바지" },
    { "category": "accessory", "name": "보건용 마스크" }
  ],
  "tips": ["미세먼지가 나빠요. 보건용 마스크(KF80 이상)를 쓰세요."]
}
```

| 필드 | 설명 |
| --- | --- |
| `lat`, `lon` | 국내 좌표 |
| `wardrobe` | 옷 목록, 200벌까지. 옷 하나는 `id`(1~64자), `category`, `name`(1~50자), `thickness`(`thin`, `medium`, `thick`), `waterproof`(true, false) |
| 응답 | `/api/conditions`의 `outfit`과 같은 모양이고, 옷장에서 고른 옷에만 `id`가 붙습니다. 맞는 옷이 없는 종류는 일반 추천의 옷이 `id` 없이 들어갑니다 |

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 본문이 JSON 객체가 아니거나 64KB를 넘음, 국내가 아닌 좌표, `wardrobe`가 목록이 아니거나 200벌을 넘음, 형식이 맞지 않는 옷이 있음 |
| 502 | `upstream_error` | 날씨를 받지 못해 추천할 수 없음 |

고르는 순서와 구간별 두께는 [outfit-rules.md "옷장 추천"](outfit-rules.md#옷장-추천)에 있습니다.

---

## POST /api/wardrobe/classify

옷장 등록 화면에서 옷 이름으로 종류, 두께, 방수 여부를 미리 채우기 위한 추정입니다. 틀릴 수 있어서 화면에서 사용자가 고칠 수 있습니다.

```http
POST /api/wardrobe/classify
Content-Type: application/json

{ "name": "고어텍스 등산화" }
```

```json
{ "category": "shoes", "thickness": "medium", "waterproof": true, "source": "llm" }
```

| 필드 | 설명 |
| --- | --- |
| `name` | 옷 이름. 앞뒤 공백을 뺀 1~50자 |
| `category` | `outer`, `top`, `bottom`, `shoes`, `accessory`. 옷이 아니거나 알 수 없으면 `null` |
| `thickness` | `thin`, `medium`, `thick`. 알 수 없으면 `medium` |
| `waterproof` | 방수 여부 |
| `source` | 추정 방법. Claude(Anthropic API)면 `llm`, 키워드 규칙이면 `rules`. 응답 모양은 같습니다 |

LLM이 꺼져 있거나, 호출이 실패하거나(5초 제한), 답이 정해진 모양이 아니면 키워드 규칙으로 답합니다. 그래서 외부 API 문제로 오류가 나지 않습니다.

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 본문이 JSON 객체가 아님, `name`이 비었거나 50자를 넘음 |

키워드 규칙과 LLM 설정은 [outfit-rules.md "옷 분류"](outfit-rules.md#옷-분류)에 있습니다.

---

## POST /api/chat

"오늘 뭐 입어?", "우산 챙겨야 해?" 같은 질문에 오늘의 날씨, 대기질, 생활지수, 옷차림을 바탕으로 짧게 답합니다. 대화 기록은 받지 않고 질문마다 따로 답합니다.

```http
POST /api/chat
Content-Type: application/json

{ "lat": 37.62, "lon": 127.06, "message": "오늘 뭐 입을까?" }
```

```json
{
  "answer": "오늘은 기온 16도에 체감 15도라 쌀쌀한 편이에요. 가벼운 재킷에 긴팔 티셔츠, 청바지 차림을 추천하고, 미세먼지가 나쁘니 KF80 이상 보건용 마스크도 꼭 챙기세요!",
  "source": "llm"
}
```

| 필드 | 설명 |
| --- | --- |
| `lat`, `lon` | 국내 좌표 |
| `message` | 질문. 앞뒤 공백을 뺀 1~200자 |
| `answer` | 답 문장 |
| `source` | 답을 만든 방법. Claude(Anthropic API)면 `llm`, 규칙 기반 요약이면 `rules` |

LLM이 꺼져 있거나 실패하면 오늘 옷차림 요약과 팁을 이어 붙인 규칙 기반 답을 줍니다.

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 본문이 JSON 객체가 아님, 국내가 아닌 좌표, `message`가 비었거나 200자를 넘음 |
| 502 | `upstream_error` | 날씨와 대기질을 모두 받지 못함 |

Anthropic API로 보내는 데이터와 비용 제한은 [chat.md](chat.md)에 있습니다.
