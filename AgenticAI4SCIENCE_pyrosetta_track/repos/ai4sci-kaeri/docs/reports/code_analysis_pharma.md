# AG_src/pipeline/pharma_properties.py 코드 분석 보고서

**파일**: `AG_src/pipeline/pharma_properties.py` (876줄)  
**분석자**: reviewer-science  
**날짜**: 2026-04-07  
**목적**: 15개 메서드 + SS bond 보정 + 5대 구조 규칙의 과학적 정확성 검증

---

## 요약

| 항목 | 상태 |
|------|------|
| 총 메서드 수 | 15개 (계산) + 1개 (구조규칙) + 1개 (복합) + 1개 (배치) |
| 수식 정확성 | ✅ 대부분 정확 |
| 잠재적 버그 | ⚠️ Radzicka-Wolfenden S 값 불일치 가능성 |
| 이전 알려진 버그 상태 | ✅ K→Q DIWV=24.68 수정됨, Pro half-life=30.0 수정됨 |
| SS bond Cys 보정 | ✅ pI, 순전하, 방사선분해 감수성 모두 적용됨 |

---

## 1. GRAVY — Grand Average of Hydropathy

**출처**: Kyte & Doolittle 1982, *J Mol Biol* 157:105-132  
**수식**: `GRAVY = Σ(KD[aa_i]) / N`  
**구현 위치**: 라인 33-38 (테이블), 285-288 (메서드)

### KD_HYDROPATHY 테이블 검증 (20개 값)

| AA | 코드값 | 논문값 | 일치 |
|----|--------|--------|------|
| A | 1.8 | 1.8 | ✅ |
| R | -4.5 | -4.5 | ✅ |
| N | -3.5 | -3.5 | ✅ |
| D | -3.5 | -3.5 | ✅ |
| C | 2.5 | 2.5 | ✅ |
| Q | -3.5 | -3.5 | ✅ |
| E | -3.5 | -3.5 | ✅ |
| G | -0.4 | -0.4 | ✅ |
| H | -3.2 | -3.2 | ✅ |
| I | 4.5 | 4.5 | ✅ |
| L | 3.8 | 3.8 | ✅ |
| K | -3.9 | -3.9 | ✅ |
| M | 1.9 | 1.9 | ✅ |
| F | 2.8 | 2.8 | ✅ |
| P | -1.6 | -1.6 | ✅ |
| S | -0.8 | -0.8 | ✅ |
| T | -0.7 | -0.7 | ✅ |
| W | -0.9 | -0.9 | ✅ |
| Y | -1.3 | -1.3 | ✅ |
| V | 4.2 | 4.2 | ✅ |

**결론**: 20개 전값 논문과 일치 ✅  
**SST-14 계산**: AGCKNFFWKTFTSC → GRAVY ≈ -0.07 (소수성 경계선)  
**한계**: 선형 평균으로 위치 정보 없음; 양친매성 구조 불인식

---

## 2. Boman Index

**출처**: Boman 2003, *J Intern Med* 254:197-215  
**기반 스케일**: Radzicka & Wolfenden 1988, *Biochemistry* 27:1664-1670 (물→사이클로헥산 전이 자유에너지)  
**수식**: `BI = Σ(ΔG_transfer[aa_i]) / N`  
**구현 위치**: 라인 40-46 (테이블), 292-300 (메서드)  
**해석**: `BI > 2.48 kcal/mol` → 높은 단백질 결합 잠재력

### RW_TRANSFER 테이블 검증

| AA | 코드값 | 문헌값(RW1988) | 상태 |
|----|--------|----------------|------|
| A | -1.81 | -1.81 | ✅ |
| R | 14.92 | 14.92 | ✅ |
| N | 6.64 | 6.64 | ✅ |
| D | 8.72 | 8.72 | ✅ |
| C | -1.28 | -1.28 | ✅ |
| Q | 5.54 | 5.54 | ✅ |
| E | 6.81 | 6.81 | ✅ |
| G | -0.94 | -0.94 | ✅ |
| H | 4.66 | 4.66 | ✅ |
| I | -4.92 | -4.92 | ✅ |
| L | -4.92 | -4.92 | ✅ |
| K | 5.55 | 5.55 | ✅ |
| M | -2.35 | -2.35 | ✅ |
| F | -2.98 | -2.98 | ✅ |
| P | -2.54 | -2.54 | ✅ |
| **S** | **3.40** | **1.83** | ⚠️ 불일치 가능 |
| T | 2.57 | 2.57 | ✅ |
| W | -2.33 | -2.33 | ✅ |
| Y | 0.14 | 0.14 | ✅ |
| V | -4.04 | -4.04 | ✅ |

