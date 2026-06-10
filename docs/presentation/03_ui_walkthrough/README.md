# Silo B 대시보드 UI 순차 캡처 보고

브라우저에서 **위→아래로 스크롤**하며 보는 순서와 동일하게, 저장된 HTML 스냅샷을 캡처해 패널별로 설명한 자료입니다.

## 캡처 출처·방법

| 항목 | 내용 |
|------|------|
| **원본 HTML** | `/home/helloworld/Desktop/AI-Scientist_SSTR2_Pipeline_Dashboard.html` (브라우저에서 `localhost:5173/silo-b` 를 저장한 단일 파일; React 렌더 결과가 DOM에 포함됨) |
| **도구** | Playwright (Chromium / 시스템 Chrome 채널) |
| **뷰포트** | 1680×950 px |
| **스크롤** | 820 px씩 아래로 이동하며 **뷰포트 단위 PNG** 저장 (인접 이미지 약 130 px 겹침) |
| **총 페이지 높이** | 약 13 098 px → **17장** |
| **보고서용 후처리** | 저장 PNG는 **최대 폭 900 px**로 리사이즈해 PDF·GitHub 미리보기에서 레이아웃이 깨지지 않게 함 (`docs/reports/resize_report_images.py`) |

수치·수식의 근거는 [`../silo_b_computational_definitions_detailed.md`](../silo_b_computational_definitions_detailed.md), 코드 경로는 [`../silo_b_code_to_ui_pipeline_trace.md`](../silo_b_code_to_ui_pipeline_trace.md)를 참고하면 됩니다.

---

## 스크롤 캡처 갤러리 (순서대로)

아래 이미지는 `assets/scroll_XX_yYYYY.png` 파일명과 동일합니다.

### 1) `scroll_00_y0.png` — 헤더 · 실험 제어 · 파이프라인 상태

- **상단 탭**: Silo A / Silo B / Combined 등 네비게이션. 현재 **Silo B: PyRosetta** 트랙.
- **배지**: `PyRosetta-only`, 사용 LLM 공급자, **Target ΔG** 목표, 아카이브 런 개수 등 요약.
- **Experiment control**: 반복 횟수(Iterations), 후보 수(Candidates), Top-K, **Objective·Validation** 모드, 실행 버튼.
- **Pipeline Status**: 단계별 스텝(예: Step06 PyRosetta)과 소요 시간, **Rosetta 서브스텝**(Prepare → Mutate → Refine → Score → QC Gate → Critic → Reporter)의 완료 여부.
- **Loop Timeline** 상단: 반복 루프 이벤트 로그의 시작 부분.

*데이터는 백엔드 `PIPELINE_STATUS_FILE` JSON(또는 아카이브)에서 로드됩니다.*

---

### 2) `scroll_01_y820.png` — Loop Timeline (연속)

- 반복별 **planner / rosetta / qc / critic / reporter** 이벤트가 시간순으로 펼쳐짐.
- 각 줄은 subprocess·에이전트가 남긴 한 줄 요약(가설, ddG 스니펫, 경로 등).

---

### 3) `scroll_02_y1640.png` — Loop Timeline 하단 · 구조 시각화 상단

- 타임라인 후반(특정 iteration의 refine·score 완료 로그 등).
- **Structure Visualization** 영역이 시작되면 PyMOL/렌더 이미지(Overview, Close-up, Interface, Electrostatics) 썸네일이 나타남.

---

### 4) `scroll_03_y2460.png` — 구조 이미지 · 타임라인 후반

- 렌더 PNG가 채워진 경우 2×2 그리드로 표시.
- 타임라인에서 **특정 후보의 ddG**가 체크 표시와 함께 보일 수 있음.

---

### 5) `scroll_04_y3280.png` — Agent Monitor + Candidate Ranking 상단

- **Agent Monitor**: Planner 가설, QC & Ranker·Critic 등 에이전트 상태.
- **Candidate Ranking** 테이블 상단: Rank, ΔG, Total Score, Clash, Sequence, Result 등.

---

### 6) `scroll_05_y4100.png` — 후보 테이블 · ΔG 분포

- 후보 행 전체와 **재현성(Repro. ΔG)** 열.
- **ΔG Distribution** 히스토그램: 후보 집합의 결합 에너지 분포.

---

### 7) `scroll_06_y4920.png` — Validation · Cluster 요약

