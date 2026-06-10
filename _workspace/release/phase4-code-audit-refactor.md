# Phase 4 — 코드 감사 및 리팩토링 필요성 검토
**작성일**: 2026-05-27  
**리뷰어**: reviewer-code  
**근거 파일**: narrative v3, 3-layer 격차 분석, phase2/3 smoke, session-overview, ACTION ITEMS 9건, 직접 ls/wc-l/grep 결과  
**신뢰 등급 범례**: HIGH = 코드 직접 확인 / MED = 보고서 기술에 근거 / LOW = 추론

---

## 1. 요약 (PASS/FAIL/CONDITIONAL)

**판정: CONDITIONAL**

A-01~A-10 기준 과학적 산출물(도킹 좌표, 후보 4건, composite scorer)은 확보되었다.  
그러나 코드베이스 상태는 세 가지 구조적 문제를 동시에 가지고 있다.

1. **enrichment 경로와 ensemble 모듈이 분리**되어 있어 narrative v3 §5.4가 명시한 "서술과 코드 사이의 격차"가 6월 회의 전까지 닫히지 않으면 의사결정 오류 리스크가 지속된다.
2. **3중 파이프라인 분리**(pipeline_local / pipelines/silo_{a,b} / AgenticAI4SCIENCE 트랙)가 각자 독립 실행되고 공유 계약이 없어 통합 검증이 불가능한 구조다.
3. **워크트리 77개(로컬 31 + /tmp 46)**, 실험 런 61개, 릴리스 문서 129개가 누적되어 유지비용이 증가하고 있으나, 이 중 상당수는 정리 정책 부재이지 구조적 결함이 아니다.

리팩토링은 필요하다. 단 **3개월 이내에 전체 재구조화를 시도하는 것은 비현실적**이다. P0~P1에 한정한 incremental 접근을 권장한다.

---

## 2. 액션 리스트 충족 매트릭스

### 평가 기준
- **코드 산출물**: 직접 확인한 파일 경로 및 LOC (HIGH)
- **테스트**: `pipeline_local/tests/` 기준 736 pass (5 skip, 2 xfail) — be-p0-fix 검증 기준 (HIGH)
- **5/19 이후 추가 발견**: session-overview, narrative v3 §5.4, 3-layer 격차 분석 기반

---

**A-01** — SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹  
- **회의 요구**: "SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 수행 (SSTR3 에러 해결 포함). 기한: 5월 회의 전."  
- **코드 산출물**: `pipeline_local/scripts/offtarget_dock.py` (직접 확인); `binding_pocket_SSTR2.json`; SSTR1/3/4/5 aligned PDB 4건; PR #61 main merge [MED]  
- **테스트 통과**: 38건 (A-01 연관), 전체 736 PASS 포함 [HIGH]  
- **충족도**: ✅ 완전  
- **충족도 근거**: RMSD 2.77~3.13 Å, 회의 KPI 4 Å 이내. SSTR3 chain 선택 오류 해결. `_SSTR_SIGNATURES` 공유 모티프 제거로 SSTR1/SSTR4 오매칭 회귀 방지 [HIGH]  
- **미충족 잔존 작업**: TM-align 대신 cealign 사용 — 도구 변경 보고 필요. SSTR2 기준 구조 7XNA vs 회의록 원문 7T10/7T11 불일치는 미해소 [MED]  
- **회의 KPI 부합**: Y

---

**A-02** — 혈청 반감기 예측 도구 비교 조사  
- **회의 요구**: "혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가). 담당: AI팀/RI팀."  
- **코드 산출물**: `pipeline_local/scripts/predict_halflife_pepmsnd.py`; `pharmacology_guards.py::ENDPOINT_CONFIDENCE` 혈청 계열 11개 키 등록 (halflife_pepmsnd, pepmsnd_local_halflife_hours 등); A-02 도구 비교 문서 [HIGH]  
- **테스트 통과**: 736 PASS 포함 (혈청 반감기 테스트 별도 집계 불가 — 전체 포함) [HIGH]  
- **충족도**: 🟡 부분  
- **충족도 근거**: 7종 비교 완료, 회의 요구 "5종 이상" 충족. 그러나 D-AA 지원 도구 0개, Octreotide 4.83× 과대 추정 확인. `ENDPOINT_CONFIDENCE`에 `benchmark_test_r2_hours_2026_05_20: -0.028` 기록 — 의사결정용 절대값 제공 불가 상태 [HIGH]  
  - 추가: `pharmacology_guards.py` L954 이후 동일 키(`halflife_webmetabase_indirect`, `halflife_hle_regression_albumin`) 중복 정의 확인 — 후행 정의가 우선 적용됨 [HIGH]  
