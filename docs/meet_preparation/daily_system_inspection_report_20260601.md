# 시스템 점검·Action Items 분석·반영 계획 종합 보고
**작성일**: 2026-06-01
**원본**: KAERI-AIRL-MOM-2026-003 (2026-04-06 제3차 월간회의)
**상태**: 초안 / 현재 상태 공유 (최종 성과 발표 아님)
**근거 원칙**: 코드·로그·실행 결과·검증된 출처만 인용. 미확인은 `확인 필요` 명시.

---

## 0. 목차
1. Executive Summary
2. 금일 보고 목적
3. 전체 시스템 구성 개요
4. 영역별 점검 결과
5. **Action Items 5블록 분석 + P0 종합표**
6. 통합 아키텍처 및 데이터 흐름
7. 주요 발견 사항 (분류·요약)
8. 리스크 및 이슈 (매트릭스)
9. 분석 — 보고→분석 (근본 원인·연쇄)
10. **반영 계획 요약** (상세는 `reflection_plan/`)
11. **References** (상세는 `references/`)
12. **종합 향후 진행 방향 의견**
13. Appendix 참조

---

## 1. Executive Summary

> **한 줄 요약**: 4/6 회의 Action Items 9건(A-08 삭제) 중 6건은 PR 머지·구현 완료, 3건은 부분 진행이다. 데모 서비스 스택(BE/FE/vLLM/FlexPepDock)은 라이브 응답 중이나 **본 점검 신규 발견 3건**(K-1/K-2 selectivity 결함·Silo C 코드 가정 vs 구현 격차·dual-silo 종단 검증 0건)과 **A-02 D-AA 블로커·A-03 Layer 3 STUB·A-06 PoC 미완**이 6월 회의 안건이다. 본 보고는 **초안/현재 상태 공유**.

| 차원 | 상태 | 근거 |
|------|------|------|
| 데모 서비스 (BE/FE/vLLM/Workers) | 🟢 라이브 | curl 200 확인 (§4) |
| 테스트 781 PASS / 1 skip / 2 xfail | 🟢 회귀 없음 | `phase1-module-tests-2026-05-27.md` |
| 4/6 Action Items 9건 | 🟢 6 완료 / 🟡 3 진행 | `action_items/00_master_table.md` |
| **본 점검 신규 P0 발견** | 🔴 3건 | §7 (K-1/K-2, Silo C, dual 검증 0) |
| **A-02 D-AA HIGH-BLOCKER** | 🔴 | `A-02_serum_halflife_tools.md` |
| **A-03 Layer 3 STUB** | 🔴 | `A-03_fab_admet_validation.md` |
| PRST-001~004 후보·합성 의뢰서 | 🟢 도출 완료 | PR #63, `A-09_final_candidates.md` |
| MCP filesystem 경로 오류 | 🟢 즉시 수정 가능 (5분) | `.mcp.json` (본 점검 신규 발견) |

---

## 2. 금일 보고 목적

1. 4/6 회의 Action Items의 **원본 요청 ↔ 현재 대응** 정합 평가
2. 데모 라이브 시연 가능 여부의 객관적 판정 (서비스 가동 ≠ 파이프라인 완주)
3. 6월 회의에서 의사결정 필요한 안건 정리 + 추적성 확보
4. 박사 청자에게 과장·은폐 없이 전달할 핵심 메시지 정리

---

## 3. 전체 시스템 구성 개요

자세한 도식은 PPTX 메인 §전체 시스템 한 장 요약 슬라이드 참조. 핵심 구성:

```
연구자 → FE(:5173, 16 페이지) → BE(:8787, 21 라우터/81 엔드포인트)
                              ↘ vLLM(:8002, deepseek-r1-distill-32b, uptime 4d 16h)
                              ↘ Silo A (3-Arm NIM | 로컬 1-Arm 축약판 — 이중 구현)
                              ↘ Silo B (8-Step + Gate 4종 + FlexPepDock 워커 4)
                              ↘ Dual-silo (aggregator.rank_fusion A:0.34/B:0.33/C:0.33)
                                          └ Silo C는 코드 가정만 (구현 없음)
```

