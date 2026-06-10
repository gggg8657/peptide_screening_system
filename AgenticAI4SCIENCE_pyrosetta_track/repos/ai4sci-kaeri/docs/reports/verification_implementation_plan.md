# 검증 + 구현 이슈 전수 실행 계획

**작성일**: 2026-04-07
**근거**: 3건의 코드 분석 보고서 (pharma, admet_cluster, selectivity_scoring)
**목적**: 모든 이슈를 빠짐없이 추출하고 실행 순서를 확정

---

## 이슈 전체 목록 (ID 부여)

| ID | 분류 | 출처 보고서 | 파일 | 이슈 | 심각도 |
|----|------|------------|------|------|--------|
| V-01 | 검증 | pharma | `AG_src/pipeline/pharma_properties.py` L45 | RW S(Ser) = 3.40 vs 문헌 1.83 불일치 가능 | High |
| V-02 | 검증 | admet_cluster | `pyrosetta_flow/pepadmet_infer_script.py` L36 | `sorted(fp.items())` 알파벳 순서 — 학습 시 feature 순서 일치 보장 불명확 | High |
| V-03 | 검증 | admet_cluster | `backend/admet.py` L155 | Docstring "DOTATATE score ~25 (Low)" vs 실제 계산값 35 (Moderate) 불일치 | High |
| I-01 | 구현 | selectivity | `AG_src/pipeline/step05b_selectivity.py` L406-428 | `apply_selectivity_gate()`가 `r.passed`만 사용 — 파라미터 재적용 불일치 (이중 gate) | High |
| I-02 | 구현 | selectivity | `pyrosetta_flow/pareto_ranking.py` L148-188 | `pareto_rank_candidates()` dict in-place 수정 — 원본 데이터 변조 위험 | High |
| I-03 | 구현 | selectivity | `pyrosetta_flow/smiles_converter.py` L87-89 | SS bond 형성 실패 시 조용히 선형 SMILES 반환 — 호출자 감지 불가 | Medium |
| I-04 | 구현 | admet_cluster | `backend/admet.py` L53-69 | `n_hbd` Pro backbone NH 과대계산 (Pro는 backbone NH 없음) | Medium |
| I-05 | 구현 | admet_cluster | `backend/admet.py` L89-105 | `amphipathicity_index` = KD 분산 — Eisenberg 소수성 모멘트(벡터합)와 명칭 불일치 | Medium |
| I-06 | 구현 | admet_cluster | `backend/admet.py` L150-228 | His가 `cationic_residues`에 포함되나 `renal_risk_score` 공식에서 제외 | Medium |
| I-07 | 구현 | pharma | `AG_src/pipeline/pharma_properties.py` L510-533 | DPP-IV 모든 내부 X-P/X-A 탐지 — N말단 2번째 위치 전용 규칙 부재 | Medium |
| I-08 | 구현 | selectivity | `AG_src/pipeline/step05b_selectivity.py` L132-133 | tempfile.NamedTemporaryFile(delete=False) 잔류 파일 미정리 | Medium |
| I-09 | 구현 | admet_cluster | `backend/admet.py` L109-136 | `druglikeness_score` 명칭이 Lipinski와 무관한 in-house 4규칙에 부적절 | Low |
| I-10 | 구현 | admet_cluster | `pyrosetta_flow/pepadmet_infer_script.py` | linear fallback 시 SS/cycle 소실 — `graph_note` downstream 미필터링 | Low |
| I-11 | 구현 | admet_cluster | `pyrosetta_flow/pepadmet_infer_script.py` | HC50 출력 단위 미명시 (μg/mL 추정) | Low |
| I-12 | 구현 | admet_cluster | `pyrosetta_flow/pepadmet_runner.py` | subprocess timeout=120초 고정 — 대용량 배치 위험 | Low |
| I-13 | 구현 | selectivity | `pyrosetta_flow/bayesian_optimizer.py` L496-530 | docstring "qNEHVI" vs 실제 product-of-improvements proxy — 명칭 불일치 | Low |
| I-14 | 구현 | selectivity | `AG_src/pipeline/step05b_selectivity.py` | `SelectivityResult.offtarget_max_score` 필드명이 의미를 역으로 암시 | Low |
| I-15 | 구현 | selectivity | `AG_src/pipeline/step05b_selectivity.py` | `_run_offtarget_pyrosetta()` out_pdb 생성 후 미사용 및 미정리 | Low |
| I-16 | 구현 | selectivity | `pyrosetta_flow/gnina_rescoring.py` | ECR tie 처리 없음, score_keys 수 변화 시 절대값 비교 불가 | Low |
| I-17 | 구현 | selectivity | `AG_src/pipeline/step05b_selectivity.py` | `_convert_cif_to_pdb()` QUIET=True 경고 억제 | Low |
| I-18 | 구현 | admet_cluster | `pyrosetta_flow/cluster_report.py` | `pLDDT_available` all() 포함 설계 의도 주석 부재 | Low |
| I-19 | 구현 | admet_cluster | `pyrosetta_flow/cluster_report.py` | `selectivity_margin` 필드 생성 위치 명시 없음 → 누락 시 B 자동 탈락 | Low |
| I-20 | 구현 | pharma | `AG_src/pipeline/pharma_properties.py` | 단일동위원소 MW: 경험적 0.9994 스케일링 — 정밀 MS 비교 시 부족 | Low |

