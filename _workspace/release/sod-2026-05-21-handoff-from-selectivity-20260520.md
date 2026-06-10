# SOD 2026-05-21 — Selectivity Session Handoff (from 2026-05-20)

> **목적**: 2026-05-20 selectivity-validation orchestrator 세션이 남긴 위임·발견·결정을 다음 세션 (Claude Code / Codex / Cursor 어느 도구든) 이 즉시 이어받을 수 있도록 정리.
>
> **전제 입력**:
> - `_workspace/release/eod-2026-05-20-selectivity-validation.md` (직전 EOD)
> - 본 SOD 의 §2 "진행 중 위임" 4 트랙

---

## 0. 한 줄 컨텍스트

본 세션 (5/20) 은 selectivity 5단 결함을 PR 4건 (#69/#70/#71/#82) 으로 정렬했고, **PRST-001~004 의 pepADMET binary_toxicity=1.0 이 OOD 외삽 아티팩트로 판정**되어 Gate-2 합성 발주는 "리스트 보존" 으로 축소·**pepADMET 재훈련 별도 트랙** 결정으로 닫혔다. 다음 세션은 진행 중 4 트랙 결과 수신 + 후보 작업 중 1개 선택으로 시작.

---

## 1. 환경 (이미 살아 있음)

| 자원 | 상태 |
|---|---|
| BE uvicorn (pid 62459) `127.0.0.1:8787` | LIVE (`bio-tools` conda env) |
| receptor data | 5/5 loaded — `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor/` (PR #69 머지로 정상) |
| GPU | H100 NVL ×4, `CUDA_VISIBLE_DEVICES=2` |
| conda env 후보 | `bio-tools`, `pepadmet` |
| `selectivity-validation-20260520` team | 9 명 위임 이력 보유, 일부 idle |
| origin/main HEAD | `a2139a3` (PR #82 머지) + 다른 세션 PR (#68/#72/#73/#74/#78/#79/#81/#83) |
| local main divergence | `4d3583c` (다른 세션 미푸시 P1/P2 sprint, **건드리지 말 것** — PR #68 에 내용 이미 포함됨) |

**즉시 검증 명령**:
```bash
curl -s http://127.0.0.1:8787/api/selectivity/receptors | python3 -m json.tool | head -20  # 5/5 loaded
git log --oneline origin/main -5
git status --short | head -10
```

---

## 2. 진행 중 위임 4 트랙 (Owner 별)

다음 세션은 우선 각 owner 의 mailbox / 결과를 확인하고 받지 못한 트랙은 ping.

### 2.1 `research` Task #3 — `rosetta_ddg_max` AG_src 단위 혼재 조사
- **출처**: be-fe-trace + backend G-2 분석 부산물
- **사실**: PR #79 가 `pipeline_local/config/gate_thresholds.yaml` 을 `498.4713 REU` 로 통일했으나, **`AG_src/config/gate_thresholds.yaml` 의 `-5.0 kcal/mol` 잔존** (단위 자체 다름)
- **요구 산출**: caller 매트릭스 + REU↔kcal/mol 동등성 분석 + 통일 권고
- **다음 세션 행동**: research 결과 도착 시 sources 합쳐서 PR 진행 결정 (또는 backend 위임 후속)
- **즉시 명령**:
  ```bash
  grep -rn "rosetta_ddg_max" AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/ pipeline_local/
  ```

### 2.2 `dock` Task #4 — PRST-001~004 변이 도킹 진단
- **사실**: 현재 PRST 4 후보의 pre-docked PDB 부재 → selectivity 가 항상 estimation. 1차 dock production 진입은 SST-14 baseline 자기참조 우연
- **요구 산출**: mutdock pipeline 실행 가능 여부 + 시간·GPU 견적
- **다음 세션 행동**: dock 결과 + 위 §4 pharma+bio 결론 종합. 실 변이 도킹 실행 여부 결정 (ADMET 위양성이라 합성 발주 안 한다면 우선도 LOW 로 떨어질 가능성)

### 2.3 `backend` Task #11 — 보완 PR (`pepadmet-guards-20260520`)
- **사실**: 위임 후 결과 미도착. 본 세션 종료 시점에도 idle 상태
- **요구 산출**: 새 worktree + PR (묶음 A: pharmacology_guards SS-bond 분기, 묶음 B: composite_scorer fallback WARN, 묶음 C: untracked ensemble_router/layer1_ensemble 통합 판단)
- **다음 세션 행동**: backend ping → PR 도착 시 tester 리뷰 → 머지

### 2.4 `research` Task #12 — pepADMET 재훈련 plan SOD
- **사실**: 위임 후 결과 미도착
- **요구 산출**: `sod-2026-05-20-pepadmet-retrain-plan.md` 신규 — 학습 데이터 큐레이션, 재훈련 전략 비교, 메트릭, 일정·자원 견적
- **다음 세션 행동**: SOD 도착 → 사용자 검토 → 실 재훈련 진행 결정

---

## 3. 다음 세션 1순위 후보 (우선순위)

| 후보 | 출처 | 권고 우선도 | 비고 |
|---|---|---|---|
| 진행 중 4 트랙 결과 수신·정리 | §2 | **P0** (필수) | ping → 결과 → 결정 |
| pipeline_local · vLLM · UI 점검 v1.2~ | 사용자 IDE 열린 `docs/pipeline_local_vllm_ui_inspection_plan.md` (P1-2 vLLM 스모크, P1-3 자동 테스트, P2 UX) | **P1** | v1.1 까지 일부 구현됨, 잔여는 명확 |
| pepADMET 재훈련 실행 (Task #12 plan 검토 후) | 본 EOD §3 결정 | P1 (시간 큼) | data curation + transfer learning + 검증 |
| In vitro RBC hemolysis assay 발주 | pharma+bio 권고 | P2 (사용자 결정) | 외부 외주 vs 내부 lab |
| AG_src `rosetta_ddg_max` 단위 통일 PR | Task #3 결과 후 | P2 | research 결과 의존 |
| `pipeline_local/scoring/ensemble_router.py`·`layer1_ensemble.py` 정착 | codex 산출 (untracked) | P2 | backend Task #11 에 흡수 시도 중 |
| `qc_ranker.py` `datetime.utcnow()` DeprecationWarning | tester PR #82 §부수 | P3 | 1 라인 |
| Boltz complex 로 PRST-001 ΔG 재산출 | 어제 EOD §12 #3 | P3 | V-A09-06 부분 해소 |

---

## 4. 다른 세션 좌표 (충돌 회피 — 반드시 점검)

본 세션이 진단한 다른 세션 상태 (2026-05-20 ~07:00 기준):

| 세션 | 도구 | 활동 | 본 세션 영향 |
|---|---|---|---|
| 28 (claude-swarm) | Claude Code orchestrator | 본 세션 (이제 종료) | — |
| 23 pane1 | be-binding-api | main cherry-pick 진행 중 | main divergence 가능성 — `git log origin/main -10` 으로 확인 |
| 23 pane0 | infra 메모 | "SOD §0 infra 재실행 최우선" — 어제 P2 sprint 잔여 | PR #68 으로 해결됨, 추가 작업 가능성 LOW |
| 13 | Cursor Composer | 동일 브랜치 `chore/fix-receptor-symlink-20260520` 18 files edited, Q&A 모드 | PR #69 머지로 origin 브랜치 삭제. 세션 13 이 push 시도해도 GitHub 거부. 자체 수렴 |
| 17 | Cursor Composer | 동일 브랜치 IDLE | 동일 |
| 20 | Claude Code | `/manual-selectivity` FE 검증 | 선택성 도구 — 본 세션 작업 영향 0 |
| 26 | Claude Code | Fab-ADMET URL 조사 (researcher 위임 직전) | A-03 후속, 별개 |
| 24/25/12 | PyBAMM_Inverse | 배터리 ML, 다른 프로젝트 | 무관 |

**원칙**: 다른 세션이 진행 중인 commit/PR 가로채기 금지. 충돌 발견 시 → 본 세션 작업 격리 (worktree) → 사용자 결정 받기.

---

## 5. 운영 결정 명시 (사용자 2026-05-20)

- **Gate-2 실외주 합성 발주 안 함** — `runs_local/final_candidates/synthesis_orders/PRST-00{1..4}.md` 리스트만 보존
- **pepADMET 재훈련 + 재평가** — plan 단계 (Task #12), 실 재훈련은 plan 검토 후
- **In vitro hemolysis assay** — pharma+bio 권고했으나 사용자 결정 미정 (다음 세션에서 RI팀·서호성 박사 협의 필요)

---

## 6. 본 세션 (5/20) 머지 PR 4건

| PR | merge commit | 한 줄 |
|---|---|---|
| #69 | `fdf2769` | git index helloworld symlink → 실 디렉토리 (root-cause) |
| #70 | `e6dc7de` | D+B 가드 (estimation_fallback warning) |
| #71 | `45357aa` | G-1 cid format fix (iter*_cand* 키) |
| #82 | `a2139a3` | G-2 margin sign convention — yaml SSOT 양수 컨벤션 단방향 정렬 |

---

## 7. 다음 세션 시작 즉시 점검 (1 분)

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr

# 1. main 상태 + divergence
git fetch origin && git log --oneline origin/main..HEAD; git log --oneline HEAD..origin/main

# 2. BE health
curl -s http://127.0.0.1:8787/api/selectivity/receptors | python3 -c "import sys,json; r=json.load(sys.stdin)['receptors']; [print(k, v['loaded']) for k,v in r.items()]"

# 3. 진행 중 worktrees
ls -la .worktrees/ 2>/dev/null

# 4. 본 세션 위임 결과
ls _workspace/55_*.md _workspace/release/sod-2026-05-20-pepadmet-retrain-plan.md 2>/dev/null
```

위 4 명령 결과 정상이면 §2 의 위임 4 트랙 ping 또는 §3 의 후보 1개 선택으로 시작.

---

## 8. 컨벤션 (필독)

CLAUDE.md `feedback_session_separation` 메모:
- 본 세션 (orchestrator) vs 별도 세션 (team-mate): EOD/SOD 명명 + PR 의무 + **다른 세션 미커밋 변경 손대지 않음**
- 본 SOD 는 다음 세션 (도구 무관) 이 이어받을 입력 — 명령어·경로·결정 사실만 적었음. 다음 세션이 추가 발견·결정 시 새 SOD 또는 EOD 로 분기.

---

## 변경 이력

| 버전 | 작성 | 비고 |
|---|---|---|
| 1.0 | 2026-05-20 orchestrator (Opus 4.7) 세션 종료 직후 | handoff |
