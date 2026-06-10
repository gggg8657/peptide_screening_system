# 통합 부록 — SSTR2 방사성의약품 AI Co-Scientist

**5개 발표 버전 공용 참조 자료** · 발표 슬라이드에서 `(→ 부록 §X)` 형태로 참조

2026-04-05

> **형식**: 일반 마크다운 (Marp·슬라이드 비사용). 미리보기·GitHub·브라우저 인쇄로 PDF 등 확보.

## §별 목차

| § | 주제 |
|:---:|------|
| **§A** | 도구 전수 조사 (A-01) |
| **§B** | pharma_properties 15메서드·검증·수식 |
| **§C** | SS bond Cys 보정 (pI 등) |
| **§D** | DIWV Lookup 16건 버그 |
| **§E** | pepADMET 상세 |
| **§E-2** | pepADMET Toxicity 모델 |
| **§F-0** | Tier 1/2/3 병렬 후보·파레토 맥락 |
| **§F** | A~E 클러스터 분류 기준 |
| **§G** | Selectivity·margin·CIF |
| **§H** | 반감기 모델·PeptideCutter 비교 |
| **§I** | 13-메트릭 우선순위 |
| **§J** | Q&A 예상 질문 |
| 참고 문헌 | 참고 문헌 |


## 부록 §A: 도구 전수 조사 결과 (A-01)

회의록(2026-03-09) 안건 1에서 권장된 **18개 도구**의 실제 상태


## 부록 §A: 도구 전수 조사 (1/2)

| # | 도구 | 실제 상태 | 접속 | AI팀 대응 |
|---|------|----------|:----:|----------|
| 1 | PepCalc (Innovagen) | MW/pI/전하 계산기. **반감기 없음** | ✅ | `calculate_mw/pi/charge` |
| 2 | Peptide2.0 | 합성 회사. 계산 도구 아님 | ✅ | scope 밖 |
| 3 | PEPlife 2.0 (IIITD) | 실험 DB (r=0.743, 163건) | ✅ | `nend_rule_halflife` |
| 4 | PlifePred (IIITD) | 서열 기반. cyclic 학습 데이터 부재 | ✅ | 미통합 (동일 한계) |
| 5 | ExPASy PeptideCutter | 신뢰. 웹 전용, API 없음 | ✅ | 6종 효소 자체 구현 |
| 6 | ProteinSol | **solubility 도구**. protease 무관 | ✅ | GRAVY+WW 대체 |


## 부록 §A: 도구 전수 조사 (2/2)

| # | 도구 | 실제 상태 | 접속 | AI팀 대응 |
|---|------|----------|:----:|----------|
| 7 | DPPred | 실체 불분명 | ❓ | — |
| 8 | PepAnalyzer | 논문 존재, **서버 타임아웃** | ❌ | `calculate_all` 19항목 |
| 9 | Stability (BiRNN) | 실체 불확실 | ❓ | — |
| 10 | ADMETlab 3.0 | SSL 만료, API 404, MW<500 전용 | ⚠️ | pepADMET 전환 |
| 11 | SwissADME | small molecules 전용 | ✅ | GRAVY+MW/pI |
| 12 | ProtParam (ExPASy) | 기본 물성. 신뢰 | ✅ | II/AI/MW/pI 자체 구현 |
| 13~18 | HSPred 외 5종 | 접근성 불확실 또는 목적 불일치 | ❓ | 자체 구현으로 해결 |


> **총평**: 18개 중 신뢰 가능 4~5개, SST-14 cyclic peptide 특화 도구 **0개** → 자체 구현 불가피


*참고 · 근거: 회의록 2026-03-09 안건 1, a01_halflife_and_protease_detail.md*


## 부록 §B: pharma_properties 15메서드 + 검증 상세

### 검증 결과 요약
- **peptides** PyPI v0.5.0 대비
- 6서열 x 13메서드 = **78케이스**
- 오차율: **0.00%** (완벽 일치)
- 추가 2메서드(Metal, Radiolysis)는 자체 기준


----

### DIWV 버그 수정 후
- pharma_properties.py **12건** 수정
- pharmacology.py **4건** 수정
- Boman Index 부호 반전 수정
- 테스트 35개 → **62개**


