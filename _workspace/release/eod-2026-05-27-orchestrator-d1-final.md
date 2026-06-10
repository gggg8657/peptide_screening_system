# EOD — 2026-05-27 (수, D-1) orchestrator 세션 final (PR 머지 + phase1 재실행 + vLLM 가동)

> **세션 명명**: orchestrator (본 세션) — final 갱신
> **시작**: 2026-05-27 05:00 KST
> **마침**: 2026-05-27 ~12:35 KST
> **선행 EOD**: `_workspace/release/eod-2026-05-27-orchestrator-d1-system-audit.md` (09:50 시점, 작업 산출물 + 5/28 체크리스트)
> **본 EOD**: 09:50 이후 추가 작업 + PR 머지 3건 + 781 PASS 회귀 baseline + vLLM 가동
> **회의**: 2026-05-28 (목) KAERI-AIRL-MOM-2026-004 (예정)
> **다음 세션 핸드오프**: 본 EOD §6 체크리스트로 5/28 회의 진행

---

## 1. 09:50 이후 한 줄

선행 EOD 작성 후 PR 4건 분리 push → PR #122/#124/#125 main 머지 → phase1 재실행으로 781 PASS 달성 (SSTR2 symlink + Boltz 실 호출 4건 추가) → vLLM `deepseek-r1-distill-32b` GPU 3에 가동 → 5/28 시연 환경 main 기준으로 완전 준비됨.

---

## 2. PR 머지 결과 (오전 11:30 ~ 12:30)

| # | 제목 | main commit | 상태 |
|---|------|-------------|------|
| #122 | `fix(be)`: P0 부팅 실패 복구 — llm_benchmark optional + /api/health 식별자 | **`fc5e15b`** | ✅ MERGED 11:31 UTC |
| #124 | `docs(meeting)`: 5/28 회의 발표자료 v3 — narrative + PPTX 26슬라이드 | **`156fa3b`** | ✅ MERGED |
| #125 | `docs(audit)`: D-1 시스템 전체 점검 Phase 0~5 + 시연 시나리오 + EOD + phase1 재실행 | **`67129bb`** | ✅ MERGED 12:30 UTC |
| #123 | `feat(tools)`: 세션 통합 보고 스크립트 + /report 슬래시 | — | 🟡 **OPEN** (5/28 회의 후 머지 권장) |

main 최신 5 commits:
```
67129bb docs(audit): D-1 시스템 전체 점검 Phase 0~5 + 시연 시나리오 + EOD + phase1 재실행 (#125)
156fa3b docs(meeting): 5/28 회의 발표자료 v3 — narrative + PPTX 26슬라이드 (박사 청자 톤) (#124)
fc5e15b fix(be): P0 부팅 실패 복구 — llm_benchmark optional + /api/health 식별자 (#122)
0a8bed6 docs(meeting): Schrödinger 도입 검토 의제 추가 — 슬라이드 21 + MEETING_PREP Q9 (D-2) (#119)
0d2fe3f docs(midcheckup): 5/27 중간 점검 deck 3 버전 — V1/V2/V3 비교용 (#118)
```

---

## 3. Phase 1 재실행 결과 — 781 PASS 회귀 baseline 확정

선행 EOD에서는 777 PASS / 5 skip / 2 xfail. **재실행으로 4 skip 해제 → 781 PASS / 1 skip / 2 xfail.**

| 컴포넌트 | 결과 | 시간 |
|---------|------|------|
| `pipeline_local` | **740 PASS** / 1 skip / 2 xfail / 0 fail | 199.3 s |
| `pipelines/silo_a` | 9 PASS | 0.20 s |
| `pipelines/silo_b` | 32 PASS (Pydantic 경고 82건) | 0.61 s |
| **총합** | **781 PASS / 0 fail / 0 error** | ~200 s |

### 4 PASS 추가 사유

`pipeline_local/tests/test_offtarget_dock_boltz.py:49`가 SSTR2 PDB를 다음 3 경로에서 찾음. 본 세션이 **코드 수정 없이 데이터 alias만** 추가:

