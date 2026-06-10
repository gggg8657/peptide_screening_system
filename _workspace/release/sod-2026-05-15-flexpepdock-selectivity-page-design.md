# Manual Selectivity Page (FlexPepDock) — 설계서

> **Task #25** — 사용자 명시: ArchivesTopKSlider + HeuristicBanner를 SelectivityExplorerPage에 *이입하지 말고*, **별도 페이지를 신설하여 수기 진행 가능**하게.
> **Owner**: orchestrator (본 세션 설계) → engineer-backend (BE) + reviewer-uiux (FE 마운트) 구현 위임

---

## 1. 목적과 위치

### 차별점
| | 기존 Selectivity Explorer | **신규 Manual Selectivity** |
|---|---|---|
| 실행 트리거 | 자동 (run loop 내부) | **사용자 명시 클릭** |
| 도킹 엔진 | Boltz-2 (빠름, ~수분) | **FlexPepDock** (정밀, ~수십분-수시간) |
| 후보 선택 | run당 자동 산출 후보 | **사용자가 archive에서 선택** (ArchivesTopKSlider) |
| Receptor | SSTR1-5 모두 자동 | **SSTR1-5 중 사용자 선택** |
| 결과 신뢰도 | iPTM 기반 ranking (HEURISTIC) | **Ki/Kd 절대값 추정 가능** (FlexPepDock interface_score) |
| 사용 시점 | 매 iteration 자동 | **Tier 1-2 promising 후보 정밀 검증** |

### 가치
- 운영 루프(Boltz)는 빠르지만 ranking-only (Ki ≠ iPTM)
- FlexPepDock은 ΔΔG / interface_score 정밀 추정으로 ranking + 절대값
- pre-wet-lab 최종 컷오프 결정에 직접 활용

### URL
- `/manual-selectivity` (또는 `/selectivity/flexpepdock` 서브경로)

---

## 2. UI 구조 (재사용 컴포넌트)

```
┌─────────────────────────────────────────────────────────────┐
│ HeuristicBanner (grade: B in-silico estimation)             │
│   FlexPepDock는 in-silico estimation입니다. wet-lab 검증     │
│   전까지 Ki 절대값으로 가정하지 마세요.                       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Section 1: 후보 선택                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ArchivesTopKSlider                                       │ │
│  │  - 1,615 archive pairs                                   │ │
│  │  - Top-K (5/10/20/50/100) + Tier filter                  │ │
│  │  - 후보 선택 시 좌측 "Selected" 카드 표시                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  [수동 입력] 14aa 시퀀스 직접 입력 (textarea + validate)      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Section 2: Receptor + Params                                 │
│  ┌──────────────┐ ┌──────────────────────────────────────┐  │
│  │ ☑ SSTR1     │ │ FlexPepDock Config                    │  │
│  │ ☑ SSTR2     │ │  cycles: [10]                          │  │
│  │ ☐ SSTR3     │ │  nstruct: [50]                         │  │
│  │ ☐ SSTR4     │ │  flex_pep_freedom: [low/med/high]      │  │
│  │ ☐ SSTR5     │ │  ddg_cycle: [5]                        │  │
│  └──────────────┘ └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Section 3: 실행 + 진행                                        │
│  [🧪 Run FlexPepDock Selectivity] (선택 후보 없으면 disabled) │
│  ⏱ 예상 시간: ~30분 (selected receptors × nstruct 기준)        │
│  [progress bar] queued → running → done (SSE 또는 polling)    │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Section 4: 결과                                              │
│  Selectivity Matrix Table                                    │
│  | Receptor | ΔG (kcal/mol) | interface_score | Pass |       │
│  | SSTR1   | -8.2          | -42.5            | ❌   |        │
│  | SSTR2   | -11.5         | -68.3            | ✅   |        │
│  | ...     |               |                  |      |        │
│  ──────────────────────────────────────                       │
│  Selectivity Index = ΔG(SSTR2) - max(ΔG(others))              │
│  [Export CSV] [Download PDB ensemble]                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 백엔드 작업 큐 (engineer-backend)

### 새 endpoints (selectivity.py 확장)
```
POST /api/flexpepdock/jobs              # 작업 등록
  body: { sequence: str, receptors: list[str], config: {...} }
  resp: { job_id: str, eta_seconds: int }

GET  /api/flexpepdock/jobs              # 작업 리스트 (사용자별 또는 전체)
GET  /api/flexpepdock/jobs/{job_id}     # 상태 조회 (queued/running/done/failed)
GET  /api/flexpepdock/jobs/{job_id}/results
                                         # ΔG, interface_score per receptor