- **미충족 잔존 작업**: D-AA 처리 도구 0개 → wet-lab serum stability 측정 병행 필요. pepMSND Layer 2 R²=-0.028 → 순위 신호조차 신뢰 불가. HLP 재현 및 신뢰도 등급화 미완  
- **회의 KPI 부합**: Partial (비교 충족, 핵심 목표인 정확도 확보 불충족)

---

**A-03** — Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가  
- **회의 요구**: "Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가. 담당: AI팀."  
- **코드 산출물**: `pipeline_local/scripts/predict_admet_pepadmet.py`; `pipeline_local/scripts/predict_admet_ai_wrapper.py` (`recommended_for_decision=False` 항상); `pipeline_local/pepadmet_ood/ood_detection.py`; pepADMET 저자 문의 이메일 초안 [HIGH]  
- **테스트 통과**: 736 PASS 포함 [HIGH]  
- **충족도**: 🟡 부분  
- **충족도 근거**: "Fab-ADMET" = pepADMET 명칭 정정 완료. D-AA·cyclic·DOTA OOD 한계 문서화. 그러나 pepADMET REST API HTTP 403 차단으로 자동화 미완성. `pepadmet` conda env에서 `import pepadmet` 실패 확인 (phase2 smoke 기준) [HIGH]  
  - PR #113 pepADMET 재학습 + OOD detection main merge [MED]  
  - PR #117 (ADMET divergence guard, `e3a5413`) 현재 브랜치 및 main 미포함 [HIGH]  
- **미충족 잔존 작업**: PRST 후보용 ADMET 의사결정 모델 미확보. pepADMET import 실패 환경 미해소. KAERI GPL-3.0 / CC BY-NC-SA 법무 검토 미착수  
- **회의 KPI 부합**: Partial

---

**A-04** — Top-K 후보 선정 복합 스코어링 체계 설계  
- **회의 요구**: "ΔG + 반감기 + 셀렉티비티 + ADMET 통합 복합 스코어링 체계 설계."  
- **코드 산출물**: `pipeline_local/scoring/composite_scorer.py` (1,118 LOC); `pipeline_local/scoring/radiolysis_scorer.py`; `pipeline_local/scripts/composite_scorer.py` (별도 CLI 래퍼, 1,118 LOC — 동명 파일 2개 존재); PR #62 main merge [HIGH]  
- **테스트 통과**: 73건 (A-04 연관), 전체 736 PASS 포함 [HIGH]  
- **충족도**: ✅ 완전 (스코어링 구조 관점에서)  
- **충족도 근거**: Hard Cutoff 5개, WSS(ΔG 0.35 / selectivity 0.25 / half-life 0.20 / ADMET 0.10 / radiolysis 0.10), Pareto front, Tier S/A/B/FAIL 구현 확인 [HIGH]  
  - **주의**: `enrich_candidates_from_wrappers`가 `run_routed_halflife`를 호출하지 않음 — ADMET/반감기 입력값이 실제 3-Layer에서 오지 않음 [HIGH]  
- **미충족 잔존 작업**: canonical enrichment 경로 합의 필요 (6월 회의 의제). 동명 파일 `pipeline_local/scoring/composite_scorer.py` vs `pipeline_local/scripts/composite_scorer.py` 혼재  
- **회의 KPI 부합**: Y (구조 완성), Partial (실제 enrichment 경로 불일치)

---

**A-05** — SST14 레퍼런스 ΔG 기준선 확립  
- **회의 요구**: "SST14 레퍼런스 ΔG n회 반복 mean 기준, 가변 임계값 적용."  
- **코드 산출물**: `gate_thresholds.yaml::rosetta_ddg_max = 498.4713`; `pharmacology_guards.py::LITERATURE_VALUES`; main commit `8e7e1cc` [HIGH]  
- **테스트 통과**: 736 PASS 포함 [HIGH]  
- **충족도**: ✅ 완전  
- **충족도 근거**: FlexPepDock mean 553.857 REU, σ=4.024 (KPI σ<5 충족). `rosetta_ddg_max = 553.857 × 0.9 = 498.4713` 반영. Boltz-2 비교 -95.024 REU 별도 기록 [HIGH]  
  - **잔존 기술부채**: `orchestrator.py` L1211, L1266, L1524에 `get("rosetta_ddg_max", 498.4713)` hardcode fallback 3곳 존재 — 설정 파일 부재 시 동일값으로 폴백되므로 기능상 문제는 없으나, 단일 진실 원천(SSOT) 원칙 위반 [HIGH]  
