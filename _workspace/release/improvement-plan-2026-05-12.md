# 개선 계획 — 2026-05-12 SOD3 종합

**기반**: Team `sod-2026-05-12-f05-and-improvement` 4/4 closure (T1 F-05 fix + T2 환경 점검 + T3 UI 검증 + T4 코드 분석)

**입력 산출**:
- `_workspace/release/pr-f05-step07-foldmason-2026-05-12.md` (T1)
- `_workspace/release/be-fe-environment-check-2026-05-12.md` (T2)
- `_workspace/release/ui-verification-2026-05-12.md` (T3)
- `_workspace/release/code-analysis-pipeline-local-2026-05-12.md` (T4)

---

## 1. 즉시 처리 완료 (본 세션 인라인)

| Source | 항목 | 위치 | 비고 |
|--------|------|------|------|
| T1 backend | F-05 fix (step07 FoldMason n<2 skip) | `step07_analysis.py` + 6 신규 테스트 | 브랜치 `fix/f05-step07-foldmason` (`198f450`) |
| T3 uiux | aria-expanded | `ValidationPanel.tsx:38` | ⚠️ T1 브랜치에 혼재 |
| T3 uiux | useFocusTrap + dialogRef | `MoleculeViewer.tsx` | ⚠️ T1 브랜치에 혼재 |
| T3 uiux | Recharts formatter `any` → typed | `CombinedPage.tsx:375,417` | ⚠️ T1 브랜치에 혼재 |

**즉시 액션 권고**: T3의 3개 FE 수정을 `fix/f05-step07-foldmason`에서 빼내 별도 브랜치 `fix/ui-accessibility-2026-05-12`로 분리 (관심사 분리 + 리뷰 명확성).

---

## 2. 핵심 개선 후보 — 우선순위 통합 (T3 UI + T4 코드)

### Critical (총 3건, 모두 코드 측)

| ID | 영역 | 위치 | 내용 | 공수 |
|----|------|------|------|------|
| **C-1** | 코드 | `orchestrator.py:533~1093` | `run_single_iteration()` **561줄 God Function** 분해 (Approach A/B/dual + 6 agent + gate stats) | L |
| **C-2** | 코드 | `orchestrator.py:910, 933` | `locals().get("step03b_out")` + `type('R', (), {...})()` 익명 클래스 anti-pattern 제거 → 명시적 dataclass | M |
| **C-3** | 코드 | `orchestrator.py:1209` | SST-14 서열 `"AGCKNFFWKTFTSC"` 하드코딩 → config | S |

### High (총 8건)

| ID | 영역 | 위치 | 내용 | 공수 |
|----|------|------|------|------|
| **H-1** | 코드 | `pipeline_local/**` | `sys.path` 뮤테이션 8개 파일 분산 → `core/path_setup.py` 중앙화 | M |
| **H-2** | 코드 | orchestrator status emit | `_STEP_PROGRESS` dict 매 호출 재생성 → 모듈 상수화 (UI 2초 폴링 낭비 해소) | S |
| **H-3** | 코드 | `step06_rosetta.py` | `ref_paths` 중복 (R5 잔여) — `_build_ref_paths()` 적용 확장 | S |
| **H-4** | 코드 | `step05b_selectivity.py` | ImportError fallback dataclass 재정의 (`io_schemas.py`와 이중화) 제거 | M |
| **H-5** | UI | `SiloBPage.tsx:36` | `SILO_B_STEPS`에 step05(DiffDock, Silo A 전용) 포함된 라벨 불일치 — 제거 또는 BE 측 재정의 | S |
| **H-6** | 테스트 | `orchestrator.py` (2226줄) | **테스트 0개** — 최소 happy-path 통합 테스트 신설 | L |
| **H-7** | 테스트 | step01~step05 | 5개 step 무커버 — mock 기반 단위 테스트 | M~L |
| **H-8** | 운영 | ollama | `qwen3:8b` 모델 부재 (T2 I-2) — pull 또는 R1 LLM provider override 적용 | S |

### Medium (총 9건)