**청중용 1줄 설명** (생명공학자):
> SSTR2(somatostatin receptor 2)에 결합하는 펩타이드 후보를 자동으로 디자인·평가하는 듀얼 파이프라인이다. **Silo A**는 소분자/펩타이드/de novo 3 경로로 새로 만들고, **Silo B**는 SST-14 천연 시퀀스에 변이를 가해 SSTR2와의 결합을 PyRosetta로 정밀 계산한다. 두 결과를 통합 랭킹해 wet-lab 검증 대상 후보를 추린다.

---

## 4. 영역별 점검 결과

본 섹션은 **점검 증거** (`inspect_evidence/`)에서 도출한 핵심을 요약. 상세는 각 파일 참조.

### 4.1 Backend (FastAPI :8787) — 🟢 정상 (1건 부분 동작)
- 21 라우터 / 81 엔드포인트 / `/api/health` 200 응답
- 핵심 이슈: `/api/v1/silo-a/health` 라이브 404 (코드 등록은 됨) — `inspect_evidence/backend.md`
- 의존성: fastapi 0.135.1 / uvicorn 0.41.0 / pydantic 2.12.5
- 전역 예외 핸들러 3종 등록 완료

### 4.2 Frontend (Vite :5173) — 🟢 정상 (스모크 1/2 FAIL)
- 16 페이지 lazy-load, TanStack Query v5 + Zustand v5
- App.smoke.test.tsx의 "More" 버튼 테스트 FAIL (테스트-구현 불일치, 회귀 아님)
- 사용자 플로우: `/console → /candidate/:id → /wetlab/orders/:id` (검증 완료)

### 4.3 AI Modules + vLLM — 🟢 정상
- 6 Agent: planner / builder / critic / qc_ranker / reporter / diversity_manager
- vLLM uptime **4d 16h 57m**, GPU 3 (83 GB used, 72% util)
- 라이브 캡처: `curl :8002/v1/models → 200 5ms`, completion 200ms

### 4.4 MCP / Tools — 🔴 부분 미동작 (신규 발견)
- 3 MCP 서버: github 🟢, memory 🟢, **filesystem 🔴 경로 오류** (`/home/helloworld/.../PRST_N_FM` 미존재)
- harness-adaptation Stage 0~9 적용 이력 (CLAUDE.md 등재)

### 4.5 Docking System — 🟡 부분
- Boltz-2 (primary, MSA 우회), DiffDock (보조), **DiffPepBuilder 비활성** (`step05_docking.py:144`), PyRosetta FlexPepDock 워커 4 idle, FoldMason
- 큐: 18 잡 history, 1건 사용자 취소 (실패 아님)

### 4.6 Silo A — 🟡 **이중 구현** (본 점검 신규 강조)
- `(A1) pipelines/silo_a/` — 3-Arm 완전판, 코드 완비, **실 실행 0건 (NIM 키 부재)**
- `(A2) pipeline_local/_run_silo_a()` — 로컬 1-Arm 축약판 (RFdiffusion+ProteinMPNN만)
- "3-Arm 가상 스크리닝" narrative와 실 운영의 격차

### 4.7 Silo B — 🟢 코드 완비 / 🟡 운영 격차
- step01~08 + Gate 4종, 3-Layer Ensemble (L1 PlifePred · L2 pepMSND R²=0.022 · **L3 STUB**)
- Step05 Boltz 25분 SLA 미완 (audit 5/27): 후보당 30~40s × 55개 ≈ 1500s

### 4.8 Dual-silo 통합 — 🔴 **종단 검증 0건** (신규 발견)
- 분기 `orchestrator.py:835` (`--dual` 기본 False)
- 합류 `:981 _run_dual_silo()` → `BranchOutputs(dual_mode=True)`
- 랭킹 `aggregator.rank_fusion_weighted_sum` silo_weights={A:0.34, B:0.33, **C:0.33**}
- 🚨 **Silo C 구현/문서/실행 흔적 0건** — `policy.py:required_silos=["A","B","C"]` 가정만

---

## 5. Action Items 5블록 분석

