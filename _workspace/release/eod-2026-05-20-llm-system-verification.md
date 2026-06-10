# EOD 2026-05-20 — LLM 인프라 + Manual Selectivity 안정화 + UI 시각화 fix

**세션**: orchestrator (binding-pocket-pepadmet → vram-pcap-dpep)
**활성 시각**: 07:30 ~ 13:00 KST (~5.5h)
**팀원**: be-binding-api, fe-binding-ui, researcher, infra-vram, researcher-daa, be-endpoint-confidence, be-molstar-verify, fe-llm-ux, verify-wrappers, be-daa-smiles*, be-silo-a-local*, be-worker-pool, fe-jobs-ui*, reviewer-e2e, fe-warning-banner, be-progress-granular, be-orphan-cleanup, fe-stub-badge
(* idle/정체)

---

## 1. 오늘 본 세션 머지된 PR (11건)

| 시각 | PR | 내용 | 영역 |
|---|---|---|---|
| 07:30 | #74 | ENDPOINT_CONFIDENCE webmetabase + HLE | scoring |
| 08:09 | #89 | **LLM 인프라 통합** (vLLM 35B-A3B + DeepSeek-R1 + per-agent + Planner prompt) | LLM |
| 08:30 | #92 | **LLM UX FE** (dropdown 8 모델 optgroup) | FE |
| 08:35 | #93 | **Mol* 시각화 4 root cause fix** (DOM cleanup + URL mapping + 하드코딩 + BE static) | FE+BE |
| 09:30 | #91 | 회의 PPTX 18 슬라이드 (다른 세션) | docs |
| 11:43 | #94 | FlexPepDock timeout 4h → 6h (V4-A) | BE worker |
| 12:33 | #95 | Worker pool 2개 (per-job fcntl flock, V4-B) | BE worker |
| 12:43 | #96 | Orphan worker auto-cleanup (lifespan, V5-R4) | BE |
| 12:48 | #97 | 대형 잡 경고 배너 (V5-R2) | FE |
| 12:53 | #98 | Progress nstruct 세분화 (V5-R3) | BE worker |
| 12:55 | #99 | Stub FE badge (V5-R5) | FE |

**총 변경**: 11 PR / ~2500+ insertions / 신규 단위 테스트 80+ 건

---

## 2. 사용자 보고 3 이슈 — 모두 fix 완료

| 사용자 보고 | 진단 | Fix PR |
|---|---|---|
| **"Qwen3:8b 말고 올라가있는 것도 없다"** | 단일 모델 운영 | #89 #92 (vLLM 35B-A3B + R1 + per-agent + dropdown) |
| **"Mol* docked pose 차이가 없어 보인다"** | DOM cleanup + URL mapping + 하드코딩 + static 라우터 4 root cause | #93 |
| **"manual selectivity 안 돌아간다"** | timeout 4h + 단일 worker + UI 미구분 + 과거 stub | #94 #95 #96 #97 #98 #99 |

---

## 3. 시스템 재가동 (12:55~13:00)

| 컴포넌트 | PID | 상태 |
|---|---|---|
| uvicorn 8787 | 1620287 | ✅ Live (V5-R4 lifespan + V4-B worker pool 활성) |
| FlexPepDock worker-1 | 1652664 | ✅ |
| FlexPepDock worker-2 | 1654122 | ✅ |
| vLLM 8000 qwen3.5-35b-a3b | — | ✅ |
| vLLM 8001 deepseek-r1-distill-32b | — | ✅ |
| Orphan workers | 810467/1805735/4133267 | ✅ kill -9 정리 완료 |

---

## 4. OPEN PR (3건, 다른 세션 영역)

| PR | 내용 | 상태 |
|---|---|---|
| #84 | 회의 D-8 docs | CONFLICT — 다른 세션 author rebase 필요 |
| #85 | 3-Layer Ensemble (PlifePred + pepMSND-local + ADMET-AI) | CONFLICT — 다른 세션 author rebase 필요 |
| #11 | postmortem (5/11 old) | 검토 안 됨 |

---

## 5. 진행 중 agent (정체 또는 큰 작업)

| Agent | Task | 경과 | 비고 |
|---|---|---|---|
| be-daa-smiles | V3-A pepMSND D-AA SMILES | 6h+ | **정체** — worktree 미생성, 핑 응답 없음 |
| be-silo-a-local | V3-B Silo A 라우터 Phase 1 | 6h+ | **정체** — worktree 미생성, 핑 응답 없음 |
| fe-jobs-ui | V4-C FE status 색상 구분 | 4h+ | 작업 중 (worktree 미확인) |

→ 내일 SOD에서 재할당 또는 본 세션이 직접 진행

---

## 6. Task 종합 (31건 등록)

