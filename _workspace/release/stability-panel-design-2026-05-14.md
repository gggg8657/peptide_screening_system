# Stability Panel Design + pepADMET Data Note — 2026-05-14

## 목적

현재 `hl_score_heuristic` 단일 점수 중심의 안정성 출력을, **독립 surrogate들의 병렬 출력 구조**로 확장한다. 또한 `pepADMET`의 half-life 학습데이터 규모와 한계를 정리해, 이후 외부 모델 도입 우선순위와 충돌 체크 기준을 명확히 한다.

---

## 1. 결론

1. **네, JSON에 추가하는 방식이 맞다.**
   - 기존 flat 필드는 유지하고,
   - 새 nested block인 `surrogate_panel`과 `agreement_profile`을 sidecar로 추가하는 것이 가장 안전하다.

2. **단일 half-life 숫자로 합치지 않는다.**
   - `hl_score_heuristic`, protease site burden, biophysical descriptors, ADMET 결과는 서로 단위와 의미가 다르다.
   - 따라서 평균/가중합으로 `predicted_half_life_hours` 같은 값을 만들면 해석 오류가 커진다.

3. **실제 운영 명칭은 `ensemble predictor`가 아니라 `multi-surrogate stability panel`이 맞다.**
   - 서로 다른 근거를 나란히 제시하고,
   - `agreement_profile`은 해석 보조 레이어로만 사용한다.

4. **pepADMET half-life는 유망하지만 학습데이터 자체는 크지 않다.**
   - 공식 문서 기준 half-life fine-tune 데이터는 **970 records**다.
   - 대신 **350,000-entry retention-time pretraining**을 사용한다.
   - 즉, “half-life 자체의 직접 학습셋이 충분히 크다”기보다는, **데이터 부족을 transfer learning으로 보완하는 구조**로 보는 것이 정확하다.

---

## 2. JSON 확장 포인트

현재 결과 스키마는 아래 두 위치가 기준이다.

- [pipeline_local/scripts/stability_predictor/__init__.py](/home/dongjukim/Documents/workspace/repos/SST14-M_scr/pipeline_local/scripts/stability_predictor/__init__.py)
  - `StabilityResult`
  - `BatchStabilityResult.summary`
  - `compute_stability()`
- [AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/stability.py](/home/dongjukim/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/stability.py)
  - `StabilityResponse`

권장 원칙:
- 기존 flat 필드는 유지
- 새 결과는 nested JSON block으로 추가
- API와 batch json이 같은 키 셋을 유지

이번 변경에서 실제로 추가한 필드:
- `surrogate_panel`
- `agreement_profile`
- batch summary의 `surrogate_panel_summary`

---

## 3. 현재 적용된 스키마

### 3.1 단일 후보 결과

```json
{
  "seq_id": "cand03",
  "sequence": "AICKNFFWKTFTSC",
  "canonical_sequence": "AICKNFFWKTFTSC",
  "mw": 1617.8,
  "gravy": -0.48,
  "instability_index": 32.5,
  "pi": 8.2,
  "boman": 1.2,
  "charge_ph74": 1.7,
  "aliphatic_index": 7.1,
  "protease_cleavage_sites": {"trypsin": [4, 9], "chymotrypsin": [6, 7, 8, 11], "nep": [1, 6]},
  "admet_score": {...},
  "nephrotox_risk": "Low",
  "hl_score_heuristic": 42.0,
  "hl_warnings": [...],
  "ncaa_warnings": [],
  "is_unstable": false,
  "stability_class": "stable",
  "surrogate_panel": {
    "tool_availability": {
      "biopython": true,
      "peptides_py": true,
      "backend_admet": true,
      "step08_half_life": true
    },
    "input_normalization": {
      "original_sequence": "AICKNFFWKTFTSC",
      "canonical_sequence": "AICKNFFWKTFTSC",
      "modifications": ["cyclization"],
      "ncaa_warnings": []
    },
    "biophysical": {
      "mw": 1617.8,
      "gravy": -0.48,
      "instability_index": 32.5,
      "pi": 8.2,
      "boman": 1.2,
      "charge_ph74": 1.7,
      "aliphatic_index": 7.1
    },
    "protease": {
      "cleavage_sites": {"trypsin": [4, 9], "chymotrypsin": [6, 7, 8, 11], "nep": [1, 6]},
      "site_counts": {"trypsin": 2, "chymotrypsin": 4, "nep": 2},
      "total_sites": 8
    },
    "admet": {
      "score": {...},
      "nephrotox_risk": "Low"
    },
    "half_life": {
      "internal_step08": {
        "available": true,
        "score": 42.0,
        "score_kind": "heuristic_ranking",
        "warnings": [...]
      }
    }
  },
  "agreement_profile": {
    "biophysical_class": "stable",
    "protease_burden": "high",
    "admet_signal": "low",
    "half_life_signal": "supportive",
    "consensus_bucket": "mixed",
    "flags": ["biophysical_vs_protease_disagreement"]
  }
}
```

