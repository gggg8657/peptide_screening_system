# 액션 아이템 대응 현황 추적표

**최종 갱신**: 2026-03-24
**범위**: 회의록 액션 아이템 + 보고서·계획서 전체  
**A-01~A-10 요약 표**: [`meet_log.md`](../meet_log.md) (진행 현황은 [`progress_report_20260323.md`](progress_report_20260323.md)와 정합)  
**Linear·Git 허브**: [`bio_linear_ssot.md`](bio_linear_ssot.md) — 방사성의약품 프로젝트 URL, `MeetAction` 라벨, 매핑 표

---

## 0. 회의록 액션 아이템 → 대응 현황 (meet_0212)

### 1차 미팅 (2026-01-26) — MD Agent 아키텍처

| # | 회의 액션 아이템 | 대응 상태 | 구현 자료 |
|---|----------------|:---------:|----------|
| M1-1 | SSTR2 타겟 DOTATATE 유도체 AI 설계 시스템 | ✅ 구현 완료 | Silo A (AG_src/pipeline/) + Silo B (pyrosetta_flow/) 듀얼 파이프라인 |
| M1-2 | BioNeMo API 연결 | ✅ 구현 완료 | `AG_src/tools/api/` 8개 NIM tool wrapper (esmfold, rfdiffusion, proteinmpnn 등) |
| M1-3 | 수동적 접근 (BioNeMo 불가 시) | ✅ 대안 확보 | 로컬 모델 전환 전략 수립 (`scripts/setup_local_models.sh`), NIM→로컬 마이그레이션 진행중 |
| M1-4 | Rosetta FlexPepDock 기반 도킹 | ✅ 구현 완료 | `pyrosetta_flow/runner.py` — FlexPepDock 2단계 전략 (screening 1-trial + validation N-trial) |
| M1-5 | SSTR2 특이성 스크리닝 (SSTR1/3/4/5 negative selection) | ✅ 완료 | `step05b_selectivity.py` SSTR1/3/4/5 전부 구현. CIF 경로 등록 완료 (커밋 `ec4982f`) |
| M1-6 | 혈액 내 6-10일 Stability 유지 | ⚠️ 간접 대응 | pharma_properties.py instability index + protease sites로 surrogate. 직접 half-life 예측은 pepADMET 검토 중 |

### 2차 미팅 (2026-02-12) — 아키텍처 고도화

