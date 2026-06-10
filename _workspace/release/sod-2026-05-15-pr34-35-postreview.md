# SOD 2026-05-15 — PR #34, #35 사후 검증 (cursor-agent)

> **수행**: cursor-agent (`logs/external_agents/cursor-agent_20260515_021159_1757624.jsonl`)
> **소요**: 81초
> **참조 prompt**: `_workspace/22_cursor-agent_pr34-35-review.md`

## 결과 요약

| # | 검증 항목 | 결과 |
|---|---------|------|
| 1 | 신규 컴포넌트 사용처 (ArchivesTopKSlider, HeuristicBanner) | PASS (주의) |
| 2 | dashboard.ts 신규 hook 6종 사용처 | PASS |
| 3 | cand03 default 제거 + baseline 잔재 | PASS (주의) |
| 4 | BE 엔드포인트 일치 | **FAIL** |
| 5 | About 페이지 OKLCH 잔여 토큰 | PASS (0건) |
| 6 | 다른 세션 미커밋 테스트 (read-only) | N/A |

## FAIL: useSelectivity ↔ BE 엔드포인트 불일치

**FE**: `dashboard.ts:306` `useSelectivity` → `GET /selectivity/${runId}`
**BE**: `backend/routers/selectivity.py` 제공 라우트
- `GET /selectivity/receptors`
- `GET /selectivity/structure/{receptor_name}`
- `GET /selectivity/status/{job_id}`
- `GET /selectivity/results/{job_id}`
- `GET /selectivity/jobs`

→ `/selectivity/{run_id}` 라우트는 **존재하지 않음**. `SelectivityExplorerPage` 런타임 404.

### 해결 옵션
- **A. BE에 `GET /api/selectivity/{run_id}` 추가** (run별 selectivity 집계 조회)
- **B. FE `useSelectivity` 재설계** — `/api/runs/{run_id}` 응답의 selectivity 필드 사용 (아카이브 JSON에 이미 들어있음)

## 주의 사항 (FAIL은 아니나 후속 정리)

### 1. ArchivesTopKSlider, HeuristicBanner 사용처
- `SelectivityPage.tsx` (`/selectivity` 레거시 라우트)에서만 사용
- 메인 내비 기본 경로 `SelectivityExplorerPage` (`/selectivity-explorer`)에는 부재
- **권고**: SelectivityExplorerPage로 이입하거나, 명시적으로 레거시 표기

### 2. baseline 잔재
- `AGCKNFFWKTFTSC` (SST-14 wild type): CandidatePage / RunConsolePage / SelectivityExplorerPage / dashboard.ts `useCandidates` 의 wild_type fallback
- `CandidatePage`: `order_id` 쿼리 없을 때 `WO-2026-005` 기본값 (데모 잔재)
- **권고**: 운영 모드에서 빈 값/에러 상태를 더 드러내려면 후속 정리

## Recommendation (cursor-agent)
> BE에 `/api/selectivity/{run_id}` 추가 vs `useSelectivity` 제거·대체를 먼저 결정한 뒤, SelectivityExplorerPage에서 실제 응답 스키마로 네트워크 스모크 확인 권장.

## 사용자 결정 필요
- 옵션 A (BE endpoint 추가) vs 옵션 B (FE hook 재설계)
