# 후보 Stability 분석 — cand03 및 T3 변이체 8종

**작성일**: 2026-05-12  
**작성**: reviewer-pharma (PRST_N_FM 팀)  
**버전**: v1.0  
**근거 회귀 테스트**: pharmacology_guards 39/39 PASS (2026-05-12)  
**참고 파일**: `runs_local/cand03_variants/cand03_variants.json` (v1.1)

---

> ⚠️ **HEURISTIC 선언 (본 문서 전체)**  
> 본 문서의 `predict_half_life()` 출력값은 모두 **HEURISTIC ranking score** (step08_stability.py, 잔기 취약성 가중합 기반)이며, 실 in-vivo/in-vitro 혈청 반감기가 **아닙니다**. 숫자는 후보 간 상대 순위에만 사용하고, 절대값을 임상 예측으로 인용 금지. 신뢰 등급: **HEURISTIC / LOW**. 실 반감기는 `docs/wetlab/halflife_methodology.md` 프로토콜로 측정.

---

## 1. 후보 8종 Stability 매트릭스

### 1.1 기본 약리학 파라미터

pharmacology_guards 사전 실행 결과: **39/39 PASS** (2026-05-12, 0.15s)

| # | ID | 서열 | GRAVY | MW (Da) | Net Charge pH7.4 | Chymo 취약 | Tryp 취약 | NEP 취약 | HL score⚠️ |
|---|----|----|-------|---------|-----------------|----------|----------|---------|----------|
| 1 | **cand03** | AICKNFFWKTFTSC | +0.379 | 1,696.0 | +2 | 4 | 2 | 5 | **16.60** |
| 2 | **ILCKKFFWKTFTSC** | ILCKKFFWKTFTSC | +0.493 | 1,752.1 | +3 | 5 | 3 | 6 | **12.80** |
| 3 | **IGCWWFFWKTFTSC** | IGCWWFFWKTFTSC | +0.621 | 1,812.0 | +1 | 6 | 1 | 7 | **19.34** |
| 4 | **AGCKNDFWKTLTSC** | AGCKNDFWKTLTSC | −0.350 | 1,573.7 | +1 | 3 | 2 | 3 | **17.85** |
| 5 | **QTCKNFFWKTFTSC** | QTCKNFFWKTFTSC | −0.371 | 1,741.0 | +2 | 4 | 2 | 4 | **16.76** |
| 6 | **AGCKWEFWKTLTSC** | AGCKWEFWKTLTSC | −0.164 | 1,659.8 | +1 | 4 | 2 | 4 | **17.24** |
| 7 | **var07_I2K** | AKCKNFFWKTFTSC | −0.221 | 1,711.0 | +3 | 4 | 3 | 4 | **12.78** |
| 8 | **var12_T12dThr** | AICKNFFWKTF[dT]SC | +0.379 | 1,696.0 | +2 | 4 | 2 | 5 | **16.72** |

**⚠️ 주석**: 모든 HL score는 HEURISTIC ranking score (단위 없음, 상대 비교 전용). [신뢰 등급: HEURISTIC / LOW]

### 1.2 부호 규약 확인 (pharmacology_guards 통과 항목)

| 척도 | 부호 규약 | 기준 |
|------|---------|------|
| GRAVY (Kyte-Doolittle 1982) | 양수 = 소수성 高 | — |
| Net Charge | 양수 = 전체 양전하 (pH 7.4) | K(+1), R(+1), D(−1), E(−1) 합산 |
| Chymo 취약 | 높을수록 chymotrypsin 절단 위험 | F, W, Y, L C-terminal 개수 (마지막 제외) |
| Tryp 취약 | 높을수록 trypsin 절단 위험 | K, R C-terminal 개수 (not before P) |
| NEP 취약 | 높을수록 neprilysin 분해 위험 | F, W, Y, L, I, M 잔기 수 |

---

## 2. 위치별 Protease 취약점 분석