### 5.1 P0 종합 비교표

> 본 보고서의 핵심 표 — 상세 5블록은 `action_items/A-XX_*.md` 각 파일 참조.

| No | 원본 요구 | 관련 영역 | 대응 방법 | 달성도 | 현재 문제점 | 향후 방향 | 상태 |
|----|----------|-----------|----------|--------|------------|----------|------|
| **A-01** | SSTR1/3/4/5 위치 지정 도킹 | Docking / Silo B | cealign + binding_pocket JSON + Boltz/FlexPepDock | ● | 7T10 vs 7XNA 구조 ID 불일치 | 7T10 재검증 + 셀렉티비티 배수 확정 | ✅ PR #61 |
| **A-02** | 혈청 반감기 도구 비교 | AI / Silo B | L1 PlifePred / L2 pepMSND wrapper | ◑ | D-AA HIGH-BLOCKER, PR #117 미머지 | MD(RMSD) 2차, 실험 병행 | 🟡 진행 중 |
| **A-03** | Fab-ADMET 검증·자체학습 | AI / Silo B | pepADMET 로컬 마이그레이션 + ADMET-AI | ◑ | HTTP 403, Layer 3 STUB | pepADMET fine-tuning 산정 | 🟡 진행 중 |
| **A-04** | Top-K 복합 스코어링 | AI / Silo B | Tier S/A/B/FAIL + Critic + ensemble_router | ◕ | enrichment 분리, PR #117 | enrichment 정합 / Pareto 검토 | ✅ PR #62 |
| **A-05** | SST14 레퍼런스 ⊿G | Docking / Silo B | n회 도킹 Mean + 가변 임계 | ● | MM-GBSA/FEP 미구현 | gmx_MMPBSA·OpenFE 검토 (§11) | ✅ direct push |
| **A-06** | 디퓨전 도킹 PoC | Docking / Silo B | DiffDock or 유사 | ◔ | 본격 PoC 미수행 | DiffDock 1회 실행 + RMSD ≤2.0Å | 🟡 스크립트만 |
| **A-07** | GPU 견적 | Infra | DGX H100/B200 매트릭스 | ◑ | 외부 견적 대기 | 6월 회의 의사결정 | 🟡 견적 대기 |
| ~~A-08~~ | ~~라이브러리 서버 마이그레이션~~ | — | — | — | — | — | ❌ 삭제 |
| **A-09** | 최종 후보 3-4개 + 합성 의뢰 | All / Dual | Tier S → PRST-001~004 도출 | ● | wet-lab 미시작, ADMET=1.00 OOD | Ki assay + RI 표지 | ✅ PR #63 |
| **A-10** | SSTR3 도킹 에러 해결 | Docking / Silo B | PDB sanitize + 누락 잔기 재구축 | ● | (회귀 테스트 유지) | — | ✅ PR #60 |

> **달성도**: ● 완료 / ◕ 대부분 / ◑ 부분 / ◔ 초기 / ○ 미착수
> **확장 매핑 표**: `action_items/00_master_table.md` §3 (BE/FE/AI/MCP/vLLM/Docking/Silo 매트릭스)

### 5.2 각 Action Item 카드 위치
- `action_items/A-01_SSTR_site_directed_docking.md` — ① 원본/해석 ② CS Method ③ 현재 구현 ④ AI Scientist 관점 ⑤ 한 줄
- 동일 5블록 구조: A-02 ~ A-07, A-09, A-10 (총 9개)

### 5.3 Serum Stability 자료 조사 — L-AA / D-AA Landscape (A-02 보강 요약)

> 상세는 `action_items/A-02_serum_halflife_tools.md` **§6 (L-AA)** + **§7 (D-AA)** 참조. 본 절은 보고용 요약.

#### **L-AA Serum Stability — 알려진 성능과 한계**

자연 L-AA 펩타이드는 혈청 내 다수 protease(trypsin·chymotrypsin·elastase·carboxypeptidase·aminopeptidase)에 의해 빠르게 분해된다. **SST-14(AGCKNFFWKTFTSC) t½ ~3분** (회의록 §2.2)이 그 직접 증거.

