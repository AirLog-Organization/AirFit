# 외부 API

백엔드(Lambda)가 호출하는 외부 API 목록입니다. 키는 모두 Lambda 환경 변수로만 관리하고 브라우저에서는 호출하지 않습니다.

예시는 2026-10-29에 "월계동"으로 실제 호출한 결과이고, 응답은 쓰는 필드 위주로 줄였습니다. 전체 응답은 `backend/tests/fixtures/`에 있습니다.

## 조회 흐름

```
지역 검색: 검색어 → ① Kakao 주소 검색 → 후보 선택 → 좌표
현재 위치: 브라우저 위도·경도 → ② Kakao 지역명 변환(표시용) → 좌표

좌표 ─┬─ ③ OpenWeather 현재 날씨, 예보
      └─ ④ Kakao 좌표 변환(TM) → ⑤ 에어코리아 근접 측정소 → ⑥ 에어코리아 실시간 측정값
```

## 캐시

배포 환경에서는 응답을 DynamoDB(`CacheTable`)에 저장해 같은 요청이 외부 API를 다시 부르지 않게 합니다. 실패한 호출은 저장하지 않고, DynamoDB에 문제가 있으면 캐시 없이 외부 API를 부릅니다. 로컬(`dev_server.py`)과 테스트는 `CACHE_TABLE`이 없어 캐시를 쓰지 않습니다.

| 대상 | 키 | 유지 시간 | 이유 |
| --- | --- | --- | --- |
| ① 주소 검색 | 검색어 | 7일 | 행정구역이 바뀔 때만 달라짐 |
| ② 지역명 | 좌표 소수 3자리(약 100m) | 30일 | 행정동 경계는 거의 바뀌지 않음 |
| ③ 현재 날씨, 예보 | 좌표 소수 2자리(약 1km) | 10분 | 원본을 저장하고 요약은 매번 해서 "오늘" 범위가 어긋나지 않게 함 |
| ④ + ⑤ 근접 측정소 | 좌표 소수 2자리 | 7일 | 측정소 위치는 거의 바뀌지 않음 |
| ⑥ 실시간 측정값 | 측정소 이름 | 15분 | 매시 갱신되고 15분쯤 늦게 올라옴. 근처 사용자끼리 공유 |

`/api/conditions` 응답의 `meta.cached`는 외부 API를 하나도 부르지 않고 캐시만으로 만든 응답일 때 `true`입니다.

## Kakao 로컬

- Base URL: `https://dapi.kakao.com`
- 인증 헤더: `Authorization: KakaoAK {KAKAO_REST_API_KEY}`
- 좌표는 `x`가 경도, `y`가 위도입니다.

### ① 주소 검색

`GET /v2/local/search/address.json`

| 파라미터 | 값 |
| --- | --- |
| `query` | 검색어 (예: `월계동`) |
| `analyze_type` | `similar` |
| `size` | `10` |

사용하는 응답 필드: `documents[].address_name`, `documents[].x`, `documents[].y` (`x`, `y`는 문자열)

결과 개수와 상관없이 후보 목록을 돌려주고, 사용자가 고른 좌표로 조회합니다.

```bash
curl -G "https://dapi.kakao.com/v2/local/search/address.json" \
  -H "Authorization: KakaoAK $KAKAO_REST_API_KEY" \
  --data-urlencode "query=월계동" \
  -d analyze_type=similar -d size=10
```

```json
{
  "documents": [
    {
      "address_name": "서울 노원구 월계동",
      "address_type": "REGION",
      "x": "127.062987742987",
      "y": "37.6199191869583"
    },
    { "address_name": "서울 노원구 월계1동", "x": "127.063001311172", "y": "37.6198903481106" },
    { "address_name": "서울 노원구 월계2동", "x": "127.050744895708", "y": "37.6324884457576" },
    { "address_name": "서울 노원구 월계3동", "x": "127.069259441758", "y": "37.6210148773623" },
    { "address_name": "전남광주통합특별시 광산구 월계동", "x": "126.836183980128", "y": "35.2130871081696" }
  ],
  "meta": { "is_end": true, "pageable_count": 5, "total_count": 5 }
}
```

