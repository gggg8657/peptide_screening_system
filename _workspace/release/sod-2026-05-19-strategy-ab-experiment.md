# 4 Strategy A/B 비교 — 2026-05-19

*생성 시각: 2026-05-19 07:01 UTC*

## 실험 조건

- seed: `AGCKNFFWKTFTSC`
- fixed_positions: Cys3, FWKT(7-10), Cys14 — `{3: 'C', 7: 'F', 8: 'W', 9: 'K', 10: 'T', 14: 'C'}`
- max_variants: 50

## 결과 요약

| Strategy | 상태 | unique seq | BLOSUM mean | fixed 보존 | hamming mean | hamming max | 시간 |
|----------|------|-----------|-------------|------------|--------------|-------------|------|
| blosum | OK | 50 | 81.74 | 100.0% | 1.12 | 2 | 0.0s |
| esm_scan | OK | 50 | 78.04 | 100.0% | 2.00 | 3 | 5.2s |
| proteinmpnn | OK | 50 | 36.34 | 100.0% | 7.60 | 8 | 8.2s |
| dual_b1_b2 | OK | 50 | 38.30 | 100.0% | 7.32 | 8 | 12.1s |


## 상세 메트릭

### blosum

- 전체 생성 변이체: 50
- unique 시퀀스: 50
- BLOSUM score (seed 대비 평균): 81.74
- fixed_positions 보존: 50/50 (위반 0건)
- hamming mean: 1.12, median: 1.0, max: 2
- 실행 시간: 0.0초

### esm_scan

- 전체 생성 변이체: 50
- unique 시퀀스: 50
- BLOSUM score (seed 대비 평균): 78.04
- fixed_positions 보존: 50/50 (위반 0건)
- hamming mean: 2.0, median: 2.0, max: 3
- 실행 시간: 5.15초

### proteinmpnn

- 전체 생성 변이체: 50
- unique 시퀀스: 50
- BLOSUM score (seed 대비 평균): 36.34
- fixed_positions 보존: 50/50 (위반 0건)
- hamming mean: 7.6, median: 8.0, max: 8
- 실행 시간: 8.2초

### dual_b1_b2

- 전체 생성 변이체: 50
- unique 시퀀스: 50
- BLOSUM score (seed 대비 평균): 38.3
- fixed_positions 보존: 50/50 (위반 0건)
- hamming mean: 7.32, median: 7.0, max: 8
- 실행 시간: 12.097초

## 다양성 비교

**unique 시퀀스 수 (다양성) 순위:**

> 동점 시 hamming distance mean(seed 대비 평균 변이 거리) 큰 쪽 우선 — 더 넓은 탐색 공간

1. `proteinmpnn` — 50 unique seqs, hamming mean 7.6
2. `dual_b1_b2` — 50 unique seqs, hamming mean 7.32
3. `esm_scan` — 50 unique seqs, hamming mean 2.0
4. `blosum` — 50 unique seqs, hamming mean 1.12

**hamming distance 분포 (seed 대비 변이 거리):**

| Strategy | mean | median | max |
|----------|------|--------|-----|
| blosum | 1.12 | 1.0 | 2 |
| esm_scan | 2.0 | 2.0 | 3 |
| proteinmpnn | 7.6 | 8.0 | 8 |
| dual_b1_b2 | 7.32 | 7.0 | 8 |

**BLOSUM score (seed 대비, 높을수록 보수적 변이):**

1. `blosum` — BLOSUM mean 81.74
2. `esm_scan` — BLOSUM mean 78.04
3. `dual_b1_b2` — BLOSUM mean 38.3
4. `proteinmpnn` — BLOSUM mean 36.34

## 권고 운영 Strategy

**권고: `blosum`**

선정 기준 (우선순위):

1. fixed_positions 위반 0건 (pharmacophore guard 완전 통과)
2. unique 시퀀스 수 최대 (탐색 공간 다양성)
3. BLOSUM mean 상위 (진화적 타당성)

`blosum` 선정 근거:
- fixed 위반: 0건
- unique 시퀀스: 50
- BLOSUM mean: 81.74
- 실행 시간: 0.0초

### 목적별 권고 (운영 시나리오별)

| 시나리오 | 권고 strategy | 근거 |
|---------|--------------|------|
| 진화적 보수성 (BLOSUM 높음) | `blosum` | BLOSUM mean 81.74 — seed와 유사한 변이, pharmacophore 보존 최강 |
| 탐색 공간 다양성 (hamming 높음) | `proteinmpnn` | hamming mean 7.6 — seed에서 멀리 탐색, 신규 스캐폴드 발견 가능성 높음 |
| GPU/인프라 없는 환경 | `blosum` | 의존성 없음, 실행 시간 5.15초 이하 |
| 생물물리학적 근거 + 다양성 균형 | `esm_scan` | LM zero-shot으로 진화 허용 변이 추출, BLOSUM과 hamming 사이 균형점 |
| 하류 도킹 실험 최대 커버리지 | `dual_b1_b2` | ProteinMPNN(구조 기반) + ESM-Scan(서열 기반) union — 두 방법론의 variant pool 합산 |

> **참고**: 이 권고는 현재 실행 결과의 정량적 지표만 기반으로 합니다.
> GPU 가용성/환경 제약에 따라 일부 strategy가 SKIPPED된 경우 전체 비교가 불완전할 수 있습니다.
> 하류 도킹(Boltz/FlexPepDock) 결과와 교차 검증하여 최종 strategy를 결정하는 것을 권고합니다.

---

*자동 생성: `pipeline_local/scripts/strategy_ab_experiment.py` — 2026-05-19 07:01 UTC*