```bash
cd runs_local/selectivity_demo_20260511/alphafold_receptors
ln -sf AF-P30874-F1-model.pdb SSTR2.pdb
ln -sf AF-P30874-F1-model.pdb AF-P30874-F1-model_v4.pdb
ln -sf AF-P30874-F1-model.pdb sstr2.pdb
```

(AF-P30874 = SSTR2 UniProt ID, 동일 구조)

→ 4 skip 해제 + 각 Boltz 실 호출 30~40초 발생 (시간 60→199초).

### 남은 1 skip + 2 xfail (모두 정당)

- **SKIPPED 1**: `test_flexpep_dock_wrapper.py:242` — "SSTR2.pdb 이미 생성됨" (의도적)
- **XFAIL 1**: `test_daa_dota_conflict_detected` — `modification_conflict.py` 통합 필요 (Phase 5 **P0**)
- **XFAIL 2**: `test_batch_compute_exists` — `batch_compute_stability` 함수 부재 (Phase 5 **P3**, 정확성 영향 0)

자세한 사유와 회귀 baseline 명령: `_workspace/release/phase1-module-tests-2026-05-27.md`

---

## 4. vLLM 가동 — GPU 3 / port 8002

5/28 시연 + 향후 pipeline_local Planner agent 호출용:

```bash
MODEL_PATH="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"
CUDA_VISIBLE_DEVICES=3 nohup conda run --no-capture-output -n vllm-server \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1-distill-32b" \
    --host 127.0.0.1 --port 8002 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
  > /tmp/vllm_8002.log 2>&1 &
disown
```

**검증**:
- `/health` → HTTP 200
- `/v1/models` → `{"id": "deepseek-r1-distill-32b", "owned_by": "vllm"}`
- GPU 3 점유 83,467 MiB / 95,830 MiB
- 모델 로드 시간 약 3분 (32B bfloat16)

**종료 명령** (회의 후 또는 GPU 회수 필요 시):
```bash
pkill -f "vllm.entrypoints.openai.api_server.*port 8002"
```

---

## 5. GPU 현황 (D-Day 직전)

| GPU | 메모리 | 점유 |
|-----|-------:|------|
| 0 | 14 MiB | 타인 idle (손대지 말 것) |
| 1 | 14 MiB | 타인 idle (손대지 말 것) |
| 2 | 14 MiB | **본인 가용** (시연 중 Silo B PyRosetta 단건 호출용) |
| 3 | 83,467 MiB | 본인 vLLM (deepseek-r1-distill-32b) |

`CUDA_VISIBLE_DEVICES=2,3` 표준.

---

## 6. 5/28 회의 D-Day 직전 체크리스트 (갱신)

### 회의 30분 전
- [ ] `git pull origin main` — 본 작업 트리에서 main 최신 확보 (commit `67129bb`까지)
- [ ] BE 부팅:
  ```bash
  cd ~/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
  source ~/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --log-level info
  ```
- [ ] BE `/api/health` 응답에 `service: "ai4sci-kaeri-backend"` 확인
- [ ] FE `npm run dev` 부팅 + `/console` 화면 진입
- [ ] **vLLM `/health` HTTP 200 확인** (이미 가동 중)
- [ ] PPTX 26슬라이드 열어 Slide 17 ⚠ 정직 슬라이드 + Slide 21 슈뢰딩거 모듈 표 확인
- [ ] `runs_local/dual_final_03/local_20260402_1055_iter01/` 접근 가능 확인
- [ ] Silo B PyRosetta 단건 명령 dry-run (`demo-scenario-2026-05-28.md §시연 흐름 Step 3`)
- [ ] 다른 사용자 GPU 0/1 점유 확인 (`nvidia-smi`) — 손대지 말 것

### 회의 5분 전
- [ ] 백업 시나리오 A/B/C 점검 (PPTX 단독 진행도 가능한 상태)
- [ ] 시연 절대경로 메모지 준비 (`demo-scenario-2026-05-28.md` 부록)