### 2.1 cand03 (AICKNFFWKTFTSC) — 참조 구조

```
위치:  1  2  3  4  5  6  7  8  9  10 11 12 13 14
서열:  A  I  C  K  N  F  F  W  K  T  F  T  S  C
          │     │        │  │  │  │     │
          ↓     ↓        ↓  ↓  ↓  ↓     ↓
          NEP   Tryp    Chymo Chymo Tryp     Chymo
          (I2)  (K4)   NEP   NEP  (K9)    NEP
                       (F6)  (F7) ←FWKT→  (F11)
                              (W8)
SS bond: Cys3 ─────────────────────────── Cys14

pharmacophore FWKT 보존 위치: F6, F7, W8, K9 (절단하면 활성 소실)
위험도 최고 절단 부위: F6-F7 (double chymo), W8 (NEP+Chymo), K9 (Tryp)
```

### 2.2 후보별 취약 부위 상세

#### 후보 1 — cand03 (AICKNFFWKTFTSC)
- **Chymo**: F6↓, F7↓, W8↓, F11↓ (4개)
- **Tryp**: K4↓, K9↓ (2개)
- **NEP**: I2, F6, F7, W8, F11 (5개)
- **Carboxypeptidase**: C14→S13→T12 순 소화 (C-term 취약)
- **SS bond**: Cys3-Cys14 — 고리화로 내부 취약성 감소

**핵심 리스크**: F6-F7-W8 연속 chymotrypsin 취약 구간이 pharmacophore FWKT에 직결. K4 trypsin 절단이 빠를 경우 N-terminal 단편 분리.

---

#### 후보 2 — ILCKKFFWKTFTSC
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
I  L  C  K  K  F  F  W  K  T  F  T  S  C
   ↑     ↑  ↑  ↑  ↑  ↑  ↑     ↑
   NEP   T  T  C  C  C  T     C
         (K4)(K5)(F6)(F7)(W8)(K9)(F11)
```
- **Chymo**: 5개 (L2 추가 — L이 chymotrypsin 기질)
- **Tryp**: 3개 (K4, K5 추가, K9)
- **추가 위험**: K5 추가로 K4-K5 이중 trypsin 취약 구간 → 매우 불안정
- **HL score**: 12.80 (최저 수준 중 하나)
- **수식 제안**: K5 위치가 중요 — K5→Q 또는 K5→D 전하 중화 검토

---

#### 후보 3 — IGCWWFFWKTFTSC
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
I  G  C  W  W  F  F  W  K  T  F  T  S  C
   ↑     ↑  ↑  ↑  ↑  ↑  ↑     ↑
   NEP   C  C  C  C  C  T     C
         (W4)(W5)(F6)(F7)(W8)(K9)(F11)
```
- **Chymo**: 6개 (W4, W5, F6, F7, W8, F11)
- **Tryp**: 1개 (K9만)
- **HL score**: 19.34 (상대적으로 높음 — tryp 취약 낮음)
- **주의**: GRAVY +0.621 — 용해성 문제 심각. 실험 전 용해도 확인 필수
- **수식 제안**: 고 GRAVY로 응집 위험. PEG화 또는 Glu 도입으로 전하 중화 권장

---

#### 후보 4 — AGCKNDFWKTLTSC
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
A  G  C  K  N  D  F  W  K  T  L  T  S  C
         ↑        ↑  ↑  ↑     ↑
         T        C  C  T     C
         (K4)     (F7)(W8)(K9)(L11)
