# SSTR2 AI Co-Scientist 시연 시나리오

## 영상 개요

| 항목 | 내용 |
|------|------|
| 목적 | 내부 보고용 시스템 데모 영상 |
| 예상 시간 | 10-15분 |
| 청자 | 약학 박사, 비개발자 (방사성의약품 도메인 전문가) |
| 녹화 환경 | localhost — Backend :8787 / Frontend :5173 |
| LLM | Ollama qwen3:8b (Planner / Critic / Reporter) |
| 기준 데이터 | 아카이브 `sst14_mutdock_4002` (19 candidates, 3 iterations, completed) |

---

## 시연 흐름

### Scene 1: 대시보드 소개 (2분)

**목표**: 전체 UI 구성을 훑어 청자가 시스템 규모를 파악하게 한다.

| 순서 | 화면 | 행동 | 나레이션 포인트 |
|------|------|------|----------------|
| 1-1 | Silo B 페이지 (`/silo-b`) | 브라우저 전체 화면 표시 | "SST-14 변이 기반 후보 스크리닝 대시보드입니다" |
| 1-2 | Pipeline Status 패널 | 상단 파이프라인 단계 표시 | "baseline → mutation → dock → QC 4단계 파이프라인" |
| 1-3 | Agent Monitor 패널 | Planner/Critic/Reporter 상태 확인 | "3개 LLM 에이전트가 자율적으로 실험을 설계·검증·보고합니다" |
| 1-4 | Run 선택 드롭다운 | 아카이브 `sst14_mutdock_4002` 선택 | "완료된 실험 아카이브를 불러옵니다 — 19개 후보, 3회 반복" |
| 1-5 | Candidate Ranking 테이블 | 정렬: ddG 오름차순 | "best ddG = **-47.66 kcal/mol**, 결합 에너지가 낮을수록 유리" |

> **전환 멘트**: "이제 실제로 새 실험을 시작해 보겠습니다."

---

### Scene 2: 실험 실행 (3분)

**목표**: 실시간 파이프라인 동작을 시각적으로 보여준다.

| 순서 | 화면 | 행동 | 나레이션 포인트 |
|------|------|------|----------------|
| 2-1 | Experiment Control 패널 | iterations=2, candidates=4 설정 | "데모용 경량 설정 — 실제 production은 수천 단위" |
| 2-2 | **Run 버튼 클릭** | `POST /api/experiment/run` 호출 | "PyRosetta FlexPepDock이 bio-tools conda 환경에서 기동됩니다" |
| 2-3 | Pipeline Status | 단계별 진행 색상 변화 관찰 | "baseline 구조 로딩 → ProteinMPNN 변이 생성 → FlexPepDock 도킹" |
| 2-4 | Loop Timeline | 이벤트 실시간 추가 | "각 단계의 시작·완료·에러가 타임라인에 기록됩니다" |
| 2-5 | Agent Monitor | Planner → Critic 전환 | "Planner가 변이 전략을 제안하면, Critic이 FWKT 보존 여부를 검증" |

> **Fallback**: FlexPepDock이 예상보다 느리면 — "production 모드에서 실제 도킹이 진행 중입니다. 시간 관계상 완료된 아카이브(4002)로 이어서 보여드리겠습니다." → Scene 1-4로 전환

---

### Scene 3: 후보 평가 (3분)

**목표**: 개별 후보의 구조·약리·독성 정보를 종합 평가하는 과정을 보여준다.

| 순서 | 화면 | 행동 | 나레이션 포인트 |
|------|------|------|----------------|
| 3-1 | Candidate Ranking | best candidate 행 클릭 | "ddG가 가장 낮은 후보를 선택합니다" |
| 3-2 | MoleculeViewer (3D 뷰어) | PDB 구조 로드, 회전 | "펩타이드-수용체 복합체 3D 구조 — Cys3-Cys14 이황화결합 확인" |
| 3-3 | Pharmacology Panel | 13개 물성 값 표시 | "MW, pI(SS보정), GRAVY, Boman index 등 문헌 기반 물성 13종" |
| 3-4 | Pharmacology 상세 | pI=10.62, Radiolysis=6.5 강조 | "pI 10.62 → 신장 여과 유리, 방사선분해 지수 6.5(높음) → W8 잔기가 취약점" |
| 3-5 | Cluster Panel | Cluster A~E 분류 결과 | "비지도 클러스터링으로 구조적 유사성 기반 그룹 분류" |
| 3-6 | ADMET Panel | Druglikeness, Renal Risk | "pepADMET 모델 추론 — 약물성, 독성, 신장 위험도 평가" |

> **핵심 강조**: "모든 수치는 문헌 기반 계산값이며, 주관적 가중치를 사용하지 않습니다."

---

### Scene 4: 선택성 검증 (2분)

**목표**: SSTR2 선택성을 SSTR1~5 전체에 대해 비교 검증하는 과정을 보여준다.

| 순서 | 화면 | 행동 | 나레이션 포인트 |
|------|------|------|----------------|
| 4-1 | 좌측 메뉴 | Selectivity 페이지 이동 | "선택성 검증 페이지로 이동합니다" |
| 4-2 | Receptor 목록 | 5/5 receptor loaded 확인 | "SSTR1(9IK8), SSTR2(7T10), SSTR3(8XIR), SSTR4(7XMT), SSTR5(8ZBJ)" |
| 4-3 | Analysis 실행 | Run 버튼 클릭 (`POST /api/selectivity/run`) | "선택한 후보를 5개 수용체에 동시 도킹합니다" |
| 4-4 | 결과 테이블 | margin 값 확인 | "SSTR2 대비 다른 수용체와의 에너지 차이(margin)가 클수록 선택성이 높습니다" |