## 부록 §B: 15메서드 수식 일람 (1/3)

| # | 메서드 | 수식 / 알고리즘 | 출처 |
|---|--------|----------------|------|
| 1 | **GRAVY** | `GRAVY = (1/n) * sum(KD_i)` | Kyte-Doolittle 1982 |
| 2 | **Boman Index** | `BI = (1/n) * sum(RW_transfer_i)` ; BI > 2.48 → 결합 경향 | Boman 2003, RW 1988 |
| 3 | **Instability Index** | `II = (10/n) * sum(DIWV[R_i][R_{i+1}])` ; II < 40 안정 | Guruprasad 1990 |
| 4 | **Aliphatic Index** | `AI = x_A + 2.9*x_V + 3.9*(x_I + x_L)` (몰분율 %) | Ikai 1980 |
| 5 | **pI** | Lehninger pKa 이분탐색 → 순전하 = 0인 pH | SS bond Cys 제외 보정 |


> SST-14 예시: GRAVY = -0.48, BI = 1.73, II = 6.36 (매우 안정), AI = 42.14, pI = 10.62 (SS 보정)


## 부록 §B: 15메서드 수식 일람 (2/3)

| # | 메서드 | 수식 / 알고리즘 | 출처 |
|---|--------|----------------|------|
| 6 | **MW** | 잔기질량 합 - (n-1) x 18.015 - n_SS x 2.016 | condensation + SS 보정 |
| 7 | **Extinction Coeff** | `e280 = 5500*n_W + 1490*n_Y + 125*n_SS` | Pace 1995 |
| 8 | **N-end Rule** | N말단 잔기 → 반감기 표 (A=4.4h, R=1h...) | Varshavsky 1996 |
| 9 | **Hydrophobic Moment** | `uH = max_window( sqrt( (sum sin*H)^2 + (sum cos*H)^2 ) / w )` | Eisenberg 1982 |
| 10 | **Wimley-White** | `WW = sum(dG_transfer_i)` ; 양 → aqueous, 음 → membrane | WW 1996 |


> SST-14 예시: MW = 1639.91 Da, e280 = 6,835 M⁻¹cm⁻¹(SS), N-end = 4.4h (Ala), uH = 0.46


## 부록 §B: 15메서드 수식 일람 (3/3)

| # | 메서드 | 수식 / 알고리즘 | 출처 |
|---|--------|----------------|------|
| 11 | **Net Charge** | Henderson-Hasselbalch: `q = sum(1/(1+10^(pH-pKa)))` | 양이온/음이온 분리 계산 |
| 12 | **Protease Sites** | 6종 효소: Chymo(FWYLM), Trypsin(KR), NEP, Pepsin, Elastase, DPP-IV | ExPASy 규칙 확장 |
| 13 | **BLOSUM62 Score** | 참조 서열 대비 위치별 치환 점수 합 | Henikoff 1992 |
| 14 | **Metal Coordination** | H, C(free), D, E, M 잔기 위치 + 금속 선호도 매핑 | Rulisek 1998 |
| 15 | **Radiolysis Susceptibility** | `RS = sum(w_i * count_i)` ; M(3.0), W(2.5), C(2.0)... | 방사분해 민감 잔기 |


> SST-14 예시: Net Charge(pH7.4) = +2.02, Protease = 9건, BLOSUM62 = 68, Metal = His(1), Radiolysis = W(1)+C(2) = 6.5


## 부록 §C: SS bond Cys 보정 상세

### Henderson-Hasselbalch 기반 전하 계산


> **양이온 기여**: q⁺ = 1 / (1 + 10^(pH − pKa))
> **음이온 기여**: q⁻ = −1 / (1 + 10^(pKa − pH))
> **순전하** = sum(q⁺) + sum(q⁻)


### SS bond Cys 이온화 제외 로직

Cys3과 Cys14가 이황화 결합(S-S)을 형성하면 **SH 측쇄가 소멸** → pKa 8.18 이온화 항에서 **제외**

| 구분 | 이온화 Cys 수 | pI |
|------|:----------:|:---:|
| SS bond 미보정 | 2 | 9.04 |
| SS bond 보정 | **0** | **10.62** |


