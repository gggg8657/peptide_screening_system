# M5 — 통합 모듈 Spec 정확성 + 약리학 검증 보고서

> **작성**: reviewer-pharma · 2026-05-13  
> **모듈**: `module-verification-2026-05-13` 팀  
> **범위**: step01~step08 + step05c + stability_predictor 모듈별 출력값 신뢰도 + 약리학 cross-check  
> **회귀 테스트**: ✅ **39/39 PASS** (`pharmacology_guards.py` — 2026-05-13 실행 확인)

---

## 0. 사전 의무 — pharmacology_guards 회귀 테스트

```
pytest pipeline_local/tests/test_pharmacology_guards.py -v
============================= test session starts ==============================
collected 39 items
...
============================== 39 passed in 0.13s ==============================
```

> **상태**: 39/39 PASS (원 명세 33건 + 후속 U1/VR-cycle 추가 6건)  
> **주의**: 테스트 수가 원 문서 기술(33) 대비 39로 증가됨 → CLAUDE.md 및 README 업데이트 권장 (Action Item A-1)

---

## 1. 모듈별 출력값 신뢰도 매트릭스

### 분류 기준
| 등급 | 정의 | 사용 방식 |
|------|------|----------|
| **A** (실측 기반) | 실험 데이터 또는 물리 법칙으로 직접 검증 가능 | 보고 값으로 인용 가능 |
| **B** (in-silico 추정) | AI/모델 기반, 내부 일관성 有 but 실측 검증 미완 | 스크리닝 순위 참고 (⚠️ in-silico) |
| **C** (의심) | 검증 부족 또는 실측 불일치 문서화됨 | 보고 금지, 추가 검증 필수 |
| **HEURISTIC** | `pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS` 등록됨 | ranking score 전용, 임상 단위 인용 금지 |

---

### 1.1 step01 — SSTR2 수용체 준비 (Receptor Preparation)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `sstr2_receptor.pdb` (기존 PDB 로드) | 구조 파일 | **A** | 실험 구조 (X-ray/cryo-EM) | Chen 2022 cryo-EM SSTR2 구조 |
| `binding_pocket.json` (centroid) | Dict | **B** | 기하학적 계산 (5 Å cutoff) | 실측 pocket과 근사 |
| `binding_pocket.json` (pocket_residues) | List[int] | **B** | cutoff 기반 자동 추출 | W8·K9·T10 pharmacophore 문헌과 비교 권장 |
| OpenfoldP3 구조 예측 (fallback) | 구조 파일 | **B** | AI 예측 모델 | fallback 경로만 사용 권장 |

**부호 규약**: N/A (좌표, residue index)

---

### 1.2 step02 — 백본 생성 (RFdiffusion)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `backbone_{i}.pdb` | 구조 파일 | **B** | AI de novo 생성 | 실험 검증 없음 |
| 원자 개수 검증 (`_MIN_ATOM_COUNT=50`) | bool | **A** | 기하학적 | 최소 구조 완결성 확인 |

**한계**: RFdiffusion은 바인더-수용체 상호작용 에너지를 직접 최적화하지 않음. Backbone의 fold가 실제 결합 형태와 다를 수 있음.

---

### 1.3 step03 — 서열 설계 (ProteinMPNN)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| 설계 서열 (`*.fasta`) | str | **B** | AI inverse folding | 실험 검증 없음 |
| Sequence diversity (Hamming 등) | float | **A** | 수학적 계산 | 서열 간 비교값 |
| sampling_temp 영향 | — | **B** | ProteinMPNN paper | temp 낮을수록 보수적 |

---

### 1.4 step04 — 구조 QC (ESMFold pLDDT)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `plddt_mean` (0-100) | float | **B** | ESMFold B-factor | 14-mer cyclic peptide 적합성 미검증. 짧은 펩타이드 pLDDT 과대평가 가능 |
| `plddt_interface` (0-100) | float | **B** | pocket_residues 기반 평균 | pocket 정의 정확도에 의존 |
| `disulfide_distance` (SG-SG, Å) | float | **A** | 기하학적 측정 | 물리적 bond 거리 (~2.05 Å) |
| `disulfide_intact` | bool | **A** | `max_distance=2.5 Å` 기준 | pass/fail |
| `passed_gate` | bool | **B** | pLDDT 임계값 (75/70) 기반 | 임계값 자체의 임상 의미 미검증 |