- **미충족 잔존 작업**: cryo-EM ground truth 부재로 절대 pose validation 불가 (도구 한계, 코드 이슈 아님)  
- **회의 KPI 부합**: Y

---

**A-06** — 디퓨전 모델 기반 도킹 가속화 PoC  
- **회의 요구**: "PoC 수행 (정확도 vs Rosetta 비교). RMSD ≤2 Å 재현율 80% 이상이면 1차 필터 도입 검토."  
- **코드 산출물**: DiffPepDock 평가 보고; `runs_local/diffdock_poc/` (untracked); `HEURISTIC_FUNCTION_DISCLAIMERS`에 NOT_RECOMMENDED 사유 등록 [HIGH]  
- **테스트 통과**: 별도 DiffPepDock 테스트 없음 [HIGH]  
- **충족도**: ✅ 완전 (평가 완료, 결론 도출)  
- **충족도 근거**: SS bond 처리 한계 명확히 문서화. RMSD ≤2 Å 재현율 기준 미충족으로 NOT_RECOMMENDED 판정. 회의가 요구한 것은 PoC 수행 및 결론 도출이었으며, 성공 결과가 아니었음 [HIGH]  
- **미충족 잔존 작업**: GPU VRAM 120 GB 요구는 A-07과 연동. A-07 해결 전까지 본 항목 재시도 불가  
- **회의 KPI 부합**: Y (평가 완료) / N (도입 가능 결론 부재)

---

**A-07** — DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집  
- **회의 요구**: "최소 2개 벤더 견적. 비교 항목: VRAM, NVLink, 전력/냉각, 납기, 유지보수 계약."  
- **코드 산출물**: 견적 비교 매트릭스 문서; `A-07_GPU_infra_quote.md` [MED]  
- **테스트 통과**: N/A  
- **충족도**: 🟡 부분 (담당 외부)  
- **충족도 근거**: 비교 항목 양식과 체크리스트 작성 완료. 외부 벤더 실제 견적은 서호성/안기범 담당 영역으로 AI팀 제어 밖 [MED]  
- **미충족 잔존 작업**: DGX H100, DGX B200 최소 2벤더 실제 견적 모든 셀 TBD. Schrödinger 도입 시 Desmond/FEP+ throughput 항목 추가 필요  
- **회의 KPI 부합**: Partial

---

**A-08** — 라이브러리 서버 마이그레이션  
- **충족도**: N/A 삭제  
- **충족도 근거**: 회의 당일 삭제 결정. 외부망 서버 배포 완료로 불요 처리 [HIGH]  
- **회의 KPI 부합**: N/A

---

**A-09** — 최종 후보 3~4개 도출 및 합성 의뢰 준비  
- **회의 요구**: "최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행)."  
- **코드 산출물**: `runs_local/final_candidates/synthesis_orders/PRST-001~004.md` 4건 (각 6~9 KB); `tier_s_candidates.csv`; `tier_b_candidates.csv`; PR #63 main merge [HIGH]  
- **테스트 통과**: 전체 736 PASS 포함 [HIGH]  
- **충족도**: ✅ 완전 (산출물 관점)  
- **충족도 근거**: PRST-001 (Tier S, WSS=1.000), PRST-002~004 (Tier B) 도출. 합성 의뢰서 4건 작성. Gate-2 진입 결정은 회의 의제로 적절히 이관 [HIGH]  
  - **주의**: sequence identity 86~93% — 권장 80% 미달. 합성 의뢰서에 ADMET=1.00 OOD 가능성, H-06 disclaimer 수동 포함 [HIGH]  
  - 합성 의뢰서에 "3-Layer", "ensemble_halflife_hours", "recommended_for_decision" 표기 없음 — 사람이 작성한 H-06 문장으로 동일 정책 흡수 [HIGH]  
- **미충족 잔존 작업**: 후보 다양성 WARN 해소 방안 6월까지 필요. 실측 패키지(Ki, serum stability, hemolysis, RCP) 없이 Gate-2 통과 불가  
- **회의 KPI 부합**: Y

---

**A-10** — SSTR3 도킹 에러 해결  
- **회의 요구**: "SSTR3 도킹 에러 원인 분석 및 해결."  
- **코드 산출물**: `pipeline_local/scripts/offtarget_dock.py` chain 선택 로직; `test_offtarget_dock_cif_chain.py` 24건; `test_offtarget_dock_boltz.py` 24건 PASS; PR #60 main merge [HIGH]  
- **테스트 통과**: 48건 (A-10 연관), 전체 736 PASS 포함 [HIGH]  
- **충족도**: ✅ 완전  
- **충족도 근거**: 8XIR multi-chain 처리 로직 수정. SSTR1/SSTR4 공유 모티프(`VILRYAKMKTA`) 제거로 오매칭 근본 해결. smoke ddg=-92.09 정상 실행 [HIGH]  
- **미충족 잔존 작업**: 없음  
- **회의 KPI 부합**: Y

