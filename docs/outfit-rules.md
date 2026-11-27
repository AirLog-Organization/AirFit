# 옷차림 추천 기준

`/api/conditions`의 `outfit`을 만드는 규칙입니다. 기준값은 [`backend/src/airfit/rules/outfit.json`](../backend/src/airfit/rules/outfit.json)에 있고, 코드([`outfit.py`](../backend/src/airfit/outfit.py))는 그 값을 날씨와 대기질에 적용만 합니다. 기준을 바꿀 때는 코드 대신 JSON과 이 문서를 고칩니다.

이 기준은 기상청 같은 기관의 공식 기준이 아닙니다. 널리 쓰이는 기온별 옷차림 표를 참고해 팀이 정한 값입니다. 다르게 느끼는 구간이 있으면 이슈로 알려 주세요.

## 순서

1. 체감온도로 기본 옷차림 구간을 하나 고릅니다. 체감온도가 없으면 기온을 씁니다. 둘 다 없거나 날씨 조회에 실패하면 `outfit`은 `null`입니다.
2. 아래 팁 조건을 위에서부터 확인해, 맞는 팁을 `tips`에 넣고 팁에 딸린 소품을 `items` 뒤에 붙입니다.
3. 조건에 필요한 값이 없으면(예: 대기질 조회 실패) 그 팁만 건너뜁니다.

## 기본 옷차림 (체감온도)

바람과 습도에 따라 같은 기온도 다르게 느껴지므로 기온 대신 체감온도를 씁니다. 구간은 "이상"입니다. 예를 들어 체감온도 28도는 첫 구간, 27.9도는 두 번째 구간입니다.

| 체감온도 | 요약 | 겉옷 | 상의 | 하의 | 신발, 소품 |
| --- | --- | --- | --- | --- | --- |
| 28도 이상 | 아주 더워요 | | 반팔 티셔츠 | 반바지 | 샌들 |
| 23 ~ 27도 | 더워요 | | 반팔 티셔츠 | 면바지 | 운동화 |
| 20 ~ 22도 | 선선해요 | 얇은 가디건 | 긴팔 티셔츠 | 면바지 | |
| 17 ~ 19도 | 조금 쌀쌀해요 | | 맨투맨 | 청바지 | |
| 12 ~ 16도 | 쌀쌀해요 | 가벼운 재킷 | 긴팔 티셔츠 | 청바지 | |
| 9 ~ 11도 | 추워지기 시작해요 | 트렌치코트 | 니트 | 청바지 | |
| 5 ~ 8도 | 추워요 | 코트 | 니트, 내복 | 두꺼운 바지 | |
| 5도 미만 | 매우 추워요 | 패딩 | 두꺼운 니트 | 기모 바지 | 목도리 |

## 팁

| 조건 | 값 | 기준 | 팁 | 붙는 소품 |
| --- | --- | --- | --- | --- |
| 일교차 | 앞으로 24시간 기온 폭(`tempMax - tempMin`, 현재 기온과 3시간 간격 예보 8개) | 10도 이상 | 벗기 쉬운 겉옷을 챙기세요 | |
| 비, 눈 | 앞으로 12시간 예보의 최대 강수 확률. 지금 비나 눈이 오면 100 | 60% 이상 | 우산을 챙기세요 | 우산 |
| 미세먼지 | 미세먼지(PM10)와 초미세먼지(PM2.5) 등급 중 나쁜 쪽 | 3(나쁨) 이상 | 보건용 마스크(KF80 이상)를 쓰세요 | 보건용 마스크 |
| 바람 | 현재 풍속과 체감온도 | 7m/s 이상이고 체감온도 20도 미만 | 바람을 막는 겉옷을 입으세요 | |

