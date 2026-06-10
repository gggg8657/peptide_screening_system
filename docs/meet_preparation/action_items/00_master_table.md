# P0 — Action Items 종합 비교표
**원본**: KAERI-AIRL-MOM-2026-003 (2026-04-06 제3차 월간회의)
**작성**: 2026-06-01 (다음 회의 D-?일)
**상태**: 초안 보고 / 현재 상태 공유

---

## 1. 한눈 보기

| No | 원본 요구 (간략) | 관련 영역/Silo | 대응 방법 (요약) | 기능적 달성도 | 현재 문제점 | 향후 방향 | 상태 |
|----|------------------|----------------|------------------|--------------|------------|----------|------|
| **A-01** | SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 | Docking / Silo B | SSTR2 7XNA→ 4종 cealign + binding pocket JSON + Boltz/FlexPepDock 재도킹 | ● 완료 | 회의록의 7T10 vs 로컬 7XNA 구조 ID 불일치 (선택성 수치 해석 영향) | 7T10 공식 PDB로 재검증 + 선택성 배수 확정 | ✅ PR #61 머지 |
| **A-02** | 혈청 반감기 예측 도구 비교 조사 (벤치마크) | AI Modules / Silo B (step08) | wrapper 통합(`predict_halflife_pepmsnd.py`), N-end rule 1차, PlifePred Layer 1, pepMSND Layer 2 | ◑ 부분 | **D-AA HIGH-BLOCKER** — D-Phe/Thr(ol) 함유 펩타이드 예측 도구 미존재, PEPlife2-GAT R²=0.022 (seed 의존) | MD(RMSD) 2차 스크리닝, 실험적 Serum Stability 병행 (서호성 의견) | 🟡 wrapper 완료, 정확도 미확보 |
| **A-03** | Fab-ADMET 정확도 검증 + 자체 학습 가능성 평가 | AI Modules / Silo B (step08) | `predict_admet_ai_wrapper.py` 통합, ADMET-AI 로컬 마이그레이션, pepADMET 재훈련 | ◑ 부분 | **HTTP 403 차단** (외부 API 접근 차단), Fab-ADMET=pepADMET 식별 확인 (2026-05-20), Layer 3 (DOTA proxy) STUB | pepADMET 자체 학습 (GPU 사양 산정), `[추정]` ADMET-AI fine-tuning | 🟡 wrapper 완료, 검증 차단 |
| **A-04** | Top-K 후보 선정 복합 스코어링 체계 설계 (ΔG+반감기+셀렉티비티+ADMET) | AI/Scoring / Silo B | `composite_scorer.py` + Tier S/A/B/FAIL + ensemble_router(L1/L2/L3) + Critic Agent 자동 검증 | ◕ 대부분 | **enrichment 경로가 3-Layer 미호출** (PR #117 미머지), Layer 3 STUB, K-1/K-2 selectivity 결함이 입력 신뢰성 위협 | PR #117 머지 / enrichment 정합 / Pareto front 추가 검토 | ✅ PR #62 머지 |
| **A-05** | SST14 레퍼런스 ΔG 기준선 확립 + 가변 임계값 (n회 Mean) | Docking / Silo B | SST14 wildtype을 SSTR2(7T10)에 동일 프로토콜 도킹 → ΔG 실측 + 0.9 배율 임계값 | ● 완료 | **MD/MM-GBSA/FEP/TI 정밀 ΔG는 부재** — 서호성 의견의 6단계 정밀 계산 미구현 | gmx_MMPBSA·OpenMM·OpenFE 도입 검토 (§7-0 §5 검증) | ✅ main 직접 push |
| **A-06** | 디퓨전 모델 기반 도킹 가속화 PoC (정확도 vs Rosetta 비교) | Docking / Silo B | DiffDock 또는 유사 디퓨전 모델 + SSTR2-SST14(7T10) ground truth RMSD 비교 | ◔ 초기 | **PoC 미완** — 스크립트는 존재(`step05_docking.py`의 DiffPepBuilder는 비활성), 벤치마크 미수행 | DiffDock 본격 실행 + RMSD 2.0Å 80% 기준 평가 + GPU 부족 시 A-07 연동 | 🟡 스크립트 존재, 완성도 미확인 |
| **A-07** | DGX/고성능 GPU 서버 구매 사양 + 비용 견적 수집 (DGX H100/B200) | Infra | 매트릭스 작성 (VRAM·NVLink·전력·납기·유지보수·라이선스) + 벤더 견적 요청 | ◑ 부분 | **외부 견적 대기** — 벤더 2곳 이상 견적서 미수령 | 견적 도착 후 비교표 완성 → 6월 회의 의사결정 | 🟡 매트릭스 작성, 외부 견적 대기 |
| ~~A-08~~ | ~~라이브러리 서버 마이그레이션~~ | — | — | — | — | — | ❌ 삭제 (H100×8 서버 배포 완료, PDF §2.3) |
| **A-09** | 최종 후보 3-4개 도출 + 합성 의뢰 준비 (파이프라인 1차 완전 실행) | All / Dual-silo | A-04 복합 스코어링 적용 → PRST-001~004 도출, 합성 의뢰서 작성 (서열·수식위치·순도·납기·DOTA 킬레이터) | ● 완료 | **wet-lab 미시작** — ADMET=1.00은 OOD 외삽 위험 (서호성 의견대로 in-vitro 병행 필수) | 합성 ETA 확정 + binding affinity assay 설계 + RI 표지 protocol | ✅ PR #63 머지 (PRST-001~004) |
| **A-10** | SSTR3 도킹 에러 원인 분석 및 해결 (A-01 선행) | Docking / Silo B | SSTR3 PDB 전처리 (누락 잔기·충돌·B-factor) + Modeller/SWISS-MODEL 누락 루프 재구축 + 에너지 최소화 | ● 완료 | 별건 **SSTR4 시그니처 VILRYAKMKTA가 SSTR1과 중복 등록**이었던 회귀는 별도 해결됨 | (관련 회귀 테스트 유지) | ✅ PR #60 머지 (fix `5f5f7af`) |

> **Status legend**: ● 완료 / ◕ 대부분 / ◑ 부분 / ◔ 초기 / ○ 미착수 / ? 확인 필요
> **상태 legend**: ✅ PR 머지·완료 / 🟡 진행 중 (블로커 있음) / 🔴 미달

---

## 2. 우선순위 분포 (5/27 audit + 본 점검 신규 발견)

| 우선순위 | 건수 | 항목 |
|---------|------|------|
| **P0 (즉시/D-7)** | 4 | A-02 D-AA 블로커, A-03 HTTP 403 + Layer 3 STUB, A-04 enrichment 정합 / PR #117, A-09 wet-lab 시작 |
| **P1 (4주, audit 권고)** | 3 | A-06 디퓨전 PoC 완료, A-07 견적 도착, A-05 정밀 ΔG (MM-GBSA/FEP) 검토 |
| **P2 (확인 후 결정)** | 2 | A-01 구조 ID 불일치 재검증, A-10 회귀 테스트 유지 |

---

## 3. 도메인별 매핑 (각 Action Item × 시스템 영역)

| Action Item | Backend | Frontend | AI/LLM | MCP/Tools | vLLM | Docking | Silo A | Silo B | Dual |
|------------|---------|----------|--------|-----------|------|---------|--------|--------|------|
| A-01 |   |   |   |   |   | ✓✓✓ |   | ✓✓ | ✓ |
| A-02 |   |   | ✓ | ✓ |   |   |   | ✓✓✓ |   |
| A-03 | ✓ |   | ✓ | ✓ |   |   |   | ✓✓✓ |   |
| A-04 | ✓ | ✓ | ✓✓ |   |   |   | ✓ | ✓✓✓ | ✓ |
| A-05 |   |   |   |   |   | ✓✓✓ |   | ✓✓ |   |
| A-06 |   |   | ✓ |   | ✓ | ✓✓✓ | ✓ | ✓✓ |   |
| A-07 |   |   |   |   |   |   |   |   |   (인프라) |
| A-09 | ✓ | ✓ |   |   |   | ✓ |   | ✓ | ✓✓✓ |
| A-10 |   |   |   |   |   | ✓✓✓ |   | ✓✓ |   |

> ✓ 관련, ✓✓ 직접 영향, ✓✓✓ 주축

---

## 4. 시스템 점검 연결성 (본 보고서 §주요 발견 ↔ Action Items 매핑)

| 본 점검 P0 발견 | 영향 받는 Action Item |
|----------------|---------------------|
| K-1/K-2 selectivity 결함 (모든 후보 동일 off-target) | **A-04 입력 신뢰성 위협**, A-09 후보 ranking 재검증 필요 |
| Silo A 실 실행 0건 (NIM 키 부재) + 이중 구현 | (A-04 Tier 시스템은 Silo B에서 완성됨, Silo A 통합 6월 결정) |
| Dual `--dual` 기본 False, 종단 검증 0건 | A-04·A-09 통합 검증 추후 |
| Silo C 코드 가정 vs 구현 격차 | (해당 Action Item 없음 — 본 점검 신규 발견) |
| Step05 Boltz 25분 SLA 미완 | **A-06 디퓨전 가속화 PoC 동기 강화** (Rosetta 대비 10배 기대) |
| Layer 3 (DOTA ADMET-AI MD proxy) STUB | **A-03 Layer 3 부분**, A-04 종합 스코어링 공백 |
| PR #117 미머지 | **A-02·A-04 enrichment 경로 정합 블로커** |
| MCP filesystem 경로 오류 | (운영 환경 P3, Action Item 외) |

---

## 5. 4/6 회의 핵심 결정 사항 (Action Items 외 보조)

| 결정 | 내용 | 현재 반영 상태 |
|------|------|---------------|
| **7단계 다단계 선별 체계** (서호성 제안) | Specificity → Serum Stability → Toxicity → Lead 확정 → AA Modification → RI-MD simulation → 기타 예측 | 🟡 단계 1~3은 파이프라인 반영, 단계 4(Lead 확정)는 A-04로 부분 완료, 단계 5~7은 미구현 |
| ⊿G 단일 의존 탈피 | 반감기·셀렉티비티·ADMET 종합 (Top-K 기준 체계화) | ✅ A-04로 반영 (단, 미달 항목 존재) |
| **SSTR2 결합 영역** | 77-314 한정, ECL/TM 핵심 잔기 표 활용 (네거티브 디자인 정량 근거) | 🟡 A-01로 부분 반영, ECL/TM 표는 코드에 미통합 |
| **Radiolysis Quencher 전략** | Gentisic + Ascorbic + Methionine + Cysteine + Ethanol 조합 (서호성 제안) | ❌ 미반영 (`pipeline_local/scoring/radiolysis_scorer.py`는 존재하나 Quencher DOE 미구현) |
| **AA Modification 전략** | Met→Nle, Trp→5-F-Trp, Cys-Cys→Thioether bridge 등 | 🟡 modification_conflict checker는 구현, 실제 modification 적용 여부 미확인 |

---

## 6. 추적성 (Action Item ↔ PR ↔ 파일)

| Action Item | 머지 PR | 핵심 파일 |
|------------|---------|-----------|
| A-01 | #61 (10 files, +43K) | `pipeline_local/scripts/binding_pocket/`, `data/somatostatin_receptor/binding_pocket_*.json` |
| A-02 | (wrapper) | `pipeline_local/scripts/predict_halflife_pepmsnd.py`, `pipeline_local/scoring/layer1_ensemble.py` |
| A-03 | (wrapper, 차단) | `pipeline_local/scripts/predict_admet_ai_wrapper.py`, `pipeline_local/scripts/predict_admet_pepadmet.py` |
| A-04 | #62 (Tier 시스템) | `pipeline_local/scoring/composite_scorer.py`, `ensemble_router.py` |
| A-05 | main `8e7e1cc` | `pipeline_local/config/gate_thresholds.yaml` (가변 임계) |
| A-06 | — | `pipeline_local/scripts/run_diffpepbuilder.py` (보류) |
| A-07 | — | (외부 견적 — 미머지) |
| A-09 | #63 | `runs_local/dual_final_03/local_20260402_1055_iter01/` (PRST-001~004) |
| A-10 | #60 (fix `5f5f7af`) | `pipeline_local/scripts/structure_io.py`, SSTR3 PDB 전처리 |

---

## 7. 6월 회의 의사결정 요청 (예상)

1. **A-02 D-AA 블로커 해소 방향** — MD(RMSD) 2차 스크리닝을 채택할지, 외부 도구 추가 도입할지
2. **A-03 Fab-ADMET = pepADMET 자체 학습 진행 여부** — GPU 부담 vs 정확도 이점
3. **A-04 PR #117 머지** — Layer 2 R²=0.022 재학습 합의 시 즉시 가능
4. **A-06 디퓨전 PoC 결과 평가 + A-07 GPU 견적 도착 시 구매 의사결정**
5. **본 점검 신규 발견 — Silo C 정책 결정** (구현 vs aggregator 가중치 재설계 A:0.5/B:0.5)
6. **Schrödinger 도입 검토 결과** — 라이센스·비용 정량화 후 (audit §5 권고)

---

*상세는 각 Action Item 파일 `A-XX_*.md` 의 5블록 분석을 참조.*
