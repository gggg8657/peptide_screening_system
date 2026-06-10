# 마스터 인덱스 — 2026-04-06 제3차 월간회의 액션 아이템

**회의**: KAERI-AIRL-MOM-2026-003 | **일자**: 2026-04-06 | **작성**: 2026-05-19 | **최종 갱신**: 2026-05-20
**원본 회의록**: `../AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`

---

## 전체 현황 (한눈에)

| ID | 제목 | 담당 | 도메인 | 상태 | 선행 조건 | 정리 파일 | 프롬프트 |
|----|------|------|--------|------|---------|---------|---------|
| **A-01** | SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 | AI팀 | 도킹 | ✅ **PR #61 머지** (10 files, +43K) | A-10 | [A-01](A-01_SSTR_site_directed_docking.md) | [prompt](prompts/A-01_prompt.md) |
| **A-02** | 혈청 반감기 예측 도구 비교 조사 | AI팀·RI팀 | 약리학 | 🟡 wrapper 완료, **D-AA HIGH-BLOCKER** | — | [A-02](A-02_serum_halflife_tools.md) | [prompt](prompts/A-02_prompt.md) |
| **A-03** | Fab-ADMET *(=pepADMET, 2026-05-20 확인)* 정확도 검증 및 자체 학습 가능성 평가 | AI팀·RI팀 | 약리학 | 🟡 wrapper 완료, **HTTP 403 차단** | — | [A-03](A-03_Fab-ADMET_validation.md) · [research](A-03_research_fab_admet.md) | [prompt](prompts/A-03_prompt.md) |
| **A-04** | Top-K 후보 선정 복합 스코어링 체계 설계 | AI팀 | 스코어링 | ✅ **PR #62 머지** (Tier S/A/B/FAIL) | A-02·A-03·A-05 | [A-04](A-04_composite_scoring.md) | [prompt](prompts/A-04_prompt.md) |
| **A-05** | SST14 레퍼런스 ΔG 기준선 확립 | AI팀 | 도킹 | ✅ **main `8e7e1cc` direct push** (실측 확보) | (A-01 병행 권장) | [A-05](A-05_SST14_reference_dG.md) | [prompt](prompts/A-05_prompt.md) |
| **A-06** | 디퓨전 모델 기반 도킹 가속화 PoC | AI팀 | 도킹 | 🟡 스크립트 존재, 완성도 미확인 | A-07 연동 | [A-06](A-06_diffusion_docking_PoC.md) | [prompt](prompts/A-06_prompt.md) |
| **A-07** | DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집 | 서호성·안기범 | 인프라 | 🟡 매트릭스 작성, 외부 견적 대기 | — | [A-07](A-07_GPU_infra_quote.md) | [prompt](prompts/A-07_prompt.md) |
| ~~**A-08**~~ | ~~라이브러리 서버 마이그레이션 완료 및 검증~~ | ~~AI팀~~ | ~~도킹~~ | **삭제** (외부망 서버 배포 완료) | — | — |
| **A-09** | 최종 후보 3-4개 도출 및 합성 의뢰 준비 | AI팀·RI팀 | 최종선정 | ✅ **PR #63 머지** (PRST-001~004) | A-04 | [A-09](A-09_final_candidates_synthesis.md) | [prompt](prompts/A-09_prompt.md) |
| **A-10** | SSTR3 도킹 에러 해결 | AI팀 | 도킹 | ✅ **PR #60 머지** (fix `5f5f7af`) · ⚠ 별건 BUG | — | [A-10](A-10_SSTR3_docking_fix.md) | [prompt](prompts/A-10_prompt.md) |