---

### 5/19 이후 추가 발견 항목

**후속-1: PR #85 3-Layer Ensemble (enrichment 불연결)**  
- **발견**: 3-layer 격차 분석 + narrative v3 §5.4  
- **사실**: PR #85 main merge 완료. 그러나 `enrich_candidates_from_wrappers`는 `run_routed_halflife`, `compute_layer1_halflife`, `predict_admet_layer3`를 호출하지 않음 [HIGH]  
- **충족도**: 🟡 부분 — 모듈 존재, 표준 경로 미연결  
- **영향**: narrative와 코드 사이 격차가 6월 회의 전까지 닫히지 않으면 발표 서술 신뢰도 손상

**후속-2: PR #90 binding pocket fix**  
- **발견**: session-overview worktree 목록  
- **사실**: `fix/pdb-index-k1-20260526` 브랜치 존재, main merge 여부 직접 확인 불가 [MED]  
- **충족도**: 🟡 부분

**후속-3: PR #117 ADMET divergence guard 미머지**  
- **사실**: 커밋 `e3a5413` 현재 브랜치 및 main 미포함. `fix/fe-stale-runid-20260526`에만 존재 [HIGH]  
- **충족도**: ❌ 미달 — 발표에서 #117을 main 반영 항목으로 언급 불가

**후속-4: PR #112 Layer 2 재학습 OPEN**  
- **사실**: `experiment/layer2-pepmsnd-retrain-20260521` 브랜치 OPEN (5일). `(#112)` 머지 커밋 없음. PR #115를 통해 PPTX 부록에만 반영됨 [HIGH]  
- **충족도**: ❌ 미달 — 별도 브랜치 실험 결과이며 main 미포함

**후속-5: PR #11 16일째 방치**  
- **사실**: `proposal/postmortem-r2r3-3path` 브랜치, 2026-05-11 이후 업데이트 없음 [HIGH]  
- **충족도**: ❌ 미달 — R1~R7 통합 정정 진단이 미해소 상태로 부채 누적

**후속-6: BE app import 실패 (P0, 해결됨)**  
- **사실**: `backend/routers/benchmark.py`의 `llm_benchmark` import가 FastAPI app 전체를 차단. be-p0-fix로 router optional 처리 후 `OK 83 routes` 확인 [HIGH]  
- **현 상태**: 해결됨 — `/api/benchmark/results` 503 반환은 허용된 degraded mode

**후속-7: FE smoke test 실패 1건**  
- **사실**: `App.smoke.test.tsx:95` `getByRole('button', { name: /more/i })` 실패. 118 PASS, 1 FAIL [HIGH]  
- **충족도**: ❌ 미달 (접근성 회귀 가능성)

**후속-8: FE 미구현 endpoint 2건**  
- **사실**: `/api/archives/top-k`, `/api/candidate/{candidate_id}/report` BE router 없음 [HIGH]  
- **충족도**: ❌ 미달

---

### 충족 통계 요약

| 구분 | 원래 8건 | 후속 발견 8건 |
|------|---------|------------|
| 완전 충족 | 6건 (A-01, A-04, A-05, A-06, A-09, A-10) | 1건 (후속-6 P0 해결) |
| 부분 충족 | 2건 (A-02, A-03) | 2건 (후속-1, 후속-2) |
| 미달 | 0건 | 4건 (후속-3, 후속-4, 후속-5, 후속-7/8) |
| N/A 삭제 | 1건 (A-08) | — |
| 외부 대기 | A-07 (부분) | — |

원래 8건 기준: **6건 충족, 2건 부분, 0건 미달, 1건 삭제** (narrative v3 §4 매트릭스와 정합)  
후속 포함 16건 기준: **7건 충족, 4건 부분, 5건 미달**

---

## 3. 리팩토링 필요성 분석

### (A) 현재 구조의 구체적 문제점

**3중 파이프라인 분리**

현재 저장소에는 사실상 독립된 세 개의 파이프라인이 공존한다.

| 경로 | 역할 | 상호 결합 |
|------|------|---------|
| `pipeline_local/` (orchestrator.py 2,479 LOC) | 로컬 BE 통합, 표준 enrichment 경로, 736 테스트 | 나머지 두 패키지와 직접 import 없음 |
| `pipelines/silo_a/`, `silo_b/`, `shared/` | 패키지 수준 오케스트레이터, UnifiedCandidate 스키마 | `silo_a/arms.py`가 `silo_b.docking`, `silo_b.relax`를 lazy import [HIGH] |
| `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/` | AG_src(1,538 LOC orchestrator), BE(FastAPI), FE(React/Vite), pyrosetta_flow(1,621 LOC runner) | 독립 실행. pipeline_local과 공유 import 없음 [HIGH] |