**부호 규약**: pLDDT 0-100 (높을수록 신뢰도 높음) ✅ 표준  
**GATE 기준**: mean pLDDT ≥ 75, interface pLDDT ≥ 70, SS bond SG-SG ≤ 2.5 Å

**비고**: ESMFold의 B-factor는 AlphaFold 방식의 pLDDT가 아닌 ESMFold 자체 confidence. PyRosetta disulfide 형성 후 B-factor가 덮어쓰여지므로 pLDDT는 **disulfide 형성 전** 값으로 기록 (step04.py L282 주석 확인됨 ✅).

---

### 1.5 step05 — 도킹 (DiffPepBuilder / Boltz-2)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| DiffPepBuilder confidence score | float | **B** | AI pose 신뢰도 | pose 기하 신뢰도. Ki와 상관 미검증 |
| `Boltz2Result.iptm` (0-1) | float | **C** | geometry 신뢰도 | ⚠️ Ki 순위와 Spearman ρ≈-0.3 (§3.3 상세) |
| `Boltz2Result.affinity_kcal` (kcal/mol) | float | **C** | Boltz2 내부 추정 | 이름은 "affinity_kcal"이지만 실측 Ki/Kd와 직결 불가. 보정 인자 없음 |
| `docking_score` 기반 Top-20% gate | bool | **B** | 상대 순위 기반 | 절대값 의미 없음, 상대 순위만 유효 |

**부호 규약**:  
- DiffPepBuilder: `scores` → 낮을수록 좋음 (confidence score)  
- Boltz iPTM: 높을수록 좋음 (0-1)  
- affinity_kcal: **음수=유리한 결합** (step05c.py 명시) ✅

---

### 1.6 step05b — 선택성 스크리닝 (Multi-Receptor Docking)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `selectivity_margin` (dock_score 기반) | float | **C** | score 차이 | 실측 Ki selectivity (Ki_SSTR1/Ki_SSTR2)와 상관 미검증 |
| `offtarget_max_score` | float | **C** | 위와 동일 | |
| `passed_gate` | bool | **C** | margin_min 기반 | |

**부호 규약**: `selectivity_margin = dock_score(SSTR2) - max(dock_score(off-targets))`  
→ **낮을수록 SSTR2 선택적** (dock_score: 낮을수록 강한 결합이므로)  
→ **step05c와 부호 방향이 반대** (§5.2 상세) ⚠️

---

### 1.7 step05c — Boltz 교차 검증 (Selectivity Cross-Validation)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `iPTM` per receptor | float | **C** | geometry 신뢰도 | Ki 순위와 Spearman ρ≈-0.3 (step05c.py docstring §3) |
| `selectivity_margin` (iPTM 기반) = iPTM(SSTR2) - max(iPTM(off)) | float | **C** | iPTM 차이 | geometry 기반 1차 스크리닝 |
| Tier (T0~T3) | str | **C** | margin 임계값 분류 | T3 ≥ 0.03, T2 ≥ 0.00, T1 ≥ -0.03, T0 < -0.03 |

**한계 (step05c.py docstring 인용)**:
> iPTM은 *구조 geometry 신뢰도*이며 *결합 친화도(Ki/Kd) 또는 selectivity 순위의 비례 proxy 아님*.  
> SST-14 실측 검증: SSTR2 Ki=0.2 nM이지만 iPTM=0.946 (4위), SSTR1 Ki=0.4 nM이지만 iPTM=0.975 (1위)  
> → **순위 일치 0/5** (Spearman ρ≈-0.3)

**결론**: Tier 분류는 **구조 geometry 기반 1차 필터링**에만 사용. 정량 선택성 평가는 FEP/MM-GBSA/실측 Ki 필요.

---

### 1.8 step06 — Rosetta 정밀 정제

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `ddG` (kcal/mol) | float | **B** | PyRosetta ref2015 | ideal coord 출발점 한계 (VR-cycle-08, HEURISTIC 등록) |
| `clash_score` | int | **A** | 기하학적 검사 | 물리적 충돌 (0 = no clash) |
| `constraint_violations` | int | **A** | SS bond 거리 제약 | 물리 기하 기반 |
| Per-residue energy | Dict[int, float] | **B** | ref2015 | modification 전후 *상대* 비교만 유효 |

