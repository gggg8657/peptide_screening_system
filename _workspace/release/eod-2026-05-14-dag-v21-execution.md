# EOD 2026-05-14 — DAG v2.1 실행 sprint (orchestrator 본 세션)

**세션 역할**: orchestrator (본 세션) — DAG v2.1 통합 분석 결과를 직접 패치로 풀어낸 실행 sprint
**세션 ID**: 80814a02-319f-456f-a212-0786206f2eee
**보조 EOD**: `eod-2026-05-14-orchestrator-session.md` (별도 세션 작성, 본 EOD와 별개)
**브랜치**: `main`
**작업 시간**: SOD(02:30경) ~ EOD(10:25경) ≈ 8h

---

## 0. 한눈에 보기

본 세션은 **DAG v2.1 통합 분석(어제 EOD)을 실행으로 옮긴 2 sprint**:

1. **Sprint 1 — DAG v2.1 Tier 0** (team `dag-v21-tier0`, 5 팀원, ~2.5h)
   - 8 패치: P01/P05/P06/P08/P09/P11/P14/P15
   - Live 회귀 PASS 9/FAIL 2/SKIP 2 (FAIL은 Tier 1 미적용 예상)

2. **Sprint 2 — Tier 1 + Cluster Data** (team `tier1-cluster-data`, 5 팀원, ~3h)
   - P02/P03/P04 + backend/pharmacophore.py 신규 + SS-bond Cys fix
   - Live 회귀 **PASS 10 / FAIL 0** / SKIP 2(수동) / 우회 PASS 1

3 git commit + 외부 에이전트 호출 12+회 + 통합 테스트 **170/170 PASS**.

---

## 1. 시간순 작업

### 1.1 SOD ~ 03:00
- 어제 EOD 산출물 확인 + 시스템 상태 점검
- stale task #25~29 정리
- 어제 미커밋 commit `d6b4119` (fix infra) + `1e8c4d0` (docs release) → push

### 1.2 03:00 ~ 03:30 결정 게이트
- G-1~G-9 일괄 권장값 채택
- 메모리 `[[feedback_external_agents_workflow]]` 신규 등록
- /team API 적극 활용 전환

### 1.3 03:30 ~ 06:30 Sprint 1 (dag-v21-tier0)

| 팀원 | 패치 | 핵심 변경 |
|---|---|---|
| be-status | P01+P09 | status_emitter 경로 통일(5 files) + 3-way 폴백(6 tests) |
| be-runner-cancel | P06+P11 | step01~05 skipped emit + step06_baseline 분리 + cancel endpoint(5 tests) |
| infra | P08 | requirements.txt + subprocess **로그 파일 redirect** (DEVNULL 아님, 디버그 가능성 우선) |
| fe-ux | P05+P14+P15 | Candidate 타입 + worst off-target hotfix + Skipped 뱃지 |
| reviewer | 검증 | 회귀 PASS 8/FAIL 2(예상)/SKIP 3 |

- commit `4343732` (20 files, +1805/-82) + push
- uvicorn 재기동(PID 1049155) + live 회귀 PASS 9/FAIL 2
- 팀 shutdown + TeamDelete

### 1.4 06:30 ~ 10:25 Sprint 2 (tier1-cluster-data)

| 팀원 | 작업 | 결과 |
|---|---|---|
| be-status-2 | P02 | 이미 구현됨(`_write_initializing_status`) 검증 14 tests |
| be-state | P03 | `_with_runtime_fields` + 캐시 hit 후 server_time 갱신, 14 tests |
| fe-isLive-2 | P04 | `pipelineStateFlags.ts` 순수함수 + 5 배지 + Claude design 4 산출물, WCAG 4.78:1, 76 tests |
| be-merger | BE 머지 + 신규 | pharmacophore.py 신규 + status.py `_enrich_candidates` + runner.py 5필드 머지 + **P2-1 SS-bond Cys fix** |
| reviewer-pharma | 정의 + 검증 | FWKT/chelator 공식 정의(문헌 인용) + Live 회귀 PASS 10/FAIL 0 |

- commit `6850c7c` (7 신규 파일, +1375) + push
- 통합 테스트 **170/170 PASS**
- 팀 shutdown 진행 중

