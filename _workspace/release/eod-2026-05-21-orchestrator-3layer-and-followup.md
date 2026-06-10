# EOD 2026-05-21 — Orchestrator Session (3-Layer Ensemble + Follow-up)

## ⚠ 세션 구분 (SOD 시 헷갈리지 마세요)

| 항목 | 값 |
|------|-----|
| **세션 이름** | **`orchestrator-2026-05-20→21`** (어제 세션 연장) |
| **역할** | team-lead (orchestrator) — 문서화 + 오케스트레이션 |
| **어제 EOD** | `eod-2026-05-20-orchestrator-3layer-ensemble.md` |
| **본 EOD 범위** | 2026-05-21 자정 ~ 현재 (D-7 일과) |
| **다른 세션 통합 EOD** | [`eod-2026-05-21-master-integrated.md`](eod-2026-05-21-master-integrated.md) (작성: `action-items-closure-20260521` 세션) |

> **통합 EOD 표기 정정**: 통합 EOD가 PR #85/#84/#90/#91/#110을 "다른 세션 머지"로 표기했으나, **이 5건은 본 세션 산출물**.
> 통합 EOD의 "본 세션 머지 2건(#108, #113)"은 `action-items-closure-20260521` 세션의 산출.
> 두 세션이 같은 날 동시에 작업했으므로 PR 출처가 혼동된 것.

---

## 1. 본 세션 한 줄 결론

**오늘 PR 7개 생성 (5 머지 + 2 open)**. 3-Layer Ensemble 시스템 완성 + 회의 D-7 자산 95% 확보. 외부 위임 24건 + 1팀, 본 세션 토큰 ~99% 절약.

---

## 2. 본 세션 PR 7개 (시간순, UTC 기준)

| PR | 시각 UTC | 상태 | 제목 |
|----|---------|------|------|
| **#85** | 01:17 | ✅ MERGED | feat(scoring): **3-Layer Ensemble framework** (Layer 1 PlifePred + Layer 2 pepMSND-local + Layer 3 ADMET-AI) |
| **#84** | 02:13 | ✅ MERGED | docs(meeting): refine D-7 prep Q&A after rebase |
| **#90** | (어제) 10:46 | ✅ MERGED | fix(extract): PDB/CIF binding pocket auth_seq_id 통일 (4.076Å → 0.0Å) |
| **#91** | (어제) 11:48 | ✅ MERGED | docs(pptx): 5월 28일 회의 18 슬라이드 — 3-Layer Ensemble 결과 반영 |
| **#110** | 04:19 | ✅ MERGED | feat(scoring): HLE regression callable wrapper — Layer 1 보강 |
| **#111** | 07:23 | 🟢 open | docs(presentation): PRST-001~004 종합 매트릭스 + ADMET-AI 시각화 (D-3 발표 자료) |
| **#112** | 08:54 | 🟢 open | experiment(layer2): pepMSND 재학습 — ranking 신호 식별 (Spearman ρ 0.571) |

---

## 3. 본 세션 주요 발견 (정직한 한계 보고)