GET  /api/flexpepdock/jobs/{job_id}/ensemble.tar.gz
                                         # PDB ensemble download
DELETE /api/flexpepdock/jobs/{job_id}   # 작업 취소
```

### 작업 실행 워커
- **위치**: `pipeline_local/scripts/flexpepdock_worker.py` (신규)
- **기반**: 기존 `step06_rosetta.py`의 FlexPepDock 호출 패턴 재사용
- **큐**: 단순 file-based queue (`runs_local/flexpepdock_jobs/{job_id}/`)
  - `job.json` (request)
  - `status.json` (queued/running/done/failed + progress)
  - `result.json` (per-receptor ΔG, interface_score)
  - `ensemble/` (PDB ensemble per receptor)
- **동시 실행 제한**: 1 (GPU/CPU 자원 보호)
- **타임아웃**: 4h (configurable)

### Pre-flight 검증
- 시퀀스 14aa 길이 확인
- Cys-Cys SS bond 위치 정합성 (Cys3-Cys14)
- 선택한 receptor PDB 존재 확인 (`runs_local/alphafold_receptors/SSTR{1..5}/`)
- FlexPepDock binary 존재 확인 (`PyRosetta` 환경 활성)

---

## 4. FE 작업 (코드 위임 후속)

### 신규 파일
```
src/pages/ManualSelectivityPage.tsx       # 메인 페이지
src/hooks/useFlexPepDockJob.ts            # job 상태 polling/SSE
```

### 기존 재사용
- `ArchivesTopKSlider.tsx` (이미 PR #34에 존재)
- `HeuristicBanner.tsx` (이미 PR #34에 존재)
- `Sequence.tsx`, `TierBadge.tsx` (dashboard 컴포넌트)
- `ThemeToggle.tsx` (PR #40 — 자동 light/dark 대응)

### NAV_ITEMS 추가
- `App.tsx` NAV_ITEMS에 `Manual Selectivity` (icon: `FlaskConical` 또는 `TestTube`) 추가
- 메인 내비 `/manual-selectivity`

---

## 5. 검증 시나리오

1. **빈 폼**: Run 버튼 disabled
2. **시퀀스 + 0 receptor**: Run disabled
3. **유효한 시퀀스 + SSTR2만 선택**: Run enabled, ETA 표시
4. **Run 클릭**: status → queued → running (SSE 진행률) → done
5. **결과**: 표 + Selectivity Index + CSV/PDB 다운로드
6. **실패 케이스**: timeout, FlexPepDock crash → status=failed + 에러 메시지
7. **취소**: 진행 중 작업 DELETE

---

## 6. 단계별 구현 우선순위

1. **Phase 1 (MVP, ~1일)**: FE 페이지 + ArchivesTopKSlider 통합 + 후보 선택 UI. BE는 mock job (sleep 5초 후 dummy result 반환).
2. **Phase 2 (BE 본격, ~2-3일)**: BE 작업 큐 + flexpepdock_worker.py + 실제 FlexPepDock 실행.
3. **Phase 3 (안정화, ~1-2일)**: 타임아웃 / 에러 핸들링 / 동시 실행 제한 / PDB 다운로드.
4. **Phase 4 (선택적)**: 결과 캐싱 (동일 sequence+receptor 재실행 방지), 비교 모드 (여러 후보 한꺼번에).

---

## 7. 위임 계획

| Phase | 위임 대상 | 비고 |
|---|---|---|
| Phase 1 FE | codex | ManualSelectivityPage.tsx mock-only |
| Phase 1 BE mock | codex | flexpepdock/jobs mock endpoints |
| Phase 2 BE | engineer-backend (서브에이전트) | flexpepdock_worker.py 실 구현 |
| Phase 2 BE 검증 | reviewer-pharma | FlexPepDock 파라미터 + ΔG 신뢰도 검증 |
| Phase 3 | codex + cursor-agent | 에러 핸들링 + UI 폴리시 |

---

## 8. 사용자 결정 필요 사항

- **Run lock 정책**: 한 번에 1개 작업만 vs 여러 사용자 동시 (운영 환경 1인 기준이면 1개로 충분)
- **결과 retention**: 7일 / 30일 / 영구 — disk space 고려
- **ETA 계산 방식**: 정적 (receptors × nstruct × 평균 시간) vs 동적 (이전 평균에서 학습)
- **wet-lab 연동**: 결과에서 직접 wetlab order 생성 버튼? (CandidatePage와 통합?)
