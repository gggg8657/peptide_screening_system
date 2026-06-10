# LiveRun/SiloB UI 무동작 통합 분석 v2 + v2.1 정정안

**작성**: orchestrator-session, 2026-05-13
**위임 트리**: reviewer-code (v1, v2), engineer-backend × 2 + reviewer-uiux + reviewer-code (Phase 2), Codex gpt-5.4 (Phase 4), reviewer-code + engineer-backend + reviewer-uiux + reviewer-science (Phase 6 정합성 검증)
**관련 문서**: `eod-2026-05-13-orchestrator-session.md`, `v2-validation-cross-check-2026-05-13.md`, `codex-be-fe-review-2026-05-13-findings.md`

---

## A. 인과 그래프 v2 (text DAG)

### ROOT 노드

```
ROOT-1  writer/reader STATUS_FILE 경로 불일치
        status_emitter.py:30-33  → /tmp/ag_pipeline_status.json (writer 기본값)
        state.py:23-28           → /tmp/pipeline_local_status.json (reader 기본값, P1-2 05-13 적용됨)
        [신뢰: HIGH — 4 에이전트 모두 확인]

ROOT-2  state.py reader가 completed=true도 "활성"으로 해석
        실제 위치: App.tsx:66의 isLive 판정 (v2의 state.py:57-66 인용은 오류)
        [신뢰: HIGH — reviewer-code 정정]

ROOT-3  [신규, Codex 발견] FE-BE 계약(contract) 부재
        FE는 approach/settings 값을 payload로 보내지만 BE 무시
        experiment.py:177-186 — approach 무시, --planner-mode 하드코딩
        settings.py:41-44      — runtime_settings만 갱신
        experiment.py:128-185  — runtime_settings 미참조

        ※ 단 engineer-backend 정정: Silo A는 이미 --no-approach-b로 구현됨.
          Dual만 regex r"^[abAB]$"로 차단된 상태.
          llm_provider/model/base_url은 이미 폴백 구현됨 (line 263-291).
          미구현은 max_iterations/n_candidates/top_k 3개.

ROOT-4  [신규, Codex 발견] 선택적 의존성 누락
        requirements.txt:1-14 — python-multipart, Biopython 미선언
        ※ engineer-backend 정정: conda env bio-tools에는 이미 설치됨 (0.0.22, 1.79).
          requirements.txt 추가는 환경 재구성용 문서화.
```

### SYMPTOM 노드

```
S1  대시보드 연결 끊김 — UI가 어제 stale을 "Live"로 표시
    cause: ROOT-1, ROOT-2

S2  [신규] Stop 클릭 후 도킹 스레드 계속 동작
    useSelectivity.ts:288-292 — stoppedRef 플래그만 + polling 중단
    selectivity.py:292-324    — cancel endpoint 자체 없음
    cause: ROOT-3 (계약 부재)

S3  [신규] Settings 저장이 다음 run에 반영되지 않음
    experiment.py:128-185 — runtime_settings 미참조 (단, llm_* 일부는 이미 구현됨)
    cause: ROOT-3

S4  [신규] Silo A / Combined 시작 → 실제로는 항상 Silo B 실행
    SiloAPage.tsx:108-112 → approach='a' 주입
    CombinedPage.tsx:176,192-196 → approach='dual' 주입
    experiment.py — 이미 Silo A 분기는 구현됨, dual만 차단 (정정 후 약화된 증상)

S5  [신규] Selectivity progress bar 신뢰 불가
    BE: 후보 단위 +1 vs FE: 후보 × 4 receptor 가정

S6  [신규] off-target worst가 BE/FE 반대 표시
    BE selectivity.py:255,266 — min (가장 음수 = 가장 강한 결합)
    FE useSelectivity.ts:63-67 — max
    ※ reviewer-uiux 발견: BE 응답에 이미 offtarget_max_receptor 포함, FE가 무시하고 재계산

S7  [신규] Validation 통계 항목(rank_stability 등)이 UI에서 pass로 표시
    unified_validation.py:309-315 — passed=True, skipped=True placeholder
    ValidationPanel.tsx:41-42 — skipped 처리 일부 구현됨 (MinusCircle 아이콘)
    ※ reviewer-uiux 정정: 결과 행 dot 시각화에는 skipped 제외됨, 별도 dot 추가 필요
```

### BUG 노드