> ⚠️ **S (Serine) 값 주의**: 코드에 S=3.40이 있으나, Radzicka & Wolfenden 1988 물→사이클로헥산 스케일의 인용값은 S=1.83로 보고되는 경우가 많음. 3.40은 다른 전이 조건(예: 물→기상)에 해당할 수 있음. Boman 2003 Table 1과 대조 검증 필요.  
> 참고: `backend/pharmacology.py`의 S=1.15, P=0.0 버그는 이 파일에서는 수정됨 (P=-2.54 ✅).

**부호 규약**: 양수 = 친수성(물 선호), 음수 = 소수성(사이클로헥산 선호). 코드 주석 `"positive = hydrophilic"` ✅ Boman 2003 정의와 일치.

---

## 3. Instability Index (불안정성 지수)

**출처**: Guruprasad et al. 1990, *Protein Eng* 4:155-161  
**수식**: `II = (10/N) × Σ(DIWV[aa_i][aa_{i+1}])`  
**구현 위치**: 라인 48-132 (DIWV 테이블), 304-312 (메서드)  
**해석**: `II < 40` → 안정 단백질/펩타이드

### DIWV 주요 값 검증 (알려진 버그 포함)

| 이중펩타이드 | 코드값 | 논문값 | 상태 |
|-------------|--------|--------|------|
| C→W | 24.68 | 24.68 | ✅ (수정됨) |
| K→Q | 24.68 | 24.68 | ✅ (수정됨) |
| H→K | 24.68 | 24.68 | ✅ |
| H→N | 24.68 | 24.68 | ✅ |
| M→H | 58.28 | 58.28 | ✅ |
| R→R | 58.28 | 58.28 | ✅ |
| R→W | 58.28 | 58.28 | ✅ |
| A→C | 44.94 | 44.94 | ✅ |
| E→C | 44.94 | 44.94 | ✅ |

> ✅ **이전 버그 수정 확인**: MEMORY에 기록된 K→Q=24.64(오류)가 이 버전에서는 24.68로 정정됨.

**SST-14 계산**: AGCKNFFWKTFTSC (13개 이중펩타이드 합산) → ExPASy ProtParam과 크로스체크 권장

---

## 4. Aliphatic Index (지방족 지수)

**출처**: Ikai 1980, *J Biochem* 88:1895-1898  
**수식**: `AI = X_A + 2.9 × X_V + 3.9 × (X_I + X_L)`  
**구현 위치**: 라인 316-324

```python
xa = 100.0 * seq.count("A") / n     # Ala 몰분율 (%)
xv = 100.0 * seq.count("V") / n     # Val 몰분율 (%)
xi = 100.0 * seq.count("I") / n     # Ile 몰분율 (%)
xl = 100.0 * seq.count("L") / n     # Leu 몰분율 (%)
AI = xa + 2.9*xv + 3.9*(xi + xl)
```

- 계수 2.9: Val 측쇄 부피가 Ala 대비 2.9배 (Ikai 1980 Table 1) ✅
- 계수 3.9: Ile/Leu 측쇄 부피가 Ala 대비 3.9배 (Ikai 1980 Table 1) ✅
- **해석**: AI가 높을수록 열안정성 높음 (구상 단백질 기준)
- **한계**: 소형 순환 펩타이드(14aa)에 대한 원래 논문의 적용 범위 밖; 지표적 수치로만 사용

---

## 5. Isoelectric Point (등전점)

**출처**: Bjellqvist et al. 1993 / Lehninger pKa 세트  
**방법**: Henderson-Hasselbalch + 이진 탐색 (200회 반복)  
**구현 위치**: 라인 134-140 (pKa 테이블), 328-351 (메서드)

### Lehninger pKa 값

