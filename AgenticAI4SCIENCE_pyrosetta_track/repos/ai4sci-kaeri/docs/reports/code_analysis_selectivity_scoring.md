# 코드 분석 보고서: Selectivity & Scoring 모듈

**작성일**: 2026-04-07  
**작성자**: reviewer-code (scoring-analyst)  
**대상 파일**:
- `AG_src/pipeline/step05b_selectivity.py` (584줄)
- `pyrosetta_flow/smiles_converter.py` (125줄)
- `pyrosetta_flow/gnina_rescoring.py`, `pareto_ranking.py`, `bayesian_optimizer.py`

---

## 1. `step05b_selectivity.py` — 선택성 스크리닝

### 1.1 `run_selectivity_screening()` 전체 흐름

```
candidates (List[DockingResult])
    ↓ top_k 슬라이싱 (기본 20개)
    ↓ for each candidate:
        for each off-target receptor:
            dock_against_offtarget() → ot_score
            → OffTargetDockingResult 누적
        compute_selectivity_margin() → SelectivityResult
    ↓ apply_selectivity_gate() → (passed, failed)
    ↓ Step05bOutput 반환
```

**핵심 설정 파라미터** (config의 `selectivity` 섹션):
| 파라미터 | 기본값 | 의미 |
|---------|--------|------|
| `top_k_for_selectivity` | 20 | 선택성 평가 대상 후보 수 |
| `engine` | `"diffdock"` | 도킹 엔진 |
| `selectivity_margin_min` | -2.0 | 게이트 조건: 마진 ≤ 이 값이어야 통과 |
| `offtarget_max_allowed` | -3.0 | 게이트 조건: 최강 off-target 점수 ≥ 이 값이어야 통과 |

**주의**: config 조회가 이중으로 이루어짐 (`sel_config.get(...)` + `config.get(...)`). 중복이나 우선순위 혼선 가능성 있음.

---

### 1.2 `dock_against_offtarget()` — Production vs Estimation 모드

| 조건 | 모드 |
|------|------|
| `receptor_pdb` 존재 **AND** `sstr2_complex_pdb` 존재 | **Production**: `_run_offtarget_pyrosetta()` 호출 |
| 위 조건 불충족 또는 PyRosetta 실패 | **Estimation**: Gaussian noise 기반 추정 |

**Estimation 모드 수식**:
```
pair_hash = hash((candidate_pdb, receptor_pdb, seed)) % 2^32
offset ~ Normal(loc=noise_std, scale=noise_std/2)
estimated_score = base_score + |offset|
```
- `base_score` = `on_target_score` (없으면 -5.0)
- `noise_std` = 2.0 (기본값)
- **항상 양수 offset**이 더해짐 → off-target은 on-target보다 항상 약하게 결합하는 것으로 추정. 이는 **보수적 가정**이나 실제 교차 반응성을 과소평가할 수 있음.

---

### 1.3 `compute_selectivity_margin()` 수식

```
worst_receptor = argmin(offtarget_scores)     # 가장 강하게 결합하는 off-target
worst_score = offtarget_scores[worst_receptor]
selectivity_margin = sstr2_score - worst_score
```

**해석** (lower = stronger binding 규약):
- `margin < 0`: SSTR2가 off-target보다 강하게 결합 → 좋음
- `margin > 0`: off-target이 SSTR2보다 강하게 결합 → 나쁨

**주의**: docstring에 `offtarget_max_score`라고 명명하지만, 실제로는 **가장 작은(가장 강한) off-target 점수**다. 필드명이 의미를 반대로 암시할 수 있음 (`max` = 가장 큰 수 ≠ 가장 강한 결합).

---

### 1.4 `apply_selectivity_gate()` 조건

```python
passed = (margin <= margin_min) AND (worst_score >= offtarget_max_allowed)
```

- 조건 1: `margin ≤ -2.0` → SSTR2가 off-target보다 최소 2.0 kcal/mol 이상 강하게 결합
- 조건 2: `worst_score ≥ -3.0` → 가장 강한 off-target의 결합이 -3.0 이상 (약한 결합)

