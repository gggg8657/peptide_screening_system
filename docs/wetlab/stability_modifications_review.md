# Stability 향상 Modification 종합 리뷰
## SSTR2 방사성의약품 후보 펩타이드 (SST-14 기반)

> **작성일**: 2026-05-12  
> **작성자**: reviewer-chemistry (S3, Task id=12)  
> **버전**: 1.0  
> **참조**:  
> - `runs_local/cand03_variants/design_rationale.md` (chemistry T4 SAR)  
> - `docs/presentation/01_appendix/cluster_classification_spec.md` (A~E cluster)  
> - `pipeline_local/scripts/modification_conflict.py` (C-07 DOTA stoichiometry)  
> - `pipeline_local/steps/step08_stability.py` (heuristic ranking — 임상 반감기 ≠ 예측값)

---

## ⚠️ 면책 사항 (step08_stability.py H-06 원칙 준수)

본 문서의 반감기 수치는 **휴리스틱 ranking 참고값**이다. 실제 in-vivo/in-vitro serum half-life 측정값이 아니며, 임상 단위로 인용 금지. pre-wet-lab 후보 우선순위 부여 목적으로만 사용.

---

## 1. Modification 카테고리 종합 비교표

| # | Modification | 반감기 배수 (참고) | 합성 비용 등급 | SSTR2 결합력 영향 | SPPS 호환성 | DOTA 부위 충돌 |
|---|-------------|-----------------|-------------|-----------------|------------|--------------|
| 1 | **D-amino acid 도입** | 2~30× | 낮음 (Fmoc-D-AA 상업 구매) | 위치 의존 (D-Trp8: 보강, 기타: 중립~소폭 감소) | ✅ PASS | 없음 |
| 2 | **N-methylation** | 5~20× | 중간 (Fmoc-NMe-AA 또는 on-resin 시약) | 주의 (H-bond donor 소실로 pocket interaction ↓) | ✅ PASS (위치 제한) | 없음 |
| 3 | **Lactam bridge (Lys-Glu)** | 10~100× | 높음 (직교 보호기 2종 필요) | 보강 가능 (cyclization으로 구조 preorganization) | ⚠️ CONDITIONAL | DOTA Lys 겹침 주의 |
| 4 | **PEG화 (2~40 kDa)** | 100~1000× | 중간 (PEG-NHS reagent) | 크기 의존 감소 (20 kDa 이상: 부분 차폐) | ✅ PASS (용액상) | K4 vs PEG 경쟁 |
| 5 | **지방산 아실화 (C16/C18)** | 10~50× | 중간 (fatty acid-NHS ester) | 알부민 결합 mediated 보강 (간접) | ✅ PASS (용액상) | K4 vs acyl 경쟁 |
| 6 | **NCAA (Cha, 2-Nal, Aib, Orn)** | 3~50× | 높음 (비표준 AA, Bachem/Novabiochem) | 위치 의존 (pharmacophore 외부: 영향 낮음) | ✅ PASS | 없음 |
| 7 | **N/C-terminal cap (Ac, NH2)** | 2~10× | 매우 낮음 (resin 선택 + Ac2O) | 거의 없음 ✅ | ✅ PASS | 없음 |
| 8 | **Cyclization (head-to-tail)** | 10~100× | 높음 (추가 cyclization 단계) | 위치 의존 (기존 SS bond와 양립 설계 필요) | ⚠️ COMPLEX | 없음 |
| 9 | **이황화 결합 강화 (Pen)** | 2~5× | 중간 (Fmoc-Pen-OH 상업) | SS bond 안정성 향상 → 구조 유지 ↑ | ✅ PASS | 없음 |
| 10 | **Lys → Orn 치환** | 3~10× | 낮음 (Fmoc-Orn(Boc)-OH) | 보존적 (양전하 유지, side-chain 단축) | ✅ PASS | DOTA 결합 가능 유지 |
| 11 | **Met → Nle (norleucine)** | 2~5× | 낮음 (Fmoc-Nle-OH) | 보존적 (산화 위험 제거) | ✅ PASS | 없음 |
| 12 | **Phospho-Ser/Thr (pSer, pThr)** | 가변 | 중간 | 극성 증가, SSTR2 결합 영향 불명 | ✅ PASS | 없음 |