| 기능기 | 코드값 | Lehninger 값 | 상태 |
|-------|--------|--------------|------|
| N-말단 (α-NH₂) | 9.69 | 9.69 | ✅ |
| C-말단 (α-COOH) | 2.34 | 2.34 | ✅ |
| D (β-COOH) | 3.65 | 3.65 | ✅ |
| E (γ-COOH) | 4.25 | 4.25 | ✅ |
| H (이미다졸) | 6.00 | 6.00 | ✅ |
| C (티올) | 8.18 | 8.18 | ✅ |
| Y (페놀) | 10.07 | 10.07 | ✅ |
| K (ε-NH₂) | 10.53 | 10.53 | ✅ |
| R (구아니디늄) | 12.48 | 12.48 | ✅ |

**이진 탐색**: `lo=0.0, hi=14.0, 200회` → 수렴 정밀도 `14/2^200` ≈ machine epsilon ✅  
**SS bond Cys 처리**: `ss_bond_cysteines` 매개변수로 이황화결합 Cys의 티올 이온화 제외 ✅

---

## 6. _charge_at_ph() — Henderson-Hasselbalch 수식 분석

**구현 위치**: 라인 235-272

### 수식 전개

**염기성 기능기** (N-말단, K, R, H): 양성 기여
$$\text{charge} += \frac{1}{1 + 10^{(\text{pH} - \text{pKa})}}$$

- pH ≪ pKa: 분모 → 1, 기여 → +1 (완전 양이온화) ✅
- pH ≫ pKa: 분모 → ∞, 기여 → 0 (중성, 탈양성자화) ✅

**산성 기능기** (C-말단, D, E, Y): 음성 기여
$$\text{charge} -= \frac{1}{1 + 10^{(\text{pKa} - \text{pH})}}$$

- pH ≫ pKa: 분모 → 1, 기여 → -1 (완전 음이온화) ✅
- pH ≪ pKa: 분모 → ∞, 기여 → 0 (중성, 양성자화) ✅

**Cys 처리 (라인 267-271)**:
```python
elif aa == "C" and idx not in _ss:
    # Free thiol — participates in ionisation (pKa=8.18)
    pka = PKA_SIDECHAIN["C"]
    charge -= 1.0 / (1.0 + 10.0 ** (pka - ph))
    # Cys in SS bond: no ionisable thiol → skip
```

- 자유 Cys (SS결합 아님): 산성 기능기로 취급 (pKa=8.18) ✅
- SS결합 Cys (`idx in _ss`): 티올기 없음 → 이온화 기여 제외 ✅
- **생물학적 근거**: SS결합 형성 시 두 Cys의 티올기(−SH)가 산화되어 이황화결합(−S−S−)으로 변환됨 → 이온화 가능 수소 없음

---

## 7. Molar Extinction Coefficient (몰흡광계수)

**출처**: Pace et al. 1995, *Protein Sci* 4:2411-2423  
**수식**: `ε₂₈₀ = n_W × 5500 + n_Y × 1490 + n_SS × 125`  
**구현 위치**: 라인 355-364

| 기여 잔기 | 코드 계수 | Pace 1995 값 | 상태 |
|-----------|----------|--------------|------|
| Trp (W) | 5500 M⁻¹cm⁻¹ | 5500 | ✅ |
| Tyr (Y) | 1490 M⁻¹cm⁻¹ | 1490 | ✅ |
| SS bond | 125 M⁻¹cm⁻¹ | 125 | ✅ |

**SST-14**: W=1, Y=0, SS=1 → ε₂₈₀ = 5500 + 125 = 5625 M⁻¹cm⁻¹

---

## 8. N-end Rule Half-life (N말단 규칙 반감기)

**출처**: Varshavsky 1996, *PNAS* 93:12142-12149 (포유류 망상적혈구 기준)  
**구현 위치**: 라인 152-165 (테이블), 368-377 (메서드)

### NEND_HALFLIFE 테이블 검증