```
기존 BUG (v1 유지)
B2  App.tsx:66  isLive가 completed 무시
B3  ClusterPanel.tsx:330-338  payload 5필드만
B4  SiloBPage.tsx:61  archives 경로 FE 하드코딩 (pyrosetta_flow/archives/${runId})
B5  AG_src/config/gate_thresholds.yaml:37  selectivity_margin_min=-10.0 vs pipeline_local=+10.0 [CRITICAL]
    ※ reviewer-science 정정: 수치 +10 유지, 단위 레이블 "kcal/mol"→"REU" 정정 필요
B6  runner.py:532,547,730  step skip emit 부재 + step06 ID 재사용

신규 BUG (Codex)
B7  experiment.py:177-186  approach 파라미터 무시 → S4
    ※ engineer-backend 정정: Silo A는 구현됨, dual만 차단
B8  experiment.py:128-185  runtime_settings 미참조 → S3
    ※ engineer-backend 정정: llm_* 폴백 구현됨, max_iter/n_cand/top_k만 미구현
B9  useSelectivity.ts:288-292  stopAnalysis = polling 중단뿐 → S2
B10 useSelectivity.ts:175-180  receptor progress 가정 오류 → S5
B11 useSelectivity.ts:63-67  worst off-target max → S6
    ※ 1~2줄 fix: BE 응답의 offtarget_max_receptor 직접 사용
B12 selectivity.py:69-82  .pdb 업로드 수신, 내부 .cif 하드코딩
    ※ engineer-backend 정정: pipeline_local은 이미 _resolve_receptor_paths()로 구현됨.
       ai4sci-kaeri 옛 코드에만 해당.
B13 requirements.txt:1-14  python-multipart, Biopython 누락
    ※ engineer-backend 정정: conda env엔 이미 설치됨, 문서화 목적
B14 experiment.py:194  subprocess PIPE 미소비 → 실재 hang 위험
B15 unified_validation.py:309-315  placeholder passed=True → S7
B16 state.py:23-28 / status_emitter.py:30-33  경로 분기 (ROOT-1 반영)
```

### ENABLER 노드

```
E1  FE-BE 계약 명세 부재 (ROOT-3 원인) — OpenAPI spec에 approach 필드 없음
E2  통합 테스트 부재 — selectivity cancel / settings 반영 / approach 분기 E2E 없음
E3  requirements.txt 불완전 (B13 원인)
E4  AG_src/config/gate_thresholds.yaml의 부호가 pipeline_local 코드와 분기 (어제 Track A 통일 미반영)
```

---

## B. 패치 DAG v2.1 (v2 정정 후)

### v2 → v2.1 정정 사항

| 항목 | v2 | v2.1 정정 |
|---|---|---|
| state.py 패치 | P03 필요 | 이미 P1-2 적용됨, 제거 → 후처리만 |
| G-3 결정 | 필요 | "완료 처리"로 제거 |
| P02/P03 Tier | Tier 1 (P01 후) | P01과 독립적 → Tier 0로 재분류 |
| state.py:57-66 위치 인용 | "completed 무시" 위치 | App.tsx:66이 실제 위치 |
| G-5 Silo A | (b) Coming Soon | Silo A는 활성 유지, dual만 (b) 또는 regex 확장 |
| P09 범위 | runtime_settings 전체 연결 | llm_* 이미 구현됨, max_iter/n_cand/top_k 3개만 |
| P11 cancel | endpoint 추가 | endpoint + 도킹 루프 cancelled 체크포인트 별도 필요. soft cancel만 가능 |
| P12 _get_receptor_pdb | pipeline_local 필요 | pipeline_local은 이미 구현됨. ai4sci-kaeri 옛 코드만 |
| P14 worst off-target | 부호 통일 작업 | BE 응답값 직접 사용 1~2줄 |
| G-2 단위 | "+10 kcal/mol = 10^7-fold" | REU 단위 가능성, yaml 레이블 "kcal/mol"→"REU" 정정 필요 |

### DAG v2.1 토폴로지