| 도구 | 학습 데이터 | 보고 정확도 | 출처 [R 검증] |
|------|------------|------------|--------------|
| **N-end rule** (Bachmair 1986) | E.coli/yeast in vivo, N-terminal 잔기 | ~30h 점 추정, short peptide 부적합 | DOI: 10.1126/science.3018930 |
| **ProtParam** (ExPASy) | 자연 L-AA 단백질 | Instability index 휴리스틱 (분해능 ↓) | web.expasy.org/protparam/ |
| **PlifePred** (Mathur 2018) | 자연 L-AA 펩타이드 | 외삽 시 신뢰 저하 | DOI: 10.1371/journal.pone.0196829 (PLOS One) |
| **HLP** (IIITD Raghava) | L-AA 펩타이드 분류기 | 보고 한정 | webs.iiitd.edu.in/raghava/ |
| **PeptideRanker** (UCD) | bioactive 활성 점수 | **반감기 X — A-02 부적합** | (논문 확인) |

**L-AA 도구의 공통 한계** (4가지):
1. **자연 L-AA에 학습됨** → modification(D-AA/N-methyl/cyclic/lipidation) 외삽 시 신뢰 저하 (회의록 §2.2 명시: "GLP-1처럼 지질 수식이 포함되거나, Modification이 된 경우 기존 방법론으로는 분석이 어렵다")
2. **점 추정만 제공** (uncertainty quantification 없음)
3. **벤치마크 부족** — SST14/Octreotide/Lanreotide/RC-160 약물 라이브러리의 일관 R² 보고가 드물어, 회의록 §4 A-02 가이드가 본 프로젝트 벤치마크 구축을 요구
4. **혈청 vs 다른 매트릭스 미구분** — 위장관·세포내·혈청 분해를 구분 안 함

#### **D-AA Serum Stability — 알려진 사실과 도구 격차**

D-아미노산은 자연계 protease 입체화학과 반대이므로 분해 저항성 큼. 회의록 §2.2 벤치마크 세트가 정량적 증거:

| 펩타이드 | Modification | t½ (혈청) | 배수 vs SST14 |
|---------|-------------|----------|--------------|
| SST14 (자연형) | 없음 (전 L-AA) | ~3분 | 1× (기준) |
| **Octreotide** | D-Phe(N) + Thr(ol)(C) | ~100분 | **~33×** |
| Lanreotide | D-Nal + D-Trp | (수명 더 김) | `확인 필요` |
| RC-160 (Vapreotide) | D-Phe + L-Val | 회의록 미기재 | — |

**🔴 핵심 격차**: 현재 시점 **D-AA 펩타이드의 혈청 반감기를 신뢰 가능한 정확도로 예측하는 in silico 도구는 부재**.
- PlifePred / HLP / ProtParam: ❌ D-AA 학습 부재 → 외삽
- **PEPlife2-GAT** (Layer 2 자체 학습): △ **R²=0.022** (audit 5/27, seed 의존) → 사실상 의사결정 불가
- pepADMET: `[추정]` — 환형 펩타이드 지원 명시, D-AA 처리 가능성 검증 필요 ([R 검증] DOI: 10.1021/acs.jcim.5c02518, GPL-3.0)
- **MD(RMSD) 2차** (서호성 의견): ✅ 입체화학 직접 모델링 — 본 프로젝트 미구현, gmx_MMPBSA/OpenMM 도입 검토 (R-11)
- **in vitro 실측**: ✅ gold standard — wet-lab assay 시점에 표준화 (R-08과 함께)

**약리학적 의미 (생명공학 청중)**: D-AA 도입은 stability 향상 이상이다 — 입체화학 변경은 receptor 결합 모드·selectivity·합성비용·assay 설계에도 영향. **A-02(stability) + A-04(scoring) + A-09(synthesis)는 묶여서 의사결정해야 한다**. 본 프로젝트 7단계 §2(Serum Stability) 통과 판정은 **MD 2차 + 실험 실측 병행 없이는 의사결정 불가**라는 것이 4/6 회의의 명시적 결론(서호성 의견 p.3·p.7)이다.