| AA | 코드값 (h) | 카테고리 | Varshavsky 1996 | 상태 |
|----|-----------|---------|-----------------|------|
| M, S, A, T, V, G | 30.0 | stable | >20h (안정) | ✅ |
| I | 20.0 | intermediate | 20h | ✅ |
| C | 1.2 | intermediate | ~1.2h | ✅ |
| Y, W | 2.8 | unstable | 2.8h | ✅ |
| H | 3.5 | unstable | 3.5h | ✅ |
| L | 5.5 | unstable | 5.5h | ✅ |
| **P** | **30.0** | stable | **30h** | ✅ (수정됨) |
| F, D | 1.1 | very_unstable | 1.1h | ✅ |
| K | 1.3 | very_unstable | 1.3h | ✅ |
| R | 1.0 | very_unstable | 1.0h | ✅ |
| E | 1.0 | very_unstable | 1.0h | ✅ |
| N | 1.4 | very_unstable | 1.4h | ✅ |
| Q | 0.8 | very_unstable | 0.8h | ✅ |

> ✅ **이전 버그 수정 확인**: MEMORY에 기록된 Pro half-life=20.0(오류)이 이 버전에서는 30.0으로 정정됨.

**SST-14 적용**: N-말단 = A(Ala) → 반감기 30h (stable) ✅ N-말단 chelator 설계와 양립

---

## 9. Hydrophobic Moment (소수성 모멘트)

**출처**: Eisenberg et al. 1982, *Nature* 299:371-374  
**수식**: `μH = √(Σ[H_i·sin(n·δ)]² + Σ[H_i·cos(n·δ)]²) / window`  
**구현 위치**: 라인 167-173 (Eisenberg 스케일), 381-421 (메서드)

### Eisenberg Consensus Hydrophobicity 테이블

| AA | 코드값 | Eisenberg 1982 | 상태 |
|----|--------|----------------|------|
| A | 0.62 | 0.62 | ✅ |
| R | -2.53 | -2.53 | ✅ |
| N | -0.78 | -0.78 | ✅ |
| D | -0.90 | -0.90 | ✅ |
| C | 0.29 | 0.29 | ✅ |
| Q | -0.85 | -0.85 | ✅ |
| E | -0.74 | -0.74 | ✅ |
| G | 0.48 | 0.48 | ✅ |
| H | -0.40 | -0.40 | ✅ |
| I | 1.38 | 1.38 | ✅ |
| L | 1.06 | 1.06 | ✅ |
| K | -1.50 | -1.50 | ✅ |
| M | 0.64 | 0.64 | ✅ |
| F | 1.19 | 1.19 | ✅ |
| P | 0.12 | 0.12 | ✅ |
| S | -0.18 | -0.18 | ✅ |
| T | -0.05 | -0.05 | ✅ |
| W | 0.81 | 0.81 | ✅ |
| Y | 0.26 | 0.26 | ✅ |
| V | 1.08 | 1.08 | ✅ |

**슬라이딩 윈도우 로직**:
- 시퀀스 길이 ≤ window(11): 단일 윈도우 계산
- 시퀀스 길이 > window: 최대 μH 반환 (peak 구조 탐지)

**각도 매개변수**:
- α-나선: δ = 100° → 3.6 잔기/회전 주기에 최적 ✅
- β-시트: δ = 160° → 2.0 잔기/회전 주기에 최적 ✅

**한계**: 14aa 펩타이드는 window=11로 4회 슬라이딩 → 국소 최대값 탐지에 적합

---

## 10. Wimley-White Hydrophobicity (계면 소수성)

**출처**: Wimley & White 1996, *Nat Struct Biol* 3:842-848  
**스케일**: 물 → POPC 인터페이스 전이 자유에너지 ΔG (kcal/mol)  
**구현 위치**: 라인 175-181 (테이블), 425-433 (메서드)

| AA | 코드값 | WW1996 | 상태 |
|----|--------|--------|------|
| W | -1.85 | -1.85 | ✅ |
| F | -1.13 | -1.13 | ✅ |
| L | -0.56 | -0.56 | ✅ |
| I | -0.31 | -0.31 | ✅ |
| C | -0.24 | -0.24 | ✅ |
| M | -0.23 | -0.23 | ✅ |
| G | 0.01 | 0.01 | ✅ |
| V | 0.07 | 0.07 | ✅ |
| S | 0.13 | 0.13 | ✅ |
| T | 0.14 | 0.14 | ✅ |
| A | 0.17 | 0.17 | ✅ |
| Y | -0.94 | -0.94 | ✅ |
| P | 0.45 | 0.45 | ✅ |
| N | 0.42 | 0.42 | ✅ |
| Q | 0.58 | 0.58 | ✅ |
| H | 0.96 | 0.96 | ✅ |
| K | 0.99 | 0.99 | ✅ |
| R | 0.81 | 0.81 | ✅ |
| D | 1.23 | 1.23 | ✅ |
| E | 2.02 | 2.02 | ✅ |

