# EOD — 2026-05-20 Orchestrator Session (Claude)

> **세션 유형**: Claude Code orchestrator (본 세션, tmux pane 28)
> **세션 기간**: 2026-05-20 01:33~07:35 KST (약 6시간)
> **팀**: `gate2-closure-20260520` (5명 — be-merger, qa, be-sstr4, sync, infra)
> **외부 위임**: codex 1회 (Task #7 A-05 SSOT), cursor-agent 1회 (Task #9 PPTX)
> **작성**: team-lead (Claude Opus 4.7 1M)

---

## 0. 한 줄 결론

**시스템 구축 금일 마감 — Gate-2 closure 묶음 + Manual Selectivity 실 PyRosetta 도킹 검증 + V-03 pepADMET 발견을 OOD 명시한 채로 의뢰 진행 결정.** 본 세션 머지 PR 7건 + 위임 머지 2건 + Gate-2 의뢰서 4건 최종 확정 (옵션 B). 다른 세션 (Layer 1 ensemble + pepMSND 자체 학습) 비충돌 병행.

---

## 1. SOD → /team 가동 (Mission A — Gate-2 closure)

**SOD 결정 흐름**:
1. 어제 EOD (`eod-2026-05-19-orchestrator-session.md`) 확인 → 24 PR 머지 + Action Items 9/9 종결 + Gate-2 진입 준비 완료 상태 인지
2. 다른 세션 활동 파악 → 7개 tmux 세션 + 1 별도 orchestrator 가 매우 활발
3. STATUS_2026-05-20.md (다른 세션 작성) §7 "다음 세션 권고" 5건 중 Mission A 채택
4. 사용자 결정: **A (Gate-2 closure 묶음)** + 절대 마감 ("이월 금지, 토큰 갈아넣겠다")

**팀 `gate2-closure-20260520` 5명 기동**:

| Task | 팀원 | 미션 | PR |
|---|---|---|---|
| #1 | be-merger | feat/p1-sprint-integration → main 머지 | PR #68 (8f19082) |
| #2 | qa | BE 152 + FE 99 + pytest 626 회귀 검증 | (PR #68 PASS) |
| #3 | be-sstr4 | SSTR4 시그니처 충돌 BUG fix | PR #72 (c7d710e) |
| #4 | sync | Action Items doc 4 파일 갱신 | PR #73 (944bd00) |
| #5 | infra | biopython + pepADMET 로컬 클론 | (보고서 + 12 ERROR 해소) |
| #6 | be-sstr4 | SSTR4 fix 후 selectivity 재산정 (PRST-001~004) | PR #81 (c5b7ab3) |
| #7 | **codex (외부)** | A-05 SSOT 갱신 (gate_thresholds + 5곳 폴백) | PR #79 (26d16d8) |
| #8 | be-merger | FE worktree 3개 → 옵션 D cherry-pick | PR #83 (b4a8631) |
| #9 | **cursor-agent (외부)** | 5월 회의 PPTX 13 슬라이드 갱신 | PR #78 (c3bf16a) |
| #10 | infra | A-06 VRAM 검증 (H100 ×4 디퓨전) | (보고서, A-07 견적 불요) |
| #11 | be-sstr4 | Gate-2 의뢰서 4건 옵션 B 최종 확정 | PR #86 (6cd600f) |
| #12 | sync | pepADMET 저자 학술 문의문 초안 | (메일 한 + 영, 발송 X) |
| #13 | infra | pepMSND 자체 학습 ROI 평가 | (보고서, 옵션 B 권고) |

---

## 2. 본 세션 머지 PR — 10건 (오늘)

| PR | 내용 | SHA | 트리거 |
|---|---|---|---|
| #68 | P2 sprint wrapper × composite_scorer 자동 enrichment | `8f19082` | 본 세션 (be-merger) |
| #72 | SSTR4 시그니처 충돌 fix (`VILRYAKMKTA` 중복 제거) | `c7d710e` | 본 세션 (be-sstr4) |
| #73 | Action Items docs 갱신 (A-04 FAIL / A-05 실측 / A-09 경로 / 00_MASTER_INDEX) | `944bd00` | 본 세션 (sync) |
| #74 | A-02 ENDPOINT_CONFIDENCE 2건 (webmetabase + HLE regression) | `f2460e5` | 위임 머지 (다른 세션 작성) |
| #78 | 5월 회의 Action Items Audit PPTX 13 슬라이드 갱신 | `c3bf16a` | 본 세션 (cursor-agent) |
| #79 | A-05 SSOT — gate_thresholds.yaml + 5곳 폴백 + LITERATURE_VALUES | `26d16d8` | 본 세션 (codex) |
| #81 | SSTR4 fix 후 PRST-001~004 selectivity 재산정 (Tier/WSS 변동 없음) | `c5b7ab3` | 본 세션 (be-sstr4) |
| #82 | G-2 selectivity margin sign convention (step05b ↔ yaml SSOT) | `a2139a3` | 위임 머지 (다른 세션 작성) |
| #83 | FE 라이브 데이터 훅 + SelectivityExplorer 타입 정합성 | `b4a8631` | 본 세션 (be-merger) |
| #86 | Gate-2 의뢰서 4건 옵션 B 최종 확정 (ADMET 1.00 + wet-lab 5종 + 발주 액션 리스트) | `6cd600f` (HEAD) | 본 세션 (be-sstr4) |

**총 본 세션 영향**: 10 PR 머지 (직접 7 + 위임 머지 2 + cursor-agent 1).

(다른 세션 직접 push 3건: #69 helloworld symlink / #70 silent estimation / #71 candidate_id 형식)

---

## 3. Critical 발견 — V-03 pepADMET 재검증

**04:15 다른 세션 codex 위임 결과**:
- PRST-001~004 4 후보 모두 pepADMET 실측 binary_toxicity=1.0 (toxic, hemostasis + Na_inhibitor)
- 어제 의뢰서 ADMET 0.10/0.12/0.20/0.25 는 **`composite_scorer` wrapper 미응답 시 fallback 입력 전파** — 실측 아님
- composite_scorer.py 가 silent 으로 가짜 값 유지 → Hard Cutoff 가짜 통과 발생 (시스템 결함)

**사용자 결정: 옵션 B (OOD 명시한 채로 의뢰 진행)**:
- pepADMET 학습 데이터 (Toxicity.csv 135 row) 에 SST-14 유사 cyclic 14aa + SS bond 포함 여부 미확인 → OOD 외삽 가능성
- 어차피 wet-lab 검증 필요 → 의뢰 + 측정 병행

**PR #86 결과**:
- PRST-001~004 의뢰서: ADMET 0.1x → 1.00 정정 + 외삽 가능성 disclaimer
- Hard Cutoff: "PASS" → "실측 1.00, cutoff 미통과, 외삽 가능성 명시"
- wet-lab 5종 권고: HC50 / Cell viability / Ki SSTR2 / Serum stability / In vivo tox
- PRST-003 K4→R RI팀 협의 안건 (Nα-DOTA 전용)
- 발주 액션 리스트 (`_workspace/release/gate2-synthesis-order-action-list-2026-05-20.md`)
- 예산: W-1~W-4 ~1,050만원, full ~2,050만원

---

## 4. 파이프라인 로딩 점검 (mock 금지)

**문제**: 사용자 보고 "파이프라인 로딩 안 됨"

**원인**: uvicorn 8787 (운영 BE) 죽음 — `/tmp/uvicorn_8787.log` 마지막 `Shutting down → Finished server process [3762672] → Terminated`. 어제 도킹 잡 PID 813489 도 같이 종료.

**조치**: 8787 재기동 (PID 132191, 사용자 승인 후) — vite.config.ts 의 `target: 'http://127.0.0.1:8787'` proxy 가 부활하면서 FE 자동 복구.

**API 동작 검증 (mock 없음, 실 호출)**:

| Endpoint | 응답 |
|---|---|
| `/api/health` | ok |
| `/api/status` | run_id sst14_mutdock_20260520_022238 (실 run) |
| `/api/runs` | 실 run sst14_mutdock_9999 (best_ddg=-45.624) |
| `/api/binding_pocket/sstr2` | SSTR2_7XNA chain A residues [205,208,209,212,272,273,276,279] 실 좌표 |
| `/api/strategies` | 3 strategy 실 데이터 (blosum / esm_scan / proteinmpnn) |
| `/api/selectivity/receptors` | 5/5 loaded 실 경로 |
| `/api/flexpepdock/jobs` | 14 jobs (실 작업 이력) |
| `/api/stability/cand03` | SST14 ref + cand03 8건 실 값 |

**vite proxy (5173) → 8787**: 정상 동작 확인.

---

## 5. Manual Selectivity ETA 5시간 — 실 PyRosetta 검증

**사용자 의문**: "ETA 5시간이 맞는지, 실제로 돌아가는지"

**확인 결과 (mock 아닌 실 동작)**:

| 항목 | 값 |
|---|---|
| **현재 job** | `32e8cfe1` seq=AGCKNFFWKAFTSC × 5 receptors |
| **PID 183433** | `flexpep_dock.py` 102% CPU, 1.7GB RAM, 4분 34초 가동 |
| **PyRosetta** | `import pyrosetta` 성공 — 실 설치 확인 |
| **flexpep_dock.py L491** | `"stub": False` 실 모드 |
| **ETA** | 18972s (5.27h) = `eta_history.json` 누적 평균 |

**5시간 합리성**:
- cycles=10 × nstruct=50 × 1 receptor ≈ 1시간
- 5 receptor × 1시간 = 5시간 ✅
- Default fallback 30분 × 5 = 2.5h, 실측 학습값 = 5.27h (실제 시간 누적 학습됨)

**어제까지 stub 모드 흔적**: `ac6bd93f` (5/15) 6초 완료 — `result.json` 에 `"stub": true, "stub_reason": "PyRosetta 미설치"`. **오늘 PyRosetta 설치 후 실 모드 진입**.

**stdout/stderr 빈 이유**: worker pipe 캡처 + PyRosetta 초기화 phase + receptor 단위 progress 업데이트 (첫 receptor 완료까지 0%).

---

## 6. 다른 세션 활동 (본 세션 비개입)

### 6.1 별도 orchestrator 세션 (오늘 활발)

오늘 다음 산출:
- **PR #69 / #70 / #71** main 직접 머지 (helloworld symlink / silent estimation / candidate_id 형식)
- **PR #74 (A-02 ENDPOINT_CONFIDENCE 2개)** — 본 세션 머지
- **PR #80 (vLLM Qwen3.5-35B-A3B 업그레이드)** — rebase 대기 (본 세션 코멘트 발송)
- **PR #82 (G-2 margin sign convention)** — 본 세션 머지
- **STATUS_2026-05-20.md** 작성 (`session-sync-20260520` 4명 정찰 결과 통합)
- SOD 4건 작성 (`sod-2026-05-20-A02-daa-tools-extended.md`, `A06-vram-poc.md`, `A06-meeting-schedule.md`, `selectivity-followup.md`)
- `chore/selectivity-guard-20260520` 작업
- `docs/meeting-prep-and-post-audit-20260520` 브랜치 (`8c0b7cc` 백업 + `2182bfe` D-8 audit) — PR 미생성

### 6.2 04:15 codex 위임 (V-03 후속, 다른 세션)

PRST-001~004 의뢰서 ADMET 0.1x → 1.00 갱신 + composite_scorer.py fallback 강화 — `8c0b7cc` 백업 commit 에 포함. **본 세션 be-sstr4 가 cherry-pick → PR #86 으로 main 머지**.

### 6.3 04:17 cursor-agent (다른 세션, 04:32 종료)

pepMSND 격리 conda env 설치 완료 (`_workspace/pepmsnd_local/.conda_env`, 11GB, PyTorch 2.2 + DGL 2.1.0+cu121 + PyG). 체크포인트 미공개 → 즉시 추론 불가.

### 6.4 06:59 codex (다른 세션, 진행 중)

**Layer 1 Ensemble 구현** (`pipeline_local/scoring/layer1_ensemble.py` + `ensemble_router.py` + `test_layer1_ensemble.py`) — L-AA 펩타이드 PlifePred + HLE regression + pepADMET HBM 통합. commit 안 함 원칙.

### 6.5 07:23 cursor-agent (다른 세션, 진행 중)

**Layer 2 pepMSND 자체 학습** (PEPlife2 데이터 + 격리 env) — PRST-001~004 추론 + 벤치마크 4종 (SST14/Octreotide/Lanreotide/Vapreotide). **2-6시간 학습 예상**. 사용자 정책: "토큰과 시간을 갈아넣겠다" + "할루시네이션·거짓 결과 금지".

---

## 7. infra Task #13 — pepMSND ROI 분석 발견 (Critical)

**D-AA 데이터 극도 희소**:
- PEPlife2 4,500 records 中 **D-AA pure 26개 (0.6%)**
- Cyclic 617 (13.7%), Octreotide/Lanreotide 유사체 84 (1.9%)
- → **어떤 학습 방법도 D-AA 정확도 보장 불가**

**모델 + 학습 비용**:
- 21.55M params (Transformer 87.7% 지배)
- H100×4 학습: 15-30분
- ESMFold 구조 예측: 2-4h 추가
- 총 5-10h, GPU 비용 ~$0.003 (전기료)

**4 옵션 ROI**:
- **B (저자 weights 요청)** 1순위 (이론) — but 사용자 결정 X (학술 메일 발송 안 함)
- **A (자체 학습)** 2순위 — 다른 세션 진행 중 (07:23 cursor-agent)
- **C (CycPeptMP 대체)** 부적합 — 막 투과도 ≠ 혈중 안정성
- **D (포기 + rule-based heuristic)** 빠른 백업

**경고**: D-AA 토큰 구분 + rule-based bonus 병행 권고. 다른 세션 학습 시 적용 검토 권고됨 (전달 보류 — 사용자 결정 대기).

---

## 8. 잔여 미커밋 (다른 세션 작업 영역)

| 항목 | 상태 | 비고 |
|---|---|---|
| `pipeline_local/scoring/layer1_ensemble.py` 등 3 신규 파일 | 06:59 codex 작업, **commit 안 함** | 다른 세션 검증 대기 |
| `docs/meeting-prep-and-post-audit-20260520` 브랜치 | `2182bfe` D-8 audit 포함 | PR 미생성, 다른 세션 결정 |
| `pipeline_local/scripts/pharmacology_guards.py` 일부 추가 변경 | working tree M | 다른 세션 작업 영역 |
| **PR #80 (vLLM 35B)** | rebase 대기 | 본 세션 코멘트 발송 완료 |

본 세션 비개입 — 다른 세션 작업 영역 침범 금지.

---

## 9. 본 세션 + 외부 위임 토큰 사용 (개산)

- 본 세션 (orchestrator + 5 팀원 메시지): ~500K
- codex (Task #7 A-05 SSOT, 230초): ~독립 process
- cursor-agent (Task #9 PPTX, 230초): ~독립 process
- 5 팀원 내장 서브에이전트 (be-merger, qa, be-sstr4, sync, infra): ~독립 컨텍스트 ×5
- 절감률 (외부 위임 + 팀원 병렬): 대략 ~75-85% (어제 마라톤 세션 80% 대비 유지)

---

## 10. 사용자 직접 액션 필요 항목

### 즉시
1. **PRST-003 N-말단 DOTA 방법 변경 RI팀 협의 예약** (K4→R + Nα-DOTA 전환, Pbf 보호기 탈보호 조건)
2. **다른 세션 cursor-agent pepMSND 학습 결과 모니터링** (2-6h 후 완료)

### 이번 주
3. **Peptron 4 후보 견적서 요청** (PRST-001~004, 비표준 AA + DOTA 부착)
4. **PR #80 (vLLM 35B)** 다른 세션 rebase 답변 모니터링

### W-1/W-2 병행 (의뢰 즉시)
5. **in vitro hemolysis HC50 + cell viability** 측정 의뢰 (HepG2/HEK293)

### W-3 준비
6. **SSTR2 membrane Ki binding assay** biology팀 스케줄링

### 결정 보류 항목
7. **D-AA 토큰 구분 + rule-based bonus** 적용 여부 (cursor-agent 학습 결과 받은 후)
8. **pepADMET 저자 학술 협력 메일** — sync Task #12 산출물 보존 (`_workspace/release/pepadmet-author-inquiry-letter-2026-05-20*.md`). 사용자 결정: 발송 X

---

## 11. 미진 (wet-lab 또는 다음 세션)

| 항목 | 자동화 가능성 |
|---|---|
| V-A09-01/03/05/06 wet-lab Gate-2 의존 | NO (합성 + Ki 측정 후 자동 해결) |
| AboutPage OKLCH 추가 조정 | 별도 sprint (main 884줄 보존) |
| pepADMET 29 endpoint 로컬화 (V-04) | 저자 weights 요청 또는 자체 학습 |
| 다른 세션 학습 결과 종합 평가 (Layer 1 + Layer 2) | 다음 세션 |
| 5월 회의 일자 [TBD] 확정 | 사용자 입력 |

---

## 12. 본 세션 자체 평가

**성공 요인**:
- /team 의 5명 병렬 작업 + codex/cursor-agent 외부 위임 효과적 결합
- 비충돌 가드 명시 (다른 세션 selectivity-guard / fe-binding-ui / docs/meeting-prep 영역 침범 X)
- 사용자 명시 "이월 금지" 정책 충실히 지킴 (10 PR 머지 + 추가 task 즉시 배정)
- "mock 금지" 정책 검증 (PyRosetta 실 설치 + flexpep_dock.py stub:False + 실 102% CPU 가동 확인)

**개선 가능**:
- 본 세션 cwd 가 `ai4sci-kaeri` 로 이동 후 일부 명령어 path 혼동 (사용자에게 확인 받기까지 시간 소요)
- 임시 cherry-pick 시 `docs/meeting-prep-and-post-audit-20260520` 브랜치에 잘못 commit → 즉시 stash + reset 으로 복구. 다른 세션 작업 영역 직접 만지지 않는 원칙 재확인 필요
- Manual selectivity ETA 5시간 검증 시 progress 0% + stdout 0 byte 가 정상이라는 사실 사전 인지 부족 (worker pipe 캡처 메커니즘 사전 숙지 필요)

---

**최종**: 2026-05-20 07:35 KST (orchestrator 본 세션 EOD 마감)

**다음 세션 권장 1순위 (다음 SOD)**:
1. cursor-agent pepMSND 학습 완료 결과 + Layer 1 codex 결과 종합 평가
2. PR #80 (vLLM 35B) rebase 후 머지
3. ~~Gate-2 합성 실 발주 진행 모니터링 (Peptron 견적 + RI팀 협의)~~ — **§13.B 사용자 결정으로 무효** (합성 발주 안 함)
4. `docs/meeting-prep-and-post-audit-20260520` 브랜치 PR 처리 결정

---

## 13. 추가 정보 (D+1 후속 갱신, 2026-05-21 SOD 시점에 작성)

> **추가 시점**: 2026-05-21 D-7 시점에 본 세션이 다른 세션 EOD 2건 + 본 세션 D-7 작업을 종합하여 보강.

### 13.A 다른 세션 EOD 2건 종합

본 세션 EOD 마감 (07:35) 직후·직전 작성된 다른 세션 EOD 2건의 핵심:

#### 13.A.1 `eod-2026-05-20-orchestrator-3layer-ensemble.md`
- **PR 4건 작성** (open): #84 D-8 audit / **#85 3-Layer Ensemble framework** / #90 binding_pocket 좌표 / #91 PPTX 18 슬라이드
- **16 외부 위임** (codex 7 + cursor-agent 5 + researcher 3 + 본 세션 팀 1) — 본 세션 토큰 99% 절약
- **Layer 2 pepMSND-local R²=-0.028 (음수) P4 정직 보고** — DGL libnvrtc.so.12 비호환 + 공식 model.py 비호환 → GAT 대체 학습 결과 음수 R²
- **Layer 3 ADMET-AI PRST-001~004 + Octreotide 5건 CPU 추론 성공** (104 endpoint × 5)
- 5월 회의 일자 **2026-05-28 (목)** 확정 — 어제 D-8, 오늘 D-7

#### 13.A.2 `eod-2026-05-20-selectivity-validation.md`
- **PR 4건 머지** (다른 세션이 본 세션 mission 과 별개로 머지): #69 helloworld symlink fix / #70 silent estimation guard / #71 candidate_id format / **#82 G-2 margin 부호 컨벤션**
- **5 단계 진단 → 5 fix**: BE 0/5 receptor → hot fix → git index symlink → silent estimation guard → candidate_id 포맷 → margin 부호
- **PRST-001~004 ADMET 신뢰성 위기 — pharma + bio 합의 결론**:
  - cyclic 14aa SS-bond 학습 데이터 0건 (구조적 OOD)
  - Octreotide 교차검증: FDA 승인 안전약 Sandostatin 도 `binary_toxicity=1.0, hemostasis, Na_inhibitor` → **체계적 오분류**
  - 4 후보 모두 동일 (confidence=1.0) = 변이 구별력 0
  - hemostasis = SST-14 의 **치료 기전** (혈소판 응집, 위장관 출혈 치료) — 독성 아님
  - Na_inhibitor = µ-Conotoxin 구조 요건 미충족 (Trp8 ≠ pore-blocking Arg) — 위양성

### 13.B 🔴 사용자 운영 결정 변경 (본 세션 EOD §10 무효화)

본 세션 EOD §10 "사용자 직접 액션 필요 항목" 의 **즉시/이번 주 항목 1, 3, 5, 6 무효**:

| 본 세션 EOD §10 항목 | 변경 결정 |
|---|---|
| 1. PRST-003 RI팀 협의 예약 | ❌ **합성 발주 안 함** |
| 3. Peptron 4 후보 견적서 요청 | ❌ **외주 안 함** |
| 5. wet-lab hemolysis HC50 + cell viability 의뢰 | 🟡 보류 (사용자 결정 보류) |
| 6. SSTR2 membrane Ki binding assay | 🟡 보류 |

**확정 운영 결정** (`eod-2026-05-20-selectivity-validation.md` §3):
- **Gate-2 합성 발주 안 함** — 실 외주 안 함. `synthesis_orders/PRST-00{1..4}.md` **리스트만 보존**
- **pepADMET 재훈련 + 재평가 별도 트랙 시작** (plan 단계)
- 보완 PR (cyclic SS-bond guard + fallback WARN) 즉시 진행 → **PR #108** `f6d4990` 머지 완료

### 13.C 본 세션 EOD 마감 후 머지된 추가 PR (D-7 시점, 11 PR)

본 세션 EOD 07:35 이후 main 머지 (다른 세션 작업):

| PR | 내용 | SHA |
|---|---|---|
| #87 | (지난 PR, 확인 필요) | — |
| #88~#90 | binding pocket 좌표 일관성 (auth_seq_id 통일) | (~PR #90) |
| #91 | PPTX 5월 28일 회의 18 슬라이드 (3-Layer Ensemble 결과 반영) | (PR #91) |
| #92 | (다른 세션) | — |
| #93 | Mol* 후보별 pdbUrl mapping fix | — |
| #94 | per-receptor timeout 4h → 6h (V4-A manual selectivity stuck fix) | — |
| #95 | FlexPepDock worker pool 2개 동시 잡 처리 (V4-B) | `90eb2b7` |
| #96 | orphan worker auto-cleanup — startup hook + PID file GC (V5-R4) | — |
| #97 | Manual Selectivity 대형 잡 경고 배너 (V5-R2) | — |
| #98 | FlexPepDock nstruct 단위 sub-progress 세분화 (V5-R3) | — |
| #99 | stub 결과 FE badge — Job 리스트 + Section4 (V5-R5) | — |
| #100 | EOD 2026-05-20 (다른 세션) | — |
| #108 | cyclic SS-bond OOD guard + composite_scorer fallback WARN (재훈련 트랙 보완) | `f6d4990` |

### 13.D 본 세션 D-7 (2026-05-21) 작업 (어제 EOD 이후 추가)

본 세션이 2026-05-21 SOD 시점부터 진행한 작업:

1. **SOD 작성** — 다른 세션 11 PR 활동 + open PR 3건 (#84/#85/#80) + Manual Selectivity 진행 상황 종합
2. **Manual Selectivity 32e8cfe1 / e36b362d failure 분석**:
   - `32e8cfe1` (어제 본 세션 검증): per-receptor 4h timeout 으로 cancelled (PR #94 적용 전)
   - `e36b362d` (어제 11:26 새 job): SSTR1 dG=0.0 silent fallback 발견 — `flexpep_dock.py:aggregate_scores` 가 빈 ddg_values 에 (0.0, 0.0) silent return
3. **PR #109 작성 + 머지** — `fix(flexpep): silent 0.0 fallback 제거 — mock 금지 정책` (`a5f44c7`)
   - `aggregate_scores`: `if not ddg_values: raise RuntimeError(...)` 명시
   - `main()`: PDB 있는데 ddg 비면 `stub:True` + `stub_reason='interface_analyzer_failed_all_nstruct'` + `exit(2)`
   - 회귀 테스트 갱신 (`test_empty_raises_runtime_error`) — 19/19 PASS
4. **8787 운영 BE 재기동** (PID 132191) — 어제 11:26 죽음 → 오늘 SOD 시점에 부활
   - 실 API 검증 (mock 없음): health/runs/binding_pocket/strategies/selectivity/stability/flexpepdock 모두 정상
5. **아키텍처 문서 작성** — `_workspace/release/architecture-silo-ab-2026-05-21.md`
   - Silo A (LLM-driven, AG_src + NIM/vLLM) vs Silo B (PyRosetta direct, pyrosetta_flow) 구분 플로우차트
   - 데이터 플로우 (전체 8 섹션, 약 380줄)
   - 🔴 미구현 3건: A-09 자동화 모듈 (`select_final_candidates.py` / `synthesis_checker.py` / `generate_synthesis_request.py`)
   - 🟡 부분 구현 6건: PR #85 main 미머지 / NIM API dry-run / Bandit·BO 실 운영 검증 / Boltz-2 1 후보만 / FlexPepDock done 9건 silent fallback audit
   - 5월 28일 회의 발표 매트릭스 권고 (완료 40% / 진행 중 25% / 이월 15% / OOD 제한 15% / 요청 5%)

### 13.E 본 세션 EOD §10 갱신 후 사용자 직접 액션 (D-7 갱신본)

#### 즉시 (D-7)
1. **PR #85 (3-Layer Ensemble framework) 머지 결정** — open 상태, 검토 필요
2. **다른 세션 cursor-agent pepMSND 학습 결과 평가** — Layer 2 R²=-0.028 정직 보고 받음 → 재훈련 트랙 결정
3. **`docs/meeting-prep-and-post-audit-20260520`** (PR #84) 머지 — D-7 prep 갱신 후 (PR #84 `d0855b2` 머지 완료 확인됨)

#### D-6 ~ D-3
4. **pepADMET 재훈련 plan 검토 + 실행 결정** (별도 트랙)
5. **5월 28일 회의 PPTX 18 슬라이드 (PR #91) 갱신** — 본 세션 architecture 문서 §5 미구현 사항 반영

#### D-1 ~ D-Day
6. **시연 리허설** + 자료 배포
7. **회의 진행** (KAERI-AIRL-MOM-2026-004, 2026-05-28 목요일)

#### 결정 보류 (사용자 명시)
8. **in vitro RBC hemolysis assay** 외부 외주 vs 내부 lab — 결정 보류

### 13.F D-7 종합 평가

**오늘 본 세션 핵심 성과**:
- ✅ Silent fallback 제거 (PR #109) — selectivity 신뢰도 회복
- ✅ 아키텍처 문서 — Silo A/B 명확화, 미구현 매트릭스 작성
- ✅ 8787 운영 BE 부활 + 실 API 검증

**미진**:
- PR #85 (3-Layer Ensemble) 미머지 → 다음 세션 결정
- PR #80 (vLLM 35B) rebase 대기 → 다른 세션 응답 대기
- Silo A NIM 실 호출 검증 0회 (dry-run fallback 만)
- A-09 자동화 3 모듈 미구현

**D-7 작업 종료 시점**: 2026-05-21 ~03:30 UTC (orchestrator 본 세션 SOD-EOD 사이 짧은 작업 사이클)

---

*보강 작성: 2026-05-21 D-7 by team-lead (orchestrator)*