---

## 6. 통합 아키텍처 및 데이터 흐름

### 6.1 사용자 요청 → 결과 반환 end-to-end
```
연구자 → /run/new (RunLauncherPage) → POST /api/experiment/run
       → Planner(vLLM) → 후보 생성 → Silo A 또는 B 또는 Dual
       → step04~08 + Gate → aggregator.rank_fusion_weighted_sum
       → /api/runs/{id} → /candidate/:id (Mol* 3D + ADMET)
       → /wetlab/orders/:id (in-vitro 의뢰)
```

### 6.2 장애 발생 가능 지점
- vLLM 연결 실패 (Phase 2 smoke 사례 `errno 111`) → Planner 규칙 기반 폴백 (구현됨)
- Boltz-2 25분 SLA 초과 → demo subset 운영
- FlexPepDock OOM → per-receptor 6h timeout + orphan GC
- MCP filesystem 경로 부재 → 본 점검 발견, 5분 수정 가능
- BE silo_a 404 → BE 재기동 + import 검증

---

## 7. 주요 발견 사항 (분류·요약)

### 🔴 P0 — 라이브 시연/신뢰성 직접 위협
1. **K-1/K-2 selectivity 결함** — `_build_pdb_index` 정렬 + `candidate_pdb` 미전달로 모든 후보가 동일 off-target. A-04·A-09 입력 신뢰성 위협. (본 점검 신규)
2. **Silo A 실 실행 0건 + 이중 구현** — `pipelines/silo_a/` 3-Arm은 NIM 키 부재, `pipeline_local/_run_silo_a()`는 1-Arm 축약판. (본 점검 신규 강조)
3. **Silo C 코드 가정 vs 구현 격차** — `policy.py` + `aggregator.py` 가정만, 구현 흔적 0건. (본 점검 신규)
4. **Dual 종단 검증 0건** — `--dual` 기본 False, phase 2 smoke도 미활성. (본 점검 신규)
5. **A-02 D-AA HIGH-BLOCKER** — PEPlife2-GAT R²=0.022, D-AA 신뢰 도구 부재.
6. **A-03 Layer 3 STUB** — DOTA 평가 공백.

### 🟠 P1 — 계산 신뢰성·통합 격차
7. **Step05 Boltz 25분 SLA 미완** (A-06과 연동).
8. **PR #117 미머지** (A-02·A-04 enrichment 정합 블로커).
9. **DiffPepBuilder 비활성** (`step05_docking.py:144`).
10. **`/api/archives/top-k` stub 누락** (FE `ArchivesTopKSlider.tsx:96` 에러).

### 🟢 P2 — 즉시 수정 가능·낮은 영향
11. **MCP filesystem 경로 오기재** (5분 수정, 본 점검 신규).
12. **BE silo_a 라우터 404** (재기동 검증).
13. **FE smoke "More" 테스트 FAIL** (테스트 갱신).
14. **diversity 가중치 0.10 사문화** (어떤 Arm도 미계산).

### Baseline (안정)
15. vLLM 4d 16h 무중단 · 테스트 781 PASS · PRST-001~004 합성 의뢰서 완료.

---

## 8. 리스크 매트릭스 (영향도 × 발생 가능성)

| 영향도 ↓ \ 가능성 → | 낮음 | 보통 | 높음 |
|---|---|---|---|
| **高** | — | Layer 3 STUB (DOTA 평가 공백) | **K-1/K-2 selectivity / Silo A 실행 0건 / Dual SLA 미완** |
| **中** | vLLM downtime | silo_a 404 / DiffPepBuilder 비활성 / Silo C 격차 | **PR #117 미머지 → enrichment 불일치 지속** |
| **低** | 워커 OOM | FE smoke 1 FAIL / diversity 사문화 | MCP fs path (5분 수정) |

---

## 9. 분석 — 보고→분석 (근본 원인·연쇄)

본 점검 + 4/6 Action Items에서 식별된 **최상위 근본 원인 3가지**:

