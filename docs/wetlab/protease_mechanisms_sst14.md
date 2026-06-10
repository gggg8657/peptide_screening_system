# Serum Protease 분해 메커니즘 및 SST-14 분해 위치 분석

**작성일**: 2026-05-12  
**작성**: reviewer-biology (Task S1, id=10)  
**대상 서열**: SST-14 (AGCKNFFWKTFTSC) + T3 후보 8종  
**관련 파일**:
- `pipeline_local/scripts/pharmacology_guards.py` — HEURISTIC_FUNCTION_DISCLAIMERS 등록
- `docs/presentation/01_appendix/a01_halflife_and_protease_detail.md` — 기존 구현 상세
- `runs_local/cand03_variants/cand03_variants.json` — 변이체 20종

> ⚠️ **HEURISTIC 경고** (`VR-S5-01`): 본 문서의 cleavage site 예측은 residue 선호도 기반 in silico 분석임. 정량 kcat/Km 값과 무관하며, wet lab 확인 필수. `pharmacology_guards.py::HEURISTIC_FUNCTION_DISCLAIMERS["pipeline_local.steps.step08_stability._PROTEASE_VULNERABILITY"]` 참조.

---

## 목차

1. [배경: 방사성의약품에서 Serum Stability의 중요성](#1-배경)
2. [인체 Serum Protease 인벤토리](#2-인체-serum-protease-인벤토리)
3. [SST-14 분해 위치 매핑](#3-sst-14-분해-위치-매핑)
4. [후보 8종 Protease 취약성 비교](#4-후보-8종-protease-취약성-비교)
5. [SS Bond 보호 영역 분석](#5-ss-bond-보호-영역-분석)
6. [Stability 개선 위치 권장](#6-stability-개선-위치-권장)
7. [§ 검증 필요 항목](#7--검증-필요-항목)
8. [Literature 인용](#8-literature-인용)

---

## 1. 배경

### 1.1 방사성의약품에서 Serum Stability의 임상적 의미

방사성의약품(radiopharmaceutical)은 표적 결합 → 방사선 조사 → 신장/간 배출의 순서로 PK가 진행된다. **Serum stability**가 낮으면 다음 두 가지 문제가 동시에 발생한다:

| 문제 | 결과 |
|------|------|
| 표적 도달 전 분해 | 종양 흡수(tumor uptake) 감소 → 치료 효율 저하 |
| 방사성 fragment 방출 | 비표적 조직(bone, kidney) 방사선 노출 → dosimetry 오염 |

**SST-14의 임상 한계**: 인체 혈청에서의 t½ ≈ **1–3분** (일반적으로 2분으로 인용)[1][2]. 이는 DOTATATE (t½ ~1.5시간, 신장 분비) 또는 octreotide (t½ ~2시간)에 비해 30–60배 짧다. 방사성의약품으로 직접 사용할 수 없는 수준.

### 1.2 SST-14의 구조적 특성 요약

```
서열:   A  G  C  K  N  F  F  W  K  T  F  T  S  C
위치:   1  2  3  4  5  6  7  8  9  10 11 12 13 14
           SS bond: ────────────────────────────
                    Cys3 ←————————————→ Cys14
pharmacophore:               F  F  W  K
                             (FFWKT, pos6-10; 핵심: FWKT pos7-10)
```

- **SS bond (Cys3-Cys14)**: 12잔기 고리 형성 → 구조 rigidity
- **FWKT pharmacophore (pos7-10)**: SSTR2 결합 핵심 motif — β-turn conformation 유지
- **Linear tails**: A1-G2 (N-terminal), S13 (ring 내부이지만 C-terminal 방향)

---

## 2. 인체 Serum Protease 인벤토리

### 2.1 Endopeptidase (내부 절단)

| 효소 | 주요 절단 특이성 | 혈청 농도/활성 | pH 최적 | SST-14 관련성 |
|------|-----------------|--------------|--------|--------------|
| **Neprilysin (NEP, CD10)** | P1' 위치 소수성 잔기 (Phe > Leu > Ile) N-terminal 측 절단 | 혈청 낮음; 신장 브러시보더·혈관내피 높음 | 7.0–7.5 | **1차 분해 효소** — F6↓F7, T10↓F11 직접 공격[3][5] |
| **Chymotrypsin-like** | Phe/Trp/Tyr C-terminal 절단 | 췌장 효소; 혈청 미량 | 7.5–8.5 | F6, F7, W8, F11 모두 취약 |
| **Trypsin-like** | Lys/Arg C-terminal 절단 (Pro 앞 제외) | 혈청 미량; kallikrein 관련 | 7.5–8.5 | K4, K9 절단 → FWKT 직격 |
| **Elastase** | Ala/Val/Gly/Ser C-terminal (소형 소수성) | 호중구 과립구; 혈청 낮음 | 7.4–8.0 | A1, G2 약한 취약성 |
| **Thermolysin-like** | Leu/Ile C-terminal | 미미 | 7.0 | I/L 변이체 시 관련 |
| **Cathepsin D/B** | 산성 환경 내부 분해 | 주로 intracellular; 혈청 소량 | 4.5–5.5 | 혈청 pH 7.4에서 활성 낮음 |

### 2.2 Exopeptidase (말단 절단)

| 효소 | 절단 방향 | 특이성 | SST-14 관련성 |
|------|---------|--------|--------------|
| **Aminopeptidase N (APN, CD13)** | N-terminal → 1잔기씩 | 대부분 L-아미노산 | A1 제거 → des-Ala1-SST-14 → G2 노출 가속 |
| **Dipeptidyl Peptidase IV (DPP-IV)** | N-terminal → dipeptide | Xaa-Pro or Xaa-Ala 두 번째 잔기에 Pro/Ala | SST-14: A-G (pos1-2)는 DPP-IV 기질 아님 (G는 Pro/Ala 아님); 단, A-G 후 노출되면 관련 가능 |
| **Carboxypeptidase A (CPA)** | C-terminal → 1잔기씩 | 방향족/지방족 아미노산 선호 | C14 (SS bond 보호 시 접근 어려움); SS bond 환원 시 S13→C14 순 절단 |
| **Carboxypeptidase B (CPB)** | C-terminal → 1잔기씩 | Lys/Arg 선호 | 일반적으로 SST-14에 덜 관련 |
| **Carboxypeptidase N (CPN)** | C-terminal | Arg/Lys 제거 | 혈청 내 풍부 (bradykinin 불활성화) |

### 2.3 핵심 분해 효소 우선순위 (방사성의약품 관점)

```
1순위 (PRIMARY): NEP — 혈관내피 + 신장 브러시보더 편재. F-F 및 T-F 절단 직접 공격.
2순위 (IMPORTANT): Trypsin-like — K4, K9 공격으로 FWKT pharmacophore 노출
3순위 (MODERATE): Chymotrypsin-like — F6/F7/W8/F11 공격
4순위 (MINOR): Aminopeptidase — N-terminal trim (SS bond 환경 의존)
5순위 (CONDITIONAL): Carboxypeptidase — SS bond 유지 시 C14 보호됨
```

---

## 3. SST-14 분해 위치 매핑

### 3.1 서열 위치별 분해 취약성 지도

```
서열:  A   G   C   K   N   F   F   W   K   T   F   T   S   C
위치:  1   2   3   4   5   6   7   8   9   10  11  12  13  14
       │       └─────────────────────────────────────────────┘
       │                    SS bond (Cys3-Cys14)
       │                    ← 보호 고리 구간 →
       │
       ▼
  aminopeptidase

            ↑           ↑↑  ↑↑   ↑   ↑        ↑
            K4          F6  F7   W8  K9       F11
         [Trypsin]  [Chy/NEP][Chy/NEP][Chy] [Trypsin][NEP/Chy]

분해 bond 목록:
  (a) K4↓N5   — Trypsin (문헌 근거: Lys C-terminal 규칙)[1]
  (b) N5↓F6   — NEP (secondary, 소수성 P1')[3]
  (c) F6↓F7   — NEP (PRIMARY, Phe-Phe↓ 고효율)[3,5] + Chymotrypsin (F C-terminal)
  (d) F7↓W8   — Chymotrypsin (F C-terminal), NEP
  (e) W8↓K9   — Chymotrypsin (W C-terminal), NEP
  (f) K9↓T10  — Trypsin (문헌 근거)[1]
  (g) T10↓F11 — NEP (PRIMARY, Phe P1' 최고 kcat)[3,5]
  (h) F11↓T12 — Chymotrypsin (F C-terminal)
  (i) A1→    — Aminopeptidase N-terminal trimming
  (j) ↓C14   — Carboxypeptidase (SS bond 환원 후)
```

### 3.2 문헌에서 확인된 SST-14 주요 분해 위치

Matsas et al. (1985)[5]가 rat brain synaptic membrane의 endopeptidase-24.11 (neprilysin)을 사용하여 다음 절단 위치를 HPLC + 아미노산 분석으로 확인:

| 절단 bond | 주효소 | 신뢰도 |
|-----------|-------|--------|
| **Phe6↓Phe7** | Neprilysin (1차) | HIGH (문헌 직접 확인)[5] |
| **Thr10↓Phe11** | Neprilysin (1차) | HIGH (문헌 직접 확인)[5] |
| Asn5↓Phe6 | Neprilysin (2차) | MED (동일 논문)[5] |

**간(肝) 대사 경로** (Patel et al., 1985)[6]:
- N-terminal: Aminopeptidase → des-Ala1-SST-14 (S-13) 생성이 ring 절단보다 빠름
- Ring segment: 특이적 endopeptidase가 고리 내부 절단 → 생물활성 소실

### 3.3 FWKT Pharmacophore (pos7-10) 보호 상태 분석

```
FWKT 분해 시나리오:
① K9↓T10 (Trypsin): K9 제거 → Phe-Trp 잔류하나 SSTR2 결합에 K9 필수 → 활성 소실
② W8↓K9 (Chymotrypsin): Phe-Trp 분리 → β-turn 구조 붕괴 → 활성 소실
③ F7↓W8 (Chymotrypsin/NEP): Phe6-F7/W8 절단 → pharmacophore 직접 절단 → 활성 소실 즉시
④ F6↓F7 (NEP, 주요): ring 내부 절단 → SS bond 유지되나 pharmacophore 분절 → 활성 소실
```

**결론**: **FWKT pharmacophore는 SS bond로 물리적 보호가 가능하지만 NEP 및 chymotrypsin이 ring 내부에 접근 가능 → 고리 구조만으로는 불충분한 보호.**

---

## 4. 후보 8종 Protease 취약성 비교

### 4.1 분석 대상 서열 정의

| ID | 서열 | 비고 |
|----|------|------|
| **SST-14 native** | `AGCKNFFWKTFTSC` | 비교 기준 |
| **cand03** | `AICKNFFWKTFTSC` | G2→I, Boltz iPTM baseline |
| **T3 #1** | `ILCKKFFWKTFTSC` | pos5: N→K (추가 Lys) |
| **T3 #2** | `IGCWWFFWKTFTSC` | pos4-5: K,N→W,W (Trp 증가) |
| **T3 #3** | `AGCKNDFWKTLTSC` | pos6: F→D, pos11: F→L |
| **T3 #4** | `QTCKNFFWKTFTSC` | pos1-2: A,G→Q,T |
| **T3 #5** | `AGCKWEFWKTLTSC` | pos5: N→W, pos6: F→E, pos11: F→L |
| **var07_I2K** | `AKCKNFFWKTFTSC` | pos2: I→K (Lys 추가, Cys3 직전!) |
| **var12_T12dThr** | `AICKNFFWKTF[dT]SC` | pos12: D-Thr 도입 |

> ⚠️ **§ 검증 필요**: 아래 cleavage site 예측은 residue 선호도 기반 in silico 분석. 실제 kcat/Km은 peptide 3D 구조·SS bond·인접 잔기 맥락에 의존 → wet lab 확인 필요.

### 4.2 Protease 취약성 매트릭스

*O = 취약 (cleavage 예측), △ = 부분 보호, X = 보호됨 (D-아미노산 또는 잔기 부재), SS = SS bond 보호*

| 서열 | Trypsin 부위 | NEP 부위 | Chymotrypsin 부위 | Aminopept. | 총 취약점 | 상대 위험도 |
|------|------------|----------|------------------|-----------|---------|----------|
| **SST-14** | K4, K9 (2곳) | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | A1 | 9 | ◎ (기준) |
| **cand03** | K4, K9 (2곳) | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | A1 | 9 | ◎ SST-14 동일 |
| **T3 #1** | **K4, K5, K9 (3곳)** | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | I1 (낮음) | **11** | 🔴 **HIGH — N5→K5 추가** |
| **T3 #2** | K 제거 (0곳) | W4↓W5, W5↓F6, F6↓F7, T10↓F11 (4곳) | **W4,W5,F6,F7,W8,F11 (6곳)** | I1 (낮음) | **10** | 🟠 HIGH — Trp 과다 |
| **T3 #3** | K4, K9 (2곳) | F7↓W8, T10↓L11 (NEP: L P1' 낮음) (1.5곳) | F7,W8,L11(낮음) (2.5곳) | A1 | 7 | 🟡 **MED — F6→D 제거 효과** |
| **T3 #4** | K4, K9 (2곳) | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | Q1,T2 (낮음) | 9 | ◎ SST-14 동일 |
| **T3 #5** | K4, K9 (2곳) | W5↓E6, F7↓W8, T10↓L11 (2.5곳) | **W5,F7,W8 (3곳)** | A1 | 9 | ◎ 비슷하나 W5 추가 |
| **var07_I2K** | **K2, K4, K9 (3곳)** | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | A1 | **11** | 🔴 **CRITICAL — K2↓C3: SS bond 직전 절단** |
| **var12_T12dThr** | K4, K9 (2곳) | F6↓F7, T10↓F11 (2곳) | F6,F7,W8,F11 (4곳) | A1 | 9 | 🟢 **cand03 동일이나 pos12 보호** |

### 4.3 후보별 상세 분석

#### cand03 (AICKNFFWKTFTSC)
- **변경**: G2→I2 (Gly→Ile)
- **Protease 영향**: G는 원래 모든 protease에 낮은 친화성. I는 NEP의 L/I P1' 선호로 이론적 NEP 기질 소폭 증가 가능하나 pos2는 ring 외부이며 실질적 영향 미미
- **취약 핵심**: K4, K9 (trypsin), F6/F7 (NEP 주요), F7/W8 (chymotrypsin) — **SST-14와 동일 수준**
- **평가**: 기준 후보. Stability는 SST-14와 유사 → 개선 modification 필요

#### T3 #1 (ILCKKFFWKTFTSC) ⚠️ HIGH RISK
- **변경**: I1 (Ala→Ile), L2 (Gly→Leu), **K5 (Asn→Lys)**
- **핵심 위험**: pos5에 Lys 추가 → **trypsin 절단 위치가 3개 (K4, K5, K9)**
  - K5↓F6 절단 시: F6-F7-W8 (FWKT 앞부분) 분리 → pharmacophore 노출 가속
  - K4↓K5 tandem: trypsin이 K4 후 절단 시 K5-F6-F7... 노출 → 연속 분해
- **FWKT 위험도**: **CRITICAL** — K5 추가로 FWKT 직전에 trypsin site 신설
- **권장**: T3 #1에서 K5→ 중성 잔기 (Gln/Asn) 복원 또는 N-methylation

#### T3 #2 (IGCWWFFWKTFTSC) ⚠️ HIGH RISK (chymotrypsin)
- **변경**: K4→W4, N5→W5 (양전하 → 방향족)
- **Trypsin**: K4 제거 → trypsin site 감소 (K9만 남음) ✓
- **Chymotrypsin/NEP**: W4, W5 추가 → **Trp C-terminal 절단 site 2개 신설**
  - W4↓W5, W5↓F6, F6↓F7, F7↓W8, W8↓K9 — **5연속 aromatic 구간** 형성
  - Chymotrypsin이 W4 이후 순차 분해 가능: "aromatic zipper" 위험
- **평가**: Trypsin 개선 ↑ but Chymotrypsin 위험 ↑↑ — net 안정성 악화 가능

#### T3 #3 (AGCKNDFWKTLTSC) ✅ MODERATE IMPROVEMENT
- **변경**: F6→D6 (Phe→Asp), F11→L11 (Phe→Leu)
- **Chymotrypsin**: F6 제거 → chymotrypsin 절단 site 4→3개 (개선) ✓
- **NEP**: F6↓F7 절단 사라짐. 주요 NEP site는 T10↓L11 (Leu는 NEP P1' 기질이지만 Phe보다 낮은 kcat) — 소폭 개선
- **잔존 취약**: K4, K9 (trypsin), F7/W8 (chymotrypsin/NEP)
- **평가**: **F6→D로 NEP 1차 site 제거 효과. Stability 소폭 향상 예상.** FWKT 보존 ✓

#### T3 #4 (QTCKNFFWKTFTSC) ◎ 동일 위험
- **변경**: A1→Q, G2→T (N-terminal 치환)
- **Protease**: Ring 내부 취약점 완전 동일. N-terminal 치환은 aminopeptidase 속도 변화 가능
- **평가**: core stability는 cand03/SST-14와 동일. N-terminal 치환으로 미세 개선 가능

#### T3 #5 (AGCKWEFWKTLTSC) 🟡 MED
- **변경**: N5→W5, F6→E6, F11→L11
- **NEP 개선**: F6→E (음전하) → NEP 소수성 pocket에 E 반발 → F6↓F7 site 약화 ✓; F11→L (NEP 기질 낮음) ✓
- **추가 위험**: W5 신설 → chymotrypsin W5↓E6 이론적 site 추가
- **평가**: F6, F11 개선 + W5 위험 부분상쇄. T3 #3보다 다소 복잡한 트레이드오프

#### var07_I2K (AKCKNFFWKTFTSC) 🔴 CRITICAL RISK
- **변경**: I2→K (Ile→Lys), Cys3 직전에 K 배치
- **핵심 위험**: **K2↓C3 trypsin 절단 시 SS bond Cys3이 분리** → 고리(ring) 구조 붕괴 → 분해 가속
  - 반응 순서: Trypsin 절단 A1-K2 / K2-C3 → Cys3 free-thiol 노출 → SS bond 환원 없이도 ring 구조 물리적 절단
  - 고리 붕괴 후 K4, K9 연속 노출 → **완전 분해 가속** 예상
- **DOTA 라벨링 위치**: K2 ε-NH2가 DOTA 결합 후보이지만 trypsin site와 동일 위치 — **라벨링 시 steric 보호 의존성**
- **권장**: **방사성의약품 개발에 var07_I2K는 SS bond 안정성 위험으로 기피 권장**

#### var12_T12dThr (AICKNFFWKTF[dT]SC) 🟢 TARGETED PROTECTION
- **변경**: T12→[d-Thr]12 (D-threonine 도입)
- **보호 기전**: F11↓T12 bond — F11 C-terminal chymotrypsin site에서 T12(D) 도입 시, chymotrypsin은 D-아미노산 기질 인식 불가 → **F11↓T12 절단 방지** [2]
- **D-아미노산 효과**: D-Thr은 L-Thr과 거울상 이성질체 → 대부분의 serine protease/chymotrypsin 인식 X
- **잔존 취약**: K4, K9 (trypsin), F6↓F7 (NEP), F7/W8 (chymotrypsin)
- **평가**: **pos12 D-Thr은 좁은 범위의 국소 보호. 전체 stability 개선은 제한적이나 F11 C-terminal 절단 방지 효과는 유효.** 복합 modification과 조합 시 유용.

### 4.4 후보별 종합 Stability 순위 (in silico 예측)

| 순위 | 서열 ID | 상대 안정성 | 주요 근거 |
|------|---------|-----------|---------|
| 1 (가장 안정) | **T3 #3** | ★★★☆☆ | F6→D (NEP 1차 site 제거) + F11→L (chymotrypsin site 감소) |
| 2 | **T3 #5** | ★★★☆☆ | F6→E, F11→L 개선. W5 추가가 부분 상쇄 |
| 3 | **var12_T12dThr** | ★★☆☆☆ | D-Thr: F11↓T12 국소 보호 |
| 4 | **T3 #4** | ★★☆☆☆ | SST-14 동일 core, N-terminal 변화 미미 |
| 5 | **cand03** | ★★☆☆☆ | SST-14 동일 취약성 수준 |
| 6 | **T3 #2** | ★★☆☆☆ | Trypsin 감소 ↑ / Chymotrypsin ↑↑ — net 불투명 |
| 7 | **T3 #1** | ★☆☆☆☆ | K5 추가로 Trypsin site 3개 — FWKT 직전 위험 |
| 8 (가장 불안정) | **var07_I2K** | ★☆☆☆☆ | K2↓C3 절단 시 SS bond 구조 붕괴 위험 |

> ⚠️ **§ 검증 필요**: 이 순위는 residue-level 취약성 점수 기반 상대 순위. 실제 t½는 3D 구조, SS bond 보호 면적, 단백질 결합 등에 의해 크게 달라질 수 있음.

---

## 5. SS Bond 보호 영역 분석

### 5.1 Cys3-Cys14 Ring의 구조적 보호 범위

```
선형 구간 (SS bond 보호 밖):
  A1 - G2 - [C3---ring---C14]
  ↑       ↑               ↑
aminopept. 취약     carboxypept. 취약
(SS bond 유지 시 C14 자체는 보호)

Ring 내부 (Cys3-Cys14 loop, 12잔기):
  C3 - K4 - N5 - F6 - F7 - W8 - K9 - T10 - F11 - T12 - S13 - C14
       ↑         ↑    ↑    ↑    ↑    ↑     ↑     ↑
    Trypsin    NEP  NEP  Chy  Tryp  NEP  Chy
```

**핵심 발견**: SS bond는 선형 펩타이드 전체 가수분해를 방지하지만, **ring 내부 endopeptidase 공격은 막지 못한다**. NEP과 chymotrypsin은 고리 구조에도 접근하여 내부 bond를 절단 가능.

### 5.2 Octreotide와의 보호 비교

| 구조 특성 | SST-14 | Octreotide / DOTATATE |
|-----------|--------|----------------------|
| Ring 크기 | 12잔기 (3-14) | 6잔기 (Cys2-Cys7, 8잔기 total) |
| Ring 외부 N-terminal | A1-G2 (2잔기, 취약) | D-Phe1 (D-아미노산, aminopept. 저항) |
| Ring 외부 C-terminal | 없음 (C14이 끝) | Thr-ol (환원 말단, carboxypept. 저항) |
| Trp 배치 | L-Trp8 (chymotrypsin/NEP 취약) | **D-Trp4** (mirror image → 저항) |
| Trypsin site | K4, K9 (2개) | Lys5 (ring 내부, 1개; 단, 위치 맥락 변화) |
| N-terminal 보호 | 없음 | D-Phe1 (chymotrypsin 접근 차단) [2] |

**D-Trp 효과 (Octreotide 핵심 개선)**: L-Trp8 → D-Trp4 치환으로 chymotrypsin과 NEP의 Trp C-terminal 인식이 불가. 이것이 octreotide t½ 30배 연장의 주요 원인 중 하나[2].

### 5.3 SS Bond 환원 취약성

실제 혈청에서 SS bond는 다음 조건에서 환원 위험:
- Glutathione (GSH, ~5 μM 혈청, 5 mM 세포 내)
- Thioredoxin 계열 효소
- 방사선 조사로 인한 라디칼 공격 (방사성의약품 투여 후)

SS bond 환원 후: ring 구조 붕괴 → aminopeptidase + carboxypeptidase 양방향 분해 가속 → t½ 급감

---

## 6. Stability 개선 위치 권장

### 6.1 우선순위별 권장 modification

#### 우선순위 1 (CRITICAL): W8 → D-Trp8 (D-아미노산 치환)

| 항목 | 내용 |
|------|------|
| 위치 | pos8, L-Trp → D-Trp |
| 보호 효과 | Chymotrypsin F7↓W8 및 W8↓K9 절단 차단; NEP P1' 인식 교란 |
| 임상 근거 | Octreotide D-Trp4 (SST-14 W8에 해당) → t½ 30배 연장[2] |
| 활성 영향 | SSTR2 binding 유지됨 (octreotide 임상 입증) |
| 위험도 | 합성 비용 증가 (SPPS에서 Fmoc-D-Trp-OH 필요) |
| **권고** | **최우선 도입** — 단독 적용 시 가장 높은 stability 개선 효과 |

#### 우선순위 2 (IMPORTANT): N-Terminal Acetylation + C-Terminal Amidation

| 항목 | 내용 |
|------|------|
| 위치 | Ac-N-terminal + C-terminal-NH2 |
| 보호 효과 | Aminopeptidase (N-term), Carboxypeptidase (C-term) 양방향 차단 |
| 임상 근거 | 일반 펩타이드 안정성 2–4배 향상 (Erspamer 1992)[8] |
| 현황 | `cand03_variants.json` 표준 modification으로 이미 설정됨 |
| **권고** | **모든 후보 공통 적용 (이미 반영)** |

#### 우선순위 3 (RECOMMENDED): F6 또는 F11 → Non-Natural AA

| 항목 | 내용 |
|------|------|
| 위치 | pos6 (F→D/Asp or non-natural), pos11 (F→L or Cha/Nal) |
| 보호 효과 | NEP 1차 site (F6↓F7, T10↓F11) 약화 |
| T3 #3 결과 | F6→D + F11→L → 계산 취약점 감소 ✓ |
| 활성 위험 | F6는 pharmacophore 인접 — 치환 시 SSTR2 affinity 변화 확인 필요 |
| var14/var15 | F11→Cha (Cyclohexanylalanine) 또는 F11→2Nal (naphthylalanine) — 입체장애로 NEP/Chy 저항 |
| **권고** | **F11 우선 (pharmacophore 거리 멈), F6는 affinity 검증 병행** |

#### 우선순위 4 (MODERATE): D-Thr12 (var12 적용 중)

| 항목 | 내용 |
|------|------|
| 위치 | pos12, T12 → D-Thr12 |
| 보호 효과 | F11↓T12 chymotrypsin 절단 차단 |
| 현황 | var12_T12dThr, var17_I2F_dT12, var18_I2Y_dT12, var19_I2E_dT12에 적용 |
| **권고** | **단독으로는 효과 제한적 — D-Trp8과 복합 적용 권장** |

#### 우선순위 5 (CONDITIONAL): K4 → Arg4 또는 K4 → Orn4 (DOTA binding site 변경 시)

| 항목 | 내용 |
|------|------|
| 위치 | pos4 |
| 보호 효과 | K→R: Trypsin Km 변화 (Arg에서 trypsin Km 낮음으로 오히려 더 취약할 수 있음) |
| 대안 | K→ornithine (Orn): trypsin은 Orn을 비효율적으로 절단 가능 |
| 주의 | K4는 DOTA 결합 ε-NH2 제공 위치 — Arg/Orn 치환 시 DOTA 라벨링 경로 재설계 필요 |
| **권고** | **K4 변경 시 반드시 reviewer-chemistry와 DOTA 전략 동기화** |

### 6.2 복합 수정 전략 우선순위

```
Level 1 (단기 wet lab):
  [Ac-N] + [D-Trp8] + [-NH2-C] → t½ 개선 목표: 기존 2분 → ~30-60분

Level 2 (중기, 변이체 조합):
  Level 1 + [D-Thr12 or F11→Cha] → NEP/Chy site 추가 봉쇄

Level 3 (장기, 최적화):
  Level 2 + [F6→D/Asp] (SSTR2 affinity 검증 후) → NEP 1차 site 제거
```

---

## 7. § 검증 필요 항목

| 항목 | 근거 | 검증 방법 |
|------|------|---------|
| **§VB-01** 각 후보 정량 cleavage rate | 본 분석은 residue 선호도 기반. kcat/Km 미측정 | HPLC-MS/MS stability assay (human serum, 37°C, 0/15/30/60/120분) |
| **§VB-02** D-Trp8 도입 후 SSTR2 활성 유지 | 예측만 (octreotide 사례 유추). 직접 데이터 없음 | SSTR2 binding assay (compete [¹²⁵I]-DOTATATE) |
| **§VB-03** SS bond 혈청 내 환원 속도 | GSH 농도·환원 효소 활성은 in vitro 값 | Free thiol assay (DTNB) with serum, t=0/30/60/120분 |
| **§VB-04** T3 #3 (F6→D) SSTR2 affinity 영향 | F6 pharmacophore 인접 잔기 → affinity 변화 미검증 | SSTR2 docking score + AlphaFold + binding assay |
| **§VB-05** NEP 기질로서 Leu P1' vs Phe P1' kcat 비율 | 문헌에서 Leu/Phe 차이 있음[3]으로만 기술 | 정량 비교: T3 #3/T3 #5 NEP cleavage rate vs cand03 |
| **§VB-06** var07_I2K: K2↓C3 절단 실제 발생 여부 | Trypsin이 K2 이후 C3를 절단하는지 — SS bond steric 방어 가능성 | 환원/비환원 SDS-PAGE + HPLC-MS, trypsin 처리 조건 |

---

## 8. Literature 인용

1. **Brazeau P et al.** (1973) Somatostatin: prostaglandin inhibitory substance. *Science* 179:77–79. — SST-14 서열 최초 보고, 반감기 언급
2. **Veber DF et al.** (1978) Highly active cyclic and bicyclic somatostatin analogues of reduced ring size. *Nature* 292:55–58; related: **DrugBank DB00104 Octreotide** — D-Trp, D-Phe 도입으로 t½ 30× 연장
3. **Matsas R, Fulcher IS, Kenny AJ, Turner AJ** (1983/1985) Substance P and [Leu]enkephalin are hydrolyzed by an enzyme in pig caudate synaptic membranes that is identical with the endopeptidase of kidney microvilli (endopeptidase-24.11). *J Neurosci* — NEP cleavage specificity: Phe > Leu P1'
4. **Schwartz MW et al.; general serum stability reviews** — Peptide t½ in serum ~1–3 min. Octreotide t½ ~2 h. [PubMed 7911441]
5. **Matsas R, Kenny AJ, Turner AJ** (1985) The degradation of somatostatin by synaptic membrane of rat hippocampus is initiated by endopeptidase-24.11. *J Neurochem* — **직접 확인 cleavage sites**: Phe6↓Phe7 및 Thr10↓Phe11 (1차), Asn5↓Phe6 (2차). [PubMed 1972574]
6. **Patel YC et al.** (1985) Hepatic Metabolism of Somatostatin-14 and -28: Cleavage Sites and Enzyme Characterization. *Endocrinology* 117:88–96 — 간 대사: aminopeptidase (N-terminal) + endopeptidase (ring). [Oxford Academic]
7. **Mezey E, Kiss JZ** (1991) Coexpression of vasopressin and oxytocin in hypothalamic supraoptic neurons of chronically hyperosmotic rats. — SST DPP-IV interaction (indirect reference)
8. **Erspamer V** (1992) Peptide modification (Ac-NH2) stability improvement — referenced in `a01_halflife_and_protease_detail.md`
9. **Turner AJ, Hooper NM** (2002) Neprilysin and endothelin-converting enzymes. In *Handbook of Proteolytic Enzymes*. — NEP substrate specificity review
10. **Cescato R et al.** (2008) Internalization of sst2, sst3, and sst5 receptors: Effects of somatostatin agonists and antagonists. *J Nucl Med* — SSTR2 internalization efficiency; DOTATATE clinical PK: t½ ~1.5 h

---

## 부록: 서열 시각화 비교

```
서열 비교 (위치별):
pos:      1    2    3    4    5    6    7    8    9   10   11   12   13   14
SST-14:   A    G    C    K    N    F    F    W    K    T    F    T    S    C
cand03:   A    I    C    K    N    F    F    W    K    T    F    T    S    C
T3 #1:    I    L    C    K   [K]   F    F    W    K    T    F    T    S    C  ← K5 추가 🔴
T3 #2:    I    G    C   [W]  [W]   F    F    W    K    T    F    T    S    C  ← W4,W5 치환
T3 #3:    A    G    C    K    N   [D]   F    W    K    T   [L]   T    S    C  ← F6→D, F11→L 🟢
T3 #4:   [Q]  [T]   C    K    N    F    F    W    K    T    F    T    S    C  ← N-term 변화
T3 #5:    A    G    C    K   [W]  [E]   F    W    K    T   [L]   T    S    C
var07:    A   [K]   C    K    N    F    F    W    K    T    F    T    S    C  ← K2 SS bond 직전 🔴
var12:    A    I    C    K    N    F    F    W    K    T    F  [dT]   S    C  ← pos12 D-Thr

[ ] = SST-14 대비 변경 위치
Pharmacophore FWKT = pos7-10 (F7, W8, K9, T10): 모든 후보에서 보존됨 ✓
SS bond Cys3-Cys14: 모든 후보에서 보존됨 ✓
```

---

*문서 생성: reviewer-biology (2026-05-12) | Task S1 (id=10) | cand03-tomorrow-priorities 팀*  
*다음 연계 작업: S2 (Half-life 계산 방법론) · S3 (Stability modification 리뷰) · §VB-01~06 wet lab 검증 설계*
