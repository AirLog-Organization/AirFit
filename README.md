# AirFit

실시간 날씨와 미세먼지 데이터를 외출, 마스크, 환기, 빨래 지수와 옷차림 추천으로 바꿔 주는 웹 서비스입니다. 설치나 회원가입 없이, 수치를 해석하지 않아도 오늘 필요한 판단을 바로 보여 주는 것이 목표입니다.

서비스 주소: <https://d1bdayuw5d2l10.cloudfront.net>

## 주요 기능

| 기능 | 내용 | 단계 |
| --- | --- | --- |
| 위치, 지역 검색 조회 | 현재 위치나 시·군·구 검색으로 날씨와 미세먼지 조회 | 1단계 |
| 생활지수 카드 | 외출, 마스크, 환기, 빨래 지수 | 1단계 |
| 옷차림 추천 | 기온, 체감온도, 강수, 미세먼지 기반 규칙(JSON) 추천 | 2단계 |
| 시간대별 그래프, 다크 모드 | | 2단계 |
| 옷장 등록과 코디 추천 | 옷장은 브라우저에만 저장하고 서버에 저장하지 않음 | 3단계 |
| 옷 자동 분류 | 옷 이름으로 종류, 두께, 방수 여부를 추정해 등록 화면에 미리 채움 (Claude, 실패 시 키워드 규칙) | 도전 |
| 챗봇 | 오늘 날씨와 옷차림 질문에 짧게 답함 (Claude, 실패 시 규칙 기반 요약) | 도전 |

API는 [docs/api.md](docs/api.md), 버전별 변경 기록은 [CHANGELOG.md](CHANGELOG.md)에 있습니다.

## 구조

브라우저는 AirFit API만 호출하고, 외부 API 호출과 지수 계산은 AWS Lambda가 맡습니다. 외부 API 키는 브라우저에 노출되지 않습니다.

| 폴더 | 내용 |
| --- | --- |
| `backend/` | AWS Lambda(Python 3.14) API와 SAM 템플릿 |
| `frontend/` | React, Vite, Tailwind CSS 웹 앱 |
| `docs/` | API 명세, 생활지수와 옷차림 기준, 외부 API, 챗봇 ([목록](docs/README.md)) |
| `infra/` | GitHub Actions 배포용 IAM(OIDC) 템플릿 |
| `licenses/` | 서드파티 라이선스 원문 |

## 로컬 실행

필요한 도구: Python 3.14, Node.js 24

### 백엔드

macOS, Linux:

```bash
cd backend
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
```

Windows (PowerShell):

```powershell
cd backend
py -3.14 -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
.venv\Scripts\pytest
```

### 프론트엔드

```bash
cd frontend
npm ci
npm run dev
```

## 배포

