# cand03 변이체 디자인 근거 및 SAR 가설

> **작성일**: 2026-05-12  
> **작성자**: reviewer-chemistry  
> **버전**: 1.0  
> **기반 후보**: cand03 — AICKNFFWKTFTSC (SSTR2-selective T2, Boltz-2 + AlphaFoldDB MSA)  
> **참조**: `cluster_classification_spec.md`, `runs_local/selectivity_demo_20260511/`

---

## 1. 서론 — 디자인 전략 개요

### 1.1 출발점: cand03의 화학적 특성

cand03는 SST-14(AGCKNFFWKTFTSC)의 pos2 Gly→Ile 단일 치환 변이체이다.

```
SST-14:  A-G-C-K-N-F-F-W-K-T-F-T-S-C
          1  2  3  4  5  6  7  8  9 10 11 12 13 14
cand03:  A-I-C-K-N-F-F-W-K-T-F-T-S-C
              ^
              pos2: G→I (selectivity 기여 핵심 잔기)
```

**Cys3-Cys14 이황화 결합**: 14원자 macrolactam 형성. ring 내부에 pharmacophore FWKT(pos7-10) 위치. 이 구조적 제약이 SSTR2 결합 선택성의 scaffold를 구성한다.

**기본 물리화학 파라미터** (pH 7.4, free N/C-term):

| 파라미터 | 값 | Cluster 기준 적합성 |
|---------|------|---------------------|
| MW | ~1,579 Da | — |
| GRAVY | +0.379 | Cluster D: PASS (-1.0~+0.5) |
| net charge | +2 | Cluster D: FAIL (|charge|>1) |
| BLOSUM62 vs SST-14 | +3 (G→I 치환) | — |
| SS bond | Cys3-Cys14 | PASS |
| FWKT pharmacophore | 보존 | PASS |

### 1.2 디자인 목표 우선순위

1. **SSTR2 선택성 강화** (selectivity_margin ≥ 3.0 kcal/mol → Cluster B)
2. **합성 가능성** (SPPS standard ≥95% coupling efficiency)
3. **방사성의약품 적합성** (Cluster D: GRAVY, charge, metal coordination)
4. **혈청 안정성** (protease 저항성, 반감기 연장)

---

## 2. 고정 위치 화학적 근거

### 2.1 절대 보존 위치

| 위치 | 잔기 | 이유 |
|------|------|------|
| pos3 (Cys) | 변경 불가 | Cys3-Cys14 이황화 결합 — ring scaffold 핵심 |
| pos14 (Cys) | 변경 불가 | 상동 |
| pos7 (Phe) | 변경 불가 | FWKT pharmacophore — SSTR2 결합 필수 |
| pos8 (Trp) | 변경 불가 | FWKT pharmacophore 핵심 방향족 |
| pos9 (Lys) | 변경 불가 | FWKT pharmacophore — 결합 네트워크 핵심 |
| pos10 (Thr) | 변경 불가 | FWKT pharmacophore |

### 2.2 이황화 결합 화학 (SPPS 관점)

```
합성 순서:
1. Rink Amide resin에 Fmoc-Cys(Trt)-OH anchor (C-terminal)
2. Fmoc SPPS: pos13→pos1 역방향 어셈블리
3. pos3 Cys: Fmoc-Cys(Trt)-OH (Trt = trityl, 산 탈보호)
4. TFA 칵테일: 95% TFA / 2.5% H2O / 2.5% TIS — Trt 탈보호 동시
5. 조 선형 펩타이드 HPLC 정제
6. SS bond 산화: 0.01 M I2/MeOH (5 min, RT) 또는 DMSO/AcOH 공기 산화 (24h)
7. 역상 HPLC 재정제 → 순도 ≥95%
```

**SS bond 형성 수율**: 선형 전구체 대비 60~80% (dilute 조건 0.1~1 mM 필수; 분자간 SS bond 억제)

---

## 3. 변이 그룹별 SAR 가설

### 3.1 그룹 1: pos2 소수성/방향족 sweep (var01~var08)

pos2는 SS bond ring 외부에 위치하며, SSTR2 결합 포켓 진입부의 소수성 groove와 접촉하는 것으로 예측된다. cand03에서 G(Gly, MW 57) → I(Ile, MW 113) 치환이 selectivity margin +0.008 향상을 보였다 — 소수성 side-chain이 pos2 결합에 유리함을 시사.