phase2 smoke 결과: `pipeline_local.LocalPipelineOrchestrator`와 `pipelines.silo_a.SiloAOrchestrator`는 **별도 패키지** — dual 통합은 `--dual` 플래그 + 설정 합의 없이는 자동 연동되지 않음 [HIGH]

합리성 판단: 3중 분리는 초기 실험-통합 사이클의 흔적이다. `pipeline_local`이 사실상 운영 베이스이고 나머지는 실험/모듈화 시도이다. 구조 자체는 이해 가능하지만, `UnifiedCandidate` 계약이 실제 산출물 JSON과 스키마가 다른 상태(`phase2-dual-silo-smoke §5`)가 방치되면 통합 검증이 영구 불가능해진다. [HIGH]

**누적 아티팩트**

- `_workspace/release/`: 129개 파일. 대부분 EOD/SOD 보고서 및 릴리스 노트. 아카이브 정책 없이 단조 증가 중 [HIGH]
- `runs_local/`: 61개 디렉토리. `dual_final_01~03`, `siloa_verify1~7`, `dogfood_*`, `diffdock_poc` 등 실험 런이 기여자 삭제 없이 누적 [HIGH]
- `.worktrees/`: 31개 (로컬) + `/tmp/SST14-*`: 46개 = 77개 동시 존재 [HIGH]. 세션 종료 후 `/tmp` 파일은 자동 정리될 수 있으나 로컬 `.worktrees/`는 수동 정리 필요
- conda env: 17개 (base + 16). `pepadmet`, `pepadmet-upgrade`, `diffpepbuilder`, `genmol`, `openfold3`, `pybamm-inv`, `pybamm-inv-cu128` 등 비활성 환경 포함 가능 [HIGH]

**코드 격차 및 기술부채**

- `ensemble_router.py:61-76`: Layer 1/3 스텁. Layer 1 실구현 파일(`layer1_ensemble.py`)은 존재하나 `run_routed_halflife`에서 미호출 [HIGH]
- `pharmacology_guards.py` L954/L1130: `halflife_webmetabase_indirect`, `halflife_hle_regression_albumin` 동일 키 중복 정의 — 파이썬 dict 후행 우선 [HIGH]
- `pipeline_local/orchestrator.py` 2,479 LOC: God Function 수준. `pipeline_local/scoring/composite_scorer.py` 1,118 LOC + `pipeline_local/scripts/composite_scorer.py` 1,118 LOC 동명 파일 2개 공존 [HIGH]
- `AgenticAI4SCIENCE_pyrosetta_track/.../pyrosetta_flow/runner.py` 1,621 LOC (CLAUDE.md에 790줄로 언급되어 있으나 실제 1,621 LOC — 문서 갭) [HIGH]
- Pydantic v2 마이그레이션: `pipelines/silo_b/src/` 기준 `@validator` 패턴 50건 존재 [HIGH]. silo_b 실행 시 `PydanticDeprecatedSince20` 경고 발생 여부는 실제 import에서 미확인 (import OK, warning 미관측) [MED]
- BE endpoint 미구현: `/api/archives/top-k`, `/api/candidate/{candidate_id}/report` FE 호출 대비 BE 미존재 [HIGH]
- FE smoke test 1건 실패: accessible name `/more/i` 회귀 [HIGH]

---

### (B) 리팩토링 후보 구조 제안

**원칙**: 현재 `pipeline_local/`의 736 pytest가 통과하는 상태를 훼손하지 않는다. 3개월 이내 완료 가능한 범위만 제안한다.

**제안 방향: "통합 레이어만 정리, 두 트랙 유지"**

전체 monorepo 재구조화 대신, 현행 3중 분리 자체는 유지하되 명시적 경계를 확립한다.