> **📊 통합 진행 상태 리포트 (2026-05-20)**: [`STATUS_2026-05-20.md`](STATUS_2026-05-20.md) — 팀 정찰 결과 + 5개 핵심 변경 사항 + 갱신 필요 파일 + 다음 세션 권고
> **✅ BUG 후속 해결 확인**: A-10과 별건이던 **SSTR4 시그니처 `VILRYAKMKTA` SSTR1/SSTR4 중복 등록**은 `_SSTR_SIGNATURES`에서 공유 모티프가 제거되어 회귀 테스트 통과
> **🔴 가장 긴급**: `feat/p1-sprint-integration` PR 생성 + 머지 (P2 sprint 전체, CONDITIONAL PASS)

> **A-08 [삭제]**: 회의록 §3 기준 "라이브러리 서버 마이그레이션 완료" — 외부망 H100×8 서버 배포 완료(PDF §2.3)로 삭제 처리. 파일 미생성이 정상 상태.

---

## 도메인별 분류

### 🔬 도킹 / 스코어링 (T2)
```
A-10 (SSTR3 에러 해결)
  └─ A-01 (SSTR1/3/4/5 위치 지정 도킹)
A-05 (SST14 레퍼런스 ΔG 기준선) ── 병행
A-06 (디퓨전 모델 PoC) ── A-07 GPU 연동
```
- 담당 에이전트: `engineer-backend`, `reviewer-biology`

### 💊 약리학 (T3 — 부분 완료)
```
A-02 (혈청 반감기 도구 비교)
A-03 (Fab-ADMET 검증)
```
- 담당 에이전트: `reviewer-pharma`, `reviewer-chemistry`
- **상태**: wrapper/가드 등록은 완료, D-AA 지원과 pepADMET HTTP 403은 HIGH-BLOCKER로 잔존

### 📊 복합 스코어링 + 최종 후보 (T4)
```
A-04 (복합 스코어링 체계) ← A-02, A-03, A-05 입력 필요
  └─ A-09 (최종 후보 도출 및 합성 의뢰)
```
- 담당 에이전트: `engineer-backend`, `reviewer-pharma`, `reviewer-science`

### 🖥 인프라 (T5 — 부분 완료)
```
A-07 (GPU 서버 견적)
```
- 담당 에이전트: `engineer-infra`
- **상태**: 견적 매트릭스 작성, 외부 벤더 견적 대기

---

## 의존성 그래프

```
A-07 (GPU 견적)
  │
  └─── A-06 (디퓨전 PoC)

A-10 (SSTR3 fix)
  │
  └─── A-01 (위치 지정 도킹)

A-05 (ΔG 기준선) ─────────────────┐
A-02 (반감기 도구) ───────────────┤
A-03 (Fab-ADMET) ─────────────────┤
                                   ▼
                              A-04 (복합 스코어링)
                                   │
                                   └─── A-09 (최종 후보 도출)
```

---

## TPP KPI 매핑

| KPI | 기준 | 관련 액션 아이템 |
|-----|------|---------------|
| 결합 친화도 (SSTR2 선택성) | ΔΔG < −1 kcal/mol | A-01, A-05, A-10 |
| 혈청 반감기 TPP-B | ≥ 24시간 | A-02, A-04 |
| 혈청 반감기 TPP-C | ≥ 72시간 | A-02, A-04 |
| ADMET 독성 | Fab-ADMET 또는 대안 도구 기준 | A-03, A-04 |
| 최종 후보 수 | 3-4개 (Tier-S) | A-04, A-09 |
| 도킹 가속화 | 디퓨전 모델 PoC 성공 | A-06, A-07 |

---

## pharmacology_guards.py (Stage 5) 연동 현황