**단, 이미 `compute_selectivity_margin()`에서 `passed` 필드가 계산되어 있으므로**, `apply_selectivity_gate()`는 단순히 `r.passed`를 기준으로 분류만 수행한다. 파라미터를 다시 받지만 실제로 재계산하지 않는 불일치가 있음 — **이중 게이트 파라미터 적용 문제**.

---

### 1.5 `_run_offtarget_pyrosetta()` subprocess 호출

```python
cmd = ["conda", "run", "-n", conda_env, "python", str(script),
       "--sstr2-complex", sstr2_complex_pdb,
       "--offtarget-receptor", receptor_pdb,
       "--output", str(out_pdb)]
subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
```

- stdout에서 JSON 파싱: `result["ddg"]` 반환
- 실패 시 `RuntimeError` → 호출부에서 `except Exception`으로 캐치 후 estimation 모드 fallback
- **보안 이슈 없음**: 인자가 모두 Path 객체 or 고정 플래그. 단, `sstr2_complex_pdb`/`receptor_pdb`가 사용자 입력이라면 경로 검증 필요.
- `out_pdb` 파일이 생성되지만 파이프라인에서 직접 사용되지 않는 것으로 보임 → 임시파일 정리 로직 없음.

---

### 1.6 `_convert_cif_to_pdb()` BioPython 로직

```python
MMCIFParser(QUIET=True).get_structure(stem, cif_path)
→ ChainSelect (chain 필터) or Select (전체)
→ PDBIO.save(pdb_path, selector)
```

- `QUIET=True`로 파싱 경고 억제 — 데이터 품질 문제가 조용히 넘어갈 수 있음
- 클래스 내 클래스 정의 (`ChainSelect`)는 가독성 저하 요소 (매 호출마다 재정의)
- 반환값: 작성한 PDB 경로 (str)

---

### 1.7 `load_offtarget_receptors_from_config()` 설정 파싱

```
config["off_target_receptors"]
    for each rec:
        pdb_source != "local" → {name, pdb_path=None, chain}
        pdb_source == "local":
            local_path → 절대경로 변환
            .cif → _convert_cif_to_pdb() (pdb_output_dir or tempfile)
            .pdb → 직접 사용
        → {name, pdb_path, chain}
```

- `tempfile.NamedTemporaryFile(delete=False)` 사용 → 프로세스 종료 후에도 파일 잔류. 명시적 정리 로직 필요.
- `pdb_source == "rcsb"` 케이스는 처리 로직 없음 (단순 `None` 처리) — RCSB API 다운로드 미구현 상태.

---

## 2. `smiles_converter.py` — 펩타이드 SMILES 변환

### 2.1 `sequence_to_smiles()` 전체 흐름

```
sequence (str)
    ↓ Chem.MolFromSequence(seq)  # RDKit 내장 펩타이드 파서
    ↓ SS bond 위치 결정:
        - 명시적 ss_bond_positions: 직접 사용
        - None: Cys 위치 자동탐지 (첫 번째 + 마지막 Cys)
    ↓ SG 원자 탐색 + AddBond(SINGLE)
    ↓ RemoveHs + SanitizeMol
    ↓ MolToSmiles()
    → canonical SMILES (str) or None
```

---

### 2.2 SG atom 탐색 → AddBond → RemoveHs

```python
for atom in mol.GetAtoms():
    ri = atom.GetPDBResidueInfo()
    if ri is not None:
        res_idx = ri.GetResidueNumber() - 1
        atom_name = ri.GetName().strip()
        if res_idx in (pos1_0idx, pos2_0idx) and atom_name == "SG":
            sg_atoms.append(atom.GetIdx())

emol = Chem.RWMol(mol)
emol.AddBond(sg_atoms[0], sg_atoms[1], Chem.BondType.SINGLE)
mol = emol.GetMol()
mol = Chem.RemoveHs(mol)
Chem.SanitizeMol(mol)
```

**주요 특징**:
- `Chem.MolFromSequence()`는 RDKit가 PDB residue info를 원자에 붙임 → `GetPDBResidueInfo()`로 잔기 번호 접근 가능
- **잠재적 문제**: `GetResidueNumber()`가 1-based인지 0-based인지 RDKit 버전에 따라 다를 수 있음. 현재 코드는 `-1` 보정을 적용.
- SS 결합 형성 후 `RemoveHs()`만 호출 — 실제로 S-H 수소가 명시적으로 제거되는지는 RDKit의 Hs 표현 방식에 의존. `SanitizeMol()` 성공 여부가 유일한 검증.
- 실패 시 예외를 조용히 catch하고 선형 SMILES로 폴백 → SS 결합 없는 SMILES가 반환될 수 있음 (호출자가 알기 어려움).