### 🚨 PRST-001~004 ADMET 시스템 결함
- 의뢰서 `ADMET=0.10/0.12/0.20/0.25`는 **fallback 전파값** (composite_scorer wrapper 미응답)
- pepADMET 실측 재검증: **4개 후보 모두 binary_toxicity=1.00** (hemostasis + Na_inhibitor)
- 처리: Hard Cutoff 불일치 양측 보존 (PR #111 매트릭스), composite_scorer fallback WARN 추가
- **다른 세션 PR #108**도 같은 영역 fix (cyclic SS-bond OOD guard) — 충돌 없이 보완 관계

### 🔬 Layer별 정직 보고
- **Layer 1**: PlifePred2 'Halflife' 컬럼이 사실 **확률값** (PyPI/소스 확인) — SST-14만 calibration 작동
- **Layer 2**: GAT 재학습 결과
  - 어제: R²=-0.028, Spearman ρ=-0.119 (P4 정직)
  - **오늘 (PR #112)**: R²=0.022 (양수 전환), **Spearman ρ=0.571** (ranking 큰 개선)
  - cursor-agent 권고: seed 흔들림 → P-grade 유지(보수적), ranking 보조 지표 활용 가능성 명시
- **Layer 3**: ADMET-AI 5 SMILES × 104 endpoint 추론 성공 + H-06 외삽 가드 강제

### 🔧 인프라 발견
- binding_pocket PDB/CIF 좌표 4.076Å 차이 → `auth_seq_id` 통일 (PR #90, 0.0Å)
- HLE regression 회귀 계수 공개 X → callable framework만 작성, unavailable 정직 반환 (PR #110)
- pepADMET 저자 이메일 초안 작성 완료 (EN+KR, KAERI 행정 발송 대기)

---

## 4. 외부 위임 누적 (24건 + 1팀)

| 도구 | 횟수 | 영역 |
|------|------|------|
| codex | 11 | pharmacology_guards, estate.py 패치, PRST 재검증, 의뢰서 갱신, PlifePred wrapper, Layer 3, binding_pocket, 리베이스 #85/#84, HLE wrapper |
| cursor-agent | 9 | V-02/V-03 pepADMET, biopython, pepMSND 격리설치/학습/재학습, PPTX, PRST 매트릭스, SOD/EOD |
| researcher (subagent) | 4 | 환경 조사, ensemble 시스템 설계, 학습 가능성, 저자 이메일 초안 |
| 본 세션 팀 | 1 (4명) | tracker/be-status/fe-status/sync 정찰 |

**본 세션은 통합·문서·PR 작성만 담당.**

---

## 5. 회의 D-7 자산 (5/28 회의 1주 전)

| 자산 | 상태 | 위치 |
|------|------|------|
| 3-Layer Ensemble framework | ✅ main | `pipeline_local/scoring/layer{1,2,3}_*.py` |
| HLE wrapper (callable) | ✅ main | `pipeline_local/scripts/predict_halflife_pepmsnd.py` |
| binding_pocket 좌표 정합성 | ✅ main | `data/somatostatin_receptor/binding_pocket_SSTR2.json` |
| PPTX 18 슬라이드 | ✅ main | `_workspace/pptx/PRST_N_FM_ActionItems_Audit_2026-05-28.pptx` |
| MEETING_PREP D-7 Q&A (Q1~Q8) | ✅ main | `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md` |
| PRST 종합 매트릭스 + 차트 | 🟢 PR #111 | `docs/meet_log/2026-04-06_action_items/PRST_comprehensive_matrix_2026-05-21.md` + `_workspace/admet_ai_local/charts/` |
| Layer 2 재학습 실험 | 🟢 PR #112 | `_workspace/pepmsnd_local/retraining_2026-05-21.md` + 체크포인트 |
| pepADMET 저자 이메일 초안 | ⏳ 사용자 발송 대기 | `docs/meet_log/2026-04-06_action_items/A-03_pepadmet_author_email_draft.md` |

---

## 6. 다른 세션 통합 EOD와의 관계

### 6.1 같은 날 활동한 세션들 (통합 EOD §3 참고)
- `action-items-closure-20260521` (통합 EOD 작성자): PR #108, #113 — pepADMET 재훈련 + OOD detection
- `fe-jobs-status`: PR #101
- `silo-a-router`: PR #102
- `daa-smiles`: PR #103
- `worker-pool`: PR #104
- `wetlab-prst`: PR #105
- `fe-candidate-selector`: PR #106
- `flexpep-silent-fallback`: PR #109 (본 세션 K-1/K-2 영역 부분 fix)
- `fe-2level-selector`: PR #107
- **본 세션 (`orchestrator-2026-05-20→21`)**: PR #84, #85, #90, #91, #110, #111, #112

### 6.2 본 세션과 다른 세션 충돌 회피
- 본 세션은 **read-only 또는 본 세션 전용 디렉토리** (`_workspace/{pepadmet,pepmsnd,admet_ai}_local/`)에서만 작업
- 다른 세션 미커밋 변경 BE/FE 9 M 파일 + 73 untracked는 **손대지 않음** (세션 분리 컨벤션)
- PR 리베이스는 모두 worktree 격리 (`.worktrees/pr85-rebase`, `.worktrees/pr84-rebase`)

---

## 7. 사용자 4대 원칙 준수 점검

| 원칙 | 점검 |
|------|------|
| 시스템 완성 우선 (발표 X) | ✅ 7 PR 모두 시스템/코드/검증 산출 |
| 할루시네이션 금지 | ✅ Layer 1/2/3 unavailable/외삽/P4 정직, fallback 양측 보존, seed 흔들림 명시, PlifePred 확률값 발견 |
| codex/cursor-agent 적극 활용 | ✅ 24건 위임 |
| 끝까지 완성 | ✅ 5 머지 + 2 open (사용자 결정 대기) |

---

## 8. D-6 (2026-05-22) 권고 작업

### 본 세션 우선 (문서화)
- [ ] PR #111 사용자 머지 결정 (PRST 매트릭스, MERGEABLE 예상)
- [ ] PR #112 사용자 머지 결정 (Layer 2 실험, MERGEABLE 예상)
- [ ] MEETING_PREP Q&A 추가 정교화 (D-3 발표자료 대비)

### 외부 위임 후보 (codex/cursor-agent)
- [ ] pepADMET 저자 이메일 발송 결정 + KAERI 행정 (사용자 결정)
- [ ] Layer 2 재학습 재현성 정량화 (seed 고정, A/B)
- [ ] DGL libnvrtc 정비 후속 (cursor-agent 권고 2번)
- [ ] PRST-001 단일 후보 wet-lab 평가 시나리오 (회의 발표용)

### 다른 세션 영역 (본 세션 손대지 말 것)
- K-1/K-2 selectivity 결함 (action-items-closure-20260521 세션 잔여 Task #14)
- BE/FE M 파일 미커밋 변경
- worktree 3개 (feat-fe-*) main 머지

---

## 9. SOD 작성자 메모 (다음 세션 인계)

본 세션 = **`orchestrator-2026-05-20→21`** (어제 세션 연장).
오늘 작업의 진짜 출처를 PR 메타데이터에서 확인하려면:
- `gh pr view <PR번호> --json author,headRefName,createdAt` 사용
- `headRefName`이 `docs/meeting-prep-and-post-audit-20260520`, `feat/layer1-ensemble-framework-20260520`, `fix/binding-pocket-pdb-cif-auth-consistency-20260520`, `docs/pptx-2026-05-28-3layer-ensemble`, `feat/hle-regression-callable-wrapper-20260521`, `docs/prst-comprehensive-matrix-20260521`, `experiment/layer2-pepmsnd-retrain-20260521` → **본 세션 산출**

통합 EOD(`eod-2026-05-21-master-integrated.md`)는 `action-items-closure-20260521` 세션 시점에 작성되어 본 세션을 다른 세션으로 잘못 표기. 본 EOD가 본 세션 실제 산출.

---

## 10. 변경 이력

| 시각 | 변경 |
|------|------|
| 2026-05-21 EOD | 본 세션 분 명시 작성 (통합 EOD와 별개) — `orchestrator-2026-05-20→21` |

---

*작성: 2026-05-21 EOD (orchestrator-2026-05-20→21 세션 종료)*