```
- **Chymo**: 3개 (F7, W8, L11)
- **Tryp**: 2개 (K4, K9)
- **HL score**: 17.85 (상대적으로 양호)
- **특징**: GRAVY −0.350 (친수성), Charge +1 (Cluster D 유리)
- **D6 위치**: D→F 대비 음전하 도입으로 K4와 근접 salt bridge 가능
- **수식 제안**: L11→Cha (chymotrypsin 저항) 권장

---

#### 후보 5 — QTCKNFFWKTFTSC
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
Q  T  C  K  N  F  F  W  K  T  F  T  S  C
         ↑        ↑  ↑  ↑  ↑     ↑
         T        C  C  C  T     C
         (K4)     (F6)(F7)(W8)(K9)(F11)
```
- **Chymo**: 4개, **Tryp**: 2개 — cand03과 유사 취약점
- **HL score**: 16.76 (cand03 유사)
- **특징**: GRAVY −0.371 (친수성, Q1+T2 기여), Charge +2
- **수식 제안**: N-terminal Ac 표준 적용 + D-Thr12

---

#### 후보 6 — AGCKWEFWKTLTSC
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
A  G  C  K  W  E  F  W  K  T  L  T  S  C
         ↑  ↑     ↑  ↑  ↑     ↑
         T  C     C  C  T     C
         (K4)(W5) (F7)(W8)(K9)(L11)
```
- **Chymo**: 4개 (W5, F7, W8, L11)
- **Tryp**: 2개 (K4, K9)
- **HL score**: 17.24
- **특징**: Charge +1 (E6 도입), GRAVY −0.164
- **E6**: Glu 도입으로 charge 중화 긍정적 → 방사성의약품 비특이적 결합↓
- **수식 제안**: W5→F 또는 W5→Nal로 절단 위험 감소 + L11→Cha

---

#### 후보 7 — var07_I2K (AKCKNFFWKTFTSC)
```
1  2  3  4  5  6  7  8  9  10 11 12 13 14
A  K  C  K  N  F  F  W  K  T  F  T  S  C
   ↑  ↑  ↑        ↑  ↑  ↑  ↑     ↑
   T  SS T        C  C  C  T     C
   (K2) (K4)     (F6)(F7)(W8)(K9)(F11)
