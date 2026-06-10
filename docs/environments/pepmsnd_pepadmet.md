# 반감기·ADMET 예측 도구 환경 가이드

**작성**: engineer-infra (2026-05-19)  
**근거**: A-02 혈청 반감기 비교 보고서 + A-03 ADMET 검증 보고서  
**업데이트 필요 시**: 웹서버 접근 상태 변경 또는 신규 도구 채택 시

---

## 요약: 도구별 현황 (2026-05-19)

| 도구 | 로컬 실행 | conda env | D-AA | 신뢰도 | 상태 |
|------|---------|---------|------|--------|------|
| **PlifePred2** | ✅ | `peptools` | ❌ | P4 | 설치 확인 |
| **PepMSND** | ❌ (웹 전용) | 없음 | ❌ | P3 | HTTP 403 |
| **pepADMET** | ❌ (웹 전용) | 없음 | 미확인 | P2 | HTTP 403 |
| **modlamp** | ✅ | `pepadmet` | ❌ | P3 (디스크립터) | 설치 확인 |

> **핵심**: PepMSND/pepADMET 모두 웹 전용이며, 현재 이 서버에서 403 응답.  
> 로컬 실행 가능한 가장 근접한 대안: PlifePred2 (L-AA 14aa+, P4 등급)

---

## 1. `peptools` conda 환경 (PlifePred2 + SMILES)

### 1.1 설치

```bash
# 신규 생성 (bio-tools와 scikit-learn 버전 충돌 방지)
conda create -n peptools python=3.11 -y
conda run -n peptools pip install plifepred2 rdkit biopython requests
```

### 1.2 설치된 패키지

| 패키지 | 버전 | 비고 |
|--------|------|------|
| Python | 3.11 | |
| plifepred2 | 1.0 | scikit-learn 1.4.2 의존 |
| scikit-learn | 1.4.2 | bio-tools(1.8.0)과 충돌 → 별도 env |
| rdkit | 2026.3.2 | SMILES 변환용 |
| biopython | 1.87 | 서열 처리 |
| requests | 2.34.2 | 웹 API 통신 |

### 1.3 충돌 주의

bio-tools env에서 plifepred2 설치 시 scikit-learn 1.8.0 → 1.4.2 다운그레이드 발생.  
ESMFold/ProteinMPNN 의존성 파괴 위험 → **반드시 `peptools` 별도 env 사용**.

---

## 2. PlifePred2 사용 가이드

### 2.1 CLI 직접 사용

```bash
# 단일 서열 예측 (FASTA 파일 필요)
echo ">SST14
AGCKNFFWKTFTSC" > /tmp/sst14.fasta

conda run -n peptools plifepred2 -i /tmp/sst14.fasta -m 1 -o /tmp/result.csv
cat /tmp/result.csv
```

### 2.2 Python wrapper 사용

```bash
conda run -n peptools python pipeline_local/scripts/predict_halflife_pepmsnd.py \
    --sequence AGCKNFFWKTFTSC \
    --seq-id SST14 \
    --output runs_local/pepmsnd_benchmark/sst14.json
```

### 2.3 D-AA 서열 처리

PlifePred2는 D-AA를 지원하지 않습니다. 비표준 아미노산이 포함된 서열은 자동 거부됩니다.  
wrapper는 D-AA 감지 시 `confidence_grade: "P4"` + 경고를 반환하고 계산을 건너뜁니다.

### 2.4 출력 해석

| 필드 | 값 예시 | 설명 |
|------|---------|------|
| `plifepred2_score` | 3.38 (SST14) | 점수 (단위 미명시, 로그 변환 추정) |
| `plifepred2_score_unit` | "probability (0~1, NOT hours)" | 실제로 >1 출력 가능 |
| `confidence_grade` | "P4" | peer-review 미검증 |

> **⚠️ 중요**: 스코어를 시간(hour) 단위로 직접 변환하는 방법은 현재 미확인.  
> TPP KPI(≥24h, ≥72h) 직접 적용 불가. 상대적 순위 비교로만 사용.

---

## 3. PepMSND 사용 가이드 (웹 전용)

### 3.1 현황

- **웹서버**: http://model.highslab.com/pepmsnd
- **접근 상태**: HTTP 403 (이 서버에서 2026-05-19 확인)
- **로컬 설치**: 불가 (GitHub/PyPI 없음)

### 3.2 수동 사용 절차 (웹 브라우저)

1. 브라우저에서 http://model.highslab.com/pepmsnd 접속
2. 표준 L-아미노산 서열 입력 (D-AA, 비천연 AA 불가)
3. 결과: stable / highly stable / unstable / non-degradable 이진 분류

> **⚠️ 한계**: 이진 분류 출력 — 연속 t½ 값 없음. Octreotide(D-Phe, D-Trp) 입력 불가.

### 3.3 자동화 wrapper

```bash
# 자동화 시도 (현재 403 예상)
conda run -n peptools python pipeline_local/scripts/predict_halflife_pepmsnd.py \
    --sequence AGCKNFFWKTFTSC \
    --pepmsnd-web \
    --output runs_local/pepmsnd_benchmark/sst14.json
```

---

## 4. pepADMET 사용 가이드 (웹 전용)

### 4.1 현황