전체 응답: `kakao_search_address.json`

### ② 좌표 → 지역명

`GET /v2/local/geo/coord2regioncode.json`

| 파라미터 | 값 |
| --- | --- |
| `x` | 경도 |
| `y` | 위도 |

사용하는 응답 필드: `region_type`이 `H`인 문서의 `address_name`

```bash
curl -G "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json" \
  -H "Authorization: KakaoAK $KAKAO_REST_API_KEY" \
  -d x=127.062987742987 -d y=37.6199191869583
```

```json
{
  "meta": { "total_count": 2 },
  "documents": [
    { "region_type": "B", "address_name": "서울특별시 노원구 월계동" },
    { "region_type": "H", "address_name": "서울특별시 노원구 월계1동" }
  ]
}
```

전체 응답: `kakao_coord2regioncode.json`

### ④ 좌표 → TM 좌표

`GET /v2/local/geo/transcoord.json`

| 파라미터 | 값 |
| --- | --- |
| `x` | 경도 |
| `y` | 위도 |
| `input_coord` | `WGS84` |
| `output_coord` | `TM` |

사용하는 응답 필드: `documents[0].x`, `documents[0].y` (⑤의 `tmX`, `tmY`)

```bash
curl -G "https://dapi.kakao.com/v2/local/geo/transcoord.json" \
  -H "Authorization: KakaoAK $KAKAO_REST_API_KEY" \
  -d x=127.062987742987 -d y=37.6199191869583 \
  -d input_coord=WGS84 -d output_coord=TM
```

```json
{
  "meta": { "total_count": 1 },
  "documents": [{ "x": 205491.31234154067, "y": 457510.25750212977 }]
}
```

## OpenWeather

- Base URL: `https://api.openweathermap.org`
- 공통 파라미터: `appid={OPENWEATHER_API_KEY}`, `units=metric`, `lang=en`
- 날씨 상태는 영어로 받고, 프론트엔드가 `weather[0].id`(condition code)로 한국어 문구와 아이콘을 매칭합니다. `lang=kr` 번역은 "실 비"처럼 어색해서 쓰지 않습니다.
- 응답의 `name`(도시명)은 호출마다 달라질 수 있어서 쓰지 않습니다. 지역명은 Kakao 결과를 씁니다.

### ③ 현재 날씨

`GET /data/2.5/weather?lat={위도}&lon={경도}`

사용하는 응답 필드: `main.temp`, `main.feels_like`, `main.humidity`, `wind.speed`, `weather[0].id`, `rain`

```bash
curl -G "https://api.openweathermap.org/data/2.5/weather" \
  -d lat=37.6199191869583 -d lon=127.062987742987 \
  -d units=metric -d lang=en -d appid=$OPENWEATHER_API_KEY
```

```json
{
  "weather": [{ "id": 500, "main": "Rain", "description": "light rain", "icon": "10d" }],
  "main": { "temp": 9.41, "feels_like": 7.59, "humidity": 53 },
  "wind": { "speed": 3.38 },
  "rain": { "1h": 0.75 },
  "dt": 1793238594,
  "cod": 200
}
```

비가 오지 않으면 `rain` 키 자체가 없습니다.

전체 응답: `openweather_current.json`

### ③ 예보 (5일, 3시간 간격)

`GET /data/2.5/forecast?lat={위도}&lon={경도}`

사용하는 응답 필드: `list[].dt`, `list[].main.temp`, `list[].weather[0].id`, `list[].pop`(강수 확률, 0~1)

```bash
curl -G "https://api.openweathermap.org/data/2.5/forecast" \
  -d lat=37.6199191869583 -d lon=127.062987742987 \
  -d units=metric -d lang=en -d appid=$OPENWEATHER_API_KEY
```

