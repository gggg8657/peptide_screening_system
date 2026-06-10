# EOD 2026-05-13 — orchestrator-session

**세션 역할**: orchestrator (본 세션) — 업무 분장·취합·의사결정·EOD 작성
**세션 ID**: 80814a02-319f-456f-a212-0786206f2eee
**브랜치**: `main` (작업 중)
**작업 시간**: SOD(07:00경) ~ EOD(11:40경) ≈ 4.5h

---

## 1. 오늘 본 세션이 진행한 작업 (시간순)

### 1.1 어제 Track A/B/C 후속 검증 (07:00~08:00)
- 어제 적용한 Track A(Selectivity 데이터 흐름 4파일) + Track B(Critic 매핑 1파일) 결과 회귀 검증
- 신규 테스트: `test_selectivity_router.py` 14/14, `test_critic_normalization.py` 27/27
- 회귀 테스트: `test_step05b_selectivity.py` 26/26 PASS
- `tests/test_selectivity_router.py`의 fixture 1건이 backend 패키지 stub 문제로 실패 → monkeypatch 방식으로 정정 (본 세션 직접 수정)

### 1.2 Ollama 포트 불일치 진단·수정 (08:00~08:30)
- pipeline_config.yaml의 base_url 11434 vs 실제 OLLAMA_HOST=11435 (사용자가 5/11 13:17 띄운 인스턴스) 발견
- 수정 1: `AG_src/config/pipeline_config.yaml:223` `11434 → 11435`
- 수정 2: `backend/routers/experiment.py:135-139` `OLLAMA_HOST` env 인식 로직 추가
- 백엔드 graceful kill (PID 2232367/2232386) + 재기동 (PID 3762672, OLLAMA_HOST env 주입)
- `/api/experiment/models` 응답 확인 → qwen3:8b 포함 8개 모델 정상 노출

### 1.3 Silo B 라이브런 (08:00~08:51, 사용자가 UI에서 시작)
- run_id: `sst14_mutdock_1000`
- 5 iter 정상 종료, 41 candidates + historical 200, top ddG **-49.635** (iter03_cand003)
- `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_05/08_reports/`에 critic_report.json/rank_table.csv/summary.md/iteration_manifest.json/planner_report.json 모두 생성
- Ollama qwen3:8b가 실제 호출되어 critic 동적 분석 산출

### 1.4 LiveRun UI 무동작 진단·통합 분석 (09:00~11:30)
사용자 질문 "라이브런에 안 보이는데? 더미 같다" → 다단계 분석:

**Phase 1 — STATUS_FILE 분기 발견**
- `/tmp/ag_pipeline_status.json` (08:51 갱신, 진행 데이터) ← orchestrator가 쓰는 곳
- `/tmp/pipeline_local_status.json` (어제 05:45 stale) ← backend가 읽는 곳
- 원인: P1-2(05-13) 패치가 reader만 변경, writer는 미변경

**Phase 2 — 4 도메인 fan-out 분석 (engineer-backend × 2, reviewer-uiux, reviewer-code)**
- Domain 1: STATUS_FILE 통합 — writer 1줄 변경 권장
- Domain 2: step emitter 매핑 — runner.py step skip emit 부재
- Domain 3: LiveRun UI 흐름 — App.tsx isLive 판정이 completed 무시
- Domain 4: 두 파이프라인 컨벤션 차이 — C-06 selectivity margin 부호 반전 [CRITICAL]

**Phase 3 — 사용자 지적 "이게 왜 도메인 통합?" → reviewer-code 단일 재통합 (v1)**
- ROOT × SYMPTOM × INDEPENDENT BUG × ENABLER 구조로 인과 그래프 + DAG + 회귀 시나리오 + 결정 게이트 산출

**Phase 4 — Codex BE/FE 전체 리뷰 (gpt-5.4, 218초, 156k tokens)**
- 10 findings (P0 × 3, P1 × 5, P2 × 2)
- 신규 발견: Stop semantics 결함, Settings ↔ 실행 단절, Silo A/Combined approach 무시, off-target worst min/max 역전, requirements 누락, subprocess PIPE 미소비, Validation placeholder

**Phase 5 — 통합 v2 (Codex + v1 흡수, reviewer-code)**
- ROOT 2 → 4 (FE-BE 계약 부재 + 의존성 누락 추가)
- SYMPTOM 1 → 7
- BUG 5 → 15
- 패치 7 → 15
- 결정 게이트 4 → 7