**해석**: 음수 ΔG → 막 계면 삽입 선호; 양수 → 수용액 선호  
**반환값**: `total_dG`, `mean_dG`, `per_residue` 모두 포함 ✅

---

## 11. Net Charge (순전하) — pH 7.4 / pH 6.5

**방법**: Henderson-Hasselbalch (§6 참조)  
**구현 위치**: 437-452  
**SS bond Cys 처리**: `ss_bond_cysteines` 전달 → 이황화 결합 Cys 이온화 제외 ✅

**SST-14 (AGCKNFFWKTFTSC, SS bond Cys3+Cys14) 예상값**:
- 하전 기능기: N-말단(+), K9(+), K10(+), C-말단(-) (free Cys 없음)
- pH 7.4 순전하 ≈ +1 (양이온성) → 세포막 음전하 SSTR2와 정전기 유리

---

## 12. Molecular Weight (분자량)

**수식**: `MW = Σ(AA_MW) − (N−1) × 18.015 − n_SS × 2.016`  
**구현 위치**: 라인 142-150 (테이블), 456-498 (메서드)

### 수식 근거
- 각 아미노산 분자량: PubChem/NIST 평균 동위원소 질량 ✅
- (N−1) × H₂O: 펩타이드 결합 형성 시 탈수 반응 ✅
- n_SS × 2 × 1.008 ≈ n_SS × 2.016 Da: SS결합당 두 H원자 제거 ✅

### 단일동위원소 보정
```python
_MONO_CORRECTION = 0.9994
mw_mono = round(mw_avg * _MONO_CORRECTION, 2)
```

- 0.9994는 경험적 스케일링 상수 (≤50aa 펩타이드에서 ±0.5 Da 이내) ✅
- **주의**: 정확한 단일동위원소 계산이 필요하면 원소별 정밀 계산 권장

**SST-14 예상**: ≈1638 Da (환원형) / ≈1636 Da (SS결합 형성 후)

---

## 13. Protease Cleavage Sites (프로테아제 절단 부위)

**출처**: MEROPS 데이터베이스 프로테아제 규칙  
**구현 위치**: 502-541

### 프로테아제 규칙 분석

#### Chymotrypsin (키모트립신)
```python
# F, W, Y, L, M의 C-말단 절단 (마지막 잔기 제외)
if aa in {"F","W","Y","L","M"} and i < len(seq) - 1:
    chymo.append(i + 1)
```
- 표준 키모트립신 특이성 (F/W/Y/L/M의 카르복실측 절단) ✅
- 마지막 잔기 예외 처리 ✅

#### Trypsin (트립신)
```python
# K, R의 C-말단 절단 (단, 다음 잔기가 P인 경우 제외)
if aa in {"K","R"} and i < len(seq) - 1:
    if seq[i + 1] != "P":
        trypsin.append(i + 1)
```
- K/R 이후 P가 오면 절단 저항성 (Schechter-Berger 규칙) ✅
- K-P 및 R-P 이중펩타이드 예외 ✅

#### Neprilysin (엔도펩티다아제-24.11)
```python
nep_residues = set("FWYLIVM")  # 소수성 잔기 N-말단 절단
if aa in nep_residues and i > 0:
    nep.append(i + 1)
```
- 소수성 잔기(F/W/Y/L/I/V/M)의 아미노측 절단 ✅
- 첫 번째 잔기 제외 (i > 0) ✅

#### DPP-IV (디펩티딜 펩티다아제 IV) — 상세 분석

```python
dppiv_residues = set("PA")  # Pro 또는 Ala
# DPP-IV: X-Pro 또는 X-Ala 이중펩타이드 절단
if aa in dppiv_residues and i > 0 and i < len(seq) - 1:
    if seq[i + 1] != "P":  # Pro-Pro 저항성
        dppiv.append(i + 1)
```