```json
{
  "cod": "200",
  "cnt": 40,
  "list": [
    {
      "dt": 1793242800,
      "main": { "temp": 10.44, "feels_like": 8.79 },
      "weather": [{ "id": 500, "main": "Rain", "description": "light rain" }],
      "pop": 0.2,
      "rain": { "3h": 0.29 },
      "dt_txt": "2026-10-29 03:00:00"
    }
  ]
}
```

`dt_txt`는 UTC입니다. 한국 시간은 `dt`에 9시간을 더해서 계산합니다.

전체 응답: `openweather_forecast.json`

## 에어코리아 (공공데이터포털)

- Base URL: `https://apis.data.go.kr/B552584`
- 공통 파라미터: `serviceKey={AIRKOREA_SERVICE_KEY}`, `returnType=json`
- 측정값과 등급은 숫자가 아니라 문자열로 옵니다.

### ⑤ 근접 측정소 목록

`GET /MsrstnInfoInqireSvc/getNearbyMsrstnList`

| 파라미터 | 값 |
| --- | --- |
| `tmX` | ④의 `x` |
| `tmY` | ④의 `y` |
| `ver` | `1.1` |

사용하는 응답 필드: `response.body.items[0].stationName` (거리순 정렬, `tm`은 km)

```bash
curl -G "https://apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getNearbyMsrstnList" \
  --data-urlencode "serviceKey=$AIRKOREA_SERVICE_KEY" \
  -d returnType=json -d tmX=205491.31234154067 -d tmY=457510.25750212977 -d ver=1.1
```

```json
{
  "response": {
    "body": {
      "totalCount": 3,
      "items": [
        { "stationName": "화랑로", "tm": 1.1, "addr": "서울 노원구 화랑로 429 태능입구역 8번 출구" },
        { "stationName": "성북구", "tm": 3.5, "addr": "서울 성북구 삼양로2길 70 길음2동 주민센터" },
        { "stationName": "정릉로", "tm": 3.8, "addr": "서울 성북구 돈암동 8-164번지 " }
      ]
    },
    "header": { "resultMsg": "NORMAL_CODE", "resultCode": "00" }
  }
}
```

전체 응답: `airkorea_nearby_station.json`

### ⑥ 측정소별 실시간 측정값

`GET /ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty`

| 파라미터 | 값 |
| --- | --- |
| `stationName` | ⑤의 `stationName` |
| `dataTerm` | `DAILY` |
| `numOfRows` | `1` |
| `pageNo` | `1` |
| `ver` | `1.3` |

사용하는 응답 필드: `response.body.items[0]`의 `dataTime`, `pm10Value`, `pm25Value`, `pm10Grade`, `pm25Grade`

```bash
curl -G "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty" \
  --data-urlencode "serviceKey=$AIRKOREA_SERVICE_KEY" \
  --data-urlencode "stationName=화랑로" \
  -d returnType=json -d dataTerm=DAILY -d numOfRows=1 -d pageNo=1 -d ver=1.3
```

```json
{
  "response": {
    "body": {
      "totalCount": 23,
      "items": [
        {
          "dataTime": "2026-10-29 10:00",
          "pm10Value": "43",
          "pm25Value": "15",
          "pm10Grade": "2",
          "pm25Grade": "1"
        }
      ]
    },
    "header": { "resultMsg": "NORMAL_CODE", "resultCode": "00" }
  }
}
```

등급은 `1` 좋음, `2` 보통, `3` 나쁨, `4` 매우나쁨입니다.

전체 응답: `airkorea_realtime_measure.json`

## 환경 변수

| 이름 | 용도 |
| --- | --- |
| `KAKAO_REST_API_KEY` | Kakao 로컬 (REST API 키) |
| `OPENWEATHER_API_KEY` | OpenWeather |
| `AIRKOREA_SERVICE_KEY` | 에어코리아 (공공데이터포털 일반 인증키, Decoding 값) |
