# Stage 5 검증 보고서 — 약리학 환각 가드

> harness INTEGRATION_PLAN Stage 5 적용 결과.
> 작성: 2026-05-11
> 출처 디렉토리: `tools/harness-adaptation/`

---

## 1. 적용 범위

| 신설 | 경로 | 줄 |
|------|------|----|
| 가드 모듈 | `pipeline_local/scripts/pharmacology_guards.py` | 245 |
| 회귀 테스트 | `pipeline_local/tests/test_pharmacology_guards.py` | 271 |
| 테스트 패키지 | `pipeline_local/tests/__init__.py` | 0 |

**기존 코드 수정**: 없음 (안전 우선 — 기존 운영 코드는 손대지 않고 회귀 테스트로 보호).

---

## 2. 가드 분류

### 2-1. Anti-Hallucination 가드 (H-01~05 대응)

| 위험 | 가드 |
|------|------|
| H-01 파라미터 테이블 오기재 | `LITERATURE_VALUES` 정답 사전 + `assert_literature_value()` + `audit_table()` |
| H-02 부호 규약 역전 | `SIGN_CONVENTIONS` 사전 + `check_sign_convention()` |
| H-03 척도 혼용 | `SCALE_RANGES` 사전 + `assert_in_range()` |
| H-04 PyRosetta 채점 환각 | (별도 모듈 대상 — 본 Stage 범위 외) |
| H-05 반감기 참조 종 혼동 | `LITERATURE_VALUES["nend_half_life_mammalian_hours"]` (Varshavsky 1996 mammalian 명시) |

### 2-2. GATE-C 범위 가드

5개 척도 + 5개 출력에 대한 합리 범위 정의:
- `kyte_doolittle_per_residue`, `kyte_doolittle_mean`
- `boman_index_kcal_per_mol` (이론 max 14.92, all-R)
- `instability_index`, `n_end_half_life_hours`
- `predicted_half_life_hours` (≤1e4)
- `isoelectric_point`, `molecular_weight_peptide_da`
- `rosetta_total_score`, `hydrophobic_moment`

---

## 3. 테스트 실행 결과

```
============================== 33 passed in 0.12s ==============================
```

### 3-1. 회귀 보호 효과 (실제 라이브 검증)

- `KD_HYDROPATHY` 20 entries 모두 Kyte & Doolittle 1982 Table I과 일치 ✅
- `RW_TRANSFER` 10 핵심 entries 모두 Boman 2003 convention 일치 ✅
- `NEND_HALFLIFE["P"]` = 30.0 (Varshavsky 1996 mammalian), **20.0이 아님** ✅
  → 메모리(`feedback`)에 기록된 "Pro half-life=20.0 (정답 30.0)" 결함 부재 확인
- `PKA_SIDECHAIN` Lehninger pKa set 일치 ✅

### 3-2. 부호 규약 invariant 검증

- Kyte-Doolittle: `KD[I] > KD[R]` (소수성 > 친수성) ✅
- Boman convention: `RW[R] > RW[I]` (친수성 > 소수성 — 부호 뒤집힘) ✅

### 3-3. 출력 범위 검증 (SST-14 native 기준)

- `calculate_gravy("AGCKNFFWKTFTSC")` ∈ [-2.0, 3.0] ✅
- `calculate_boman_index(...)` ∈ [-5.0, 15.0] ✅
- `calculate_instability_index(...)` ∈ [0, 100] ✅
- `predict_half_life(...)` ∈ [0, 1e4] ✅

### 3-4. 발견된 가드 자체 결함 (즉시 수정)

테스트 작성 중 1건 가드 가설 오류 발견·수정:
- **초기 가설**: `boman_index_kcal_per_mol` 범위 = `[-5, +5]`
- **현실**: all-K 14mer = 5.55, all-R 14mer = 14.92 (이론 max)
- **수정**: 범위를 `[-5, +15]`로 보정 (pharmacology_guards.py:113)
- **의의**: 가드가 자체 가설의 부정확성을 검출한 사례 — GATE-C가 작동함을 입증

---

## 4. 알려진 historical defect 회귀 차단

