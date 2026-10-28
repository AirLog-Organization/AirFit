# AirFit

실시간 날씨와 미세먼지 데이터를 외출, 마스크, 환기, 빨래 지수와 옷차림 추천으로 바꿔 주는 웹 서비스입니다. 설치나 회원가입 없이, 수치를 해석하지 않아도 오늘 필요한 판단을 바로 보여 주는 것이 목표입니다.

## 주요 기능

| 기능 | 내용 | 단계 |
| --- | --- | --- |
| 위치, 지역 검색 조회 | 현재 위치나 시·군·구 검색으로 날씨와 미세먼지 조회 | 1단계 |
| 생활지수 카드 | 외출, 마스크, 환기, 빨래 지수 | 1단계 |
| 옷차림 추천 | 기온, 체감온도, 강수, 미세먼지 기반 규칙(JSON) 추천 | 2단계 |
| 시간대별 그래프, 다크 모드 | | 2단계 |
| 옷장 등록과 코디 추천 | 옷장은 브라우저에만 저장하고 서버에 저장하지 않음 | 3단계 |

## 구조

브라우저는 AirFit API만 호출하고, 외부 API 호출과 지수 계산은 AWS Lambda가 맡습니다. 외부 API 키는 브라우저에 노출되지 않습니다.

| 폴더 | 내용 |
| --- | --- |
| `backend/` | AWS Lambda(Python 3.14) API와 SAM 템플릿 |
| `frontend/` | React, Vite, Tailwind CSS 웹 앱 |
| `docs/` | API 명세와 생활지수 기준 |
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
- 프론트엔드(S3, CloudFront) 배포는 준비 중입니다.

## 데이터 출처와 이용 조건

AirFit은 아래 외부 서비스를 API로 호출만 하며, 해당 서비스의 코드는 포함하지 않습니다.

### 에어코리아 (한국환경공단, 공공데이터포털)

| 항목 | 내용 |
| --- | --- |
| 사용 API | 한국환경공단_에어코리아_대기오염정보, 한국환경공단_에어코리아_측정소정보 |
| 이용허락범위 | 공공누리 제3유형 (출처표시, 변경금지) |
| 호출 제한 | 개발계정 API별 일일 500건. 활용사례를 등록하면 운영계정으로 늘릴 수 있음 |
| 출처 표기 | 화면에 "출처: 한국환경공단 에어코리아"를 표시할 예정 |

측정값은 바꾸지 않고 그대로 표시하며, 백엔드에서 약 10분간 캐싱해 호출 수를 줄입니다.

### OpenWeather

| 항목 | 내용 |
| --- | --- |
| 요금제 | Free |
| 호출 제한 | 분당 60회, 월 1,000,000회 |
| 출처 표기 | Free 요금제는 출처 표기가 필수입니다. 화면에 "Weather data provided by OpenWeather"와 [openweathermap.org](https://openweathermap.org/) 링크를 표시할 예정 |

이용 조건은 바뀔 수 있으니 [공공데이터포털](https://www.data.go.kr/)과 [OpenWeather](https://openweathermap.org/price)에서 최신 내용을 확인해 주세요.

## 기여

버그 신고, 기능 제안, 규칙 보정 모두 환영합니다. 브랜치, 커밋, PR 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 확인해 주세요.

## 라이선스

[MIT License](LICENSE)로 배포됩니다. 사용한 오픈소스와 라이선스 고지는 [NOTICE](NOTICE)에 정리되어 있습니다.