| # | 회의 액션 아이템 | 대응 상태 | 구현 자료 |
|---|----------------|:---------:|----------|
| **구조 예측** ||||
| M2-1 | AlphaFold3 → Rosetta 대체 가능성 검토 | ✅ 결론 도출 | Hybrid 전략 채택: SSTR2 구조 고정, 펩타이드만 Rosetta/FlexPepDock 탐색. `ARCHITECTURE.md` |
| M2-2 | FastRelax 적용 시점 결정 | ✅ 구현 완료 | 1차 스크리닝 생략, 상위 후보만 2차 적용. `runner.py` 2단계 validation |
| **후보 설계** ||||
| M2-3 | 14-mer FWKT 고정 + 8잔기 변이 | ✅ 구현 완료 | `runner.py` Thompson Sampling + BLOSUM62 constraint. 5대 구조 규칙 (FWKT, K9-D122, Cys3-Cys14, Phe6-Phe11, N-term chelator) |
| M2-4 | Evolutionary-guided mutation (BLOSUM 기반) | ✅ 구현 완료 | `pharma_properties.py` BLOSUM62 conservation score + `bayesian_optimizer.py` GP surrogate |
| M2-5 | 경우의 수 폭증 문제 해결 | ✅ 구현 완료 | Bayesian Optimization + Pareto Ranking으로 탐색 효율화. 대안 스코어링 3모듈 |
| **Stability Agent** ||||
| M2-6 | Protease resistance 예측 | ✅ 부분 구현 | `pharma_properties.py` chymotrypsin/trypsin/neprilysin 3효소. pharmacology.py +pepsin. DPP-IV 미구현 |
| M2-7 | Half-life prediction | ⚠️ 간접 대응 | Instability Index (surrogate). pepADMET Half-life 모델 (5종 조직) 검토 중, 모델 파일 미확보 |
| M2-8 | Structural rigidity score | ❌ 미시작 | OpenMM MD 기반 RMSF/Rg 계산 미구현. 대안: Rosetta relax 기반 surrogate 검토 가능 |
| M2-9 | PEG/lipid modification 효과 예측 | ❌ 미시작 | Phase 4 (화학 최적화) 단계. D-AA, backbone 변형, PEGylation 미착수 |
| **Docking Agent** ||||
| M2-10 | SSTR2 specificity ΔG ranking | ✅ 구현 완료 | FlexPepDock ddG + GNINA CNN rescore + ECR consensus |
| M2-11 | SSTR1/3/4/5 negative selection | ✅ 완료 | SSTR1/3/4/5 CIF 경로 등록 완료 (커밋 `ec4982f`). selectivity 파이프라인 연결 완료 |
| **ADME/Stability 도구** ||||
| M2-12 | Serum stability predictor 최종 선정 | ✅ 보고서 완료 | `serum_stability_admet_tools_report.md` — 16개 도구 평가, Tier 1-4 계획 수립 |
| M2-13 | ADMETlab, pkCSM 활용 검토 | ✅ 평가 완료 | **소분자 도구 부적합 판정** (MW<500 전용, AD 밖). **pepADMET** (JCIM 2026) 전문 분석 완료 — 펩타이드 전용, 19 ADMET endpoints, Tier 1.5 적용 가능 |
| M2-14 | GPU 클러스터 분배 전략 | ⚠️ 계획만 | 3 conda env 전략 설계, RTX 4090 24GB 대상. 실제 실행 미시작 |
| **최종 파이프라인** ||||
| M2-15 | Step 1: Random Mutation | ✅ 구현 완료 | `runner.py` Thompson Sampling + BLOSUM constraint |
| M2-16 | Step 2: Serum Stability Screening | ✅ 구현 완료 | `pharma_properties.py` 13 methods + 5 rules (surrogate) |
| M2-17 | Step 3: DOTATATE baseline similarity | ✅ 구현 완료 | BLOSUM62 conservation score |
| M2-18 | Step 4: Structure prediction | ✅ 구현 완료 | ESMFold (NIM) + ColabFold fallback |
| M2-19 | Step 5: Docking (FlexPepDock) | ✅ 구현 완료 | pyrosetta_flow FlexPepDock 2단계 |
| M2-20 | Step 6: ΔG Ranking | ✅ 구현 완료 | GNINA CNN + ECR + Pareto NSGA-II |
| M2-21 | Step 7: Top candidates modification | ❌ 미시작 | D-AA, PEGylation, lipidation — Phase 4 |
| **추가 검토 사항 (섹션 9)** ||||
| M2-22 | Rosetta 구조 예측 대체 가능 여부 | ✅ 결론 | Hybrid 전략 (SSTR2 고정 + 펩타이드만 Rosetta) |
| M2-23 | FastRelax 적용 시점 | ✅ 결정 | 상위 후보만 2차 적용 |
| M2-24 | Serum stability predictor 선정 | ✅ 보고서 | 16개 도구 평가 완료, Tier별 계획 |
| M2-25 | ADME 단계 포함 여부 | ✅ 결정 | 물리적 constraint 기반 필터 채택 (pharma 13 methods). ADME 도구는 보조 |
| M2-26 | GPU 클러스터 분배 전략 | ⚠️ 계획만 | 3 conda env 설계, 실제 구축 미완 |
| **추천 도구 조합 (섹션 11)** ||||
| M2-27 | CycPeptPPB (cyclic peptide PPB 예측) | ❌ 미시작 | GitHub 오픈소스 확인 필요 |
| M2-28 | RPG + CleaveNet (protease resistance) | ❌ 미시작 | 자체 protease sites 3효소로 대체 중. 전용 DL 모델 미도입 |
| M2-29 | Renal avoidance score (물리 기반) | ⚠️ 부분 대응 | MW/charge/hydrophobicity 계산 → pharma_properties.py. 전용 스코어 미구현 |
| M2-30 | AGGRESCAN3D (aggregation) | ❌ 미시작 | 구조 기반, PDB 필요. Phase 3 이후 |
| M2-31 | OpenMM 짧은 MD (rigidity) | ❌ 미시작 | GPU env 구축 후 |

### 회의록 액션 대응 요약

```
총 31건 회의 액션 아이템:
  ✅ 완료      18건 (58%)  — 핵심 파이프라인, 구조 예측, 도킹, 랭킹, SSTR selectivity
  ⚠️ 부분/간접  5건 (16%)  — stability surrogate, GPU
  ❌ 미시작     8건 (26%)  — rigidity, modification, 전용 DL 도구들
```

**미시작 8건의 성격**:
- 4건은 **Phase 4 (화학 최적화)**: D-AA, PEGylation, lipidation, modification 재평가
- 2건은 **전용 DL 도구**: CycPeptPPB, CleaveNet/RPG (자체 surrogate로 커버 중)
- 1건은 **구조 기반 분석**: AGGRESCAN3D (Silo B 실행 결과 PDB 필요)
- 1건은 **MD 시뮬레이션**: OpenMM rigidity (GPU env 필요)

