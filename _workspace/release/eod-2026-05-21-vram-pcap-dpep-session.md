# EOD 2026-05-21 — vram-pcap-dpep 세션 (UI/UX + FlexPepDock 안정화)

> **세션 유형**: orchestrator (Claude Opus 4.7) · 팀 `vram-pcap-dpep`
> **worktree**: `.worktrees/llm-vllm-upgrade` (branch `main`, EOD commit 시점)
> **활성 시간**: **2026-05-20 ~07:30 → 2026-05-21 ~07:40 UTC (~24h 누적, 실 작업 ~9-10h)**
> **선행/병행**: `eod-2026-05-20-llm-system-verification.md` (어제 EOD), 다른 세션 `eod-2026-05-21-master-integrated.md` + `eod-2026-05-21-action-items-closure.md`

---

## 0. 본 세션의 정체 (Session Identity) — 다른 EOD와 구분

| 구분 | 본 세션 (vram-pcap-dpep) | action-items-closure (다른 세션) | pepADMET-retrain (다른 세션) |
|---|---|---|---|
| 팀 이름 | `vram-pcap-dpep` | `action-items-closure-20260521` | (engineer-backend 단독) |
| 활성 시작 | 5/20 07:30 (어제) | 5/21 04:00 | 5/21 ~08:00 |
| 주 영역 | **UI/UX (Mol* 시각화, LLM UX) + FlexPepDock 안정화 (worker pool, timeout, progress)** | Action Items A.A1~A.A5 closure (재훈련 plan + 보완 PR #108 + #113) | pepADMET GNN 재훈련 chain A.A5Pa~Pe |
| 위임 방식 | codex exec + cursor-agent + Agent tool subagent (11+ 회) | Group A 6명 위임 (backend/research/dock/tester/infra) | 단독 |
| EOD 보고서 | **본 파일** | `eod-2026-05-21-action-items-closure.md` | `eod-2026-05-21-pepadmet-retrain.md` |

→ **master EOD (`eod-2026-05-21-master-integrated.md`)는 다른 세션이 본 세션을 "다른 세션 11건"으로 분류**. 본 EOD는 그 흔적을 본 세션 관점으로 재구성한 보완본.

---

## 1. 본 세션 머지 PR (5/20 어제 + 5/21 오늘 누적 13건)

### 1.1 어제 (5/20) 머지 6건
| PR | merge commit | 내용 |
|---|---|---|
| #89 | `f5a6acf` | LLM 인프라 통합 (vLLM 35B-A3B + DeepSeek-R1 + per-agent + Planner prompt) |
| #92 | `f8ca931` | LLM UX FE dropdown 8 모델 |
| #93 | `992cc20` | **Mol* 시각화 4 root cause fix** (DOM cleanup + URL mapping + 하드코딩 7XNA + BE static 라우터) |
| #94 | `4858e61` | FlexPepDock timeout 4h → 6h |
| #95 | `90eb2b7` | Worker pool 2개 (per-job fcntl.flock) |
| #96 | `931c25a` | Orphan worker auto-cleanup (FastAPI lifespan startup hook) |
| #97 | `5fa61b3` | Manual Selectivity 대형 잡 amber 경고 배너 |
| #98 | `5b729d7` | FlexPepDock nstruct sub-progress 세분화 (timer-based 15s daemon) |
| #99 | `e888e80` | Stub 결과 FE badge 표시 (jobs list + Section 4) |
| #100 | `94b49f5` | EOD 2026-05-20 보고서 |

### 1.2 오늘 (5/21) 머지 7건
| PR | merge commit | 내용 |
|---|---|---|
| #101 | `768a243` | FE jobs status chips (색상 + 아이콘 — timeout/사용자 취소/오류 구분) |
| #102 | `25d27b9` | Silo A 로컬 라우터 Phase 1 (헬스 + dry-run, V3-B) |
| #103 | `ab4a011` | D-AA SMILES utility (pepMSND 학습 D-AA 0건 fix, V3-A) |
| #104 | `6bd843d` | Worker pool 2 → 4 확장 |
| #105 | `22db857` | PRST-001~004 wetlab orders 통합 (BE wetlab.py) |
| #106 | `db93d44` | Candidate selector v1 (CandidatePage header dropdown) |
| #107 | `fd23f71` | **2-level 셀렉터 — Run (header) + Candidate (Mol* 근처) 직관 UI** |

**누적 머지: 13 PR.** Master EOD의 "본 세션 2건" 표기와 다른 이유 → master EOD가 본 세션을 **"다른 세션 11건"**으로 분류했기 때문 (관점 차이).

---

## 2. 사용자 보고 이슈 대응 결과 (5 → 5 = 100%)

| 사용자 보고 | 진단 결과 | 처리 PR | 상태 |
|---|---|---|---|
| **"Qwen3:8b 말고 올라간 것도 없다"** | 단일 모델 운영 + RunLauncher dropdown 3개만 | #89 #92 | ✅ |
| **"Mol* docked pose 차이 없어 보임"** | 4 root cause (DOM cleanup + URL + 하드코딩 + static) | #93 | ✅ |
| **"manual selectivity 안 돌아간다"** | timeout 4h + 단일 worker + UI 미구분 + 과거 stub | #94 #95 #96 #97 #98 #99 | ✅ |
| **"세션 셀렉터지 후보 셀렉터 아님"** | PR #106는 후보지만 사용자 혼동 → 2-level 분리 | #107 | ✅ |
| **"큐 38분 너무 김"** | worker 2 → 4 확장 | #104 | ✅ |

---

## 3. 본 세션 위임 패턴 (master EOD에 없는 본 세션 고유)

### 3.1 외부 CLI (codex/cursor-agent) 위임 ~10회
- **/codex exec**: V3-A SMILES (#103), V3-B Silo A (#102), V4-C FE jobs (#101 cursor), D Candidate selector (#106), F Worker pool 4 (#104), G PRST wetlab (#105), D2 2-level 셀렉터 (#107)
- 모든 호출 `./scripts/agent-wrapper.sh codex exec` + `cursor-agent -p` 패턴
- 로그 위치: `logs/external_agents/codex_20260521_*.jsonl` (10+ entries)

### 3.2 Agent tool subagent dispatch (어제 11명)
- be-binding-api, fe-binding-ui, researcher-daa, infra-vram, verify-wrappers, be-endpoint-confidence, be-molstar-verify, fe-llm-ux, be-worker-pool, fe-jobs-ui, be-progress-granular, fe-warning-banner, be-orphan-cleanup, fe-stub-badge, reviewer-e2e
- 5/20 13:32에 일괄 shutdown_request 발사 (EOD 정리)

### 3.3 정체 agent 처리 (어제 V3-A/V3-B/V4-C → 오늘 codex 재할당)
- be-daa-smiles 6h+ 정체 → /codex exec로 재할당 → PR #103 30분 완료
- be-silo-a-local 6h+ 정체 → /codex exec → PR #102 30분 완료
- fe-jobs-ui 4h+ 정체 → /cursor-agent -p → PR #101 30분 완료

→ **외부 CLI가 내장 subagent 정체 시 회복 도구로 작동함** 입증.

---

## 4. 본 세션 고유 결정 (master EOD에 없음)

| 결정 | 시점 | 근거 |
|---|---|---|
| **PR #80 close + #87 cherry-pick + #89 통합 신규** | 5/20 12:30 | 다른 세션 commits 섞임 → 중복 머지 위험 |
| **uvicorn 재시작 진행** (사용자 명령) | 5/20 12:55 | V4-A timeout + V4-B pool + V5-R4 cleanup 효과 활성화 |
| **e36b362d 잡 보존 (B 선택)** | 5/21 02:10 | 9h+ 진행 잡 손실 회피 |
| **PR #84/#85 rebase 코멘트** | 5/21 01:30 | 다른 세션 author 알림 → PR #84 자체 처리 → 머지 |
| **V-05 PepMSND 학습 진행** | 5/21 01:25 (사용자 ✅) | task #41 등록, V3-A SMILES utility가 선행 — 다른 세션 PR #112가 picked up |
| **NIM API key/V-07 contact 제외** | 5/21 01:23 (사용자 ✅) | 사용자 명시 — 외부 contact 안 함 |

---

## 5. 회귀 검증 결과 (Phase H, 5/21 ~02:46)

| Test Suite | 결과 |
|---|---|
| AG_src | 253 PASS + 1 fail + 8 errors (모두 pre-existing macOS 경로) |
| backend | **169/169 PASS (100%)** |
| pipeline_local | **634 PASS + 5 skipped + 2 xfailed** |
| FE vitest | 100/101 (1 fail은 어제부터) |

→ 본 세션 7 PR 머지 후 **신규 회귀 0건**. 

---

## 6. master EOD/action-items EOD에서 빠진 본 세션 흔적

### 6.1 본 세션 codex 위임 흐름 (master EOD §3 "다른 세션 활동" 일부에 흡수)
master EOD는 PR 머지 시점 + 제목만 추적. 본 세션의 **위임 → 재할당 → 머지** 흐름은 본 EOD에만 보존.

### 6.2 본 세션 발견 갭 (master EOD §2.3 "신규 발견 K-1/K-2"와 별개)
- **본 세션 갭**: Mol* 4 root cause / LLM UX dropdown / FE jobs UI 색상 / 2-level 셀렉터 → 모두 PR로 closure
- **action-items 세션 갭 (K-1/K-2)**: selectivity production 검증 시 _build_pdb_index 알파벳 정렬 + _run_offtarget_pyrosetta candidate_pdb 미사용 — 별도 잔존
- 두 세션 갭은 **다른 코드 영역**이라 충돌 없음

### 6.3 본 세션이 머지 처리한 다른 세션 PR
- **#84 회의 D-7 docs** (다른 세션 작업) → 본 세션이 5/21 02:13 머지 (rebase 코멘트 + author 자체 처리)
- **#91 5월 28일 회의 PPTX** → 본 세션이 5/20 12:30 머지

---

## 7. 다음 SOD 2026-05-22 시작 가이드 (본 세션 관점)

### 7-1. 즉시 확인 (3분)
```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
git fetch origin
git log --oneline origin/main -10

# 시스템 가동
ss -tln | grep -E ':(5173|8000|8001|8787)'
pgrep -af "flexpepdock_worker.py"
```

### 7-2. 본 세션 잔여 (다음 sprint 이월)

| 우선 | 항목 | 비고 |
|---|---|---|
| **High** | **본 세션 PR #107 효과 검증** (사용자 직접 UI) | 2-level 셀렉터 직관성 확인 |
| **High** | **action-items 세션 K-1/K-2 selectivity production 결함** | 다른 세션 영역, master EOD §2.3 |
| Med | **본 세션 e36b362d 잡 결과 회수** (cancel 됐지만 SSTR1 PDB 10개 valid) | 다른 세션 PR #109 효과 검증에도 유용 |
| Low | uvicorn 18h+ 무중단 — 재시작 권고 (PR #104/#106 새 코드 활성) | 다른 세션 동의 필요 |

### 7-3. 다른 세션과 영역 분리 (충돌 회피)

| 영역 | 담당 세션 | 본 세션 |
|---|---|---|
| pepADMET 재훈련 (Layer 2/3) | pepADMET-retrain + action-items | ❌ 손대지 말 것 |
| selectivity K-1/K-2 결함 | action-items | ❌ 손대지 말 것 |
| 회의 D-7 발표 자료 (#111 매트릭스) | docs 다른 세션 | ❌ |
| UI/UX 개선 + FlexPepDock 안정화 | **본 세션** | ✅ |
| LLM 인프라 / 모델 비교실험 | **본 세션** | ✅ |

### 7-4. 사용자 결정 사항 (어제 5건 → 오늘 2건 처리, 3건 남음)

| 항목 | 5/21 결정 |
|---|---|
| NIM API key 신청 | ❌ 사용자 거부 — 영구 deferred |
| V-07 pepADMET 저자 contact | ❌ 사용자 거부 — 영구 deferred |
| 5월 회의 일자 확정 | TBD — 사용자 결정 |
| **V-05 PepMSND 학습** | ✅ 진행 → 다른 세션 PR #112 picked up |
| **PR #84/#85 rebase** | ✅ 완료 (#84 머지, #85 머지) |

### 7-5. 추가 권고 (본 세션 발견 후속)
- 작은 잡 (cycles=1, nstruct=3) 우선 큐 — V5-R3 progress 세분화 효과 검증
- FE light 모드 검증 (어제 EOD 5/19 light-mode 보고서 이후 후속 없음)
- vLLM 8000/8001 health check 자동화 (현재 수동 curl)

---

## 8. 한 줄 결론

본 세션은 **사용자 UI/UX 직접 보고 5건 모두 closure** + **FlexPepDock 안정화 6 PR** + **외부 CLI 위임 패턴 입증** + **다른 세션과 영역 분리 명확화**. 누적 13 PR 머지, 회귀 0건, 사용자 결정 5건 중 2건 진행 ✅ / 2건 거부 ❌ / 1건 TBD.

---

*최초 작성: 2026-05-21 07:40 UTC by team-lead (vram-pcap-dpep)*
