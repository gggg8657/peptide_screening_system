# pharma_properties.py vs peptides 패키지 — 종합 검증 보고서

**작성일**: 2026-03-13
**검증 대상**: `AG_src/pipeline/pharma_properties.py` (canonical), `backend/pharmacology.py` (API 래퍼)
**Ground Truth**: `peptides` PyPI v0.5.0 (Guruprasad 1990 원본 테이블 내장)

---

## 1. 배경

SST-14 유사체 평가 파이프라인에서 사용 중인 13개 문헌 기반 물리화학적 계산 메서드의 정확성·현행성을 검증.
사용자 우려: "문헌 기반인데 좀 올드한 방식들인거 같았어"

## 2. 검증 방법

### L1: 테이블 정확성 — 전수 대조
- DIWV 400개 엔트리 (20×20): peptides 패키지 instability_index() 역산으로 ground truth 추출
- Radzicka-Wolfenden 20개: peptides boman() 스케일 대조
- N-end Rule 20개: 양 파일 간 교차 비교 + ExPASy ProtParam 기준
- Kyte-Doolittle 20개: peptides hydrophobicity('KyteDoolittle') 대조

### L2: 공식 정확성 — 수치 비교
- 6개 테스트 서열 × 13개 메서드 = 78 케이스
- SST-14, All-A, Charged(KKKKDDDDEE), Hydrophobic(ILLLVVFFWW), M-rich(MMFMMTMMRR), Short(ACDEF)

### L3: 기능 커버리지 — 3자 비교 (pharma / pharmacology / peptides)

---

## 3. 발견된 버그 (수정 완료)

### 3.1 DIWV (Instability Index 다이펩타이드 가중치)

#### pharma_properties.py — 12개 오류

| 다이펩타이드 | 수정 전 | 수정 후 (peptides GT) | 영향 |
|-------------|---------|----------------------|------|
| AD | 1.0 | **-7.49** | A-D 포함 서열 |
| HL | -6.54 | **1.0** | H-L 포함 서열 |
| HR | -6.54 | **1.0** | H-R 포함 서열 |
| KQ | 24.64 | **24.68** | 타이포 (0.04) |
| LG | 20.26 | **1.0** | L-G 포함 서열 |
| MF | -14.03 | **1.0** | M-F 포함 서열 |
| MM | -14.03 | **-1.88** | M 연속 서열 (최대 12.15 오차) |
| MT | -13.34 | **-1.88** | M-T 포함 서열 |
| RH | 1.0 | **20.26** | R-H 포함 서열 |
| RR | -6.54 | **58.28** | R 연속 서열 (**최대 64.82 오차**) |
| TE | 33.60 | **20.26** | T-E 포함 서열 |
| TG | 1.0 | **-7.49** | T-G 포함 서열 |

원인: dict-of-dict 형식에서 행 간 copy-paste 전사 오류. SST-14 자체에는 해당 다이펩타이드 미포함으로 기존 테스트 미탐지.

#### pharmacology.py — 4개 오류

| 다이펩타이드 | 수정 전 | 수정 후 | 영향 |
|-------------|---------|---------|------|
| EW | -9.37 | **-14.03** | E-W 포함 서열 |
| KP | -7.49 | **-6.54** | K-P 포함 서열 |
| VK | -14.03 | **-1.88** | V-K 포함 서열 |
| YT | 33.60 | **-7.49** | Y-T 포함 서열 (**최대 41.09 오차**) |

### 3.2 Radzicka-Wolfenden (Boman Index)

| 아미노산 | pharma 수정 전 | pharmacology 수정 전 | 수정 후 (공통) | 출처 |
|---------|---------------|---------------------|---------------|------|
| **H** (His) | 2.06 | 2.06 | **4.66** | Radzicka & Wolfenden 1988 Table 1 |
| **S** (Ser) | 1.83 | 1.15 | **3.40** | 동일 |
| **W** (Trp) | -2.09 | -2.09 | **-2.33** | 동일 |
| **P** (Pro) | -2.54 | 0.0 | **-2.54** | 동일 (pharmacology에서 누락) |

### 3.3 Boman Index 부호 반전

`pharmacology.py`의 `boman_index()`가 `-sum(RW)/n` 공식을 사용하여 부호 반전.
Boman 2003 원문 및 peptides 패키지 모두 `+sum(RW)/n` (양수 = 높은 단백질 결합 가능성).