**개선 제안**: SS bond 형성 성공 여부를 명시적으로 반환하거나 플래그를 추가해야 함.

---

## 3. Scoring 모듈 — GNINA / Pareto / Bayesian

### 3.1 `gnina_rescoring.py` — GNINA CLI 호출

**`gnina_rescore()` 흐름**:
```
complex_pdb
    ↓ split_receptor_peptide() → (rec_tmp.pdb, pep_tmp.pdb)
    ↓ subprocess: gnina --receptor rec --ligand pep --score_only
    ↓ _parse_gnina_output(stdout) → {cnn_score, cnn_affinity, vina_score}
    ↓ finally: tmp파일 삭제
```

**Dry-run fallback**: `gnina` 바이너리 없으면 `{0.0, 0.0, 0.0, gnina_dry_run: 1.0}` 반환.

**`_parse_gnina_output()` 파싱 로직**:
```
stdout 줄 탐색 → "CNNscore" 포함 줄 찾기 (header_idx)
header_idx + 1 줄에서 tokens[0], [1], [2] 파싱
→ {gnina_cnn_score, gnina_cnn_affinity, gnina_vina_score}
```
- 헤더 미발견 또는 토큰 부족 시 `float("nan")` 반환
- GNINA stdout 포맷 변경에 취약 (컬럼 순서 의존)

---

### 3.2 `exponential_rank_consensus()` ECR 수식

$$ECR_i = \sum_{k} \exp\left(-\frac{rank_{i,k}}{N}\right)$$

- $N$: 후보 전체 수
- $rank_{i,k}$: 후보 $i$의 $k$번째 점수 항목에서의 1-based 순위
- 낮은 점수 = 좋은 결합 → 오름차순 정렬 후 순위 부여 (1 = 최고)
- NaN 값은 `float("inf")`로 대체 → 최하위 순위 부여

**특징**:
- ECR 범위: $(0, K]$ (K = score_keys 수)
- 정규화 없음 — score key 수가 달라지면 ECR 절대값 변동
- 동일 순위(tie) 미처리: 정렬 시 Python의 stable sort 의존

---

### 3.3 `pareto_ranking.py` — pymoo NSGA-II

**목적 함수 (모두 최소화로 통일)**:
| 원본 목표 | 변환 방식 |
|---------|---------|
| ddG (낮을수록 강한 결합) | 그대로 |
| stability (높을수록 좋음) | 부호 반전 `-stability` |
| druggability (높을수록 좋음) | 부호 반전 `-druggability` |
| diversity (높을수록 좋음) | 부호 반전 `-diversity` |

**제약 조건**:
```python
G = [hard_violations, clash_score - clash_threshold]
cv = sum(max(G_i, 0))  # 전체 위반 합계
```

**`_penalise_infeasible()`**: 비가능해(infeasible) 후보를 feasible 프론트 뒤로 relegation. 위반 합계 기준 오름차순 정렬.

**`pareto_rank_candidates()` 반환**: 입력 dict를 **in-place** 수정 (`pareto_rank`, `crowding_distance` 추가). 이는 원본 데이터 변조 위험 — 복사본 반환이 더 안전.

**front 크기 ≤ 2일 때**: pymoo의 crowding distance가 경계점을 `inf`로 설정하는 대신, 직접 `np.full(..., math.inf)` 처리. pymoo API 변경 방어 코드.

---

### 3.4 `bayesian_optimizer.py` — GP surrogate + UCB/qNEHVI

#### OneHotEmbedder vs ESM2Embedder

| 항목 | OneHotEmbedder | ESM2Embedder |
|------|---------------|-------------|
| 의존성 | numpy only | transformers + torch |
| 출력 차원 | `max_len × 20` | ESM-2 hidden dim (예: 320) |
| 특징 | 순서 정보 없음, 단순 | 진화적/구조적 정보 포함 |
| 실패 가능성 | 없음 | ImportError, VRAM 부족 |
| mean-pool 방식 | N/A | `last_hidden_state[1:-1]` (CLS/EOS 제외) |

