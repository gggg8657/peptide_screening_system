# 코드 분석 보고서: ADMET / pepADMET / Cluster

**작성일**: 2026-04-07  
**분석 대상**:
- `backend/admet.py`
- `pyrosetta_flow/pepadmet_infer_script.py`
- `pyrosetta_flow/pepadmet_runner.py`
- `pyrosetta_flow/pepadmet_toxicity.py`
- `pyrosetta_flow/cluster_report.py`

---

## 1. `backend/admet.py`

### 1.1 `compute_admet(sequence)` — ADMET-like 물성 계산

#### 1.1.1 분자량 (MW)

**수식**
```
MW = Σ(잔기 단량체 질량) + 18.01056 (H₂O, 말단 보정)
```

**근거**  
잔기 질량은 펩타이드 결합 형성 시 H₂O가 제거된 모노아이소토픽 값을 사용.  
H₂O 한 번 가산은 N-말단 H + C-말단 OH 복원에 해당하며 표준 관례.  
근거: **Roepstorff & Fohlman (1984)** 펩타이드 단편화 명명법 관례; 잔기 질량은 NIST/UniMod 데이터베이스와 일치.

---

#### 1.1.2 pH 7.4 순전하 (net_charge_ph74)

**수식**
```
charge = +1 × n(K,R) − 1 × n(D,E) + 0.1 × n(H)
charge += 1.0  (N-말단 NH₃⁺)
charge -= 1.0  (C-말단 COO⁻)
→ N/C 말단 상쇄, 최종적으로 사이드체인 기여만 남음
```

**근거**  
Henderson-Hasselbalch 방정식의 단순화. pKa 값 사용 없이 ±1 부울 가중치 적용.  
His의 0.1 가중치는 pKa ≈ 6.0에서 pH 7.4 시 protonation 확률의 근사 (실제 값은 ~4%).  
**한계**: 환경 의존 pKa 변이(Cys 쌍이온, Glu 매몰 시 pKa 상승 등) 미반영.  
근거: **in-house 단순화 모델** (Henderson-Hasselbalch 완전 구현 아님).

---

#### 1.1.3 H-결합 공여체/수용체 수 (n_hbd, n_hba)

**수식**
```
n_hbd = Σ(사이드체인 NH/OH 기여) + length  ← 각 잔기 backbone NH 1개 가산
n_hba = Σ(사이드체인 C=O/OH/COO⁻ 기여) + length  ← 각 잔기 backbone C=O 1개 가산
```

**사이드체인 공여체 기여표**
| AA | 기여 |
|----|------|
| K  | 1 (ε-NH₃⁺) |
| R  | 3 (3 × NH) |
| H  | 1 (NH) |
| N,Q | 2 (NH₂) |
| S,T | 1 (OH) |
| W  | 1 (NH) |
| Y  | 1 (OH) |

**한계**:
1. Pro은 backbone NH 없음에도 `+length` 포함 → n_hbd 과대 계산.
2. 이황화 결합 형성 시 Cys–SH HBD 기여 미반영.
3. 하전 상태 미반영 (Asp/Glu는 수용체 수가 산/염기 형태에 따라 달라짐).

근거: **Lipinski Rule of 5 (1997)** 방법론의 변형; 펩타이드 맥락 적용은 **in-house**.

---

#### 1.1.4 소수성 (hydrophobicity)

**수식**
```
hydrophobicity = mean(KD_i)  for i in sequence
```

**근거**: **Kyte & Doolittle (1982)** *J Mol Biol* 157:105-132.  
값 범위: −4.5 (Arg) ~ +4.5 (Ile).

---

#### 1.1.5 양친매성 지수 (amphipathicity_index)

**수식**
```
amphipathicity_index = Var(KD) = (1/n) × Σ(KD_i − mean(KD))²
```

