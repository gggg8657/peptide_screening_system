# P1-5 — UI P0 신규 기능 구현

> **작성일**: 2026-05-13  
> **작성자**: reviewer-uiux  
> **판정**: ✅ PASS — 빌드 성공, 60/60 테스트 통과

---

## 요약

| 항목 | 결과 |
|------|------|
| `npm run build` | ✅ 성공 (9.08s) |
| `npm test` | ✅ 60/60 통과 |
| 신규 컴포넌트 | 3개 (HeuristicBanner, CandidateCompareModal, ArchivesTopKSlider) |
| 수정 페이지 | 2개 (CombinedPage, SelectivityPage) |
| 신규 테스트 | 26건 (HeuristicBanner 8 + CandidateCompareModal 9 + ArchivesTopKSlider 9) |

---

## 1. HeuristicBanner.tsx (신규, ~90 LOC)

**경로**: `frontend/src/components/HeuristicBanner.tsx`

### 구현 내용
- 4등급 지원: `A` (실측 기반) / `B` (in-silico 추정) / `C` (검증 부족) / `HEURISTIC` (ranking 전용)
- `warnings[]` prop — 경고 목록 bullet 표시 (compact=false 시)
- `compact` prop — 경고 숨김 (압축 뷰)
- WCAG 2.1 AA: `role="note"` + `aria-label` 적용

### 등급별 색상 체계
| 등급 | 아이콘 | 배경 | 텍스트 |
|------|--------|------|--------|
| A | CheckCircle2 | `bg-green-900/20 border-green-500/50` | `text-green-400` |
| B | FlaskConical | `bg-yellow-900/20 border-yellow-500/50` | `text-yellow-400` |
| C | AlertTriangle | `bg-orange-900/20 border-orange-500/50` | `text-orange-400` |
| HEURISTIC | ShieldAlert | `bg-red-900/20 border-red-500/50` | `text-red-400` |

### 테스트 (8/8 ✓)
- 4등급 각 렌더링 확인
- compact 모드에서 경고 숨김
- `aria-label` 접근성 속성

---

## 2. CandidateCompareModal.tsx (신규, ~260 LOC)

**경로**: `frontend/src/components/CandidateCompareModal.tsx`

### 구현 내용
- 2~3개 후보 side-by-side 비교 테이블
- 서열 diff 하이라이트: 첫 번째 후보(기준)와 다른 AA 위치에 `bg-amber-500/30` 배경 + tooltip
- 비교 행: 서열, Result, ΔΔG, Total Score, Boltz iPTM, HL score, Instability Index, GRAVY, Nephrotox, Protease sites, Clash Score
- 색상 코딩: ddG / iPTM / instability / GRAVY 각각 의미별 색상
- HEURISTIC 경고 footer 고정
- 접근성: `role="dialog"` + `aria-modal` + `useFocusTrap` + Escape 키 닫기 + 오버레이 클릭 닫기
- `overflow: hidden` 스크롤 잠금 (모달 열림 시)
- Export PDF: placeholder (Phase 2 예정)

### 타입 확장
```typescript
interface ExtendedCandidate extends Candidate {
  iptm?: number
  instability_index?: number | null
  gravy?: number
  nephrotox?: string
  hl_score?: number | null
  protease_sites?: number
}
```

### 테스트 (9/9 ✓)
- 2개 후보 렌더링, ID 헤더 확인
- 첫 번째 후보 "(기준)" 표시
- X 버튼 + Escape 키 닫기
- HEURISTIC footer 확인
- 서열 aria-label 확인
- 빈 배열 → null 렌더링
- 속성 비교 테이블 row 확인

---

## 3. ArchivesTopKSlider.tsx (신규, ~250 LOC)

**경로**: `frontend/src/components/ArchivesTopKSlider.tsx`