#### BayesianPeptideOptimizer 구조

```
fit(candidates):
    embed_batch(sequences) → X (n, d)
    extract objectives → Y (n, m)
    부호 반전 (minimize 목표)
    → _fit_botorch (ModelListGP) OR _fit_fallback (_FallbackGP)

suggest(n, reference_seq, allowed_positions):
    _enumerate_mutations() → 단일점 돌연변이 전체 열거
    _compute_acquisition() → [BoTorch product-of-improvements | UCB 합]
    상위 n개 반환
```

#### BoTorch Acquisition (production)

```python
improvement = posterior.mean - ref_point
improvement = clamp(improvement, min=0)
acq = improvement.prod(dim=-1)  # product-of-improvements
```

이는 **qNEHVI의 근사 proxy**임. 진정한 qNEHVI는 Monte Carlo 샘플링을 사용하나, 대규모 후보 열거에서는 계산 비용이 과도하여 이 근사를 채택.

#### Fallback GP (numpy-only)

```
UCB_k = mean_k + β × sqrt(var_k + ε)
acq = Σ UCB_k
```
- β = 2.0 (고정)
- RBF kernel: `exp(-0.5 * ||x1-x2||² / l²)`
- 다목적이지만 scalarization 없이 단순 합산 → Pareto 최적성 보장 없음

---

## 4. 종합 품질 평가

### 강점

| 항목 | 평가 |
|------|------|
| Fallback 전략 | 모든 외부 도구(GNINA, PyRosetta, BoTorch)에 graceful fallback 구현 |
| 보안 | subprocess 인자가 고정 플래그 기반, `_safe_filename_component()` 경로 검증 |
| 타입 힌팅 | 전반적으로 일관된 타입 힌트 사용 |
| 모듈 분리 | 스코어링 로직이 명확히 단일 파일에 캡슐화됨 |
| Dry-run | 바이너리 없어도 파이프라인 전체 실행 가능 |

### 이슈 및 개선 필요사항

| 우선순위 | 위치 | 이슈 |
|---------|------|------|
| 높음 | `apply_selectivity_gate()` | 이미 계산된 `r.passed`만 사용 → 파라미터 재적용 불일치 |
| 높음 | `pareto_rank_candidates()` | dict in-place 수정 → 예기치 않은 원본 데이터 변조 |
| 중간 | `sequence_to_smiles()` | SS bond 형성 실패 시 조용히 선형 SMILES 반환 (감지 어려움) |
| 중간 | `load_offtarget_receptors_from_config()` | `tempfile.NamedTemporaryFile(delete=False)` 잔류 파일 미정리 |
| 중간 | `SelectivityResult.offtarget_max_score` | 필드명이 의미를 역으로 암시 (max = 가장 강한 결합 = 가장 작은 수) |
| 낮음 | `_run_offtarget_pyrosetta()` | `out_pdb` 파일 생성 후 미사용 및 미정리 |
| 낮음 | `exponential_rank_consensus()` | tie 처리 없음, score_keys 수 변화 시 ECR 절대값 비교 불가 |
| 낮음 | `_acquisition_botorch()` | 주석에 "qNEHVI"라고 했으나 실제는 product-of-improvements proxy |
| 낮음 | `_convert_cif_to_pdb()` | `QUIET=True`로 데이터 품질 경고 억제 |

---

## 5. 아키텍처 메모

- **Estimation 모드**: off-target score가 항상 on-target보다 낮게(약하게) 추정됨. 초기 스크리닝에서는 허용 가능하나, 결과 해석 시 "estimation" 플래그가 필요.
- **ECR + Pareto + BO의 상호보완**: 세 모듈이 서로 독립적으로 설계되어 있으나, 파이프라인에서 어떤 순서로 적용되는지(직렬/병렬/선택적)는 `runner.py`에서 결정됨.
- **ESM-2 pseudo-perplexity 미구현**: MEMORY.md에 기재된 대로 ESMFold 가중치 미다운로드 상태. `ESM2Embedder`는 구현되어 있으나 현재 사용 불가.