----

### 방사성의약품적 의미

**pI 9.04 → 10.62** 변화의 임상적 함의:

1. **사구체 여과**: pH 7.4에서 양전하 증가 → 사구체 기저막(음전하)과 정전기 상호작용 → **여과 촉진**
2. **신장 체류**: 양이온성 펩타이드 = megalin 수용체 결합 경향 → PRRT 신독성 관련
3. **MW 보정**: condensation (−(n−1) x 18.015) + SS bond (−2 x 1.008)
   → **1639.91 Da** (정확값)


> 이 보정 없이는 pI 오류 1.58, MW 오류 2.016 Da 발생 → 클러스터 D 판정에 직접 영향


*참고 · pharma_properties.py calculate_pi(), calculate_mw()*


## 부록 §D: DIWV Lookup Table 16건 버그 상세

### 오류 분포

| 모듈 | 오류 건수 | 유형 |
|------|:--------:|------|
| `pharma_properties.py` | **12건** | DIWV 값 오타/누락 |
| `pharmacology.py` | **4건** | DIWV 값 오타 |

### 대표 사례 — Instability Index 영향

| dipeptide | 오류값 | 정답값 | 오차 | II 영향 |
|-----------|------:|------:|-----:|---------|
| RR | −6.54 | **58.28** | 64.82 | II 과소평가 → 불안정 서열을 안정으로 오분류 |
| MM | −14.03 | **−1.88** | 12.15 | II 과대평가 |
| FK | 미등록 | **−0.46** | — | KeyError 발생 가능 |

### Boman Index 부호 반전


> 수정 전: `BI = −mean(RW)` (부호 반전) → 친수성 펩타이드가 소수성으로 오판
> 수정 후: `BI = mean(RW)` → Boman(2003) 원논문 정의 준수


> 전체 16건 수정 후 peptides PyPI v0.5.0 대비 78케이스 0오차 달성


*참고 · pharma_properties_verification_report.md*


## 부록 §E: pepADMET 상세 (1/2)

### 논문 정보

- **JCIM 2026**, Vol.66, pp.936–946
- **36,643** 펩타이드 학습 데이터
- **19** ADMET endpoints
- MGA 아키텍처: RGCN + descriptor branch
- GitHub 공개 → 자체 데이터 재학습 가능

### 독성 사전학습 모델 결과

| 태스크 | 결과 | 비고 |
|--------|------|------|
| Binary toxicity | **AUC 0.885** | 추론 성공 |
| Toxicity type | softmax 분류 | 5종 분류 |
| Neurotoxicity | softmax 분류 | 서브타입 |
| HC50 회귀 | R²=0.474 | 보조 신호만 |


----

### Descriptor 2133차원 — 진행중


> **용어 정리 — descriptor**  
> 머신러닝에서 **descriptor**는 분자(여기서는 펩타이드)를 **고정 차원 실수 벡터**로 표현한 **특성(feature) 집합**이다. 화학 구조에서 뽑은 **수치 특성들**(부분구조 개수, 결합·원자 통계, 위상 지표 등)을 **하나의 2133차원 벡터**로 묶은 것이 pepADMET 논문·코드의 입력 한 축이다. **그래프 신경망(RGCN)** 이 2D 구조를 보고, **descriptor 분기**가 같은 화합물의 **전통적 수치 특성**을 보는 **듀얼 입력** 구조다.


- `calculate_descriptors()` → 2133차원 벡터
- 부족/초과 시 자동 패딩/절단
- 파이프라인 통합 테스트 단계
- 완료 시 full MGA forward 가능

### ADMETlab 3.0 부적합 사유

| 항목 | 상태 |
|------|------|
| SSL 인증서 | **만료** (2026-01-13) |
| API endpoint | **전부 404** |
| MW 적용범위 | <500 Da (소분자 전용) |
| SST-14 MW | ~1640 Da → **AD 밖** |


*참고 · JCIM 2026 66:936-946, pepadmet_runner.py*


## 부록 §E: pepADMET 상세 (2/2)

### SMILES → 그래프 변환 체인