---

## 1. 출처별 액션 아이템 통합 현황

### 출처 A: REFACTORING_PLAN.md (22항목)

| ID | 항목 | 상태 | 대응 자료 |
|----|------|:----:|----------|
| C1 | Path traversal 취약점 | ✅ 완료 | 커밋 `79845a8` (2026-03-03) |
| C2 | 캐시 뮤테이션 위험 | ✅ 완료 | 커밋 `79845a8` |
| C3 | subprocess timeout 없음 | ✅ 완료 | 커밋 `79845a8` |
| C4 | JSON stdout 파싱 미보호 | ✅ 완료 | 커밋 `79845a8` |
| C5 | StatusEmitter 파일 잠금 없음 | ✅ 완료 | 커밋 `79845a8` |
| H1 | 아카이브 모드 3D 버튼 | ✅ 완료 | 커밋 `860472a` |
| H2 | 폴링 레이스 컨디션 | ✅ 완료 | 커밋 `99104a7` |
| H3 | CandidateTable 분리 | ✅ 완료 | 커밋 `99104a7` |
| H4 | FastAPI 마이그레이션 | ✅ 완료 | 커밋 `10bdc03` |
| H5 | Validation 엔드포인트 통합 | ✅ 완료 | 커밋 `10bdc03` |
| H6 | pytest 스위트 (118 tests) | ✅ 완료 | 커밋 `10bdc03` |
| M1 | PipelineContext 도입 | ✅ 완료 | 커밋 `99104a7` |
| M2 | 접근성 보완 | ✅ 완료 | 커밋 `99104a7` |
| M3 | 미사용 mockData 삭제 | ✅ 완료 | 커밋 `99104a7` |
| M4 | JSON 에러 응답 표준화 | ✅ 완료 | 커밋 `10bdc03` |
| M5 | Status 스키마 검증 | ✅ 완료 | 커밋 `10bdc03` |
| M6 | 매직넘버 ConfigClass 추출 | ✅ 완료 | 커밋 `10bdc03` |
| M7 | 듀얼 아키텍처 설계 문서 | ✅ 완료 | `ARCHITECTURE.md` (2026-03-04) |
| L1-L4 | Sprint 3 항목 4건 | ✅ 완료 | 2026-03-04 완료 |

> **소계**: 22/22 완료 (100%)

---

### 출처 B: pharma_properties 검증 보고서 (섹션 8)

| # | 우선순위 | 항목 | 상태 | 대응 자료 |
|---|---------|------|:----:|----------|
| B1 | P0 | DIWV 테이블 버그 수정 (12+4건) | ✅ 완료 | 커밋 `eb213c9` — peptides GT 전수 대조 0 errors |
| B2 | P0 | RW H/S/W/P 값 수정 | ✅ 완료 | 커밋 `eb213c9` — 양쪽 파일 동일값 통일 |
| B3 | P0 | Boman 부호 반전 수정 | ✅ 완료 | 커밋 `eb213c9` — `-sum/n` → `+sum/n` |
| B4 | P0 | N-end Rule P 통일 | ✅ 완료 | 커밋 `eb213c9` — (30.0h, stable) 통일 |
| B5 | **P0** | **SS bond Cys pI/charge 보정** | ✅ 완료 | pI 0.2-1.1 pH 오차. 신장 클리어런스 직결 |
| B6 | **P1** | **BLOSUM62 설계 통일** | ✅ 완료 | 전체 포지션 vs 변이만 — 해석 불일치 |
| B7 | **P1** | **MW 계산 메서드 추가** | ✅ 완료 | 방사성의약품 MW 검증 필수 |
| B8 | **P2** | **pharmacology → pharma_properties 래핑** | ✅ 완료 | 중복 코드 13개 메서드 × 2 파일 |
| B9 | P3 | Pepsin, DPP-IV protease 추가 | ✅ 완료 | 혈청 안정성 커버리지 확장 |
| B10 | P3 | Metal Coordination Ga3+ D/E 배위 추가 | ✅ 완료 | 68Ga 킬레이션 정확도 |

> **소계**: 10/10 완료 (100%) — 전 항목 완료

---

### 출처 C: serum stability / ADMET 도구 보고서 (Tier별 적용 계획)