---

## 2. 각 Modification의 합성 Protocol Overview

### 2.1 D-amino acid 도입 (★★★ 최우선 권장)

**원리**: L-아미노산 특이적 protease는 D-배열 기질을 인식하지 못함 → 절단 저항.

**적용 위치 원칙**:
- Pharmacophore(pos7-10) 외부 위치에 적용
- D-Trp8(octreotide)처럼 pharmacophore 내부 D-AA도 가능하나 구조 검증 필수
- Gly에는 적용 불가 (키랄 중심 없음)

**SPPS 합성 절차**:
```
표준 Fmoc/tBu 화학 그대로 적용
    ↓
Fmoc-D-XX(PG)-OH 사용 (XX = Thr, Phe, Lys, Trp, Ser 등)
    ↓
HATU/HOBt/DIPEA coupling (L-형과 동일 조건, 효율 ≥95%)
    ↓
탈보호 후 HPLC + 광학 회전 측정 → D-형 순도 확인 (>99% ee)
    ↓
SS bond 산화 (기존과 동일: I2/MeOH 또는 DMSO/AcOH)
```

**상업 시약**:
- Fmoc-D-Thr(tBu)-OH: Bachem (F-1575), Sigma-Aldrich (852945) — ~₩150,000/g
- Fmoc-D-Phe-OH: Bachem (F-1060) — ~₩120,000/g
- Fmoc-D-Trp(Boc)-OH: Novabiochem (04-12-2100) — ~₩200,000/g

**비용 추정**: L-형 대비 1.5~3배 (D-AA 구매 비용 차이). 합성 공정 추가 비용 없음.

---

### 2.2 N-methylation

**원리**: backbone N-H → N-CH3 전환으로 amide bond protease 인식 차단. cis/trans 이성질체 혼합 위험 있음.

**적용 가능 위치**: pos11(F), pos12(T), pos13(S) — pharmacophore 외부 권장.

**합성 절차**:
```
방법 A (Fmoc-NMe-AA-OH 직접 사용):
    Fmoc-NMe-Phe-OH, Fmoc-NMe-Ala-OH 등 상업 구매
    → 표준 SPPS (단, 커플링 효율 감소 주의: double coupling 권장)

방법 B (on-resin N-methylation):
    1. Fmoc 탈보호 → free α-NH2
    2. 2-Nitrobenzenesulfonyl chloride (Ns-Cl, 과량) → Ns 보호
    3. MeOH / PPh3 / DIAD (Mitsunobu) → N-Me 도입
    4. PhSH / K2CO3 → Ns 탈보호
    5. 다음 아미노산 coupling
```

**주의사항**: N-Me AA 도입 위치 다음 잔기는 coupling 효율 ↓ (입체장해). microwave SPPS 또는 triple coupling 권장.

**비용**: 방법 A의 경우 Fmoc-NMe-AA-OH는 L-형 대비 3~5배 비쌈 (~₩300,000~500,000/g).

---

### 2.3 Lactam Bridge (Lys ε-NH2 ↔ Glu γ-COOH)

**원리**: 분자 내 공유 결합으로 backbone ring 형성 → 엔도·엑소 펩티다제 공격면 감소.

**설계 요구사항**:
- Lys와 Glu를 i+4 또는 i+7 위치에 배치 (α-helical ring closure에 최적)
- 14aa SST-14 기반에서 가능한 조합:
  ```
  cand03: pos1(A)에 Glu 도입 → Glu1-Lys4 lactam (i+3: 허용)
  또는 pos5 Asn → Glu 도입 → pos5-Glu + 도입 Lys (별도 위치) lactam
  ```

