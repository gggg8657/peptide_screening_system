## 0. 기존 보고서 맵 및 통합 분석

| 원본 파일 | 역할 | 본 통합본에서의 위치 |
|-----------|------|----------------------|
| `silo_b_dashboard_panels_methodology.md` | 패널별 데이터 출처, Live/Mock, ADMET·Pharma·Cluster 요약, 스크린샷 경로 | Part II §1~4·6 요약 + **부록 A** 전문 |
| `silo_b_code_to_ui_pipeline_trace.md` | FlexPepDock → QC → 상태 JSON → API, Mermaid 다이어그램 | Part II §3·5 + **부록 B** 전문 |
| `silo_b_computational_definitions_detailed.md` | 필드별 수식, pepADMET SMILES/폴백, Cluster 코드 주의 | Part II §1·4·5·7 + **부록 C** 전문 |
| `silo_b_ui_walkthrough/README.md` | 저장 HTML 스크롤 캡처 17장·패널 설명 | Part II §6 + **부록 D** 전문 |

**중복 제거 관점**: 방법론(부록 A)과 계산 정의(부록 C)는 ADMET·pepADMET 설명이 겹친다. 발표 시에는 **§4·5 요약표**만 슬라이드에 올리고, 질의응답 시 **부록 C**(특히 pepADMET·Cluster 관련 절)를 연다.

**의존 자산**: `silo_b_ui_walkthrough/assets/scroll_*.png`(17장, 폭 리사이즈됨), `docs/screenshots/*.png`, Desktop 저장 HTML(워크스루 README 경로 참고).

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

- **연속 스크롤 PNG 17장**: `docs/reports/silo_b_ui_walkthrough/assets/scroll_00_y0.png` ~ `scroll_16_y13120.png` (저장 폭 약 900px로 리사이즈)
- **설명 텍스트**: 부록 D (`silo_b_ui_walkthrough/README.md`)

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