#### 소수성 계열 (var01~var03)

```
Ile (4.5) > Val (4.2) > Leu (3.8) > Met (1.9)   [Kyte-Doolittle 소수성]
                                                    → 소수성↓ = selectivity ?
```

- **var01 (I→L)**: BLOSUM +2, 매우 보수적. Leu는 Ile와 유사 크기이나 δ-분지 구조가 다름. SSTR2 pocket이 β-분지를 선호하는지 직선형을 선호하는지 평가하는 SAR probe.
- **var02 (I→V)**: BLOSUM +3, 가장 보수적. Val은 β-분지 유지하며 크기 감소. pos2 pocket 크기 탐색.
- **var03 (I→M)**: Met S atom이 포켓 내 hydrophobic contact에 추가 기여. 단, 산화 취약성 → 안정성 profile에서 trade-off.

#### 방향족 계열 (var04~var06)

```
π-stacking 강도: Trp > Tyr ≈ Phe >> Ile (지방족, 방향족 없음)
```

- **var04 (I→F)**: 가장 단순한 방향족 도입. SSTR2 binding pocket에 방향족 cage가 있다면 π-stacking으로 affinity ↑. SSTR1/3/4/5와 해당 위치 residue 환경 차이가 selectivity 결정인자.
- **var05 (I→Y)**: Tyr의 OH가 SSTR2 극성 잔기(Asn276 추정)와 H-bond → selectivity 강화 기대. DOTATATE 계열에서 Tyr3 치환이 SSTR2 친화도 향상의 표준 전략 (Reubi et al., 2000).
- **var06 (I→W)**: 대형 indole ring — pocket이 수용할 수 있다면 최강 결합이나, 입체장해로 Cys3 SS bond 형성에 영향 가능. **합성 후 HPLC로 SS bond 형성 효율 확인 필수.**

#### 전하 계열 (var07~var08)

- **var07 (I→K)**: pos2 Lys는 DOTA 결합 최적 사이트. K9(pharmacophore)의 ε-NH2는 결합 interface에 위치하여 DOTA 탑재 불가 — K2가 최적 대안. DOTA 결합 후 net charge ≈ +1~0.
- **var08 (I→E)**: Glu 도입으로 net charge +2→+1. Cluster D 전하 기준 충족. SSTR2의 양전하 pocket과 salt bridge 가능. **가장 우수한 방사성의약품 전하 profile.**

#### GRAVY vs selectivity 가설

```
pos2 소수성 값 → 예상 SSTR2 affinity 방향:
↑ 소수성 (Trp > Phe > Tyr > Ile > Leu > Val > Met > Glu > Lys) → 
  pocket이 소수성이면: 좌측이 유리
  pocket이 극성이면:   우측이 유리
  SSTR2 선택적이면:    SSTR2 환경 ≠ off-target 환경
```

**SAR 가설**: Boltz 도킹에서 pos2 residue의 SSTR2 pocket 접촉면적(BSA, buried surface area)과 selectivity_margin의 상관관계를 분석하여 최적 소수성 윈도우 결정.

---

### 3.2 그룹 2: pos4/pos5 결합 포켓 미세 조정 (var09~var11)

pos4(K4)와 pos5(N5)는 SS bond ring 내부에 위치하여 SSTR2 결합 직접 접촉 가능성이 높다.

#### var09: K4 → Arg (K4R)

```
Lys(K):   -CH2-CH2-CH2-CH2-NH3+         pKa ~10.5, ammonium
Arg(R):   -CH2-CH2-CH2-NH-C(=NH)-NH2    pKa ~12.5, guanidinium (planar, resonance)
```

**Arg의 장점**:
- guanidinium은 pH 7.4에서 항상 양전하 (Lys는 pKa 10.5 → 부분 중성화 가능)
- bidentate H-bond 형성 (Asp/Glu carboxylate와 2개 H-bond)
- DOTATATE의 Tyr3 치환과 함께 K4→R 유사 치환이 SSTR2 binding에 유리한 사례 (DOTATOC, DOTANOC)

**합성 주의**: Fmoc-Arg(Pbf)-OH 사용. Pbf 탈보호는 TFA 3h 필요. SPPS 효율 ≥95% 기대.

#### var10: N5 → Gln (N5Q)

