# Claude Skills 도입 계획서

> 작성일: 2026-03-12
> 기반: awesome-claude-skills 레포 분석 (3팀 병렬 리뷰)

## 프로젝트 컨텍스트

- SSTR2 방사성의약품 후보 스크리닝 AI Co-Scientist 파이프라인
- 5-Agent tmux 팀 (orchestrator + 4 teammates)
- conda 환경 3개 (bio-tools, rfdiffusion, diffpepdock)
- CI/CD: GitHub Actions 7 jobs (실패 시 메일 알림 기구축)
- 기존 커맨드: /codex, /cursor-agent, /team, /agent-status

## Phase 1: 즉시 도입 (상)

| # | 스킬 | 출처 | 용도 |
|---|------|------|------|
| 1 | using-git-worktrees | obra/superpowers | tmux 팀원별 격리 작업, 단일 main 브랜치 리스크 해소 |
| 2 | test-driven-development | obra/superpowers | 로컬 모델 전환 시 인터페이스 계약 먼저 정의 (Red-Green-Refactor) |
| 3 | subagent-driven-development | NeoLabHQ/context-engineering-kit | /team 강화, WS1~5 병렬 + 코드리뷰 체크포인트 |
| 4 | root-cause-tracing | obra/superpowers | 4개 ML 모델 x 3 conda env 에러 체인 추적 |
| 5 | test-fixing | mhattingpete/claude-skills-marketplace | 150개 테스트 x 7 CI jobs 실패 시 자동 패치 |
| 6 | tapestry | michalparkola/tapestry-skills | 7+ 디렉토리 분산 문서의 지식 네트워크화 |
| 7 | pptx | anthropics/skills | 학회 발표 슬라이드 자동 생성 |
| 8 | xlsx | anthropics/skills | 22K 후보 결과 구조화된 비교표 |

## Phase 2: 이후 도입 (중)

| # | 스킬 | 용도 |
|---|------|------|
| 1 | review-implementing | 5-Agent 구현 계획 품질 관리 |
| 2 | GitHub Automation | gh CLI 확장, webhook 반응형 자동화 |
| 3 | brainstorming | 가설 경쟁/실험 설계 구조화 |
| 4 | kaizen | 리팩토링 완료 후 지속적 개선 체계화 |
| 5 | pdf / docx | 기관 제출용 변환, 논문 PDF 추출 |
| 6 | Changelog Generator | 기간별 변경 이력 자동 생성 |
| 7 | CSV Data Summarizer | 22K 후보 빠른 탐색/시각화 |

## 제외 및 사유

| 스킬 | 제외 사유 |
|------|-----------|
| n8n-skills | GitHub Actions → 메일 알림 이미 구축됨, 중복 |
| Slack/Telegram Automation | 외부 서비스 경유 → 데이터 노출 위험, webhook 미사용 방침 |
| deep-research | Gemini API 필수, 미보유. /codex로 대체 가능 |
| MCP Builder | MCP 서버 구축 필요성 없음 |
| Skill Creator | 수동 생성으로 충분 |
| Playwright / Webapp Testing | 웹 프론트엔드가 핵심 아님, Vitest+RTL 충분 |
| prompt-engineering | 에이전트 프롬프트 이미 최적화됨 |
| postgres | DB 미사용, 파일 기반 파이프라인 |
| computer-forensics | 프로젝트 무관 |
| Google Workspace / Notion | GitHub 중심 워크플로, 미사용 |
| Datadog / Vercel / CircleCI | 현 규모에 과도 또는 미사용 |
| Discord | 연구팀 커뮤니케이션에 비주류 |
| Canvas Design / Video Downloader / EPUB | 연구 파이프라인과 무관 |
