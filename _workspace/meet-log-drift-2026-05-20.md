# meet_log ↔ 실제 코드 정합성 (T5 by sync)

**작성일**: 2026-05-20  
**작성자**: sync (도메인 정합성 라우터, team `session-sync-20260520`)  
**방법론**: read-only — git log/show/diff, 파일 직접 읽기  
**범위**: `docs/meet_log/2026-04-06_action_items/` ↔ 어제(2026-05-19) 실 구현 브랜치/커밋

---

## Action Item별 정합성 매트릭스

| A-ID | 정리 파일 상태 | 실제 브랜치 / 핵심 커밋 | 일치도 | 갱신 필요 사항 |
|------|--------------|----------------------|:------:|--------------|
| A-01 | 신규 | `feat/a01-sstr-site-directed-docking` / `bd0c568` (PR #61) | **95%** ✅ | 상태 "신규" → "완료" 갱신 필요 |
| A-04 | 신규, Tier S/A/B 3단계 | `feat/a04-composite-scoring` / `8d98861` (PR #62) | **80%** ⚠️ | Tier 명칭 불일치 — §A-04 항목 참고 |
| A-05 | 신규 | main 직접 커밋 `8e7e1cc` (PR 없음) | **90%** ⚠️ | 브랜치 stale — §A-05 항목 참고 |
| A-09 | 신규 | `feat/a09-final-candidates-synthesis` / `eaaba95` (PR #63) | **85%** ⚠️ | 의뢰서 파일 형식 불일치 — §A-09 항목 참고 |
| A-08 | (삭제 — 파일 미생성) | `_workspace/release/sod-2026-05-19-A08-meeting-recovery.md` 존재 | **100%** ✅ | 정합 확인됨 — §A-08 항목 참고 |
| A-02 | 신규, 미결 5건 | 실 테스트 완료 (`39b6e39` P1 sprint 포함) | **75%** ⚠️ | 정리 파일 §미결 사항 업데이트 필요 |
| A-03 | "Fab-ADMET" 표기 | researcher SOD 완료, 명칭 정정 | **90%** ✅ | "Fab-ADMET" → "pepADMET" 정정 완료 반영 필요 |
| A-10 | 신규 | `fix/a10-sstr3-docking` / `233611d` (PR #60) | **100%** ✅ | 완료, 상태 갱신만 필요 |

---

## A-08 정체 파악

### SOD 파일 내용 (`sod-2026-05-19-A08-meeting-recovery.md`)

`meeting-recovery`라는 이름은 **researcher가 PDF 원문을 확인하여 A-08 삭제 결정의 근거를 복원(recover)한 조사 작업**을 의미한다. A-08 자체가 신규 액션 아이템이 아님.

조사 결론:
- A-08 원래 내용: "라이브러리 서버 마이그레이션 완료 및 검증"
- 삭제 사유: 회의 당일 외부망 H100×8 배포 완료 보고 (PDF §2.3) → 마이그레이션 불필요
- PDF §3 표에서 A-08 행이 취소선(strikethrough) + 상태 "삭제"로 명기됨

### 본 세션 처리와의 충돌 여부

**충돌 없음**. 본 세션이 "회의록 §3 '외부망 H100×8 서버 배포 완료 → A-08 삭제'"로 처리한 것과 SOD 파일 결론이 완전히 일치한다.

`00_MASTER_INDEX.md`의 A-08 행이 `~~삭제~~` + 사유까지 이미 정확히 기록되어 있다.

### 결론

`_workspace/release/sod-2026-05-19-A08-meeting-recovery.md`는 삭제 처리 정당성을 PDF 원문에서 검증한 사후 확인 문서다. **어떤 정합성 문제도 없음**.

---

## A-09 합성 의뢰서 산출물 위치

### 정리 파일 명세 (기대 경로)

```
runs_local/final_candidates/synthesis_request_<YYYYMMDD>.md  ← 단일 통합 파일
```

### 실제 저장 위치 (확인됨)

```
runs_local/final_candidates/
├── synthesis_orders/
│   ├── PRST-001.md   (Tier S, AGCKNIIWKTITSC, WSS=1.000)
│   ├── PRST-002.md   (Tier B, AGCKNFIWKTITSC, WSS=0.582)
│   ├── PRST-003.md   (Tier B, AGCRNFIWKTITSC, WSS=0.271)
│   └── PRST-004.md   (Tier B, AICKNFIWKTITSC, WSS=0.365)
├── tier_s_candidates.csv
├── tier_a_candidates.csv   (empty — Tier A 없음)
├── tier_b_candidates.csv
├── all_candidates.csv
├── hard_cutoff_pass.csv
└── summary.json
```

추가로 `_workspace/release/sod-2026-05-19-A09-final-candidates-synthesis.md` (277줄 종합 보고서) 존재.

### 불일치 사항

정리 파일은 단일 `synthesis_request_YYYYMMDD.md`를 예상했으나, 실제 구현은 **후보별 개별 파일 4개** (`synthesis_orders/PRST-NNN.md`). 내용 완결성은 동등하거나 더 상세함.

### 4개 후보 요약

| ID | 서열 | Tier | WSS | 주요 특징 |
|----|------|:---:|:---:|---------|
| PRST-001 | AGCKNIIWKTITSC | **S** | 1.000 | radiolysis_count=1 (최우선) |
| PRST-002 | AGCKNFIWKTITSC | B | 0.582 | F6 pharmacophore 유지 |
| PRST-004 | AICKNFIWKTITSC | B | 0.365 | G2→I, cand03 SAR 연장 |
| PRST-003 | AGCRNFIWKTITSC | B | 0.271 | K4→R, N-말단 DOTA 경로 |

⚠️ **다양성 경고**: 후보 간 서열 identity 86~93% (기준 ≤80% 미달). 14aa SS bond 구조 제약 상 불가피. WARN 처리 후 진행 기록됨.

---

## A-04 Tier 체계 정합성

### 세 곳에서 발견된 표현

| 출처 | Tier 명칭 |
|------|---------|
| 정리 파일 `A-04_composite_scoring.md` §Step 3 | S, A, B (3단계, FAIL 암묵적) |
| **commit 제목** `8d98861` | "Tier **S/A/B/C** 분류" |
| **SOD 파일** `sod-2026-05-19-A04-composite-scoring.md` §5 | S, A, B, **FAIL** (4단계) |
| **실제 코드** `pipeline_local/scoring/composite_scorer.py` L111~122 | `Tier.S / Tier.A / Tier.B / Tier.FAIL` |

### 판정

**commit 제목의 "C"는 오기재**다.

- 코드에 `Tier.C`는 존재하지 않음 (`grep "\"C\"" composite_scorer.py` 결과 없음)
- SOD와 코드 모두 S/A/B/FAIL 4단계 일치
- SOD 미완료 항목에 "Tier C 분류 — OPEN (현재 spec은 S/A/B/FAIL 4단계. orchestrator 요청 시 C 추가)" 명시 → C는 미래 옵션

### 정확한 체계

| Tier | 조건 |
|------|------|
| S | WSS 상위 20% AND Pareto rank=1 |
| A | WSS 상위 20% XOR Pareto rank=1 |
| B | 나머지 Hard Cutoff 통과 후보 |
| **FAIL** | Hard Cutoff 미통과 (≥1개 게이트 탈락) |

정리 파일 `A-04_composite_scoring.md` 갱신 필요: §Step 3 최종 순위 결정에 **FAIL** 단계 명시.

---

## A-05 vs A-10 혼동 여부

### 브랜치 상태 (확인됨)

```
feat/a05-sst14-reference-dg
  └── 최신 커밋: 5f5f7af "fix(docking): handle SSTR3 8XIR chain selection (#60)"
  └── A-05 작업 커밋 8e7e1cc 이 브랜치에 없음 (10개 커밋 뒤처짐)

fix/a10-sstr3-docking
  └── 최신 커밋: 233611d "fix(docking): handle SSTR3 8XIR chain selection"
  └── 5f5f7af (#60)는 이 브랜치를 main에 머지한 결과
```

### A-05 실제 작업 경로

`commit 8e7e1cc "feat(scoring): A-05 SST14 reference dG n=10 FlexPepDock 도킹 + 통계"`는  
**main 브랜치에 직접 push**되었다 (PR 없음). SOD 파일이 명시: "커밋: `8e7e1cc` (main 직접 push 완료)".

`feat/a05-sst14-reference-dg` 브랜치는 `8e7e1cc` 커밋을 포함하지 않으며, A-10 fix PR #60이 머지된 시점에서 멈춰있다.

### 판정

**혼동이 아니다. 브랜치가 stale 상태일 뿐.**

- A-05 작업은 main에 완료됨 ✅
- A-10 작업은 `fix/a10-sstr3-docking` → PR #60으로 완료됨 ✅
- `feat/a05-sst14-reference-dg` 브랜치는 A-05 작업이 main 직접 커밋으로 종결되면서 사용되지 않은 채 남겨진 stale 브랜치

정리 파일 `A-05_SST14_reference_dG.md` 갱신 필요: 상태 "신규" → "완료", 실측값 (mean=553.857 REU, σ=4.024) 반영.

---

## D-AA pepADMET 테스트 진행 상태 (A-02/A-03)

### A-02 (혈청 반감기 도구 비교)

**어제 진행된 작업 (어제 SOD `sod-2026-05-19-A02-followup-pepadmet-daa-test.md`)**:

researcher가 pepADMET 웹서버 실 POST 테스트 7건 수행 (~9.5분):
- SST-14 HBN 예측: 14.484 min (실측 3분 대비 4.83× 과대)
- D-AA half-life 지원: **NO (HIGH-BLOCKER 확정)**
- D-AA modification 옵션: 40종 중 0개
- 비표준 AA 입력 시 silent error 확인

**정리 파일 `A-02_serum_halflife_tools.md` §미결 사항과 대비**:

| 미결 항목 | 실 테스트 결과 |
|---------|-------------|
| HLP 도구 1.6초 예측 재현 | ⚠️ 미수행 (HLP 미포함) |
| PeptideStability ML GitHub 확인 | ⚠️ 미수행 |
| 지방산 수식 지원 도구 | ⚠️ 미수행 |
| D-아미노산 지원 도구 ≥1개 확보 | ✅ **HIGH-BLOCKER 확정** (pepADMET 미지원) |
| MD 기반 stability 예측 상관관계 | ⚠️ 미수행 |

추가로 `39b6e39` P1 sprint에서 `predict_halflife_pepmsnd.py` (PlifePred2 + PepMSND 래퍼) 신설됨. D-AA 미지원 명시 + UNKNOWN grade 등록.

**정리 파일 갱신 필요**: 미결 사항 中 "D-AA 지원 ≥1개 확보" 항목에 HIGH-BLOCKER 결과 반영.

### A-03 (Fab-ADMET 검증)

**진행 완료**:
- "Fab-ADMET" 오기재 확정 → 실제 도구는 **pepADMET** (2025 JCIM)
- 사용자 직접 확인 (2026-05-19 V-01 해결)
- pepADMET 성능 표 (AUC, D-AA 지원 여부, 환형 지원 여부) 문헌 기반 정리

**정리 파일 `A-03_Fab-ADMET_validation.md` 갱신 필요**: 
- 파일 이름의 "Fab-ADMET" → 내용 상 pepADMET으로 명시
- 상태 "신규" → "완료"

---

## 추가 발견

### 1. A-09 브랜치 vs main 커밋 이원화

`feat/a09-final-candidates-synthesis` 브랜치의 A-09 커밋: `eaaba95`  
main의 A-09 커밋: `7b53dca` (PR #63 머지 결과)  

두 커밋의 diff 첫 줄이 동일 (`sod-2026-05-19-A09-final-candidates-synthesis.md` 신규 파일)로 내용 동일한 별도 커밋. 이는 PR 머지 시 별도 커밋이 생성되는 정상적인 git workflow다.

### 2. P1 Sprint (`39b6e39`) — 정리 파일 미반영

A-02/A-03 정리 파일에는 언급되지 않은 **P1 sprint 산출물**이 main에 존재:

```
pipeline_local/scripts/predict_halflife_pepmsnd.py    (PlifePred2 + PepMSND 래퍼)
pipeline_local/scripts/predict_admet_pepadmet.py      (pepADMET + modlamp fallback)
pipeline_local/scripts/sequence_to_smiles.py          (L-AA→SMILES + D-AA 19종 + DOTA)
```

55/55 tests pass. `ENDPOINT_CONFIDENCE` 신규 6건 + admet 추가 등록됨.

**정리 파일 갱신 필요**: A-02 §"본 프로젝트 매핑"에 세 wrapper 스크립트 추가.

### 3. P2 Sprint — 정리 파일 범위 외 신규 기능

어제 P2 sprint에서 구현된 내용 (Action Items와 무관한 독립 기능):
- `eeae158`: BindingPocketEditor + `/binding-pocket` 라우트 + `useBindingPocket` 훅 (FE)
- `e83fda9`: box_size Pydantic validation fix
- `84698f4`: Boltz-2 SSTR2-SST14 complex 생성 (Task #38, issue #67)

이들은 meet_log Action Items에 없는 항목이므로 정리 파일 갱신 대상 아님.

### 4. A-05 값 불일치 (Boltz2 vs FlexPepDock)

A-04 SOD가 `SST14_SSTR2_ref_ddg_boltz2 = -95.024 REU`를 사용하는 반면,  
A-05 SOD는 `SST14_SSTR2_ref_ddg_flexpep = 553.857 REU` (FlexPepDock, **양수**).

이 두 수치는 **다른 도킹 엔진 결과**이며 단위/부호 체계가 다르다:
- Boltz-2: iPTM proxy (`-100 × iptm`), 음수 = 강한 결합
- FlexPepDock: Rosetta Energy Units (REU), **양수가 정상** (fallback 모드, 상대적 비교 기준)

정합성 문제 없음. 단 정리 파일 A-05.md에 이 구분이 명시되지 않아 혼동 위험 있음. 갱신 권고.

### 5. `sod-2026-05-19-comprehensive-plan.md` 내용 확인

어제 전체 계획 문서. Action Items 9/9 완료 및 P1/P2 sprint + Task #38 + A-06 DiffPepDock PoC 포함. `V-검증 HIGH 6건`은 모두 wet-lab 의존 (Gate-2 대기). 정리 파일과 충돌 없음.

### 6. A-01 Step 5 (SSTR3 재도킹) 상태

A-01 정리 파일은 Step 5를 "A-10 선행 이후 수행"으로 기재. A-10이 PR #60으로 완료되었으므로 SSTR3 재도킹은 이제 blocking 없음. 단 실제 재도킹 수행 여부는 확인되지 않음 (A-01 commit `bd0c568`에 SSTR3 재도킹 결과 포함 여부 미확인).

---

## 갱신 권장 사항 (team-lead에게 전달용)

> **주의**: 아래는 본 세션이 직접 수정하지 않음. team-lead가 처리.

### 즉시 갱신 필요 (높음)

| 파일 | 갱신 내용 |
|------|---------|
| `A-01_SSTR_site_directed_docking.md` | 상태: "신규" → "완료". Step 1-4 완료(PR #61). Step 5(SSTR3 재도킹) 수행 여부 확인 후 업데이트 |
| `A-04_composite_scoring.md` | §Step 3 최종 순위 결정에 FAIL 단계 명시 ("Tier-B 나머지" 아래 "Tier-FAIL: Hard Cutoff 미통과" 추가) |
| `A-05_SST14_reference_dG.md` | 상태: "신규" → "완료". 실측값 mean=553.857 REU (FlexPepDock, σ=4.024) 및 Boltz2 기준값 -95.024 REU 구분 명시. 커밋 `8e7e1cc` main 직접 push 기록 |
| `A-09_final_candidates_synthesis.md` | 합성 의뢰서 파일 경로 정정: `synthesis_request_YYYYMMDD.md` → `synthesis_orders/PRST-001~004.md`. 다양성 WARN 기록 추가. 상태 "완료" |

### 갱신 권장 (보통)

| 파일 | 갱신 내용 |
|------|---------|
| `A-02_serum_halflife_tools.md` | §미결 사항: D-AA 확정 결과 반영 (HIGH-BLOCKER). predict_halflife_pepmsnd.py wrapper 신설 추가 |
| `A-03_Fab-ADMET_validation.md` | 상태 "완료". "Fab-ADMET" = pepADMET 확정 명시 (V-01 사용자 직접 확인). pepADMET 실 테스트 결과 요약 추가 |
| `A-10_SSTR3_docking_fix.md` | 상태 "완료". PR #60 커밋 `5f5f7af` 기록 |
| `00_MASTER_INDEX.md` | A-01/A-04/A-05/A-09/A-10 상태 갱신, A-03 명칭 정정 |

### 확인 후 갱신 (낮음)

| 항목 | 확인 필요 내용 |
|------|-------------|
| A-01 Step 5 | SSTR3 재도킹 (`bd0c568` 내 포함 여부 확인) |
| `feat/a05-sst14-reference-dg` 브랜치 | stale 브랜치 삭제 또는 `8e7e1cc` fast-forward 처리 여부 결정 |
| A-09 서열 다양성 WARN | Gate-2 진입 전 RI팀과 4개 후보 다양성 충분성 협의 필요 |

---

*검증 완료: 2026-05-20 | sync (reviewer-science)*  
*근거: git log --oneline, git show --stat, Read(파일 직접), Bash(grep)*