> **Fallback**: 도킹 ~60초 소요 시 — "실제 전원자 도킹이 진행 중입니다. 각 수용체당 약 1분 소요됩니다."

---

### Scene 5: 수렴 분석 + 종합 (2분)

**목표**: 반복 실험의 수렴성과 전체 SAR(구조-활성 관계)을 종합 정리한다.

| 순서 | 화면 | 행동 | 나레이션 포인트 |
|------|------|------|----------------|
| 5-1 | Convergence Graph | iteration별 ddG 추세 | "3회 반복에 걸쳐 ddG가 수렴 — 탐색 공간이 좁아지고 있음" |
| 5-2 | DdG Distribution | 히스토그램 | "전체 후보의 결합 에너지 분포 — 좌측 꼬리가 우수 후보군" |
| 5-3 | SAR Heatmap | 위치별 변이-에너지 관계 | "어떤 위치의 어떤 변이가 에너지에 기여하는지 한눈에 파악" |
| 5-4 | Sequence Logo | 위치별 아미노산 빈도 | "FWKT(7-10번) 위치가 100% 보존 — pharmacophore 보전 확인" |
| 5-5 | Best candidate 하이라이트 | 테이블 상단 | "최종 best: ddG -47.66, FWKT 100% 보존, Cluster A, pI 10.62" |

> **마무리 멘트**: "AI Co-Scientist가 자율적으로 후보를 설계·평가·검증하여, 연구자는 최종 의사결정에 집중할 수 있습니다."

---

## 핵심 수치 (시연 중 강조)

| 지표 | 값 | 시연 포인트 |
|------|------|----------|
| Best ddG | **-47.66 kcal/mol** | 가장 낮은 결합 에너지 → 높은 친화도 |
| FWKT 보존율 | **100%** | 약리단(pharmacophore) 완전 보존 |
| 후보 수 | **19개** | 3회 iteration에서 생성된 전체 후보 |
| pI (SS보정) | **10.62** | 양전하 → 신장 여과에 유리 |
| 방사선분해 지수 | **6.5 (high)** | Trp(W8) 잔기가 방사선 취약 → 개선 포인트 |
| Selectivity receptors | **5/5 loaded** | SSTR1~5 전체 수용체 구조 로드 완료 |

---

## 데모 실험 설정 (Scene 2용)

```yaml
approach: "b"           # Silo B (mutation + dock)
iterations: 2           # 시간 절약 (production: 10+)
candidates_per_iter: 4  # 시간 절약 (production: 100+)
예상 소요: 3-5분
conda env: bio-tools    # PyRosetta, ESMFold, ProteinMPNN
LLM: qwen3:8b via Ollama
```

---

## 주의사항 / Fallback 계획

| 상황 | 대응 |
|------|------|
| FlexPepDock 느림 (>5분) | 아카이브 `sst14_mutdock_4002`로 즉시 전환, "production 환경에서는 GPU 병렬화로 가속" 언급 |
| Selectivity 도킹 60초+ | "전원자 도킹이 실시간으로 진행 중" 설명, 결과 대기 |
| LLM 응답 지연 | "로컬 LLM(qwen3:8b) 사용 중 — 보안상 외부 API 미사용" 설명 |
| WebSocket 연결 끊김 | 새로고침 후 아카이브 모드로 전환 |
| 3D 뷰어 로딩 실패 | PDB 파일 경로 확인, 수동 경로 입력으로 우회 |
| Experiment Stop 필요 | `POST /api/experiment/stop` — Experiment Control 패널의 Stop 버튼 |

---

## 페이지별 URL 정리

| 페이지 | URL | 주요 컴포넌트 |
|--------|-----|-------------|
| Silo B (메인) | `/silo-b` | PipelineStatus, AgentMonitor, CandidateTable, ExperimentControl, MoleculeViewer, PharmacologyPanel, LoopTimeline, ConvergenceGraph, DdGDistribution, SARHeatmap, SequenceLogo, ClusterPanel, ADMETPanel |
| Selectivity | `/selectivity` | Receptor 목록, 도킹 실행, margin 비교 |
| Silo A | `/silo-a` | 3-Arm NIM 파이프라인 (이번 데모 범위 외) |
| Combined | `/combined` | A+B 통합 뷰 (이번 데모 범위 외) |
| Settings | `/settings` | 실험 설정, 모델 경로 |

---

## 녹화 체크리스트

- [ ] Backend 기동 확인: `curl http://localhost:8787/api/health`
- [ ] Frontend 기동 확인: 브라우저에서 `http://localhost:5173` 접속
- [ ] Ollama 기동 확인: `ollama list` → qwen3:8b 표시
- [ ] bio-tools conda env 활성화 확인
- [ ] 아카이브 `sst14_mutdock_4002` 데이터 존재 확인
- [ ] SSTR1~5 PDB/CIF 파일 로드 확인 (Selectivity 페이지)
- [ ] 화면 해상도: 1920x1080, 브라우저 줌 100%
- [ ] 녹화 소프트웨어 준비 (OBS 등)
- [ ] 마이크 테스트