**직교 보호기 전략**:
```
Fmoc-Lys(Dde)-OH + Fmoc-Glu(OAllyl)-OH
    ↓
SPPS 완성 (다른 잔기는 표준 보호기)
    ↓
2% N2H4/DMF → Dde 탈보호 (Lys ε-NH2 노출)
    ↓
Pd(PPh3)4 / PhSiH3 → OAllyl 탈보호 (Glu γ-COOH 노출)
    ↓
HATU/HOBt/DIPEA, DMF, 2h → intramolecular lactam ring formation
    ↓
TFA 글로벌 탈보호 → HPLC 정제 → SS bond 산화
```

**비용**: 합성 1회 추가 단계 ×3회 (탈보호 2회 + cyclization) → 합성비 +30~50%. 직교 시약 비용 ~₩200,000 추가.

**결합력 영향**: lactam bridge 위치에 따라 SSTR2 결합 유지 또는 향상 가능. **반드시 Boltz 도킹으로 lactam 구조 사전 검토 권장**.

---

### 2.4 PEG화 (PEGylation)

**원리**: PEG의 고분자량이 수력역학적 반경(hydrodynamic radius)을 증가시켜 신장 사구체 여과 억제. 20 kDa PEG: MW ~22 kDa 추가, 수력역학적 반경 ~4배 증가.

```
분자량 별 효과 (문헌 기반, 절대값 X — ranking 참고):
  PEG2kDa:  반감기 2~5×  (신장 여과 부분 억제)
  PEG5kDa:  반감기 5~20× (주요 청소 경로 차단 시작)
  PEG20kDa: 반감기 20~100× (PEGylated exenatide 기준; Chapman 2002)
  PEG40kDa: 반감기 ~1000× (최대 — 비특이적 결합↑, solubility↓ 균형)
```

**SPPS 합성 절차**:
```
방법 A (용액상 PEGylation):
    1. 선형 펩타이드 SPPS + SS bond 형성
    2. HPLC 정제 (순수 펩타이드)
    3. mPEG-NHS ester (원하는 MW) + 펩타이드 (1:1.2)
    4. PBS pH 8.0, RT, 2h
    5. 역상 HPLC 또는 SEC 정제 → 단일 PEGylation site 확인

방법 B (site-specific, Lys orthogonal):
    Lys(ivDde) 도입 → SPPS → ivDde 탈보호(2% N2H4) → mPEG-NHS coupling
```

**주의사항**:
- K9(pharmacophore)는 PEGylation 금지
- K4와 K9 모두 존재하는 경우 site-specific 제어 필수
- PEG 20 kDa 이상 도입 시 SSTR2 결합력 감소 위험 (pocket 접근 차단)
- 방사성의약품: PEG는 신장 배설을 억제하여 **종양 uptake 향상 효과 있으나 background ↑ 동반**

---

### 2.5 지방산 아실화 (Fatty Acid Acylation) — 세마글루타이드 방식

**원리**: C16~C18 지방산이 HSA(human serum albumin) site II에 결합 → 유리 형태 감소 → 신장 청소율 감소 + 반감기 연장. 세마글루타이드(C18 이중산, Lys26)로 168h 달성.

```
지방산 chain 길이별 albumin Kd:
  C8 (octanoyl):   Kd > 100 μM  (약한 결합)
  C12 (lauroyl):   Kd ~ 10 μM
  C16 (palmitoyl): Kd ~ 1 μM    ★ 적정 (결합 충분, 응집 위험 낮음)
  C18 (stearoyl):  Kd ~ 0.1 μM  ★★ 최적 (세마글루타이드 수준)
  C20 이상:        응집 위험 ↑, 수용성 ↓ → 비권장
```

**SPPS 합성 절차**:
```
1. Fmoc-Lys(ivDde)-OH로 target Lys 보호
2. SPPS 완성 → TFA 글로벌 탈보호 (ivDde 유지됨)
3. 2% N2H4/DMF, 5 min → ivDde 탈보호 (Lys ε-NH2 노출)
4. C16-/C18-NHS ester (dimethyl sulfoxide, DIPEA) → amide coupling
   또는 세마글루타이드 방식: 미니 PEG linker + C18 diacid 도입
5. HPLC 정제 → MS 확인 → SS bond 산화
```

