# Peptide Stability / Half-life In-Silico Predictor 도구 인벤토리
## SSTR2 방사성의약품 후보 — 즉시 사용 가능한 코드/라이브러리 종합 조사

> **작성일**: 2026-05-12  
> **작성자**: researcher (S6, Task id=15)  
> **버전**: 1.0  
> **조사 범위**: Python 오픈소스 라이브러리, web-based predictor, 프로젝트 내장 코드  
> **참조 파일**:  
> - `pipeline_local/scripts/pharmacology_guards.py` (H-01~H-06 가드)  
> - `pipeline_local/steps/step08_stability.py` (휴리스틱 stability ranker)  
> - `pipeline_local/backend/routers/admet.py` (ADMET 배치 API)  
> - `docs/wetlab/stability_modifications_review.md` (S3-T12 chemistry 리뷰)  
> - `docs/wetlab/sst_analog_stability_literature.md` (S5-T14 문헌 리뷰)

---

## ⚠️ 출력 해석 주의사항

본 문서의 in-silico 예측값은 **휴리스틱 ranking score** 또는 **QSAR 모델 출력**이다.  
실 in-vitro serum stability assay (37°C 인간 혈청) 측정값을 대체하지 않는다.  
`step08_stability.py H-06 원칙`: "계산 불가능을 계산 가능한 척 하지 말 것" — 모든 출력에 `(heuristic)` 표기 의무.

---

## 1. 도구 인벤토리 — 16개 도구 종합표

### 1.1 Python 오픈소스 라이브러리 (pip/conda)

| 도구 | GitHub / URL | pip install | 오프라인 | NCAA 지원 | KAERI 가용 | 주용도 |
|------|-------------|-------------|---------|----------|----------|-------|
| **Biopython ProtParam** | biopython.org | `pip install biopython` | ✅ | ❌ 표준 20종 | ✅ bio-tools | MW, pI, GRAVY, Instability Index |
| **peptides.py** | github.com/althonos/peptides.py | `pip install peptides` | ✅ | ❌ | ⚠️ 미설치 | Boman, 전하, aliphatic index |
| **modlAMP** | github.com/alexarnimueller/modlAMP | `pip install modlamp` | ✅ (코어) | ❌ | ⚠️ 미확인 | AMP 설계, 200+ descriptor |
| **pepADMET** | github.com/ifyoungnet/pepADMET | GitHub 클론 + .pth | 부분 ✅ | ✅ D-aa, cyclic, PTM | ⚠️ 클론 필요 | 29개 ADMET endpoint |
| **RDKit** | rdkit.org | `conda install rdkit` | ✅ | ✅ SMILES 기반 | ⚠️ 미확인 | SMILES 기반 molecular property |

### 1.2 Protease 절단 예측 도구

| 도구 | 접근 방식 | 오프라인 | 프로테아제 종류 | NCAA | KAERI 우선순위 |
|------|----------|---------|--------------|------|--------------|
| **ExPASy PeptideCutter** | 웹 전용 | ❌ | 70+ (NEP 포함) | ❌ | LOW (웹 접근 시) |
| **PROSPER** | 웹+Java 스탠드얼론 | ✅ (4GB) | 24종 (Caspase, MMP, Furin, Chymotrypsin) | ❌ | MED (다운로드 후) |
| **PROSPERous** | 웹 + 소스 가능 | ✅ (요청) | 90종 | ❌ | MED |
| **DeepCleave** | 웹+모델 다운로드 | ✅ (모델) | 12종 (Caspase, MMP) | ❌ | MED |
| **MEROPS DB** | 웹 전용 (DB) | ❌ | 수천 종 | ❌ | LOW (참고용) |

### 1.3 Half-life / ADMET 예측 도구