- **웹서버**: https://pepadmet.ddai.tech/
- **접근 상태**: HTTP 403 (이 서버에서 2026-05-19 확인)
- **로컬 설치**: 불가 (소스 미공개)
- **29 endpoints**: 반감기 (human/mouse blood + intestine), 독성, BBB, Caco-2, PPB 등

### 4.2 수동 사용 절차 (웹 브라우저)

1. 브라우저에서 https://pepadmet.ddai.tech/ 직접 접속
2. 서열 입력 (FASTA 또는 단일 서열)
3. 결과 JSON/CSV 다운로드

### 4.3 fallback: modlamp 디스크립터

```bash
conda run -n pepadmet python pipeline_local/scripts/predict_admet_pepadmet.py \
    --sequence AGCKNFFWKTFTSC \
    --seq-id SST14 \
    --output runs_local/pepadmet_benchmark/sst14.json
```

반환 값:
- `molecular_weight_da`: 분자량 (Da)
- `charge_ph7`: 순전하 (pH 7)
- `isoelectric_point`: 등전점
- `instability_index`: 불안정성 지수 (<40 = 안정)
- `boman_index`: 단백질 결합 가능성
- `aliphatic_index`, `hydrophobic_ratio`, `aromaticity`

---

## 5. SMILES 변환 유틸리티

```bash
# 표준 서열 → 선형 펩타이드 SMILES
conda run -n peptools python pipeline_local/scripts/sequence_to_smiles.py \
    --sequence AGCKNFFWKTFTSC

# D-AA 치환 포함 (6번째 Phe → D-Phe, 8번째 Trp → D-Trp)
conda run -n peptools python pipeline_local/scripts/sequence_to_smiles.py \
    --sequence AGCKNFFWKTFTSC \
    --daa "6:D-Phe,8:D-Trp"

# DOTA 킬레이터 N-term 부착
conda run -n peptools python pipeline_local/scripts/sequence_to_smiles.py \
    --sequence AGCKNFFWKTFTSC \
    --dota N-term \
    --output runs_local/smiles/sst14_dota.json
```

### D-AA SMILES 지원 목록

| 코드 | 이름 | 비고 |
|------|------|------|
| D-Phe | D-Phenylalanine | Octreotide 1번 잔기 |
| D-Trp | D-Tryptophan | Octreotide 4번 잔기 |
| D-Nal | D-2-Naphthylalanine | Lanreotide 비천연 AA |
| D-Thr | D-Threonine | |
| D-Lys | D-Lysine | |
| Cha | L-Cyclohexylalanine | SST 유사체 비천연 AA |
| Orn | L-Ornithine | |

> **⚠️ H-06**: SMILES는 1차 화학 구조 표현입니다. SS bond, 환화, D-AA 키랄 정확성은  
> wet-lab 합성 전 전문 화학자(reviewer-chemistry) 검토가 필수입니다.

---

## 6. SST14 벤치마크 결과 (2026-05-19)

### 서열: AGCKNFFWKTFTSC (SST-14, 14aa, t½_실측=3분)

| 도구 | 결과 | 단위 | 신뢰도 |
|------|------|------|--------|
| PlifePred2 (model_1_natural) | 3.38 | 점수 (시간 변환 불가) | P4 |
| pepADMET (웹) | — | 403 오류 | P2 |
| PepMSND (웹) | — | 403 오류 | P3 |
| modlamp MW | 1638.92 Da | Da | P3 (디스크립터) |
| modlamp Charge (pH7) | +2.68 | — | P3 |
| modlamp pI | 9.88 | — | P3 |
| modlamp InstabilityIndex | 30.65 | — | P3 |

---

## 7. 자주 발생하는 오류

### 7.1 `plifepred2: sequence too short`

```
Error: sequence length < 12 — filtered out
```

**원인**: PlifePred2는 12aa 미만 서열 거부. Octreotide(8aa), Lanreotide(8aa) 사용 불가.  
**해결**: 12aa 이상의 서열만 사용. 짧은 유사체는 pepADMET 웹(수동) 시도.

### 7.2 `ModuleNotFoundError: No module named 'plifepred2'`

```
conda run -n peptools pip install plifepred2
```

### 7.3 `HTTP 403 on pepADMET/PepMSND`

**원인**: 웹서버가 서버 측 IP 접근을 차단하거나 User-Agent를 차단.  
**해결**: 브라우저 수동 접속 또는 KAERI 네트워크 환경에서 시도.

### 7.4 `modlamp: attribute error`

v0.4.3 기준 `calculate_all()` 사용. `calculate_gravy()`는 미지원.  
```python
desc.calculate_all()  # ✅ correct
desc.calculate_gravy()  # ❌ AttributeError
```

---

## 8. GPU 요구사항

PlifePred2 / modlamp: CPU 전용 — GPU 불필요.  
pepADMET / PepMSND: 웹 전용 — 로컬 GPU 불관련.

---

## 9. 다음 단계 (§검증 필요)

| 항목 | 우선순위 | 담당 |
|------|---------|------|
| pepADMET D-AA 지원 여부 — Octreotide SMILES 브라우저 테스트 | HIGH | reviewer-chemistry |
| PlifePred2 스코어 단위 확인 — 원 논문 재현 | HIGH | engineer-backend |
| pepADMET API 키 확보 — DDAI Tech 문의 | MED | 사용자/RI팀 |
| D-AA 반감기 자체 ML 모델 — PEPlife2 데이터 기반 | MED (장기) | engineer-backend |
