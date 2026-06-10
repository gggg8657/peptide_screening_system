# P1 액션 아이템 통합 실행 결과 (2026-05-19)

> **작성**: reviewer-pharma  
> **팀**: p1-action-items (4 팀원: be-a04 / be-a01-cif / infra / reviewer-pharma)  
> **단계**: Step 2~6 완료 (Step 1은 다른 팀원 완료 후 통합 확인 예정)  
> **검증 기준**: `pharmacology_guards.py` Stage 5 절차 + H-06 가드 준수

---

## 1. 회귀 테스트 결과

```
pipeline_local/tests/test_pharmacology_guards.py — 55/55 PASS (0.16s)

기존: 39/39 → 신규 +16 = 55/55
회귀: 0건 (기존 39 전부 유지)
```

### 신규 테스트 클래스: `TestEndpointConfidenceExternalTools` (16개)

| 테스트 | 결과 | 검증 내용 |
|--------|------|-----------|
| test_halflife_pepmsnd_registered | ✅ PASS | PepMSND 등록 + AUC=0.912 |
| test_halflife_plifepred_registered | ✅ PASS | P2 등급 + R²≈0.552 |
| test_halflife_protparam_is_p4 | ✅ PASS | N-end rule → P4 강제 |
| test_halflife_hlp_is_p4_and_has_gi_warning | ✅ PASS | GI 전용 + '1.6초' 경고 |
| test_admet_pepadmet_is_p1 | ✅ PASS | P1 등급 + R²≥0.80 |
| test_admet_fab_is_unknown | ✅ PASS | 원출처 미식별 → UNKNOWN |
| test_hlp_d_amino_acid_support_is_false | ✅ PASS | D-AA 미지원 명시 |
| test_admet_fab_url_is_none_or_absent | ✅ PASS | url=None 강제 |
| test_no_internal_endpoint_grade_used_for_external_tools | ✅ PASS | A/B/C 혼용 금지 |
| test_pepmsnd_heuristic_disclaimer_registered | ✅ PASS | 이진 분류 한계 등록 |
| test_hlp_heuristic_disclaimer_is_intestinal_only | ✅ PASS | GI-only + 1.6초 |
| test_admet_pepadmet_heuristic_disclaimer_registered | ✅ PASS | DOTA OOD 가드 |
| test_c04_ss_bond_tools_cannot_assess_d_aa | ✅ PASS | C-04 D-AA 도구 부재 검증 |
| test_c07_dota_no_tool_supports_dota | ✅ PASS | C-07 DOTA 도구 부재 검증 |
| test_attach_confidence_external_halflife_pepmsnd | ✅ PASS | P3 등급 주입 |
| test_attach_confidence_admet_fab_unknown | ✅ PASS | UNKNOWN 등급 주입 |

---

## 2. ENDPOINT_CONFIDENCE 실 코드 등록 결과

### 2.1 혈청 반감기 도구 (6개)

| 키 | 등급 | 도구 | 핵심 근거 | team-lead 스펙 대비 |
|----|------|------|-----------|---------------------|
| `halflife_pepmsnd` | **P3** | PepMSND 2025 | 이진 분류, D-AA 미지원 (A-02 §3.7) | ⚠️ P1→P3 강등: 이진 분류 연속 t½ 아님 |
| `halflife_plifepred` | P2 | PlifePred | R²≈0.55, 혈중 직접 예측 (Mathur 2018) | 일치 |
| `halflife_ml_peptide` | P3 | ML_Peptide / PlifePred2 | peer-review 검증 미확보 (A-02 §3.4) | 일치 |
| `halflife_protparam` | **P4** | ProtParam (ExPASy) | 세포 내 N-end rule, 혈청 불일치 (A-02 §3.1) | ⚠️ P3→P4 강등: 메커니즘 완전 불일치 |
| `halflife_hlp` | P4 | HLP | 장내(GI) 전용, 혈청 절대 금지 (A-02 §3.2) | 일치 |
| `halflife_peptiderranker` | P4 | PeptideRanker | 생물활성 순위 전용, 반감기 부적합 | 일치 |

> **등급 강등 사유 (reviewer-pharma 판정)**:
> - `halflife_pepmsnd` P1→P3: A-02 연구 결과, PepMSND는 binary classifier (stable/unstable 등급) 출력. 연속 t½ 값 없음. TPP KPI(≥24h, ≥72h) 직접 판정 불가. D-AA 웹 인터페이스 미지원. team-lead 스펙 P1은 A-02 결과 이전 초안 기준. (근거: Wang 2025 Digital Discovery DOI:10.1039/D5DD00118H)
> - `halflife_protparam` P3→P4: N-end rule은 세포 내(intracellular) 반감기 메커니즘. 혈청 t½와 전혀 다름. SST-14 ProtParam 예측 ~30h (intracellular) vs 실측 ~3분 (serum) — 완전 불일치. (근거: A-02 §3.1; Gasteiger 2005)