- 등급은 에어코리아가 준 값을 그대로 씁니다(1 좋음, 2 보통, 3 나쁨, 4 매우나쁨).
- 비는 외출하는 동안 필요한지가 중요해서 하루 전체가 아니라 앞으로 12시간(3시간 간격 예보 4개)만 봅니다.
- 바람 팁은 "춥게 느껴질 수 있다"는 내용이라, 더운 날에 붙지 않도록 체감온도가 20도(선선한 구간) 미만일 때만 보여 줍니다.
- 일교차, 강수 확률, 풍속, 체감온도 기준값은 팀이 정한 값입니다.

## 옷장 추천

사용자가 브라우저에 등록한 옷장에서 오늘 입을 옷을 고릅니다. 코드는 `outfit.recommend_from_wardrobe`이고, 옷장 추천 API(`POST /api/wardrobe/recommend`)로 호출합니다. 옷장은 추천을 요청할 때만 본문으로 보내고, 서버는 저장하지 않으며 요청 본문을 로그에 남기지 않습니다.

옷 하나는 아래 값을 가집니다.

| 필드 | 설명 | 제한 |
| --- | --- | --- |
| `id` | 옷장 항목 id. 추천 결과에 그대로 붙어 화면이 어떤 옷인지 알 수 있습니다 | 문자열, 1~64자 |
| `category` | `outer`, `top`, `bottom`, `shoes`, `accessory` 중 하나 | |
| `name` | 사용자가 붙인 이름 | 앞뒤 공백을 뺀 1~50자 |
| `thickness` | `thin`, `medium`, `thick` 중 하나 | |
| `waterproof` | 방수 여부 | `true` 또는 `false` |

### 추천 API

```http
POST /api/wardrobe/recommend
Content-Type: application/json

{
  "lat": 37.6199,
  "lon": 127.063,
  "wardrobe": [
    { "id": "w1", "category": "outer", "name": "바람막이", "thickness": "thin", "waterproof": true },
    { "id": "w2", "category": "top", "name": "회색 니트", "thickness": "medium", "waterproof": false }
  ]
}
```

응답은 `/api/conditions`의 `outfit`과 같은 모양이고, 옷장에서 고른 옷에만 `id`가 붙습니다.

```json
{
  "summary": "쌀쌀해요. 가벼운 재킷을 걸치세요.",
  "items": [
    { "id": "w1", "category": "outer", "name": "바람막이" },
    { "id": "w2", "category": "top", "name": "회색 니트" },
    { "category": "bottom", "name": "청바지" }
  ],
  "tips": []
}
```

| 상태 | `error` | 언제 |
| --- | --- | --- |
| 400 | `invalid_params` | 본문이 JSON 객체가 아니거나 64KB를 넘음, 국내가 아닌 좌표, `wardrobe`가 목록이 아니거나 200벌을 넘음, 형식이 맞지 않는 옷이 하나라도 있음 |
| 502 | `upstream_error` | 날씨를 받지 못해 추천할 수 없음 |

좌표 범위와 오류 응답 모양(`{ "error", "message" }`)은 `/api/conditions`와 같습니다. 날씨와 대기질은 `/api/conditions`와 같은 캐시를 씁니다.

### 고르는 순서

1. 기본 옷차림과 같은 체감온도 구간을 고릅니다. 요약 문구와 팁은 기본 옷차림과 같습니다.
2. 겉옷, 상의, 하의는 구간의 맞는 두께(`wear`)를 앞에서부터 확인해 처음 맞는 옷을 고릅니다. 두께가 같으면 먼저 등록한 옷입니다.
3. 맞는 옷이 없는 종류는 기본 옷차림의 옷을 `id` 없이 넣습니다. 화면에서 "옷장에 없는 옷"으로 구분할 수 있습니다.
4. 신발과 소품, 팁에 딸린 소품(우산, 마스크)은 기본 옷차림을 그대로 씁니다.
5. 비 소식이 있으면(앞으로 12시간 강수 확률 60% 이상, 또는 지금 비나 눈) 같은 두께 안에서 방수 겉옷을 먼저 고르고, 옷장에 방수 신발이 있으면 기본 신발 대신 넣습니다. 두께 순서보다 방수를 앞세우지는 않습니다.