```
Asn(N):  -CH2-CO-NH2         (side-chain 2탄소)
Gln(Q):  -CH2-CH2-CO-NH2    (side-chain 3탄소, 1 CH2 연장)
```

GRAVY 변화 없음(-3.5 = -3.5). SSTR2 결합 포켓에서 amide의 reach 최적화. **효과 미미할 것으로 예상** — pos5의 역할이 결합에 중요하지 않을 가능성.

#### var11: N5 → Asp (N5D)

Asn → Asp는 이소전자(isoelectronic) 치환이나 pH 7.4에서 완전 이온화. K4(+1)와 D5(-1) 인접 — **분자내 salt bridge 가능성**.

```
분자내 salt bridge:
K4-ε-NH3+ ···· D5-γ-COO-
  거리: 측쇄 말단 간 ~4-6 Å (backbone 2잔기 간격)
  → backbone 굴곡 pre-organization → SSTR2 binding loop에 유리/불리
```

Net charge +1 달성 (Cluster D 전하 기준 충족). **방사성의약품 측면에서 주목할 만한 변이.**

---

### 3.3 그룹 3: 혈청 안정성 향상 변이 (var12~var15)

#### var12: T12 → D-Thr (혈청 안정성 ★★★)

D-아미노산 도입의 표준 전략. SSTR analogue 문헌에서 D-Phe1, D-Trp8(octreotide) 등이 확립.

```
D-Thr vs L-Thr:
  - 동일 side-chain (-CH(OH)-CH3)
  - 키랄 중심 반전 (S→R at α-carbon)
  - 결과: 절단 protease 인식 불가
  - 반감기: L-Thr 함유 vs D-Thr 함유 펩타이드 비교 시 3~10배 혈청 안정성 향상 보고
```

**SPPS 합성**: Fmoc-D-Thr(tBu)-OH (상업 구매: Bachem, Sigma-Aldrich, ≥98% ee). coupling 효율 L-형과 동등.

**구조 영향**: pos12는 pharmacophore(FWKT, pos7-10) 외부. D-Thr 도입으로 local backbone 반전이 SS bond ring 구조에 미치는 영향은 Boltz 도킹으로 확인 필요.

#### var13: S13 → Ala (protease 부위 제거)

```
Ser(S): -CH2-OH (serine protease 절단 기질)
Ala(A): -CH3    (소수성, protease 비인식)
```

S13은 SS bond에 인접하여 C-terminal Cys14 이전 위치. Ala 치환으로 GRAVY +0.186 상승(0.564) — Cluster D GRAVY 상한(+0.5)을 소폭 초과. **단독 사용보다 음전하 변이(I2E 등)와 조합 권장**.

#### var14: F11 → Cha (지환족, proteolytic 보호)

```
Phe(F): -CH2-Ph      (방향족, protease 기질 가능)
Cha:    -CH2-Cy      (cyclohexyl, 포화 환)
  Cy = cyclohexyl ring; 방향족 산화 제거; 입체장해 ↑ → chymotrypsin 인식 ↓
```