**권장 결합 위치 (SSTR2 기준)**:
- **K4 (pos4)**: pharmacophore K9 보호 + SSTR2 결합 면에서 원거리 → **1차 권장**
- **K2 (var07)**: pos2에 Lys 도입 시 최적 (pharmacophore에서 더 원거리)
- **K9 (pos9)**: **절대 금지** — pharmacophore 핵심 잔기

**비용**: fatty acid NHS ester ~₩80,000~200,000/g (C16-NHS Sigma-Aldrich #P9716). 합성 추가 비용 포함 +₩300,000/후보.

---

### 2.6 NCAA (Non-Canonical Amino Acids)

| NCAA | 대체 대상 | 합성 시약 | 효과 | 비용 |
|------|----------|----------|------|------|
| **Cha** (cyclohexyl-Ala) | Phe → Cha | Fmoc-Cha-OH (Bachem F-3310) | chymotrypsin 저항 ↑↑ | ~₩180,000/g |
| **2-Nal** (2-naphthyl-Ala) | Phe → 2-Nal | Fmoc-2-Nal-OH (Bachem F-1730) | 방향족 강화 + protease 저항 ↑ | ~₩220,000/g |
| **Aib** (α-aminoisobutyric acid) | Arg/Leu → Aib | Fmoc-Aib-OH (Bachem F-1865) | 양쪽 protease 차단 (α-메틸 입체장해) | ~₩150,000/g |
| **Orn** (ornithine) | Lys → Orn | Fmoc-Orn(Boc)-OH (Bachem F-1860) | trypsin 저항 ↑ (side-chain 단축), 양전하 유지 | ~₩160,000/g |
| **Nle** (norleucine) | Met → Nle | Fmoc-Nle-OH (Bachem F-1340) | Met 산화 제거, 동일 소수성 | ~₩100,000/g |
| **MePhe** (N-methyl-Phe) | Phe → MePhe | Fmoc-NMe-Phe-OH (Novabiochem) | backbone amide 절단 저항 | ~₩400,000/g |

**SPPS 호환성**: 전품목 Fmoc 화학 호환. coupling 효율 각 ≥90% (double coupling 권장).

---

### 2.7 N/C-Terminal Cap (★ 기본 필수)

```
N-terminal Acetylation (Ac-):
    - 방법: SPPS 완성 후 레진 상에서 Ac2O/DIPEA (DMF, 10 min)
    - 효과: aminopeptidase M, leucine aminopeptidase 차단
    - 비용: ₩5,000 이하/합성 (Ac2O 시약비)

C-terminal Amidation (-NH2):
    - 방법: Rink Amide MBHA resin 사용 (TFA 탈보호 시 자동 NH2 생성)
    - 효과: carboxypeptidase A/B 차단
    - 비용: Rink Amide resin은 Wang resin 대비 +20% (₩30,000/g 차이)
```

**결합력 영향**: 거의 없음. **모든 후보에 기본 적용 필수 (표준화 권장).**

---

### 2.8 Head-to-Tail Cyclization

**주의**: SST-14 계열은 이미 Cys3-Cys14 SS bond로 ring scaffold 존재. 추가 head-to-tail cyclization은 **이중 cyclization** 구조 → 설계 복잡도 급증.

- 적용 가능 전략: SS bond를 제거하고 lactam ring으로 대체 → **본 후보에 비권장**
- 예외: linear analogue(SS bond 제거) + head-to-tail ring closure → 별도 설계 계통 필요

---

### 2.9 이황화 결합 강화 — Penicillamine (Pen)

**원리**: Pen = β,β-dimethyl-Cys. gem-dimethyl기가 SS bond 주변 회전 제한 → 구조 rigidity ↑, reductive 환경 저항성 ↑ (GSH, DTT에 저항).

```
Cys3 → Pen3 또는 Cys14 → Pen14 치환:
    Fmoc-Pen(Trt)-OH 사용 (Bachem F-2115, ~₩350,000/g)
    SS bond 산화 조건 동일
    
결과: SS bond 가수분해 반감기 延長, 환원 환경(혈청 GSH ~10 μM) 저항
```

---

## 3. 후보 8종 Modification 권장 매트릭스

> baseline: AICKNFFWKTFTSC (cand03). 위치 표기 1-indexed.  
> 고정 위치: Cys3, Cys14 (SS bond), Phe7-Trp8-Lys9-Thr10 (pharmacophore)

### 후보 서열 정보

| 코드 | 서열 | pos2 | pos4 | pos5 | pos11 | 특이사항 |
|------|------|------|------|------|-------|---------|
| **cand03** | AICKNFFWKTFTSC | I | K | N | F | T2 baseline, best selectivity |
| **T3-01** | ILCKKFFWKTFTSC | L | K | **K** | F | K-K at 4-5: trypsin 이중 취약 |
| **T3-02** | IGCWWFFWKTFTSC | G | K | N | F | W-W(pos5-6) 응집 위험, 4 aromatic |
| **T3-03** | AGCKNDFWKTLTSC | G | K | N | L | D6, L11 — 안정적 |
| **T3-04** | FGCKNFFWKTLASC | F | K | N | L | F1, L11 |
| **T3-05** | AGCKNTFWKTFTSA | G | K | N | F | T6, A14(C14→A: SS bond 없음?) |
| **var07_I2K** | AKCKNFFWKTFTSC | **K** | K | N | F | DOTA at K2, charge+3 |
| **var12_dT12** | AICKNFFWKTF[dT]SC | I | K | N | F | D-Thr12, 안정성 우선 |

> ⚠️ T3-05 (AGCKNTFWKTFTSA): pos14가 A(Ala) → **Cys14 부재 → SS bond 불가**. 선형 펩타이드로 처리 필요. 안정성 프로파일 완전히 상이함.

---

### 권장 매트릭스 — 후보별 우선 modification 3순위

| 후보 | 1순위 (효과 최대) | 2순위 (실용적) | 3순위 (추가 안정성) | 우선 제외 | DOTA 결합 위치 |
|------|-----------------|--------------|------------------|---------|--------------|
| **cand03** | Ac + NH2 (기본) | T12→D-Thr | C16/C18 acyl at K4 | PEG20k (결합↓우려) | K4-ε-NH2 |
| **T3-01 (ILCKKFFWKTFTSC)** | K5→Orn (trypsin site 제거) | T12→D-Thr | Ac + NH2 | K5-DOTA (K9 보호) | **K5-ε-NH2** ★ |
| **T3-02 (IGCWWFFWKTFTSC)** | Ac + NH2 | W5→2-Nal (응집↓) | D-Ser13 | PEG (소수성 응집 악화) | K4-ε-NH2 |
| **T3-03 (AGCKNDFWKTLTSC)** | Ac + NH2 | L11→Cha (protease↓) | D-Thr12 | N-methylation (D6와 충돌 위험 없으나 effect 낮음) | K4-ε-NH2 |
| **T3-04 (FGCKNFFWKTLASC)** | Ac + NH2 | L11→Cha | D-Phe1(?) | — | K4-ε-NH2 |
| **T3-05 (AGCKNTFWKTFTSA)** | **SS bond 재설계 필수** (Cys14 없음) | Pen3(A14→C 복구 후) | Ac + NH2 | 현 상태 모든 modification 보류 | C14 복구 후 K4 |
| **var07_I2K** | DOTA-NHS at K2-ε | Ac + NH2 | D-Thr12 | 지방산 at K4 (K2-DOTA와 K4 경쟁) | **K2-ε-NH2** (primary) |
| **var12_dT12** | Ac + NH2 | C16 acyl at K4 | F11→Cha | N-methylation (효과 중복) | K4-ε-NH2 |

---

## 4. SAR vs Stability Trade-off 분석

### 4.1 결합력 손실 위험도 분류

```
위험도: LOW → MEDIUM → HIGH

LOW (결합력 영향 최소):
  ✅ Ac-Nterm + NH2-Cterm
  ✅ D-Thr12, D-Ser13 (pharmacophore 외부 D-AA)
  ✅ F11→Cha, F11→2-Nal (pos11은 pharmacophore 외부)
  ✅ Lys→Orn (비pharmacophore K4)

MEDIUM (위치·사이즈 의존):
  ⚠️ K4-지방산 acylation (K4가 SSTR2 결합에 기여 시 affinity↓ 가능)
  ⚠️ PEG5kDa at K4 (포켓 접근 차단 부분적)
  ⚠️ Lactam K4-Glu(i+??) (ring 형성으로 conformation 변화)
  ⚠️ N-methylation at F11, T12 (backbone H-bond 소실)

HIGH (결합력 손실 가능성 높음):
  ❌ PEG20kDa 이상 at K4 (포켓 완전 차단 위험)
  ❌ D-Trp8, D-Phe7 (pharmacophore 위치 D-AA: affinity 대폭 변화 — 일부 사례에서 향상도)
  ❌ K9→Orn/Lys→anything (pharmacophore 핵심 잔기)
  ❌ T10, W8, F7 변경 (pharmacophore 보존 규칙)
```

### 4.2 안정성 vs 선택성 최적 균형 지점

```
예상 Pareto front (stability rank vs selectivity rank):

                 stability ↑
                     |
var12_dT12+Ac+NH2 ●  |   ● var07+DOTA+Ac
(안정 우선)           |     (theranostic 최적)
                     |
         cand03+Ac+  | ● cand03+D-Thr12+C18acyl
              NH2 ●  |   (균형 최적)
                     |
SST-14 baseline ●    |
                     +------------------→ selectivity ↑
```

**권장**: cand03+Ac+NH2+D-Thr12 가 cost-effectiveness 최고 (합성비 최소, stability 중간, selectivity 유지)

### 4.3 DOTA chelator 부위 충돌 규칙 (C-07)

`modification_conflict.py` C-07 규칙 준수:
```
규칙 C-07: DOTA chelator 단일성
  - 펩타이드당 DOTA 1개만 결합 가능
  - 근거: isotope stoichiometry (68Ga/177Lu/90Y binding)
  - 위반 시: specific activity 예측 불가 → theranostic 실패

충돌 조합:
  ❌ K2-DOTA + K4-DOTA (var07 + 추가 DOTA): C-07 위반
  ❌ N-term-DOTA + K4-DOTA: C-07 위반
  ✅ K2-DOTA only (var07 권장)
  ✅ K4-DOTA only (cand03 권장)
  ✅ N-term-DOTA only (K4를 지방산에 사용할 때)
```

### 4.4 K4 vs K2 DOTA 결합 위치 비교

| 기준 | K4 ε-NH2 (cand03) | K2 ε-NH2 (var07) |
|------|-----------------|-----------------|
| SSTR2 결합 영향 | 중간 (K4가 결합 관여 가능) | 낮음 (ring 외부) |
| 수용액 접근성 | 중간 | 높음 (N-term 근처) |
| 킬레이터 접근성 | 양호 | 우수 |
| 합성 난이도 | 낮음 (K4만 있는 경우) | 중간 (ivDde 필요) |
| 권장 조건 | cand03/T3 계열 | var07_I2K 전용 |

---

## 5. 합성 회사 + 비용 추정

### 5.1 CRO 합성 서비스 (외주 가능 업체)

| 회사 | 국가 | 특기 | 합성비 추정 (14aa, ≥95% purity) |
|------|------|------|-------------------------------|
| **Bachem** | 스위스 | GMP 가능, D-AA + NCAA 전문 | ₩3~5M / 100 mg |
| **PolyPeptide** | 스웨덴/미국 | 상업 규모, 방사성의약품 CRO 경험 | ₩4~8M / 100 mg |
| **Genscript** | 미국/중국 | 빠른 납기, 비용 효율 | ₩1~2M / 100 mg (표준 AA만) |
| **AnaSpec** | 미국 | 방사성의약품 특화, D-AA 전문 | ₩2~4M / 50 mg |
| **Peptron** | 한국 | 국내 최대 펩타이드 합성 CRO | ₩1.5~3M / 100 mg |
| **제이비 바이오사이언스** | 한국 | DOTA-펩타이드 경험 있음 | ₩2~4M / 50 mg |

### 5.2 modification별 추가 비용 추정 (per 후보)

| Modification | 추가 시약비 | CRO 추가 공정비 | 합계 추정 |
|-------------|----------|--------------|---------|
| Ac + NH2 | ~₩10,000 | 없음 (표준) | **₩10,000** |
| D-Thr12 | ~₩150,000 (D-AA) | 없음 | **₩150,000** |
| F11→Cha | ~₩180,000 | 없음 | **₩180,000** |
| F11→2-Nal | ~₩220,000 | 없음 | **₩220,000** |
| K4→Orn | ~₩160,000 | 없음 | **₩160,000** |
| C18 acylation | ~₩200,000 | +₩300,000 (용액상) | **₩500,000** |
| PEG5kDa | ~₩400,000 | +₩500,000 | **₩900,000** |
| PEG20kDa | ~₩800,000 | +₩800,000 | **₩1,600,000** |
| K2-DOTA (var07) | ~₩300,000 (DOTA-NHS) | +₩500,000 (ivDde 공정) | **₩800,000** |
| Lactam bridge | ~₩300,000 | +₩800,000 (직교 보호기) | **₩1,100,000** |
| Pen 치환 | ~₩350,000 | 없음 | **₩350,000** |

### 5.3 후보당 권장 합성 패키지 비용 (우선 순위 조합)

```
패키지 A (표준 기본): Ac + NH2 + D-Thr12
  → 추가 비용: ~₩160,000/후보 → 총 8종 기준 ~₩1.3M

패키지 B (방사성의약품 기본): Ac + NH2 + D-Thr12 + K4-DOTA
  → 추가 비용: ~₩960,000/후보 → 총 8종 기준 ~₩7.7M

패키지 C (안정성 강화): Ac + NH2 + D-Thr12 + C18 acyl at K4
  → 추가 비용: ~₩660,000/후보 → 총 8종 기준 ~₩5.3M

패키지 D (var07 전용 theranostic): Ac + NH2 + D-Thr12 + K2-DOTA
  → 추가 비용: ~₩960,000 → var07 단독
```

---

## 6. 문헌 인용

1. **Veber DF et al. (1981)** "A potent cyclic hexapeptide analogue of somatostatin." *Nature* 292, 55-58. — 옥트레오타이드(D-Phe1, D-Trp8 + cyclization) 반감기 연장 원리.

2. **Reubi JC et al. (2000)** "Somatostatin receptor sst1-sst5 expression in normal and neoplastic human tissues." *Eur J Nucl Med* 27, 273-282. — DOTATATE SS bond + Tyr3 치환의 SSTR2 결합 향상.

3. **Knudsen LB & Lau J (2019)** "The Discovery and Development of Liraglutide and Semaglutide." *Front Endocrinol* 10:155. — C18 지방산 아실화 + miniPEG 링커 전략으로 168h 반감기 달성 (Lys26 ε-NH2 결합).

4. **Chapman AP (2002)** "PEGylated antibodies and antibody fragments for improved therapy." *Adv Drug Deliv Rev* 54, 531-545. — PEG 분자량 vs 신장 청소율 관계.

5. **Tyndall JDA, Nall T & Fairlie DP (2005)** "Proteases universally recognize beta strands." *Chem Rev* 105, 973-999. — D-amino acid 도입의 β-strand protease 저항 메커니즘.

6. **Lau JL & Dunn MK (2018)** "Therapeutic peptides: Historical perspectives, current development trends, and future directions." *Bioorg Med Chem* 26, 2700-2707. — 치료 펩타이드 안정화 전략 종합 리뷰.

7. **Wadas TJ, Wong EH, Weisman GR & Anderson CJ (2010)** "Coordinating Radiometals of Copper, Zirconium, Indium, Yttrium, and Lutetium with Bifunctional Chelates for PET and SPECT Imaging of Disease." *Chem Rev* 110, 2858-2902. — DOTA stoichiometry 원칙 (68Ga/177Lu/90Y).

8. **Tugyi R et al. (2005)** "Partial retro-inverso analogs of the Herpes simplex virus peptide." *Proc Natl Acad Sci* 102, 413-418. — Partial D-AA 도입 펩타이드의 serum stability + 활성 보존.

9. **de Visser M et al. (2003)** "Comparison of radiolabelled somatostatin analogues with different ring sizes." *Eur J Nucl Med Mol Imaging* 30, 1538-1545. — ring 크기와 SSTR2 결합력·안정성 관계.

10. **Kwekkeboom DJ et al. (2008)** "Treatment with the radiolabeled somatostatin analog [177Lu-DOTA0,Tyr3]octreotate." *J Clin Oncol* 26, 2124-2130. — 177Lu-DOTATATE 임상 표준 프로토콜.

---

## 7. 종합 권고

### 7.1 단기 실험 우선 순위 (1-2개월)

```
Step 1 (필수, 모든 후보):
  → Ac-N-term + C-NH2 표준화 (비용 최소, 효과 즉각)

Step 2 (cand03 + T3 안정성 향상):
  → cand03: T12→D-Thr 추가 (var12 패턴 확인)
  → T3-01: K5→Orn + D-Thr12 (trypsin K-K site 제거)
  → T3-03: L11→Cha 추가 (안정 but affinity 검증 필요)

Step 3 (방사성의약품 후보 정제):
  → cand03 + DOTA at K4 (패키지 B)
  → var07 + DOTA at K2 (패키지 B, ivDde 공정)
```

### 7.2 T3-05 (AGCKNTFWKTFTSA) 특이 주의

**Cys14 → Ala14 치환으로 SS bond 불가** → 현재 서열 상태로는 선형 펩타이드. 다음 중 선택:
- A) Ala14를 Cys14로 복구 후 SS bond 재형성 → 정상 진행
- B) 선형 펩타이드 그대로 → head-to-tail lactam cyclization 설계 (별도 프로젝트)