**부호 규약**: ddG → **음수=유리한 결합, 양수=불리** (Rosetta ref2015 표준) ✅  
**GATE 기준**: ddG ≤ -5.0 kcal/mol, clash_score = 0  
**HEURISTIC 등록**: `pyrosetta.pose_from_sequence_ideal_coord` — ideal coord에서 시작, native energy minimum 도달 보장 없음 (VR-cycle-08).

---

### 1.9 step07 — 분석 + 시각화 (FoldMason / PyMOL)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| `lDDT` (0-1) | float | **B** | 구조 유사도 점수 | 참조 구조 의존 |
| Contact residues (Å 기반) | List[int] | **A** | 기하학적 | 물리적 거리 기준 |
| H-bond count | int | **A** | 기하학적 | 물리적 |
| Hydrophobic SASA | float | **B** | 프로그램 모델 의존 | 용매 접근 표면 추정 |

---

### 1.10 step08 — 안정성 평가 (HEURISTIC ranking scores)

| 출력값 | 표면 단위 | 신뢰도 | HEURISTIC 등록 | 설명 |
|--------|-----------|--------|---------------|------|
| `predict_half_life(seq, mods)` | hours | **HEURISTIC** | ✅ | 임상 t½ 아님. ranking score 전용 |
| `suggest_modifications()` | List[ModificationSuggestion] | **HEURISTIC** | ✅ | GLP-1 기반 휴리스틱 우선순위 |
| `_compute_stability_score()` | 0-1 | **HEURISTIC** | ✅ | sigmoid 정규화. 임상 안정성 확률 아님 |
| `_PROTEASE_VULNERABILITY[aa]` | 0-3 | **HEURISTIC** | ✅ | 정성적 protease 선호도. kcat/Km 정량 출처 없음 (VR-S5-01) |

---

### 1.11 stability_predictor (core.py / combined)

| 출력값 | 타입 | 신뢰도 | 근거 | 비고 |
|--------|------|--------|------|------|
| MW (Da) | float | **A** | 원소 질량 합산 | 오차 ±0.01 Da |
| pI (isoelectric point) | float | **A/B** | Biopython ProtParam (Henderson-Hasselbalch) | Lehninger pKa set 기반 **A** — cyclic peptide는 미검증 **B** |
| GRAVY (Kyte-Doolittle mean) | float | **A** | LITERATURE_VALUES 검증 ✅ | `assert_in_range("kyte_doolittle_mean")` |
| Instability Index (Guruprasad) | float | **B** | Guruprasad 1990 (PEDS 4:155) | 일반 단백질 훈련셋. cyclic peptide, D-AA 검증 부재 |
| Boman Index (kcal/mol) | float | **A/B** | Radzicka-Wolfenden (Boman 2003 sign-flip) | 부호 규약 LITERATURE_VALUES 검증 ✅. 단, cyclic peptide 미검증 **B** |
| Aliphatic Index (Ikai 1980) | float | **A** | LITERATURE_VALUES 검증 ✅ (Val=2.9, Ile/Leu=3.9) | 열안정성 proxy |
| `hl_score_heuristic` | hours | **HEURISTIC** | ✅ 등록됨 | step08 predict_half_life 동일 한계 |
| ADMET 신독성 (compute_admet) | High/Mod/Low | **C** | AG_src/backend/admet.py DLscore | **DLscore 100/100 포화 문제** (§검증 필요 G-05) |

---

### 신뢰도 매트릭스 요약 (9 모듈 × 카테고리)

```
               A(실측)   B(추정)   C(의심)   HEURISTIC
─────────────────────────────────────────────────────
step01          2         2         0          0
step02          1         1         0          0
step03          1         1         0          0
step04          3         2         0          0
step05          0         1         2          0
step05b         0         0         3          0
step05c         0         0         3          0
step06          2         2         0          0  (ddG: HEURISTIC에 가까움)
step07          2         2         0          0
step08          0         0         0          4
stability_pred  3         3         1          1
─────────────────────────────────────────────────────
합계           14        14         9          5
```

> **경고**: C등급 9개 중 5개가 iPTM/selectivity 관련. 파이프라인의 핵심 선택성 지표(step05~05c)가 모두 C등급임을 인지해야 함.

---

## 2. HEURISTIC_FUNCTION_DISCLAIMERS 적용 현황

### 2.1 등록 함수 목록 (pharmacology_guards.py §3)