**Phase 6 — v2 정합성 검증 4 에이전트 병렬 (reviewer-code, engineer-backend, reviewer-uiux, reviewer-science)**
- 결과: **CONDITIONAL** — 핵심 버그 식별 정확, 단 4건의 v2 오류 발견

### 1.5 응급 처치 (10:18경)
- `cp /tmp/ag_pipeline_status.json /tmp/pipeline_local_status.json` 1회
- 효과 확인: `/api/status`가 sst14_mutdock_1000 + 41 candidates 정상 응답

---

## 2. 핵심 산출물 (영구 기록)

| 파일 | 내용 |
|---|---|
| `_workspace/release/liverun-integration-analysis-v2-2026-05-13.md` | 통합 v2 분석 + v2.1 정정안 (인과 그래프, DAG, 회귀 시나리오) |
| `_workspace/release/v2-validation-cross-check-2026-05-13.md` | 4 에이전트 정합성 검증 결과 (v2의 4건 오류 식별) |
| `_workspace/release/codex-be-fe-review-2026-05-13-findings.md` | Codex 10 findings 원문 보존 |
| `/tmp/uvicorn_8787.log` | 백엔드 재기동 후 로그 (휘발성, /tmp 재부팅 시 사라짐) |
| `logs/external_agents/codex_20260513_110724_365423.jsonl` | Codex 호출 raw 트랜스크립트 |

---

## 3. 본 세션이 직접 만든 코드 변경 (미커밋, 본 세션 책임)

```
AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/config/pipeline_config.yaml
  → llm.base_url: 11434 → 11435  (1줄)

AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/experiment.py
  → list_models()에 OLLAMA_HOST env 인식 (3줄, os 모듈 기존 import 활용)

AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/tests/test_selectivity_router.py
  → _patch_backend_state fixture를 monkeypatch 방식으로 정정 (8줄)
```

**커밋 방식 권장**: 다음 SOD에 본 세션이 단일 commit으로 — 메시지 예시 "fix(infra): Ollama 11435 + selectivity router test fixture (orchestrator-session)". 다른 세션이 만든 변경(어제 Track A/B 결과 등)은 손대지 않음.

---

## 4. 미결 결정 게이트 (다음 SOD 즉시 확정 필요)

v2.1 정정 후 최종 게이트:

| ID | 결정 | 본 세션 권장 | 사유 |
|---|---|---|---|
| G-1 | writer 통일 방향 | **(A) 코드 + 문서 3건** | `start_monitoring.sh` + `ENVIRONMENT_FILE.md`/`UI_GUIDE.md`/`PIPELINE_GUIDE.md` 동시 수정 |
| G-2 | margin 부호·임계·단위 | **+10.0 유지 + 단위 레이블 "kcal/mol"→"REU" 정정** | reviewer-science: REU 단위 혼동, +10 통과율 73.5% (μ-0.66σ) 합리적 |
| G-3 | pipeline_local 정식 | **완료 처리(제거)** | state.py 이미 P1-2 적용됨 |
| G-4 | run_id 표준 | **`sst14_mutdock_{timestamp}`** | experiment.py:171 기존 사용 |
| G-5 | Silo A/Combined 방향 | **Silo A 활성 유지 + Combined(dual)만 regex 확장 또는 비활성** | Silo A는 이미 `--no-approach-b`로 구현됨, dual만 차단 |
| G-6 | Stop semantics | **(a) cancel endpoint + soft cancel** | 즉시 cancel은 SelectivityRunner PID 노출 별도 sprint |
| G-7 | Validation placeholder | **(a) Skipped 뱃지** | ValidationPanel.tsx의 CheckRow에 이미 처리 구현됨, dot만 추가 |
| G-8 (신규) | Silo A 실동작 확인 | **다음 sprint** | G-5 후 실제 실행 가능성 검증 후 비활성 여부 재결정 |
| G-9 (신규) | off-target 실측 트랙 등록 | **VR-G2-01/02 등록** | 단위 정정 + 1회 실측 후 임계값 재조정 |

---

## 5. 패치 DAG v2.1 (확정 — 다음 SOD 즉시 디스패치 가능)