| 도구 | 접근 방식 | NCAA | 혈중 반감기 | 오프라인 | KAERI 우선순위 |
|------|----------|------|-----------|---------|--------------|
| **HLP** (IIITD) | 웹 전용 | ❌ | 장내 t½ | ❌ | LOW |
| **PlifePred** (IIITD) | 웹 전용 | ✅ Modified 모듈 | 혈중 t½ (modified 포함) | ❌ | MED (웹 접근 시) |
| **PeptideRanker** | 웹 전용 | 불명 | 간접 (생물활성 점수) | ❌ | LOW |
| **ADMETlab 3.0** | 웹/REST API | ✅ SMILES | 전체 ADMET 119항목 | ❌ | MED (API) |
| **CamSol-PTM** | 웹 (등록 필요) | ✅ SMILES 확장 | 용해도 특화 | ❌ | MED (등록 후) |

### 1.4 프로젝트 내장 코드 (즉시 사용 가능)

| 모듈 | 위치 | 기능 | NCAA | 상태 |
|------|------|------|------|------|
| **compute_admet** | `backend/admet.py` | MW, 전하, HBD/HBA, 소수성, druglikeness | ❌ | ✅ 가동 중 |
| **compute_nephrotox_risk** | `backend/admet.py` | 신독성 위험 점수 (PRRT 전용) | ❌ | ✅ 가동 중 |
| **step08_stability** | `pipeline_local/steps/step08_stability.py` | 안정성 휴리스틱 ranking score | 부분 | ✅ 가동 중 |
| **pharmacology_guards** | `pipeline_local/scripts/pharmacology_guards.py` | 문헌 정답 회귀 검증 (H-01~H-06) | ❌ | ✅ 93/93 tests |
| **ADMET batch API** | `pipeline_local/backend/routers/admet.py` | FastAPI 배치 엔드포인트 | ❌ | ✅ REST API |

---

## 2. 도구별 상세 설명 및 본 프로젝트 적용 가능성

### 2.1 Biopython ProtParam ⭐ (즉시 사용)

**설치**: `pip install biopython` (bio-tools conda env에 포함)  
**입력**: 표준 아미노산 단일 문자 string  
**출력**: MW, pI, GRAVY (Kyte-Doolittle 평균), Instability Index (Guruprasad 1990), 아미노산 조성  
**NCAA**: 표준 20종 전용. D-아미노산, NMe, DOTA 미지원  
**한계**: "Instability Index < 40 = 안정" 규칙은 세포내 단백질 기반 — **혈중 펩타이드에 직접 적용 주의**  
**적용**: 빠른 초기 필터, 상대 비교 용도

```python
from Bio.SeqUtils.ProtParam import ProteinAnalysis

candidates = {
    "SST-14 (ref)":   "AGCKNFFWKTFTSC",
    "cand03 (G2I)":   "AICKNFFWKTFTSC",
    "ILCKKFFWKTFTSC": "ILCKKFFWKTFTSC",
}
print(f"{'Name':<22} {'MW':>8} {'GRAVY':>7} {'Instab':>8} {'pI':>6}")
for name, seq in candidates.items():
    p = ProteinAnalysis(seq)
    print(f"{name:<22} {p.molecular_weight():>8.1f} {p.gravy():>7.3f} "
          f"{p.instability_index():>8.2f} {p.isoelectric_point():>6.2f}")
```

**신뢰**: HIGH (물리화학적 계산), 반감기 예측 관련성: **LOW** (휴리스틱 proxy)  
**출처**: (Cock et al. 2009 Bioinformatics 25:1422, DOI:10.1093/bioinformatics/btp163)

---

### 2.2 peptides.py ⭐ (pip install 후 즉시 사용)

**설치**: `pip install peptides` (현재 bio-tools env에 미설치 → 설치 필요)  
**버전**: v0.5.0 (2025-09-04)  
**입력**: 표준 아미노산 string  
**출력**: Boman index, 전하(pH 7.4), aliphatic index, 소수성 모멘트, Kidera factors, Z-scales  
**NCAA**: 미지원  
**핵심 기능**: **Boman index** — 단백질 결합 잠재력 (높을수록 세포막/수용체 결합 잠재력 높음, SSTR2 결합력 proxy로 활용 가능)

```python
import peptides

candidates = {
    "SST-14":       "AGCKNFFWKTFTSC",
    "cand03 G2I":   "AICKNFFWKTFTSC",
    "ILCKKFFWKTFTSC": "ILCKKFFWKTFTSC",
}
for name, seq in candidates.items():
    p = peptides.Peptide(seq)
    print(f"{name}: boman={p.boman():.3f}, aliphatic={p.aliphatic_index():.2f}, "
          f"charge@pH7.4={p.charge(pH=7.4):.2f}")
```