| QualName | surface_unit | confidence_grade | fix_status |
|---------|-------------|-----------------|------------|
| `step08_stability.predict_half_life` | hours | HEURISTIC | VR-cycle-09 closure 2026-05-11 ✅ |
| `step08_stability.suggest_modifications` | list[ModificationSuggestion] | HEURISTIC | VR-cycle-09 closure 2026-05-11 ✅ |
| `step08_stability._compute_stability_score` | 0-1 score | HEURISTIC | VR-cycle-09 closure 2026-05-11 ✅ |
| `step08_stability._PROTEASE_VULNERABILITY` | 0-3 per residue | HEURISTIC | VR-S5-01 partial closure 2026-05-11 ✅ |
| `stability_predictor.compute_stability` | StabilityResult | HEURISTIC | U1 2026-05-12 ✅ |
| `stability_predictor.batch_evaluate` | List[StabilityResult] | HEURISTIC | U1 2026-05-12 ✅ |
| `pyrosetta.pose_from_sequence_ideal_coord` | ref2015 score | HEURISTIC | VR-cycle-08 partial closure ✅ |

**등록 수**: 7개 / 7개 ✅

### 2.2 UI/API 자동 disclaimer 부착 현황

| 위치 | 현황 | 권장 |
|------|------|------|
| `step08_stability.py` 모듈 docstring | ✅ 명시 (`⚠️ 휴리스틱...`) | - |
| `stability_predictor/core.py` docstring | ✅ 명시 | - |
| `pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS` API | ✅ `is_heuristic_function()` 제공 | 호출자가 사용하도록 강제 필요 |
| **UI (프론트엔드 표시)** | ⚠️ **미확인** | `⚠️ in-silico 추정값 (ranking score)` 배지 의무 |
| **API 응답 JSON** | ⚠️ **미확인** | `"confidence": "HEURISTIC"` 필드 자동 부착 |
| `stability_predictor.combined_report.py` | ⚠️ 확인 필요 | disclaimer 문자열 포함 여부 |

> **Action Item A-2**: UI에서 `hl_score_heuristic` 표시 시 `⚠️ in-silico 추정값` 배지 의무화. `backend/routers/` API 응답에 `"confidence_grade": "HEURISTIC"` 필드 자동 주입.

---

## 3. 약리학적 Cross-Check

### 3.1 cand03 (G2I: AICKNFFWKTFTSC) — 알려진 SST-14 modification 사례?

**서열**: SST-14 `AGCKNFFWKTFTSC` → cand03 `AICKNFFWKTFTSC` (pos2: G→I)

| 항목 | 값 | 출처 | 신뢰도 |
|------|-----|------|--------|
| MW | 1696.0 Da | Biopython ProtParam | **A** |
| GRAVY | 0.379 | Kyte-Doolittle | **A** |
| Instability Index | 30.65 | Guruprasad 1990 | **B** |
| 신독성 | High | compute_admet (DLscore) | **C** (포화 문제) |
| HL ranking score | 16.60 | predict_half_life (HEURISTIC) | **HEURISTIC** |

**문헌 근거 검토**:
- G→I at pos2: SST-14의 Gly2는 β-turn 전환 위치. Ile 치환으로 소수성 증가 (GRAVY 0.029→0.379).
- 알려진 analogues: Octreotide (8-mer cyclic)에서는 pos2 존재 않음. 14-mer analogues에서 pos2 변이 선례는 **문헌 미확인** (§ VB-01 참조).
- **Ile2가 Cys3-SS bond conformation에 미치는 영향**: Ile의 β-branching이 Cys3 χ 각도에 sterically 영향 가능 → in-silico 구조 확인 권장.
- **약리학적 결론**: G2I 치환은 소수성 증가 목적으로 타당하나 SSTR2 pharmacophore (F6/F7/W8/K9/T10) 외부 위치이므로 결합력 직접 손상 위험은 낮음 (MED 신뢰).

### 3.2 ILCKKFFWKTFTSC — 약리학적 의미 종합

**서열**: I1L2C3K4K5F6F7W8K9T10F11T12S13C14 (Cys3-Cys14 SS bond 유지)