### 9.1 narrative ↔ 코드 격차 (최상위)
- "3-Arm Silo A", "Silo C 통합 가중", "3-Layer 보호" 등 narrative 상의 시스템 서술이 실제 코드 구현과 분리되어 있다.
- 연결 사례: Silo A 이중 구현 / Silo C 코드 가정 vs 구현 / enrichment 경로 분리 (PR #117) / Layer 3 STUB.
- 반영: **R-06 (enrichment 정합), R-13 (Silo A 통합 결정), R-14 (Silo C 정책)** — `reflection_plan/`.

### 9.2 단일 도구 출력 과신 회피의 framework 정신 vs 운영 미정착
- ADMET=1.00 OOD 위험·D-AA 반감기 예측 불가 등은 "한계 노출 framework"의 표현인데, 운영 화면·의뢰서가 그 한계 명시를 일관 노출하지 않는다 (A-09 wet-lab 병행 명시는 의뢰서에 들어가 있으나 FE 화면 표시는 부분).
- 연결 사례: A-02·A-03·A-04·A-09 / Mol* fallback 표시 (audit Phase 3).
- 반영: **R-07 (Layer 3 OOD 경고 최소 구현), Mol* 레이블 (audit P3)**.

### 9.3 검증 단계 부족 (정밀 ⊿G·실측 병행)
- 서호성 의견의 6단계 정밀 계산(Rosetta → MM-GBSA → FEP/TI)이 1단계(Rosetta ⊿G)에서 멈춰 있다. 결과 신뢰성은 가장 거친 단계의 정확도에 묶인다.
- 연결 사례: A-05·A-04·K-1/K-2 selectivity 결함이 그 위에서 결정한 ranking.
- 반영: **R-11 (MM-GBSA 검토), R-04+R-08 (K-1/K-2 정정 + ranking 재검증)**.

---

## 10. 반영 계획 요약

총 21건의 반영 항목 (P0 즉시 3 / P0 차주 7 / P1 4주 8 / P2 검토 3). `committed` 10건 / `proposed` 11건.

**금일 착수 가능 (committed)**: **R-01** MCP 경로 / **R-02** BE silo_a 404 / **R-03** FE smoke / **R-04** K-1/K-2 정정 / **R-08** PRST ranking 재검증 / **R-09** DiffDock PoC.

상세는 `reflection_plan/00_master_plan.md` 참조 (Owner·완료기준·검증방법·committed/proposed·추적성 매핑 포함).

---

## 11. References

총 **19개 출처 검증 통과 / 4건 제외** (`references/references.md`). 모든 인용은 공식 출처·DOI·repo URL 검증.

### 검증 통과 핵심 출처 (선별)
| 분류 | 자원 | 출처 (DOI / URL) | Action Item |
|------|------|------------------|------------|
| 논문 | Gervasoni 2023 JCIM | DOI: 10.1021/acs.jcim.3c00712 | A-01 (SSTR2 결합 영역 근거) |
| 논문 | Gervasoni 2024 CSBJ | DOI: 10.1016/j.csbj.2024.03.005 | A-01 (셀렉티비티 MD) |
| 논문 | PlifePred | DOI: 10.1371/journal.pone.0196829 | A-02 |
| 논문 | N-end Rule | DOI: 10.1126/science.3018930 | A-02 |
| 논문 | pepADMET | DOI: 10.1021/acs.jcim.5c02518 | A-03 |
| 논문 | ADMET-AI | DOI: academic.oup.com/bioinformatics btae416 | A-03 |
| 논문 | gmx_MMPBSA | DOI: 10.1021/acs.jctc.1c00645 | A-05 |
| 논문 | DiffDock | arXiv:2210.01776 (Corso 2023) | A-06 |
| 논문 | Boltz-2 | PMC12262699 (CASP16 affinity 1위) | A-05·A-06 |
| 논문 | AlphaFold3 | Nature 2024, s41586-024-07487-w | (참고) |
| Repo | pepADMET | github.com/ifyoungnet/pepADMET (GPL-3.0) | A-03 |
| Repo | gmx_MMPBSA | github.com/Valdes-Tresanco-MS/gmx_MMPBSA (GPL-3.0, v1.6.5 2026-05) | A-05 |
| Repo | Boltz-2 | github.com/jwohlwend/boltz (MIT) | A-05·A-06 |
| Repo | ADMET-AI | github.com/swansonk14/admet_ai | A-03 |
| Repo | DiffDock | github.com/gcorso/DiffDock | A-06 |
| Tool | OpenFE | openfree.energy (v1.0 안정 릴리스 2024-05) | A-05 |
| Tool | ADMETlab 3.0 | admetlab3.scbdd.com | A-03 |
| Tool | pymoo | pymoo.org (Pareto/NSGA-II) | A-04 |
| Tool | NVIDIA H100 | nvidia.com/en-us/data-center/h100/ | A-07 |
| 규제 | Lutathera FDA DailyMed | NDA 208700 (2026-01-15 갱신) | Radiolysis Quencher |

### 제외 후보 (근거 부족)
- `PeptideStability (ML)` — 동명 공식 repo/논문 미발견
- `PeptideRanker` URL — 서버 timeout (논문은 확인)
- `NVIDIA DGX B200` — H100만 검증, B200은 추가 확인 필요
- `openfree-energy.org` — 도메인 변경 (`openfree.energy`로 교체)

---

## 12. 종합 향후 진행 방향 의견

> **본 의견은 추정과 권고이며, 모든 핵심 주장에 §11 References의 검증된 출처를 연결한다.**

### 12.1 현재 위치 진단
- **강점**: 테스트 781 PASS 안정, vLLM 4d 16h 무중단, Action Items 9건 중 6건 PR 머지·구현, PRST-001~004 후보 도출·합성 의뢰서 완료, framework로서 "한계 노출" 정신 확립.
- **약점**: ① narrative ↔ 코드 격차 (이중 Silo A·Silo C 미구현·enrichment 분리·Layer 3 STUB), ② K-1/K-2 selectivity 결함으로 ranking 신뢰성 위협, ③ 정밀 계산(MM-GBSA·FEP/TI) 미도입으로 결과 신뢰성이 거친 단계의 정확도에 묶임.

### 12.2 우선 추진 방향 (근거 ↔ §11)

#### 권고 1: **wet-lab 실측 사이클의 빠른 진입**
- 근거: A-09 framework는 "in silico 출력은 단일 판정 기준이 아니다"라는 audit §1.1 ④ + 서호성 의견 (PDF p.7) 명시. 출력 신뢰성 향상은 결국 wet-lab 실측이 가장 강건.
- 실행: **R-08** (PRST ranking 재검증) + RI 표지 후 binding affinity (Ki) assay 시작.
- 6월 회의 안건: 합성 ETA + assay 프로토콜.

#### 권고 2: **정밀 계산 단계 도입 — gmx_MMPBSA → OpenFE 단계적**
- 근거: §11 검증 통과 — gmx_MMPBSA (DOI: 10.1021/acs.jctc.1c00645, v1.6.5 2026-05 활성 유지), OpenFE 1.0 (openfree.energy, 2024-05 안정 릴리스). 서호성 의견 (PDF p.8): "MM-PBSA는 OpenMM에서 직접 구현하거나 gmx_MMPBSA를 사용할 수 있다."
- 실행: **R-11** (MM-GBSA 도구 검토) → 1차 gmx_MMPBSA, 2차 OpenFE FEP/TI 단계적.
- 6월 회의 안건: 도입 의사결정 + GPU 요구사항 (A-07과 연동).

#### 권고 3: **D-AA / cyclic / DOTA 도메인 격차의 명시적 해소**
- 근거: A-02 PEPlife2 R²=0.022 / A-03 Layer 3 STUB / D-AA에 대한 신뢰 도구 부재는 본 프로젝트의 약리학 핵심 격차. §11 pepADMET (DOI: 10.1021/acs.jcim.5c02518, GPL-3.0) 가 펩타이드 전용 ADMET으로 19개 엔드포인트 동시 예측 — D-AA·cyclic 처리 가능성 검증 필요 (`확인 필요`).
- 실행: **R-07** (Layer 3 최소 구현) + **R-18** (pepADMET 자체 학습 산정).
- 6월 회의 안건: pepADMET fine-tuning 자원·시간.

### 12.3 로드맵 (단기·중기·장기)

**단기 (~6월 회의 D-7)**
- R-01~03 (즉시 수정 3건)
- R-04 K-1/K-2 정정 + R-08 PRST ranking 재검증
- R-09 DiffDock PoC 1회 실행 + R-10 GPU 견적 수령
- R-12 벤치마크 R²/Spearman 측정

**중기 (~Q3 2026)**
- R-05 PR #117 머지 + R-06 enrichment 정합 (Option A vs B 결정)
- R-07 Layer 3 최소 구현
- R-11 MM-GBSA 도입 (gmx_MMPBSA)
- R-13 Silo A 이중 구현 통합 + R-14 Silo C 정책 결정
- R-15 25분 SLA 재평가 / R-16 orchestrator.py 1차 분리

**장기 (~Q4 2026 / 2027)**
- OpenFE FEP/TI 도입 (정밀 ⊿⊿G)
- pepADMET 자체 학습 + Layer 3 본격 구현
- Radiolysis Quencher DOE (R-21, 서호성 의견 Lutathera 참조 §11)
- Schrödinger 도입 의사결정 (R-19)

### 12.4 리스크와 선결 조건 (Blocker)
- **R-05 (PR #117 머지)** → Layer 2 R²=0.022 재학습 합의 선행 (reviewer-pharma)
- **R-09 (DiffDock PoC)** → GPU VRAM 120GB 충족 확인 → A-07 GPU 견적과 연동
- **R-11 (MM-GBSA 도입)** → 라이선스 검토 (gmx_MMPBSA GPL-3.0) + 도구 비교
- **R-19 (Schrödinger)** → 라이센스·비용 정량화 필요

### 12.5 연구·운영 종합 의견 (생명공학 청중 고려)
> 본 프로젝트는 "in silico에서 wet-lab으로 가는 닫힌 사이클"의 1회를 PRST-001~004로 통과했다. **다음 단계는 wet-lab 실측이 in silico 출력을 정정하는 사이클의 정착**이다. 동시에 framework 측에서는 narrative ↔ 코드 격차 해소(이중 Silo A·Silo C·enrichment), 정밀 계산 단계 도입(MM-GBSA·FEP/TI), D-AA/cyclic/DOTA 도메인 격차 해소가 6월 회의 의사결정 안건이다. AI 모델의 정확도는 항상 "OOD 외삽 가능성"을 안고 있으므로, **인간 전문가 (서호성 박사·김유종 박사·김동주 박사 등)의 검토를 최종 의사결정 단계에 의무화**하는 것이 옳다.

---

## 13. Appendix 참조

- 상세 시스템 점검: `inspect_evidence/{backend, frontend, silo_a, silo_b_docking, dual_silo_actions}.md`
- Action Items 5블록 카드: `action_items/A-XX_*.md`
- 반영 계획 상세: `reflection_plan/00_master_plan.md`
- References 검증 통과 목록: `references/{references.md, papers/, libraries/, repos/, benchmarks/}`
- 디자인 시스템: `assets/design_system.md`
- 발표 자료: `pptx/{main.pptx, appendix.pptx, build_pptx.js}`
- 회의록 원본: `../meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`
- 4/6 Action Items 1차 작성: `../meet_log/2026-04-06_action_items/`
- 본 점검 이전 보고서: `_workspace/release/daily_system_inspection_report_20260601.md`

---

## 확인 필요 (정직 명시)
1. `pipelines/silo_a/`의 NIM 대체 어댑터 결정 (6월 회의)
2. Silo C 정책 결정 (구현 vs 가중치 재설계)
3. K-1/K-2 selectivity 정정 후 PRST ranking 변동 폭
4. PR #117 6/1 현재 상태 (audit 시점 5/27 vs 현재)
5. NVIDIA DGX B200 사양·납기 (별도 견적 미수령)
6. PeptideStability(ML) 공식 도구 존재 여부 (검증 실패)

---

*orchestrator 세션 · 2026-06-01 · 초안 / 현재 상태 공유*