- **ValidationPanel**: 선택 후보에 대한 통합 검증 배지(티어링).
- **Cluster** 띠: A–E 클러스터별 후보 수·비율 막대.

---

### 8) `scroll_07_y5740.png` — Cluster 상세 · ADMET 시작

- 선택 후보에 대한 **A–D 기준 체크리스트**(각 조건 충족/미충족).
- **ADMET & Nephrotoxicity** 카드가 시작: Druglikeness 링, MW, 전하 등.

---

### 9) `scroll_08_y6560.png` — Cluster 상세 · ADMET (Druglikeness ~ Amphipathicity)

- **Cluster** 띠·선택 후보의 A–D 조건 체크리스트(이 스트립에 포함되는 경우).
- **ADMET**: **Druglikeness** 4규칙(각 25점), MW, Net charge, HBD/HBA, KD 평균, Amphipathicity.
- **pepADMET** 상단: 이진 독성, 클래스, HC50; `linear graph fallback` 은 SMILES 실패 시 선형 그래프 추론.

---

### 10) `scroll_09_y7380.png` — pepADMET 하단 · PRRT · Pharmacology · BLOSUM62

- **pepADMET** 신경독성 서브타입 등 잔여 필드.
- **Renal Retention Risk (PRRT)**: 양전하 잔기·점수·Moderate/High 경고 문구.
- **Pharmacological Properties** 그리드(GRAVY, Boman, II, pI, MW, ε₂₈₀, N-end rule, 소수성 모멘트, Wimley–White, 전하 pH 7.4/6.5, 프로테아제, 금속, 방사선 분해).
- **BLOSUM62 Mutation Analysis vs SST-14** 표(위치별 치환·점수·보수성).

---

### 11) `scroll_10_y8200.png` — RCSB PDB Match

- 후보별 **PDB 유사 검색** 결과(Checked/Matched/Novel, identity cutoff).
- 행 확장 시 PDB ID, Identity, E-value, Bitscore 테이블.

---

### 12) `scroll_11_y9020.png` — SAR Heatmap · Agent Flow Diagram

- **SAR HEATMAP**: 잔기×위치 빈도, **FWKT** 약물포어 열 강조.
- **Agent Flow Diagram**: Planner → Candidate Gen → Simulation(FlexPepDock) 등 세대/평가 흐름.

---

### 13) `scroll_12_y9840.png` — Sequence Logo · Mutation Analysis

- 후보 정렬 기반 **서열 로고**.
- 기준 서열 대비 **돌연변이 요약**·잔기별 해석.

---

### 14) `scroll_13_y10660.png` — Mutation Analysis 하단 · Position Enrichment

- 잔기 치환 빈도·평균 ΔG 등 **포지션 농축** 표/차트(색: 유리/중간/불리한 ΔG, FWKT 위치 강조).

---

### 15) `scroll_14_y11480.png` — Position Enrichment 하단 · QC Funnel · Convergence · Run Comparison 시작

- **QC Gate Funnel**: RosettaGate 등 게이트별 통과/실패 비율.
- **Convergence Graph**: 반복별 Best ΔG·Top candidates 추이.
- **Run Comparison** 테이블 상단: 아카이브 런 메타데이터.

---

### 16) `scroll_15_y12300.png` — Run Comparison · Risk Matrix

- 과거 런과 **Best ΔG·Trend·Model** 비교.
- **Risk Matrix**: 영향×가능성 격자(정적 시나리오 목록; 실시간 파이프라인 수치와 별개).

---

### 17) `scroll_16_y13120.png` — 페이지 하단

- Run Comparison 테이블 하단 행·**Risk Matrix** 전체·푸터(모니터 버전·Run ID).

---

## 파일 목록

```
assets/
  scroll_00_y0.png
  scroll_01_y820.png
  …
  scroll_16_y13120.png
```

---

## 보고서에 넣을 때 팁

1. **한 장씩 붙이기**: 위 번호 순서대로 넣으면 발표 슬라이드·PDF와 자연스럽게 맞습니다.
2. **겹침**: 인접 이미지는 같은 패널이 반복될 수 있으니, 필요하면 둘 중 한 장만 사용해도 됩니다.
3. **최신 UI**: 이 캡처는 **저장 시점의 HTML** 기준입니다. 라이브 앱에서 다시 저장하면 숫자·테마가 달라질 수 있습니다.

---

*생성: Playwright 자동 캡처 + UI 구조 설명. 원본 HTML 경로는 사용자 Desktop 기준.*
