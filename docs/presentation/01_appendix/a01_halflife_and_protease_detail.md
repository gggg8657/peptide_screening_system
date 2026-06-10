# 부록: A-01 반감기 예측 및 프로테아제 분석 구현 상세

**작성일**: 2026-04-05
**관련 액션**: A-01 (PepCalc/PeptideCutter → 자체 구현)

---

## 보강 1: 반감기 예측 — 외부 도구 대비 구현 상세

### 외부 도구 한계

| 도구 | 반감기 예측 가능? | 한계 |
|------|:----------------:|------|
| PepCalc | **불가** | MW, pI, 전하, 흡광계수만 계산. 반감기 기능 없음 |
| PlifePred | 가능 | 서열 기반 예측. cyclic SST-14 학습 데이터 부재, 예측값은 상대 순위 참고용 |
| PEPlife 2.0 | DB 조회만 | 실험 반감기 DB (163 데이터, r=0.743). 예측기가 아니라 레퍼런스 |
| ADMETlab 3.0 | 소분자만 | HLM stability 등 있으나 MW<500 전용. SST-14 AD 밖 |

### AI팀 구현: `step08_stability.py` (300+ 줄)

**핵심 함수**: `predict_half_life(sequence, modifications)`

| 항목 | 구현 내용 |
|------|----------|
| 기본 반감기 | 3시간 (선형 펩타이드 기준) |
| 취약성 스코어링 | 20개 AA별 프로테아제 취약성 가중치 → 지수 감쇠 적용 |
| 고리화 탐지 | Cys 쌍 자동 탐지 → +24시간 보너스 (SST-14 기본 특성) |
| 변이체 페널티 | Arg/Lys/Met 등 취약 잔기 수에 비례한 감쇠 |
| 절단 부위 | dipeptide 패턴 기반 계산 |

**5종 수정(modification) 보너스**:

| 수정 타입 | 반감기 연장 | 근거 |
|----------|:----------:|------|
| `fatty_acid` (C18 지방산) | **+120시간** | Semaglutide — 알부민 결합 경로로 반감기 ~168h |
| `pegylation` (PEG 2kDa) | **+96시간** | 신장 사구체 여과 제한 효과 |
| `d_amino_acid` | **+48시간/잔기** | DPP-4, NEP 효소 저항성 |
| `cyclization` | **+24시간** | 프로테아제 접근성 감소 (SST-14 Cys3-Cys14) |
| `substitution` | **+12시간** | 프로테아제 취약 잔기 교체 (F→Nal 등) |

> C18 반감기 연장 벤치마크 (GLP-1 계열): C10≈0.8h < C12≈7.6h < C14≈9h < C16≈16h < C18≈21h (2차 회의 안건 3 데이터 기반)

**20개 AA 프로테아제 취약성 스코어** (높을수록 절단 위험):

| AA | 스코어 | 주요 효소 |
|----|:------:|----------|
| R (Arg) | 3.0 | 트립신 (C-terminal 절단) |
| K (Lys) | 2.5 | 트립신 |
| F (Phe) | 2.0 | 키모트립신 |
| Y (Tyr) | 1.8 | 키모트립신 |
| W (Trp) | 1.5 | 키모트립신 + 방사분해 취약 |
| L (Leu) | 1.2 | NEP |
| M (Met) | 1.5 | 산화 취약 |
| 나머지 | 0.2~1.0 | — |

---

## 보강 2: 프로테아제 분석 — ExPASy PeptideCutter 대비 구현 상세

### ExPASy PeptideCutter vs AI팀 구현

| 항목 | ExPASy PeptideCutter | AI팀 (`count_protease_sites()` + `pharmacology.py`) |
|------|---------------------|-----------------------------------------------------|
| 효소 수 | 다수 (범용) | **6종 선택** (방사성의약품 관련 핵심 효소) |
| 지원 효소 | Trypsin, Chymotrypsin, Pepsin 등 범용 | **Chymotrypsin** (FWYLM), **Trypsin** (KR, not before P), **NEP** (FWYLIVM), **Pepsin** (FL at acidic pH), **Elastase** (AGSV), **DPP-IV** (X-Pro/X-Ala) |
| API | **없음** (웹 수동 입력만) | 파이프라인 내 자동 호출, 배치 분석 |
| SS bond | 미고려 | SS bond 위치 인식 → 절단 부위 해석에 반영 |
| 방사성의약품 특화 | 없음 | **NEP** (신장 브러시 보더 효소, 방사성 펩타이드 분해 주요 경로), **DPP-IV** (GLP-1/SST 분해 핵심) |
| 출력 형식 | 절단 위치 시각화 (그래픽) | 효소별 절단 위치 리스트 + 총 개수 + 위치 인덱스 (JSON) |
| 배치 처리 | 불가 (1개씩 수동) | `batch_analyze()` → 수천 개 서열 일괄 처리 |

### SST-14 프로테아제 절단 분석 예시

```
AGCKNFFWKTFTSC
  │ ││││ │ │
  K4: Trypsin (C-term of K, not before P → 절단)
  F7: Chymotrypsin, NEP
  F8: Chymotrypsin, NEP
  W9: Chymotrypsin, NEP, 방사분해 취약
  K10: Trypsin
  T11-F12: NEP
```

**총 절단 위치**: Chymotrypsin 4, Trypsin 2, NEP 5~6 → **혈청 안정성 위험 구간이 FWKT pharmacophore(7-10) 근처에 집중**

이 분석은 변이 설계 시 **pharmacophore 보존과 프로테아제 저항성 사이의 트레이드오프**를 정량적으로 평가하는 데 사용된다.

---

## 참고 문헌

- Guruprasad K et al. (1990) Protein Eng. — Instability Index
- Kyte J & Doolittle RF (1982) J Mol Biol. — GRAVY
- Boman HG (2003) J Intern Med. — Boman Index
- Ikai A (1980) J Biochem. — Aliphatic Index
- Radzicka A & Wolfenden R (1988) Biochemistry. — Transfer free energy
- Varshavsky A (1996) PNAS. — N-end rule
- Eisenberg D et al. (1982) Nature. — Hydrophobic moment
- Wimley WC & White SH (1996) Nature Struct Biol. — Membrane partitioning
- Henikoff S & Henikoff JG (1992) PNAS. — BLOSUM62