> 1. `smiles_converter.sequence_to_smiles(seq)` → Cys-Cys SS bond 포함 SMILES 시도
> 2. `MolFromSmiles(smiles)` 성공 → `graph_from_mol` → DGL 그래프 → MGA forward
> 3. 실패 시 → `graph_from_sequence_linear(seq)` 폴백 (SS bond 미반영)


### 폴백 시 주의사항

| 구분 | 설명 |
|------|------|
| 트리거 | cyclic/이황화 SMILES가 RDKit 버전에 따라 파싱 실패 |
| 계산 | 폴백이어도 MGA forward는 **실행됨** (독성 예측 스킵 아님) |
| 토폴로지 | 선형 그래프 → Cys3-Cys14 브릿지 미반영 → 모델 입력 분포 이탈 가능 |
| UI 표시 | "SMILES round-trip failed" 배지 + `linear_sequence_fallback` 태그 |


> ADMET 휴리스틱(Druglikeness, MW, KD 등)은 서열 규칙만 사용하므로 SMILES 폴백과 무관.
> pepADMET만 그래프 토폴로지에 의존 → 폴백 시 "ADMET 정상 + pepADMET 폴백 배지" 조합 가능


## 부록 §E-2: pepADMET Toxicity 모델 아키텍처 상세 (1/2)

### MGA (Multi-Graph Attention) 아키텍처

**한줄 요약**: 분자의 "구조"와 "숫자 특성"을 각각 읽은 뒤, 중요한 쪽에 가중치를 줘서 합친다.

```
┌─────────────────────┐   ┌──────────────────────┐
│  입력 1: 분자 그래프  │   │  입력 2: Descriptor   │
│  SMILES → RDKit      │   │  2,133차원 벡터       │
│  원자=노드, 결합=엣지 │   │  (RDKit+PyBioMed     │
│                      │   │   +modlAMP)           │
│  ↓                   │   │  ↓                    │
│  RGCN 인코딩         │   │  MLP 임베딩           │
│  (이웃 원자 정보를    │   │  (숫자→압축 벡터)     │
│   집계하는 신경망)    │   │                       │
└──────┬──────────────┘   └──────┬───────────────┘
       │                         │
       └────────┬────────────────┘
                ↓
        Attention 가중 결합
        (어느 branch가 더 유용한지
         모델이 스스로 학습)
                ↓
        ┌───────────────────┐
        │  4개 출력 헤드     │
        │  (Multi-task)     │
        └───────────────────┘
```


----

### 용어 해설 (비전공자용)

| 용어 | 쉬운 설명 |
|------|----------|
| **RGCN** | 분자의 원자-결합 연결 관계를 읽는 신경망. "이웃 원자가 뭔지"를 반복적으로 집계 |
| **MLP** | 숫자 입력을 받아 층층이 변환하는 가장 기본적인 신경망 |
| **Attention** | 두 정보원 중 "지금 이 예측에 더 중요한 쪽"에 높은 가중치를 자동 부여 |
| **Multi-task** | 하나의 모델이 여러 과제를 동시에 학습 → 공유 표현으로 성능 향상 |

### 학습 설정

| 항목 | 값 |
|------|-----|
| Batch | 128 |
| Epochs | 300 (Patience 50) |
| Learning Rate | 1e-3 |
| Weight Decay | 1e-5 |
| 학습 데이터 | **14,660** 펩타이드 |

**가중치**: `model/toxicity_early_stop.pth` (공개, 즉시 추론)
**코드**: `Train.ipynb` + `MY_GNN.py` (재학습 가능)


*참고 · pepADMET — JCIM 2026 66:936-946, GitHub: SXKDZ/pepADMET*


## 부록 §E-2: pepADMET Toxicity 모델 아키텍처 상세 (2/2)

### 4개 출력 헤드 (Multi-task)

| Task | 출력 | 활성화 | 메트릭 |
|------|------|--------|--------|
| task_0: Binary Toxicity | 독성 유무 | Sigmoid | AUC **0.885** |
| task_1: 6-class Type | 독성 유형 분류 | Softmax | AUC **0.949** |
| task_2: Neuro Subtype | 신경독성 서브타입 | Softmax | AUC (논문 참조) |
| task_3: HC50 | 적혈구 용혈 농도 | Linear | **R² = 0.474** |

