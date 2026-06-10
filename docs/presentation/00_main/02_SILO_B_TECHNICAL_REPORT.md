# Silo B 기술 패키지 (SILO_B_TECHNICAL_REPORT)

**작성일**: 2026-04-03  
**미팅 액션 A-01~A-10 전문**: [`01_ACTION_ITEMS_RESPONSE_REPORT.md`](01_ACTION_ITEMS_RESPONSE_REPORT.md) — 본 문서에는 링크만 둔다.  
**PDF**: 동일 디렉터리 `SILO_B_TECHNICAL_REPORT.pdf` — `python _md_to_pdf_weasyprint.py --input SILO_B_TECHNICAL_REPORT.md --output SILO_B_TECHNICAL_REPORT.pdf --profile technical`

---

## Silo B 파이프라인·대시보드 기술 요약

## 0. 기존 보고서 맵 및 통합 분석

| 원본 파일 | 역할 | 본 통합본에서의 위치 |
|-----------|------|----------------------|
| `silo_b_dashboard_panels_methodology.md` | 패널별 데이터 출처, Live/Mock, ADMET·Pharma·Cluster 요약, 스크린샷 경로 | Part II §1~4·6 요약 + **부록 A** 전문 |
| `silo_b_code_to_ui_pipeline_trace.md` | FlexPepDock → QC → 상태 JSON → API, Mermaid 다이어그램 | Part II §3·5 + **부록 B** 전문 |
| `silo_b_computational_definitions.md` | 필드별 수식, pepADMET SMILES/폴백, Cluster 코드 주의 | Part II §1·4·5·7 + **부록 C** 전문 |
| `../03_ui_walkthrough/README.md` | 저장 HTML 스크롤 캡처 17장·패널 설명 | Part II §6 + **부록 D** 전문 |

**중복 제거 관점**: 방법론(부록 A)과 계산 정의(부록 C)는 ADMET·pepADMET 설명이 겹친다. 발표 시에는 **§4·5 요약표**만 슬라이드에 올리고, 질의응답 시 **부록 C**(특히 pepADMET·Cluster 관련 절)를 연다.

**의존 자산**: `../03_ui_walkthrough/assets/scroll_*.png`(17장, 폭 리사이즈됨), `../screenshots/*.png`, Desktop 저장 HTML(워크스루 README 경로 참고).

---

## 1. Executive Summary (발표 1장 분량)

1. **Silo B**는 SSTR2 펩타이드 설계를 **PyRosetta FlexPepDock** 기반 **mutate → dock → QC → Critic → Reporter** 루프로 돌리고, 진행 상황과 후보는 **`StatusEmitter` → JSON → `/api/status`** 로 대시보드에 표시한다.
2. **후보 점수의 본체**는 스크립트 `flexpep_dock.py` 가 반환하는 **`ddG`, `total_score`, `clash_score`** 이다. PyRosetta 전용 QC에서는 **상위 k개 선정이 `ddG` 오름차순(`ddg_primary`)** 이다.
3. **GNINA / ECR / Pareto / BO** 는 `extra_scores` 등 **보조 지표**이며, 기본 순위를 바꾸는 것과 동일시하면 안 된다(설정·가용성 의존).
4. **ADMET 패널**은 (1) `admet.py` **규칙 기반** 휴리스틱, (2) **PRRT nephrotox**, (3) 선택적 **pepADMET ML**(`pepadmet` 키)의 **세 층**이다. Druglikeness·MW 등은 pepADMET과 무관한 **순수 서열 휴리스틱**이다.
5. **pepADMET**은 `smiles_converter`로 **이황화 포함 SMILES**를 우선 시도하고, 실패 시 **선형 그래프 폴백**(`linear_sequence_fallback`) — 수치는 나올 수 있으나 **브릿지 토폴로지가 빠질 수 있어** 해석에 주의.
6. **Pharmacology**는 `PharmaProperties` 문헌 기반 13+ 지표; **Cluster A–E**는 `cluster_report.py`의 결정적 규칙(일부 조건은 PyRosetta-only·입력 dict 형태에 민감).
7. **Risk Matrix** 등은 **정적 시나리오**에 가까운 항목이 있어 실시간 수치와 혼동하지 말 것.
8. **UI 순차 캡처** 17장은 저장 HTML 기준이며, 라이브 재캡처 시 수치는 달라질 수 있다.

---

## 2. 페이지·데이터 모드 (요약)

- **컴포넌트 순서**: `SiloBPage.tsx` 기준 PipelineStatus → LoopTimeline → Visualization → AgentMonitor+CandidateTable → DdG 분포 → Validation → Cluster → **ADMET** → **Pharmacology** → RCSB → SAR → AgentFlow → SequenceLogo → Mutation → PositionEnrichment → QC/Convergence → RunComparison → RiskMatrix.
- **Live vs Mock**: `/api/status` 정상 시 실험 상태·후보; 아니면 `mockData.ts`.
- **ADMET/Pharma**: 후보 **서열**만으로 `/api/admet/batch`, `/api/pharmacology/batch` 별도 호출 — 파이프라인 JSON과 **독립**.

---

## 3. 파이프라인 → UI (요약 다이어그램)

아래는 `silo_b_code_to_ui_pipeline_trace.md` 와 동일한 관계를 한눈에 보이게 한 것이다.

```mermaid
flowchart LR
  subgraph R["러너"]
    FP[flexpep_dock.py]
    QC[QCRanker ddG primary]
    EM[StatusEmitter]
  end
  subgraph API["API"]
    ST[/api/status]
    AD[/api/admet/batch]
    PH[/api/pharmacology/batch]
  end
  subgraph UI["Silo B"]
    T[후보 테이블]
    A[ADMETPanel]
    P[PharmacologyPanel]
  end
  FP --> QC --> EM --> ST --> T
  AD --> A
  PH --> P
```

---

## 4. ADMET vs pepADMET (발표에서 자주 나오는 오해)

| 질문 | 답 |
|------|-----|
| Druglikeness 100점이 pepADMET 결과인가? | **아니오** — `compute_admet` 규칙 4개×25점. |
| pepADMET이 꺼져 있으면? | `SKIP_PEPADMET=1` 또는 conda 실패 시 `pepadmet` 키만 비활성/에러. |
| linear fallback이면 독성이 NaN인가? | 보통 **아니오** — 선형 그래프로 MGA는 돌아감; **구조 신뢰도** 이슈. |

---

## 5. 계산·코드 인덱스 (슬라이드용 한 표)

| 블록 | 주 파일 |
|------|---------|
| ΔG·clash·totalScore | `AG_src/scripts/flexpep_dock.py`, `pyrosetta_flow/runner.py` |
| QC 순위 | `AG_src/agents/qc_ranker.py` |
| 상태 JSON | `backend/status_emitter.py` |
| ADMET 휴리스틱·PRRT | `backend/admet.py` |
| pepADMET | `pepadmet_runner.py`, `pepadmet_infer_script.py`, `smiles_converter.py` |
| Pharmacology | `backend/pharmacology.py`, `AG_src/pipeline/pharma_properties.py` |
| Cluster | `pyrosetta_flow/cluster_report.py` |

---

## 6. UI 스크린 캡처 자료 (경로만)

- **연속 스크롤 PNG 17장**: `docs/reports/../03_ui_walkthrough/assets/scroll_00_y0.png` ~ `scroll_16_y13120.png` (저장 폭 약 900px로 리사이즈)
- **설명 텍스트**: 부록 D (`../03_ui_walkthrough/README.md`)

---

## 7. 면책·한계 (권장 발표 멘트)

- ADMET 휴리스틱은 **스크리닝용**이며 IND/임상 등급 예측을 대체하지 않는다.
- pepADMET은 **공개 가중치·로컬 추론**이며, 폴백 시 그래프 토폴로지 한계를 문서화했다.
- Cluster·수렴 지표는 **구현된 임계값·입력 필드**에 묶여 있으며, 과학적 주장은 별도 검증이 필요하다.

---

## 8. 부록 구성·액션 자료 위치

| 구분 | 파일·위치 |
|------|-----------|
| **미팅 A-01~A-10 대응** | **본서 Part I** = `action_response_report.md` (문구는 `meet_log_backup.md` 기준) |
| ADMET 대안·Rosetta 상태 | **부록 E.1, E.2** |
| 차기 문서 작업(A-11~) | `action_response_report.md` §「차기·추가 액션」 |

### 산출물 체크리스트

- [x] Part I 액션 보고 우선 배치 · 번호 정합 (`meet_log_backup.md`)
- [x] 부록 A~D · 부록 E(admet/rosetta)
- [x] PDF 페이지 번호 · 스크린/스크린샷 이미지 폭 조정

---

*아래는 부록. 상대 링크·이미지 경로는 원본 기준.*

---

# 부록 A — 패널·방법론 (원문: silo_b_dashboard_panels_methodology.md)

# Silo B 대시보드 패널별 계산·데이터 출처 상세