- PR마다 GitHub Actions가 `backend`, `frontend` CI를 실행합니다. 두 체크가 통과하고 리뷰 승인 1명을 받아야 `main`에 병합할 수 있습니다.
- `backend/` 코드가 바뀐 PR이 `main`에 병합되면 Deploy workflow가 AWS SAM으로 백엔드(API Gateway HTTP API + Lambda)를 배포합니다. AWS 인증은 장기 키 대신 OIDC를 사용합니다.
- `frontend/` 코드가 바뀐 PR이 `main`에 병합되면 Deploy Frontend workflow가 빌드 결과를 S3에 올리고 CloudFront 캐시를 비웁니다. 화면과 API는 CloudFront 주소(<https://d1bdayuw5d2l10.cloudfront.net>) 하나로 제공되고, `/api/*` 요청은 API Gateway로 전달됩니다.

## 데이터 출처와 이용 조건

AirFit은 아래 외부 서비스를 API로 호출만 하며, 해당 서비스의 코드는 포함하지 않습니다.

### 에어코리아 (한국환경공단, 공공데이터포털)

| 항목 | 내용 |
| --- | --- |
| 사용 API | 한국환경공단_에어코리아_대기오염정보, 한국환경공단_에어코리아_측정소정보 |
| 이용허락범위 | 공공누리 제3유형 (출처표시, 변경금지) |
| 호출 제한 | 개발계정 API별 일일 500건. 활용사례를 등록하면 운영계정으로 늘릴 수 있음 |
| 출처 표기 | 화면 하단에 "출처: 한국환경공단 에어코리아"를 표시 |

측정값은 바꾸지 않고 그대로 표시하며, 호출 수를 줄이려고 백엔드에서 실시간 측정값을 15분, 측정소 목록을 7일 캐싱합니다. 캐시 기준은 [docs/external-apis.md](docs/external-apis.md)에 정리되어 있습니다.

### OpenWeather

| 항목 | 내용 |
| --- | --- |
| 요금제 | Free |
| 호출 제한 | 분당 60회, 월 1,000,000회 |
| 출처 표기 | Free 요금제는 출처 표기가 필수입니다. 화면 하단에 "Weather data provided by OpenWeather"와 [openweathermap.org](https://openweathermap.org/) 링크를 표시 |

### Kakao 로컬 API (Kakao Developers)

지역 검색과 지역 이름 표시, 에어코리아 측정소 조회용 좌표 변환에 씁니다.

| 항목 | 내용 |
| --- | --- |
| 사용 API | 주소로 좌표 변환(`search/address`), 좌표로 행정구역정보 변환(`geo/coord2regioncode`), 좌표계 변환(`geo/transcoord`). 카카오맵 REST API 정책을 따름 |
| 호출 제한 | 무료 쿼터는 API별 일일 100,000건, 전체 API 월 3,000,000건. 개발자 계정에서 처음 활성화한 앱에만 제공됨 |
| 초과 시 | 429 에러. 유료 API를 설정하면 건당 0.5원으로 추가 호출 가능 (AirFit은 무료 쿼터만 사용) |
| 출처 표기 | 확인한 공식 문서(쿼터, 카카오맵 이해하기, 운영 정책, 서비스 약관)에서 별도 출처 표기 요구를 찾지 못함 |
| 상표 | 카카오 상표는 서비스 특성을 설명하는 문구에만 쓸 수 있고, 쓸 때는 첨자 ®을 붙여야 합니다(운영 정책 제18조). 서비스 이름이나 로고, 아이콘에는 쓸 수 없습니다. AirFit은 Kakao와 제휴하거나 Kakao가 제공하는 서비스가 아닙니다 |
| 캐시 | 사용자 경험 개선 목적으로만 허용되고, 캐시한 데이터는 최신으로 유지해야 합니다. AirFit은 검색 결과를 7일, 지역 이름을 30일 캐싱합니다 |

### Claude (Anthropic API)

옷장 등록 화면의 옷 분류와 챗봇에 씁니다. 데이터 출처가 아니라 AI 기능입니다. 처음에는 Amazon Bedrock으로 붙였지만, 팀 AWS 계정에서 Claude Haiku 5.5 호출이 허가되지 않아 Anthropic API를 직접 호출합니다.

| 항목 | 내용 |
| --- | --- |
| 모델 | Claude Haiku 5.5 (`claude-haiku-5-5`), Anthropic API(`api.anthropic.com`) |
| 보내는 데이터 | 옷 분류: 사용자가 적은 옷 이름 하나. 챗봇: 질문과 오늘 정보 요약(지역 이름, 날씨, 대기질, 생활지수, 옷차림). 좌표와 옷장 목록은 보내지 않음 |
| 켜고 끄기 | 배포 설정 `LlmClassify`(옷 분류), `LlmChat`(챗봇)과 API 키(GitHub Secrets `ANTHROPIC_API_KEY`). 꺼져 있거나 키가 없거나 호출이 실패하면 키워드 규칙이나 규칙 기반 요약으로 답함 |
| 요금 | Anthropic API 요금표를 따름. Claude Haiku 5.5는 입력 100만 토큰당 $0.10, 출력 $0.50(프롬프트 10만 토큰 이하, 2026-11 기준) |

자세한 동작은 [docs/outfit-rules.md](docs/outfit-rules.md)의 "옷 분류"와 [docs/chat.md](docs/chat.md)에 있습니다.

이용 조건은 바뀔 수 있으니 [공공데이터포털](https://www.data.go.kr/), [OpenWeather](https://openweathermap.org/price), [Kakao Developers 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)와 [운영 정책](https://developers.kakao.com/terms/ko/site-policies), [Anthropic API 요금](https://platform.claude.com/docs/en/about-claude/pricing)에서 최신 내용을 확인해 주세요.

## 기여

버그 신고, 기능 제안, 규칙 보정 모두 환영합니다. 브랜치, 커밋, PR 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 확인해 주세요.

## 라이선스

[MIT License](LICENSE)로 배포됩니다. 사용한 오픈소스와 라이선스 고지는 [NOTICE](NOTICE)에 정리되어 있습니다.