**근거**: **in-house 정의**. 공식 Eisenberg 소수성 모멘트(helical wheel 기반 벡터합)와 다름.  
이 코드의 `amphipathicity_index`는 KD 분산(variance)이며, 실제 물리적 양친매성과의 상관관계는 부분적임.

**주요 문제점**:
- Eisenberg et al. (1982) 소수성 모멘트 `<μH>` 수식은 아래와 같음:
  ```
  <μH> = (1/n) × |Σ H_i × exp(i×δ×i)|
  δ = 100° (α-helix), 180° (β-strand)
  ```
  코드의 분산 계산은 이 회전 각도 기반 벡터합을 구현하지 않아 **명칭 불일치** 발생.

---

#### 1.1.6 Druglikeness Score (0-100, peptide-specific)

**수식**: 4개 이진 규칙 × 25점 = 최대 100점

| 규칙 | 조건 | 근거 |
|------|------|------|
| mw_range | 1200–2000 Da | in-house (14-mer 기준) |
| charge | \|net_charge\| ≤ 3 | in-house |
| hydrophobicity | −2.0 ≤ KD_mean ≤ +1.0 | in-house |
| no_repeats | 3+ 연속 동일 AA 없음 | in-house |

**한계**:
- 4개 규칙이 모두 동일 가중치(25점)를 가짐 → MW와 서열 복잡도가 동등 취급.
- 경계값(1200, 2000 Da)은 14-mer에 특화; 다른 길이 후보군에는 부적절.
- 전통적 Lipinski 규칙(MW < 500, HBA < 10, HBD < 5, logP < 5)은 경구 소분자용으로 여기서 직접 적용 안 됨 → "druglikeness"라는 명칭이 오해 소지.

---

### 1.2 `compute_nephrotox_risk(sequence)` — 신독성 위험 점수

**수식**
```
renal_risk_score = min(100, (n_K + n_R) × 20 + max(0, net_charge) × 15)
```

**위험 등급**
| 점수 범위 | 등급 |
|-----------|------|
| < 30      | Low |
| 30–60     | Moderate |
| > 60      | High |

**근거**:  
양이온성 잔기(Lys, Arg)가 신세뇨관 재흡수를 촉진한다는 관찰에 기반.  
메도독성 키네틱스는 **Bodei et al. (2011)** *Eur J Nucl Med Mol Imaging* 38:2125-2135 (PRRT 신독성 검토)에서 양이온성 공동주입(아미노산 용액, Gelofusine) 필요성이 확립됨.  
계수(×20, ×15)는 **in-house 추정치** — 문헌 기반 정량 파라미터 아님.

**레퍼런스 포인트**: DOTATATE (1 Lys, net_charge ≈ +1) → score ≈ 20+15 = 35 (Moderate).  
코드 docstring에는 "score ~25 (Low)"라 명시했으나 실제 계산값은 35 (Moderate) — **주석-수식 불일치** 존재.

**한계**:
- His는 양이온 카운트(n_his)에는 포함되지만 리스크 공식에서는 제외됨 → `cationic_residues` 필드와 공식 사이 불일치.
- 선형 스케일 가정: 실제 신독성은 포화 가능성 있음.
- pH 7.4 외 환경(내소체 산성 환경 등) 미반영.

---

### 1.3 데이터 흐름 요약

```
sequence (str)
    ↓ compute_admet()
    ├── mw, net_charge_ph74, n_hbd, n_hba
    ├── hydrophobicity (KD mean)
    ├── amphipathicity_index (KD variance)
    └── druglikeness_score (0-100) + breakdown

    ↓ compute_nephrotox_risk()
    ├── n_lys, n_arg, n_his, cationic_residues
    ├── net_charge
    ├── renal_risk_score (0-100)
    └── risk_level (Low/Moderate/High) + warning

    ↓ compute_admet_full()
    └── {sequence, admet:{...}, nephrotox:{...}}

    ↓ merge_pepadmet_into_admet_results()  (SKIP_PEPADMET=1이면 bypass)
    └── results[i]["pepadmet"] 병합
```

---