**신뢰**: HIGH (물리화학적), 반감기 관련성: LOW  
**출처**: (Osorio D et al. 2015 Bioinformatics 31:4018, DOI:10.1093/bioinformatics/btv578; althonos GitHub v0.5.0)

---

### 2.3 pepADMET ⭐⭐ (GitHub 클론 후 사용 — 권장)

**설치**: `git clone https://github.com/ifyoungnet/pepADMET && pip install -r requirements.txt`  
**입력**: CSV (예시: `example.csv`) — 서열 + 수식 타입 포함  
**출력**: **29개 ADMET endpoint** (LogD7.4, Bioavailability, Caco-2, PAMPA, RRCK, BBB, 반감기 5종, 독성 11종)  
**NCAA 지원**: ✅ D-아미노산, cyclic 펩타이드, Palmitoyl, 인산화, 산화 등 35종+ 수식  
**DOTA**: 명시 미지원 — 확인 필요  
**오프라인**: PyTorch 사전학습 모델(.pth) 로컬 실행 가능  
**논문**: (Tan et al. 2025 J. Chem. Inf. Model. DOI:10.1021/acs.jcim.5c02518)

```python
# pepADMET 예시 (클론 후)
import pandas as pd
# CSV 형식: sequence, modification_type
df = pd.DataFrame({
    "sequence": ["AICKNFFWKTFTSC", "ILCKKFFWKTFTSC", "AGCKNFFWKTFTSC"],
    "type": ["standard", "standard", "standard"],  # or 'cyclic', 'D-amino'
})
df.to_csv("input.csv", index=False)
# python predict.py --input input.csv --output result.csv
```

**신뢰**: MED (2025 최신 모델, ADMET endpoint 문헌 검증 중)  
**KAERI 적용 우선순위**: HIGH — D-아미노산 수식 후보 평가에 필수

---

### 2.4 프로젝트 내장 ADMET + Nephrotox (즉시 사용 가능)

**경로**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/admet.py`  
**API**: `pipeline_local/backend/routers/admet.py` (FastAPI REST)  

```python
import sys
sys.path.insert(0, "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri")
from backend.admet import compute_admet, compute_nephrotox_risk

seqs = ["AICKNFFWKTFTSC", "ILCKKFFWKTFTSC"]
for seq in seqs:
    admet = compute_admet(seq)
    nephro = compute_nephrotox_risk(seq)
    print(f"{seq}: MW={admet['mw']:.1f}, charge={admet['net_charge_ph74']}, "
          f"hydro={admet['hydrophobicity']}, DLscore={admet['druglikeness_score']}, "
          f"nephro_risk={nephro['risk_level']}")