---

## 각 이슈 상세

### V-01: RW S(Ser) 값 검증
**파일**: `AG_src/pipeline/pharma_properties.py` L45
**현재 코드**: `"S": 3.40`
**문제**: Radzicka & Wolfenden 1988 물→사이클로헥산 전이 자유에너지 테이블에서 S(Ser)가 다수 2차 인용에서 1.83으로 보고됨. 3.40은 물→기상(gas phase) 전이 조건에 해당할 수 있음. 이전 세션에서 peptides 패키지 GT 대조로 3.40으로 수정한 이력이 있어 교차 검증 필요.
**해결**: (1) Radzicka & Wolfenden 1988 Table 1 원본 확인, (2) Boman 2003 Table 1 대조, (3) peptides R 패키지 `boman()` 결과 역산 비교
**예상 소요**: 30분 (문헌 검색 + 계산 대조)
**테스트**: SST-14에 대해 `peptides::boman("AGCKNFFWKTFTSC")` 결과와 코드 출력 비교
**의존성**: 없음

---

### V-02: pepADMET descriptor 정렬 순서 검증
**파일**: `pyrosetta_flow/pepadmet_infer_script.py` L36
**현재 코드**: `sorted(fp.items())` — Python dict의 알파벳 순 key 정렬
**문제**: pepADMET 원본 학습 코드(`calculate_descriptors`)가 동일 정렬 순서를 사용하는지 검증 필요. 순서 불일치 시 모든 독성 예측이 무의미해짐.
**해결**: (1) pepADMET GitHub 원본 `calculate_descriptors.py` + 학습 스크립트 코드 확인, (2) 원본 inference 코드의 descriptor 순서 비교
**예상 소요**: 1시간 (원본 코드 분석)
**테스트**: 알려진 펩타이드(SST-14)로 원본 pepADMET과 우리 코드의 descriptor tensor 비교
**의존성**: 없음

---

### V-03: nephrotox DOTATATE docstring 불일치 검증
**파일**: `backend/admet.py` L155
**현재 docstring**: `"DOTATATE has 1 Lys, charge ~+1, renal_risk_score ~25 (Low)"`
**실제 계산**: DOTATATE → n_lys=1, n_arg=0, net_charge≈+1 → score = (1+0)×20 + max(0,1)×15 = 35 → **Moderate** (Low가 아님)
**해결**: docstring을 실제 계산값(35, Moderate)으로 수정
**예상 소요**: 10분
**테스트**: `compute_nephrotox_risk("DOTATATE_SEQ")` 단위 테스트 추가
**의존성**: 없음

---

### I-01: selectivity gate 이중 파라미터 불일치
**파일**: `AG_src/pipeline/step05b_selectivity.py` L406-428
**현재 코드**: `apply_selectivity_gate(results, margin_min, offtarget_max)`는 `margin_min`, `offtarget_max` 파라미터를 받지만 실제로는 `r.passed`만 확인. `r.passed`는 이미 `compute_selectivity_margin()`에서 계산됨.
**문제**: `apply_selectivity_gate()`에 다른 threshold를 전달해도 결과가 변하지 않음. 호출자가 파라미터가 반영된다고 착각할 위험.
**해결 옵션**:
  - (A) `apply_selectivity_gate()`에서 파라미터를 제거하고 `r.passed`만 사용 (현재 동작 명시화)
  - (B) `apply_selectivity_gate()`에서 실제로 재계산: `r.margin <= margin_min and r.offtarget_max_score >= offtarget_max`
  - **권장**: (B) — 유연성 확보. 단, `compute_selectivity_margin()`의 `passed` 필드는 기본 gate로 유지