API는 형식이 맞지 않는 옷이 있으면 400으로 거절합니다. 함수(`recommend_from_wardrobe`)만 직접 부를 때는 종류나 두께가 빠진 옷을 고르지 않고 넘어가며, 날씨가 없으면 `None`을 돌려줍니다.

### 구간별 맞는 두께

앞에 적은 두께를 먼저 고릅니다. 비어 있는 칸은 그 종류를 추천하지 않는다는 뜻입니다.

| 체감온도 | 겉옷 | 상의 | 하의 |
| --- | --- | --- | --- |
| 28도 이상 | | thin | thin |
| 23 ~ 27도 | | thin | thin, medium |
| 20 ~ 22도 | thin | thin | medium, thin |
| 17 ~ 19도 | | medium | medium |
| 12 ~ 16도 | thin, medium | thin, medium | medium |
| 9 ~ 11도 | medium | medium | medium |
| 5 ~ 8도 | medium, thick | medium, thick | thick, medium |
| 5도 미만 | thick | thick, medium | thick |

기본 옷차림 표에 맞춰 팀이 정한 값입니다.

## 옷 분류

옷장 등록 화면에서 옷 이름을 적으면 종류, 두께, 방수 여부를 미리 채워 주기 위한 추정입니다. 이름만 보고 추정하므로 틀릴 수 있어서, 화면에서 사용자가 고칠 수 있어야 합니다.

두 가지 방법을 차례로 씁니다.

1. **LLM 분류** (`llm_classify.py`): Anthropic API의 Claude Haiku 5.5(`claude-haiku-5-5`)에 옷 이름만 보내고, 정해진 JSON 모양(종류, 두께, 방수 여부)으로만 답하게 합니다. 배포 설정 `LlmClassify`가 `enabled`이고 API 키가 있을 때만 씁니다.
2. **키워드 규칙** (`classify.py`, [`wardrobe_classify.json`](../backend/src/airfit/rules/wardrobe_classify.json)): LLM이 꺼져 있거나, 호출이 실패하거나(5초 제한), 답이 정해진 모양이 아니거나, 모델이 답을 거절하면 씁니다.

### 키워드 규칙

이름의 공백을 지우고(예: "롱 패딩" → "롱패딩") 키워드가 들어 있는지 봅니다.

| 값 | 방법 | 예 |
| --- | --- | --- |
| `category` | 종류별 키워드 중 **가장 긴 키워드**가 맞은 종류. 길이가 같으면 규칙 파일에 먼저 적은 종류(겉옷, 상의, 하의, 신발, 소품 순). 맞는 키워드가 없으면 `null` | "레인부츠"는 "레인"보다 긴 "레인부츠"가 맞아 신발, "후드집업"은 "후드"(상의)와 "집업"(겉옷)이 같은 길이라 겉옷 |
| `thickness` | 두꺼움(`thick`), 얇음(`thin`) 키워드 중 더 긴 쪽. 길이가 같으면 두꺼움. 둘 다 없으면 `medium` | "기모 바지"는 thick, "반팔 티셔츠"는 thin, "회색 니트"는 medium |
| `waterproof` | 방수 키워드("방수", "레인", "장화", "우비", "고어텍스")가 하나라도 있으면 `true` | "방수 바람막이", "레인부츠" |

키워드 목록은 팀이 자주 쓰는 옷 이름으로 정했습니다. 빠진 이름이 있으면 규칙 파일에 추가해 주세요.

### 분류 API

```http
POST /api/wardrobe/classify
Content-Type: application/json

{ "name": "롱패딩" }
```

```json
{ "category": "outer", "thickness": "thick", "waterproof": false, "source": "rules" }
```

- `name`은 앞뒤 공백을 뺀 1~50자 문자열입니다. 아니면 400 `invalid_params`입니다.
- `source`는 추정 방법입니다. LLM 분류면 `llm`, 키워드 규칙이면 `rules`입니다. 응답 모양은 같습니다.
- LLM이 꺼져 있으면 외부 서비스를 부르지 않습니다. 켜져 있으면 옷 이름만 Anthropic API로 보냅니다. 어느 쪽이든 옷 이름은 로그에 남기지 않습니다.