```

**특이사항**: PRRT 전용 신독성 점수 (`compute_nephrotox_risk`) — SSTR2 방사성의약품 후보에 특화된 유일한 내장 기능

---

### 2.5 PlifePred (웹 — NCAA 지원)

**URL**: https://webs.iiitd.edu.in/raghava/plifepred/  
**특징**: **혈중 반감기 예측**, D-아미노산/PEG화/사이클화 포함 Modified 모듈 지원  
**입력**: sequence string, PDB 파일, 또는 Marvin Draw 화학 구조  
**출력**: in-vitro serum t½ 예측 (분 단위)  
**한계**: 웹 전용, 스탠드얼론 미공개  
**논문**: (Mathur D et al. 2018 PLoS ONE DOI:10.1371/journal.pone.0196829)  
**KAERI 적용**: 망 접근 시 즉시 사용 가능. D-Phe6 도입 후보의 안정성 예측에 활용 권장.

---

### 2.6 PROSPER 스탠드얼론 (오프라인 protease predictor)

**다운로드**: https://prosper.erc.monash.edu.au/downloads.html (Java, ~4GB 압축 해제)  
**지원 프로테아제**: 24종 — Chymotrypsin, Trypsin, Cathepsin K/B/D, MMP-2/3/7/9, Caspase 1/3/6/7/8, HIV-1, Furin, Thrombin  
**NEP (Neprilysin, M13) 포함 여부**: ❌ 미포함 — NEP는 별도 자원 필요 (ExPASy PeptideCutter는 NEP 포함)  
**입력**: FASTA 형식  
**오프라인**: ✅ KAERI 망 제한 환경에서 사용 가능  
**논문**: (Song J et al. 2012 PLoS ONE 7:e50300 DOI:10.1371/journal.pone.0050300)

---

### 2.7 ExPASy PeptideCutter (NEP 절단 시뮬레이션)

**URL**: https://web.expasy.org/peptide_cutter/  
**특징**: **Neprilysin(M13) 포함 70+ 효소 절단 시뮬레이션** — 본 프로젝트 SST-14 NEP 분해 검증에 직접 유용  
**입력**: 아미노산 서열 (web form)  
**출력**: 각 효소에 의한 절단 위치 지도  
**오프라인**: ❌ 웹 전용 (Python API 없음)  
**KAERI 적용**: 망 접근 시 최우선 사용. NEP 절단 F6-F7, T10-F11 확인용.

---

### 2.8 ADMETlab 3.0 (REST API 접근)

**웹**: https://admetlab3.scbdd.com  
**API**: REST 기반 배치 평가 가능  
**입력**: SMILES (펩타이드를 SMILES로 변환 필요 — RDKit 활용)  
**출력**: 119개 endpoint (ADMET 전반)  
**DOTA 처리**: SMILES 기반이므로 DOTA chelator 구조 SMILES 포함 가능  
**한계**: 펩타이드 특화 아님, 소분자 중심 훈련 데이터  
**논문**: (Fu Z et al. 2024 Nucleic Acids Res. 52:W422 DOI:10.1093/nar/gkae236)

---

### 2.9 CamSol-PTM (용해도 — 비표준 AA 지원)

**URL**: https://www-cohsoftware.ch.cam.ac.uk/index.php/camsolptm  
**특징**: D-아미노산, NLE, CHA, AIB 등 비표준 아미노산 SMILES 확장 지원  
**DOTA**: 명시 미지원 (크기 제한)  
**등록**: 학술 이메일(dongjukim@kaeri.re.kr)로 등록 필요  
**용도**: D-Phe6 또는 D-Thr10 도입 후 용해도 변화 예측  
**논문**: (Oeller M et al. 2023 Nat. Commun. DOI:10.1038/s41467-023-42940-w)

---

## 3. KAERI 즉시 사용 가능 목록 및 우선순위

### 3.1 즉시 사용 가능 (현재 환경)

| 우선순위 | 도구 | 명령 | 용도 |
|---------|------|------|------|
| 🥇 **1** | **Biopython ProtParam** | `from Bio.SeqUtils.ProtParam import ProteinAnalysis` | MW, GRAVY, Instability, pI |
| 🥇 **1** | **프로젝트 compute_admet** | `from backend.admet import compute_admet` | MW, 전하, DL score, 신독성 |
| 🥇 **1** | **step08_stability** | `from pipeline_local.steps.step08_stability import evaluate_stability` | 휴리스틱 ranking (⚠️ heuristic only) |
| 🥇 **1** | **pharmacology_guards** | `from pipeline_local.scripts.pharmacology_guards import assert_in_range` | 문헌값 범위 검증 |

### 3.2 빠른 설치 후 사용 가능

| 우선순위 | 도구 | 설치 명령 | 예상 시간 |
|---------|------|---------|---------|
| 🥈 **2** | **peptides.py** | `conda run -n bio-tools pip install peptides` | < 1분 |
| 🥈 **2** | **modlAMP** | `conda run -n bio-tools pip install modlamp` | < 2분 |
| 🥈 **2** | **pepADMET** | `git clone + pip install -r requirements.txt` | 5-10분 |

### 3.3 사전 다운로드 필요 (망 제한 환경)

| 도구 | 다운로드 크기 | 우선순위 | 이유 |
|------|------------|---------|------|
| PROSPER 스탠드얼론 | ~4 GB | MED | 24종 프로테아제 오프라인 실행 |
| DeepCleave 모델 | ~500 MB | MED | DL 기반 Caspase/MMP |
| pepADMET .pth 모델 | < 100 MB | HIGH | D-아미노산 수식 ADMET |

### 3.4 웹 전용 (접근 가능 시 사용)

| 도구 | URL | 핵심 기능 |
|------|-----|---------|
| PlifePred | webs.iiitd.edu.in/raghava/plifepred/ | **혈중 반감기 (modified 포함)** — 최우선 |
| ExPASy PeptideCutter | web.expasy.org/peptide_cutter/ | **NEP 절단 위치 확인** — 최우선 |
| ADMETlab 3.0 | admetlab3.scbdd.com | 전체 ADMET (SMILES) |
| CamSol-PTM | (등록 후) | 용해도 |

---

## 4. Python 코드 예시

### 4.1 Biopython ProtParam — 본 후보 배치 계산

```python
from Bio.SeqUtils.ProtParam import ProteinAnalysis