| 항목 | 값 | 신뢰도 | 해석 |
|------|-----|--------|------|
| MW | 1752.1 Da | **A** | SST-14 대비 +112.2 Da |
| GRAVY | 0.493 | **A** | 높은 소수성. 용해도↓ 가능성 |
| Instability Index | **55.14** | **B** | >40 = unstable (Guruprasad 기준). 다른 후보 30.65 대비 2× |
| Boman Index | (계산 필요) | **A** | KK 쌍으로 양수 증가 → 단백 결합 가능성↑ |
| HL ranking score | **12.80** | **HEURISTIC** | 후보 중 최저 (Trypsin site 3개: K4, K5, K9) |
| Trypsin sites | 3 (K4-N5, K5-F6, K9-T10) | **A (문헌)** | Reubi 2000: K-X 절단 |
| Boltz iPTM margin | +0.070 (T3, selectivity 최강) | **C** | geometry 신뢰도, Ki 상관 미검증 |

**약리학적 결론**:
- **장점**: Boltz T3 selectivity (geometry 기반), I1L2 소수성 증가
- **단점**: Instability Index 55.14 (≥40 = unstable), 트립신 site 3개, HL ranking 최저
- **처방 (다도메인 합의)**: K5→Orn + D-Phe6 + N-term DOTA 조합 적용 시 조건부 GO
  - K5→Orn: 트립신 site K5-F6 제거 (Knudsen & Lau 2019)
  - D-Phe6: NEP F6-F7 1차 cleavage site 차단 (Tatsi 2024)
  - 합성 비용: ₩5-8M (패키지 C, chemistry S3)

### 3.3 Boltz iPTM 0.94 vs octreotide Ki 0.2 nM — 일치 여부?

**데이터** (step05c.py docstring + 문헌):

| 수용체 | Ki (nM) [Reubi 2000] | iPTM [Boltz, SST-14] | Ki 순위 | iPTM 순위 |
|--------|---------------------|---------------------|---------|----------|
| SSTR2 | **0.2** (최강) | 0.946 | **1위** | **4위** ← 역전 ⚠️ |
| SSTR5 | 0.3 | 0.913 | 2위 | 5위 |
| SSTR1 | 0.4 | 0.975 | 3위 | 1위 |
| SSTR3 | 0.8 | 0.958 | 4위 | 2위 |
| SSTR4 | 1.6 | 0.956 | 5위 | 3위 |

**Spearman ρ ≈ -0.3** (step05c.py 계산)  

**결론**: Boltz iPTM 0.94와 Ki 0.2 nM은 **일치하지 않음**.
- iPTM = *구조 geometry 신뢰도* (folding confidence)
- Ki = *결합 친화도* (열역학적 equilibrium)
- 목표 수용체(SSTR2)에서 **Ki 1위이지만 iPTM 4위**라는 역전 현상이 실측됨
- **해석 지침**: iPTM은 "Boltz가 구조를 얼마나 확신하는가"이며 "얼마나 강하게 결합하는가"가 아님
- **실천 원칙**: iPTM을 Ki/Kd 대리 지표로 사용하는 모든 보고 금지 (C등급 유지)

> ⚠️ **UI 경고 의무**: step05c 결과 표시 시 `"iPTM ≠ Ki proxy — Spearman ρ≈-0.3"` disclaimer 필수.

### 3.4 HL 64.72 (var12: AICKNFFWKTF[D-Thr12]SC) — 임상 t½ 90min 도달 가능?

**데이터**:
- var12 HL ranking score = **64.72** (heuristic, HEURISTIC 신뢰 등급)
- 임상 t½ 90 min = **octreotide 실측 혈중 반감기** (Veber 1978, Reubi 2000)

**분석**:

| 항목 | var12 | octreotide | 비교 가능? |
|------|-------|-----------|-----------|
| HL 값 | 64.72 (heuristic score) | 90 min (임상 t½) | ❌ 단위·측정법 상이 |
| 측정 방법 | 잔기 vulnerability 점수 + modification 보너스 단순 가산 | 인간 혈장 LC-MS/MS 실측 | 전혀 다름 |
| D-Thr12 효과 | cyclization bonus 24h + penalty_factor 조정 반영 | NEP T10-F11 절단 차단 (정성) | 방향 일치 가능 |