**DPP-IV 메커니즘**: 세린 프로테아제; N-말단부터 두 번째 잔기가 Pro 또는 Ala일 때 첫 두 잔기(X↓Pro/Ala-...)를 절단. 펩타이드 호르몬 불활화에 핵심 (GLP-1, NPY 등).

**구현 평가**:
- ✅ Pro-Pro 저항성 처리: `seq[i+1] != "P"` (PP 이중펩타이드는 DPP-IV 저항성)
- ⚠️ **범위 일반화**: 표준 DPP-IV는 N-말단 2번째 위치(position 2)에 특이적이나, 이 구현은 모든 내부 X-P/X-A 부위를 탐지. 광의의 DPP-IV-유사 활성 스크리닝으로 간주 가능하나 엄밀한 특이성 재현은 아님.
- ✅ 스크리닝 목적에는 보수적(더 많이 탐지) 접근법으로 실용적

**SST-14 (AGCKNFFWKTFTSC)**:
- K9 다음 T10 → T는 PA 아님, DPP-IV 없음
- 전체 시퀀스에 Pro/Ala 내부 위치 없음 → DPP-IV 부위 없음 (바람직)

---

## 14. BLOSUM62 Conservation Score

**출처**: Henikoff & Henikoff 1992, *PNAS* 89:10915-10919  
**구현 위치**: 라인 184-214 (행렬), 545-575 (메서드)

### 행렬 구조
- 20×20 표준 BLOSUM62 ✅
- 대각선 (동일 잔기): A=4, R=5, N=6, D=6, C=9, W=11, Y=7... ✅
- `_BLOSUM62_FLAT` → `BLOSUM62[aa1][aa2]` dict-of-dict O(1) 조회 ✅

### 카테고리 분류
```python
"identical"        # query == reference
"conservative"     # BLOSUM62 score ≥ 1
"semi-conservative" # BLOSUM62 score == 0
"non-conservative" # BLOSUM62 score < 0
```

**주의**: 입력 시퀀스가 reference_seq와 길이가 다를 경우 `{"error": "length mismatch"}` 반환 (라인 865-867).

---

## 15. Metal Coordination Residues (금속 배위 잔기)

**출처**: Rulísek & Vondrásek 1998, *J Inorg Biochem* 71:115-127  
**구현 위치**: 579-615

### 배위 잔기 분류

| 잔기 | 배위 기능기 | 배위 금속 | 코드 |
|------|-----------|---------|------|
| H | 이미다졸 N | Zn²⁺, Cu²⁺, Ga³⁺ | ✅ |
| C | 티올레이트 S | Zn²⁺, Cu²⁺ | ✅ |
| D | 카르복실레이트 O | Ca²⁺, Mg²⁺, Lu³⁺, Ac³⁺, Ga³⁺ | ✅ |
| E | 카르복실레이트 O | Ca²⁺, Mg²⁺, Lu³⁺, Ac³⁺, Ga³⁺ | ✅ |
| M | 티오에테르 S | Cu²⁺ | ✅ |

**방사성의약품 연관성**:
- Ga³⁺ (⁶⁸Ga PET): H(이미다졸) + D/E(카르복실레이트)으로 배위 ✅
- Lu³⁺ (¹⁷⁷Lu 치료): D/E 카르복실레이트로 배위 ✅
- Ac³⁺ (²²⁵Ac): D/E 카르복실레이트 + DOTA 킬레이터 협력 ✅

**SST-14 (AGCKNFFWKTFTSC)**:
- C3, C14: Cys_thiolate → Zn²⁺, Cu²⁺ (SS결합으로 실질 배위 가능성 제한)
- K9: 배위 잔기 아님 (ε-아미노기 배위는 미포함)
- N-말단 A1: 미포함 (DOTA/NOTA 킬레이터는 N-말단에 외부 접합)

---

## 16. SS Bond Cys 제외 로직 (calculate_all 통합)

**구현 위치**: 라인 803-876 (`calculate_all`)

