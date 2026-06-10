# Silo B 계산 정의 상세 보고 (ADMET · pepADMET · Pharmacology · Cluster)

**목적**: 대시보드에 표시되는 수치·라벨이 **소스 코드에서 어떤 식으로 정의·계산**되는지 필드 단위로 기술한다.  
**구현 기준 경로**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`  
**연관 문서**: 경로 다이어그램은 [`silo_b_code_to_ui_pipeline_trace.md`](./silo_b_code_to_ui_pipeline_trace.md), 패널 개요는 [`silo_b_dashboard_panels_methodology.md`](./silo_b_dashboard_panels_methodology.md).

---

## A. ADMET 패널 (휴리스틱, 규칙 기반)

**엔드포인트**: `POST /api/admet/batch` → `backend/admet.py` 의 `compute_admet` + `compute_admet_full`, 이후 `merge_pepadmet_into_admet_results`.

**공통**: 입력 서열은 대문자·공백 제거. **외부 네트워크 API 없음** (pepADMET 제외).

### A.1 Molecular Weight (`admet.mw`)

- **정의**: 각 잔기 **잔기 질량(펩타이드 결합으로 물 1분자 제거된 형태)** 의 합 + **자유 N/C 말단 보정으로 물 1분자** (`18.01056 Da`) 가산.
- **코드**: `backend/admet.py` — `_AA_RESIDUE_WEIGHTS`, `_WATER_MW`.

### A.2 Net Charge pH 7.4 (`admet.net_charge_ph74`)

- **정의 (단순 카운트 규칙)**:
  - 측쇄: K, R 각 +1; D, E 각 −1; H는 **+0.1** (고정 분획 근사).
  - 명시적으로 **N말단 +1**, **C말단 −1** 를 더함 (`compute_admet` 주석: 생리학적 pH에서 상쇄될 수 있으나 스펙상 포함).
- **주의**: Pharmacology의 Henderson–Hasselbalch 기반 전하(`charge_at_ph74`)와 **숫자가 다를 수 있음** (아래 H절 참고).

### A.3 H-bond Donors / Acceptors (`admet.n_hbd`, `admet.n_hba`)

- **n_hbd**: 측쇄 HBD 개수 테이블(`_SIDECHAIN_HBD`) 합 + **잔기 수**(백본 NH를 잔기마다 1개로 단순 가산; Pro 예외 미반영).
- **n_hba**: 측쇄 HBA(`_SIDECHAIN_HBA`) 합 + **잔기 수**(백본 C=O).

### A.4 Hydrophobicity (`admet.hydrophobicity`)

- **정의**: **Kyte–Doolittle** 값의 산술 평균 (`_KD_HYDROPATHY`).

### A.5 Amphipathicity Index (`admet.amphipathicity_index`)

- **정의**: 동일 서열에 대해 KD 스케일 값들의 **분산**(코드상 `mean_kd = hydrophobicity` 로 두고 `(v - mean_kd)²` 평균).  
- UI 문구 “KD hydropathy variance”와 대응.

### A.6 Druglikeness Score 0–100 (`admet.druglikeness_score`, `druglikeness_breakdown`)

**총점 = 네 규칙 각 최대 25점 합** (`backend/admet.py`).

| 규칙 키 | 조건 (통과 시 +25) | 비고 |
|--------|---------------------|------|
| `mw_range` | `1200 ≤ mw ≤ 2000` (Da) | 펩타이드 스크리닝용 고정 구간 |
| `charge` | `abs(net_charge) ≤ 3` | A.2의 단순 전하 |
| `hydrophobicity` | `-2 ≤ hydrophobicity ≤ 1` | KD 평균 |
| `no_repeats` | 동일 잔기가 **연속 3개 이상** 없음 (`re.search(r"(.)\1{2,}", seq)` 가 없을 것) |

- **라벨**: 보통 100/100이면 UI에 “DRUG-LIKE” 등으로 매핑(프론트 표시 로직은 컴포넌트 쪽).

---

## B. PRRT Renal Retention Risk (`nephrotox`)

**함수**: `compute_nephrotox_risk` (`backend/admet.py`).

| 필드 | 계산 |
|------|------|
| `n_lys`, `n_arg`, `n_his` | 서열 내 개수 |
| `cationic_residues` | 위 세 합 |
| `net_charge` | K/R ±1, D/E −1, H +0.1 누적 (**N/C 말단 ±1 없음** — ADMET `net_charge_ph74` 와 다를 수 있음) |
| `renal_risk_score` | `min(100, round((n_lys + n_arg) * 20 + max(0, net_charge) * 15, 1))` |
| `risk_level` | &lt;30 Low, 30–60 Moderate, &gt;60 High |
| `warning` | Moderate/High 시 생성 문자열 |

---

## C. pepADMET 독성 (ML, 서브프로세스)

**병합**: `merge_pepadmet_into_admet_results` → `pyrosetta_flow/pepadmet_runner.predict_toxicity_batch`  
**추론 스크립트**: `pyrosetta_flow/pepadmet_infer_script.py` (conda 환경 `pepadmet`).

### C.1 입력·그래프 (SMILES 경로 vs 선형 폴백)

**호출 체인**: `pepadmet_runner.predict_toxicity_batch` → conda로 `pepadmet_infer_script.py` 실행. 입력 JSON에는 `sequence`와 `smiles`가 들어가며, `smiles`는 기본적으로 **`pyrosetta_flow/smiles_converter.sequence_to_smiles(sequence)`** 로 생성된다.

#### C.1.1 SMILES 생성 쪽 — 이황화를 **반영하려는** 경로 (`smiles_converter.py`)

- `Chem.MolFromSequence(seq)` 로 선형 펩타이드를 만든 뒤, **기본값**으로 **첫 Cys ↔ 마지막 Cys**(1-indexed 위치)의 **SG–SG 이황화 결합**을 RWMol로 추가하고 `MolToSmiles` 한다.
- SS 형성이 실패하면(산itize 예외 등) **선형 분자**로 되돌려 SMILES를 낸다.
- **요지**: pepADMET에 넘기는 1차 SMILES는 **가능하면 브릿지가 포함된** 형태를 목표로 한다. “시스테인이 있으면 pepADMET이 아예 동작하지 않는다”가 아니다.

#### C.1.2 추론 스크립트 쪽 — 그래프 빌드 순서 (`pepadmet_infer_script.py`)

1. **`smiles_to_graph(smiles)`**: `MolFromSmiles(smiles)` 성공 시 → `graph_from_mol` 로 DGL 그래프.
2. **그래프가 `None`이면** `graph_from_sequence_linear(seq)` 호출:
   - **`Chem.MolFromSequence(seq)` 만** 사용 (여기서는 **이황화 결합을 추가하지 않음**).
   - 성공 시 `graph_note = "linear_sequence_fallback"` 이 결과에 붙는다.

#### C.1.3 `linear_sequence_fallback` 이 뜰 때의 의미 (Cys·SST-14 맥락)

| 구분 | 설명 |
|------|------|
| **트리거** | 1차 SMILES가 `MolFromSmiles`에서 깨지거나 그래프 생성 실패 — 주석상 **사이클릭/이황화 SMILES가 RDKit 버전·환경에 따라 파싱 실패**하는 경우를 염두에 둠. |
| **계산 자체** | 폴백이어도 `available: True`이면 **MGA forward는 실행**된다. “독성 예측이 완전히 스킵된다”는 뜻이 아니다. |
| **토폴로지** | 폴백 그래프는 **선형 펩타이드**에 가깝고, **의도한 Cys3–Cys14 이황화 브릿지가 그래프에 반영되지 않을 수 있다.** 모델 입력 분포와 어긋나면 수치·해석 신뢰도가 떨어질 수 있다. |
| **UI 배지** | “SMILES round-trip failed” 류 문구와 함께, **근거 구조가 선형 대체**임을 사용자에게 알리는 용도. |

#### C.1.4 ADMET 휴리스틱(`admet.py`)과의 관계

- **Druglikeness·MW·KD 등**은 **서열 규칙**만 쓰므로 SMILES/pepADMET 그래프와 독립이다.
- **pepADMET**만 그래프 토폴로지에 의존하므로, **폴백 시 불일치**가 생기면 “ADMET 카드는 정상인데 pepADMET만 폴백 배지” 같은 조합이 나올 수 있다.

### C.2 모델

- **아키텍처**: `MGA` (RGCN + descriptor branch), 가중치 `model/toxicity_early_stop.pth`.
- **Descriptor**: `calculate_descriptors` → **2133차원** (부족/초과 시 패딩·절단).
- **태스크** (출력 헤드):
  - `task_0`: 이진 독성 로짓 → **sigmoid** → `binary_toxicity` ∈ (0,1); `is_toxic = (bp > 0.5)`.
  - `task_1`: 독성 유형 **softmax** → `TYPE_NAMES` 중 argmax (`toxicity_type`, `toxicity_type_confidence`).
  - `task_2`: 신경독성 서브타입 softmax → `NEURO_NAMES` (`neurotoxicity_type`, `neurotoxicity_confidence`).
  - `task_3`: **회귀** 스칼라 `hc50` (스크립트상 변수명; UI “HC50” 등과 연결).

### C.3 비활성

- 환경변수 **`SKIP_PEPADMET=1`**: 병합 생략.
- repo/conda 실패 시 `pepadmet.available: false` + `error` 문자열.

---

## D. Pharmacological Properties (13+ 방법, 서열 기반)

**엔드포인트**: `POST /api/pharmacology/batch` → `backend/pharmacology.py` → **`AG_src/pipeline/pharma_properties.PharmaProperties`** (가능 시; 실패 시 폴백).

**이황화(Cys)**: 짝수 개 Cys면 **순차 짝지음**(첫↔끝 …). SST-14에서는 0-based index 2·13 등 → **등전점·전하 프로파일에서 해당 Cys는 이온화 제외**.

아래 표는 **정상적으로 PharmaProperties가 로드될 때**의 정의이다.

| UI / 필드 | 정의·출처 (요약) |
|-----------|------------------|
| **GRAVY** | Kyte–Doolittle 평균: `sum(KD)/n` (`pharma_properties.calculate_gravy`). |
| **Boman Index** | Radzicka–Wolfenden 친수성 값 평균; 문헌상 &gt;2.48이면 단백질 결합 경향 높음 (`calculate_boman_index`). |
| **Instability Index** | Guruprasad et al. DIWV: 인접 이펩티드에 가중치 합 × `10/n` (`calculate_instability_index`). **&lt;40 → stable** (UI·`instability_classification`). |
| **Aliphatic Index** | Ikai: A,V,I,L 비율 기반 `x_a + 2.9*x_v + 3.9*(x_i+x_l)` (`calculate_aliphatic_index`). |
| **pI** | Lehninger 계열 pKa로 **순전하=0**이 되는 pH 이분 탐색; SS 결합 Cys는 제외 (`calculate_pi`). |
| **Molecular Weight** | 잔기 평균 질량 합 − (n−1)×H₂O − n_SS×2.016 등 (`calculate_mw`). UI: average / monoisotopic. |
| **Extinction ε₂₈₀** | Trp/Tyr 및 이황화 보정 (`calculate_extinction_coefficient`); SS/환원 형 둘 다 반환. |
| **N-end Rule** | N말단 잔기별 반감기 테이블(`NEND_HALFLIFE`) (`calculate_nend_rule_halflife`). |
| **Hydrophobic Moment** | Eisenberg 스케일 + 각도(기본 100°) 슬라이딩 윈도우에서 최대 모멘트 (`calculate_hydrophobic_moment`). |
| **Wimley–White** | 잔기별 water→interface ΔG 합·평균 (`calculate_wimley_white`); 총합 부호로 membrane/aqueous 해석. |
| **Charge pH 7.4 vs 6.5** | `_charge_at_ph` (Henderson–Hasselbalch, SS Cys 제외). **Tumor selectivity** = `charge_at_ph65 - charge_at_ph74` (`charge_ph_profile`). |
| **Protease sites** | 키모트립신/트립신/NEP/DPP-IV 규칙 + **pepsin**은 `pharmacology.protease_cleavage_sites` 전용 규칙. `total_sites`는 열거 규칙 합산. **주의**: `PharmaProperties.count_protease_sites`에는 pepsin이 없어, **파이프라인 manifest·클러스터 입력**의 `protease_sites.total`과 **Pharmacology API**의 `total_sites` 숫자가 다를 수 있음. |
| **BLOSUM62** | 참조(기본 SST-14) 대비 위치별 치환 점수 합·리스트 (`calculate_blosum62_score` / pharmacology 래퍼). |
| **Metal coordination** | H,C,D,E,M 잔기 위치·금속 선호 — **pharmacology** 래퍼는 `n_strong`, `chelator_interference_risk` 포함. **PharmaProperties `analyze_metal_coordination`** 는 `residues`·`total_coordinating` 중심으로 **`n_strong` 없음**. |
| **Radiolysis susceptibility** | M,W,C,H,Y,F 등에 경험적 가중치 합; FWKT 구간의 취약 잔기 강조 (`calculate_radiolysis_susceptibility`). |

### D.1 ADMET 전하 vs Pharmacology 전하 (혼동 방지)

- **ADMET `net_charge_ph74`**: 잔기 카운트 + N/C 말단 고정 항.
- **Pharmacology `charge_at_ph74`**: pKa·HH로 측쇄·말단 기여 — **소수 자리까지 다를 수 있음**.

---

## E. Cluster A–E (결정적 규칙)

**모듈**: `pyrosetta_flow/cluster_report.py` — `classify_cluster`, `batch_classify`.  
**우선순위**: A &gt; B &gt; C &gt; D &gt; E (먼저 **모든** 조건을 만족하는 최상위 클러스터 하나만 부여, 나머지는 E).

### E.1 Cluster A — High Affinity Core (`_criteria_a`)

| 조건 키 | 코드 판정 |
|---------|-----------|
| `ddG_lte_minus8` | `ddG ≤ -8.0` (NaN 아님) |
| `clash_lte_5` | `clash_score ≤ 5` |
| `pLDDT_gte_75` | pLDDT가 **유효하고 &gt;0**일 때만 `≥ 75` 요구; **없으면 이 조건은 True**(벌점 없음) |
| `pLDDT_available` | pLDDT가 유효 숫자이고 &gt;0 |
| `fwkt_contact` | `structural_rules` 내 **FWKT pharmacophore** (잔기 7–10이 `FWKT`) `pass` |

**구현 주의**: `classify_cluster`는 `if all(crit_a.values())` 로 판정하므로 **`pLDDT_available`가 True여야** A에 들어갈 수 있다. 즉 **ESMFold 등으로 pLDDT가 없으면** PyRosetta-only 실행에서 **Cluster A는 사실상 배제**될 수 있다.

### E.2 Cluster B — Selectivity (`_criteria_b`)

- `selectivity_margin ≥ 3.0` (값 없으면 NaN → 불만족).
- `ddG < -5.0` (SSTR2 결합 “있음”의 운영 정의).

### E.3 Cluster C — Stability (`_criteria_c`)

- `instability_index < 30`
- BLOSUM62 **합계 ≥ 0** (`total_score` 또는 `total_blosum62_score` 키 모두 수용).
- **프로테아제 총 점** ≤ **9** (`_SST14_PROTEASE_BASELINE`) — “native 대비 감소” 조건.

### E.4 Cluster D — Radiochemistry (`_criteria_d`)

- `-1 ≤ GRAVY ≤ 0.5`
- `|net_charge_ph74| ≤ 1` — **클러스터 입력 dict의 `net_charge_ph74`** (pharma·파이프라인이 채운 값).
- **`n_strong ≥ 1`** (`metal_coordination.n_strong`).

**데이터 소스 주의**: 파이프라인 manifest에 넣는 `PharmaProperties.calculate_all`의 `metal_coordination`은 **`n_strong` 키가 없을 수 있음**. 이 경우 **`_metal_n_strong` → 0** 이 되어 **D 조건 `chelator_site_available`이 실패**할 수 있다. 반면 **Pharmacology API** 경로의 `metal_coordination`은 `n_strong`을 채운다. **동일 후보라도 클러스터 API 입력 구성에 따라 D 적합 여부가 달라질 수 있음**.

### E.5 Cluster E

- A–D 중 어느 것도 `all(...)` 불만족 시.

---

## F. 요약 표 (UI 블록 → 소스)

| UI 블록 | 주 소스 파일 |
|---------|----------------|
| Druglikeness·MW·HBD/HBA·KD·Amphi | `backend/admet.py` `compute_admet` |
| PRRT renal | `backend/admet.py` `compute_nephrotox_risk` |
| pepADMET | `pepadmet_infer_script.py` + `pepadmet_runner.py` + `smiles_converter.py`(1차 SMILES·이황화 시도); 폴백 토폴로지는 **§C.1** |
| Pharmacology 전부 | `backend/pharmacology.py` + `AG_src/pipeline/pharma_properties.py` |
| Cluster A–E | `pyrosetta_flow/cluster_report.py` |

---

*본 문서는 구현 스냅샷 기준이며, 임계값·테이블은 코드 변경 시 함께 갱신해야 한다.*