**대상**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend` — Silo B (`/silo-b`) 페이지에 배치된 시각화·패널  
**작성 목적**: 데모·보고 시 각 UI 블록이 **무엇을**, **어디서**, **어떤 식으로** 계산·표시하는지 한 문서에서 추적 가능하도록 정리함.

**연관 문서**:
- 파이프라인 코드에서 **연산·모델·상태 파일·API**까지 한 줄로 잇는 추적 → [`silo_b_code_to_ui_pipeline_trace.md`](../01_appendix/silo_b_code_to_ui_pipeline_trace.md).
- **Druglikeness·ADMET·pepADMET·Pharmacology·Cluster** 필드별 **수식·임계값·구현 주의** 상세 → [`silo_b_computational_definitions.md`](../01_appendix/silo_b_computational_definitions.md).
- **저장 HTML 기준 UI 스크롤 캡처 + 패널 설명** 보고 → [`../03_ui_walkthrough/README.md`](../03_ui_walkthrough/README.md) 및 `../03_ui_walkthrough/assets/scroll_*.png`.

---

## 1. 스크린샷·정적 캡처 자료

라이브 브라우저 캡처 대신, 동일 UI를 저장해 둔 자료를 활용한다.

| 구분 | 경로·설명 |
|------|-----------|
| 단일 HTML 덤프 | [`../screenshots/AI-Scientist_SSTR2_Pipeline_Dashboard.html`](../screenshots/AI-Scientist_SSTR2_Pipeline_Dashboard.html) — Vite Silo B 페이지 전체를 저장한 파일(로컬 에셋 링크는 환경에 따라 깨질 수 있음). |
| PNG 모음 | [`../screenshots/`](../screenshots/) — 대표 파일명 아래 표 참고. |

본 문서 삽입 이미지(상대 경로는 **이 MD 파일 기준** `../screenshots/`):

| 패널 영역 | 참고 이미지 파일 |
|-----------|------------------|
| Silo B 전체 레이아웃 | `01_silo_b_full.jpg` |
| 실험 제어 | `02_experiment_control.png`, `03_experiment_control.png` |
| 후보 테이블 | `03_candidate_table.png`, `05_candidate_table.png` |
| 에이전트·후보 요약 | `04_agent_and_candidates.png` |
| ΔG 분포 | `05_ddg_distribution.png`, `06_ddg_distribution.png` |
| Pharmacology | `08_pharmacology.png`, `09_pharmacology.png` |
| SAR 히트맵 | `06_sar_heatmap.png`, `09_sar_heatmap.png` |
| 시퀀스 로고 | `07_sequence_logo.png`, `10_sequence_logo.png` |
| 변이 분석 | `08_mutation_analysis.png`, `11_mutation_analysis.png` |
| Validation | `07_validation.png`, `10_validation.png` |
| QC / 수렴 | `11_qc_gate.png`, `13_qc_convergence.png` |
| Risk matrix | `12_risk_matrix.png`, `14_risk_matrix.png` |
| 수렴 그래프(별도) | `04_convergence.png` |

### 1.1 대표 화면 (이미지)

![Silo B 전체](../screenshots/01_silo_b_full.jpg)

*그림 1. Silo B 대시보드 전체 예시 (`01_silo_b_full.jpg`).*

![Pharmacology 패널 예시](../screenshots/08_pharmacology.png)

*그림 2. Pharmacology 패널 영역 예시 (`08_pharmacology.png`).*

---

## 2. 페이지 구성 순서 (코드 기준)

`SiloBPage.tsx`에서 렌더 순서는 다음과 같다.

1. `PipelineStatus` — 파이프라인 스텝·Rosetta 서브스텝
2. (조건부) `LoopTimeline`
3. (조건부) `VisualizationPanel` — PyMOL 등 이미지
4. `AgentMonitor` + `CandidateTable`
5. `DdGDistribution`
6. `ValidationPanel`
7. `ClusterPanel`
8. **`ADMETPanel`**
9. **`PharmacologyPanel`**
10. `RCSBMatchPanel`
11. `SARHeatmap`
12. `AgentFlowDiagram`
13. `SequenceLogo`
14. `MutationAnalysis`
15. `PositionEnrichment`
16. `QCGateChart` + `ConvergenceGraph`
17. `RunComparisonPanel`
18. `RiskMatrix`
19. (조건부) `MoleculeViewer`

---

## 3. 데이터 공급: Live vs Mock

| 모드 | 조건 | 후보·스텝 출처 |
|------|------|----------------|
| **Live / Archive** | `usePipelineStatus`가 `/api/status`로 읽은 JSON에 `error`가 없고, 스텝이 있거나 아카이브 런을 선택한 경우 | `runs/.../experiment` 상태 또는 `/api/runs/{id}` 아카이브 |
| **Mock** | 위 조건 미충족 | `frontend/src/data/mockData.ts` |

ADMET·Pharmacology는 후보 **서열**이 있으면 각각 `/api/admet/batch`, `/api/pharmacology/batch`를 호출한다(프록시 → FastAPI).

---

## 4. ADMET & Nephrotoxicity 패널

**컴포넌트**: `ADMETPanel.tsx`  
**API**: `POST /api/admet/batch` → `backend/routers/admet.py` → `backend/admet.py`

### 4.1 서열 휴리스틱 ADMET (`compute_admet`)

입력: 한 글자 아미노산 서열(대문자 정규화). **외부 API 없음**, 순수 파이썬.

| 출력 필드 | 계산 요약 |
|-----------|-----------|
| **mw** | 잔기 단위 **모노아이소토픽 질량** 합 + N/C 말단을 위한 물 1분자(`18.01056 Da`). 잔기 테이블은 `backend/admet.py` 상단 `_AA_RESIDUE_WEIGHTS`. |
| **net_charge_ph74** | K/R: +1, D/E: −1, H: +0.1 누적 후, **N말단 +1**, **C말단 −1** 명시 반영(코드 주석상 생리학적 pH에서 상쇄될 수 있으나 스펙대로 항목 포함). |
| **n_hbd** | 측쇄 HBD 개수(`_SIDECHAIN_HBD`) + **잔기 수**(백본 NH 단순화, Pro 예외 미반영). |
| **n_hba** | 측쇄 HBA(`_SIDECHAIN_HBA`) + **잔기 수**(백본 C=O). |
| **hydrophobicity** | **Kyte–Doolittle** 평균. |
| **amphipathicity_index** | 동일 스케일 값들의 **분산**(평균 대비). |
| **druglikeness_score (0–100)** | 펩타이드용 4규칙 각 25점: (1) MW 1200–2000 Da, (2) \|net charge\| ≤ 3, (3) hydrophobicity ∈ [−2, 1], (4) 동일 잔기 3연속 없음. |
| **druglikeness_breakdown** | 규칙별 `passed`, `value`, `range`, `points`. |

### 4.2 PRRT 신장 보유 위험 (`compute_nephrotox_risk`)

| 출력 | 계산 |
|------|------|
| **n_lys, n_arg, n_his** | 서열 내 개수. |
| **cationic_residues** | 위 세 합. |
| **net_charge** | ADMET과 동일한 단순 전하 규칙(단, N/C 말단 ±1 미포함 — ADMET 블록과 숫자가 다를 수 있음). |
| **renal_risk_score** | `min(100, (n_lys + n_arg) × 20 + max(0, net_charge) × 15)` (소수 반올림). |
| **risk_level** | &lt;30 Low, 30–60 Moderate, &gt;60 High. |
| **warning** | Moderate/High일 때 문구 생성. |

### 4.3 pepADMET 독성 (ML, 선택)

`merge_pepadmet_into_admet_results`가 `pyrosetta_flow.pepadmet_runner.predict_toxicity_batch` 결과를 **`pepadmet`** 키로 병합.

- **환경**: `conda` 환경 `pepadmet`, 로컬 클론 `local_models/pepadmet/repo`(또는 `PEPADMET_REPO`).
- **추론**: `pepadmet_infer_script.py` — RDKit 그래프 + `calculate_descriptors` + `MGA` 모델(`toxicity_early_stop.pth`).
- **1차 SMILES**: `smiles_converter.sequence_to_smiles`가 선형 `MolFromSequence` 후 **Cys 쌍 SG–SG 이황화**를 붙여 SMILES를 만들도록 설계됨(SST-14 유사체 전제).
- **폴백 (`graph_note: linear_sequence_fallback`)**: 1차 SMILES가 `MolFromSmiles`/그래프 단계에서 실패할 때만 **`MolFromSequence` 선형 그래프**로 재시도. 이 경로에서는 **코드상 이황화 결합이 그래프에 명시되지 않음** → 수치는 나오나(모델 forward는 실행) **브릿지 포함 구조와 달라 해석에 주의**. 상세 표·오해 방지 문단은 [`silo_b_computational_definitions.md`](../01_appendix/silo_b_computational_definitions.md) **§C.1** 참고.
- **비활성**: 환경변수 `SKIP_PEPADMET=1`이면 병합 생략.

---

## 5. Pharmacology 패널

**컴포넌트**: `PharmacologyPanel.tsx`  
**API**: `POST /api/pharmacology/batch` → `backend/pharmacology.py` → 주로 `AG_src.pipeline.pharma_properties.PharmaProperties`

### 5.1 이황화 결합 가정

짝수 개 Cys가 있으면 **순차 짝지음**(첫↔끝 …)으로 이황화에 참여하는 Cys 인덱스를 잡고, **등전점·pH 전하 프로파일**에서 해당 Cys는 이온화에서 제외.

### 5.2 필드별 요약 (정상 시 `PharmaProperties` 사용)

| 필드 | 의미·출처 |
|------|-----------|
| **gravy** | Grand Average of Hydropathy (Kyte–Doolittle 평균). |
| **boman_index** | Boman — 단백질 결합 경향(잔기별 Radzicka–Wolfenden 유사 기여 평균). |
| **instability_index** | Guruprasad et al. 불안정성 지수; &lt;40 은 `stable` 분류. |
| **aliphatic_index** | Aliphatic index (A,V,I,L 비율 기반 경험식). |
| **isoelectric_point** | Bjellqvist 등 pKa 기반 이분 탐색. |
| **extinction_coefficient** | ε₂₈₀; Trp/Tyr 개수 및 이황화 수에 따른 보정(`PharmaProperties` 또는 단순식 폴백). |
| **n_end_rule** | N-end rule 반감기 추정. |
| **hydrophobic_moment** | 소수성 모멘트(윈도우). |
| **wimley_white** | Wimley–White 합성 막 친화도. |
| **charge_ph_profile** | 여러 pH에서 순전하(Henderson–Hasselbalch, SS 제외 반영). |
| **molecular_weight** | 평균/모노아이소토픽 MW, SS 개수만큼 H₂ 제거 보정. |
| **protease_sites** | 효소 절단 위치 후보 집계. |
| **blosum62** | 참조 서열(기본 SST-14) 대비 BLOSUM62 합산·위치별. |
| **metal_coordination** | 방사성 금속 킬레이션에 유리한 잔기(예: D/E/H 등) 평가. |
| **radiolysis_susceptibility** | 방사선 분해에 민감한 잔기 경향. |

`PharmaProperties` import 실패 시 일부는 0 또는 `error` 반환(폴백 테이블 경로).

---

## 6. Cluster 패널 (A–E)

**컴포넌트**: `ClusterPanel.tsx`  
**API**: `POST /api/cluster/classify` → `pyrosetta_flow/cluster_report.py::batch_classify`

각 후보는 **하나의 클러스터**만 부여(우선순위 A &gt; B &gt; C &gt; D &gt; E).

| 클러스터 | 조건(모두 만족 시) |
|----------|---------------------|
| **A** High Affinity Core | ΔG ≤ −8, clash ≤ 5, (pLDDT 있으면 ≥75, 없으면 해당 조건 생략), FWKT pharmacophore pass |
| **B** Selectivity | selectivity_margin ≥ 3, ΔG &lt; −5 |
| **C** Stability | instability_index &lt; 30, BLOSUM 합 ≥ 0, protease 총 ≤ SST-14 기준(9) 이하 |
| **D** Radiochemistry | GRAVY ∈ [−1, 0.5], \|net_charge_ph74\| ≤ 1, metal `n_strong` ≥ 1 |
| **E** | 위 어느 것도 미충족 |

후보 dict에 `instability_index`, `gravy`, `net_charge_ph74` 등은 파이프라인이 **pharmacology·구조 규칙**과 함께 채운 필드를 기대한다. UI만으로는 숫자를 다시 계산하지 않는다.

---

## 7. 기타 Silo B 패널 (요약)

| 패널 | 데이터 소스 / 계산 |
|------|---------------------|
| **PipelineStatus** | 상태 JSON의 `steps`, `rosetta_substeps` |
| **CandidateTable** | 후보 `ddG`, `clash`, rank 등 상태 파일 |
| **DdGDistribution** | 후보 ΔG 히스토그램 |
| **ValidationPanel** | 선택 후보에 대해 `/api/validate/selected` 등(백엔드 검증 라우터) |
| **RCSBMatchPanel** | `/api/rcsb` 계열 — 유사 펩타이드 검색 |
| **SARHeatmap** | 후보별 잔기·위치 스코어 매트릭스 |
| **SequenceLogo** | 정렬된 서열 로고 |
| **MutationAnalysis** | 기준 대비 돌연변이 요약 |
| **PositionEnrichment** | 위치별 잔기 빈도 |
| **QCGateChart** | QC 게이트 통과/실패 집계 |
| **ConvergenceGraph** | 반복별 수렴 지표 |
| **RunComparisonPanel** | 아카이브 런 메타 비교 |
| **RiskMatrix** | 정적/설정 기반 리스크 표시(코드 확인 필요 시 `RiskMatrix.tsx` 참고) |
| **MoleculeViewer** | `/api/structures/...` PDB 로드 |

---

## 8. 버전·추적성 참고

| 항목 | 위치 |
|------|------|
| ADMET 휴리스틱 | `repos/ai4sci-kaeri/backend/admet.py` |
| ADMET API + pepADMET 병합 | `repos/ai4sci-kaeri/backend/routers/admet.py` |
| Pharmacology | `repos/ai4sci-kaeri/backend/pharmacology.py`, `AG_src/pipeline/pharma_properties.py` |
| 클러스터 | `repos/ai4sci-kaeri/pyrosetta_flow/cluster_report.py` |
| pepADMET subprocess | `repos/ai4sci-kaeri/pyrosetta_flow/pepadmet_runner.py`, `pepadmet_infer_script.py` |
| 프론트 Silo B | `repos/ai4sci-kaeri/frontend/src/pages/SiloBPage.tsx` |

---

## 9. 보고서 활용 시 권장 문구

- 본 대시보드의 **ADMET 휴리스틱**은 **빠른 스크리닝용 규칙 기반 추정**이며, **IND 수준 ADMET 예측을 대체하지 않는다.**
- **pepADMET** 독성은 **공개 모델·로컬 추론**이며, 선형 그래프 폴백 시 `graph_note`로 표시된다.
- **Pharmacology** 수치는 `PharmaProperties` 구현·문헌과 일치하도록 유지하며, 환경 미설치 시 폴백·제한이 있을 수 있다.

---

*문서 생성: Silo B UI·백엔드 소스 트레이스 기준. 스크린은 `../screenshots/*.png` 및 저장 HTML을 캡처 대체 자료로 사용. 배포·PDF용으로 PNG는 **최대 폭 900 px**로 리사이즈할 수 있음 (`docs/reports/resize_report_images.py`).*

---

# 부록 B — 코드→UI 추적 (원문: silo_b_code_to_ui_pipeline_trace.md)

# Silo B: 코드 연산 경로 → 대시보드 집계 (추적성)

**목적**: 실제 소스에서 **어떤 연산·모델·서브프로세스**가 돌고, 그 결과가 **어디에 기록되며**, **UI에 어떻게 반영**되는지 한 흐름으로 설명한다.  
**필드별 수식·임계값·ML 헤드 정의**는 [`silo_b_computational_definitions.md`](../01_appendix/silo_b_computational_definitions.md)를 본문으로 삼는다. 패널 개요·스크린 참고는 [`silo_b_dashboard_panels_methodology.md`](../01_appendix/silo_b_dashboard_panels_methodology.md).

**코드 루트(이 문서 기준)**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`

---

## 1. 다이어그램 (세분화)

### 1.1 한 장 요약 (런너 vs REST vs UI)

```mermaid
flowchart LR
  subgraph runner["pyrosetta_flow/runner.py"]
    FP["flexpep_dock.py\n(PyRosetta subprocess)"]
    CR[CandidateResult\nddg/total_score/clash]
    QC[QCRankerAgent\ngates + ddg_primary]
    ALT["GNINA / ECR / Pareto / BO\n(선택, extra_scores)"]
    PH["PharmaProperties.calculate_all"]
    CL["cluster_report.batch_classify"]
    EM[StatusEmitter.set_candidates]
  end
  subgraph api["FastAPI backend"]
    ST["/api/status ← PIPELINE_STATUS_FILE"]
    AD["/api/admet/batch"]
    PHAPI["/api/pharmacology/batch"]
  end
  subgraph ui["frontend Silo B"]
    TB[CandidateTable 등]
    ADUI[ADMETPanel]
    PHUI[PharmacologyPanel]
  end
  FP --> CR --> QC --> EM
  CR --> ALT
  PH --> CL --> EM
  EM --> ST --> TB
  AD --> ADUI
  PHAPI --> PHUI
```

### 1.2 단일 iteration — PyRosetta 후보가 상태 JSON까지 가는 순서

```mermaid
flowchart TD
  M[Mutate 후보 서열 생성] --> D[_dock_one: flexpep_dock.py]
  D --> R[CandidateResult JSON 파싱\nddg, total_score, clash_score]
  R --> QC[QCRanker: Rosetta 게이트 + top_k by ddG]
  QC --> E1[_emit_candidates → set_candidates\n1차 테이블]
  E1 --> ALT[_apply_alternative_scoring\nGNINA→ECR→Pareto→BO]
  ALT --> MAN[iteration_manifest 후보 dict\n+ pharma enrich]
  MAN --> CLU[batch_classify A–E]
  CLU --> E2[set_candidates enriched\nmw, cluster, …]
  E2 --> JSON[PIPELINE_STATUS_FILE / archive]
```

### 1.3 ADMET 패널 데이터 계층 (서열 → 휴리스틱 → 선택 ML)

```mermaid
flowchart TD
  SEQ[후보 서열 문자열] --> AD[compute_admet\nMW, charge, HBD/HBA, KD, variance]
  SEQ --> NEP[compute_nephrotox_risk\nPRRT renal score]
  AD --> MERGE[merge_pepadmet_into_admet_results]
  NEP --> MERGE
  MERGE --> SKIP{SKIP_PEPADMET?}
  SKIP -->|no| SUB[conda pepadmet env\npepadmet_infer_script.py\nMGA + RDKit graph]
  SKIP -->|yes| APIR[results 그대로]
  SUB --> APIR[pepadmet 키 병합]
  APIR --> UI[ADMETPanel]
```

### 1.4 Pharmacology 패널 (단일 코드 경로)

```mermaid
flowchart TD
  SEQ[서열 + optional reference] --> PP[PharmaProperties\n13+ literature methods]
  PP --> OUT[gravy, boman, II, pI, MW, ε280, …\nprotease, blosum, metal, radiolysis]
  OUT --> UI[PharmacologyPanel]
```

### 1.5 Cluster 판정 입력 (API 또는 파이프라인)

```mermaid
flowchart LR
  D["ddG, clash\n(구조 파이프라인)"] --> C[classify_cluster]
  P["pharma 필드\ngravy, net_charge_ph74, …"] --> C
  S["selectivity_margin\n(선택)"] --> C
  PL[pLDDT 선택] --> C
  C --> L["A–E + criteria_met"]
```

---

## 2. 구조·도킹 파이프라인 (PyRosetta agentic mutdock)

### 2.1 진입점

- **`pyrosetta_flow/runner.py`** — `run_pyrosetta_agentic_mutdock_flow(config)`
- Baseline·각 iteration에서 **`AG_src/scripts/flexpep_dock.py`** 를 `conda` 서브프로세스로 호출 (`_run_script`).
- 변이 후보당 도킹은 내부 함수 **`_dock_one`** 에서 동일 스크립트를 호출해 PDB와 JSON 마지막 줄을 파싱한다.

### 2.2 FlexPepDock 스크립트가 내는 값 (물리 연산의 핵심)

- **스크립트**: `AG_src/scripts/flexpep_dock.py`
- **역할**: PyRosetta 초기화 후 FlexPepDock 계열 refinement, InterfaceAnalyzer 등으로 **인터페이스 ΔΔG·에너지·클래시**를 계산하고 **stdout 마지막 줄만 JSON**으로 낸다.
- **`CandidateResult`에 매핑되는 필드** (`runner._dock_one`):
  - `ddg` ← `result["ddg"]`
  - `total_score` ← `result["total_score"]`
  - `clash_score` ← `result["clash_score"]`

이 세 값이 이후 QC·표시의 **1차 물리 스코어**이다.

### 2.3 QC & Ranker (게이트 + 상위 후보 선정)

- **`AG_src/agents/qc_ranker.py`** — `QCRankerAgent`
- PyRosetta 전용 가중치: **`PYROSETTA_ONLY_WEIGHTS`** (`plddt`/`dock` 등은 0에 가깝게 두는 용도)이나, 실제 **상위 k개 선정**은 `thresholds["ranking_mode"] == "ddg_primary"`일 때 **`get_top_by_ddg`** — 즉 **`ddg` 오름차순(더 음수일수록 우선)** 이다 (`runner.py`에서 해당 모드로 호출).
- **`runner._candidate_to_qc`**: PyRosetta-only 모드에서는 `plddt`·`dock_score`·`lddt`를 **0으로 고정**하고, `ddg`·`clash_count`(정수화된 clash)만 실값으로 넘긴다.
- **게이트** (`runner` 내 `thresholds`): `plddt` / `docking` / `selectivity` 게이트는 **OFF**, **`rosetta` 게이트만 ON** (`ddg` 상한, clash 상한 등은 `FlowConfig`와 연동).

### 2.4 첫 번째 후보 테이블 푸시 (iteration 중)

- **`runner._emit_candidates`** → **`StatusEmitter.set_candidates`**
- 각 행 예: `ddG`, `totalScore`, `clashScore`, **`finalScore` = `-ddg` (표시용 단순 변환), `result` PASS/FAIL, `failReason` 등.
- **상태 파일**: `backend/status_emitter.py` — 기본 `PIPELINE_STATUS_FILE`(환경변수로 변경 가능)에 JSON 기록 → **`GET /api/status`** 가 프론트에 제공.

### 2.5 대안 스코어링 체인 (같은 run 내, 후처리·부가 지표)

**함수**: `runner._apply_alternative_scoring` (iteration reporter 단계 직전에 `candidates`에 in-place 반영)

| 순서 | 내용 | 모델/라이브러리 | 산출물 |
|------|------|-----------------|--------|
| 1 | GNINA rescoring | `pyrosetta_flow/gnina_rescoring.py` (바이너리 없으면 dry-run) | `extra_scores`에 CNN/Vina 유사 필드 |
| 2 | ECR consensus | `exponential_rank_consensus` — `ddg`와 GNINA 스코어들의 순위 합성 | `ecr_score` |
| 3 | Pareto | `pyrosetta_flow/pareto_ranking.py` — pymoo NSGA-II, 목표 최소화: ddG, −stability, −druggability, −diversity 등 | `pareto_rank`, `crowding_distance` |
| 4 | BO | `BayesianPeptideOptimizer` (선택) | 다음 iteration 힌트(부수 효과 위주) |

**주의**: 위 항목은 **`CandidateResult.extra_scores`** 및 로그·매니페스트에 남고, **기본 QC top-k 선정은 여전히 ddG 기준**이다. Pareto/ECR은 **다목적·보조 분석**에 가깝다.

### 2.6 Pharmacology·클러스터·“대시보드 enrich” 재푸시

같은 iteration의 **reporter/manifest** 구간에서:

1. **`PharmaProperties.calculate_all(seq)`** (`AG_src/pipeline/pharma_properties.py`)  
   - 서열 기반 물리·화학 휴리스틱(GRAVY, 불안정성, 전하, BLOSUM62, 방사선 분해 경향 등). 이황화 Cys 짝은 코드에 명시된 규칙으로 추정.
2. **`cluster_report.batch_classify`** (`pyrosetta_flow/cluster_report.py`)  
   - `ddG`, `clash`, pharma 필드, FWKT 규칙 등으로 **A–E 단일 클러스터** 부여.
3. **`emitter.set_candidates(enriched_entries)`**  
   - 후보 행에 `mw`, `instability_index`, `radiolysis_score`, `cluster` 등을 **추가**해 다시 기록 (`runner.py` “dashboard-enrich” 블록).

따라서 **같은 Silo B 후보 테이블**이 iteration 후반에는 **PyRosetta 스코어 + pharma + cluster**가 합쳐진 형태로 갱신될 수 있다.

### 2.7 RCSB 유사도 (선택)

- **`_rcsb_check_candidates`**: 선택된 서열에 대해 PDB 검색(네트워크·설정 의존).  
- **`iteration_manifest.json`** 의 `rcsb_hits` 등으로 남고, UI **`RCSBMatchPanel`** 과 연결.

---

## 3. ADMET·Pharmacology API 패널 (서열 기반, 상태 파일과 독립 호출)

프론트는 후보 **서열 문자열**을 알면 **파이프라인 JSON과 별도로** API를 호출한다.

| 엔드포인트 | 백엔드 | 핵심 연산 |
|------------|--------|-----------|
| `POST /api/admet/batch` | `backend/routers/admet.py` | `compute_admet_full` → 규칙 기반 ADMET + nephrotox (`backend/admet.py`) 후 **`merge_pepadmet_into_admet_results`** |
| pepADMET | `pyrosetta_flow/pepadmet_runner.py` | 서브프로세스로 `pepadmet_infer_script.py` — RDKit 그래프 + 학습된 독성 헤드(`toxicity_early_stop.pth` 등). `SKIP_PEPADMET=1` 이면 생략 |
| `POST /api/pharmacology/batch` | `backend/pharmacology.py` | **`PharmaProperties`** 위임(동일 물리·화학 계산군) |

UI **`ADMETPanel`**, **`PharmacologyPanel`** 은 이 응답을 그대로 표시한다.  
→ **파이프라인의 `pharma` enrich과 숫자 체계가 같도록** 설계되어 있으나, ADMET 블록의 단순 전하 규칙은 `compute_admet` 주석대로 **PharmaProperties의 HH 기반 전하와 완전히 동일하지 않을 수 있음**(방법론 문서 참고).

---

## 4. 클러스터 패널 (HTTP 경로)

- **`POST /api/cluster/classify`** — `backend/routers/cluster.py` → `pyrosetta_flow/cluster_report.batch_classify`
- 입력은 후보별 dict( `ddG`, `clash_score`, pharma 서브필드 등).  
- **런타임 파이프라인**이 이미 클러스터를 후보에 붙인 경우와, **UI가 따로 분류 API를 부르는 경우**를 구분해 보면, 둘 다 **동일 `batch_classify` 로직**을 사용한다.

---

## 5. UI에서 “데모/정적”에 가까운 부분

- **`RiskMatrix`**: `frontend/src/data/mockData.ts`의 **`RISK_ITEMS`** 등 정적/설정 데이터에 의존하는 영역이 있어 **실시간 파이프라인 수치와 직접 연동되지 않을 수 있음** (`RiskMatrix.tsx` 참고).

---

## 6. 한 페이지 질의응답 (무엇이 무엇인가)

| 질문 | 답 (코드 기준) |
|------|----------------|
| ΔG / totalScore / clash는 어디서 오나? | `flexpep_dock.py` PyRosetta subprocess → `CandidateResult` → `StatusEmitter` 후보 목록 |
| 순위는 무엇으로 정해지나? | QC 단계에서 **`ranking_mode: ddg_primary`** 이면 **`ddg` 오름차순** top-k |
| `finalScore` 컬럼은? | 표시상 **`-ddg`** 로 많이 세팅 (`_emit_candidates` / dashboard-enrich) |
| GNINA/Pareto는 순위를 바꾸나? | 기본 top-k 경로의 **직접 대체가 아니라** `extra_scores`·분석용; 최종 테이블 enrich는 ddG·pharma·cluster 중심 |
| ADMET 숫자는 도킹과 같은가? | **아니오** — 별도 `compute_admet` + 선택적 pepADMET ML |
| Pharmacology 패널과 파이프라인 pharma는? | 같은 **`PharmaProperties`** 계열을 쓰도록 맞춤 (`backend/pharmacology.py`) |

---

## 7. 주요 파일 인덱스

| 역할 | 경로 |
|------|------|
| 러너·도킹·QC·enrich | `pyrosetta_flow/runner.py` |
| FlexPepDock CLI | `AG_src/scripts/flexpep_dock.py` |
| QC 게이트·(가중)랭킹 | `AG_src/agents/qc_ranker.py` |
| GNINA/ECR | `pyrosetta_flow/gnina_rescoring.py`, `runner._apply_alternative_scoring` |
| Pareto | `pyrosetta_flow/pareto_ranking.py` |
| Pharma 계산 | `AG_src/pipeline/pharma_properties.py`, `backend/pharmacology.py` |
| 클러스터 | `pyrosetta_flow/cluster_report.py` |
| 상태 JSON | `backend/status_emitter.py` |
| ADMET·pepADMET 병합 | `backend/admet.py`, `backend/routers/admet.py` |
| pepADMET 추론 | `pyrosetta_flow/pepadmet_runner.py`, `pepadmet_infer_script.py` |
| Silo B 페이지 | `frontend/src/pages/SiloBPage.tsx` |

---

*본 문서는 소스 트레이스 기준이며, 설정(`FlowConfig`, 환경변수, conda 가용성)에 따라 일부 분기(GNINA dry-run, pepADMET skip 등)가 달라질 수 있다.*

---

# 부록 C — 계산 정의 상세 (원문: silo_b_computational_definitions.md)

# Silo B 계산 정의 상세 보고 (ADMET · pepADMET · Pharmacology · Cluster)

**목적**: 대시보드에 표시되는 수치·라벨이 **소스 코드에서 어떤 식으로 정의·계산**되는지 필드 단위로 기술한다.  
**구현 기준 경로**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`  
**연관 문서**: 경로 다이어그램은 [`silo_b_code_to_ui_pipeline_trace.md`](../01_appendix/silo_b_code_to_ui_pipeline_trace.md), 패널 개요는 [`silo_b_dashboard_panels_methodology.md`](../01_appendix/silo_b_dashboard_panels_methodology.md).

---

## A. ADMET 패널 (휴리스틱, 규칙 기반)

**엔드포인트**: `POST /api/admet/batch` → `backend/admet.py` 의 `compute_admet` + `compute_admet_full`, 이후 `merge_pepadmet_into_admet_results`.

**공통**: 입력 서열은 대문자·공백 제거. **외부 네트워크 API 없음** (pepADMET 제외).

### A.1 Molecular Weight (`admet.mw`)

- **정의**: 각 잔기 **잔기 질량(펩타이드 결합으로 물 1분자 제거된 형태)** 의 합 + **자유 N/C 말단 보정으로 물 1분자** (`18.01056 Da`) 가산.
- **코드**: `backend/admet.py` — `_AA_RESIDUE_WEIGHTS`, `_WATER_MW`.

### A.2 Net Charge pH 7.4 (`admet.net_charge_ph74`)

- **정의 (단순 카운트 규칙)**:
  - 측쇄: K, R 각 +1; D, E 각 −1; H는 **+0.1** (고정 분획 근사).
  - 명시적으로 **N말단 +1**, **C말단 −1** 를 더함 (`compute_admet` 주석: 생리학적 pH에서 상쇄될 수 있으나 스펙상 포함).
- **주의**: Pharmacology의 Henderson–Hasselbalch 기반 전하(`charge_at_ph74`)와 **숫자가 다를 수 있음** (아래 H절 참고).

### A.3 H-bond Donors / Acceptors (`admet.n_hbd`, `admet.n_hba`)

- **n_hbd**: 측쇄 HBD 개수 테이블(`_SIDECHAIN_HBD`) 합 + **잔기 수**(백본 NH를 잔기마다 1개로 단순 가산; Pro 예외 미반영).
- **n_hba**: 측쇄 HBA(`_SIDECHAIN_HBA`) 합 + **잔기 수**(백본 C=O).

### A.4 Hydrophobicity (`admet.hydrophobicity`)

- **정의**: **Kyte–Doolittle** 값의 산술 평균 (`_KD_HYDROPATHY`).

### A.5 Amphipathicity Index (`admet.amphipathicity_index`)

- **정의**: 동일 서열에 대해 KD 스케일 값들의 **분산**(코드상 `mean_kd = hydrophobicity` 로 두고 `(v - mean_kd)²` 평균).  
- UI 문구 “KD hydropathy variance”와 대응.

### A.6 Druglikeness Score 0–100 (`admet.druglikeness_score`, `druglikeness_breakdown`)

**총점 = 네 규칙 각 최대 25점 합** (`backend/admet.py`).

| 규칙 키 | 조건 (통과 시 +25) | 비고 |
|--------|---------------------|------|
| `mw_range` | `1200 ≤ mw ≤ 2000` (Da) | 펩타이드 스크리닝용 고정 구간 |
| `charge` | `abs(net_charge) ≤ 3` | A.2의 단순 전하 |
| `hydrophobicity` | `-2 ≤ hydrophobicity ≤ 1` | KD 평균 |
| `no_repeats` | 동일 잔기가 **연속 3개 이상** 없음 (`re.search(r"(.)\1{2,}", seq)` 가 없을 것) |

- **라벨**: 보통 100/100이면 UI에 “DRUG-LIKE” 등으로 매핑(프론트 표시 로직은 컴포넌트 쪽).

---

## B. PRRT Renal Retention Risk (`nephrotox`)

**함수**: `compute_nephrotox_risk` (`backend/admet.py`).

| 필드 | 계산 |
|------|------|
| `n_lys`, `n_arg`, `n_his` | 서열 내 개수 |
| `cationic_residues` | 위 세 합 |
| `net_charge` | K/R ±1, D/E −1, H +0.1 누적 (**N/C 말단 ±1 없음** — ADMET `net_charge_ph74` 와 다를 수 있음) |
| `renal_risk_score` | `min(100, round((n_lys + n_arg) * 20 + max(0, net_charge) * 15, 1))` |
| `risk_level` | &lt;30 Low, 30–60 Moderate, &gt;60 High |
| `warning` | Moderate/High 시 생성 문자열 |

---

## C. pepADMET 독성 (ML, 서브프로세스)

**병합**: `merge_pepadmet_into_admet_results` → `pyrosetta_flow/pepadmet_runner.predict_toxicity_batch`  
**추론 스크립트**: `pyrosetta_flow/pepadmet_infer_script.py` (conda 환경 `pepadmet`).

### C.1 입력·그래프 (SMILES 경로 vs 선형 폴백)

**호출 체인**: `pepadmet_runner.predict_toxicity_batch` → conda로 `pepadmet_infer_script.py` 실행. 입력 JSON에는 `sequence`와 `smiles`가 들어가며, `smiles`는 기본적으로 **`pyrosetta_flow/smiles_converter.sequence_to_smiles(sequence)`** 로 생성된다.

#### C.1.1 SMILES 생성 쪽 — 이황화를 **반영하려는** 경로 (`smiles_converter.py`)

- `Chem.MolFromSequence(seq)` 로 선형 펩타이드를 만든 뒤, **기본값**으로 **첫 Cys ↔ 마지막 Cys**(1-indexed 위치)의 **SG–SG 이황화 결합**을 RWMol로 추가하고 `MolToSmiles` 한다.
- SS 형성이 실패하면(산itize 예외 등) **선형 분자**로 되돌려 SMILES를 낸다.
- **요지**: pepADMET에 넘기는 1차 SMILES는 **가능하면 브릿지가 포함된** 형태를 목표로 한다. “시스테인이 있으면 pepADMET이 아예 동작하지 않는다”가 아니다.

#### C.1.2 추론 스크립트 쪽 — 그래프 빌드 순서 (`pepadmet_infer_script.py`)

1. **`smiles_to_graph(smiles)`**: `MolFromSmiles(smiles)` 성공 시 → `graph_from_mol` 로 DGL 그래프.
2. **그래프가 `None`이면** `graph_from_sequence_linear(seq)` 호출:
   - **`Chem.MolFromSequence(seq)` 만** 사용 (여기서는 **이황화 결합을 추가하지 않음**).
   - 성공 시 `graph_note = "linear_sequence_fallback"` 이 결과에 붙는다.

#### C.1.3 `linear_sequence_fallback` 이 뜰 때의 의미 (Cys·SST-14 맥락)

| 구분 | 설명 |
|------|------|
| **트리거** | 1차 SMILES가 `MolFromSmiles`에서 깨지거나 그래프 생성 실패 — 주석상 **사이클릭/이황화 SMILES가 RDKit 버전·환경에 따라 파싱 실패**하는 경우를 염두에 둠. |
| **계산 자체** | 폴백이어도 `available: True`이면 **MGA forward는 실행**된다. “독성 예측이 완전히 스킵된다”는 뜻이 아니다. |
| **토폴로지** | 폴백 그래프는 **선형 펩타이드**에 가깝고, **의도한 Cys3–Cys14 이황화 브릿지가 그래프에 반영되지 않을 수 있다.** 모델 입력 분포와 어긋나면 수치·해석 신뢰도가 떨어질 수 있다. |
| **UI 배지** | “SMILES round-trip failed” 류 문구와 함께, **근거 구조가 선형 대체**임을 사용자에게 알리는 용도. |

#### C.1.4 ADMET 휴리스틱(`admet.py`)과의 관계

- **Druglikeness·MW·KD 등**은 **서열 규칙**만 쓰므로 SMILES/pepADMET 그래프와 독립이다.
- **pepADMET**만 그래프 토폴로지에 의존하므로, **폴백 시 불일치**가 생기면 “ADMET 카드는 정상인데 pepADMET만 폴백 배지” 같은 조합이 나올 수 있다.

### C.2 모델

- **아키텍처**: `MGA` (RGCN + descriptor branch), 가중치 `model/toxicity_early_stop.pth`.
- **Descriptor**: `calculate_descriptors` → **2133차원** (부족/초과 시 패딩·절단).
- **태스크** (출력 헤드):
  - `task_0`: 이진 독성 로짓 → **sigmoid** → `binary_toxicity` ∈ (0,1); `is_toxic = (bp > 0.5)`.
  - `task_1`: 독성 유형 **softmax** → `TYPE_NAMES` 중 argmax (`toxicity_type`, `toxicity_type_confidence`).
  - `task_2`: 신경독성 서브타입 softmax → `NEURO_NAMES` (`neurotoxicity_type`, `neurotoxicity_confidence`).
  - `task_3`: **회귀** 스칼라 `hc50` (스크립트상 변수명; UI “HC50” 등과 연결).

### C.3 비활성

- 환경변수 **`SKIP_PEPADMET=1`**: 병합 생략.
- repo/conda 실패 시 `pepadmet.available: false` + `error` 문자열.

---

## D. Pharmacological Properties (13+ 방법, 서열 기반)

**엔드포인트**: `POST /api/pharmacology/batch` → `backend/pharmacology.py` → **`AG_src/pipeline/pharma_properties.PharmaProperties`** (가능 시; 실패 시 폴백).

**이황화(Cys)**: 짝수 개 Cys면 **순차 짝지음**(첫↔끝 …). SST-14에서는 0-based index 2·13 등 → **등전점·전하 프로파일에서 해당 Cys는 이온화 제외**.

아래 표는 **정상적으로 PharmaProperties가 로드될 때**의 정의이다.

| UI / 필드 | 정의·출처 (요약) |
|-----------|------------------|
| **GRAVY** | Kyte–Doolittle 평균: `sum(KD)/n` (`pharma_properties.calculate_gravy`). |
| **Boman Index** | Radzicka–Wolfenden 친수성 값 평균; 문헌상 &gt;2.48이면 단백질 결합 경향 높음 (`calculate_boman_index`). |
| **Instability Index** | Guruprasad et al. DIWV: 인접 이펩티드에 가중치 합 × `10/n` (`calculate_instability_index`). **&lt;40 → stable** (UI·`instability_classification`). |
| **Aliphatic Index** | Ikai: A,V,I,L 비율 기반 `x_a + 2.9*x_v + 3.9*(x_i+x_l)` (`calculate_aliphatic_index`). |
| **pI** | Lehninger 계열 pKa로 **순전하=0**이 되는 pH 이분 탐색; SS 결합 Cys는 제외 (`calculate_pi`). |
| **Molecular Weight** | 잔기 평균 질량 합 − (n−1)×H₂O − n_SS×2.016 등 (`calculate_mw`). UI: average / monoisotopic. |
| **Extinction ε₂₈₀** | Trp/Tyr 및 이황화 보정 (`calculate_extinction_coefficient`); SS/환원 형 둘 다 반환. |
| **N-end Rule** | N말단 잔기별 반감기 테이블(`NEND_HALFLIFE`) (`calculate_nend_rule_halflife`). |
| **Hydrophobic Moment** | Eisenberg 스케일 + 각도(기본 100°) 슬라이딩 윈도우에서 최대 모멘트 (`calculate_hydrophobic_moment`). |
| **Wimley–White** | 잔기별 water→interface ΔG 합·평균 (`calculate_wimley_white`); 총합 부호로 membrane/aqueous 해석. |
| **Charge pH 7.4 vs 6.5** | `_charge_at_ph` (Henderson–Hasselbalch, SS Cys 제외). **Tumor selectivity** = `charge_at_ph65 - charge_at_ph74` (`charge_ph_profile`). |
| **Protease sites** | 키모트립신/트립신/NEP/DPP-IV 규칙 + **pepsin**은 `pharmacology.protease_cleavage_sites` 전용 규칙. `total_sites`는 열거 규칙 합산. **주의**: `PharmaProperties.count_protease_sites`에는 pepsin이 없어, **파이프라인 manifest·클러스터 입력**의 `protease_sites.total`과 **Pharmacology API**의 `total_sites` 숫자가 다를 수 있음. |
| **BLOSUM62** | 참조(기본 SST-14) 대비 위치별 치환 점수 합·리스트 (`calculate_blosum62_score` / pharmacology 래퍼). |
| **Metal coordination** | H,C,D,E,M 잔기 위치·금속 선호 — **pharmacology** 래퍼는 `n_strong`, `chelator_interference_risk` 포함. **PharmaProperties `analyze_metal_coordination`** 는 `residues`·`total_coordinating` 중심으로 **`n_strong` 없음**. |
| **Radiolysis susceptibility** | M,W,C,H,Y,F 등에 경험적 가중치 합; FWKT 구간의 취약 잔기 강조 (`calculate_radiolysis_susceptibility`). |

### D.1 ADMET 전하 vs Pharmacology 전하 (혼동 방지)

- **ADMET `net_charge_ph74`**: 잔기 카운트 + N/C 말단 고정 항.
- **Pharmacology `charge_at_ph74`**: pKa·HH로 측쇄·말단 기여 — **소수 자리까지 다를 수 있음**.

---

## E. Cluster A–E (결정적 규칙)

**모듈**: `pyrosetta_flow/cluster_report.py` — `classify_cluster`, `batch_classify`.  
**우선순위**: A &gt; B &gt; C &gt; D &gt; E (먼저 **모든** 조건을 만족하는 최상위 클러스터 하나만 부여, 나머지는 E).

### E.1 Cluster A — High Affinity Core (`_criteria_a`)

| 조건 키 | 코드 판정 |
|---------|-----------|
| `ddG_lte_minus8` | `ddG ≤ -8.0` (NaN 아님) |
| `clash_lte_5` | `clash_score ≤ 5` |
| `pLDDT_gte_75` | pLDDT가 **유효하고 &gt;0**일 때만 `≥ 75` 요구; **없으면 이 조건은 True**(벌점 없음) |
| `pLDDT_available` | pLDDT가 유효 숫자이고 &gt;0 |
| `fwkt_contact` | `structural_rules` 내 **FWKT pharmacophore** (잔기 7–10이 `FWKT`) `pass` |

**구현 주의**: `classify_cluster`는 `if all(crit_a.values())` 로 판정하므로 **`pLDDT_available`가 True여야** A에 들어갈 수 있다. 즉 **ESMFold 등으로 pLDDT가 없으면** PyRosetta-only 실행에서 **Cluster A는 사실상 배제**될 수 있다.

### E.2 Cluster B — Selectivity (`_criteria_b`)

- `selectivity_margin ≥ 3.0` (값 없으면 NaN → 불만족).
- `ddG < -5.0` (SSTR2 결합 “있음”의 운영 정의).

### E.3 Cluster C — Stability (`_criteria_c`)

- `instability_index < 30`
- BLOSUM62 **합계 ≥ 0** (`total_score` 또는 `total_blosum62_score` 키 모두 수용).
- **프로테아제 총 점** ≤ **9** (`_SST14_PROTEASE_BASELINE`) — “native 대비 감소” 조건.

### E.4 Cluster D — Radiochemistry (`_criteria_d`)

- `-1 ≤ GRAVY ≤ 0.5`
- `|net_charge_ph74| ≤ 1` — **클러스터 입력 dict의 `net_charge_ph74`** (pharma·파이프라인이 채운 값).
- **`n_strong ≥ 1`** (`metal_coordination.n_strong`).

**데이터 소스 주의**: 파이프라인 manifest에 넣는 `PharmaProperties.calculate_all`의 `metal_coordination`은 **`n_strong` 키가 없을 수 있음**. 이 경우 **`_metal_n_strong` → 0** 이 되어 **D 조건 `chelator_site_available`이 실패**할 수 있다. 반면 **Pharmacology API** 경로의 `metal_coordination`은 `n_strong`을 채운다. **동일 후보라도 클러스터 API 입력 구성에 따라 D 적합 여부가 달라질 수 있음**.

### E.5 Cluster E

- A–D 중 어느 것도 `all(...)` 불만족 시.

---

## F. 요약 표 (UI 블록 → 소스)

| UI 블록 | 주 소스 파일 |
|---------|----------------|
| Druglikeness·MW·HBD/HBA·KD·Amphi | `backend/admet.py` `compute_admet` |
| PRRT renal | `backend/admet.py` `compute_nephrotox_risk` |
| pepADMET | `pepadmet_infer_script.py` + `pepadmet_runner.py` + `smiles_converter.py`(1차 SMILES·이황화 시도); 폴백 토폴로지는 **§C.1** |
| Pharmacology 전부 | `backend/pharmacology.py` + `AG_src/pipeline/pharma_properties.py` |
| Cluster A–E | `pyrosetta_flow/cluster_report.py` |

---

*본 문서는 구현 스냅샷 기준이며, 임계값·테이블은 코드 변경 시 함께 갱신해야 한다.*

---

# 부록 D — UI 워크스루 (원문: ../03_ui_walkthrough/README.md)

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

수치·수식의 근거는 [`../01_appendix/silo_b_computational_definitions.md`](../01_appendix/silo_b_computational_definitions.md), 코드 경로는 [`../01_appendix/silo_b_code_to_ui_pipeline_trace.md`](../01_appendix/silo_b_code_to_ui_pipeline_trace.md)를 참고하면 됩니다.

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

---

# 부록 E — 프로젝트 메모 (ADMET 대안 · Rosetta-only)

## E.1 `admet_alternative_plan_20260402.md` (전문)

# ADMETlab 3.0 대체 전략 — pepADMET + PharmPapp 통합 계획

**작성일**: 2026-04-02
**배경**: A-02 액션 아이템 "ADMETlab 3.0 API로 상위 21개 후보 ADMET 프로파일 일괄 생성" 부적합 판정에 대한 대안 수립

---

## 1. ADMETlab 3.0 부적합 사유 (확정)

| 사유 | 상세 | 확인 방법 |
|------|------|---------|
| SSL 인증서 만료 | `notAfter=2026-01-13` — 3개월째 갱신 안 됨 | `openssl s_client` |
| API 엔드포인트 404 | 홈페이지(200)는 뜨지만 `/api/predict` 등 전부 404 | `curl -sk` 테스트 |
| 소분자 전용 학습 데이터 | 400K+ entries, drug-like 소분자. 논문에 "peptide" 언급 0회 | NAR 2024 논문 (PMID 38572755) |
| Applicability Domain | 학습 MW 150-500 Da. SST-14 MW ~1600 Da → 분포 밖 | 논문 + DMPNN 아키텍처 |
| 온프레미스 불가 | 소스/모델 비공개, 웹서비스 전용 | GitHub 없음 |

**판정**: 기술적으로 입력은 가능하나 (DMPNN 그래프 기반), 학습 분포 밖 외삽이므로 예측값 무의미. API도 비활성화 상태로 파이프라인 통합 불가.

---

## 2. 대체 도구 선정

### 선정 기준
1. **펩타이드 전용** 학습 데이터 (소분자 아님)
2. **실험 데이터** 기반 (합성 데이터 제외)
3. **Peer-reviewed 논문** 존재
4. **로컬 실행** 가능 (온프레미스)
5. SST-14 (14aa, MW~1600, 사이클릭, SS bond) **AD 안**

### 선정 결과

| 도구 | 역할 | 논문 | 데이터 | Endpoint | 로컬 | 선정 근거 |
|------|------|------|--------|----------|:----:|---------|
| **pepADMET** | 종합 ADMET | JCIM 2026, 66, 936-946 | 36,643 실험 | 19개 | ⚠️ 독성만 | 유일한 systematic 펩타이드 ADMET. 사이클릭/SS bond 명시 지원 |
| **PharmPapp** | 투과도 특화 | (투고 중, 같은 Dong 그룹) | 실험 | 5개 (Caco2×3, RRCK, PAMPA) | ✅ KNIME | pepADMET과 **동일 연구팀**, 투과도 심화 |

### 탈락 도구

| 도구 | 탈락 사유 |
|------|---------|
| openclaw-peptide-admet | 합성 데이터 15K, 0⭐, 2026-03-24 생성, peer review 없음 |
| Deep-PK | 소분자 전용, 서버 다운 (GitHub 404 + 웹 ECONNREFUSED) |
| ADMETlab 3.0 | 상기 사유 |
| pkCSM / admetSAR / ProTox / SwissADME | 전부 소분자 전용, 온프레미스 불가 |

---

## 3. 통합 아키텍처

```
SST-14 유사체 후보 서열
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Layer 1: 자체 구현 (pharma_properties.py)        │
│  15 메서드 + 5 구조 규칙 + A~E 클러스터            │
│  → 즉시 실행, 외부 의존성 없음                      │
│  GRAVY, Boman, II, AI, pI(SS보정), MW,            │
│  ε280, N-end, μH, WW, charge, protease(4효소),    │
│  BLOSUM62, metal coord(Ga3+), radiolysis          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 2: pepADMET 독성 모델 (즉시)                │
│  입력: SMILES + 서열                               │
│  독성 binary (AUC 0.885)                           │
│  독성 6-class (AUC 0.949)                          │
│  독성 4-class 신경독성 (AUC 0.905)                  │
│  HC50 용혈 (R² 0.474)                              │
│  → GitHub .pth 공개, Python 3.7 + DGL 0.4.3        │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 3: pepADMET 재현 모델 (6주)                 │
│  Half-life 5종 (HBN/HBM/MBN/MBM/MIM)             │
│  BBB (AUC 0.889)                                   │
│  LogD7.4 (R² 0.818)                               │
│  Bioavailability F (AUC 0.900)                     │
│  → 학습 데이터 수집 + 재학습 필요                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 4: PharmPapp 투과도 (중기)                   │
│  Caco-2 A/C/L (R² 0.435~0.527)                    │
│  RRCK (R² 0.623)                                   │
│  PAMPA (R² 0.657)                                  │
│  → KNIME 워크플로우, 로컬 실행                       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
           종합 ADMET 프로파일
     15 자체 + 4 독성 + 8 ADME + 5 투과도
              = 32 endpoint
```

---

## 4. 구현 계획

### Phase 1: pepADMET 독성 모델 통합 (즉시, 1-2일)

| 단계 | 내용 | 의존성 |
|------|------|--------|
| 1.1 | `pepadmet` conda env 생성 (Python 3.7, DGL 0.4.3, PyTorch 1.13.1) | 네트워크 |
| 1.2 | pepADMET GitHub clone | 네트워크 |
| 1.3 | SST-14 SMILES 변환 파이프라인 (RDKit, Cys3-Cys14 SS bond 포함) | 1.1 |
| 1.4 | `toxicity_early_stop.pth` 로딩 + 추론 테스트 | 1.2 |
| 1.5 | 상위 21개 후보 일괄 독성 스크리닝 | 1.3 + 1.4 |
| 1.6 | `calculate_descriptors.py`로 2,133 feature 계산 | 1.2 |

**산출물**: 21개 후보 × 독성 4종 (binary, 6-class, 4-class, HC50) 결과 테이블

### Phase 2: pepADMET 전 모델 재현 (6주)

`docs/pepadmet_reproduction_plan.md` 참조.

| 주차 | 내용 |
|------|------|
| W1 | env + 독성 검증 + 데이터 수집 시작 |
| W2 | BBB/LogD/F 전통 ML 3모델 재학습 |
| W3 | Permeability GNN + RT DB 수집 |
| W4 | Permeability 완료 + Half-life TL pre-train |
| W5 | Half-life fine-tune 5종 + 전체 검증 |
| W6 | 22K 후보 일괄 ADMET 프로파일링 |

### Phase 3: PharmPapp 투과도 보완 (Phase 2와 병렬)

| 단계 | 내용 |
|------|------|
| 3.1 | KNIME 4.7.2 설치 |
| 3.2 | PharmPapp 워크플로우 다운로드 + 테스트 |
| 3.3 | SST-14 + 상위 21개 후보 투과도 예측 |
| 3.4 | pepADMET Permeability 결과와 교차 검증 |

---

## 5. SMILES 변환 전략 (선행 작업)

pepADMET은 **SMILES + 서열 이중 입력**이 필요. SST-14 유사체의 cyclic SMILES 생성:

```python
from rdkit import Chem
from rdkit.Chem import AllChem

def peptide_to_cyclic_smiles(sequence, ss_bond_positions=(3, 14)):
    """서열 → 사이클릭 펩타이드 SMILES (Cys-Cys SS bond 포함)"""
    # 1. 선형 펩타이드 빌드
    mol = Chem.MolFromSequence(sequence)
    # 2. Cys3-Cys14 SS bond 추가
    # ... RDKit EditableMol로 S-S 결합 형성
    # 3. Canonical SMILES 출력
    return Chem.MolToSmiles(mol)
```

**검증**: pepADMET 웹에서 동일 서열 입력 → 생성 SMILES 비교.
pepADMET GitHub의 `data/example.csv`에 SS bond 포함 SMILES 예시 있음 (`CSSC` 패턴).

---

## 6. 최종 커버리지 비교

| 카테고리 | ADMETlab 3.0 (부적합) | pepADMET + PharmPapp + 자체 |
|---------|:-------------------:|:-------------------------:|
| Physicochemical | 10 | **15** (자체 pharma) |
| Absorption | 5 | **6** (pepADMET F + PharmPapp 5) |
| Distribution | 2 | **2** (pepADMET BBB + LogD) |
| Metabolism | 0 | 0 |
| Excretion | 5 | **5** (pepADMET T½ 5종) |
| Toxicity | 12 | **4+** (pepADMET 4 + 자체 radiolysis) |
| **합계** | 34 (소분자 기반) | **32 (펩타이드 전용)** |
| **SST-14 AD** | ❌ 밖 | ✅ 안 |
| **신뢰도** | 외삽, 무의미 | 실험 데이터 기반 |

**수가 2개 적지만, 전부 펩타이드 AD 안이므로 실제 가치는 비교 불가하게 높음.**

---

## 7. 위험 요소

| 위험 | 확률 | 대안 |
|------|:----:|------|
| pepadmet env 구축 실패 (Python 3.7 EOL) | 중 | Docker 이미지 또는 Python 3.8+로 코드 마이그레이션 |
| SMILES 변환 오류 (SS bond) | 중 | pepADMET 웹에서 수동 비교 검증 |
| PharmPapp KNIME 호환 문제 | 낮 | Python 스크립트로 재구현 (모델 파일 공개) |
| Half-life RT DB 수집 어려움 | 중 | TL 없이 baseline RF로 시작, RT DB 확보 후 업그레이드 |
| pepADMET 독성 .pth 로딩 실패 | 낮 | DGL 0.4.3 정확 버전 맞추면 해결 |

---

## E.2 `rosetta_only_status_20260402.md` (전문)

# Rosetta-Only (pyrosetta_flow) 상태 보고서

**작성일**: 2026-04-02
**범위**: `pyrosetta_flow/` 모듈 전체 — 코드, 테스트, 액션 대응, 이슈

---

## 1. 모듈 구성

| 파일 | 역할 | 테스트 |
|------|------|--------|
| `runner.py` | 메인 파이프라인 (mutation→dock→rank loop) | test_runner_integration (10) + test_runner_helpers |
| `adapter.py` | PyRosetta FlexPepDock 어댑터 | test_adapter |
| `schema.py` | FlowConfig (Pydantic), CandidateResult | test_schema |
| `bandit.py` | Thompson Sampling 변이 전략 | test_bandit |
| `ranking.py` | ddG/clash 기반 후보 순위 | test_ranking |
| `convergence.py` | Mann-Whitney U 수렴 판정 | test_convergence |
| `gnina_rescoring.py` | GNINA CNN rescore + ECR consensus | test_alternative_scoring_integration |
| `pareto_ranking.py` | NSGA-II 다목적 Pareto 순위 | (위와 동일) |
| `bayesian_optimizer.py` | GP surrogate + UCB/BO 제안 | (위와 동일) |
| `cluster_report.py` | A~E 5등급 후보 분류 | test_cluster_report (57) |
| `rcsb_sequence_search.py` | RCSB PDB 서열 유사도 검색 | test_rcsb_integration (26) |
| `pdb_store.py` | SQLite 메타데이터 관리 | test_pdb_store |

**총 12개 모듈 + 12개 테스트 파일**

---

## 2. 테스트 현황

```
pyrosetta_flow/tests/: 265 passed, 6 skipped ✅

내역:
  test_runner_integration    10 passed
  test_runner_helpers        ~20 passed
  test_adapter               ~15 passed
  test_schema                ~10 passed
  test_bandit                ~15 passed
  test_ranking               ~10 passed
  test_convergence           ~10 passed
  test_alt_scoring_integ     24 passed
  test_cluster_report        57 passed
  test_rcsb_integration      23 passed + 3 skipped (network)
  test_pdb_store             ~60 passed + 3 skipped
```

---

## 3. 이번 세션 구현 내역 (rosetta_only 관련)

### 3.1 pharma 검증 + 버그 수정

| 항목 | 내용 | 커밋 |
|------|------|------|
| DIWV lookup table | 16건 오류 수정 (pharma 12 + backend 4), peptides GT 전수 대조 0 errors | `eb213c9` |
| RW 테이블 | H: 2.06→4.66, S: 1.83→3.40, W: -2.09→-2.33 | `eb213c9` |
| Boman 부호 | pharmacology.py `-sum/n` → `+sum/n` (방향 반전 수정) | `eb213c9` |
| N-end Rule P | 양 파일 (30.0h, stable) 통일 | `eb213c9` |
| **peptides GT 검증** | 8/8 메서드 완벽 일치 (6서열 × 13메서드 = 78 케이스) | `eb213c9` |

### 3.2 신규 기능

| 항목 | 내용 | 테스트 | 커밋 |
|------|------|--------|------|
| SS bond Cys pI 보정 | `_charge_at_ph()` ss_bond_cysteines 파라미터. SST-14 pI: 9.04→10.62 | 31 tests | `e5bcb51` |
| MW 계산 | `calculate_mw()` 평균 동위원소 질량. SST-14: 1639.91 Da | 26 tests | `e5bcb51` |
| Radiolysis Susceptibility | Met(3)/Trp(3)/Cys(2)/His(2)/Tyr(1)/Phe(0.5) 가중. SST-14: 6.5 high | 31 tests | `e5790dd` |
| A~E Cluster Report | `classify_cluster()` + `batch_classify()`. 5등급 분류 | 57 tests | `e5790dd` |
| FWKT Gate 강화 | `_mutable_design_positions()` FWKT 제외 + 3회 재시도 | 2 tests | `270b348` |
| DPP-IV Protease | `count_protease_sites()` DPP-IV 추가 (X-Pro/X-Ala 절단) | 7 tests | b9-b10 |
| Ga3+ D/E 배위 | `analyze_metal_coordination()` Asp/Glu carboxylate → Ga3+ 추가 | 6 tests | b9-b10 |
| 대안 스코어링 통합 | `_apply_alternative_scoring()` GNINA→ECR→Pareto→BO 체인 | 24 tests | d5 |
| pharmacology 래핑 | `pharmacology.py` → `pharma_properties.py` thin wrapper | 93 tests | b8 |
| Frontend 메트릭 | PharmacologyPanel MW/Radiolysis/SS corrected pI 표시 | tsc+lint OK | frontend |

### 3.3 RCSB PDB 통합

| 항목 | 내용 |
|------|------|
| `rcsb_sequence_search.py` | MMseqs2 기반 RCSB Search API v2 |
| `runner.py` 통합 | `_rcsb_check_candidates()` iteration 후 자동 검색 |
| Backend endpoint | `POST /api/rcsb-search` |
| Frontend | `RCSBMatchPanel.tsx` 매치 시각화 |
| 테스트 | 26개 (unit + live network) |

---

## 4. 발견된 이슈

| # | 이슈 | 심각도 | 상태 | 비고 |
|---|------|:------:|:----:|------|
| 1 | `tests/__init__.py` 누락 | 낮음 | ✅ 수정 | cross_validation import error |
| 2 | `AG_src/tests/test_config.py` 8 errors | 중간 | ⏸️ 기존 | config YAML 경로 불일치, rosetta_only 무관 |
| 3 | `test_design_alignment.py` 1 fail | 낮음 | ⏸️ 기존 | self_improving_loop 미구현 |
| 4 | `tests/test_cross_validation.py` 19 skipped | 낮음 | ⏸️ 정상 | 외부 패키지 미설치 시 skip 설계 |

**rosetta_only 자체에는 이슈 0건.** 265 passed, 6 skipped (network mark).

---

## 5. 액션 아이템 대응 (rosetta_only 관련)

| 항목 | 상태 | 비고 |
|------|:----:|------|
| B1-B4: pharma lookup table 수정 | ✅ | 16건 → 0건 |
| B5: SS bond Cys pI 보정 | ✅ | pI +1.58 보정 |
| B6: BLOSUM62 통일 | ✅ | pharmacology 래핑으로 해결 |
| B7: MW 추가 | ✅ | 1639.91 Da |
| B8: pharmacology 래핑 통합 | ✅ | 중복 lookup table 제거 |
| B9: DPP-IV 추가 | ✅ | 4번째 protease |
| B10: Ga3+ D/E 배위 | ✅ | Asp/Glu → Ga3+ |
| D5: 대안 스코어링 runner 통합 | ✅ | GNINA→ECR→Pareto→BO |
| A-04: A~E 클러스터 분류 | ✅ | 57 tests |
| A-08: Radiolysis Susceptibility | ✅ | SST-14 6.5 high |
| A-10: Radiolysis risk | ✅ | A-08과 동시 해결 |
| FWKT gate 강화 | ✅ | 46%→100% (immutable positions) |
| RCSB PDB 통합 | ✅ | 26 tests |
| Frontend MW/Radiolysis/pI | ✅ | PharmacologyPanel 반영 |

**14/14 전부 완료.**

---

## 6. 코드 품질 지표

| 메트릭 | 값 |
|--------|-----|
| 모듈 수 | 12 |
| 테스트 파일 | 12 |
| 테스트 통과 | **265** |
| 테스트 커버리지 | ~93% (추정, 이전 측정 기준) |
| pharma 메서드 | **15** (13 기존 + MW + radiolysis) |
| 구조 규칙 | **5** (FWKT, K9-D122, Cys3-Cys14, Phe6-Phe11, N-term) |
| 클러스터 등급 | **A~E 5등급** |
| 대안 스코어링 | **3모듈** (GNINA, Pareto, BO) |
| 누적 커밋 (이번 세션) | 10+ |

---

## 7. 남은 작업 (rosetta_only)

| # | 항목 | 우선순위 | 의존성 |
|---|------|---------|--------|
| 1 | cluster_report 대시보드 연결 (ClusterPanel.tsx) | P2 | 없음 |
| 2 | pdb_store.py 커밋 (untracked) | P2 | 없음 |
| 3 | agent monitor UI 디버깅 | P3 | 없음 |
| 4 | 22,000 후보 대규모 실행 | P3 | 서버 env 완료 후 |

---

## 8. Git 상태

| 항목 | 상태 |
|------|------|
| 현재 브랜치 | `feat/pharma-cross-validation` |
| main 대비 | 3 ahead, 1 behind |
| PR | [#2](https://github.com/AI-scientist4BIO/SST14-M_scr/pull/2) — 생성됨 |
| CI (main) | ✅ 3연속 success |
| untracked | `pdb_store.db`, `config/` |