## 2. pepADMET 모듈 (3파일)

### 2.1 모델 개요

**원저 논문**: Zhu et al. (2026) *J Chem Inf Model* 66:936-946  
**GitHub**: `ifyoungnet/pepADMET`  
**모델명**: `toxicity_early_stop.pth` — MLR-GAT (Multi-scale Graph Attention + MLP)  
**아키텍처**: MGA (MY_GNN.MGA) — RGCN + attention + 4 task heads

---

### 2.2 MGA forward pass 흐름

```
SMILES (str)
    ↓ Chem.MolFromSmiles()
    ↓ Chem.AddHs()           ← 수소 명시화
    ↓ atom_features(atom)    ← 40차원 원자 특성 벡터
    ↓ etype_features(bond)   ← 결합 유형 정수
    ↓ dgl.DGLGraph()         ← src/dst 양방향 엣지
       ndata["atom"] = (N_atoms × 40)
       edata["etype"] = (N_edges,)
    ↓ dgl.batch([g])         ← 배치화

sequence + smiles_used
    ↓ build_descriptor_tensor()
       └── calculate_descriptors((smiles, seq)) → dict
           ├── sorted by key
           ├── float 변환 (SMILES, SEQUENCE 키 제외)
           ├── n < 2133 → zero-padding
           └── n > 2133 → truncation[:2133]
       → desc: (1 × 2133) float32 tensor

model(bg, bg.ndata["atom"], bg.edata["etype"], desc)
    ↓ MGA forward (RGCN layers [64,64] → attention → FPN)
    ↓ 4 task heads:
        task_0: binary toxicity logit (scalar)
        task_1: 6-class toxicity type logit (1 × 6)
        task_2: 4-class neurotoxicity type logit (1 × 4)
        task_3: HC50 regression (scalar)

후처리:
    bp = sigmoid(task_0)          → binary toxicity probability
    tp = softmax(task_1)[0]       → 6-class 확률
    np_ = softmax(task_2)[0]      → 4-class 확률
    hc = task_3.item()            → HC50 (단위 미명시, 아마 μg/mL)
```

**4 task heads 출력 형식**
| 출력 키 | 타입 | 해석 |
|---------|------|------|
| binary_toxicity | float [0,1] | sigmoid(task_0) |
| is_toxic | bool | bp > 0.5 |
| toxicity_type | str | argmax(tp) → TYPE_NAMES |
| toxicity_type_confidence | float | max(tp) |
| neurotoxicity_type | str | argmax(np_) → NEURO_NAMES |
| neurotoxicity_confidence | float | max(np_) |
| hc50 | float | regression 원값 |

**클래스 레이블**
```python
TYPE_NAMES = ["cytolysis", "GPCR_toxin", "neurotoxin",
              "cytotoxicity", "hemostasis", "hemolysis"]
NEURO_NAMES = ["AChR_inhibitor", "Ca_inhibitor", "K_inhibitor", "Na_inhibitor"]
```

---

### 2.3 `build_descriptor_tensor()` 상세

**수식/흐름**
```
calculate_descriptors((smiles, seq))
    → dict { feature_name: numeric_value, ... }
    → "Error" 키 존재 시 → zeros(1, 2133) 반환
    → 숫자형 key만 필터 (SMILES, SEQUENCE 제외)
    → sorted(fp.items()) 기준 정렬
    → float 변환 리스트 (n개)
    → n < 2133: [0.0] × (2133-n) 패딩
    → n > 2133: [:2133] truncation
    → torch.tensor([feature_values], dtype=float32)
```

**2133 feature 구성**: `calculate_descriptors`는 pepADMET 원본 코드 함수로, RDKit 기반 분자 기술자(Morgan fingerprint, 물리화학 파라미터) + 서열 기반 특성을 계산.  
정확한 feature 목록은 pepADMET 논문 부록 또는 `calculate_descriptors.py` 내부 확인 필요.