### 1.5 사건 사고
- **be-status (Sprint 2)**: `claude.exe Permission denied`로 spawn 실패. be-status-2로 재spawn 성공.
- **fe-isLive (Sprint 2)**: 사용자가 pane에 직접 명령 입력해 종료. fe-isLive-2로 재spawn 성공.
- **uvicorn 1277240**: EOD 시점 외부 SIGTERM으로 종료 (별도 세션 추정).
- **별도 세션 origin/main 활동**: PR #27~#33 (6건) 머지. 본 세션 작업 일부(state.py, runner.py, cluster_report.py 등)가 별도 세션 PR과 통합되어 origin/main에 자동 push됨.

---

## 2. 회귀 시나리오 13단계 최종

| # | 패치 | Tier 0 (Sprint 1) | Tier 1 (Sprint 2) |
|---|---|---|---|
| 1 | P01 STATUS_FILE 경로 | ✓ | ✓ |
| 2 | P02 즉시 갱신 | — | ✓ |
| 3 | P03 is_active_run/server_time | ✗ | ✓ |
| 4 | P04 FE Live 배지 (수동) | ⏭ | ⏭ |
| 5 | P06 step skip emit | ✓ | ✓ |
| 6 | P01 동일 파일 write | ✓ | ✓ |
| 7 | P03 completed→is_active_run | ✓ | ✓ |
| 8 | P04 Live→Completed 전환 (수동) | ⏭ | ⏭ |
| 9 | P05 Cluster A~E 혼재 | ✗ | ✓ 우회 |
| 10 | P11 cancel endpoint | ✓ | ✓ |
| 11 | P09 Settings 폴백 | ✓ | ✓ |
| 12 | P10 approach 분기 | ✓ static | ✓ static |
| 13 | P14 worst off-target | ✓ | ✓ |

**최종: PASS 10 / SKIP 2(수동) / 우회 PASS 1 / FAIL 0**

---

## 3. 커밋 이력

| 커밋 | 메시지 | LOC |
|---|---|---|
| `d6b4119` | fix(infra): Ollama 11435 포트 + selectivity router test fixture | 3 files, +225/-2 |
| `1e8c4d0` | docs(release): 2026-05-13 EOD + LiveRun 통합 분석 v2.1 | 4 files, +864 |
| `4343732` | feat(dag-v21-tier0): LiveRun 8 패치 일괄 적용 | 20 files, +1805/-82 |
| `6850c7c` | feat(tier1-cluster-data): pharmacophore 모듈 + isLive 4-배지 + 통합 보고서 | 7 files, +1375 |

별도 세션이 본 세션 modified 코드(state.py, runner.py, cluster_report.py 등)를 PR #27~#33로 추가 머지함. 본 세션은 신규 파일만 commit.

---

## 4. 통합 테스트 170/170

```
backend/tests/test_pharmacophore.py          52/52
pyrosetta_flow/tests/test_cluster_report.py  65/65
pipeline_local/tests/test_pharmacology_guards.py  39/39
backend/tests/test_experiment_router.py      14/14
```

---

## 5. 다음 SOD 시작 시 할일 (남겨둔 작업)

### 5.1 High Priority

1. **uvicorn 재기동** — EOD 시점 죽음(외부 SIGTERM). 사용자가 UI 사용하려면 필요:
   ```bash
   cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
   OLLAMA_HOST=127.0.0.1:11435 PYTHONPATH=. nohup conda run --no-capture-output \
     -n bio-tools uvicorn backend.main:app --host 127.0.0.1 --port 8787 \
     > /tmp/uvicorn_8787.log 2>&1 &
   disown
   ```

2. **회귀 #4, #8 수동 검증** — React DevTools로 isLive 5 배지(Live/Stale/Archive/Completed/Mock) 시각 확인 + 새 run 시작/완료 전환 캡쳐. **사용자 수동**.

3. **G-5 Silo A 실 동작 확인 (G-8)** — BE는 `--no-approach-b` 분기 구현됨. RFdiffusion/ProteinMPNN 환경 정비 + dogfood 1회. 미동작 시 (b) Coming Soon 비활성 결정.

### 5.2 Medium (Sprint 후보)

4. **회귀 스크립트 #9 mock 개선** — realistic 후보(structural_rules + metal_coordination 포함)로 mock 강화.

5. **fwkt_contact Phase 2** — PDB 도킹 기반 4.5Å 거리 계산. 현재는 sequence-only substring 휴리스틱.

6. **fwkt_contact strict mode** — `seq[6:10]=="FWKT"` 옵션.

7. **G-2 yaml 단위 정정** — `pipeline_local/config/gate_thresholds.yaml`의 "kcal/mol" → "REU".