| 액션 아이템 | 연동 포인트 | 상태 |
|-----------|-----------|------|
| A-02 | `ENDPOINT_CONFIDENCE["halflife_<tool>"]` 등록 | 완료 — 7개 혈청 반감기 도구 등록, D-AA 미지원 경고 포함 |
| A-03 | `ENDPOINT_CONFIDENCE["admet_pepadmet"]`, `ENDPOINT_CONFIDENCE["pepadmet_toxicity"]` 등록 | 완료 — HTTP 403 및 D-AA 재검증 필요 경고 포함 |
| A-04 | `pipeline_local/scoring/composite_scorer.py` + `radiolysis_scorer.py` | 완료 — Tier S/A/B/FAIL, Hard Cutoff + WSS + Pareto |
| A-05 | `LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]`, `["SST14_SSTR2_ref_ddg_flexpep"]` | 완료 — Boltz-2 -95.024 REU, FlexPepDock mean 553.857 REU |
| A-09 | `runs_local/final_candidates/synthesis_orders/PRST-001~004.md` | 완료 — 후보별 합성 의뢰서 4개 존재 |

> 실제 코드 등록은 `engineer-backend`가 검증 결과 수신 후 수행.  
> H-06 가드: 모든 예측 함수에 `HEURISTIC_FUNCTION_DISCLAIMERS` 명세 필수.

---

## 미결 사항 통합 (§검증 필요)

### 데이터 정합성 ⚠ (docking 팀원 신고)
- [ ] **SSTR2 구조 ID 불일치**: 회의록 원문 **7T10/7T11** vs 로컬 `data/somatostatin_receptor/SSTR2_7XNA.pdb` (**7XNA**) — A-01/A-05 수행 전 담당팀 확정 필요

### A-02 (혈청 반감기)
- [ ] 🔴 **HIGH-BLOCKER: D-아미노산 지원 도구 부재** — pepMSND·CAMSOL 등 현재 도구 전부 L-AA 기반. D-AA 후보(Octreotide 계열) 반감기 예측 시 SST-14 유사도 4.83× 과대 추정 실측 (2026-05-20 확인). D-AA ≥1개 도구 확보 또는 자체 ML 모델 로드맵 필수.
- [ ] HLP 도구 1.6초 예측 재현 및 신뢰도 등급화
- [ ] 지방산 수식(lipidation) 지원 도구 존재 여부