**한계**:
- `sorted(fp.items())` 기반 정렬은 알파벳 순서 → 학습 시 feature 순서와 일치 여부 보장 불명확.
- truncation(n > 2133) 시 끝 feature 손실 → 어떤 descriptor가 잘리는지 로그 없음.
- 예외 시 `zeros(1,2133)` 반환 → 모델에 zero-descriptor 입력으로 추론 계속 (에러 전파 없음, 하지만 결과 신뢰성 감소).

---

### 2.4 `graph_from_sequence_linear()` 폴백 작동 조건

```
smiles_to_graph(smiles) → g = None 이면:
    ↓ graph_from_sequence_linear(seq)
        └── Chem.MolFromSequence(seq)   ← 선형 펩타이드 생성 (사이클 없음)
            ├── 실패 시: (None, None) 반환
            └── 성공 시: MolToSmiles() + graph_from_mol()
                        → (g, smi_fb) 반환

결과:
    g is not None → graph_note = "linear_sequence_fallback" 태깅
    g is None (두 경로 모두 실패) → error: "graph build failed"
```

**폴백이 발동되는 경우**:
1. SMILES가 빈 문자열이거나 None인 경우
2. 사이클릭/이황화 SMILES가 특정 RDKit 버전에서 파싱 실패하는 경우  
   (예: SST-14는 Cys3-Cys14 이황화 결합 → cyclic SMILES 복잡성)

**한계**:
- 선형 폴백 시 이황화 결합, 사이클 구조가 소실 → 그래프가 실제 분자와 다름 → 독성 예측 정확도 저하 가능.
- `graph_note`로 태깅되나 downstream 코드에서 이 플래그를 필터링하지 않음.

---

### 2.5 subprocess 격리 아키텍처 (`pepadmet_runner.py`)

```
bio-tools conda env (현재)
    ↓ predict_toxicity_batch(sequences, smiles_list)
        ├── SMILES 변환: smiles_converter.sequence_to_smiles()  (ImportError 시 "" 사용)
        ├── input_json = JSON 직렬화
        ↓ subprocess.run(["conda", "run", "--no-capture-output",
                          "-n", "pepadmet",
                          "python3", pepadmet_infer_script.py, input_json],
                         timeout=120)
            ↓ pepadmet conda env (DGL 0.4.3)
               pepadmet_infer_script.py → MGA 추론 → JSON stdout
        ↑ stdout 마지막 JSON 줄 파싱 → list[dict]

오류 처리:
    returncode != 0 → error_msg = stderr[-500:]
    TimeoutExpired → "timeout"
    JSON 없음 → "no JSON output"
```

**격리 이유**: pepADMET은 DGL 0.4.3을 요구하며 현재 bio-tools env(DGL 최신)와 호환 불가 → conda 환경 분리.

**한계**:
- conda run 오버헤드 (첫 호출 ~5-10초).
- `--no-capture-output` 사용으로 stderr 출력이 콘솔에 직접 노출.
- timeout=120초 고정 → 대용량 배치에서 타임아웃 위험.
- stdout 마지막 JSON 줄만 파싱 → 스크립트 내 print 문이 추가될 경우 취약.

---

### 2.6 `pepadmet_toxicity.py` — 레거시 API 래퍼

```
predict_toxicity(sequence, smiles=None)
    ↓ predict_toxicity_batch([sequence], [smiles])
    ↓ _normalize_runner_row(rows[0], sequence)
    → {available, model, sequence, binary_toxicity, toxicity_type,
       neurotoxicity_type, hc50, is_toxic (optional),
       toxicity_type_confidence (optional), ...}

batch_predict_toxicity(sequences, smiles_list)
    ↓ predict_toxicity_batch(sequences, smiles_list)
    ↓ [_normalize_runner_row(r, seq) for r, seq in zip(raw, sequences)]
```

`_normalize_runner_row()`는 `pepadmet_runner` 출력 dict를 레거시 API 형태로 변환.  
`smiles` 필드는 80자 초과 시 절삭 (`[:80] + "..."`).

