# 통합 분석 v2 정합성 검증 결과 (4 에이전트 cross-check)

**작성**: orchestrator-session, 2026-05-13
**검증 대상**: `liverun-integration-analysis-v2-2026-05-13.md`
**위임**: reviewer-code + engineer-backend + reviewer-uiux + reviewer-science 4 에이전트 병렬
**판정**: **CONDITIONAL** — 핵심 버그 식별 정확, 4건의 v2 오류 식별

---

## A. 4 에이전트별 핵심 발견

### A.1 reviewer-code (코드 정합성·DAG 검증)

**v2 라인 인용 정확성**: 24 항목 중 22 ✓, 부분일치 2 (state.py:23-28 이미 P1-2 적용 / state.py:57-66 위치 인용 오류 — 실제는 App.tsx:66), ✗ 1

**DAG 검증**:
- ✓ 사이클 없음
- **오류 1**: P02←P01 의존성 불필요 (state.py 이미 수정됨)
- **오류 2**: P03←P01 의존성 불필요 (P03 수정 대상은 App.tsx, P01과 무관)

**회귀 시나리오 13단계 분류**:
- 자동화: 10건 (1,2,4,5,6,7,8,9,11,13)
- 수동: 2건 (3 React DevTools, 10 Storybook/E2E)
- 불명확: 1건 (12 subprocess hang 재현 조건 미정)

**결정 게이트 코드 일관성**:
- G-1: 1줄 → 코드 1줄 + 문서 3곳 + start_monitoring.sh 동시 필요
- G-2: ✓
- **G-3: 이미 완료, 결정 게이트에서 제거**
- G-4: ✓
- G-5: 타당 (단 Silo A 미동작 확인 별도 필요)
- G-6: 불완전 — cancel endpoint + 도킹 루프 cancelled 체크포인트 별도 필요
- G-7: ✓

### A.2 engineer-backend (BE 패치 실효성)

**P01**: ⚠️ 조건부 — `start_monitoring.sh:85` rm 경로 + `ENVIRONMENT_FILE.md` + `UI_GUIDE.md` + `PIPELINE_GUIDE.md` 동시 수정 필요

**P02**: ⚠️ 조건부 — Popen 성공 직후 write + OSError try/except 필요 (Popen 실패 시 initializing 상태 잔존 방지)

**P03**: ✓ 적용 가능 — 단, server_time은 캐시 hit 후 후처리 주입 필요 (캐시 동일성으로 인한 stale time 방지)

**P08**: ⚠️ 조건부
- **conda env에 이미 설치됨**: python-multipart 0.0.22, biopython 1.79
- requirements.txt 추가는 환경 재구성 문서화 목적
- **subprocess PIPE drain 위험 실재** — OS 64KB buffer fill 시 hang. `DEVNULL` 권장 (daemon thread는 asyncio 혼용 위험)
- watchdog의 lock holding도 별도 위험

**P09**: ⚠️ 조건부
- **llm_provider/model/base_url 이미 폴백 구현됨** (experiment.py:263-291)
- **미구현은 max_iterations/n_candidates/top_k 3개만**
- 3-way 폴백 (`req.X or runtime_settings.get('X') or DEFAULT['X']`) 추가
- 멱등성 문제 없음 (CLI 인자로 전달되므로 subprocess 내부 고정)

**P10**: ⚠️ 조건부
- **approach='a'/'b'는 이미 구현됨** — `--no-approach-b`/`--approach-b` 플래그가 `run_pipeline_local.py`에 전달됨
- **dual만 차단됨** — `ExperimentRunRequest`의 `pattern=r"^[abAB]$"` 제약
- 해결: regex `r"^[abABdD]$"` 확장 + approach='dual'→`--dual` 매핑

**P11**: ⚠️ 조건부
- **soft cancel만 가능** — production 모드의 `runner.dock_against_receptor()`가 `subprocess.run(..., timeout=600)`이라 시작된 subprocess는 600초 대기. 다음 후보부터 skip 가능.
- **즉시 cancel**: SelectivityRunner에 PID 노출 리팩토링 선행 필요 (별도 sprint)
- 변수명 `_jobs` (소문자, `_job_lock`으로 보호). v2의 `_JOBS` 표기 오기
- 완료 job에 cancel 호출 시 409 Conflict 권장

**P12**: ✓ 적용 가능 (대상 파일 정정)
- **pipeline_local 버전엔 이미 `_resolve_receptor_paths()`로 구현됨** (`selectivity.py:257-269`, `.pdb > .cif > .mmcif` 우선)
- **ai4sci-kaeri 옛 selectivity.py에만 해당**
- 두 버전 동기화 검토 별건