# T3 후보 + 기준 서열
candidates = {
    "SST-14 (ref)":       "AGCKNFFWKTFTSC",
    "cand03 (G2I)":       "AICKNFFWKTFTSC",
    "ILCKKFFWKTFTSC":     "ILCKKFFWKTFTSC",
    "VLCKNFFWKTFTSC":     "VLCKNFFWKTFTSC",
    "ALCKNFFWKTFTSC":     "ALCKNFFWKTFTSC",
    "AICKAFFWKTFTSC":     "AICKAFFWKTFTSC",
    "AIRCNFFWKTFTSC":     "AIRCNFFWKTFTSC",
}
print(f"{'Name':<24} {'MW(avg)':>9} {'GRAVY':>7} {'Instab':>8} {'pI':>6}")
print("-" * 60)
for name, seq in candidates.items():
    p = ProteinAnalysis(seq)
    print(f"{name:<24} {p.molecular_weight():>9.1f} {p.gravy():>7.3f} "
          f"{p.instability_index():>8.2f} {p.isoelectric_point():>6.2f}")
```

### 4.2 프로젝트 내장 ADMET + Nephrotox 배치 실행

```python
import sys
sys.path.insert(0, "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri")
from backend.admet import compute_admet, compute_nephrotox_risk

candidates = {
    "SST-14 (ref)":   "AGCKNFFWKTFTSC",
    "cand03 G2I":     "AICKNFFWKTFTSC",
    "ILCKKFFWKTFTSC": "ILCKKFFWKTFTSC",
}
for name, seq in candidates.items():
    a = compute_admet(seq)
    n = compute_nephrotox_risk(seq)
    print(f"{name}: MW={a['mw']:.1f} Da | charge={a['net_charge_ph74']:+.1f} | "
          f"hydro={a['hydrophobicity']:.3f} | DL={a['druglikeness_score']}/100 | "
          f"nephro={n['risk_level']}")
```

### 4.3 pharmacology_guards 범위 검증

```python
from pipeline_local.scripts.pharmacology_guards import (
    assert_in_range, SCALE_RANGES, LITERATURE_VALUES
)

# SSTR2 Ki 범위 검증 예시
sstr2_ki = 2.5  # nM (예시 docking score)
assert_in_range("sstr2_ki_nm", sstr2_ki,
                min_val=0.1, max_val=1000,
                context="cand03 binding estimate")

# 반감기 범위 검증
predicted_t_half = 5.0  # 분 (heuristic score)
assert_in_range("plasma_half_life_min", predicted_t_half,
                min_val=0.1, max_val=10000,
                context="step08 heuristic output")
```

### 4.4 pepADMET 래퍼 예시 (클론 후)

```python
# pepADMET 사용 예시 — GitHub 클론 후 실행
# git clone https://github.com/ifyoungnet/pepADMET
# pip install -r requirements.txt

import subprocess, json

seqs = ["AICKNFFWKTFTSC", "ILCKKFFWKTFTSC", "AGCKNFFWKTFTSC"]
with open("input.csv", "w") as f:
    f.write("sequence,type\n")
    for s in seqs:
        f.write(f"{s},standard\n")