### HC50 (Half-maximal Hemolytic Concentration) 상세


> **HC50**은 적혈구의 50%가 용혈(파괴)되는 펩타이드 농도. **높을수록 안전** (높은 농도에서야 용혈 발생).
> 회귀 태스크 → R²=0.474 = 설명력 47%. Multi-task의 부산물이며 주 태스크는 Binary Toxicity (AUC 0.885).
> **파이프라인 내 위치**: 단독 탈락 기준으로 사용 안 함. 다중 지표(pharma 15종 + cluster + selectivity) 중 하나.


### pepADMET 전체 17개 모델 현황

| 그룹 | 모델 수 | 아키텍처 | 현재 상태 |
|------|:------:|---------|----------|
| **Toxicity** | 4 | MGA (RGCN+MLP+Attn) | ✅ 추론 성공 (14,660건) |
| Permeability | 5 | GNN + LightGBM | 재현 필요 (7,765건) |
| Half-life | 5 | Transfer Learning | 재현 필요 (970건) |
| Distribution | 2 | RF / XGBoost / SVM | 재현 필요 (850건) |
| Absorption | 1 | RF / XGBoost / SVM | 재현 필요 (305건) |


> **핵심 메시지 (청중용)**: HC50은 딥러닝(MGA) 모델의 multi-task 출력 중 하나입니다. 주 태스크인 Binary Toxicity (AUC 0.885)는 신뢰할 수 있으나, HC50 회귀(R²=0.474)는 설명력이 절반 수준이라 **보조 참고 지표로만** 활용합니다.


*참고 · pepADMET — JCIM 2026 66:936-946, model/toxicity_early_stop.pth*


## 부록 §F-0: A-05 Tier 1/2/3 병렬 후보 생성 구조

### 원본 요구 (회의 안건 4 + 액션 A-05)

RI팀이 "BLOSUM62만으로는 혁신 후보 발굴 어려움" 제기 → AI팀이 계층적 Tier 전략으로 대체 제안 → 합의

### Tier 구조 상세

| Tier | 전략 | 허용 범위 | 후보 규모 | 장점 |
|:----:|------|----------|:---------:|------|
| **1** | BLOSUM62 ≥ 0 보존 치환 | FWKT 고정, 보존 치환 위주 | ≤ 1,000 | 안전, QC 빠름 |
| **2** | 물리화학 유사도 필터 | 소수성 \|Δ\| ≤ 3.0, 전하 ±1, 비표준 AA 포함 | ≤ 10,000 | 비보존 탐색 확장 |
| **3** | 비제한 자유 탐색 | D-AA, Aib, β-AA, N-메틸화 등 완전 자유 | 탐색적 | 혁신 후보 발굴 |

### Thompson Sampling 자동 배분

- 각 Tier에서 생성된 후보의 **ddG 성과**를 Beta 분포로 추적
- 성과가 좋은 Tier에 **자원(계산 시간) 자동 집중**
- 초기에는 균등 배분 → 반복할수록 유망 Tier에 수렴

### 최적화 체인 (Tier 이후)

| 단계 | 알고리즘 | 역할 |
|------|---------|------|
| 1 | **Bayesian Optimization** (GP + UCB) | ddG surrogate 학습 → 유망 서열 영역 집중 탐색 |
| 2 | **Pareto Front** (NSGA-II) | ddG × selectivity × stability 다목적 최적화 |
| 3 | **A~E 분류** | Top-K 비지배 해를 등급별 분류 |

> Thompson Sampling: 다중 슬롯 머신 문제의 해법. BO: Gaussian Process 기반. Pareto: 한 목적 개선 시 다른 목적 악화 없는 최적 집합

*참고 · 구현: runner.py, bayesian_optimizer.py, pareto_ranking.py*


## 부록 §F: A~E 클러스터 분류 기준

### 판정 우선순위: A > B > C > D > E (첫 번째 all-pass 클러스터 부여)