### 회의 진행 시
- [ ] §7 의사결정 5건 + 추가 1건(reviewer-pharma 권고: Ki/serum/hemolysis assay 담당 기관)
- [ ] 다음 회의 일자 합의

---

## 7. 5/28 회의 직후 본 세션 첫 작업

1. **EOD 신설** (`eod-2026-05-28-meeting.md`) — 의사결정 결과 + Q&A 기록
2. **PR #123 (도구) 머지** — 시연 후 가벼운 머지
3. **P0 리팩토링 착수 결정** — 5/29 새 세션에서 P0 작업
4. **vLLM 종료 여부 결정** — 시연 종료 후 GPU 3 회수할지
5. **SSTR2 symlink 영구성** — 본 phase1에서 만든 symlink 3개를 다음 PR로 commit할지, 또는 코드 수정 (`_SSTR2_PDB_CANDIDATES`에 기존 경로 추가)으로 대체할지

---

## 8. 오늘 main에 들어간 변경 종합

| commit | 의미 | 본 세션 |
|--------|------|---------|
| `fc5e15b` | BE P0 fix (시연 가능 상태 복원) | ✅ |
| `156fa3b` | 회의 자료 v3 (narrative + PPTX 26슬라이드 + 3-Layer 코드 격차 분석) | ✅ |
| `67129bb` | D-1 시스템 점검 (Phase 0~5 + 시연 시나리오 + 선행 EOD + phase1 재실행 + PDB 4) | ✅ |
| (PR #123 OPEN) | 세션 보고 도구 (`/report` 슬래시 + `session_report.sh`) | 🟡 |

총 main 변경 (오늘): **약 16 files, +5,500 / -160 lines**

---

## 9. 본 세션 외부 위임 사용 통계 (참고)

| 도구 | 호출 수 | 누적 시간 | 산출물 |
|------|--------:|---------:|--------|
| `/codex exec` | 4회 | 약 25분 | narrative v2, PPTX 빌드, BE fix, Phase 3 점검 |
| `/cursor-agent` | 2회 | 약 8분 | 3-Layer 격차 분석, Phase 2 dual silo smoke |
| Agent reviewer-* | 4회 (동시) | 약 12분 | Phase 4 다관점 분석 4명 fan-out |
| 본 세션 직접 | — | (지속) | Phase 0/1, 통합, 4 PR 분리·머지, EOD |

CLAUDE.md memory "외부 에이전트 워크플로"와 정합 — 본 세션 토큰 절약 + 외부 위임 결과 통합.

---

## 10. 한계 (정직 명시, 5/28 이전 미해결)

- **PR #123 머지 안 됨** — 시연에 영향 없지만 `/report` 슬래시 사용 시 main에서 가용 안 됨 (본 working tree 또는 PR head에서만 사용 가능)
- **PR #117 (ADMET divergence guard) 미머지** — main 아닌 `docs/eod-2026-05-26-vram-pcap-dpep`에 있음. 발표 narrative §5.4가 이미 명시
- **PR #112 (Layer 2 재학습) OPEN** — main 머지 없음, narrative §5.2에 R²=0.022 양쪽 명시
- **`dual_silo.enabled=false`** — `--dual` 활성화 안 되어 실제 통합 흐름 미트리거 (narrative §5.4 격차)
- **NGC API key 미보유** — Silo A 3-Arm 라이브 시연 불가, PPTX 시연 시나리오 백업 시나리오로 대응
- **SSTR2 symlink가 git에 들어갈지 미정** — `.gitignore` "Max-retention" 정책으로 `runs_local/` 전체 track 상태이나, 본 세션에서 commit 안 함. 다음 세션 결정 사항

---

## 11. 다음 세션 한 줄 복원

```bash
git pull origin main && \
bash scripts/session_report.sh --save && \
cat _workspace/release/eod-2026-05-27-orchestrator-d1-final.md
```

또는 5/28 회의 진행만 필요하면 `_workspace/release/demo-scenario-2026-05-28.md` 만 보고 §사전 준비 명령 실행.

---

*작성: 2026-05-27 12:35 KST · 5/28 회의 D-1 작업 완료. 본 세션 종료 가능 상태.*