```
SST14-M_scr/
├── src/                         # (신설) canonical 운영 소스
│   ├── pipeline_local/          # (이동) 현행 유지, 입력 경로만 정비
│   ├── pipelines/               # (이동) silo_a, silo_b, shared 패키지
│   └── integration/             # (신설) UnifiedCandidate 매핑 레이어
│       ├── __init__.py
│       └── adapter.py           # pipeline_local ↔ pipelines 스키마 변환
├── apps/
│   └── ai4sci-kaeri/            # (이동) AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
│       ├── backend/
│       ├── frontend/
│       ├── AG_src/
│       └── pyrosetta_flow/
├── data/                        # 현행 유지
├── docs/                        # 현행 유지
├── scripts/                     # 현행 유지
├── tools/                       # 현행 유지
├── _workspace/
│   ├── release/                 # 현행 — 정리 정책 적용
│   └── archived/                # (신설) 30일 이상 미참조 EOD/SOD 이관
├── runs_local/
│   ├── active/                  # 최근 14일 런 또는 final_candidates
│   └── archived/                # (신설) 14일 이전 실험 런
└── .worktrees/                  # 정리 정책: 30일 이상 비활성 삭제
```

**대안 구조가 부적절한 이유**:  
전체 monorepo(`packages/`, `apps/`) 표준 전환은 `AgenticAI4SCIENCE_pyrosetta_track` 경로를 사용하는 기존 conda env, CI 스크립트, pyproject.toml 의존을 동시에 갱신해야 하며, 3개월 이내 완료가 불확실하다.  
따라서 `src/` 통합은 **P2 수준 목표**로 남겨 두고, P0~P1은 명시적 경계 확립과 정리 정책 시행에 집중하는 것이 현실적이다.

---

### (C) 리팩토링 우선순위

**P0 (발표 직후 1주일 — 2026-05-29 ~ 2026-06-04)**

| 항목 | 비용 | 위험 | 이득 | 신뢰 |
|------|------|------|------|------|
| `pharmacology_guards.py` 중복 키 2개 제거 (L954~L1130) | 매우 낮음 (10분) | 낮음 (dict 후행 우선이므로 동작 동일) | 분석 정확도 확보 | HIGH |
| `ensemble_router.py` Layer 1/3 스텁 경고 메시지 명확화 (스텁임을 코드 주석에 명시) | 낮음 | 없음 | 오해 방지 | HIGH |
| `_workspace/release/` 30일 이상 미참조 파일 `archived/` 이관 정책 수립 + 1회 실행 | 낮음 | 없음 | 129개 → 추정 50개로 감소 | MED |
| `runs_local/` retention policy: `final_candidates/`와 최근 14일 런만 active 유지 | 낮음 | 낮음 (삭제 전 목록 확인 필요) | 61개 → 추정 15개 | MED |
| FE smoke test 1건 수정 (`more` button accessible name) | 낮음 | 없음 | CI 녹색 복원 | HIGH |
| BE `/api/archives/top-k` 미구현 — FE에서 graceful 404 처리 또는 BE stub 등록 | 낮음~중간 | 낮음 | 데모 안정성 | HIGH |

**P1 (1개월 — 2026-06-04 ~ 2026-07-01, 6월 회의 전후)**

| 항목 | 비용 | 위험 | 이득 | 신뢰 |
|------|------|------|------|------|
| `enrich_candidates_from_wrappers`에 3-Layer 연결 결정 (narrative-code 격차 해소) | 중간 (2~5일 작업) | 중간 (736 pytest PASS 유지 조건) | narrative 정합, 발표 신뢰도 | HIGH |
| PR #117 ADMET divergence guard main merge | 낮음 (PR 리뷰 + merge) | 낮음 | ADMET 불일치 경고 운영 적용 | HIGH |
| PR #11 (R1~R7 postmortem) 처리 — 머지 또는 명시적 폐기 결정 | 낮음 | 없음 | 16일째 방치 해소 | HIGH |
| `pipeline_local/orchestrator.py` 2,479 LOC → 함수 분리 시작 (1차 분리 목표: 1,200 LOC 이하) | 높음 (1~2주) | 중간 (회귀 테스트 필수) | 유지보수성 | HIGH |
| `pipeline_local/scripts/composite_scorer.py` vs `pipeline_local/scoring/composite_scorer.py` 동명 해소 | 낮음 | 낮음 | 혼란 제거 | HIGH |
| .worktrees/ 30일 이상 비활성 13개 이상 삭제 | 낮음 | 낮음 | 공간 및 인지 부하 감소 | MED |
| conda env 비활성 환경 감사 (17개 → 목표 10개 이하) | 낮음 | 낮음 | 환경 혼란 감소 | MED |
| BE `/api/candidate/{candidate_id}/report` 구현 또는 FE 제거 | 중간 | 낮음 | anchor 404 침묵 오류 제거 | HIGH |

**P2 (3개월 — 2026-07 ~ 2026-09)**