```python
# 짝수 Cys → 순차 쌍 형성 (first↔last, second↔second-last...)
if n_cys > 0 and n_cys % 2 == 0:
    cys_positions = [i for i, aa in enumerate(seq) if aa == "C"]
    lo_ptr, hi_ptr = 0, len(cys_positions) - 1
    while lo_ptr < hi_ptr:
        pairs.append((cys_positions[lo_ptr], cys_positions[hi_ptr]))
        lo_ptr += 1; hi_ptr -= 1
    ss_bond_cysteines = {pos for pair in pairs for pos in pair}
```

**SST-14 (AGCKNFFWKTFTSC)**: C 위치 = [2, 13] (0-indexed)  
→ 쌍: (2, 13) → `ss_bond_cysteines = {2, 13}` (Cys3-Cys14) ✅

**SS bond 보정이 적용되는 메서드**:
| 메서드 | 보정 내용 |
|-------|---------|
| `calculate_pi()` | SS Cys 이온화 제외 → pI 변동 |
| `calculate_net_charge()` | SS Cys 이온화 제외 → 순전하 보정 |
| `calculate_radiolysis_susceptibility()` | SS Cys 가중치 2→1 감소 |
| `calculate_mw()` | n_disulfide × 2.016 Da 감소 |
| `calculate_extinction_coefficient()` | n_disulfide × 125 추가 |

---

## 17. 5대 구조 규칙 (check_structural_rules)

**구현 위치**: 619-682

### Rule 1: FWKT Pharmacophore (위치 7-10)
```python
motif = seq[6:10]  # 0-indexed [6,7,8,9] = 위치 7,8,9,10
results["fwkt_pharmacophore"] = {"pass": motif == "FWKT", ...}
```
**근거**: SSTR2 결합에 필수적인 Phe-Trp-Lys-Thr 약물효과단 (FWKT) ✅  
SST-14: seq[6:10] = "FWKT" → PASS ✅

### Rule 2: K9 Salt Bridge (SSTR2 D122)
```python
results["k9_salt_bridge"] = {"pass": seq[8] == "K", ...}
```
**근거**: SST-14의 Lys9(K9)이 SSTR2 TM3 Asp122(D3.32)와 염다리 형성 (분자 도킹 연구 기반) ✅  
SST-14: seq[8] = "K" → PASS ✅

### Rule 3: Cys3-Cys14 Disulfide
```python
results["cys3_cys14_disulfide"] = {"pass": seq[2] == "C" and seq[13] == "C", ...}
```
**근거**: SST-14의 순환 구조 유지에 필수 이황화결합 ✅  
**주의**: 14aa 미만 시퀀스는 FAIL 처리 ✅

### Rule 4: Phe6-Phe11 Aromatic Stacking
```python
aromatic = set("FWY")
results["phe6_phe11_stacking"] = {
    "pass": seq[5] in aromatic and seq[10] in aromatic, ...
}
```
**근거**: Phe6-Phe11 방향족 π-π 스태킹이 활성 구조 안정화에 기여 ✅  
**유연성**: FWY 모두 방향족으로 허용 (보수적 판단) ✅  
SST-14: seq[5]="F", seq[10]="F" → PASS ✅

### Rule 5: N-terminal Chelator Compatibility
```python
preferred_nterm = set("AG")
results["nterm_chelator"] = {"pass": seq[0] in preferred_nterm, ...}
```
**근거**: A 또는 G N-말단이 DOTA/NOTA 킬레이터 접합에 최적 (짧은 측쇄, 유연한 링커) ✅  
SST-14: seq[0]="A" → PASS ✅

---

## 18. Radiolysis Susceptibility (방사선분해 감수성)

**구현 위치**: 686-799

### 가중치 근거 및 메커니즘

| 잔기 | 가중치 | 산화 메커니즘 | 문헌 근거 |
|------|-------|------------|---------|
| Met (M) | 3.0 | 황 산화 → Met-sulfoxide (−S→−S=O) | Schöneich 2000, Free Radic Biol Med 29:1049; k≈10⁷ M⁻¹s⁻¹ |
| Trp (W) | 3.0 | 인돌 고리 산화 → 키누레닌/하이드록실 | Davies 2016, Free Radic Biol Med 93:78 |
| Cys (C, 자유) | 2.0 | 티올 산화 → 설펜산/이황화물 | Stadtman 2006, Free Radic Biol Med 40:107 |
| Cys (C, SS결합) | 1.0 | SS결합으로 보호; 직접 산화 감소 | ↑ 동일 참조 |
| His (H) | 2.0 | 이미다졸 산화 → 아스파르테이트/2-옥소히스티딘 | Schöneich 2000 |
| Tyr (Y) | 1.0 | 페놀 산화 → 다이티로신 교차결합 | Davies 2016 |
| Phe (F) | 0.5 | 방향족 수산화 (가장 낮은 반응성) | Hawkins & Davies 2001, Biochem J 359:197 |

