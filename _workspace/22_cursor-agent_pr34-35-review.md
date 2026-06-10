# PR #34, #35 사후 검증 의뢰

## 대상
- **PR #34** (commit `2082a69`): `feat(fe): About 페이지 OKLCH 토큰 + handoff 디자인 마이그레이션`
  - 변경: `AboutPage.tsx`, `ArchivesTopKSlider.tsx` (신규), `HeuristicBanner.tsx` (신규)
- **PR #35** (commit `79bb803`): `feat(fe): 신규 6 화면 실 BE 데이터 연동 + cand03 default 제거`
  - 변경: `App.tsx`, `hooks/dashboard.ts`, `CandidatePage.tsx`, `RunConsolePage.tsx`, `RunLauncherPage.tsx`, `SelectivityExplorerPage.tsx`, `WetlabOrderPage.tsx`, `data.js`

## 검증 항목 (각 항목 PASS/FAIL/N/A + 짧은 근거)
1. **신규 컴포넌트 사용처** — `ArchivesTopKSlider`, `HeuristicBanner` 가 어디서 import 되어 실제 렌더링되는가? 사용되지 않으면 dead code.
2. **dashboard.ts 신규 hook 사용처** — `useCand03Variants`, `useADMET`, `usePredictedPassRates`, `useBenchmark`, `useWetlabOrders`, `useWetlabOrder`, `useTransitionWetlabOrder` 각 hook이 실제 페이지에서 호출되는가?
3. **cand03 default 제거 완전성** — `cand03` / 'AGCKNFFW...' 같은 하드코딩된 baseline 잔재 검색. `default` placeholder가 *명시적으로 placeholder임을 알리는가* (e.g., "데이터 없음" 표시).
4. **BE 엔드포인트 일치** — dashboard.ts의 `get()` 호출 경로가 BE `backend/main.py` 또는 `backend/routers/*.py` 에 *실제 존재*하는가? 누락된 endpoint 있는지.
5. **About 페이지 OKLCH 적용 완전성** — `AboutPage.tsx`에 잔여 `slate-*`, `gray-*`, `bg-black` 클래스가 있는지 grep.
6. **다른 세션 미커밋 파일** — `components/__tests__/ArchivesTopKSlider.test.tsx`, `HeuristicBanner.test.tsx`, `CandidateCompareModal.test.tsx` 가 미커밋 상태로 working tree에 존재. *건드리지 말고* 어떤 테스트인지만 보고.

## 출력 형식
표 1개 + Recommendation 섹션 (max 200 words).

## 제약
- 파일 수정 금지 (read-only 분석)
- 본 세션 컨벤션 (feedback_session_separation): 다른 세션 미커밋은 손대지 말 것