| 항목 | 비용 | 위험 | 이득 |
|------|------|------|------|
| `pyrosetta_flow/runner.py` 1,621 LOC 함수 분리 | 높음 | 중간 | 테스트 가능 구조 확보 |
| `AG_src/pipeline/orchestrator.py` 1,538 LOC 모듈화 | 높음 | 중간 | SRP 준수 |
| Pydantic v2 마이그레이션 (`pipelines/silo_b/` `@validator` 50건) | 중간 | 낮음 | 미래 Python/Pydantic 호환성 |
| `UnifiedCandidate` 스키마 - pipeline_local 산출물 스키마 정합 (`integration/adapter.py` 신설) | 중간 | 낮음 | 실제 Dual Silo 통합 가능 |
| Layer 2 반감기 모델 재설계 (D-AA 포함, wet-lab t½ 피드백 루프) | 매우 높음 | 높음 | A-02 핵심 미충족 항목 해소 |

**P3 (Nice-to-have, 시점 미정)**

- `src/` 통합 디렉토리 재구조화 전체 완료
- 단일 pytest suite로 silo_a + silo_b + pipeline_local + backend 통합 커버리지
- conda env 통합 (bio-tools 단일 env 목표)
- `_workspace/` 자동 아카이브 스크립트

---

## 4. 리팩토링 플랜 (P0~P1 상세)

### 사전 준비

```bash
# 1. 현재 736 PASS 기록
python3 -m pytest pipeline_local/tests/ --tb=no -q > /tmp/baseline_736.txt 2>&1

# 2. worktree 목록 스냅샷
git worktree list > /tmp/worktree_baseline.txt

# 3. _workspace/release 파일 목록 및 최종 수정일
ls -lt _workspace/release/ > /tmp/release_baseline.txt
```

### P0 단계별 커밋 전략 (1주일)

**Day 1-2: 데이터 정리 (코드 수정 없음)**  
1. `_workspace/release/`: 2026-04-30 이전 EOD/SOD → `_workspace/archived/` 이관  
2. `runs_local/`: `final_candidates/` + 최근 14일 런 외 → `runs_local/archived/` 이관  
3. PR #11 처리 결정 (머지 또는 Close with comment)  
4. 검증: `git status` + `git worktree list` 확인  

**Day 3: 코드 버그 수정 (소규모, 독립 PR)**  
1. `pharmacology_guards.py` 중복 키 2개 제거  
   - 커밋: `fix(guards): ENDPOINT_CONFIDENCE 중복 키 2개 제거 (halflife_webmetabase_indirect, halflife_hle_regression_albumin)`  
   - 검증: `python3 -m pytest pipeline_local/tests/ --tb=no -q` 736 PASS 확인  
2. `ensemble_router.py` Layer 1/3 스텁 주석 명확화  
   - 커밋: `docs(router): Layer 1/3 스텁 상태 주석 명시 — run_routed_halflife 미연결`  
   - 검증: import test  

**Day 4-5: FE/BE P0 잔여 처리**  
1. FE smoke test `more` button accessible name 수정  
   - 커밋: `fix(fe): smoke test accessible name 회귀 — more button aria-label 정합`  
   - 검증: `npm test` 119 PASS  
2. BE `/api/archives/top-k` — stub 등록 (503 반환)  
   - 커밋: `fix(be): /api/archives/top-k stub 등록 — FE 404 침묵 오류 제거`  
   - 검증: `python3 -m pytest pipeline_local/tests/ --tb=no -q` 736 PASS  

### P1 단계별 커밋 전략 (6월 회의 전)

**Phase 1-A: PR #117 main merge**  
- 선행: 현재 브랜치 내용 확인 + 736 PASS 상태 보존 확인  
- 커밋: `feat(scoring): ADMET divergence guard main merge — PR #117 (#117)`  
- 검증: 736 PASS + `composite_scorer.py` 통합 테스트  

**Phase 1-B: enrichment 경로 합의 + 연결**  
- 결정 필요: "enrichment가 3-Layer를 호출한다" vs "narrative를 코드에 맞게 조정한다"  
  - Option A (연결): `enrich_candidates_from_wrappers`에 `run_routed_halflife` 호출 추가  
    - 위험: Layer 2 R²=-0.028 출력이 실제 enrichment에 진입 → 분리 처리 로직 필요  
  - Option B (narrative 조정): 6월 발표에서 "모듈은 존재, enrichment 통합은 진행 중"으로 서술  
  - **권장**: 회의 전 Option B, 회의 후 Option A 실행. 양자 모두 코드와 narrative를 동기화해야 함  
- 커밋 (Option A 선택 시): `feat(scoring): enrich_candidates_from_wrappers — 3-Layer 라우터 연결 (Layer 2 D-AA 분기 포함)`  
- 검증: 736 PASS + `composite_scorer.py::test_enrich_*` 추가 필요  

