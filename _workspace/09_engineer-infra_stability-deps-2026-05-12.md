# 환경 변경 메모 — stability predictor 의존성 설치

**날짜**: 2026-05-12  
**작성자**: engineer-infra  
**작업 ID**: U2

---

## 1. 설치된 패키지

### bio-tools env

| 패키지 | 버전 | 설치 방법 | 상태 |
|--------|------|----------|------|
| peptides | 0.5.0 | `conda run -n bio-tools pip install peptides` | ✅ 신규 설치 |
| biopython | 1.79 | 기존 | ✅ 정상 |
| numpy | 1.26.4 | 기존 | ✅ 정상 |
| scipy | 1.12.0 | 기존 | ✅ 정상 |

---

## 2. 검증 결과 (AICKNFFWKTFTSC 기준)

```
GRAVY:             0.3786   (Biopython ProteinAnalysis.gravy())
Instability Index: 30.65    (안정 — <40 기준, Biopython)
Boman Index:       0.4086   (peptides.py)
Aliphatic Index:   35.0     (peptides.py)
Charge (pH 7.4):   1.7088   (peptides.py)
Hydrophobicity:    0.3786   (peptides.py, Kyte-Doolittle scale)
Molecular Weight:  1696.00  (Biopython)
```

**전체 4/4 통과** — `bash scripts/verify_stability_env.sh` 로 재현 가능

---

## 3. 충돌 검토

- **의존성 충돌 없음**: peptides.py 0.5.0은 pure Python 패키지 (C extension 없음)
- numpy/scipy/biopython 기존 버전과 완전 호환
- PyRosetta 환경 영향 없음

### 주의: peptides.py 0.5.0 API 변경

| 메서드 | 상태 | 대체 |
|--------|------|------|
| `pep.boman()` | ✅ 정상 | — |
| `pep.aliphatic_index()` | ✅ 정상 | — |
| `pep.charge(pH=7.4)` | ✅ 정상 | — |
| `pep.hydrophobicity()` | ✅ 정상 | — |
| `pep.instability_index()` | ✅ 정상 | — |
| `pep.gravy()` | ❌ **없음** | `ProteinAnalysis(seq).gravy()` 사용 |

> **engineer-backend (U1)에 전달**: `stability_predictor.py`에서 `gravy()` 는 `peptides.py`가 아닌 `Biopython.ProteinAnalysis`로 계산해야 합니다.

---

## 4. pepADMET 도입 평가

### 결론: **별도 env 격리 설치 (Y) — bio-tools 통합 불가 (N)**

| 항목 | 상태 | 비고 |
|------|------|------|
| PyPI 배포 | ❌ 없음 | `pip install pepADMET` → "No matching distribution" |
| GitHub 소스 | ✅ https://github.com/ifyoungnet/pepADMET | Python 3.7, PyTorch 1.13 필요 |
| bio-tools 통합 | ❌ **불가** | Python 3.10-3.12 vs pepADMET 요구 3.7 — 버전 불일치 |
| 별도 env | ✅ **권장** | `pepadmet` env (Python 3.7, PyTorch 1.13.1+cu117) |
| 내부망 접근 | ⚠️ GitHub 접근 필요 | `scripts/download_pepadmet.sh` 참조 |

### pepADMET 의존성 (도입 시 별도 env 필요)

```
Python:          3.7.16
PyTorch:         1.13.1+cu117
DGL:             0.4.3
scikit-learn:    1.0.2
numpy:           1.21.5
pandas:          1.3.5
rdkit-pypi:      2022.9.5
modlamp:         4.3.0
PyBioMed:        GitHub 소스
```

### pepADMET 제공 endpoint (29개)

- **Stability**: Half-life (plasma), Protease stability
- **Permeability**: PAMPA, Caco-2, RRCK, BBB
- **PK**: LogD_7.4, Bioavailability(F)
- **Toxicity**: Hemolytic, DILI, Hepatotoxicity 등
- **D-amino acid 지원**: ✅ (cand03 변이체에 활용 가능)

### 현 단계 도입 권장 여부

**단계적 접근 권장:**
1. **즉시**: `peptides.py` + Biopython으로 6개 지표 계산 (이미 완료)
2. **이후**: pepADMET은 `pepadmet` env로 격리 설치 (`scripts/download_pepadmet.sh`)
3. **통합**: pipeline_local에서 subprocess로 `conda run -n pepadmet` 호출

---

## 5. environment-bio-tools.yml 업데이트

`peptides==0.5.0` pip 섹션에 추가 완료:

```yaml
  - pip:
    - meeko
    - py3Dmol
    - pynvml
    - peptides==0.5.0    # Boman, aliphatic, hydrophobicity (2026-05-12 추가)
```

---

## 6. 산출물 목록

| 파일 | 상태 |
|------|------|
| `scripts/verify_stability_env.sh` | ✅ 신규 (4/4 통과) |
| `environment-bio-tools.yml` | ✅ peptides==0.5.0 추가 |
| `_workspace/09_engineer-infra_stability-deps-2026-05-12.md` | ✅ 이 파일 |

---

## 7. 재현 명령

```bash
# 설치 재현
conda run -n bio-tools pip install peptides==0.5.0

# 검증
bash scripts/verify_stability_env.sh

# pepADMET 설치 (향후, 별도 env)
bash scripts/download_pepadmet.sh
```

---

## 8. 팀원 영향도

| 팀원 | 영향 | 조치 |
|------|------|------|
| engineer-backend (U1) | `gravy()` API 주의 | `peptides.py` 대신 `ProteinAnalysis.gravy()` 사용 요망 |
| reviewer-pharma | pepADMET 29 endpoint 향후 활용 가능 | 별도 env 도입 후 알림 |
| 다른 팀원 | bio-tools env 변경 최소 (pure Python 추가만) | 영향 없음 |