### A.3 reviewer-uiux (FE 패치 실효성)

**P04**: ⚠️ 조건부 — `live.completed`와 `live.updatedAt`은 이미 hook이 반환. P03 없이도 FE 단독 가능. 단:
- "Snapshot" 명칭이 연구자에게 생소 → "Completed" 권장
- Stale 임계값 30s는 polling 2s 대비 깜빡임 위험 → **60s 이상 또는 polling × 5 이상**
- 4 배지 aria-label 추가 (WCAG 1.4.1)

**P05**: ⚠️ 조건부 — payload 필드 확장 **순서 문제**:
- `Candidate` 타입에 필드 없음
- stability/selectivity/SAR 결과를 candidate에 머지하는 로직 부재
- **순서: 타입 확장 → mapCandidate 보강 → payload 확장**
- 현재 payload만 확장하면 null 전송에 불과

**P11-FE**: ⚠️ 조건부 — `jobIdRef.current`는 유효, race condition 처리 필요:
- cancel 응답 도착 전 polling이 `completed` 받으면 자동 복구 로직이 다시 로드 → 조용한 데이터 불일치
- BE 미배포 환경: 404 graceful 처리 (try/catch + console.warn)

**P13**: ⚠️ 조건부 — BE가 receptor 단위 카운트 별도 제공 안 하면 FE 단독으론 추정 개선만. BE 협의 후 진행 권장.

**P14**: ✗ 위험 → **즉시 수정 필요**
- BE 응답에 `c.offtarget_max_receptor`/`c.offtarget_max_score` 이미 있음 (`selectivity.py:273-274`)
- FE `_mapCandidates`가 이걸 무시하고 `otEntries`를 max로 재계산 (`useSelectivity.ts:64-66`)
- **결과: 실제 -12 ddG receptor(가장 위험)가 amber/green으로 표시 — 데이터 오류**
- 수정: 1~2줄. BE 값 그대로 사용

**P15**: ✓ 적용 가능 — 기존 `CheckRow:32-69`에 `MinusCircle` 처리 있음. 결과 행 dot에 회색 dot 추가만. aria-label 필요.

**Silo A/Combined Coming Soon**: ✓ 적용 가능 — 기존 `SiloAEmptyBanner` 활용. 단, Coming Soon 배너와 중복 방지.

### A.4 reviewer-science (G-2 부호·임계·단위)

**부호 컨벤션**: pipeline_local 신 (+ = 선택적) 채택 권장
- 수학적으로 두 컨벤션 완전 동치 (단순 부호 반전)
- 시각화·정렬 직관성, step05c iPTM과 일관

**[CRITICAL] 단위 혼동**:
- 현재 top ddG=-49.6은 **Rosetta Energy Units(REU)일 가능성 높음** (실제 펩타이드-GPCR ΔG는 -8~-15 kcal/mol)
- yaml의 "kcal/mol" 레이블 → "REU" 또는 "Rosetta Score Units"로 정정 필수
- "+10 kcal/mol = 10^7-fold selectivity" 같은 v2 해석은 단위 혼동에서 비롯

**임계값 +10.0 통계 위치 (N=34)**:
- SSTR2 ddG: mean=-30.98 REU, std=13.58 REU
- OT=-12 시나리오 +10.0 통과율 73.5% (μ-0.66σ)
- 통계적으로 +5.0(μ-1σ)이 더 적절
- **+10.0은 현재 데이터 내 합리적 위치 — 단기 유지, 중기에 off-target 실측 후 재조정**

**DOTATATE 임상 기준**:
- DOTATATE SSTR3 ΔΔG = 3.30 kcal/mol (211-fold)
- DOTATATE SSTR5 ΔΔG = 1.99 kcal/mol (25-fold) — 가장 취약
- PRRT 임상 요구: 100-fold (~2.84 kcal/mol)
- 단, kcal/mol과 REU 직접 비교 불가

**AG_src yaml 동기화 위험**:
- yaml -10 → +10만 변경 시 **코드 gate 조건도 동시 변경 필수**
- 코드 변경 금지 시: yaml 그대로 + 문서만 업데이트

**검증 트랙 등록 필요**:
- VR-G2-01: off-target SSTR1/3/4/5 실측 ddG 없이 -12 REU 상수 가정 → 1회 실제 실행
- VR-G2-02: yaml 단위 레이블 "kcal/mol" → "REU" 재확인