# 로컬 실행 (사전학습 .pth 모델 필요)
result = subprocess.run(
    ["python", "predict.py", "--input", "input.csv", "--output", "out.csv"],
    capture_output=True, text=True
)
# out.csv에 29개 ADMET endpoint 결과 저장
```

### 4.5 step08_stability 휴리스틱 랭킹

```python
from pipeline_local.steps.step08_stability import evaluate_stability, StabilityConfig

candidates = [
    {"sequence": "AICKNFFWKTFTSC", "name": "cand03"},
    {"sequence": "ILCKKFFWKTFTSC", "name": "T3-ILCK"},
]
config = StabilityConfig(target_half_life_hours=144)  # 6일 목표
results = evaluate_stability(candidates, config)
for r in results:
    # r.ranking_score (HEURISTIC — 임상 반감기 아님)
    print(f"{r.name}: score={r.ranking_score:.2f} (heuristic)")
```

---

## 5. 본 후보 7종 배치 적용 결과

> **계산 일시**: 2026-05-12  
> **도구**: Biopython ProtParam + 프로젝트 내장 compute_admet + compute_nephrotox_risk  
> **⚠️ 주의**: 모든 수치는 in-silico 계산값 (heuristic / QSAR). 임상 수치 아님.

### 5.1 물리화학적 descriptor 표

| 후보 서열 | MW (avg, Da) | GRAVY | Instability Index | pI | KD Hydro | DL Score |
|---------|------------|-------|------------------|-----|---------|---------|
| **SST-14 (ref)** AGCKNFFWKTFTSC | 1639.9 | **0.029** | 30.65 ✅ | 8.91 | 0.029 | **100/100** |
| **cand03** AICKNFFWKTFTSC | 1696.0 | 0.379 | 30.65 ✅ | 8.91 | 0.379 | **100/100** |
| **ILCKKFFWKTFTSC** | 1752.1 | 0.493 | **55.14 ⚠️** | 9.39 | 0.493 | **100/100** |
| VLCKNFFWKTFTSC | 1724.1 | 0.500 | 30.65 ✅ | 8.90 | 0.500 | **100/100** |
| ALCKNFFWKTFTSC | 1696.0 | 0.329 | 30.65 ✅ | 8.91 | 0.329 | **100/100** |
| AICKAFFWKTFTSC | 1653.0 | 0.757 | 41.39 ⚠️ | 8.91 | 0.757 | **100/100** |
| AIRCNFFWKTFTSC | 1724.0 | 0.336 | 30.65 ✅ | 8.96 | 0.336 | **100/100** |

### 5.2 신독성 위험 표 (PRRT 방사성의약품 전용)

| 후보 서열 | n_Lys | n_Arg | n_His | 양이온 잔기 | 신독성 위험 |
|---------|-------|-------|-------|-----------|-----------|
| SST-14 (ref) | 2 | 0 | 0 | 2 | **High** |
| cand03 | 2 | 0 | 0 | 2 | **High** |
| ILCKKFFWKTFTSC | 3 | 0 | 0 | 3 | **High** |
| VLCKNFFWKTFTSC | 2 | 0 | 0 | 2 | **High** |
| ALCKNFFWKTFTSC | 2 | 0 | 0 | 2 | **High** |
| AICKAFFWKTFTSC | 1 | 0 | 0 | 1 | **Moderate** |
| AIRCNFFWKTFTSC | 1 | 1 | 0 | 2 | **High** |
| Octreotide core (CFYWKTC) | 1 | 0 | 0 | 1 | **Moderate** |

**해석**: 
- 모든 SST-14 기반 후보는 Lys2개(K4, K9)로 **신독성 High** — 이는 SST-14 특성이며 DOTATATE와 동일. PRRT 시 Lys/Arg 아미노산 공동 투여로 신독성 감소 표준화 됨 (Lutathera 프로토콜).
- AICKAFFWKTFTSC(N5A 치환)만 Moderate — 하지만 N5A는 NEP 절단 위치(N5-F6) 직접 관련 잔기 제거이므로 안정성 개선 가능성 있음 (검증 필요).

### 5.3 Instability Index 해석 (Guruprasad 1990 원칙)

> ⚠️ Instability Index는 **세포내 단백질 안정성** 기준. 혈중 펩타이드 반감기에 직접 대응하지 않음.

| Instability Index | 세포내 해석 | 혈중 안정성 관련성 |
|-----------------|-----------|---------------|
| < 40 | "안정" | 참고 가능 (낮음) |
| 40 - 60 | "불안정" 경계 | 약한 음의 상관 |
| > 60 | "불안정" | 단순 참고 |

**주목**: ILCKKFFWKTFTSC Instability = 55.14 — K4→K 이중 Lys 치환에 의한 DW 쌍 증가가 원인. 단 이것이 혈중 t½에 직접 영향 여부는 in-vitro assay 필요.

---

## 6. 한계 및 §검증 필요 항목

### 6.1 도구별 핵심 한계

| 도구 | 핵심 한계 |
|------|---------|
| Biopython ProtParam | DOTA, D-아미노산 미지원. Instability Index는 혈중 t½ ≠ |
| peptides.py | 표준 20종 전용. 비표준 수식 불가 |
| pepADMET | 2025 신규 모델 — 외부 검증 제한적. DOTA 명시 미지원 |
| PlifePred | 웹 전용. Modified 모듈 정확도 검증 부족 |
| step08_stability | H-06 원칙: 휴리스틱 ranking만 허용. 절대 t½ 출력 금지 |
| compute_admet (내장) | 단순 규칙 기반. DLscore = 100/100이 모든 후보에서 나오는 것은 규칙이 너무 관대함을 시사 |
| PROSPER | NEP 미포함. Caspase/MMP 위주 |

### 6.2 §검증 필요 항목

| # | 항목 | 현황 | 우선순위 |
|---|------|------|---------|
| G-01 | pepADMET D-아미노산 SST-14 예측 정확도 | 검증 논문 없음 | HIGH |
| G-02 | PlifePred Modified 모듈 — cand03 D-Phe6 입력 가능 여부 | 웹 실제 테스트 필요 | HIGH |
| G-03 | ExPASy PeptideCutter — ILCKKFFWKTFTSC NEP 절단 위치 확인 | 웹 접근 시 즉시 실행 가능 | HIGH |
| G-04 | AICKAFFWKTFTSC (N5A) — 신독성 Moderate의 실제 renal clearance 영향 | in-vitro 필요 | MED |
| G-05 | compute_admet DLscore = 100/100 포화 문제 | 규칙 재정의 검토 필요 (너무 관대) | MED |
| G-06 | peptides.py bio-tools env 설치 확인 | `pip install peptides` 1분 | LOW |
| G-07 | pepADMET DOTA 수식 처리 방법 | GitHub Issue/README 확인 | MED |
| G-08 | ADMETlab 3.0 API 배치 접근 가능 여부 | 망 접근 테스트 필요 | LOW |

---

## 7. 추가 권장 도구 (다음 분기 도입 검토)

| 도구 | 기능 | 도입 근거 | 예상 비용 |
|------|------|---------|---------|
| **HELM notation + BigSMILES** | 비표준 펩타이드 표준 표현 | DOTA 수식 펩타이드 입력 형식 표준화 | 낮음 (사양 학습만) |
| **RDKit 펩타이드 SMILES 변환기** | 서열 → SMILES 자동화 | ADMETlab 3.0 / CamSol 입력 | 낮음 |
| **PROSPERous (90종 프로테아제)** | PROSPER 후속, NEP 포함 여부 확인 필요 | 프로테아제 커버리지 확장 | 낮음 (Java) |
| **DeepMet** | DL 기반 펩타이드 대사 안정성 | 2023+ 새 모델 | 중간 |
| **PeptideBERT** | ESM 계열 펩타이드 특성 예측 | HuggingFace 오픈소스 | 낮음 (GPU 필요) |

---

## 8. 참고 — 도구별 논문

1. Cock, P. J., Antao, T., Chang, J. T., et al. (2009). Biopython: Freely available Python tools for computational molecular biology and bioinformatics. *Bioinformatics*, 25(11), 1422–1423. https://doi.org/10.1093/bioinformatics/btp163

2. Guruprasad, K., Reddy, B. V. B., & Pandit, M. W. (1990). Correlation between stability of a protein and its dipeptide composition: A novel approach for predicting in vivo stability of a protein from its primary sequence. *Protein Engineering*, 4(2), 155–161. https://doi.org/10.1093/protein/4.2.155

3. Müller, A. T., Gabernet, G., Hiss, J. A., & Schneider, G. (2017). modlAMP: Python for antimicrobial peptides. *Bioinformatics*, 33(17), 2753–2755. https://doi.org/10.1093/bioinformatics/btx285

4. Osorio, D., Rondón-Villarreal, P., & Torres, R. (2015). Peptides: A package for data mining of antimicrobial peptides. *Bioinformatics*, 31(24), 4018–4020. https://doi.org/10.1093/bioinformatics/btv578

5. Sharma, A., Singla, D., Rashid, M., & Raghava, G. P. S. (2014). Designing of peptides with desired half-life in intestine-like environment. *BMC Bioinformatics*, 15(1), 282. https://doi.org/10.1186/1471-2105-15-282

6. Mathur, D., Prakash, S., Anand, P., et al. (2018). PlifePred: Predicting the half-life of peptides in biologically relevant fluids using the random forest approach. *PLoS ONE*, 13(4), e0196829. https://doi.org/10.1371/journal.pone.0196829

7. Song, J., Tan, H., Perry, A. J., et al. (2012). PROSPER: An integrated feature-based tool for predicting protease substrate cleavage sites. *PLoS ONE*, 7(11), e50300. https://doi.org/10.1371/journal.pone.0050300

8. Li, F., Chen, J., Leier, A., et al. (2020). DeepCleave: A deep learning predictor for caspase and matrix metalloprotease substrates and cleavage sites. *Bioinformatics*, 36(4), 1057–1065. https://doi.org/10.1093/bioinformatics/btz721

9. Tan, Y., et al. (2025). pepADMET: A comprehensive machine learning platform for ADMET property prediction of peptide drugs. *Journal of Chemical Information and Modeling*. https://doi.org/10.1021/acs.jcim.5c02518

10. Fu, Z., Li, X., Xiong, Z., et al. (2024). ADMETlab 3.0: An updated comprehensive online ADMET prediction platform enhanced with broader coverage, improved performance, API interfaces and decision support. *Nucleic Acids Research*, 52(W1), W422–W431. https://doi.org/10.1093/nar/gkae236

11. Oeller, M., Kang, R., Bell, R., et al. (2023). Sequence-based prediction of the intrinsic solubility of peptides containing non-natural amino acids. *Nature Communications*, 14(1), 7475. https://doi.org/10.1038/s41467-023-42940-w

12. Mooney, C., Haslam, N. J., Holton, T. A., Pollastri, G., & Shields, D. C. (2012). PeptideRanker: A webserver for the ranking of general bioactive peptides predicted from protein sequence. *PLoS ONE*, 7(9), e45012. https://doi.org/10.1371/journal.pone.0045012

---

## 9. 요약 — KAERI 단계별 실행 로드맵

```
단계 1 (즉시): 
  → Biopython + compute_admet 배치 실행 (코드 §4.1, §4.2 그대로 사용)
  → pharmacology_guards 범위 검증 통합
  
단계 2 (설치 후, < 10분):
  → pip install peptides → Boman index 추가
  → pip install modlamp → descriptor 확장
  
단계 3 (GitHub 클론, < 30분):
  → pepADMET 클론 → D-아미노산 수식 후보 ADMET 29항목 평가
  
단계 4 (웹 접근 시):
  → PlifePred — D-Phe6 도입 후보 혈중 t½ 예측 (Modified 모듈)
  → ExPASy PeptideCutter — NEP 절단 위치 F6-F7, T10-F11 확인
  
단계 5 (다음 분기):
  → PROSPER 스탠드얼론 다운로드 (4GB) → 24종 프로테아제 오프라인 분석
  → CamSol-PTM 등록 → 용해도 예측 (D-아미노산 포함)
```

---

*작성: researcher (S6, Task id=15) | 2026-05-12*  
*검토 요청: reviewer-pharma (§5 수치 해석), reviewer-chemistry (DOTA SMILES 처리 방법)*