| 등급 | 조건 | 의미 | 우선순위 |
|:----:|------|------|:--------:|
| **A** | ddG ≤ −8, clash ≤ 5, pLDDT ≥ 75*, FWKT 유지 | 결합 엘리트 — 최우선 합성 | 1 |
| **B** | selectivity_margin ≥ 3.0, ddG < −5 | 선택성 특화 — SSTR2 >100x 목표 | 2 |
| **C** | II < 30, BLOSUM62 합계 ≥ 0, protease ≤ 9 | 안정성 강화 — 반감기 연장 | 3 |
| **D** | −1 ≤ GRAVY ≤ 0.5, \|charge\| ≤ 1, n_strong ≥ 1 | 방사화학 최적 — 표지 QC | 4 |
| **E** | 위 모두 불만족 | 탐색 후보 — MD 추가 검증 | 5 |

### 주의사항


> - **pLDDT skip**: ESMFold 미실행 시 pLDDT 조건은 True 처리 (벌점 없음). 단, `pLDDT_available = False`이므로 **Cluster A 진입 불가**
> - **II 30 vs 40**: 표준 문헌 기준 40이나, 방사성의약품 보수적 기준으로 **30** 적용 (Cluster C)
> - **n_strong 불일치**: `PharmaProperties.calculate_all`에서 `n_strong` 키 누락 가능 → Cluster D 판정 실패 위험 → Pharmacology API 경로 사용 필요


*참고 · cluster_report.py classify_cluster()*


## 부록 §G: Selectivity 상세 (1/2)

### SSTR1~5 수용체 구조

| 수용체 | PDB ID (CIF) | 리간드 | 비고 |
|--------|:-----------:|--------|------|
| SSTR1 | **9IK8** | — | off-target |
| SSTR2 | **7XNA** | SST-14 유사체 | **표적** |
| SSTR3 | **8XIR** | — | off-target |
| SSTR4 | **7XMT** | — | off-target |
| SSTR5 | **8ZBJ** | — | off-target |

### FlexPepDock Production Mode 프로토콜


> 1. 수용체 CIF → PyRosetta `pose_from_pdb`
> 2. 변이 펩타이드 → 초기 도킹 배치 (SST-14 참조 구조 기반)
> 3. FlexPepDock refinement → ddG 계산
> 4. 5개 수용체 각각에 대해 독립 실행


## 부록 §G: Selectivity 상세 (2/2)

### Selectivity Margin 계산


> **selectivity_margin** = min( ddG(SSTR1), ddG(SSTR3), ddG(SSTR4), ddG(SSTR5) ) − ddG(SSTR2)
>
> Gate: margin ≥ 3.0 kcal/mol → **Cluster B 자격**


### 해석

| margin 범위 | 의미 | 선택성 배수 (근사) |
|:-----------:|------|:-----------------:|
| ≥ 5.0 | 우수한 선택성 | >1000x |
| 3.0 ~ 5.0 | 양호 (B등급 통과) | 100~1000x |
| 1.0 ~ 3.0 | 약한 선택성 | 10~100x |
| < 1.0 | 비선택적 | <10x |


> **현재 상태**: 시스템 구축 완료 (CIF 5종 등록 + FlexPepDock 연결). 시뮬레이션 진행 가능 단계.
> 합성 후보 확정 시 실제 selectivity screening 실행 예정


*참고 · selectivity.py, CIF: 9IK8/7XNA/8XIR/7XMT/8ZBJ*


## 부록 §H: 반감기 예측 모델 (step08_stability.py)

### 기본 반감기 + 5종 수정 보너스

| 구분 | 기본값/보너스 | 근거 |
|------|:----------:|------|
| 기본 (선형) | **3h** | 혈청 내 선형 펩타이드 |
| C18 지방산 | **+120h** | Semaglutide 알부민 결합 |
| PEG 2kDa | **+96h** | 사구체 여과 제한 |
| D-amino acid | **+48h/잔기** | DPP-4/NEP 저항 |
| Cyclization | **+24h** | 프로테아제 접근 감소 |
| Substitution | **+12h** | 취약 잔기 교체 |

SST-14 (cyclic): 3 + 24 = **27h** 기본 예측


----

### 20AA 프로테아제 취약성 스코어 (상위)

| AA | 스코어 | 주요 효소 |
|:--:|:------:|----------|
| R | **3.0** | Trypsin |
| K | **2.5** | Trypsin |
| F | **2.0** | Chymotrypsin |
| Y/W | 1.5~1.8 | Chymotrypsin (+방사분해) |
| M/L/I | 1.0~1.5 | 산화/NEP |
| V 외 | 0.2~0.8 | Elastase 등 |