```
Tier 0 (병렬, 의존성 0): 8 패치
  P01  status_emitter 경로 + start_monitoring.sh + 문서 3개         engineer-backend
  P05  Candidate 타입 확장 → mapCandidate 보강 → ClusterPanel payload  reviewer-uiux + engineer-backend
  P06  runner.py step skip emit + step06 분리                       engineer-backend
  P08  requirements.txt + subprocess DEVNULL                        engineer-infra
  P09  max_iter/n_cand/top_k 3-way 폴백 (llm_* 이미 구현됨)          engineer-backend
  P11  selectivity cancel endpoint (soft, _jobs 변수명, 409 처리)    engineer-backend
  P14  FE _mapCandidates에서 BE의 offtarget_max_receptor 사용 (1~2줄)  reviewer-uiux
  P15  ValidationPanel skipped 뱃지 + dot                            reviewer-uiux

Tier 1 (Popen 성공 후 write):
  P02  experiment.py run 시작 후 status 즉시 초기화                  engineer-backend
  P03  read_status 후처리에 is_active_run, server_time              engineer-backend

Tier 2 (P03 응답 활용):
  P04  App.tsx isLive에 completed 반영 + 배지 4종 명칭/임계 결정     reviewer-uiux

결정 게이트 선행:
  P07 ← G-2 (수치 +10 유지, yaml 단위 레이블 정정)
  P10 ← G-5 (Silo A 유지, dual regex 확장/비활성)
  P12 ← ai4sci-kaeri 옛 selectivity.py 동기화 (pipeline_local은 구현됨)

uvicorn 재기동: 1회 (Tier 0+1 묶음 적용 후). FE는 HMR 즉시.
```

---

## 6. 통합 회귀 시나리오 v2.1 (13단계, 다음 SOD 적용 후 검증)

| # | 시나리오 | 검증 방법 | 실패 시 |
|---|---|---|---|
| 1 | STATUS_FILE 경로 일치 | `stat /tmp/{ag,pipeline_local}_pipeline_status.json` | P01 |
| 2 | /api/status가 새 run 반환 | `curl /api/status \| jq .run_id` | P01+P02 |
| 3 | is_active_run + server_time 응답 | `jq '{is_active_run,server_time}'` | P03 |
| 4 | FE Live 배지 + run_id prominent (수동) | DevTools | P04 |
| 5 | runner step01~05 "skipped" emit | `jq .steps[0].status` | P06 |
| 6 | iter 완료 후 same 파일에 write | `jq .phase` | P01 |
| 7 | completed=true, is_active_run=false | `jq` 결합 | P03 |
| 8 | FE Live → Completed 전환 (수동) | UI 배지 | P04 |
| 9 | Cluster A~E 혼재 (E만 아님) | `letter != 'E'` | P05 |
| 10 | Stop → BE cancel → 다음 후보 skip | `curl /api/selectivity/cancel/{job_id}` 200 | P11 |
| 11 | Settings 변경 → 다음 run에 반영 | PUT settings → POST run → max_iter 확인 | P09 |
| 12 | approach='a' → Silo A 분기 실행 | BE 로그 확인 (G-5 활성 시) | P10 |
| 13 | off-target worst BE/FE 동일 | response.offtarget_max_receptor 비교 | P14 |

---

## 7. 외부 에이전트 호출 기록

| 시각 | 에이전트 | 작업 | 결과 |
|---|---|---|---|
| 07:24 | engineer-backend × 2 | Track A(selectivity 흐름) + Track B(critic 매핑) | 완료, 14+27+26 tests PASS |
| 09:18 | engineer-backend × 2 + reviewer-uiux + reviewer-code | 4 도메인 분석 (STATUS_FILE/step emitter/UI 흐름/컨벤션) | 4 결과 수신 |
| 09:55 | reviewer-code | LiveRun 통합 v1 | 인과 그래프 + DAG + 회귀 시나리오 + 결정 게이트 |
| 11:07 | codex (gpt-5.4) | BE/FE 전체 리뷰 | 10 findings, 218초, 156k tokens, log `codex_20260513_110724_365423.jsonl` |
| 11:18 | reviewer-code | 통합 v2 (v1 + Codex 10건 흡수) | ROOT 4, BUG 15, 패치 15, 게이트 7 |
| 11:35 | reviewer-code + engineer-backend + reviewer-uiux + reviewer-science | v2 정합성 검증 4 에이전트 | 4건 v2 오류 발견, CONDITIONAL 판정 |

