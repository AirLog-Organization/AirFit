# AirFit 기여 가이드

AirFit에 관심을 가져 주셔서 감사합니다. 버그 신고, 기능 제안, 옷차림 규칙 보정, 문서 수정 모두 환영합니다.

## 기여 방법

1. [이슈](https://github.com/AirLog-Organization/AirFit/issues)를 먼저 검색하고, 없으면 템플릿(버그 신고, 기능 제안)으로 새 이슈를 만듭니다.
2. 처음이라면 `good first issue` 라벨이 붙은 이슈부터 시작해 보세요.
3. 작업할 이슈에 댓글을 남겨 담당자를 정한 뒤 시작합니다.

## 개발 환경

| 영역 | 필요한 도구 |
| --- | --- |
| backend | Python 3.14, (배포 확인 시) AWS SAM CLI |
| frontend | Node.js 24 (`frontend/.nvmrc`) |

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
npm run dev     # 개발 서버
npm run lint
npm test
npm run build
```

## 브랜치 전략

GitHub Flow를 따릅니다.

- `main`은 항상 배포 가능한 상태로 유지합니다. 직접 push할 수 없습니다.
- 작업은 `main`에서 `feature/기능명` 브랜치를 만들어 진행합니다. 예: `feature/region-search`, `feature/outfit-rules`
- 작업이 끝나면 PR을 올려 `main`에 병합합니다.

## 커밋 메시지

접두어를 붙이고, 무엇을 바꿨는지 한 줄로 적습니다.

| 접두어 | 용도 |
| --- | --- |
| `feat:` | 새 기능 |
| `fix:` | 버그나 잘못된 동작 수정 |
| `docs:` | 문서만 변경 |
| `test:` | 테스트 추가, 수정 |
| `refactor:` | 동작은 그대로 두고 구조만 변경 |
| `chore:` | 빌드, 설정, 의존성, CI 등 |

예: `feat: add laundry index calculation`, `fix: handle missing PM10 value`

- 기능 하나는 커밋 하나로 남깁니다.
- 이미 올린 커밋을 고칠 때는 amend나 force push 대신 `fix:` 같은 새 커밋을 만듭니다.

## Pull Request

1. PR 템플릿의 항목(개요, 변경 내용, 확인 방법, 체크리스트)을 채웁니다.
2. 관련 이슈가 있으면 본문에 `Closes #번호`를 적습니다.
3. 아래 조건을 모두 만족해야 병합할 수 있습니다.
   - CI 필수 체크 `backend`, `frontend` 통과
   - 리뷰 승인 1명 이상
4. 병합은 Create a merge commit으로 합니다. 기능별 커밋이 `main` 이력에 그대로 남으므로, PR 안의 커밋 메시지도 모두 접두어 규칙을 따라야 합니다.

### CI에서 확인하는 것

| 체크 | 내용 |
| --- | --- |
| `backend` | `ruff check`, `ruff format --check`, `pytest`(커버리지 70% 이상), `sam validate --lint` |
| `frontend` | `npm run lint`, `npm test`, `npm run build` |

`main`에 병합되면 Deploy workflow가 백엔드를 AWS에 자동 배포합니다.

### 팀 내 교차 리뷰

팀원 PR은 아래 순서로 리뷰합니다. 외부 기여자의 PR은 메인테이너가 리뷰를 배정합니다.

| PR 작성자 | 리뷰어 |
| --- | --- |
| 백엔드 (@hynjjn) | 프론트엔드 (@hwi-cafe) |
| 프론트엔드 (@hwi-cafe) | 규칙, 품질, 문서 (@KxxgHx) |
| 규칙, 품질, 문서 (@KxxgHx) | 백엔드 (@hynjjn) |

AI 도구로 코드를 만들었더라도, 작성자는 PR의 모든 코드를 설명할 수 있어야 합니다.

## 규칙(JSON) 기여

생활지수 기준과 옷차림 규칙은 코드와 분리된 JSON 파일과 `docs/` 문서로 관리합니다. 규칙을 바꾸는 PR에는 아래를 함께 담아 주세요.

- 바꾼 기준과 근거 자료 (예: 에어코리아 통합대기환경지수 등급)
- 바뀐 기준을 확인하는 단위 테스트
- `docs/`의 기준 문서 수정

## 비밀 값

API 키, AWS 자격 증명은 저장소에 커밋하지 않습니다. `.env` 파일은 `.gitignore`에 포함되어 있습니다. 실수로 올렸다면 키를 즉시 폐기하고 메인테이너에게 알려 주세요.

## 응답

메인테이너는 외부 이슈와 PR에 3일 이내에 응답합니다.

## 라이선스

기여한 코드는 이 저장소의 [MIT License](LICENSE)로 배포됩니다.