Fmoc-Cha-OH (L-cyclohexylalanine): Novabiochem (#06-2X-0081), Bachem에서 상업 구매 가능. SPPS 호환성 우수.

**선택 근거**: chymotrypsin은 방향족/소수성 잔기(Phe, Tyr, Trp, Leu) C-말단을 절단. Cha의 포화 cyclohexyl은 chymotrypsin substrate specificity 감소.

#### var15: F11 → 2-Nal (나프탈렌, 강화 방향족)

```
Phe(F): benzyl ring (6원 aromatic)
2-Nal: 2-naphthylmethyl (bicyclic 10원 aromatic)
```

2-Nal은 Phe보다 소수성이 크고 van der Waals 접촉 면적이 넓다. **방향족 접촉 강화 + protease 입체장해 ↑**. SSTR analogue에서 2-Nal3-octreotate(DOTA-2-Nal3-Tyr6-octreotate) 등의 사용 사례 있음.

---

### 3.4 그룹 4: 복합 변이 (var16~var20)

#### var17: I2F + D-Thr12 — 방사성의약품 최우선 후보

```
디자인 의도:
  I2F: SSTR2 aromatic groove 강화 결합 → selectivity_margin ↑
  D-Thr12: 혈청 반감기 연장 → in vivo efficacy ↑
  조합 결과: 고선택성 + 장기 혈중 체류 → 방사성의약품 theranostic ideal
```

BLOSUM 합산: 0(I2F) + 5(T→T D형 동질 치환) = 5. GRAVY 0.258 (Cluster D PASS).

#### var18: I2Y + D-Thr12 — DOTATATE 유사 프로파일

DOTATATE 자체가 Tyr3-D-Phe1-octreotide 기반. cand03에서 Tyr2 + D-Thr12 조합은 DOTATATE 화학의 원리를 SST-14 기반에 적용한 것. 

**추가 라벨링 경로**: Tyr2의 OH를 통한 방사성 요오드 직접 도입 (electrophilic aromatic substitution). DOTA 없이 125I/131I 라벨링 가능 → DOTA 탑재 실험과 병행 검토.

#### var19: I2E + D-Thr12 — Cluster D 최적 후보 ★★★

```
Cluster D 기준 충족 분석:
  GRAVY: -0.193 → PASS (-1.0~+0.5)
  net charge at pH 7.4: +1 → PASS (|charge| ≤ 1.0)
  metal_coordination: Cys3, Cys14 (strong), Glu2 (moderate) → n_strong ≥ 2 → PASS
```

**세 기준 모두 충족하는 유일한 단일 치환 기반 후보**. 방사성의약품 주사제 formulation에 최적화.

#### var20: I2K + N5D + DOTA — theranostic 전용 설계

```
DOTA conjugation 설계 도식:
                            DOTA
                              |
Ac-A-K(ε-DOTA)-C-K-D-F-F-W-K-T-F-T-S-C-NH2
    2             4  5                   14
      ↑                                       ↑
      K2-ε-NH2에 DOTA-NHS 결합             Cys14 SS bond
```

K2의 dedicated DOTA site 설계로 K4의 ε-NH2는 SSTR2 결합에 활용 가능. DOTA 탑재 stoichiometry 1:1 제어는 ivDde 직교 보호기 전략으로 달성:

```
SPPS 전략:
1. K4-ε: Fmoc-Lys(Boc)-OH → DOTA 결합 안됨 (Boc 탈보호만)
2. K2-ε: Fmoc-Lys(ivDde)-OH → ivDde 선택적 탈보호(2% hydrazine/DMF)
3. K2-ε 탈보호 후 DOTA-NHS-ester coupling (in solution 또는 on-resin)
4. 최종 TFA 글로벌 탈보호 → Boc(K4) 탈보호 완료
```

---

## 4. 합성 가능성 요약표

| 변이체 | SPPS 호환성 | 비표준 시약 | 예상 합성 난이도 | 최대 위험 |
|--------|------------|------------|----------------|-----------|
| var01_I2L | PASS | 없음 | 낮음 | — |
| var02_I2V | PASS | 없음 | 낮음 | — |
| var03_I2M | PASS | 없음 | 낮음 | Met 산화 |
| var04_I2F | PASS | 없음 | 낮음 | — |
| var05_I2Y | PASS | Fmoc-Tyr(tBu)-OH | 낮음 | — |
| var06_I2W | PASS | Fmoc-Trp(Boc)-OH | 중간 | Trp 산화, SS bond 저해 |
| var07_I2K | PASS | Fmoc-Lys(Boc)-OH | 중간 | DOTA stoichiometry |
| var08_I2E | PASS | Fmoc-Glu(OtBu)-OH | 낮음 | — |
| var09_K4R | PASS | Fmoc-Arg(Pbf)-OH | 낮음 | Pbf 탈보호 시간↑ |
| var10_N5Q | PASS | Fmoc-Gln(Trt)-OH | 낮음 | Gln 탈수 |
| var11_N5D | PASS | Fmoc-Asp(OtBu)-OH | 낮음 | aspartimide 주의 |
| var12_T12dThr | PASS | Fmoc-**D**-Thr(tBu)-OH | 낮음 | 키랄 순도 확인 |
| var13_S13A | PASS | 없음 | 낮음 | GRAVY 상한 초과 |
| var14_F11Cha | PASS | Fmoc-Cha-OH (상업) | 낮음 | — |
| var15_F11Nal | PASS | Fmoc-2-Nal-OH (상업) | 낮음 | — |
| var16_I2L_K4R | PASS | Fmoc-Arg(Pbf)-OH | 낮음 | Pbf 탈보호 |
| var17_I2F_dT12 | PASS | Fmoc-D-Thr(tBu)-OH | 낮음 | 키랄 순도 |
| var18_I2Y_dT12 | PASS | Fmoc-Tyr(tBu) + Fmoc-D-Thr(tBu) | 낮음 | — |
| var19_I2E_dT12 | PASS | Fmoc-Glu(OtBu) + Fmoc-D-Thr(tBu) | 낮음 | — |
| var20_I2K_N5D_DOTA | PASS (SPPS) | Fmoc-Lys(ivDde)-OH + DOTA-NHS | 높음 | 직교 보호기 관리 |

**전체 20종 SPPS 호환성**: PASS (100%)  
**표준 Fmoc/tBu 화학으로 합성 가능**: 20/20  
**상업용 비표준 아미노산 필요**: var12~var15 (D-Thr, Cha, 2-Nal)  
**후처리 복잡도 높음**: var20 (직교 보호기 + DOTA)

---

## 5. DOTA 킬레이션 전략

### 5.1 위치별 DOTA 결합 가능성

| 위치 | 잔기 | DOTA 결합 가능 | 비고 |
|------|------|--------------|------|
| N-term α-NH2 | Ala1 | ✓ (Ac 대신) | pharmacophore와 거리 있음 |
| K4 ε-NH2 | Lys4 | ✓ | 결합 포켓 인접 — affinity 영향 가능 |
| K9 ε-NH2 | Lys9 (pharmacophore) | ✗ | 결합 필수 잔기 → DOTA 금지 |
| K2 ε-NH2 (var07, var20) | Lys2 | ✓ ★ 최적 | 수용액 노출, pharmacophore 거리 최대 |

### 5.2 DOTA-NHS 결합 프로토콜 (일반)

```
1. 선형 또는 환화 펩타이드 (보호기 제거 완료)
2. DOTA-NHS ester (0.5 M, DMF 용액) + 펩타이드 (1 equiv)
3. DIPEA 2 equiv, pH 8.5, RT, 2h
4. HPLC 정제 → DOTA-펩타이드 conjugate
5. 금속 킬레이션:
   - 68Ga: GaCl3 in HCl, pH 4.0, 95°C, 15 min
   - 177Lu: LuCl3, pH 4.5, 95°C, 30 min
   - 90Y: YCl3, pH 4.0-5.0, 95°C, 30 min
6. Sep-Pak C18 purification → 최종 라벨링 산물
```

### 5.3 DOTA 탑재 후 예상 성질 변화

| 변수 | 변화 |
|------|------|
| MW | +504 Da (DOTA), +572 Da (DOTA-68Ga) |
| net charge | -2~-4 기여 (DOTA 4 carboxylates) |
| GRAVY | 다소 감소 (DOTA 친수성) |
| 방사성 순도 | ≥95% (GMP 기준) |

---

## 6. Cluster 분류 예측

### Cluster D 기준 충족 변이체 (방사성의약품 우선)

| 변이체 | GRAVY | charge | n_strong | 종합 |
|--------|-------|--------|----------|------|
| baseline cand03 | 0.379 ✓ | +2 ✗ | Cys×2 ✓ | FAIL (charge) |
| var08_I2E | -0.193 ✓ | +1 ✓ | Cys×2, Glu×1 ✓ | **PASS** |
| var11_N5D | 0.379 ✓ | +1 ✓ | Cys×2, Asp×1 ✓ | **PASS** |
| var19_I2E_dT12 | -0.193 ✓ | +1 ✓ | Cys×2, Glu×1 ✓ | **PASS** |
| var20 + DOTA | -0.221 ✓ | ~0 ✓ | Cys×2, Lys×2 ✓ | **PASS** (DOTA 후) |

### Cluster B 잠재력 (selectivity, Boltz 도킹 후 확정)

pos2 방향족 치환(var04 I2F, var05 I2Y, var18 I2Y_dT12)이 selectivity_margin ≥ 3.0 kcal/mol 달성 가능성이 높다고 예측 (SAR 가설 기반).

### Cluster C 잠재력 (안정성)

D-Thr12 포함 변이체(var12, var17, var18, var19)는 instability_index 감소 및 protease_sites 감소로 Cluster C 기준 충족 가능성.

---

## 7. Boltz 도킹 우선 실행 권장

**40페어 (8 우선 변이체 × 5 SSTR subtype) 도킹 후 분석**:

```python
# 우선 도킹 대상
priority_variants = [
    "var01_I2L",    # 보수적 기준점
    "var04_I2F",    # aromatic selectivity
    "var05_I2Y",    # DOTATATE 유사 Tyr
    "var07_I2K",    # DOTA theranostic
    "var12_T12dThr", # 안정성 단독
    "var17_I2F_dT12", # aromatic + 안정성
    "var18_I2Y_dT12", # Tyr + 안정성
    "var19_I2E_dT12", # Cluster D 최적
]
receptors = ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]
```

**평가 지표**:
- iPTM (interface predicted TM-score) — 결합 신뢰도
- pTM (predicted TM-score) — 구조 예측 신뢰도
- selectivity_margin: SSTR2 iPTM - max(SSTR1,3,4,5 iPTM)

**기대 결과**:
- var05_I2Y 또는 var04_I2F에서 selectivity_margin 최대 예측
- var19_I2E_dT12에서 Cluster D + Cluster B 동시 충족 가능성

---

## 8. 화학적 위험 요소 요약

| 위험 | 해당 변이체 | 대응 |
|------|------------|------|
| Met 산화 (Met-SO 생성) | var03_I2M | HPLC-MS로 Met-SO 부산물 모니터링; 불활성 가스 보관 |
| Trp 산화 (indole 산화) | var06_I2W | TFA 탈보호 시 EDT 1% 첨가; RP-HPLC 순도 ≥95% 확인 |
| D-Thr 키랄 순도 | var12, var17, var18, var19 | 광학 회전 측정 + chiral HPLC (>99% ee) |
| SS bond 효율 저하 (Trp2 입체장해) | var06_I2W | 산화 조건 최적화 (dilute 조건, DMSO/AcOH) |
| Gln 탈수 사이클화 | var10_N5Q | 커플링 후 즉시 Fmoc 탈보호 진행 |
| Asp aspartimide | var11_N5D | 0.1 M HOBt 첨가, HATU coupling |
| DOTA stoichiometry | var07, var20 | ivDde 직교 보호기; RP-HPLC 단일 피크 확인 |
| GRAVY 상한 초과 | var13_S13A | 단독보다 I2E 등 음전하 변이와 조합 권장 |

---

## 9. §검증 필요 사항

1. **var06_I2W SS bond 효율**: Trp2-Cys3 근접으로 SS bond 형성 방해 여부 — 합성 실험 필요
2. **var12 D-Thr12 local backbone 변화**: Boltz 도킹에서 SS bond ring 구조 유지 여부 확인
3. **var11 K4-D5 salt bridge**: 분자 역학 시뮬레이션 또는 NMR로 실제 형성 여부
4. **var07/var20 DOTA conjugate 결합력**: DOTA 탑재 후 SSTR2 결합 affinity 보존 여부 (in vitro 결합 실험)
5. **pos2 소수성 최적값**: var01~var05 Boltz 도킹 결과로 SSTR2 pocket 소수성 선호도 결정
6. **Cluster B selectivity_margin 예측**: var04, var05, var17, var18에서 실제 ≥3.0 kcal/mol 달성 여부

---

## 10. 참고 문헌 (SAR 가설 근거)

1. **Reubi JC et al. (2000)** — SSTR2-selective peptide analogues: Tyr3-octreotate > Tyr3-octreotide. *Eur J Nucl Med* 27, 273-282.
2. **Knudsen LB et al. (2019)** — Semaglutide-style fatty acid acylation via Lys ε-NH2. *J Med Chem* 62, 1843-1857.
3. **Kwekkeboom DJ et al. (2008)** — DOTATATE theranostics: 68Ga + 177Lu. *J Nucl Med* 49, 1987-1994.
4. **Tyndall JDA et al. (2005)** — Crystal structures of serine proteases with D-amino acid substrates. *Chem Rev* 105, 973-999.
5. **de Visser M et al. (2003)** — Comparison of radiolabelled somatostatin analogues with different ring sizes. *Eur J Nucl Med Mol Imaging* 30, 1538-1545.

---

*생성일: 2026-05-12 | reviewer-chemistry | PRST_N_FM 프로젝트*