8. **`metal_coordination()` SS-bond Cys 제외 파라미터** — reviewer-pharma §검증 필요 등록. backend/pharmacology.py 수정.

### 5.3 Low

9. **chelator_site_available 세분화** — boolean → 필드 분리.

10. **VR-G2-01/02 검증 트랙 등록** — off-target 실측 + yaml 단위 검증.

### 5.4 보류

- Bayes/NSGA-II 최적화 통합 (메모리 `[[project_pipeline_local]]` TODO 9개)
- BE schema candidate 머지 (현재 on-the-fly `_enrich_candidates`로 우회)

### 5.5 별도 세션 책임 (본 세션 손대지 않음)
- `pipeline_local/*` modified 다수
- `tools/harness-adaptation/*` cursor-cli 추가
- `CLAUDE.md` 수정
- `_workspace/release/half-life-tool-evaluation`, `stability-panel-design`, `module-verification-2026-05-13` 등 다른 세션 산출물

---

## 6. 시스템 상태 (다음 SOD 시작점)

```
uvicorn :8787    : 죽음 (PID 1277240 SIGTERM, 재기동 필요)
Ollama :11435    : 가정상 가동 (PID 930000)
Vite dev server  : 가정상 가동
STATUS_FILE      : /tmp/pipeline_local_status.json (응급 cp 36h+ 유지)
최근 commit     : 6850c7c (origin/main 동기화됨)
미커밋          : 별도 세션 책임 (본 세션 손대지 않음)
```

---

## 7. 위험·블로커

- **다중 세션 동시 작업 복잡도**: 별도 세션이 origin/main에 본 세션 작업 자동 머지. git history multi-author 패턴. 메모리 `[[feedback_session_separation]]` + `[[feedback_external_agents_workflow]]` 컨벤션 유지 필요.

- **uvicorn 외부 종료**: 본 세션 결정 대기 중 SIGTERM. 재기동 시 위 §5.1 명령 참조.

- **be-merger Phase 1 휴리스틱**: reviewer-pharma 정의 받기 전 sequence-only 구현. Phase 2(5필드 머지)로 정정됨. 향후 SendMessage 동기 대기 메커니즘 개선 검토.

- **응급 cp 36h+ 유지**: `/tmp/pipeline_local_status.json`이 응급 복사 후 별도 갱신 없음 (uvicorn 재기동 후 새 run flush에서 자동 정상화).

---

## 8. 메모리 (오늘)

신규: `[[feedback_external_agents_workflow]]`

다음 SOD 검토 후보:
- `[[infra_uvicorn_external_signal]]` — 외부 SIGTERM 대응 패턴
- `[[project_dag_v21_completed]]` — Tier 0+1 완료, P02~P15 적용 상태

---

## 9. 산출물 (본 세션 책임)

| 파일 | 작성자 | 상태 |
|---|---|---|
| `_workspace/release/eod-2026-05-14-dag-v21-execution.md` | 본 EOD (orchestrator) | 신규 |
| `_workspace/release/tier1-cluster-data-execution-2026-05-14.md` | reviewer-pharma (Sprint 2) | commit `6850c7c` |
| `_workspace/release/tier1-cluster-data-pharma-defs-2026-05-14.md` | reviewer-pharma (Sprint 2) | commit `6850c7c` |
| `_workspace/release/dag-v21-tier0-execution-2026-05-14.md` | reviewer (Sprint 1) | commit `4343732` |
| `_workspace/release/dag-v21-tier0-regression-2026-05-14.sh` | reviewer (Sprint 1) | commit `4343732` |
| `backend/pharmacophore.py` | be-merger (Sprint 2) | commit `6850c7c` |
| `backend/tests/test_pharmacophore.py` | be-merger (Sprint 2) | commit `6850c7c` |
| `frontend/src/utils/pipelineStateFlags.ts` | fe-isLive-2 (Sprint 2) | commit `6850c7c` |
| `frontend/src/utils/__tests__/pipelineStateFlags.test.ts` | fe-isLive-2 (Sprint 2) | commit `6850c7c` |

---

**EOD 확정 시각**: 2026-05-14 10:25 KST (추정)
**팀 상태**: tier1-cluster-data shutdown 진행 중 (5 SendMessage 송신)
**다음 SOD 첫 액션**: §5.1 High Priority 3건 — uvicorn 재기동 + 회귀 #4·#8 수동 검증 + G-5/G-8 Silo A 동작 확인