- 수정 전: SST-14 → **-0.55** (잘못된 방향)
- 수정 후: SST-14 → **+0.69** (peptides와 일치)

### 3.4 N-end Rule — 양 파일 통일

Pro를 (30.0h, "stable")로 통일. ExPASy ProtParam 기준 Pro는 포유류 레티큘로사이트에서 안정(>20h).

---

## 4. 수정 후 검증 결과

### 4.1 peptides ground truth 대비 정확도 (8개 비교 가능 메서드)

| # | Method | 테스트 서열 | 결과 |
|---|--------|-----------|------|
| 1 | GRAVY | 6/6 | **완벽 일치** |
| 2 | Boman Index | 6/6 | **완벽 일치** |
| 3 | Instability Index | 6/6 | **완벽 일치** |
| 4 | Aliphatic Index | 6/6 | **완벽 일치** |
| 5 | pI (Lehninger) | 6/6 | **완벽 일치** (오차 <0.05 pH) |
| 8 | Hydrophobic Moment | 6/6 | **완벽 일치** |
| 10 | Net Charge (pH 7.4) | 6/6 | **완벽 일치** |
| 9 | Wimley-White | — | 스케일 상이 (POPC vs pH8), 비교 불가 |

### 4.2 양 파일 간 정합성 (13개 전체 메서드)

| # | Method | pharma vs pharmacology | 비고 |
|---|--------|----------------------|------|
| 1-10, 13 | 11개 메서드 | **완전 일치** | — |
| 11 | Protease Sites | **일치** (공통 3 효소) | pharmacology에만 pepsin 추가 |
| 12 | BLOSUM62 | **설계 차이** | 아래 상세 |

### 4.3 BLOSUM62 설계 차이

| 항목 | pharma_properties.py | pharmacology.py |
|------|---------------------|----------------|
| 점수 범위 | 전체 포지션 (동일+변이) | 변이 포지션만 |
| SST-14 identical | total = 87 | total = 0 |
| K5R mutant | total = 84 | total = 2 |

pharma는 "서열 전체 보존도 점수", pharmacology는 "변이 위치 요약". 해석이 다르므로 통일 필요.

---

## 5. 수치 비교표 (SST-14: AGCKNFFWKTFTSC)

| # | 항목 | pharma_prop | pharmacology | peptides v0.5 | 일치 |
|---|------|------------|-------------|--------------|------|
| 1 | GRAVY | +0.0286 | +0.0286 | +0.0286 | ✓ |
| 2 | Boman Index (kcal/mol) | +0.6929 | +0.6929 | +0.6929 | ✓ |
| 3 | Instability Index | 30.65 | 30.65 | 30.65 | ✓ |
| 4 | Aliphatic Index | 7.14 | 7.14 | 7.14 | ✓ |
| 5 | pI (Lehninger) | 9.04 | 9.04 | 9.04 | ✓ |
| 6 | ε280 (1 SS bond) | 5625 | 5625 | — | ✓ |
| 7 | N-end (A→) | 30h/stable | 30h/stable | — | ✓ |
| 8 | μH α-helix | 0.3248 | 0.3248 | 0.3248 | ✓ |
| 9 | WW mean ΔG | -0.195 | -0.195 | -0.336* | *스케일 다름 |
| 10 | Net charge pH 7.4 | +1.709 | +1.709 | +1.709 | ✓ |
| 11 | Protease sites | 10 (3효소) | 13 (4효소) | — | 일치(공통) |
| 12 | BLOSUM62 (identical) | 87 (전체) | 0 (변이만) | — | 설계 차이 |
| 13 | Metal coord residues | 2 | 2 | — | ✓ |
| — | MW | **미구현** | **미구현** | 1639.91 Da | TODO |

---

## 6. 메서드 현행성 평가 (2026년 기준)