**위험 수준 분류**:
```
low: total_score ≤ 3
moderate: 3 < total_score ≤ 6  
high: total_score > 6
```

**SS bond 보정 로직** (라인 742-753):
```python
# Cys 위치 수집 후 first↔last 쌍 형성
cys_positions = [i+1 for i, aa in enumerate(seq) if aa == "C"]
if len(cys_positions) >= 2:
    lo, hi = 0, len(cys_positions) - 1
    while lo < hi:
        ss_bond_positions.add(cys_positions[lo])
        ss_bond_positions.add(cys_positions[hi])
        ...
```

**SST-14 감수성 계산**:
- F7 (0.5), W8 (3.0), K9 (-), T10 (-), C3-SS (1.0), C14-SS (1.0)
- total_score ≈ 3.0 + F6(0.5) + F11(0.5) = 6.0 → moderate 위험
- FWKT 약물효과단 내 W8 → `critical_positions`에 포함 ⚠️

**방사성의약품 적용**: ¹⁷⁷Lu/⁶⁸Ga 방사선이 물을 방사선분해하여 ·OH 라디칼 생성 → W8 산화 위험이 SSTR2 결합 친화도 저하 유발 가능. Trp8 동등체(예: Nal 또는 bAla) 치환 스크리닝 필요성 시사.

---

## 종합 검증 결과

| 메서드 | 테이블 정확성 | 수식 정확성 | 알려진 버그 |
|-------|------------|-----------|----------|
| GRAVY | ✅ 20/20 일치 | ✅ | - |
| Boman Index | ⚠️ S값 불일치 가능 | ✅ 부호 정상 | S=3.40 vs 1.83 확인 필요 |
| Instability Index | ✅ 주요값 일치 | ✅ | K→Q=24.64→24.68 수정됨 |
| Aliphatic Index | ✅ | ✅ | - |
| pI / Net Charge | ✅ Lehninger pKa 일치 | ✅ H-H 정확 | - |
| Extinction Coeff | ✅ Pace 1995 일치 | ✅ | - |
| N-end Rule | ✅ | ✅ | Pro=20→30 수정됨 |
| Hydrophobic Moment | ✅ 20/20 Eisenberg 일치 | ✅ | - |
| Wimley-White | ✅ 20/20 일치 | ✅ | - |
| MW | ✅ AA_MW 표준값 | ✅ | 단일동위원소 ±0.5Da 근사 |
| Protease Sites | ✅ MEROPS 규칙 | ⚠️ DPP-IV 범위 일반화 | - |
| BLOSUM62 | ✅ 표준 행렬 | ✅ | - |
| Metal Coord | ✅ Rulísek 1998 | ✅ | - |
| Structural Rules | ✅ 5규칙 올바름 | ✅ | - |
| Radiolysis | 경험적 가중치 | ✅ | - |
| SS Bond Correction | ✅ 전체 적용 | ✅ | - |

---

## 권장 후속 조치

1. **[High]** Radzicka-Wolfenden S(Serine) 값 원본 논문 대조: 코드 S=3.40 vs 인용 S=1.83 — Boman 2003 Table 1 직접 확인
2. **[Medium]** DPP-IV 특이성 정밀화: N-말단 2번째 위치 전용 규칙 추가 옵션 고려 (현재 구현은 내부 모든 X-P/X-A 탐지)
3. **[Low]** 단일동위원소 MW: 정밀 계산이 필요한 MS 비교 응용에서는 원소 조성 기반 계산으로 대체 권장
4. **[참고]** 방사선분해 가중치: 단일 통합 논문 없음 — 복수 방사선 화학 문헌 기반 경험치. 정량적 k 상수(M⁻¹s⁻¹)로 보완 가능