**Phase 1-C: orchestrator.py 1차 분리**  
- `pipeline_local/orchestrator.py` 2,479 LOC → 핵심 함수 추출  
  - `_run_step_01_to_04()` 블록 분리  
  - `_run_silo_a()`, `_run_silo_b()` 별도 모듈로 이동  
- 목표 LOC: 1,200 이하 (단일 반복)  
- 커밋 단위: 기능 단위 3~5 PR 분리 (한 번에 1,000 LOC 이상 이동 금지)  
- 검증: 각 PR 후 `python3 -m pytest pipeline_local/tests/ --tb=no -q` 736 PASS  

### 5/28 회의 후 ~ 6월 회의 사이 안전한 작업 윈도우

```
5/28 회의 → [5/29-6/4] P0 실행
            → [6/5-6/11] P1-A (PR #117 merge)
            → [6/12-6/18] enrichment 경로 합의 결정
            → [6/19-6/25] enrichment 연결 또는 narrative 조정
            → [6월 회의 전 ~6/26] P1-B narrative-code 정합 확보
```

**회의 직전(5/28) 금지 작업**: orchestrator.py 대규모 리팩토링, conda env 삭제, worktree 대량 정리. 발표 안정성 최우선.

---

## 5. 리팩토링이 필요한가 — 종합 판단

필요하다. 근거:

1. **narrative-code 격차가 계속되면 의사결정 오류 리스크가 증가한다.** enrichment 경로가 3-Layer를 호출하지 않는 상태에서 "3-Layer가 pipeline을 보호한다"는 발표 서술은 사실과 다르다. 이 격차가 6월 회의 후까지 방치되면 합성 의뢰서 해석에 영향을 줄 수 있다.

2. **orchestrator.py 2,479 LOC와 runner.py 1,621 LOC는 현재 유지보수 병목이다.** 테스트 추가, 버그 재현, 변경 영향 분석이 모두 파일 전체 숙지를 요구한다.

3. **아티팩트 정리는 즉시 시행 가능하고 위험이 없다.** 129개 문서, 61개 실험 런, 77개 worktree를 아카이브 정책 없이 두면 신규 개발자 온보딩과 다음 세션 컨텍스트 로드 비용이 증가한다.

리팩토링이 불필요한 영역:
- `pipeline_local/scoring/` 모듈 (ensemble_router 83 LOC, layer1/2 각 ~150 LOC): 현재 크기와 책임 범위가 적절하다.
- `pharmacology_guards.py` 1,247 LOC: 레지스트리 파일 특성상 길이가 불가피하다. 중복 키 2개만 제거하면 충분하다.
- `pipelines/silo_b/src/scoring.py` 92 LOC: 현행 유지.

---

## 마지막 stdout 5줄

1. **충족 매트릭스 종합**: 원래 8건 기준 충족 6 / 부분 2 / 미달 0 / 삭제 1. 후속 포함 16건 기준 충족 7 / 부분 4 / 미달 5 (PR #117 미머지, PR #112 미머지, PR #11 방치, FE test 실패, BE 미구현 endpoint 2건).

2. **가장 결정적 리팩토링 필요 항목**: `enrich_candidates_from_wrappers`의 3-Layer 미연결 — `pipeline_local/scripts/composite_scorer.py:400-408` D-AA skip 로직과 `pipeline_local/scoring/ensemble_router.py:61-76` Layer 1/3 스텁이 함께 방치되면 narrative §5.4의 격차가 6월 회의 발표에서도 재현된다. 코드 수정 없이 narrative를 조정하거나, narrative를 코드와 정합하거나 — 둘 중 하나가 6월 전에 결정되어야 한다.

3. **가장 시급한 코드 격차**: PR #117 ADMET divergence guard (`e3a5413`) main 미포함. 커밋은 존재하고 테스트도 통과하는 상태이므로 PR 리뷰 + merge만 하면 되는 최저 비용 개선이다. main 머지 가능 시점: 5/29 (P0 완료 직후, 736 PASS 유지 조건).

4. **리팩토링 전체 일정**: P0 1주 + P1 4주 + P2 8주 + P3 시점 미정 = P0~P2 합산 약 13주 (6월 중순~8월 말). P0만으로도 가장 가시적인 효과(CI 녹색, 중복 키 제거, 문서 정리)를 얻을 수 있다.

5. **narrative v3 또는 PPTX 반영 위치**: narrative v3 §5.4 "코드 실태와 narrative의 격차" 표에 "enrichment-3Layer 연결 여부" 행 추가, PPTX D-6 슬라이드 21번(Schrödinger 검토 의제) 직전에 "6월 회의 전 코드 정합 작업 계획" 1슬라이드 삽입 권장.
