# CHANGELOG

AirFit의 버전별 변경 기록입니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를, 버전 번호는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [1.0.0] - 2026-11-27

첫 공개 버전입니다. 제안서의 필수, 추가, 도전 기능을 모두 담아 AWS에 배포했습니다.

배포 주소: <https://d1bdayuw5d2l10.cloudfront.net>

### 추가

**조회와 생활 정보**

- 현재 위치와 지역 검색으로 날씨, 대기질 조회 (#9, #12, #32)
- 지역 검색의 최근 검색과 키보드 선택 (#27)
- 생활지수 카드 4종: 외출, 마스크, 환기, 빨래 (#31)
- 규칙(JSON) 기반 옷차림 추천과 보조 팁 (#19, #21, #22)
- 시간대별 기온, 체감온도, 강수 확률 그래프와 다크 모드 (#13)

**옷장**

- 옷장 등록, 목록, 삭제, 수정. 옷장은 브라우저에만 저장 (#38, #40)
- 옷장 안에서 오늘 입을 옷 추천: `POST /api/wardrobe/recommend`와 결과 화면 (#36, #41, #46)
- 옷 이름으로 종류, 두께, 방수 여부를 추정해 미리 채우기: `POST /api/wardrobe/classify` (#42, #48)

**챗봇**

- 오늘 날씨와 옷차림 질문에 답하는 챗봇: `POST /api/chat`과 챗봇 화면 (#43, #50)
- 옷 분류와 챗봇에 Claude Haiku 5.5(Anthropic API) 사용. 꺼져 있거나 실패하면 키워드 규칙과 규칙 기반 요약으로 답함 (#55)

**인프라와 운영**

- AWS SAM으로 Lambda, API Gateway(HTTP API) 배포와 GitHub Actions CD. AWS 인증은 OIDC (#5)
- S3와 CloudFront로 프론트 호스팅. 화면과 `/api/*`를 같은 주소로 제공 (#20, #25)
- 외부 API 응답을 DynamoDB에 캐시 (#34)
- 백엔드, 프론트 CI: ruff, pytest(커버리지 70% 하한), SAM 템플릿 검사, ESLint, Vitest, 빌드 (#2)
- 배포 후 smoke test: 상태 확인, 지역 검색, 옷 분류, 챗봇 (#55, #56)

**문서**

- README, CONTRIBUTING, NOTICE, 이슈와 PR 템플릿 (#6, #7)
- 외부 API 이용 조건(에어코리아, OpenWeather, Kakao, Anthropic API) (#24, #33, #55)
- API 명세(`docs/api.md`)와 이 CHANGELOG

### 변경

- 옷 분류와 챗봇의 LLM 호출을 Amazon Bedrock에서 Anthropic API로 바꿈. 팀 AWS 계정에서 Claude Haiku 5.5 호출이 허가되지 않았음 (#53, #54, #55)
- Lambda 메모리를 256MB에서 1024MB로 올리고, Anthropic SDK를 Lambda 시작 단계에서 불러오게 함. 요청 중에 불러오면 10초 제한을 넘겼음 (#55)

### 수정

- 밤에 최저/최고 기온이 현재 기온과 같게 나오던 문제. 앞으로 24시간 범위로 계산 (#44, #35)
- 너무 긴 지역 검색어를 막고, 바다 좌표의 지역명 처리 (#32)
- 외부 API 키를 GitHub Secrets에서 `sam deploy`로 넘기도록 수정 (#28)
- Windows에서 테스트 fixture와 `.env`를 UTF-8로 읽도록 수정 (#23)
- 옷장, 챗봇 화면 리뷰 사항 반영: 429 안내 문구, 사용자가 고른 값 유지, 위치 변경 시 지난 결과 정리 (#52)
- Anthropic API 키가 없을 때 배포가 실패하던 문제 (#56)

[1.0.0]: https://github.com/AirLog-Organization/AirFit/releases/tag/v1.0.0
