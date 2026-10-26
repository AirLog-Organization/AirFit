# AirFit

실시간 날씨와 미세먼지 데이터를 외출, 마스크, 환기, 빨래 지수와 옷차림 추천으로 바꿔 주는 웹 서비스입니다.

## 저장소 구조

| 폴더 | 내용 |
| --- | --- |
| `backend/` | AWS Lambda(Python 3.14) API와 SAM 템플릿 |
| `frontend/` | React, Vite, Tailwind CSS 웹 앱 |
| `docs/` | API 명세와 생활지수 기준 |

## 로컬 실행

백엔드:

```bash
cd backend
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/pytest
```

프론트엔드:

```bash
cd frontend
npm install
npm run dev
```