**권고**: A를 우선. 현재 서열 그대로의 stability modification은 SS bond 복구 후 적용.

### 7.3 T3-02 (IGCWWFFWKTFTSC) 응집 주의

W5-W6 + F7-F8 총 4개 방향족 잔기 연속 → 소수성 응집(aggregation) 고위험.
- PEG화로 응집 억제 효과 있으나 결합력 ↓ 동반
- W5→2-Nal 또는 W5→Tyr 치환으로 극성 도입 검토
- Formulation: DMSO 1~5% 공용매 사용 고려

---

## 8. §검증 필요 사항

1. **T3-05 Cys14→Ala 의도적 치환 여부**: 설계 오류인지 선형 펩타이드 의도인지 확인 필요
2. **K4 DOTA + C18 acyl 동시 적용 가능성**: K4 단일 site에 2가지 modification 충돌(C-07 참조) — K4-acyl + N-term-DOTA 조합으로 해소 가능한지 검증
3. **D-Thr12 local backbone 변화가 SS bond ring에 미치는 영향**: Boltz 도킹 구조 확인
4. **T3-01 K5→Orn 치환 시 DOTA 결합**: Orn은 Lys보다 ε-NH2에서 1 methylene 짧음 — DOTA-NHS coupling 효율 검증
5. **T3-02 W5-W6 응집 임계 농도**: 1 mg/mL 이상에서 aggregation 발생 여부 — DLS 또는 CD로 확인

---

*작성일: 2026-05-12 | reviewer-chemistry | PRST_N_FM 프로젝트 S3 Task*