### 2.2 ADMET 도구 (3개)

| 키 | 등급 | 도구 | 핵심 근거 |
|----|------|------|-----------|
| `admet_pepadmet` | P1 | pepADMET 2026 | R²=0.84~0.90 (human blood), 29 endpoints (A-03; JCIM 2025) |
| `admet_ai` | P2 | ADMET-AI (MIT) | 소분자 중심, 펩타이드 적용 신뢰도 감점 (A-03 §표1) |
| `admet_fab` | **UNKNOWN** | Fab-ADMET | 학술 DB·GitHub·GitLab 어디서도 미확인 (A-03 §핵심 발견) |

---

## 3. HEURISTIC_FUNCTION_DISCLAIMERS 신규 등록 (3개)

| qualname | actual_meaning | 신규 등록 내용 |
|----------|----------------|----------------|
| `external_tool.halflife_pepmsnd` | 혈중 안정성 이진 분류 | 연속 t½ 오용 방지, D-AA 미지원 명세 |
| `external_tool.admet_pepadmet` | 29 ADMET endpoint ML 예측 | DOTA OOD, D-AA 미확인, web-only 한계 |
| `external_tool.halflife_hlp` | 장내(GI) 환경 반감기 | 혈청 절대 금지, '1.6초' 오적용 traceback |

모든 신규 항목: `confidence_grade = "HEURISTIC"` ✅

---

## 4. modification_conflict_rules C-04/C-07 검증

### C-04 (D-Cys → Cys3-Cys14 SS bond 손상)

**검증 결과: C-04 ERROR 보수적 적용 정당화 확인**

현재 등록된 혈청 반감기 도구 전체 (`halflife_*`) 중 `d_amino_acid_support = True`인 도구 **0개**.

| 도구 | d_amino_acid_support |
|------|---------------------|
| halflife_pepmsnd | False (웹 인터페이스 natural AA 전용) |
| halflife_plifepred | False (natural 서열만) |
| halflife_ml_peptide | False (flag-based only) |
| halflife_protparam | False (L-AA 표준 서열만) |
| halflife_hlp | False (표준 AA 기반) |
| halflife_peptiderranker | False |

→ **D-Cys 치환 후보의 혈청 반감기를 in-silico로 평가할 수 있는 도구 없음.** C-04 ERROR는 보수적이나 정당한 가드.

### C-07 (DOTA stoichiometry)

**검증 결과: C-07 ERROR 보수적 적용 정당화 확인**

현재 등록된 ADMET 도구 전체 (`admet_*`) 중 `dota_support = True`인 도구 **0개**.

| 도구 | dota_support |
|------|-------------|
| admet_pepadmet | False (OOD 예상) |
| admet_ai | False (소분자 중심) |
| admet_fab | None (원출처 미식별) |

→ **DOTA-결합 펩타이드의 ADMET를 in-silico로 평가할 수 있는 도구 없음.** C-07 ERROR(DOTA 단일 stoichiometry 강제)는 정당한 보수적 가드.

---

## 5. 등급 강등 PASS/FAIL 매트릭스

| 항목 | 기준 | 실제 | 판정 | 근거 |
|------|------|------|------|------|
| PepMSND 연속 t½ 출력 | False | False | ✅ PASS | 이진 분류 모델 (Wang 2025) |
| PepMSND AUC | =0.912 | 0.912 | ✅ PASS | 원논문 일치 |
| PlifePred R² | ~0.55 | 0.552 | ✅ PASS | R=0.743 → R²=0.552 |
| pepADMET R² (human blood) | ≥0.80 | 0.84 | ✅ PASS | pepADMET JCIM 2025 |
| ProtParam 메커니즘 | intracellular | intracellular | ✅ PASS | N-end rule 확인 |
| HLP 환경 | intestinal | GI | ✅ PASS | Sharma 2014 BMC Bioinformatics |
| Fab-ADMET 원출처 | 학술 DB 확인 | 미확인 | ⚠️ UNKNOWN | A-03 §핵심 발견 |

---

## 6. 부호 규약 일관성

신규 등록 외부 도구 엔트리에 부호 규약 검사 필요 수치 없음 (등급·불리언·R² 수치만).  
기존 부호 규약 테스트 (`TestPharmaPropertiesSignConventions`) 2/2 회귀 이상 없음 ✅

---

## 7. 출처 카운트

| 카테고리 | 총 항목 | 출처 있음 | 비율 |
|----------|---------|-----------|------|
| halflife 도구 6개 | 6 | 6 (모두 "source" 키 포함) | 100% |
| admet 도구 3개 | 3 | 3 (admet_fab는 'A-03 연구' 명시) | 100% |
| HEURISTIC disclaimer 3개 | 3 | 3 | 100% |
| **합계** | **12** | **12** | **100% ≥ 80%** ✅ |

---

## 8. 5월 회의 안건 갱신