---

## 3. `pyrosetta_flow/cluster_report.py`

### 3.1 클러스터 기준 상세

#### Cluster A — High Affinity Core (우선순위 1)

| 기준 | 코드 조건 | 임계값 |
|------|----------|--------|
| ddG_lte_minus8 | `ddG <= -8.0` | ≤ −8.0 kcal/mol |
| clash_lte_5 | `clash_score <= 5.0` | ≤ 5 |
| pLDDT_gte_75 | `pLDDT >= 75.0` if available | ≥ 75 |
| fwkt_contact | `structural_rules.rules.fwkt_pharmacophore.pass == True` | PASS |

**pLDDT skip 로직**:
```python
plddt_available = (not isnan(plddt_val)) and plddt_val > 0
plddt_ok = plddt_val >= 75.0 if plddt_available else True
```
pLDDT 값이 None, 0, NaN이면 → `pLDDT_available=False`, `pLDDT_ok=True` (패널티 없음)  
→ PyRosetta-only 모드(ESMFold 미사용) 에서도 A 클러스터 진입 가능.

**참고**: `_criteria_a` dict 내 `pLDDT_available`은 정보 플래그 (`all(crit_a.values())` 계산에 포함됨).  
→ `pLDDT_available=False` + `pLDDT_ok=True`면 pLDDT 기준 통과로 간주 — 의도된 설계.

---

#### Cluster B — Selectivity-Optimised (우선순위 2)

| 기준 | 코드 조건 | 임계값 |
|------|----------|--------|
| selectivity_margin_gte_3 | `selectivity_margin >= 3.0` | ≥ 3.0 |
| ddG_binding_present | `ddG < -5.0` | < −5.0 kcal/mol |

`selectivity_margin`은 SSTR2 ddG와 off-target ddG의 차이 (출처: runner 파이프라인).  
"SSTR2 ddG low"를 `ddG < -5.0`으로 운영화 — 주석에 명시.

---

#### Cluster C — Stability-Enhanced (우선순위 3)

| 기준 | 코드 조건 | 임계값 |
|------|----------|--------|
| instability_lt_30 | `instability_index < 30.0` | < 30 |
| blosum62_nonnegative | `blosum62_total >= 0` | ≥ 0 |
| protease_sites_reduced | `total_sites <= 9` | ≤ 9 (SST-14 기준선) |

`_SST14_PROTEASE_BASELINE = 9` — SST-14 native의 프로테아제 절단 사이트 수.  
BLOSUM62 총점은 두 필드명 모두 지원: `total_blosum62_score` (pharmacology.py) 또는 `total_score` (pharma_properties.py).

---

#### Cluster D — Radiochemistry-Optimal (우선순위 4)

| 기준 | 코드 조건 | 임계값 |
|------|----------|--------|
| gravy_in_range | `-1.0 <= gravy <= 0.5` | GRAVY ∈ [−1.0, +0.5] |
| net_charge_low | `abs(net_charge_ph74) <= 1.0` | \|charge\| ≤ 1 |
| chelator_site_available | `metal_coordination.n_strong >= 1` | n_strong ≥ 1 |

`gravy` = Grand Average of Hydropathicity (Kyte-Doolittle 평균, `hydrophobicity`와 동일 계산).  
`n_strong` = 강한 킬레이션 잔기(Cys, His, Asp, Glu 등) 수.  
**방사의약품 특화 클러스터**: ⁶⁸Ga/¹⁷⁷Lu 표지를 위한 GRAVY 범위와 하전 상태 최적화.

---

#### Cluster E — Exploratory Candidates (폴백)

A~D 모두 불충족 시 할당. 별도 기준 없음.

---

### 3.2 `batch_classify()` 통계 출력