| # | Method | 원본 연도 | 현행성 | 판정 |
|---|--------|---------|--------|------|
| 1 | GRAVY (Kyte-Doolittle) | 1982 | 44년간 학계 표준. 대안 스케일 다수 존재하나 KD가 가장 널리 인용 | **유지** |
| 2 | Boman Index (RW) | 1988/2003 | 펩타이드 결합 가능성 유일한 단일 지표. 대안 없음 | **유지** |
| 3 | Instability Index (DIWV) | 1990 | ExPASy ProtParam 표준. 400-entry 테이블 자체는 변경 없음 | **유지** |
| 4 | Aliphatic Index | 1980 | 열안정성 surrogate로 여전히 사용 | **유지** |
| 5 | pI (bisection) | 1993 | IPC 2.0 (2021)이 사이클릭/변형 펩타이드에 더 정확 | **업데이트 고려** |
| 6 | ε280 (Pace) | 1995 | 표준. 변경 필요 없음 | **유지** |
| 7 | N-end Rule (Varshavsky) | 1996 | 2019 "N-degron pathway"로 명칭 변경. Pro/N-degron 별도 경로 발견 (2018). 사이클릭 펩타이드에서는 N-말단 미노출로 적용성 제한적 | **유지 (참고용)** |
| 8 | Hydrophobic Moment (Eisenberg) | 1982 | 막 투과 예측 표준. α-helix/β-sheet 구분 지원 | **유지** |
| 9 | Wimley-White | 1996 | POPC 인터페이스 표준 스케일. 대안: octanol scale | **유지** |
| 10 | Net Charge (H-H) | — | Henderson-Hasselbalch 표준. SS bond Cys 보정 미구현 | **보정 필요** |
| 11 | Protease Sites | — | MEROPS DB 기반. DPP-IV 추가 권장 | **확장 고려** |
| 12 | BLOSUM62 | 1992 | 표준 치환 행렬. 변경 불필요 | **유지** |
| 13 | Metal Coordination | 1998 | Ga3+ 아미노산 배위 규칙이 너무 단순 (H만). D/E carboxylate도 Ga3+ 배위 가능 | **업데이트 고려** |

**결론**: 13개 중 10개는 2026년 기준으로도 gold standard. "올드"한 것이 아니라 "검증된(established)" 방법들. 문제는 메서드 자체가 아니라 lookup table 전사 오류였음.

---

## 7. 기능 커버리지 비교

| 기능 | pharma_prop | pharmacology | peptides | 비고 |
|------|:-----------:|:------------:|:--------:|------|
| 13개 기본 메서드 | ✓ | ✓ | 8/13 | GT 비교 가능 8개 완벽 일치 |
| SS bond Cys pI 보정 | — | — | — | **3자 모두 미지원. P0 구현 필요** |
| MW 계산 | — | — | ✓ | P1 추가 권장 |
| pH profile (다중 pH) | — | ✓ | — | pharmacology 전용 |
| Pepsin sites | — | ✓ | — | pharmacology 전용 |
| 5대 구조 규칙 | ✓ | — | — | 도메인 특화 (FWKT, K9-D122 등) |
| Batch analyze | ✓ | — | — | 파이프라인 전용 |
| Input validation | ✓ | — | — | 빈 서열/비표준 잔기 방어 |
| Sequence entropy | — | — | ✓ | 선택적 |
| ESI m/z | — | — | ✓ | 방사성의약품 설계 시 유용 |

---

## 8. 남은 작업 (우선순위)

| 우선순위 | 항목 | 이유 | 영향도 |
|---------|------|------|--------|
| **P0** | SS bond Cys pI/charge 보정 | SST-14 Cys3-Cys14 → pI 약 0.2-1.1 pH 오차. 방사성의약품 신장 클리어런스 판단에 직결 | 높음 |
| **P1** | BLOSUM62 설계 통일 | 양쪽 결과 해석 불일치 | 중간 |
| **P1** | MW 구현 | 방사성의약품 MW 검증 필수 (chelator+nuclide 포함 계산) | 중간 |
| **P2** | pharmacology.py → pharma_properties.py 래핑 | 중복 테이블 관리 제거 (재발 방지) | 구조적 |
| **P3** | Pepsin, DPP-IV protease 추가 | 혈청 안정성 예측 커버리지 확장 | 낮음 |
| **P3** | Metal Coordination Ga3+ D/E 배위 추가 | 68Ga 킬레이션 정확도 | 낮음 |

---

## 9. 수정 이력

| 파일 | 변경 | 건수 |
|------|------|------|
| `AG_src/pipeline/pharma_properties.py` | DIWV 12개 + RW H/S/W + N-end P | 16 |
| `backend/pharmacology.py` | DIWV 4개 + RW H/S/W/P + Boman 부호 + N-end P | 8 |
| `tests/test_pharma_vs_peptides_pkg.py` | Boman 부호 테스트 갱신 | 1 |

검증: 62/62 테스트 통과, DIWV 400개 전수 대조 0 errors, 8개 메서드 peptides GT 대비 완벽 일치.