*참고 · step08_stability.py predict_half_life(), a01_halflife_and_protease_detail.md*


## 부록 §H: ExPASy PeptideCutter 대비 비교

| 항목 | ExPASy PeptideCutter | AI팀 자체 구현 |
|------|---------------------|---------------|
| 효소 수 | 다수 (범용) | **6종** (방사성의약품 핵심) |
| 대상 효소 | Trypsin, Chymotrypsin 등 | Chymo, Trypsin, **NEP**, **Pepsin**, Elastase, **DPP-IV** |
| API | **없음** (웹 수동) | 파이프라인 내 자동 호출 |
| SS bond 인식 | 미고려 | SS bond 위치 → 절단 해석 반영 |
| 배치 처리 | 불가 (1개씩) | `batch_analyze()` 수천 개 |
| 방사성의약품 특화 | 없음 | NEP (신장 브러시 보더), DPP-IV (SST 분해) |

### SST-14 절단 부위 — FWKT pharmacophore 근처 집중


> `A G C K N F F W K T F T S C`
>          K4:Tryp  F7:Chymo,NEP  F8:Chymo,NEP  W9:Chymo,NEP  K10:Tryp  F12:NEP
> → 총 ~11건 절단 위치, **7-10번(FWKT) 구간에 집중** → pharmacophore 보존 vs 프로테아제 저항 트레이드오프


## 부록 §I: 13-메트릭 우선순위 (1/2) — 회의 안건 10

| 우선순위 | 메트릭 | 등급 | 근거 |
|:--------:|--------|:----:|------|
| 1 | **ddG (결합 에너지)** | ★★★★★ | 약효의 근본 — SSTR2 결합력 |
| 2 | **Selectivity margin** | ★★★★★ | off-target 부작용 방지 |
| 3 | **Instability Index** | ★★★★☆ | 혈청 안정성 → 반감기 |
| 4 | **GRAVY** | ★★★★☆ | 약물동태 (투과성/용해도 균형) |
| 5 | **Net Charge pH 7.4** | ★★★★☆ | 신장 체류 + 세포 투과성 |
| 6 | **Protease Sites** | ★★★☆☆ | 효소 분해 저항성 |


## 부록 §I: 13-메트릭 우선순위 (2/2)

| 우선순위 | 메트릭 | 등급 | 근거 |
|:--------:|--------|:----:|------|
| 7 | **Metal Coordination** | ★★★☆☆ | 방사성 금속 킬레이션 적합성 |
| 8 | **Radiolysis** | ★★★☆☆ | 방사분해 안정성 |
| 9 | **BLOSUM62** | ★★☆☆☆ | 보존적 변이 여부 |
| 10 | **Boman Index** | ★★☆☆☆ | 비특이적 단백질 결합 |
| 11 | **Aliphatic Index** | ★★☆☆☆ | 열안정성 보조 지표 |
| 12 | **MW** | ★☆☆☆☆ | AD 범위 확인용 |
| 13 | **pI** | ★☆☆☆☆ | 제형 최적화 참고 |


> ★★★★★ = 필수 Gate (불합격 시 클러스터 하향), ★☆☆☆☆ = 정보 제공 전용


*참고 · 회의록 2026-03-09 안건 10, cluster_report.py*


## 부록 §J: Q&A 예상 질문 대응표 (1/2)

| # | 예상 질문 | 핵심 답변 |
|---|----------|----------|
| 1 | ddG 계산의 정확도는? | FlexPepDock ddG는 상대 비교용. 절대값이 아닌 **순위 선별** 목적. MD free energy 후속 검증 계획 ¹ |
| 2 | cyclic 펩타이드에 ML 모델이 유효한가? | 학습 데이터에 cyclic 비율 낮음 인정. ML은 **사전 필터**, 최종은 실험 검증 ² |
| 3 | 반감기 3h 기본값의 근거? | in vivo 혈청 내 미변형 선형 펩타이드 평균 ³ |
| 4 | 왜 ADMETlab 대신 pepADMET? | ADMETlab MW<500 전용 + SSL 만료 + API 404. pepADMET는 펩타이드 전용 36K 데이터 ⁴ |