### 3.2 batch summary

```json
{
  "summary": {
    "n_total": 8,
    "n_stable_biopython": 6,
    "mean_mw": 1604.22,
    "mean_gravy": -0.37,
    "mean_instability": 31.02,
    "mean_hl_score": 41.85,
    "heuristic_disclaimer": "hl_score_heuristic은 임상 반감기 절대값이 아닌 ranking score임",
    "surrogate_panel_summary": {
      "consensus_bucket_counts": {
        "stable_supportive": 2,
        "mixed": 5,
        "unstable_risk": 1
      },
      "tools_present": {
        "biopython": true,
        "peptides_py": true,
        "backend_admet": true,
        "step08_half_life": true
      }
    }
  }
}
```

---

## 4. agreement 로직 초안

현재는 **경량 규칙 기반**으로만 넣는다.

입력 축:
- biophysical: `instability_index`
- protease: `total_sites`
- ADMET: `nephrotox_risk`
- half-life surrogate: `hl_score_heuristic > 0`

현재 규칙:
- `biophysical_class`
  - `stable`: instability index <= 40
  - `unstable`: instability index > 40
  - `unknown`: NaN
- `protease_burden`
  - `low`: total sites <= 2
  - `moderate`: 3-5
  - `high`: >= 6
- `consensus_bucket`
  - `stable_supportive`: stable + low burden + half-life positive
  - `unstable_risk`: unstable + high burden
  - `mixed`: 나머지
- `flags`
  - `biophysical_vs_protease_disagreement`
  - `instability_vs_half_life_disagreement`
  - `nephrotox_high_risk`
  - `half_life_signal_missing`

중요:
- 이 값들은 **새 half-life 예측값이 아니다**.
- 단지 서로 다른 surrogate가 같은 방향을 가리키는지 요약하는 레이어다.

---

## 5. 왜 이 구조가 맞는가

### 5.1 장점

- 기존 flat API를 깨지 않는다.
- 나중에 `PlifePred2`, `PepFun2`, `PepFuNN`, `peptides.py`를 붙여도 schema를 유지할 수 있다.
- 서로 다른 도구를 같은 단위로 강제하지 않는다.
- downstream UI/대시보드에서 `agreement_profile.flags`만 따로 강조할 수 있다.

### 5.2 피해야 할 구조

피해야 할 안:
- `predicted_half_life_hours`
- `ensemble_half_life_score`
- `surrogate_average`

이유:
- protease cleavage burden, descriptor score, heuristic ranking, 외부 ML predictor는 **같은 target/단위**를 공유하지 않는다.

---

## 6. pepADMET 학습데이터 조사

### 6.1 확인된 사실

공식 pepADMET 문서/사이트 기준:
- 전체 플랫폼 규모: **36,643 entries**
- 현재 서비스 범위: **29 endpoints**
- half-life fine-tune 데이터: **970 peptide half-life records**
- half-life data source: **PEPlife, PepTherDia, THPdb, public publications**
- half-life dataset split: **727 train / 243 test**
- half-life task 분할: **5 datasets**
  - HBN: human blood natural
  - HBM: human blood modified
  - MBN: mouse blood natural
  - MBM: mouse blood modified
  - MIM: mouse intestine modified