### A-03 (Fab-ADMET = pepADMET — 명칭 정정 완료 2026-05-20)
- [x] ~~Fab-ADMET GitHub URL 확인~~ → **pepADMET** ([github.com/ifyoungnet/pepADMET](https://github.com/ifyoungnet/pepADMET), GPL-3.0)
- [x] ~~원 논문 AUC / Accuracy / F1 수집~~ → Tan et al. 2026 JCIM, AUC=0.949 (독성)
- [ ] 🔴 **pepADMET REST API HTTP 403 차단** — `pepadmet.ddai.tech` 자동화 호출 차단 확인 (2026-05-19). 로컬 설치(`git clone`) 우선 진행 필요. (V-02와 연동)
- [ ] **V-02**: pepADMET 로컬 설치 (`git clone https://github.com/ifyoungnet/pepADMET`) — 다음 세션 codex 위임
- [ ] **V-03**: Octreotide(D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr) 직접 입력 테스트 → D-아미노산 처리 여부 확인 — 다음 세션 engineer-backend 위임
- [ ] **V-04**: KAERI 상업적 활용 가능성 → GPL-3.0(로컬) vs CC BY-NC-SA(웹) 법무 검토

### A-10 별건 BUG — SSTR4 시그니처 충돌 ✅ 해결 확인
- [x] **SSTR4 시그니처 `VILRYAKMKTA` SSTR1/SSTR4 중복 등록** — `offtarget_dock.py::_SSTR_SIGNATURES`에서 공유 모티프가 제거되어 서브타입별 고유 시그니처만 유지됨. `test_offtarget_dock_cif_chain.py` 24건 PASS, `test_offtarget_dock_boltz.py` 24건 PASS / 4건 SKIP.

### A-05 (게이트 임계값 정합)
- [x] **SSOT 갱신**: `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max` = `498.4713` (FlexPepDock mean `553.857 REU × 0.9`)
- [ ] **코드 폴백 5곳 일괄 갱신**: `orchestrator.py:1211,1266,1524` / `step06_rosetta.py:190,910` / `rank_table.py:245` (모두 현재 `-5.0` 폴백)
- [x] `pharmacology_guards.py::LITERATURE_VALUES`에 SST14 ΔG 측정값 등록 (`SST14_SSTR2_ref_ddg_boltz2`, `SST14_SSTR2_ref_ddg_flexpep`)
- [ ] (주의) `DOCKING_GATE_THRESHOLD` 상수는 실제 코드에 존재하지 않음 — 이전 문서 표기는 잘못된 것

### A-06 (VRAM 확인)
- [ ] 현재 H100 NVL ×4 환경에서 디퓨전 모델 Multi-GPU 모드 가능 여부 검증 (실패 시 A-07 에스컬레이션)

### A-07 (벤더 견적 6건)
- [ ] DGX H100 / B200 / 자체 빌드 견적 매트릭스 — 모든 견적 셀 TBD (서호성/안기범 책임)

---

## 파일 구조

```
docs/meet_log/2026-04-06_action_items/
├── 00_MASTER_INDEX.md          ← 본 파일
├── README.md                   ← 디렉토리 사용 가이드
├── A-01_SSTR_site_directed_docking.md
├── A-02_serum_halflife_tools.md
├── A-03_Fab-ADMET_validation.md
├── A-04_composite_scoring.md
├── A-05_SST14_reference_dG.md
├── A-06_diffusion_docking_PoC.md
├── A-07_GPU_infra_quote.md
├── A-09_final_candidates_synthesis.md
├── A-10_SSTR3_docking_fix.md
└── prompts/
    ├── A-01_prompt.md   A-02_prompt.md   A-03_prompt.md
    ├── A-04_prompt.md   A-05_prompt.md   A-06_prompt.md
    ├── A-07_prompt.md   A-09_prompt.md   A-10_prompt.md
```

---

## scoring 모듈 — 실제 구현 상태 (A-04, A-09)

> ⚠️ scoring 팀원이 "신규 5종"으로 표기했으나 **2종은 이미 구현 존재**. 보강·재사용 대상으로 정정.

| 모듈 | 역할 | 액션 아이템 | 실제 상태 |
|------|------|------------|---------|
| `pipeline_local/scoring/composite_scorer.py` | Hard Cutoff + WSS + Pareto front Tier 분류 (S/A/B/FAIL) | A-04 | **구현 완료** — PR #62 머지 |
| `pipeline_local/scoring/radiolysis_scorer.py` | Cys·Met=3 / Phe·Tyr·Trp=2 / Pro·His·Leu=1 점수화 + ss_bond_intact 플래그 | A-04 | **구현 완료** — PR #62 머지 |
| `pipeline_local/scripts/composite_scorer.py` + `composite_scorer_cli.py` | CLI 래퍼 | A-04 | **이미 존재** |
| `runs_local/final_candidates/*.csv` | Hard Cutoff/Tier 후보 표 | A-09 | **산출물 존재** — `hard_cutoff_pass.csv`, `tier_s_candidates.csv`, `tier_b_candidates.csv` |
| `runs_local/final_candidates/synthesis_orders/PRST-001~004.md` | 후보별 합성 의뢰서 | A-09 | **산출물 존재** — PR #63 머지, 다양성 WARN 포함 |
| `select_final_candidates.py` / `synthesis_checker.py` / `generate_synthesis_request.py` | 후보 선정·합성성 검사·의뢰서 생성 자동화 스크립트 | A-09 | **현재 파일 없음** — PR #63 산출물은 위 runs_local 결과로 확인 |

상세 API는 `prompts/A-04_prompt.md`, `prompts/A-09_prompt.md` 참조.

---

*최초 작성: 2026-05-19 (pharma) | 보강: 2026-05-19 (team-lead — docking·scoring 보고 통합) | 갱신: 2026-05-20 (STATUS §6 반영 — A-04/A-05/A-09 실제 상태·경로·Tier 명칭 정렬)*