```
- **Tryp**: 3개 (K2, K4, K9) — 최고 취약
- **HL score**: 12.78 (최저)
- **Charge**: +3 (DOTA 미결합 상태) → 비특이적 결합 우려
- **DOTA 결합 후**: K2-ε에 DOTA 결합 → DOTA carboxylates(−2)로 effective charge ≈ +1
- **수식 제안**: K2-DOTA 필수 결합 후 사용. K2-NH2 유리 상태로는 불안정 + 하전 과잉

---

#### 후보 8 — var12_T12dThr (AICKNFFWKTF[dT]SC)
```
cand03와 동일 서열, pos12 T→D-Thr (L-form → D-form, 동일 mass)
```
- **Chymo, Tryp, NEP**: cand03 동일 (4/2/5)
- **HL score baseline**: 16.72 (cand03 16.60 대비 +0.12)
- **HL score + d_amino_acid 수식 적용**: **64.72** [HEURISTIC] (+48h bonus by model)
- **D-Thr12 효과**: pos12 local chymotrypsin 저항 (F11-[dT12] 결합 — protease L-isomer 선호적 인식 회피)
- **화학 주의**: D-Thr12는 키랄 순도 확인 필수 (chiral HPLC 또는 optical rotation)

---

## 3. Modification 효과 정량화 (HEURISTIC Score 기준)

> ⚠️ 아래 표의 모든 HL score 변화는 ranking score 차이이며 실 반감기 변화가 아닙니다. [HEURISTIC / LOW]

### 3.1 cand03 기준 modification 효과 비교

| Modification | cand03 HL score⚠️ | Δ score | 신뢰 등급 |
|-------------|-----------------|---------|---------|
| Baseline (no mod) | 16.60 | — | HEURISTIC |
| + D-Thr12 (d_amino_acid) | 64.72 | **+48.12** | HEURISTIC |
| + C18 fatty acid (K4) | 136.60 | **+120.0** | HEURISTIC |
| + PEG 20kDa (K9) | 112.60 | **+96.0** | HEURISTIC |
| + D-Thr12 + C18 fatty acid | 184.60 | **+168.0** | HEURISTIC |
| + D-Thr12 + substitution | 76.60 | **+60.0** | HEURISTIC |

**해석 (HEURISTIC)**: 순위 기준으로 C18 지방산 acylation > PEG화 > D-아미노산 순. 조합 시 상가 효과. 단, 방사성의약품으로서 C18 acylation은 MW 증가 + 대사 복잡성 추가 — 실 PK에서 이득이 모델보다 적을 수 있음.

### 3.2 ILCKKFFWKTFTSC 특화 modification 권장

ILCKKFFWKTFTSC (HL score 12.80, 가장 취약)의 문제:
1. **K5 추가 Trypsin 위험**: K4-K5 연속 → tryp 절단 이중 노출
2. **L2 Chymotrypsin**: pos2 Leu → chymo 추가 취약

권장 modification:
| 위치 | 현재 | 권장 | 이유 |
|------|------|------|------|
| pos5 K | Lys | **D-Lys** 또는 **Orn** | Trypsin L-Lys 선호 → D-Lys 저항성. Orn은 Lys보다 짧아 tryp 인식 약화 |
| pos5 K | Lys | **Arg (K→R)** | guanidinium = tryp 기질이나 결합 포켓 내 H-bond 기여 가능 — 선택적 적용 |
| pos2 L | Leu | **D-Leu** | Chymo L-Leu 선호 → D-Leu로 저항성 향상 |
| C-term | -SC | **-SC-NH2** (amidation) | Carboxypeptidase 차단 |
| N-term | Ac- | **Ac- (acetylation)** | Aminopeptidase 차단 |

---

## 4. 각 후보 최종 합성 권장안

아래는 pharmacophore 보존 + 최소 stability 향상을 위한 **표준 합성 권장 modification**이다.

| 후보 | 서열 | 표준 Mod | 추가 권장 Mod | 최종 합성 권장 |
|------|------|---------|------------|-------------|
| **cand03** | AICKNFFWKTFTSC | Ac-N / NH2-C | D-Thr12 | **Ac-AICKNFFWKTF[dT]SC-NH2** |
| **ILCKKFFWKTFTSC** | ILCKKFFWKTFTSC | Ac-N / NH2-C | K5→D-Lys OR Orn; D-Leu2 | **Ac-I[dL]CK[dK]FFWKTFTSC-NH2** |
| **IGCWWFFWKTFTSC** | IGCWWFFWKTFTSC | Ac-N / NH2-C | PEG(short) 또는 Glu 도입 용해도 개선 | **Ac-IGCWWFFWKTFTSC-NH2** (용해도 테스트 우선) |
| **AGCKNDFWKTLTSC** | AGCKNDFWKTLTSC | Ac-N / NH2-C | L11→Cha (chymo 저항) | **Ac-AGCKNDFWKT[Cha]TSC-NH2** |
| **QTCKNFFWKTFTSC** | QTCKNFFWKTFTSC | Ac-N / NH2-C | D-Thr12 | **Ac-QTCKNFFWKTF[dT]SC-NH2** |
| **AGCKWEFWKTLTSC** | AGCKWEFWKTLTSC | Ac-N / NH2-C | L11→Cha | **Ac-AGCKWEFWKT[Cha]TSC-NH2** |
| **var07_I2K** | AKCKNFFWKTFTSC | K2-ε-NH2-DOTA | (DOTA 결합 필수) | **Ac-DOTA[K2]-CKNFFWKTFTSC-NH2** (DOTA=킬레이터) |
| **var12_T12dThr** | AICKNFFWKTF[dT]SC | Ac-N / NH2-C | 이미 D-Thr12 포함 | **Ac-AICKNFFWKTF[dT]SC-NH2** |

> **표준 modification 근거**: Ac-N/C-NH2 = exopeptidase 저항 2–4배 향상 (Erspamer 1992). SS bond = Cys3-Cys14 oxidative folding (DMSO/AcOH 또는 I2/MeOH 조건).

---

## 5. pharmacology_guards 통과 검증

### 5.1 회귀 테스트 결과

```
python -m pytest pipeline_local/tests/test_pharmacology_guards.py -q
결과: 39 passed in 0.15s  ✅
날짜: 2026-05-12
```

### 5.2 후보별 GRAVY 범위 검사 (assert_in_range 기준: −1.0 ~ +0.5)

| 후보 | GRAVY | 범위 판정 | 비고 |
|------|-------|---------|------|
| cand03 | +0.379 | ✅ PASS | 허용 범위 내 |
| ILCKKFFWKTFTSC | +0.493 | ⚠️ BORDERLINE | +0.5 경계 접근 — 용해도 확인 필요 |
| **IGCWWFFWKTFTSC** | **+0.621** | **❌ FAIL** | > +0.5 → 용해도 문제 고위험, 실험 전 용해도 테스트 필수 |
| AGCKNDFWKTLTSC | −0.350 | ✅ PASS | 친수성 |
| QTCKNFFWKTFTSC | −0.371 | ✅ PASS | 친수성 |
| AGCKWEFWKTLTSC | −0.164 | ✅ PASS | |
| var07_I2K | −0.221 | ✅ PASS | |
| var12_T12dThr | +0.379 | ✅ PASS | cand03 동일 |

### 5.3 Net Charge 검사 (방사성의약품 권장: |charge| ≤ 2)

| 후보 | Charge | 판정 | 비고 |
|------|--------|------|------|
| cand03 | +2 | ✅ 허용 | |
| ILCKKFFWKTFTSC | **+3** | ⚠️ 높음 | K5 추가로 +3 — 비특이적 결합 우려. 수식 필요 |
| IGCWWFFWKTFTSC | +1 | ✅ 우수 | |
| AGCKNDFWKTLTSC | +1 | ✅ 우수 | D6 기여 |
| QTCKNFFWKTFTSC | +2 | ✅ 허용 | |
| AGCKWEFWKTLTSC | +1 | ✅ 우수 | E6 기여 |
| var07_I2K | **+3** | ⚠️ 높음 | DOTA 결합 필수 (DOTA−2 → charge≈+1) |
| var12_T12dThr | +2 | ✅ 허용 | |

### 5.4 HEURISTIC 함수 사용 선언 (필수)

본 문서 사용 heuristic 함수:
- `predict_half_life(seq, mods)` — **HEURISTIC ranking score, 신뢰 등급 LOW**
- `_PROTEASE_VULNERABILITY[aa]` — 정량 문헌 출처 부재 (VR-S5-01 partial), 상대 순위만 유효
- `suggest_modifications()` — 휴리스틱 우선순위, 실 합성 효율·임상 결과 보장 X

---

## 6. 종합 순위 (Stability × Selectivity 복합 점수)

### 6.1 Scoring 기준

```
Composite Score = HL_score_rank × 0.5 + Selectivity_rank × 0.3 + Synthesizability_rank × 0.2
```

> 참고: Selectivity 데이터는 Boltz-2 iPTM 기반 (2026-05-11 도킹). 현재 cand03만 iPTM 확인됨; 나머지는 추정.

### 6.2 Stability 순위 (HL score 기준, 내림차순)

| 순위 | 후보 | HL score⚠️ | Stability 등급 |
|------|------|----------|-------------|
| 1 | IGCWWFFWKTFTSC | 19.34 | 상 (단, GRAVY FAIL) |
| 2 | AGCKNDFWKTLTSC | 17.85 | 상 |
| 3 | AGCKWEFWKTLTSC | 17.24 | 상 |
| 4 | var12_T12dThr | 16.72 | 중-상 |
| 5 | QTCKNFFWKTFTSC | 16.76 | 중 |
| 6 | cand03 | 16.60 | 중 |
| 7 | ILCKKFFWKTFTSC | 12.80 | 하 |
| 8 | var07_I2K | 12.78 | 하 (DOTA 없이) |

### 6.3 최종 통합 순위

| 순위 | 후보 | 이유 | 권장 |
|------|------|------|------|
| **🥇 1** | **var12_T12dThr** | cand03 Boltz 검증 완료 (SSTR2 iPTM 0.952) + D-Thr12 stability 향상 → 실용성 最高 | **1순위 합성 대상** |
| **🥈 2** | **AGCKNDFWKTLTSC** | HL 최상위권 + GRAVY PASS + Charge +1 → 방사성의약품 이상적 PK | Boltz 도킹 후 결합력 확인 필요 |
| **🥉 3** | **AGCKWEFWKTLTSC** | HL 양호 + E6(charge중화) + Charge +1 | Boltz 도킹 후 결합력 확인 필요 |
| 4 | cand03 | Boltz 검증 완료 + stability 중간 | baseline 참조용 + var12와 비교 |
| 5 | QTCKNFFWKTFTSC | HL 중간 + GRAVY 친수성 | Boltz 미확인, 차순위 |
| 6 | IGCWWFFWKTFTSC | HL 최상 but GRAVY FAIL → 용해도 문제 | GRAVY 문제 해결 후 고려 |
| 7 | ILCKKFFWKTFTSC | HL 낮음 + Charge +3 | K5 수식 후 재평가 |
| 8 | var07_I2K | HL 최하 + Charge +3 | DOTA 결합 필수; theranostic 전용 |

---

## 7. 검증 필요 항목 (§검증 필요)

1. **IGCWWFFWKTFTSC 용해도**: GRAVY +0.621 초과 → 실험 전 용해도 테스트 (PBS, DMSO 혼합 비율) 필수. **합성 전 GRAVY 개선 modification 권장.**
2. **ILCKKFFWKTFTSC K5 수식 효과**: D-Lys5 또는 Orn5 치환 후 실제 trypsin 저항성 변화 — in-vitro 확인 필요.
3. **var07_I2K DOTA stoichiometry**: K2-ε-NH2 단일 DOTA 결합 효율 (>90% required) — HPLC MS 확인 필요 (C-07 규칙).
4. **Boltz 미도킹 5종**: AGCKNDFWKTLTSC, QTCKNFFWKTFTSC, AGCKWEFWKTLTSC, ILCKKFFWKTFTSC, IGCWWFFWKTFTSC — SSTR 결합 iPTM 미확인. 순위는 stability 데이터만 반영.
5. **_PROTEASE_VULNERABILITY 스코어 출처**: 현재 정량 문헌 출처 없음 (VR-S5-01 partial). 상대 순위 사용은 유효하나 절대값 인용 불가. Trypsin/Chymotrypsin kcat/KM 문헌 보강 필요.

---

## 참고 문헌

1. **Erspamer V** (1992). Peptide stability in biological fluids. *Regul Pept* 37:1–19.
2. **Patel YC** (1994). Somatostatin receptors and pharmacological effects. *Endocrine* 2:101–109.
3. **Kyte J, Doolittle RF** (1982). J Mol Biol 157:105–132. [GRAVY]
4. **Guruprasad K, et al.** (1990). Protein Eng 4:155–161. [Instability Index]
5. **cand03_variants.json v1.1** (2026-05-12, reviewer-chemistry). [변이체 설계 근거]
6. **Boltz-2 docking results** (2026-05-11, PRST_N_FM pipeline). [iPTM 데이터 — cand03만 확인됨]
7. **Varshavsky A** (1996). PNAS 93:12142–12149. [N-end rule, Pro=30h]
8. **Wimley WC, White SH** (1996). Nat Struct Biol 3:842–848. [Wimley-White scale]