```python
batch_classify(candidates) → {
    "results": [{"id": str, "classification": classify_cluster_output}, ...],
    "statistics": {
        "total": int,
        "distribution": {
            "A": {"count": int, "percent": float, "name": str},
            "B": ..., "C": ..., "D": ..., "E": ...,
        }
    },
    "cluster_groups": {
        "A": [id_1, id_2, ...],
        "B": [...], ...
    }
}
```

- `percent` = round(100 × count / total, 1); total=0 시 0.0 반환.
- `id`는 `candidate["name"]` → `candidate["sequence"]` → `"candidate_{idx}"` 순 fallback.
- `criteria_met`에는 불충족 클러스터의 기준도 포함 (A는 항상 포함, B~D는 우선순위에 따라 누적).

---

### 3.3 우선순위 판정 로직

```
classify_cluster(candidate):
    crit_a = _criteria_a()
    if all(crit_a.values()) → return A
    crit_b = _criteria_b()
    if all(crit_b.values()) → return B
    crit_c = _criteria_c()
    if all(crit_c.values()) → return C
    crit_d = _criteria_d()
    if all(crit_d.values()) → return D
    → return E
```

**주의**: `all(crit_a.values())`에는 `pLDDT_available`(bool) 포함.  
→ `pLDDT_available=False`이고 `pLDDT_ok=True`면 `all()` 통과 — 의도된 skip 설계.

---

## 4. 전체 한계 요약

| 모듈 | 주요 한계 |
|------|-----------|
| admet.py — amphipathicity_index | KD 분산 계산 — Eisenberg 소수성 모멘트(벡터합)가 아님. 명칭 불일치. |
| admet.py — n_hbd | Pro 포함 전체 잔기에 backbone NH 가산 → Pro는 backbone NH 없어 과대계산. |
| admet.py — renal_risk_score | 계수(×20, ×15) in-house 추정치; His가 cationic_residues에는 포함되나 공식에서는 제외. Docstring의 DOTATATE 예시(score ~25)와 실제 계산값(35) 불일치. |
| admet.py — druglikeness_score | "druglikeness"라는 명칭이 Lipinski Rule과 무관한 in-house 4규칙 점수에 부적절. |
| pepadmet_infer_script.py — descriptor 정렬 | `sorted(fp.items())` 알파벳 순 → 학습 시 feature 순서와 일치 보장 불명확. |
| pepadmet_infer_script.py — linear fallback | 이황화/사이클 구조 소실 → 독성 예측 신뢰도 저하; downstream에서 `graph_note` 미필터링. |
| pepadmet_infer_script.py — HC50 단위 | task_3 HC50 단위 미명시 (μg/mL 추정, 논문 확인 필요). |
| pepadmet_runner.py — timeout | 120초 고정 → 대용량 배치 위험; conda run 오버헤드 미고려. |
| cluster_report.py — pLDDT_available | `all(crit_a.values())`에 `pLDDT_available` bool 포함됨 — False면 전체 A 기준 불충족. 설계 의도 맞으나 주석 부재. |
| cluster_report.py — selectivity_margin 소스 | `selectivity_margin` 필드 생성 위치(runner.py) 명시 없음 → 필드 누락 시 B 자동 탈락. |

---

## 5. 참고문헌

1. **Kyte & Doolittle (1982)** "A simple method for displaying the hydropathic character of a protein." *J Mol Biol* 157:105-132.
2. **Lipinski et al. (1997)** "Experimental and computational approaches to estimate solubility and permeability." *Adv Drug Deliv Rev* 23:3-25.
3. **Bodei et al. (2011)** "Peptide receptor radionuclide therapy with 177Lu-DOTATATE." *Eur J Nucl Med Mol Imaging* 38:2125-2135.
4. **Roepstorff & Fohlman (1984)** "Proposal for a common nomenclature for sequence ions in mass spectra of peptides." *Biomed Mass Spectrom* 11:601.
5. **Zhu et al. (2026)** "pepADMET: A graph-based deep learning model for peptide ADMET prediction." *J Chem Inf Model* 66:936-946.