```
완료 처리: G-3 (state.py 이미 P1-2 적용)

Tier 0 (병렬, 의존성 0): 8 패치
  P01  status_emitter.py:30-33 기본값 통일                          engineer-backend
       + start_monitoring.sh:85 경로 정리
       + ENVIRONMENT_FILE.md/UI_GUIDE.md/PIPELINE_GUIDE.md 문서

  P05  Candidate 타입 확장 → mapCandidate 보강 → ClusterPanel payload  reviewer-uiux + engineer-backend
       (순서 내부 강제: 타입 확장 선행)

  P06  runner.py:532-547,730 step01~05 "skipped" emit                 engineer-backend
       + baseline step06 → step06_baseline 분리
       + Stage 9 시나리오 시나리오 동기화

  P08  requirements.txt + experiment.py:194 subprocess DEVNULL        engineer-infra
       (DEVNULL 권장; daemon thread는 asyncio 혼용 위험)

  P09  experiment.py — max_iter/n_cand/top_k 3-way 폴백 추가          engineer-backend
       (llm_provider/model/base_url은 이미 구현됨, 추가 작업 없음)

  P11  selectivity.py — POST /selectivity/cancel/{job_id} 엔드포인트   engineer-backend
       + _run_selectivity_job 후보 루프 진입 시 cancelled 체크
       + 완료 job 409 반환
       + 변수명 _jobs (소문자) 정확히
       ※ soft cancel만 가능. subprocess timeout 대기는 별도 sprint

  P14  useSelectivity.ts:63-67 — BE 응답의 offtarget_max_receptor 사용  reviewer-uiux
       (1~2줄 수정. 가장 critical, 현재 데이터 오류 상태)

  P15  ValidationPanel.tsx 결과 행 dot에 skipped 회색 dot 추가         reviewer-uiux
       (기존 CheckRow의 MinusCircle 처리 활용)
       + aria-label="skipped"

Tier 1 (Popen 성공 후 write):
  P02  experiment.py — Popen 성공 직후 STATUS_FILE에 initializing write   engineer-backend
       + OSError try/except (실패해도 실험 시작 막지 않음)

  P03  state.py:read_status — 캐시 hit 후 후처리로 is_active_run, server_time 주입  engineer-backend

Tier 2 (P03 응답 활용):
  P04  App.tsx:66 isLive에 completed 반영                            reviewer-uiux
       + 배지 4종 (Live/Archive/Snapshot 또는 Completed/Stale) 명칭 결정
       + Stale 임계값 결정 (30s → 60s+ 권장)
       + aria-label 추가

결정 게이트 선행:
  P07 ← G-2  selectivity_margin_min 수치는 +10 유지, yaml 단위 레이블 "REU"로 정정
             AG_src yaml은 코드 동시 변경 필수, 코드 안 건드리면 yaml 그대로 유지

  P10 ← G-5  Silo A는 이미 활성, dual은 regex 확장 또는 비활성
             (a) regex r"^[abABdD]$" 확장 → --dual 호출
             (b) approach='dual' 차단 + Coming Soon UI

  P12 ← ai4sci-kaeri 옛 selectivity.py 동기화 여부 (pipeline_local은 이미 구현됨)

uvicorn 재기동: Tier 0+1 묶음 1회. Tier 2 FE는 HMR 즉시.
```

---

## C. 통합 회귀 시나리오 v2.1 — 13단계

| # | 시나리오 | 검증 방법 | 자동/수동 | 실패 시 |
|---|---|---|---|---|
| 1 | STATUS_FILE 경로 일치 | `stat /tmp/ag_pipeline_status.json /tmp/pipeline_local_status.json` 동일 | 자동 | P01 |
| 2 | BE `/api/status` 응답 즉시 갱신 | run 시작 후 1초 내 `jq .run_id` 갱신 | 자동 | P02 |
| 3 | `is_active_run`, `server_time` 응답 포함 | `jq '{is_active_run, server_time}'` | 자동 | P03 |
| 4 | FE Live 배지 + run_id prominent | React DevTools `isLive=true` | 수동 | P04 |
| 5 | runner step01~05 "skipped" emit | `jq .steps[0].status == "skipped"` | 자동 | P06 |
| 6 | iter 완료 후 동일 파일에 write | `jq .phase == "completed"` | 자동 | P01 |
| 7 | `completed=true` 시 `is_active_run=false` | `jq` 결합 | 자동 | P03 |
| 8 | FE Live → Completed 배지 전환 | UI 배지 확인 | 수동 | P04 |
| 9 | Cluster A~E 혼재 (E만 아님) | `jq '.results[].classification.cluster' \| uniq` | 자동 | P05 |
| 10 | Stop → BE cancel → 다음 후보 skip | `curl -X POST /api/selectivity/cancel/{job_id}` 200 + 완료 후보 수 확인 | 자동 | P11 |
| 11 | Settings 변경 → 다음 run에 반영 | `PUT /api/settings`로 max_iter 변경 → `POST /api/experiment/run` → BE 로그 max_iter 확인 | 자동 | P09 |
| 12 | approach='a' → Silo A 분기 실행 (G-5 활성 시) | BE 로그 `--no-approach-b` 플래그 확인 | 자동 | P10 |
| 13 | off-target worst BE/FE 동일 receptor | `response.offtarget_max_receptor == FE 표시 receptor` | 자동 | P14 |