**결론**:
- HL 64.72는 **임상 반감기 64.72시간이 아님** — 후보 간 상대 순위 스코어
- "임상 t½ 90min 도달 가능?"이라는 질문 자체가 **HEURISTIC 출력값 vs 임상 측정값을 직접 비교하는 잘못된 프레이밍**
- 타당한 질문: "D-Thr12 modification으로 ranking score가 향상되는가?" → **Yes (var12 64.72 > cand03 baseline 16.60)**
- 실제 임상 t½ 90min 도달 여부: **wet-lab serum stability assay (37°C, human serum 80%)** 필요
  - D-Thr12 → NEP T10-F11 cleavage site 부분 차단 예상 (정성 근거: biology S1)
  - 실측 시 octreotide (90min) 수준 달성 가능성: **LOW-MED** (정성 추정, 문헌 선례 없음)

> **보고 형식 의무**: "var12 HL ranking score = **64.72** (heuristic — `predict_half_life` 출처: `step08_stability.py`, 신뢰 등급: HEURISTIC). 임상 t½ 예측값 아님. 실 wet-lab assay 필요."

---

## 4. 시스템 한계 — 빈 칸 목록 (Gaps)

### 4.1 PK (in-vivo)

| 빈 칸 | 현재 상태 | 필요 wet-lab |
|--------|----------|-------------|
| 혈중 t½ (plasma half-life) | HEURISTIC ranking score만 존재 | human serum stability assay (LC-MS/MS, 37°C) |
| 단백 결합율 (fu) | 없음 | ultrafiltration + LC-MS |
| 분포 부피 (Vd) | 없음 | 단회투여 PK study (mouse) |
| 신장 청소율 (CLr) | 없음 | 방사성 표지 + 뇨 수집 |
| 생체이용률 (F) | 없음 | SC/IV 비교 AUC |
| 알부민 결합 affinity (Kd,HSA) | 없음 | SPR (Surface Plasmon Resonance) |

### 4.2 독성

| 빈 칸 | 현재 상태 | 필요 wet-lab |
|--------|----------|-------------|
| 급성 독성 (LD50) | 없음 | 동물 MTD 실험 |
| 신독성 (quantitative) | compute_admet DLscore (포화, **C**) | RPTEC 세포 독성 assay |
| 간독성 | 없음 | HepaRG 세포 assay |
| hERG 저해 | compute_admet (소분자 모델, 미검증) | patch-clamp electrophysiology |
| 세포 독성 (SSTR2+ tumor cell line) | 없음 | AR42J, NCI-H727 MTT assay |

**비고**: compute_admet DLscore 100/100 포화 문제 (§검증 필요 G-05) → 신독성 판별이 모든 펩타이드에서 "High"로 나와 변별력 없음. 규칙 재정의 필요.

### 4.3 면역원성

| 빈 칸 | 현재 상태 | 필요 wet-lab |
|--------|----------|-------------|
| T-cell 에피토프 | 없음 | NetMHCpan in-silico + PBMC assay |
| ADA (항약물 항체) | 없음 | ELISA (인체 혈청) |
| MHC II 결합 | 없음 | in-silico (IEDB) + in-vitro DC assay |

**비고**: 14-mer 펩타이드는 소분자 대비 면역원성 위험 높음. Ac/NH2 캡핑이 일부 완화하지만 정량 평가 없음.

### 4.4 방사성의약품 특이 항목

| 빈 칸 | 현재 상태 | 필요 실험 |
|--------|----------|----------|
| ¹⁷⁷Lu 라벨링 효율 | 없음 | DOTA-metal coordination assay |
| 방사성 화학 순도 (RCP) | 없음 | radio-HPLC |
| ¹⁷⁷Lu-후보 체내 분포 (biodistribution) | 없음 | mouse tumor xenograft |
| 표적/비표적 비율 (T/NT) | 없음 | 위와 동일 |
| 방사선 흡수선량 (dosimetry) | 없음 | MIRD/OLINDA 계산 |

---

## 5. 모듈 간 Consistency 검증

### 5.1 step04 pLDDT vs step05 Boltz iPTM

| 항목 | pLDDT (ESMFold) | Boltz iPTM |
|------|-----------------|------------|
| 측정 개념 | 단일 서열 구조 예측 신뢰도 | 복합체(peptide+receptor) 구조 신뢰도 |
| 범위 | 0-100 | 0-1 |
| 상관관계 | **미문서화** | — |
| Gate 역할 | step04 통과 기준 | step05 ranking |
| 일치 보장? | **없음** | pLDDT 높아도 iPTM 낮을 수 있음 |

**평가**: 두 지표는 서로 다른 컨텍스트 측정값으로 직접 상관관계 비교가 부적절. 다만 두 지표 모두 높은 후보가 구조적으로 더 신뢰 가능 (정성적 방향 일치).