**예상 소요**: 30분
**테스트**: 서로 다른 threshold로 gate 적용 시 결과가 달라지는지 검증하는 단위 테스트
**의존성**: 없음

---

### I-02: pareto_rank_candidates() in-place 수정
**파일**: `pyrosetta_flow/pareto_ranking.py` L148, L187-188
**현재 코드**: `candidates[global_idx]["pareto_rank"] = rank` — 입력 dict를 직접 수정
**문제**: 호출자의 원본 데이터가 의도치 않게 변조됨. 여러 ranking 전략을 비교할 때 원본 보존 불가.
**해결**: `copy.deepcopy(candidates)` 후 수정하여 반환. docstring의 "same dicts, mutated in-place" 문구도 변경.
**예상 소요**: 20분
**테스트**: 원본 dict에 `pareto_rank` 키가 추가되지 않는지 검증
**의존성**: 없음

---

### I-03: smiles_converter SS bond 실패 시 silent fallback
**파일**: `pyrosetta_flow/smiles_converter.py` L87-89
**현재 코드**: SS bond 형성 실패 시 `except Exception` → 선형 SMILES 반환 (경고/플래그 없음)
**문제**: 호출자(pepadmet_runner 등)가 SS bond 포함 여부를 알 수 없음 → 독성 예측 정확도 저하
**해결**: 반환값을 `(smiles, ss_bond_formed: bool)` 튜플로 변경하거나, 선형 fallback 시 로그 경고 추가
**예상 소요**: 30분
**테스트**: SS bond 형성 불가 시퀀스(단일 Cys)에서 반환값 검증
**의존성**: I-10 (pepadmet graph_note 필터링)과 연관

---

### I-04: n_hbd Pro backbone NH 과대계산
**파일**: `backend/admet.py` ~L53-69
**현재 코드**: `n_hbd += length` — Pro 포함 전체 잔기에 backbone NH 1개씩 가산
**문제**: Pro(Proline)는 이미노산으로 backbone NH가 없음 → 과대계산
**해결**: `n_hbd += length - seq.count("P")` 또는 Pro 위치 제외
**예상 소요**: 15분
**테스트**: Pro 포함 서열("PPPP" 등)에서 n_hbd 검증
**의존성**: 없음

---

### I-05: amphipathicity_index 명칭 불일치
**파일**: `backend/admet.py` ~L89-105
**현재 코드**: `amphipathicity_index = Var(KD)` (KD 분산)
**문제**: Eisenberg 소수성 모멘트(helical wheel 벡터합)와 전혀 다른 계산인데 `amphipathicity` 명칭 사용. `pharma_properties.py`에는 정확한 Eisenberg 구현이 별도 존재.
**해결 옵션**:
  - (A) 필드명을 `kd_variance`로 변경 (downstream API 영향 검토 필요)
  - (B) 주석에 "KD 분산이며 Eisenberg 소수성 모멘트 아님" 명시
  - **권장**: (A) + 마이그레이션 경고
**예상 소요**: 30분 (downstream 영향 분석 포함)
**테스트**: 기존 테스트가 필드명 변경 후에도 통과하는지 확인
**의존성**: 없음

---

### I-06: nephrotox His 공식 제외 불일치
**파일**: `backend/admet.py` L188-192
**현재 코드**: `renal_risk_score = (n_lys + n_arg) * 20 + max(0, net_charge) * 15`
**문제**: `n_his`를 `cationic_residues` 필드에 보고하면서 공식에서는 제외. pH 7.4에서 His protonation ~4%이므로 제외가 합리적이나, 필드와 공식 간 불일치가 혼란 유발.
**해결**: docstring에 His 제외 근거 명시 ("His pKa 6.0, pH 7.4에서 ~4% protonation → 임상적으로 무시 가능")
**예상 소요**: 10분
**테스트**: 기존 테스트 확인
**의존성**: V-03과 동일 파일

---