- ✅ Completed: 27건
- 🟡 In-progress: 3건 (위 §5)
- 🟡 Pending: 1건 (#3 A-06 후속, 다음 sprint)

---

## 7. 내일 SOD 2026-05-21 시작 가이드

### 7-1. 즉시 확인 (3분)

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
git fetch origin && git status

# 시스템 가동 상태
ss -tln | grep -E ':(5173|8000|8001|8787)'
ps -ef | grep -v grep | grep -E "uvicorn.*backend|flexpepdock_worker"

# 진행 중 잡
curl -s http://localhost:8787/api/flexpepdock/jobs | python3 -c "import json,sys; d=json.load(sys.stdin); print([f'{j[\"job_id\"][:8]}={j[\"status\"]}({j[\"progress\"]*100:.0f}%)' for j in d.get('jobs',[])][:5])"
```

### 7-2. UI 테스트 (사용자 직접, 30~60분)

Phase A~G 권장 순서 (어제 메시지 참조):
- **A** `/about` + `/settings` — LLM description 확인 (PR #92)
- **B** `/binding-pocket` — SSTR1↔2 탭 Mol* 갱신 (PR #93)
- **C** `/selectivity-explorer` — **후보 클릭마다 Mol* 다름** (PR #93 핵심)
- **D** `/candidate` — 상단 Mol* 후보별 다름
- **E** `/run/new` — LLM dropdown 8 모델 확인 (PR #92)
- **F** `/manual-selectivity` — 새 잡 생성 + amber 경고 (PR #97) + stub badge (PR #99) + progress 갱신 (PR #98)
- **G** `/wetlab/orders` — PRST-001~004 확인

### 7-3. 미해결 작업 (우선순위)

#### High
1. **V3-A pepMSND D-AA SMILES** — be-daa-smiles 6h+ 정체 → 본 세션 직접 진행 또는 새 agent dispatch
2. **V3-B Silo A 라우터 Phase 1** — be-silo-a-local 6h+ 정체 → 동일
3. **V4-C FE status 색상** — fe-jobs-ui 4h+ → 결과 확인 또는 직접 진행

#### Medium
4. **PR #84 / #85** — 다른 세션 author에게 rebase 요청 (CONFLICT 해결)
5. **pepMSND 자체 재학습** — D-AA SMILES fix 후 학습셋 재처리 (다른 세션 영역)
6. **Stub 잡 7개** — 과거 구 router 결과 정리 (UI 표시는 PR #99로 해결, 데이터는 cleanup 또는 보존)

#### Low (다음 sprint)
- Task #3 A-06 후속 (openmm GLIBCXX / GPU 좀비 / 2-GPU DP)
- Task #5 A-02 §검증 필요 (V-01/V-02/V-03 + Phase 1 ML 학습)
- ollama port 11434 좀비 GPU 0/1 정리 (NVIDIA reset)

### 7-4. 사용자 결정 사항 (5건 잔존)

| # | 항목 | 결정 사항 |
|---|---|---|
| 1 | V-05 PepMSND 자체 학습 착수 | H100 NVL 자원 + 2~4주 |
| 2 | V-07 pepADMET 저자 학술 contact 발신 | `_workspace/release/pepadmet-author-inquiry-letter-2026-05-20-EN.md` 작성 완료 |
| 3 | 5월 회의 일자 확정 (`sod-2026-05-20-A06-meeting-schedule.md`) | TBD |
| 4 | NVIDIA NIM API key 신청 (Silo A live mode) | 또는 dry-run + 로컬 유지 |
| 5 | PR #84/#85 다른 세션 author에게 rebase 알림 | GitHub 코멘트 또는 다른 세션 안내 |

### 7-5. 회의 KAERI-AIRL-MOM-2026-004 준비 (~5월 28일 추정)

| 자료 | 상태 |
|---|---|
| 18 슬라이드 PPTX | ✅ PR #91 머지됨 |
| Action Items Audit | ✅ PR #78 머지됨 |
| Gate-2 의뢰서 PRST-001~004 | ✅ PR #86 머지됨 |
| LLM 인프라 안내 | ✅ PR #89 + #92 머지됨 (deck 갱신은 차기) |

---

## 8. 인프라 보존 (재시작 시 자동 정리)

- V5-R4 lifespan startup hook: 다음 uvicorn 재시작 시 stale PID 파일 자동 정리
- V4-B start_workers.sh: `bash pipeline_local/scripts/start_flexpepdock_workers.sh` 로 2-worker 재가동
- `FLEXPEPDOCK_TIMEOUT=21600` (6h default, env override 가능)

---

## 9. 메모리 / 학습 보존

본 세션에서 입증된 핵심:
- vLLM Qwen3.5-35B-A3B `chat_template_kwargs={"enable_thinking": False}` 필수 (14.99x speedup)
- DeepSeek-R1 응답 `<think>...</think>` 인라인 → 정규식 strip 필요
- Per-job `fcntl.flock(LOCK_EX|LOCK_NB)` 패턴이 worker pool 동시성에 안전
- FastAPI lifespan startup hook으로 dead PID 정리 패턴

---

*최초 작성: 2026-05-20 13:00 EOD by team-lead (vram-pcap-dpep)*