**Action Item A-3**: step04 pLDDT ≥ 75 PASS + step05c Boltz iPTM 결과를 동일 후보에 대해 散布圖로 시각화 → 일치/불일치 패턴 확인.

### 5.2 step05b PyRosetta ddG vs step05c Boltz iPTM — 불일치 분석

**⚠️ 부호 방향 충돌 발견**:

```
step05b selectivity_margin = dock_score(SSTR2) - max(dock_score(off_target))
    → 낮을수록 SSTR2 선택적 (dock_score: 낮을수록 강한 결합)

step05c selectivity_margin = iPTM(SSTR2) - max(iPTM(off_target))
    → 높을수록 SSTR2 선택적 (iPTM: 높을수록 구조 신뢰도 높음)
```

| 항목 | step05b | step05c |
|------|---------|---------|
| 기반 지표 | dock_score (낮을수록 좋음) | iPTM (높을수록 좋음) |
| margin 해석 | 음수 = SSTR2 선택적 | 양수 = SSTR2 선택적 |
| GATE 방향 | `margin <= threshold` | `margin >= threshold` |
| 일치 여부 | **방향 반대** | ⚠️ UI에서 혼용 주의 |

**실제 데이터 불일치 사례** (ILCKKFFWKTFTSC):
- step05c Boltz T3 margin +0.070 (selectivity 최강) ✅
- step08 HL ranking 12.80 (stability 최약) ⚠️
- Biopython Instability 55.14 (>40, unstable) ⚠️
→ selectivity와 stability가 trade-off 관계로 설계 공간에서 Pareto front 존재 → NSGA-II 다목적 최적화 적절

**Action Item A-4**: step05b/step05c의 selectivity_margin 정의를 공통 인터페이스로 통일. 가능하면 동일 부호 방향 채택 또는 명시적 `higher_is_better` 플래그 추가.

### 5.3 step08 stability vs Biopython Instability Index — 방향 일치 검증

| 후보 | step08 HL (HEURISTIC) | Biopython II | 방향 일치? |
|------|----------------------|-------------|----------|
| cand03 (AICKNFFWKTFTSC) | 16.60 | 30.65 (stable ✅) | ✅ |
| ILCKKFFWKTFTSC | **12.80 (최저)** | **55.14 (unstable ⚠️)** | ✅ (모두 불안정 신호) |
| VLCKNFFWKTFTSC | (계산 필요) | 30.65 (stable ✅) | 예상 ✅ |
| AICKAFFWKTFTSC | (계산 필요) | 41.39 (⚠️ borderline) | 예상 ✅ |
| SST-14 ref | (baseline) | 30.65 (stable ✅) | — |

**결론**: step08 HL ranking score와 Biopython Instability Index는 **방향(불안정 후보 식별)에서 일치**. ILCKKFFWKTFTSC가 두 지표 모두 최악으로 일관성 확인됨.

**주의**: D-AA (D-Thr12 등) 도입 후보에서 Biopython ProtParam은 **D-아미노산을 인식하지 못함** (L-AA와 동일하게 처리). var12 D-Thr12의 Instability Index는 D-Thr → L-Thr 로 계산됨 → 실제 D-AA 도입 효과 반영 못함. pepADMET (D-AA 지원) 도입 권장 (§ G-01).

---

## 6. pharmacology_guards 확장 권장 사항

### 6.1 현재 미등록 주요 항목

| 항목 | 이유 | 권장 Action |
|------|------|------------|
| Boltz iPTM → Ki 단위 변환 금지 | Spearman ρ≈-0.3 불일치 실증 | `HEURISTIC_FUNCTION_DISCLAIMERS`에 `"boltz.iptm_as_ki_proxy"` 등록 |
| compute_admet DLscore 100/100 포화 | 변별력 없음 (§ G-05) | `SCALE_RANGES`에 `"admet_dlscore"` 추가 + 포화 경고 가드 |
| ESMFold pLDDT (0-100 범위) | 범위 체크 없음 | `SCALE_RANGES["esmfold_plddt"]` = (0.0, 100.0) 추가 |
| step05b selectivity_margin 부호 방향 | step05c와 충돌 | `SIGN_CONVENTIONS["selectivity_margin_step05b"]` 추가 |

### 6.2 VR-S5-01 후속 조치 (부분 미완료)