### 구현 내용
- `GET /api/archives/top-k?receptor=SSTR2&k=K` 호출
- **fallback**: API 실패 시 mock 15개 데이터 자동 전환 + "mock data" 배지 표시
- K 선택: 5 / 10 / 20 / 50 / 100 버튼 (aria-pressed)
- Tier 필터: T3 / T2 / T1 토글 버튼 (aria-pressed)
- 정렬: iPTM / Selectivity Index / Tier — 클릭 토글 asc/desc (aria-sort)
- SI× (Selectivity Index) = SSTR2 iPTM / mean(SSTR1,3,4,5 iPTM)
- 색맹 친화적 `TierBadge` — T3/T2/T1 텍스트 + 색상 조합
- `onSelect` prop → 행 클릭 시 콜백 (부모에서 CompareModal 연동 가능)
- 로딩 스피너 overlay + aria-live "로딩 중…"
- 가상 스크롤 없음 (max-h-96 overflow-y-auto, K≤100으로 충분)

### 테스트 (9/9 ✓)
- 제목 렌더링
- mock data 배지 확인 (API 실패 후)
- K 버튼 5종 확인
- K 변경 → aria-pressed 반영
- Tier 버튼 3종 확인
- Tier 토글 → aria-pressed 변경
- 테이블 렌더링 + 헤더 확인
- onSelect 콜백 호출
- SI× 컬럼 헤더 확인

---

## 4. CombinedPage.tsx 수정

**경로**: `frontend/src/pages/CombinedPage.tsx`

### 변경 내용
- `SiloAEmptyBanner` 컴포넌트 추가:
  - `siloACandidates.length === 0` 시 최상단에 amber 배너 표시
  - 메시지: "Silo A 실행 이력 없음 — 현재 Silo B 단독 데이터만 표시됩니다."
  - 빠른 이동 버튼: "Silo B 실행" + "Silo A 시작 →" (`useNavigate` 활용)
  - `role="note"` + 적절한 색상 (`border-amber-500/30 bg-amber-500/10`)
- import 추가: `AlertTriangle`, `useNavigate`

---

## 5. SelectivityPage.tsx 수정

**경로**: `frontend/src/pages/SelectivityPage.tsx`

### 변경 내용
1. **HeuristicBanner 통합**: Results 섹션 최상단에 `grade="C"` 배너 추가
   - 경고 4건: iPTM ≠ Ki / Spearman ρ ≈ −0.3 / 순위 일치 0/5 / 선택성 해석 한계
2. **ArchivesTopKSlider 추가**: 페이지 최하단 새 섹션으로 1,615 페어 평가 결과 표시
3. import 추가: `HeuristicBanner`, `ArchivesTopKSlider`
4. `BOLTZ_IPTM_WARNINGS` 상수 추가 (M5 결과 반영)

---

## 접근성 체크리스트

| 항목 | HeuristicBanner | CandidateCompareModal | ArchivesTopKSlider |
|------|-----------------|----------------------|-------------------|
| role 속성 | `role="note"` ✅ | `role="dialog" aria-modal` ✅ | `role="button"` (행) ✅ |
| aria-label | ✅ | ✅ | `aria-label="선택"` ✅ |
| Keyboard | — | Escape 닫기 ✅ | Enter/Space 행 선택 ✅ |
| 색맹 | 텍스트 + 아이콘 ✅ | 텍스트 + 값 ✅ | TierBadge 텍스트 ✅ |
| 정렬 | — | — | `aria-sort` ✅ |
| 로딩 | — | — | `aria-live="polite"` ✅ |

---

## §검증 필요

1. **useFocusTrap 실제 동작**: jsdom 환경에서 포커스 트랩 완전 검증 불가 — 브라우저에서 Tab 이동 수동 확인 필요
2. **Export PDF**: `handleExport` 현재 alert placeholder — Phase 2에서 jsPDF 또는 서버사이드 WeasyPrint 구현 필요
3. **CombinedPage Silo A 조건**: `siloACandidates.length === 0` — 실제 Silo A 데이터 수신 시 배너 자동 사라짐 확인 필요
4. **ArchivesTopKSlider API 연동**: `/api/archives/top-k` backend 라우터 P1-2 인프라 완료 후 mock → 실데이터 전환 확인 필요

---

*reviewer-uiux 작성 — 2026-05-13 / P1-5*