자동 가능: 10건 / 수동: 2건 (#4, #8) / 미정: 1건 (subprocess hang 재현 조건 별도 정의)

---

## D. 위험·충돌 분석 v2.1

### 패치 간 충돌
- P02/P03 같은 파일 경로 작업이나 라인 다름, 충돌 없음
- P03 → P04 의존 (FE가 BE 새 필드 사용)
- P10(approach 분기) + P09(settings 폴백)이 같은 파일(experiment.py)이나 다른 함수 구간

### 다른 tmux 세션 영향
- 본 세션은 [[feedback_session_separation]] 컨벤션 준수 — 다른 세션 미커밋 변경에 손대지 않음
- P01 적용 후 uvicorn 재기동까지 split-brain 지속 (writer 신 / reader 신, 단 실행 중 run 있으면 이전 emitter가 옛 파일에 계속 쓸 수 있음)

### Stage 9 Rosetta-flow-test 영향
- P06이 runner.py:730의 `start_step("step06")` 명칭을 변경하면 Stage 9 dogfood 시나리오 검증 깨질 수 있음
- 동시 Stage 9 시나리오 업데이트 필요

### 단위 혼동 (G-2)
- yaml의 "kcal/mol" 레이블이 실제 REU일 가능성 → 보고서 인용 시 모두 단위 명시 필요
- 검증 트랙 VR-G2-01 (off-target 실측), VR-G2-02 (단위 레이블) 등록 필요

### Silo A 실동작 (G-8)
- BE는 `--no-approach-b`로 분기 구현됨, 그러나 RFdiffusion/ProteinMPNN 환경 정비 상태 미확인
- 실 호출 시 subprocess 실패 가능 → 사전 환경 체크 또는 try/except fallback 권장

---

## E. 패치 책임 분담 v2.1

| 패치 | 담당 | 사유 |
|---|---|---|
| P01 | engineer-backend | status_emitter.py + 문서 동시 (single owner) |
| P02 | engineer-backend | experiment.py 실행 흐름 |
| P03 | engineer-backend | state.py reader 응답 스키마 |
| P04 | reviewer-uiux | App.tsx 배지 + 명칭/임계 |
| P05 | reviewer-uiux + engineer-backend | 타입 확장 → BE schema 검증 → payload |
| P06 | engineer-backend | runner.py + Stage 9 시나리오 |
| P07 | reviewer-pharma + reviewer-math 승인 | yaml 단위 레이블 + (선택) AG_src 코드 동시 |
| P08 | engineer-infra | requirements + subprocess (인프라) |
| P09 | engineer-backend | runtime_settings 폴백 (단순) |
| P10 | engineer-backend (G-5 후) | regex 확장 또는 차단 |
| P11 | engineer-backend | cancel endpoint + _jobs lock |
| P12 | engineer-backend | ai4sci-kaeri 옛 코드 (선택) |
| P14 | reviewer-uiux | 1~2줄 hotfix, 가장 critical |
| P15 | reviewer-uiux | ValidationPanel dot + aria-label |

---

## F. 결정 게이트 v2.1

| ID | 결정 | 본 세션 권장 | 사유 |
|---|---|---|---|
| G-1 | writer 통일 방향 | **(A) 코드 + 문서 3건 동시** | start_monitoring.sh + docs/ 3개 |
| G-2 | margin 부호·임계·단위 | **수치 +10 유지 + 단위 레이블 "kcal/mol" → "REU" 정정** | reviewer-science: REU 단위, 통과율 73.5% (μ-0.66σ) |
| G-3 | pipeline_local 정식 | **완료 처리(제거)** | state.py 이미 P1-2 |
| G-4 | run_id 표준 | **`sst14_mutdock_{timestamp}`** | experiment.py:171 기존 |
| G-5 | Silo A/Combined | **Silo A 활성 + dual은 (a) regex 확장 또는 (b) Coming Soon** | Silo A는 구현됨 |
| G-6 | Stop semantics | **(a) cancel endpoint + soft cancel** | 즉시 cancel은 별도 sprint |
| G-7 | Validation placeholder | **(a) Skipped 뱃지 + dot** | 기존 처리 활용 |
| G-8 (신규) | Silo A 실동작 확인 | **다음 sprint** | G-5 후 실행 가능성 검증 |
| G-9 (신규) | off-target 실측 트랙 | **VR-G2-01/02 등록** | 단위 정정 + 1회 실측 |

---

## 변경 이력

- **2026-05-13 09:55** — reviewer-code v1 산출 (4 도메인 통합)
- **2026-05-13 11:18** — reviewer-code v2 산출 (v1 + Codex 10건 흡수)
- **2026-05-13 11:35** — 4 에이전트 정합성 검증 (v2의 4건 오류 식별, v2.1 정정)
- **2026-05-13 11:45** — EOD 시점, 사용자 승인 대기 중