### LLM 분류 켜기

1. 저장소의 GitHub Secrets에 `ANTHROPIC_API_KEY`를 넣습니다. Deploy workflow가 배포 파라미터 `AnthropicApiKey`로 넘기고, Lambda 환경 변수가 됩니다.
2. `.github/workflows/deploy.yml` Deploy 단계의 `--parameter-overrides`에 `"LlmClassify=enabled"`가 있는지 확인합니다. 없으면 기본값 `disabled`로 배포됩니다.
3. 다른 모델을 쓰려면 Lambda 환경 변수 `CLAUDE_MODEL`을 바꿉니다.

배포 후 `/api/wardrobe/classify` 응답의 `source`가 `llm`이면 켜진 것입니다. 계속 `rules`가 나오면 키가 들어갔는지 확인해 주세요. 배포의 Smoke test가 옷 분류와 챗봇을 한 번씩 불러서, 500이 나거나 15초를 넘기면 배포를 실패로 표시합니다.

## 규칙 파일 구조

```json
{
  "bands": [
    { "min": 28, "summary": "...", "items": [{ "category": "top", "name": "반팔 티셔츠" }], "wear": { "top": ["thin"], "bottom": ["thin"] } },
    { "min": null, "summary": "...", "items": [], "wear": { "outer": ["thick"], "top": ["thick", "medium"], "bottom": ["thick"] } }
  ],
  "tips": [
    { "when": [{ "metric": "rainChance", "gte": 60 }], "text": "...", "items": [{ "category": "accessory", "name": "우산" }] },
    { "when": [{ "metric": "windSpeed", "gte": 7 }, { "metric": "feelsLike", "lt": 20 }], "text": "..." }
  ],
  "waterproof": { "when": [{ "metric": "rainChance", "gte": 60 }], "categories": ["outer", "shoes"] }
}
```

| 필드 | 설명 |
| --- | --- |
| `bands` | 높은 온도부터 적습니다. `min` 이상이면 그 구간이고, 마지막 구간은 `min: null`로 나머지를 모두 받습니다 |
| `items[].category` | `outer`, `top`, `bottom`, `shoes`, `accessory` 중 하나. 3단계 옷장 등록에서도 같은 값을 씁니다 |
| `tips[].when` | 조건 목록. 모두 맞아야 팁을 보여 줍니다 |
| `tips[].when[].metric` | `feelsLike`(체감온도), `humidity`(습도), `precipitation`(최근 1시간 강수량), `dailyRange`(일교차), `rainChance`(강수 확률), `dustGrade`(미세먼지 등급), `windSpeed`(풍속) 중 하나. 자세한 뜻은 [`life-indices.md`](life-indices.md)의 "규칙 파일 구조" |
| `tips[].when[].gte`, `lt` | 둘 중 하나. `gte`는 이 값 이상, `lt`는 이 값 미만일 때 맞습니다 |
| `tips[].items` | 선택. 팁과 함께 추천할 소품 |
| `bands[].wear` | 옷장 추천에서 구간별로 맞는 두께. 키는 `outer`, `top`, `bottom`(상의와 하의는 필수), 값은 `thin`, `medium`, `thick`을 선호 순서대로 적은 목록 |
| `waterproof.when` | 이 조건이 모두 맞으면 비 소식이 있다고 보고 방수 옷을 앞세웁니다. 형식은 `tips[].when`과 같습니다 |
| `waterproof.categories` | 방수를 앞세울 종류. `outer`, `shoes` 중에서 고릅니다 |

`backend/tests/test_outfit.py`와 `test_wardrobe.py`가 구간 순서, `category` 값, 두께 값, `metric` 이름, 비교 연산자를 검사하므로, 규칙을 고친 뒤 `pytest`로 확인해 주세요. 기여 절차는 [CONTRIBUTING.md](../CONTRIBUTING.md)의 "규칙(JSON) 기여"를 따릅니다.