### I-07: DPP-IV 특이성 범위 일반화
**파일**: `AG_src/pipeline/pharma_properties.py` L510-533
**현재 코드**: 모든 내부 위치에서 X-Pro/X-Ala 부위 탐지
**문제**: 표준 DPP-IV는 N말단 2번째 위치에 특이적. 현재 구현은 보수적(더 많이 탐지) 접근이며 스크리닝 목적에는 실용적이나, 엄밀한 DPP-IV 특이성이 아님.
**해결**: (1) 기존 `dppiv` 필드는 유지(광의 스크리닝), (2) `dppiv_nterm` 필드 추가(N말단 위치2 전용), (3) 주석에 차이 명시
**예상 소요**: 20분
**테스트**: N말단 X-P 서열에서 `dppiv_nterm` 검증
**의존성**: 없음

---

### I-08: tempfile 잔류 파일 미정리
**파일**: `AG_src/pipeline/step05b_selectivity.py` (`load_offtarget_receptors_from_config`)
**현재 코드**: `tempfile.NamedTemporaryFile(delete=False)` → CIF→PDB 변환 후 파일 잔류
**문제**: 장기 실행 시 임시 파일 누적
**해결**: `atexit.register`로 정리 등록 또는 `tempfile.TemporaryDirectory` 사용
**예상 소요**: 20분
**테스트**: 함수 호출 후 임시 파일 존재 여부 확인
**의존성**: 없음

---

### I-09: druglikeness_score 명칭 부적절
**파일**: `backend/admet.py` L109-136
**문제**: "druglikeness"가 Lipinski Rule과 무관한 in-house 4규칙(MW, charge, hydrophobicity, repeats)에 사용됨
**해결**: `peptide_quality_score` 등으로 명칭 변경 + docstring에 Lipinski와 무관함 명시
**예상 소요**: 30분 (downstream 필드명 영향 분석)
**테스트**: 기존 테스트 필드명 업데이트
**의존성**: I-05와 동일 패턴 (명칭 변경)

---

### I-10: pepadmet linear fallback graph_note 미필터링
**파일**: `pyrosetta_flow/pepadmet_infer_script.py`
**문제**: `graph_note = "linear_sequence_fallback"` 태깅은 되지만, downstream 코드에서 이 플래그를 활용하여 결과 신뢰도를 표시하거나 필터링하지 않음
**해결**: pepadmet 결과에 `confidence_flag` 추가 ("full" vs "linear_fallback"), downstream에서 표시
**예상 소요**: 30분
**테스트**: SS bond 서열에서 linear fallback 발동 시 플래그 검증
**의존성**: I-03 (smiles_converter)과 연관

---

### I-11: HC50 단위 미명시
**파일**: `pyrosetta_flow/pepadmet_infer_script.py`
**문제**: task_3 HC50 출력값의 단위 미명시. pepADMET 논문(Zhu et al. 2026) 기준 μg/mL 추정.
**해결**: 논문 확인 후 결과 dict에 `hc50_unit` 필드 추가
**예상 소요**: 20분 (논문 확인)
**테스트**: 출력 dict에 `hc50_unit` 키 존재 확인
**의존성**: V-02 (pepADMET 원본 코드 분석)와 병행 가능

---

### I-12: pepadmet_runner timeout 고정
**파일**: `pyrosetta_flow/pepadmet_runner.py`
**현재 코드**: `timeout=120` 고정
**문제**: 대용량 배치(예: 100+ 서열)에서 타임아웃 위험. conda run 초기화 오버헤드(~5-10초) 미고려.
**해결**: `timeout = max(120, len(sequences) * 10 + 30)` 등 배치 크기 비례 timeout
**예상 소요**: 15분
**테스트**: 기존 테스트 통과 확인
**의존성**: 없음

---

### I-13: bayesian_optimizer qNEHVI 명칭 불일치
**파일**: `pyrosetta_flow/bayesian_optimizer.py` L496-530
**현재 코드**: docstring에 "qNEHVI acquisition"이라 했으나 실제는 `improvement.prod(dim=-1)` (product-of-improvements proxy)
**문제**: 코드 리뷰어/사용자가 진정한 qNEHVI(Monte Carlo 기반)로 오해
**해결**: docstring을 "product-of-improvements proxy (lightweight alternative to qNEHVI)"로 수정
**예상 소요**: 10분
**테스트**: docstring 검증
**의존성**: 없음

---