> ¹ Raveh 2011, FlexPepDock  ² pepADMET 논문 한계 절  ³ Fosgerau 2015  ⁴ §E 상세


## 부록 §J: Q&A 예상 질문 대응표 (2/2)

| # | 예상 질문 | 핵심 답변 |
|---|----------|----------|
| 5 | pI 보정이 실제 약효에 영향? | pI 10.62 → pH 7.4에서 양전하 +2 → 신장 megalin 결합 ↑ → PRRT 신독성 모니터링 필요 ⁵ |
| 6 | FWKT pharmacophore 변이 시 활성 유지? | BLOSUM62 보존적 치환만 허용 (F→Y, W→F). 비보존 시 Cluster A 배제 ⁶ |


## 부록 §J: Q&A 예상 질문 대응표 (3/3)

| # | 예상 질문 | 핵심 답변 |
|---|----------|----------|
| 7 | 외부 도구 0개 채택인데 신뢰성은? | 78케이스 0오차 검증 + 62개 테스트 + GT 8/8 일치. 자체 구현이 오히려 **재현성 + 배치 처리** 가능 ⁷ |
| 8 | selectivity margin 3.0의 근거? | ddG 3 kcal/mol ≈ 100배 결합 상수 차이 (exp(3/0.593)). 방사성의약품 off-target 최소 기준 ⁸ |
| 9 | 파이프라인 실행 시간은? | 단일 후보 FlexPepDock ~15분 (CPU). 100개 배치 = ~25시간. GPU GNINA 병행 시 단축 |
| 10 | 다음 단계는? | Top-K 후보 → 합성 → in vitro 결합 → PET 영상 → 임상 전 |
| 11 | Tier 3 비제한 탐색이 너무 넓지 않나? | Thompson Sampling이 성과 기반 자동 배분 → 비효율 Tier는 자원 축소. 초기 탐색 후 유망 Tier로 수렴 |
| 12 | 블라인드 도킹 vs 위치 지정 도킹? | 현재 블라인드. FlexPepDock은 위치 지정 가능 → 정확도 향상 기대. 전환 논의 필요 |


> ⁵ §C 상세  ⁶ cluster_report.py  ⁷ §B 검증 결과  ⁸ Boltzmann 관계


*참고 · 발표 스크립트 Q&A 섹션, 05_presentation_script.md*


## 부록 — 참고 문헌


> 1. Kyte J & Doolittle RF (1982) *J Mol Biol* 157:105-132 — Hydropathy scale (GRAVY)
> 2. Boman HG (2003) *J Intern Med* 254:197-215 — Boman Index
> 3. Guruprasad K et al. (1990) *Protein Eng* 4:155-161 — Instability Index / DIWV
> 4. Ikai A (1980) *J Biochem* 88:1895-1898 — Aliphatic Index
> 5. Pace CN et al. (1995) *Protein Sci* 4:2411-2423 — Extinction coefficient
> 6. Varshavsky A (1996) *PNAS* 93:12142-12149 — N-end rule
> 7. Eisenberg D et al. (1982) *Nature* 299:371-374 — Hydrophobic moment
> 8. Wimley WC & White SH (1996) *Nature Struct Biol* 3:842-848 — Membrane partitioning
> 9. Henikoff S & Henikoff JG (1992) *PNAS* 89:10915-10919 — BLOSUM62
> 10. Rulisek L & Vondrasek J (1998) *J Inorg Biochem* 71:115-127 — Metal coordination
> 11. Radzicka A & Wolfenden R (1988) *Biochemistry* 27:1664-1670 — Transfer free energy
> 12. pepADMET (2026) *JCIM* 66:936-946 — Peptide ADMET prediction
> 13. Raveh B et al. (2011) *Proteins* 78:2029-2040 — FlexPepDock
> 14. Fosgerau K & Hoffmann T (2015) *Drug Discov Today* 20:122-128 — Peptide therapeutics


*참고 · 통합 부록 끝 — 메인 발표 덱 참조: 메인 발표 덱 (`04_v_b_action_order.md`)*