- **상태**: `_PROTEASE_VULNERABILITY` 출처 부재 등록됨 (partial closure)
- **남은 작업**: 트립신 kcat/Km 정량 문헌 (e.g., Schechter-Berger 모델) 기반 lookup table 신규 작성
- **우선순위**: MED (현 heuristic이 ranking 방향에서는 정확하므로 즉시 위험 없음)

---

## 7. §검증 필요 (이번 M5 신규 식별)

| ID | 항목 | 우선순위 | 필요 Action |
|----|------|---------|------------|
| **M5-P1** | ILCKKFFWKTFTSC D-Thr12 도입 후 Instability Index 재계산 (D-AA 인식 가능 도구) | High | pepADMET 또는 PepCalc |
| **M5-P2** | Boltz affinity_kcal (kcal/mol 표기) 실제 Ki/Kd 상관관계 검증 (문헌 보정 인자 여부) | High | MM-GBSA 비교 또는 문헌 조사 |
| **M5-P3** | compute_admet DLscore 100/100 포화 — 규칙 재정의 또는 대체 도구 도입 | High | pepADMET 29 endpoint |
| **M5-P4** | step05b/step05c selectivity_margin 부호 방향 통일 스펙 확정 | Med | engineer-backend PR |
| **M5-P5** | pLDDT (step04) ↔ iPTM (step05c) 상관관계 데이터 수집 (n≥10 후보 散布圖) | Med | pipeline run + 분석 |
| **M5-P6** | `pharmacology_guards` 회귀 테스트 수 (39)와 문서 기술 (33) 불일치 업데이트 | Low | CLAUDE.md, README 수정 |

---

## 8. 신뢰 등급 요약 표

| 모듈 출력값 | 등급 | 인용 방식 |
|------------|------|---------|
| MW, pI, GRAVY, Aliphatic Index | **A** | 보고값으로 인용 가능 |
| ESMFold pLDDT | **B** | `⚠️ in-silico` 표기 |
| Boman Index, Instability Index | **B** | `⚠️ in-silico` 표기 + D-AA 한계 주석 |
| PyRosetta ddG | **B** | `⚠️ ideal coord 한계` 표기 |
| FoldMason lDDT | **B** | `⚠️ in-silico` 표기 |
| Boltz iPTM | **C** | Ki proxy 사용 금지. geometry 신뢰도만 |
| step05b/5c selectivity_margin | **C** | 정량 선택성 보고 금지 |
| affinity_kcal (Boltz) | **C** | Ki/Kd 대리 사용 금지 |
| compute_admet nephrotox (DLscore) | **C** | 포화 문제, 절대값 신뢰 금지 |
| predict_half_life | **HEURISTIC** | "ranking score (heuristic)" 표기 의무 |
| stability_predictor.hl_score_heuristic | **HEURISTIC** | 위와 동일 |
| _compute_stability_score | **HEURISTIC** | "0-1 ranking score (heuristic)" |
| suggest_modifications | **HEURISTIC** | "우선순위 제안 (heuristic)" |

---

## 9. 결론

1. **pharmacology_guards 39/39 PASS** — lookup table 환각 방지 시스템 정상 작동 ✅
2. **신뢰도 분포**: A 14개 / B 14개 / C 9개 / HEURISTIC 5개 — C등급이 핵심 선택성 지표 집중 ⚠️
3. **Boltz iPTM ≠ Ki proxy** (Spearman ρ≈-0.3) 공식 문서화됨. 모든 UI/보고에서 disclaimer 의무
4. **HL 64.72 (var12)**: HEURISTIC ranking score. 임상 t½ 90min과 직접 비교 부적절. wet-lab 확인 필수
5. **ILCKKFFWKTFTSC**: selectivity 최강(T3)이지만 Instability 55.14 + HL ranking 최저 — 두 독립 모델 일관된 불안정 신호. K5→Orn + D-Phe6 필수
6. **step05b/05c selectivity_margin 부호 방향 충돌** — UI 혼용 방지 스펙 통일 필요 (Action A-4)
7. **HEURISTIC disclaimer UI 부착 미확인** — API/프론트엔드 `confidence_grade: HEURISTIC` 자동 주입 Action A-2
8. **§검증 필요 6건 신규 식별** (M5-P1~P6)

---

*Reviewer-pharma · 2026-05-13 · 39/39 guards PASS · 신뢰 등급 A/B/C/HEURISTIC 완료*