본 회귀 테스트가 차단하는 과거 결함 (memory 출처):

| 결함 | 정답 | 회귀 테스트 |
|------|------|----------|
| `RW_TRANSFER["P"] = 0.0` | -2.54 (Boman convention) | `test_rw_transfer_boman_convention` |
| `RW_TRANSFER["S"] = 1.15` | 3.40 (Boman convention) | `test_rw_transfer_boman_convention` |
| `NEND_HALFLIFE["P"] = 20.0` (yeast 혼동) | 30.0 (mammalian, Varshavsky 1996) | `test_nend_half_life_pro_is_30_not_20` |

향후 누군가 위 값들을 무단 변경하면 CI 또는 로컬 `pytest`에서 즉시 차단됨.

---

## 5. Phase 6 트리거 쿼리 세트 (PROMPT_TEMPLATE.md 준수)

본 가드 모듈을 호출해야 하는 시나리오:

### should-trigger (8개)
1. "약리학 파라미터 테이블 변경 확인"
2. "Boman Index 부호가 맞는지 검증"
3. "Pro 반감기 정답 확인 (mammalian)"
4. "Kyte-Doolittle lookup table 무결성"
5. "predict_half_life 범위가 비현실적인지 확인"
6. "신규 변이체 약리학 평가 후 회귀 테스트"
7. "RW transfer free energy 부호 규약"
8. "instability index 범위 검사"

### should-NOT-trigger (8개, near-miss 포함)
1. "PyRosetta 도킹 점수 검증" → 별도 모듈 (`H-04`)
2. "ProteinMPNN 시퀀스 디자인 검증" → 약리학 아님
3. "BLOSUM62 매트릭스 검증" → 변이 생성 모듈
4. "ESM-2 임베딩 검증" → ML 모델 아웃풋
5. "RFdiffusion backbone 검증" → 구조 생성
6. "Boltz 도킹 결과 검증" → 별도
7. "UI 테마 변경 확인" → 무관
8. "CI 환경 설정" → 인프라

---

## 6. 후속 권장

본 Stage 5는 **수동 호출 가드**를 제공한다. 다음 단계 권장:

| 단계 | 작업 |
|------|------|
| 5a (현재) | 회귀 테스트 모듈 추가 ✅ 완료 |
| 5b | `pharma_properties.py` 함수 진입점에 `assert_in_range` 삽입 (출력 범위 자동 검사) |
| 5c | CI에 `pytest pipeline_local/tests/test_pharmacology_guards.py` 등록 |
| 5d | 새 약리학 척도 추가 시 LITERATURE_VALUES 등록 워크플로우 명문화 |
| 5e | `_PROTEASE_VULNERABILITY`(step08_stability.py L42-63) 휴리스틱 값들의 문헌 출처 보강 — 현재 출처 부재 (§검증 필요) |

---

## 7. §검증 필요

| ID | 항목 |
|----|------|
| VR-S5-01 | `step08_stability.py` `_PROTEASE_VULNERABILITY` 테이블 값들의 정량 문헌 출처 부재 — 현재 휴리스틱. 본 가드 모듈 회귀 대상에 포함되지 않음 |
| VR-S5-02 | `_DIWV_RAW` 400 entries 전수 회귀 안 함 — 핵심 dipeptide 10개 정도만 향후 보강 권장 |
| VR-S5-03 | `WIMLEY_WHITE`, `EISENBERG` 회귀 테스트 미작성 — 범위 가드만 적용 |

---

## 8. 변경 이력 (Phase 7)

| 날짜 | 변경 | 대상 | 사유 |
|------|------|------|------|
| 2026-05-11 | Stage 5 초기 적용 | `pipeline_local/scripts/pharmacology_guards.py`, `pipeline_local/tests/test_pharmacology_guards.py` | harness INTEGRATION_PLAN Stage 5 (Critical) — 약리학 lookup table 무단 변경 차단 |
| 2026-05-11 | boman_index 범위 보정 | `pharmacology_guards.py:113` | all-K 케이스 5.55가 가설 범위 초과. 이론 max(all-R)=14.92로 확장 |

---

**End of Stage 5 Validation Report.**