| # | Tier | 항목 | 상태 | 대응 자료 |
|---|------|------|:----:|----------|
| C1 | Tier 1 | `peptides` 패키지 활용 | ✅ 활용 중 | cross-validation GT로 채택, 62 tests |
| C2 | Tier 1 | `modlAMP` 패키지 활용 | ⚠️ 평가만 | 설치 확인, 파이프라인 통합 미시작 |
| C3 | Tier 2 | `admet-ai` 통합 | ❌ 미시작 | Python 3.11 별도 env 필요, SMILES 변환 선행 |
| C4 | Tier 3 | `PRODIGY` ΔG 검증 | ❌ 미시작 | FlexPepDock 결과 PDB 필요 (Phase 3) |
| C5 | Tier 4 | PEPlife2 REST API 조회 | ❌ 미시작 | 네트워크 의존, best-effort |
| C6 | **신규** | **pepADMET 독성 추론** | ❌ 미시작 | 2026-03-23 논문 분석 완료, Tier 1.5. GitHub .pth 로컬 추론 (DGL 0.4.3 + PyTorch) |
| C7 | **신규** | **pepADMET descriptor 계산** | ❌ 미시작 | 2,133 feature (PyBioMed + modlAMP + RDKit). SMILES 변환 선행 필요 |
| C8 | **신규** | **pepADMET 웹 API 자동화** | ❌ 미시작 | permeability/half-life/BBB/LogD — 모델 미공개이므로 웹 API 경유 |

> **소계**: 1/7 완료 (14%) — peptides만 활용 중

---

### 출처 D: 대안 스코어링 모듈 (alternative_scoring_modules.md)

| # | 항목 | 상태 | 대응 자료 |
|---|------|:----:|----------|
| D1 | Pareto Ranking (NSGA-II) 구현 | ✅ 완료 | `pareto_ranking.py`, 9 tests passed |
| D2 | GNINA CNN Rescoring 구현 | ✅ 완료 | `gnina_rescoring.py`, 24 tests passed |
| D3 | Bayesian Optimization 구현 | ✅ 완료 | `bayesian_optimizer.py`, 24+3 tests |
| D4 | GNINA v1.3.2 바이너리 설치 | ✅ 완료 | `local_models/gnina/gnina` (~1.4GB) |
| D5 | **runner.py 통합** | ❌ 미시작 | GNINA→ECR→Pareto→BO 체인 연결 |
| D6 | **ESM-2 pseudo-perplexity** | ❌ 미시작 | ESMFold 가중치 다운로드 후 진행 |

> **소계**: 4/6 완료 (67%) — 모듈 구현 완료, 통합 미시작

---

### 출처 E: 로컬 모델 마이그레이션 (MEMORY.md 기록)

| # | 항목 | 상태 | 대응 자료 |
|---|------|:----:|----------|
| E1 | NIM → 로컬 전환 전략 수립 | ✅ 완료 | 3 conda env 전략 설계 |
| E2 | 설치 스크립트 3종 작성 | ✅ 완료 | `setup_local_models.sh`, `download_models_offline.sh`, `install_from_offline.sh` |
| E3 | GNINA v1.3.2 설치 | ✅ 완료 | `local_models/gnina/gnina` |
| E4 | **bio-tools env 구축** (ESMFold+ProteinMPNN) | ❌ 미완료 | PyTorch 미설치 (테더링 중단) |
| E5 | **rfdiffusion env 구축** | ❌ 미시작 | PyTorch 1.13.1+cu117 |
| E6 | **diffpepdock env 구축** | ❌ 미시작 | PyTorch 2.1.0+cu118 |
| E7 | **모델 가중치 다운로드** (~23GB) | ❌ 미완료 | 집 WSL → USB 이식 예정 |
| E8 | **NIM → 로컬 adapter 코드** | ❌ 미시작 | 각 Step별 로컬 호출 래퍼 |

> **소계**: 3/8 완료 (38%) — 전략/스크립트 완료, 실행 미완

---

### 출처 F: RCSB PDB 통합

| # | 항목 | 상태 | 대응 자료 |
|---|------|:----:|----------|
| F1 | rcsb_sequence_search.py 구현 | ✅ 완료 | 커밋 `32642e2` |
| F2 | runner.py RCSB 통합 | ✅ 완료 | `_rcsb_check_candidates()` |
| F3 | backend/routers/rcsb.py 엔드포인트 | ✅ 완료 | POST `/api/rcsb-search` |
| F4 | RCSBMatchPanel.tsx UI | ✅ 완료 | 커밋 `32642e2`, `54aa868`, `831cdf0` |
| F5 | RCSB 204 No Content 처리 | ✅ 완료 | graceful empty result |
| F6 | 테스트 26건 | ✅ 완료 | `test_rcsb_integration.py` |