### 안건 1 — HLP '1.6초' 재해석 완료 [결과 보고]
- **내용**: 2026-04-06 회의록 기재 'SST-14 HLP 예측 ~1.6초'는 장내(GI) 환경 도구를 혈청에 잘못 적용한 결과. 혈청 반감기 예측치가 아님.
- **근거**: A-02 §3.2 (Sharma 2014 BMC Bioinformatics — 장내 유사 환경 SVM 모델)
- **조치**: `halflife_hlp` P4 등록 + 경고 명세 + HEURISTIC disclaimer `external_tool.halflife_hlp` 등록

### 안건 2 — Fab-ADMET 원출처 확인 [RI팀 안건]
- **내용**: 회의록 기재 'Fab-ADMET' 도구가 학술 DB·GitHub·GitLab 어디서도 확인 불가 (A-03).
- **유력 후보**: FP-ADMET (Venkatraman 2021 J Cheminform 13:56) — 발음 유사 오기재 가능성
- **확인 필요**: RI팀 서호성 박사에게 원래 어떤 도구를 사용했는지 확인
- **현 조치**: `admet_fab` UNKNOWN 등록. 확인 전 수치 인용 금지.

### 안건 3 — pepADMET D-AA 지원 여부 실 테스트 [P1 tool 검증]
- **내용**: pepADMET(P1)의 D-아미노산 처리 능력이 문서에 미명시 (§검증 필요 V-03)
- **제안**: Octreotide (D-Phe, D-Trp) 서열 직접 웹 입력 테스트
- **담당**: reviewer-chemistry + engineer-infra
- **기간**: 1주

### 안건 4 — composite_scorer A-04 완료 시점 A-09 트리거 [일정 결정]
- **내용**: A-04 composite_scorer 완료 후 A-09(최종 후보 3-4개 도출 + 합성 의뢰서) 트리거
- **현재 상태**: A-04 in_progress (be-a04 팀원 진행 중)
- **제안**: A-04 완료 후 동일 세션에서 A-09 reviewer-pharma + orchestrator 공동 실행

### 안건 5 — A-07 GPU 견적 결정 [인프라]
- **내용**: engineer-infra GPU 견적 보고서 완료 예정. 다음 wet-lab 발주 전 인프라 결정 필요.
- **관련**: 자체 ML 모델 학습(D-AA 반감기 predictor) 시 GPU 리소스 필요 (A-02 §6.3)

---

## 9. §검증 필요

| # | 항목 | 우선순위 | 담당 |
|---|------|----------|------|
| V-01 | **Fab-ADMET 원출처** 회의록 PDF 원본 표기 확인 | HIGH | 사용자/RI팀 |
| V-02 | pepADMET 논문 전문 접근 (DOI paywall) | HIGH | reviewer-pharma |
| V-03 | **pepADMET D-AA 처리** — Octreotide SMILES 실 테스트 | HIGH | reviewer-chemistry |
| V-04 | PepMSND API/로컬 버전 존재 여부 확인 (D-AA flag 방식 지원?) | MED | engineer-infra |
| V-05 | PlifePred2 peer-review 독립 벤치마크 확보 → P3→P2 상향 검토 | MED | researcher |
| V-06 | pepADMET API 접근 가능성 + 자동화 통합 경로 | MED | engineer-infra |

---

## 10. 다음 sprint 권고

### 즉시 (이번 세션)
1. be-a04, be-a01-cif, infra 팀원 완료 알림 수신 후 통합 커밋 진행
2. V-01 Fab-ADMET 확인을 5월 회의 안건으로 정식 등록

### 단기 (1~2주)
1. **V-03 pepADMET D-AA 테스트** — P1 도구 검증 완료
2. **V-05 PlifePred2 검증** — P3→P2 상향 시 파이프라인 1차 통합 가능
3. **A-04 완료 후 A-09** — 최종 후보 도출 + 합성 의뢰서

### 중기 (1~3개월)
1. **D-AA 반감기 자체 ML 모델** 착수 (PEPlife2 데이터 + Tan 2024 방법론) — A-02 §6 로드맵
2. **wet-lab serum stability assay** 발주 — SST-14 + 합의 후보 3종 + Octreotide(대조)

---

## 11. 변경 파일 요약

| 파일 | 변경 내용 |
|------|-----------|
| `pipeline_local/scripts/pharmacology_guards.py` | ENDPOINT_CONFIDENCE: 9개 외부 도구 등록; HEURISTIC_FUNCTION_DISCLAIMERS: 3개 추가; attach_confidence: "warning" 단수 키 호환 추가 |
| `pipeline_local/tests/test_pharmacology_guards.py` | TestEndpointConfidenceExternalTools: 16개 신규 테스트; ENDPOINT_CONFIDENCE/attach_confidence import 추가 |

**테스트 결과**: 55/55 PASS (기존 39 → +16, 회귀 0건)  
**커밋 금지** — 이 변경은 team-lead 통합 커밋 대기.