| ID | 영역 | 위치 | 내용 | 공수 |
|----|------|------|------|------|
| M-1 | 코드 | `is_pyrosetta_available()` 함수 속성 캐시 | `@lru_cache` 전환 | S |
| M-2 | UI | Objective 그룹 | `role="group"` + `aria-label` | S |
| M-3 | UI | MoleculeViewer view mode buttons | `aria-label` | S |
| M-4 | UI | 전역 | `aria-live` region — 스크린 리더 알림 | M |
| M-5 | UI | ExperimentControl + PipelineStatus | 이중 진행 표시 레이블 명확화 | S |
| M-6 | 인프라 | conda env 관리 | T2 I-1: PID 836000 :8765 레거시 uvicorn 정리 | S |
| M-7 | 결함 | iter02 clash=11 (gate max=10) | `gate_thresholds.yaml` 경계값 재검토 | S |
| M-8 | 결함 | `05b_selectivity/` 빈 디렉토리 | `gates_enabled.selectivity: true`인데 미실행 — 원인 진단 | M |
| M-9 | 로깅 | 파이프라인 stdout 버퍼링 | `tee` 즉시 flush 또는 `python -u` 적용 (오늘 로그 0 bytes) | S |

### Low (총 5건)

- L-1: `ScoreCell` colorblind 아이콘 (M)
- L-2: `SiloBPage` 컴포넌트 분리 (L, 3~4h)
- L-3: T4 후속 PR `fix/tier3-followup-cleanup` 제출 — `_build_ref_paths` DRY (이미 commit, PR 미제출)
- L-4: `iter01/iter03 var_027` **pre_score 동일값(372.2717)** 모순 신호 진단 (§검증)
- L-5: `source="silo_a"` 라벨 — 기존 결과 파일은 fix 이전 상태 (cosmetic only)

---

## 3. 로드맵

### 1-Week (이번 주)
- **C-2, C-3, H-2, H-3, H-5, H-8, M-7, M-9** — 전부 공수 S~M, 즉시 적용 가능
- **F-05 fix PR (T1) 머지** — `fix/f05-step07-foldmason`
- **UI 접근성 PR 분리** — T3의 3 fix를 새 브랜치로 분리 후 PR
- **T4 후속 PR 제출** — `fix/tier3-followup-cleanup` (`680f19a`)
- 목표: 3개 PR (F-05 / UI a11y / Tier3 cleanup) 머지

### 1-Month
- **C-1** — `run_single_iteration()` 분해 (가장 큰 부채, L 공수)
- **H-1** — `sys.path` 중앙화
- **H-6** — orchestrator happy-path 통합 테스트 (커버리지 25% → 40% 목표)
- **H-4** — `step05b_selectivity` dataclass 이중화 제거
- **M-4** — `aria-live` region

### 1-Quarter
- **H-7** — step01~05 단위 테스트 (커버리지 40% → 60% 목표)
- **에이전트 인터페이스 격리** — 6 agent 호출을 protocol/ABC로 분리
- **stub 분리** — PyRosetta/Boltz/RFdiffusion stub을 production code에서 분리

---

## 4. 신규 §검증 필요 (T4 등록)
- VR-cycle-10: `_get_reference_peptide_com` 경로 (오늘 데모 source=silo_a 잔존과 관련)
- VR-cycle-11: 익명 클래스 교체 후 호출처 접근 패턴
- VR-cycle-12: BSA 추정 공식 (현재 휴리스틱)
- VR-cycle-13: 서열 하드코딩 영향 범위

---

## 5. 의사결정 대기

1. **본 세션 PR 분리 권고 승인**: T1 F-05 + T3 UI a11y 별도 브랜치/PR?
2. **다음 작업 우선순위**: 1-Week 항목 중 어느 것부터 (사용자 선택)?
3. **F9 Silo A dogfood 시점**: 어제 SOD1 T4가 환경 준비 완료 — 본 개선 작업 이후로 미룰지 동시 진행할지?
4. **§검증 4건(VR-cycle-10~13)을 별도 추적 항목으로 등록할지** (어제 등록한 R5/F-13/F-14/§검증 4건과 통합 관리)?