### I-14: SelectivityResult.offtarget_max_score 필드명 역전
**파일**: `AG_src/pipeline/step05b_selectivity.py`
**문제**: `offtarget_max_score` 필드가 실제로는 가장 강한(가장 작은 수) off-target 점수를 저장. "max"가 "가장 큰 수"를 암시하므로 의미가 역전됨.
**해결**: `offtarget_best_score` 또는 `offtarget_strongest_score`로 변경 + docstring 명확화
**예상 소요**: 30분 (downstream 참조 수정)
**테스트**: 기존 테스트 필드명 업데이트
**의존성**: I-01과 동일 파일

---

### I-15: out_pdb 미사용 파일 미정리
**파일**: `AG_src/pipeline/step05b_selectivity.py` (`_run_offtarget_pyrosetta`)
**문제**: subprocess가 `--output out_pdb` 파일을 생성하지만 파이프라인에서 사용하지 않음
**해결**: 임시 디렉토리로 관리하거나, 필요 없으면 `--output /dev/null` 사용
**예상 소요**: 15분
**테스트**: 함수 호출 후 임시 파일 미잔류 확인
**의존성**: I-08과 동일 패턴

---

### I-16: ECR tie 처리
**파일**: `pyrosetta_flow/gnina_rescoring.py`
**문제**: `exponential_rank_consensus()`에서 동점(tie) 시 Python stable sort에 의존. score_keys 수 변화 시 ECR 절대값 비교 불가.
**해결**: (1) 동점 시 평균 순위(average rank) 적용, (2) ECR 정규화: `ECR / K` (K=score_keys 수)
**예상 소요**: 30분
**테스트**: 동점 입력에서 순위 검증
**의존성**: 없음

---

### I-17: _convert_cif_to_pdb QUIET=True 경고 억제
**파일**: `AG_src/pipeline/step05b_selectivity.py`
**문제**: `MMCIFParser(QUIET=True)`로 파싱 경고 억제 → 데이터 품질 문제가 무시됨
**해결**: `QUIET=False` + 경고를 로거로 전달
**예상 소요**: 10분
**테스트**: 잘못된 CIF 파일에서 경고 로그 출력 확인
**의존성**: 없음

---

### I-18: cluster_report pLDDT_available 주석 부재
**파일**: `pyrosetta_flow/cluster_report.py`
**문제**: `all(crit_a.values())`에 `pLDDT_available` bool이 포함되는 설계 의도가 코드에서 명확하지 않음. `pLDDT_available=False`이면 전체 A 기준 불충족처럼 보이지만 실제로는 `pLDDT_ok=True`가 보완.
**해결**: 주석 추가: "pLDDT_available은 정보 플래그이며, pLDDT_ok가 실제 gate. ESMFold 미사용 시에도 A 진입 가능하도록 의도됨"
**예상 소요**: 10분
**테스트**: 기존 테스트 확인
**의존성**: 없음

---

### I-19: selectivity_margin 필드 소스 명시
**파일**: `pyrosetta_flow/cluster_report.py`
**문제**: B 클러스터 기준인 `selectivity_margin` 필드가 어디서 생성되는지(runner.py) 명시되지 않음. 필드 누락 시 B 자동 탈락.
**해결**: (1) B 기준 함수에 필드 존재 검증 추가 + 경고 로그, (2) 주석에 생성 위치 명시
**예상 소요**: 15분
**테스트**: `selectivity_margin` 키 누락 입력에서 적절한 경고 출력 확인
**의존성**: 없음

---

### I-20: 단일동위원소 MW 근사 한계
**파일**: `AG_src/pipeline/pharma_properties.py`
**현재 코드**: `mw_mono = mw_avg * 0.9994`
**문제**: 경험적 스케일링 상수 — MS 비교 응용에서는 정밀도 부족 (±0.5 Da)
**해결**: 원소 조성 기반 단일동위원소 계산 함수 추가 (선택적 사용)
**예상 소요**: 1시간
**테스트**: SST-14 monoisotopic MW를 ExPASy ProtParam과 비교
**의존성**: 없음

---

## 실행 순서 (Wave)

### Wave 1: 독립, 즉시 (의존성 없음) — 병렬 실행 가능