총 외부 에이전트 호출: 12회 (서브에이전트 11 + Codex 1)

---

## 8. 다음 SOD 시작 지점 (체크리스트)

1. **본 세션 미커밋 변경 commit + push**
   - pipeline_config.yaml 11435
   - experiment.py OLLAMA_HOST
   - test_selectivity_router.py monkeypatch
   - 메시지 예시: `fix(infra): Ollama 11435 포트 정렬 + selectivity router test fixture (orchestrator-session)`

2. **결정 게이트 G-1~G-9 사용자 일괄 확정 받기**
   - 본 세션 권장값으로 OK인지 / 어디 다르게 결정

3. **DAG v2.1 Tier 0 패치 병렬 디스패치**
   - 8 패치 → engineer-backend × 5 + reviewer-uiux × 3 + engineer-infra × 1

4. **Tier 1+2 순차 적용 → uvicorn 1회 재기동**

5. **회귀 시나리오 13단계 자동/수동 검증**

6. **응급 cp는 P01 적용까지 일회용** — 새 emitter flush 발생 전 P01 들어가야 재분기 방지. 만약 다음 SOD까지 cp가 무너졌으면 동일하게 1회 더 실행.

---

## 9. 시스템 상태 스냅샷 (다음 SOD에서 즉시 확인 가능)

```
백엔드 uvicorn:    PID 3762672, 127.0.0.1:8787, OLLAMA_HOST=127.0.0.1:11435 env
Ollama:            PID 930000, 127.0.0.1:11435, qwen3:8b 가동
Vite dev server:   PID 65891, 2225859 (2개 인스턴스, HMR 가동)
STATUS_FILE:       /tmp/pipeline_local_status.json (응급 cp 후 116KB)
최근 run:          sst14_mutdock_1000, 5 iter 완료, top ddG -49.6 REU
미커밋 변경:        본 세션 3건 (위 §3) + 다른 세션 다수 (손대지 않음)
```

---

## 10. 위험·블로커

- **응급 cp 휘발성**: 다음 emitter flush(다음 run 시작 시) 발생하면 STATUS_FILE 재분기. **P01 적용 전 새 run 시작 금지** 권장.
- **선택성 데이터 단위 혼동**: yaml의 "kcal/mol" 레이블이 실제 REU일 가능성. 의사결정·보고서 인용 시 단위 명시 주의.
- **Silo A 실동작 미확인 (G-8)**: BE는 `--no-approach-b` 분기 코드가 있으나 실제 RFdiffusion/ProteinMPNN 환경 정비 상태 미확인. SiloAPage Run 버튼 호출 시 실패 가능.
- **Codex P0/P1 일부는 pipeline_local 버전엔 이미 해결됨** (P12, P09의 llm_* 부분, _resolve_receptor_paths 등). 패치 대상이 `ai4sci-kaeri/` 옛 코드인지 `pipeline_local/` 신 코드인지 매번 확인.

---

## 11. 참고 — 별도 세션이 진행한 작업 (본 세션 미커밋 변경에 손대지 않음)

git status에 보이는 다른 미커밋 파일들은 모두 별도 세션 또는 어제 작업 결과:
- `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/agents/critic.py` (어제 Track B)
- `backend/routers/selectivity.py`, `frontend/src/hooks/useSelectivity.ts` 등 (어제 Track A)
- `pipeline_local/*` 다수 (별도 세션 작업)

본 세션은 이들을 검토만 했고 수정하지 않음. 각 세션이 직접 commit/PR.

---

## 12. 메모리 업데이트 후보 (다음 SOD에서 검토)

- [[infra_ollama_port_11435]] — Ollama가 표준 11434가 아닌 11435에서 가동됨. CUDA_VISIBLE_DEVICES=2,3 (메모리의 GPU=2와 약간 다름)
- [[project_status_file_split]] — `/tmp/{ag_,pipeline_local_}pipeline_status.json` 분기 문제 (P01 적용 시 해결)
- [[feedback_units_REU_vs_kcal]] — yaml의 "kcal/mol" 레이블 잘못, 실제 REU 가능성 (G-2 정정 후 업데이트)

---

**EOD 확정 시각**: 2026-05-13 11:45 KST (추정)
**다음 SOD 우선순위**: G-1~G-9 일괄 결정 → DAG v2.1 디스패치 → uvicorn 1회 재기동 → 회귀 13단계 검증