- half-life model 강화 전략: **350,000-entry retention-time dataset pretraining + fine-tuning**

### 6.2 “학습 데이터를 더 모아야 한다”는 해석이 맞는가

**대체로 맞다.** 다만 표현을 정확히 해야 한다.

정확한 표현:
- `pepADMET half-life는 충분히 큰 전용 half-life 데이터셋으로 학습됐다` 는 말은 과장이다.
- 더 정확한 설명은:
  - `half-life 직접 데이터는 970건으로 제한적이며, 이를 보완하기 위해 350K retention-time pretraining을 사용한다.`

즉, 공식 설계 자체가 **half-life supervised data scarcity**를 전제로 한다고 해석하는 편이 타당하다.

### 6.3 프로젝트에 주는 시사점

- `pepADMET half-life`는 참고할 가치가 있다.
- 그러나 modified SST-14 analog의 정량 blood half-life를 단독으로 확정하는 근거로는 부족하다.
- 특히 D-AA, Orn, DOTA, PEG 같은 변경이 들어가면 domain shift 가능성을 계속 경고해야 한다.

---

## 7. 도입 우선순위

1. **현재 sidecar schema 유지**
   - 내부 surrogate 먼저 안정화

2. **`PlifePred2` 추가 검증**
   - 역할: blood half-life에 가장 가까운 외부 predictor
   - 추가 위치: `surrogate_panel.half_life.plifepred2`

3. **`peptides.py` / BioPython 값 보강**
   - 이미 일부 쓰고 있으므로 환경 안정화가 우선
   - 추가 위치: `surrogate_panel.biophysical`

4. **`PepFun2` 또는 `PepFuNN` 중 하나**
   - 역할: modified peptide representation / similarity / library-space 분석
   - 추가 위치:
     - `surrogate_panel.modified_representation.pepfun2`
     - 또는 `surrogate_panel.library_space.pepfunn`

5. **`pepADMET` 외부/별도 env 연동**
   - 역할: 더 넓은 ADMET 및 half-life 보조
   - 추가 위치: `surrogate_panel.admet.pepadmet`

---

## 8. 충돌 체크리스트

### 8.1 의미 충돌

- `hl_score_heuristic`를 실제 half-life로 오해하지 않도록 유지했는가
- 외부 ML predictor를 넣더라도 기존 heuristic과 이름을 분리했는가

### 8.2 입력 충돌

- natural sequence만 받는 모델인가
- modification site metadata를 따로 받는가
- NCAA를 canonicalization하면 의미 손실이 생기는가

### 8.3 운영 충돌

- 별도 conda env가 필요한가
- 네트워크/웹 API 의존성이 있는가
- 배치 처리량과 timeout을 감당하는가

### 8.4 해석 충돌

- 서로 다른 출력 단위를 억지로 평균내고 있지 않은가
- disagreement case를 별도 flag로 남기고 있는가
- wet-lab prior를 덮어쓰지 않고 triage 용도로만 쓰고 있는가

---

## 9. 다음 실무 단계

1. `PlifePred2` 설치 가능 환경에서 cand03/SST-14/D-Phe/Orn 입력 스모크 테스트
2. `pepADMET` half-life endpoint 접근 가능 여부와 입력 제약 확인
3. `PepFun2` 또는 `PepFuNN` 중 하나를 골라 modified-peptide similarity axis 추가
4. UI에서 `surrogate_panel` collapse view와 `agreement_profile.flags` 강조 표시 추가

---

## 참고 출처

- pepADMET 공식 문서: https://pepadmet.ddai.tech/documentation/
- pepADMET 홈: https://pepadmet.ddai.tech/
- pepADMET half-life 입력 페이지: https://pepadmet.ddai.tech/calcpep/half-life/
- JCIM 논문: https://pubs.acs.org/doi/10.1021/acs.jcim.5c02518