| ID | 항목 | 소요 | 담당 | 비고 |
|----|------|------|------|------|
| V-01 | RW S(Ser) 값 문헌 확인 | 30m | reviewer-science | 문헌 검색 + peptides 패키지 대조 |
| V-02 | pepADMET descriptor 순서 검증 | 1h | reviewer-science | pepADMET GitHub 원본 코드 분석 |
| V-03 | nephrotox DOTATATE docstring 수정 | 10m | engineer-backend | docstring 수정 + 단위 테스트 |
| I-01 | selectivity gate 이중 파라미터 수정 | 30m | engineer-backend | 옵션 B (재계산) 권장 |
| I-02 | pareto_ranking deepcopy 반환 | 20m | engineer-backend | 기존 테스트 수정 포함 |
| I-04 | n_hbd Pro 제외 | 15m | engineer-backend | 단순 수정 |
| I-06 | nephrotox His 제외 근거 주석 | 10m | engineer-backend | V-03과 동일 파일 |
| I-12 | pepadmet_runner timeout 비례 | 15m | engineer-backend | 단순 수정 |
| I-13 | bayesian_optimizer docstring 수정 | 10m | engineer-backend | 주석만 수정 |
| I-17 | CIF parser QUIET 제거 | 10m | engineer-backend | 단순 수정 |
| I-18 | cluster_report pLDDT 주석 추가 | 10m | engineer-backend | 주석만 수정 |

**Wave 1 예상 합산**: ~3시간 (병렬 시 ~1시간)

---

### Wave 2: Wave 1 결과 의존 또는 연관 작업

| ID | 항목 | 소요 | 담당 | 의존 |
|----|------|------|------|------|
| I-03 | smiles_converter SS fallback 플래그 | 30m | engineer-backend | — |
| I-05 | amphipathicity_index 명칭 변경 | 30m | engineer-backend | downstream 영향 분석 필요 |
| I-07 | DPP-IV N말단 전용 규칙 추가 | 20m | engineer-backend | V-01 결과로 동일 파일 수정 최적화 |
| I-09 | druglikeness_score 명칭 변경 | 30m | engineer-backend | I-05와 동일 패턴 |
| I-10 | pepadmet graph_note 필터링 | 30m | engineer-backend | I-03 결과 반영 |
| I-14 | offtarget_max_score 필드명 변경 | 30m | engineer-backend | I-01 동일 파일 |
| I-19 | selectivity_margin 필드 검증 추가 | 15m | engineer-backend | I-18과 동일 파일 |

**Wave 2 예상 합산**: ~3시간 (병렬 시 ~1시간)

---

### Wave 3: 정리 + 테스트 통합

| ID | 항목 | 소요 | 담당 | 의존 |
|----|------|------|------|------|
| I-08 | tempfile 정리 로직 | 20m | engineer-backend | I-15와 동시 |
| I-11 | HC50 단위 명시 | 20m | engineer-backend | V-02 결과 |
| I-15 | out_pdb 미사용 파일 정리 | 15m | engineer-backend | I-08과 동시 |
| I-16 | ECR tie + 정규화 | 30m | engineer-backend | — |
| I-20 | 단일동위원소 MW 정밀 계산 | 1h | engineer-backend | V-01 결과 (동일 파일) |
| — | 전체 테스트 실행 + 회귀 확인 | 30m | reviewer-code | Wave 1-3 전체 완료 후 |

**Wave 3 예상 합산**: ~3시간 (병렬 시 ~1.5시간)

---

## 예상 총 소요

| 구분 | 직렬 | 병렬 최적 |
|------|------|----------|
| Wave 1 | ~3h | ~1h |
| Wave 2 | ~3h | ~1h |
| Wave 3 | ~3h | ~1.5h |
| **합계** | **~9h** | **~3.5h** |

---

## 심각도별 분포

| 심각도 | 건수 | ID |
|--------|------|----|
| High | 5 | V-01, V-02, V-03, I-01, I-02 |
| Medium | 5 | I-03, I-04, I-05, I-06, I-07, I-08 |
| Low | 11 | I-09 ~ I-20 |
| **합계** | **23** | |

---

## 참고: 수정하지 않는 항목 (의도된 설계)

| 항목 | 이유 |
|------|------|
| admet.py 순전하 ±1 부울 가중치 | Henderson-Hasselbalch 완전 구현은 pharma_properties.py에 별도 존재. admet.py는 간이 추정용으로 의도됨 |
| estimation 모드 양수 offset | 보수적 가정으로 초기 스크리닝에 적합. 문서에 "estimation" 플래그 이미 존재 |
| cluster_report pLDDT_available=False → A 통과 | ESMFold 미사용 모드 지원을 위한 의도된 설계 |
| bayesian_optimizer fallback GP 단순 합산 | botorch 미설치 환경 대응. 정밀 Pareto 최적은 pareto_ranking.py가 담당 |