> **소계**: 6/6 완료 (100%)

---

### 출처 G: CI/CD

| # | 항목 | 상태 | 대응 자료 |
|---|------|:----:|----------|
| G1 | 7 jobs 구성 | ✅ 완료 | `.github/workflows/ci.yml` |
| G2 | MutationAnalysis Recharts 타입 에러 | ✅ 완료 | 9연속 실패 해결 |
| G3 | RCSBMatchPanel tsc 에러 3건 | ✅ 완료 | 커밋 `831cdf0` |
| G4 | RCSBMatchPanel lint 에러 | ✅ 완료 | 커밋 `54aa868` |
| G5 | Job 5 NIM Smoke Test | ⚠️ continue-on-error | 로컬 전환 완료 후 업데이트 필요 |

> **소계**: 4/5 완료 (80%)

---

## 2. 전체 요약 — 출처별 완료율

| 출처 | 총 항목 | 완료 | 진행중 | 미시작 | 완료율 |
|------|---------|------|--------|--------|--------|
| A. REFACTORING_PLAN | 22 | 22 | 0 | 0 | **100%** |
| B. pharma 검증 보고서 | 10 | 10 | 0 | 0 | **100%** |
| C. ADMET 도구 Tier계획 | 8 | 1 | 1 | 6 | 13% |
| D. 대안 스코어링 | 6 | 4 | 0 | 2 | 67% |
| E. 로컬 모델 마이그레이션 | 8 | 3 | 0 | 5 | 38% |
| F. RCSB 통합 | 6 | 6 | 0 | 0 | **100%** |
| G. CI/CD | 5 | 4 | 1 | 0 | 80% |
| **합계** | **65** | **50** | **2** | **13** | **77%** |

---

## 3. 미완료 항목 — 의존성 체인 정리

```
의존성 없음 (즉시 착수 가능)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B5  SS bond Cys pI 보정        ← P0, 코드만
B6  BLOSUM62 통일              ← P1, 코드만
B7  MW 메서드 추가             ← P1, 코드만
B8  pharmacology 래핑 통합     ← P2, 코드만
B9  DPP-IV protease 추가      ← P3, 코드만
B10 Ga3+ D/E 배위 추가        ← P3, 코드만
D5  대안 스코어링 runner 통합   ← P1, 코드만
C2  modlAMP 파이프라인 통합    ← P2, 코드만

네트워크 의존 (다운로드 필요)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E7  모델 가중치 23GB 다운로드
    │
    ├→ E4  bio-tools env (ESMFold+ProteinMPNN)
    │      └→ D6  ESM-2 pseudo-perplexity
    │      └→ E8  NIM→로컬 adapter
    │
    ├→ E5  rfdiffusion env
    │
    └→ E6  diffpepdock env

별도 env 필요 (네트워크 + 환경 구축)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C6  pepADMET 독성 추론     ← Python 3.7 + DGL 0.4.3 + PyTorch + GitHub clone
C7  pepADMET descriptor    ← PyBioMed + modlAMP + RDKit (SMILES 변환 선행)
C8  pepADMET 웹 API 자동화 ← 네트워크 (pepadmet.ddai.tech)
C3  admet-ai              ← Python 3.11 별도 env

실행 결과 의존 (선행 완료 후)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C4  PRODIGY ΔG 검증        ← Silo B 실행 결과 PDB 필요
C5  PEPlife2 REST API      ← 네트워크 + 후보 서열 확정 후
```

---

## 4. 권장 실행 순서

### Wave 1: 즉시 (코드 작업, 의존성 없음)
1. B5 — SS bond Cys pI/charge 보정
2. B7 — MW 메서드 추가
3. B6 — BLOSUM62 설계 통일
4. D5 — 대안 스코어링 runner.py 통합
5. B8 — pharmacology.py → pharma_properties.py 래핑

### Wave 2: 다운로드 후 (집 WSL 접근 시)
6. E7 — 모델 가중치 23GB 다운로드
7. E4/E5/E6 — conda env 3종 구축
8. D6 — ESM-2 pseudo-perplexity

### Wave 3: env 구축 후
9. C6/C7 — pepADMET 독성 추론 + descriptor (DGL 0.4.3 env)
10. C8 — pepADMET 웹 API 자동화 (permeability/half-life/BBB/LogD)
11. E8 — NIM→로컬 adapter
12. C3 — admet-ai (SMILES 변환 포함)

### Wave 4: 대규모 실행
13. Silo B 22,000 후보 실행
14. C4 — PRODIGY ΔG 검증
15. B9/B10 — DPP-IV, Ga3+ 확장