---

## B. v2 → v2.1 정정 종합

| # | v2 주장 | 검증 결과 | v2.1 정정 |
|---|---|---|---|
| 1 | state.py 패치 P03 필요 | 이미 P1-2(05-13) 적용 | 후처리만 추가, 의존성 제거 |
| 2 | P02/P03이 P01에 의존 | 무관 | Tier 0로 재분류 |
| 3 | G-3 결정 필요 | 완료 처리 | 결정 게이트 제거 |
| 4 | state.py:57-66이 completed 무시 위치 | 실제는 App.tsx:66 | 위치 인용 정정 |
| 5 | C-P0-3 "Silo A/Combined 미구현" | Silo A는 구현됨, dual만 차단 | G-5 정정: Silo A 활성, dual만 regex 확장 또는 비활성 |
| 6 | P09 runtime_settings 전체 미참조 | llm_* 이미 구현, max_iter/n_cand/top_k만 | 3-way 폴백 3필드만 추가 |
| 7 | P12 _get_receptor_pdb 필요 | pipeline_local 이미 구현, ai4sci-kaeri만 | 대상 파일 정정 또는 제거 |
| 8 | P14 worst off-target 통일 작업 | 1~2줄 fix, BE 응답값 사용 | 가장 critical하지만 가장 단순 |
| 9 | G-2 "+10 kcal/mol = 10^7-fold" | REU 단위, 단위 혼동 | yaml 레이블 정정 + VR-G2-01/02 등록 |
| 10 | P05 payload 확장 | 순서 강제 필요 | 타입 확장 → mapCandidate → payload |
| 11 | P11 cancel endpoint | endpoint + 도킹 루프 cancelled 체크포인트 + soft만 가능 | 명시적 soft 표기, 즉시 cancel 별도 sprint |
| 12 | P08 requirements 미설치 | conda env엔 이미 설치, 문서화 목적 | 명시적 표기 |
| 13 | P04 4 배지 | Snapshot 명칭 + Stale 임계값 결정 | "Completed" 권장 + 60s 이상 |

---

## C. CONDITIONAL 판정 사유

**식별 정확**:
- worst_ot min/max 역전 (P14)
- step06 ID 중복 (P06)
- subprocess PIPE 미소비 (P08, 실재 hang 위험)
- requirements 누락 (P08, 문서화)
- ValidationPanel placeholder (P15)
- ClusterPanel payload 5필드 (P05)
- App.tsx isLive completed 무시 (P04)
- status_emitter 기본값 (P01)

**식별 부정확/과도**:
- C-P0-3 Silo A 미구현 → 사실은 dual만 차단
- P09 settings 전체 단절 → 일부만
- P12 pipeline_local 미구현 → 이미 구현됨
- state.py 패치 필요 → 이미 적용됨

→ v2 패치 15건 중 약 5건은 범위 정정 후 실효 (P09 일부, P12 선택, P03 후처리만, P02/P03 Tier 변경, state.py 제거). 나머지 10건은 그대로 진행 가능.

---

## D. 다음 SOD 즉시 액션

1. **G-1~G-9 사용자 일괄 확정**
2. **Tier 0 8 패치 병렬 디스패치** (engineer-backend × 5, reviewer-uiux × 3, engineer-infra × 1)
3. **Tier 1 적용 → uvicorn 1회 재기동**
4. **Tier 2 FE HMR**
5. **회귀 시나리오 13단계 검증** (자동 10 + 수동 2 + 미정 1)
6. **VR-G2-01/02 검증 트랙 등록** (별도 워크 트랙)

---

## E. 참고 — 본 분석에서 도출된 검증 필요 (VR-cycle 등록 후보)

| ID | 내용 | 등록 시점 |
|---|---|---|
| VR-G2-01 | off-target SSTR1/3/4/5 실측 ddG 없이 -12 REU 상수 가정 | G-2 정정 후 |
| VR-G2-02 | yaml 단위 레이블 "kcal/mol" vs 실제 REU 가능성 | G-2 정정 시 |
| VR-G5-01 | Silo A 실 동작 (RFdiffusion/ProteinMPNN 환경 정비) | G-5 활성 시 |
| VR-G6-01 | SelectivityRunner subprocess timeout(600s) 대기 vs PID kill | G-6 즉시 cancel 결정 시 |
| VR-G7-01 | unified_validation rank_stability/score_consistency/no_dominance 실데이터 구현 | G-7 실데이터 옵션 시 |
