# 2026-03-11 (화) 일일 작업 계획서

> **시스템**: SSTR2 AI Co-Scientist
> **작성 근거**: 6개 분야 병렬 검토 결과 종합 (UI/UX, 기능/확장성, OOP/클린코드, 스코어링 기술, 약리학/화공학, 수학/물리학)
> **전일 완료**: 대안 스코어링 설계서 + 심층 조사 보고서 작성, git 형상관리 완료

---

## 검토 결과 핵심 발견 요약

### 즉시 수정 필요 (버그/불일치)

| # | 발견 | 분야 | 심각도 |
|---|------|------|--------|
| B1 | `pharmacology.py` Radzicka-Wolfenden S=1.15→1.83, P=0.0→-2.54 오류 | 약리학 | **높음** |
| B2 | `pharma_properties.py` Boman Index 부호 반전 누락 (`-mean(RW)` 필요) | 약리학 | **높음** |
| B3 | `pharma_properties.py` DIWV KQ값 24.64→24.68, N-end Rule Pro 20.0→30.0 | 약리학 | 중간 |
| B4 | `MutationAnalysis.tsx` TS2322 recharts Formatter 타입 에러 | UI | 낮음 |
| B5 | `httpx`, `aiohttp` bio-tools 환경 미설치 | 인프라 | 낮음 |

### 구조적 문제 (리팩토링)

| # | 발견 | 분야 | 심각도 |
|---|------|------|--------|
| S1 | `runner.py` 790줄 God Function (cyclomatic complexity 30+) | OOP | **심각** |
| S2 | 약리학 계산 이중 구현 (`backend/` vs `AG_src/`) — 값 불일치 | DRY | **심각** |
| S3 | Backend 테스트 0개 (13개 순수 함수 + 7개 라우터 미검증) | 테스트 | 높음 |
| S4 | 가중합 스코어링의 4가지 수학적 한계 (비볼록 Pareto 해 누락 등) | 수학 | 높음 |
| S5 | SiloBPage God Component — 18개 컴포넌트 직접 관리 | UI | 중간 |

### 성능 위험

| # | 발견 | 분야 |
|---|------|------|
| P1 | 22K 후보 테이블: 전체 배열 2초마다 sort+filter, 1833개 pagination 버튼 | UI 성능 |
| P2 | HTTP polling 2초 고정 — 실험 미실행시에도 동일 빈도 | 네트워크 |
| P3 | `candidates` 배열 참조 불안정 → useMemo 무효화 → 전체 리렌더링 | React |

### 기능 갭

| # | 발견 | 분야 |
|---|------|------|
| F1 | Silo A — 대시보드 연결 없음 (코드 완료, UI/Backend 미연결) | 기능 |
| F2 | Settings API → FlowConfig 연동 단절 | 기능 |
| F3 | KPI Summary Bar 없음 (연구자 즉시 파악 불가) | UX |
| F4 | Pareto Scatter Plot, Iteration Trend Chart 등 핵심 시각화 부재 | 시각화 |
| F5 | 방사성의약품 특이적 metric 누락 (킬레이터 안정성, T/K ratio 등) | 약리학 |

---

## 작업 우선순위 및 일정

### AM-1: 버그 수정 (09:00-10:30)

**목표**: 약리학 계산값 정확성 확보

| Task | 파일 | 내용 | 시간 |
|------|------|------|------|
| B1 fix | `backend/pharmacology.py` | Radzicka-Wolfenden S=1.83, P=-2.54 수정 | 15분 |
| B2 fix | `AG_src/pipeline/pharma_properties.py` | Boman Index `return -mean` 수정 | 10분 |
| B3 fix | `AG_src/pipeline/pharma_properties.py` | DIWV KQ=24.68, Pro half-life=30.0 수정 | 10분 |
| B4 fix | `frontend/src/components/MutationAnalysis.tsx` | recharts Formatter 타입 캐스팅 | 10분 |
| B5 fix | shell | `conda activate bio-tools && pip install httpx aiohttp` | 5분 |
| 검증 | tests | 전체 테스트 실행 (pytest + vitest) 확인 | 15분 |
| 커밋 | git | fix 커밋 + push | 5분 |

### AM-2: NSGA-II Pareto Ranking 구현 (10:30-12:30)

**목표**: 가중합 스코어링의 수학적 한계 해결 — 최우선 대안 방법론

| Task | 내용 | 시간 |
|------|------|------|
| 의존성 설치 | `pip install pymoo>=0.6.0` | 5분 |
| 핵심 모듈 | `pyrosetta_flow/pareto_ranking.py` 작성 (~200줄) | 40분 |
| | - `CandidateRankingProblem` (4 objectives + 2 constraints) | |
| | - `pareto_rank_candidates()` (non-dominated sorting + crowding) | |
| | - `select_from_pareto_front()` (knee/crowding/ddg_primary) | |
| runner 통합 | `runner.py` step06 후 pareto ranking 삽입 | 20분 |
| emitter 확장 | `StatusEmitter.set_pareto_front()` 메서드 추가 | 10분 |
| 테스트 | `tests/test_pareto_ranking.py` 7개 케이스 | 30분 |
| 커밋 | git | 5분 |

### PM-1: GNINA CNN Rescoring 구현 (13:30-15:30)

**목표**: FlexPepDock과 독립적인 2nd opinion scoring

| Task | 내용 | 시간 |
|------|------|------|
| 설치 확인 | gnina 바이너리 설치/확인 | 15분 |
| PDB chain 확인 | FlexPepDock 출력 PDB의 chain ID 형식 실물 확인 | 15분 |
| 핵심 모듈 | `pyrosetta_flow/gnina_rescoring.py` 작성 (~250줄) | 40분 |
| | - `split_receptor_peptide()` (chain or residue 기반) | |
| | - `gnina_rescore()` (score_only CLI wrapper) | |
| | - `batch_gnina_rescore()` (ThreadPoolExecutor) | |
| consensus | `pyrosetta_flow/consensus_scoring.py` (~100줄) | 20분 |
| | - `exponential_rank_consensus()` (ECR, tau=0.1) | |
| runner 통합 | step06_gnina substep 삽입 | 15분 |
| 테스트 | mock subprocess 기반 단위 테스트 | 20분 |
| 커밋 | git | 5분 |

### PM-2: UI 핵심 개선 (15:30-17:30)

**목표**: 연구자 UX 즉시 개선 + 22K 성능 대비

| Task | 내용 | 시간 |
|------|------|------|
| KPI Summary Bar | 대시보드 상단 요약 카드 (Best ddG, FWKT%, QC Pass Rate, 총 후보, iteration) | 30분 |
| Pareto Scatter Plot | Recharts ScatterChart 컴포넌트 (ddG vs stability, rank 색상) | 30분 |
| CandidateTable | GNINA score + Consensus score 컬럼 추가 | 15분 |
| Pagination fix | ellipsis 패턴 적용 (1 2 3 ... N-2 N-1 N) | 15분 |
| candidates 참조 | shallow compare로 불필요한 리렌더링 방지 | 15분 |
| 커밋 | git | 5분 |

### PM-3: Backend 테스트 + 커밋 (17:30-18:30)

**목표**: 테스트 갭 해소 시작

| Task | 내용 | 시간 |
|------|------|------|
| pharmacology 테스트 | 13개 순수 함수 단위 테스트 (SST-14 native 기대값 검증) | 30분 |
| pareto 테스트 보강 | edge case 추가 (empty, single, all-infeasible) | 10분 |
| CI 확인 | 전체 테스트 + lint 통과 확인 | 10분 |
| 최종 커밋 | git commit + push | 5분 |
| 일일 보고 | 진행 상황 정리 | 5분 |

---

## 이번 주 로드맵 (3/11-3/14)

| 날짜 | 오전 | 오후 |
|------|------|------|
| **3/11 (화)** | 버그 수정 + NSGA-II 구현 | GNINA 구현 + UI 개선 + 테스트 |
| **3/12 (수)** | ESM-2 Pseudo-perplexity 구현 | 데모 실험 실행 (시나리오 A, 14분) + 영상 녹화 |
| **3/13 (목)** | runner.py 리팩토링 (God Function 분해) | 약리학 모듈 통합 (DRY) + Backend 테스트 확대 |
| **3/14 (금)** | Bayesian Optimization 구현 (Phase 2) | Silo A 대시보드 연결 착수 |

---

## 분야별 검토 보고서 요약

### 1. UI/UX
- 컴포넌트 18개, 페이지 5개 구성. SiloBPage가 God Component
- KPI 요약 없음, 섹션 네비게이션 없음 → 연구자 정보 탐색 비용 과다
- 22K 후보 시 성능 병목 (전체 sort 2초마다, 1833 pagination 버튼)
- 색상 대비 일부 WCAG AA 미달 (`text-slate-500` on dark bg)
- Pareto Scatter Plot, Iteration Trend, Pharmacology Radar 등 핵심 시각화 부재

### 2. 기능/확장성
- Silo B 파이프라인: **프로덕션 수준** (93% 커버리지, CI 7 jobs 통과)
- Silo A: 코드 완료(1400줄 orchestrator + 10 steps + 8 tools)이나 **대시보드 미연결**
- 단일 실험 제약 (싱글턴 프로세스), DB 없이 JSONL/파일 기반
- Settings API → FlowConfig 연동 단절

### 3. OOP/클린코드 — 전체 3.2/5.0
- **강점**: Agent/Tool/Provider 추상 계층 우수, 의존성 방향 일관
- **약점**: `runner.py` 790줄 God Function, 약리학 이중 구현, Backend 테스트 0개
- Agent execute() dict 반환 → TypedDict/dataclass 권장
- CandidateTable 609줄 → 서브컴포넌트 파일 분리 필요

### 4. 스코어링 기술
- NSGA-II: 통합 **매우 자연스러움** (pymoo NonDominatedSorting만 사용, ~200줄)
- GNINA: **chain 분리 이슈 주의** (PyRosetta dump_pdb chain ID 형식 확인 필수)
- ESM-2: pharmacology.py에 14번째 metric 추가 **자연스러움** (lazy import)
- BO: runner.py iteration 루프 구조 변경 필요 (난이도 중간)
- 의존성 충돌: **없음** (pymoo/torch/botorch 호환)
- 성능: NSGA-II <0.1초, GNINA +30초(GPU), ESM-2 +0.8초(CPU)/서열

### 5. 약리학/화공학
- 13개 property 중 **Radzicka-Wolfenden S, P값 오류** 발견
- 두 구현 간 Boman Index 부호, DIWV KQ, Pro 반감기 **불일치**
- 방사성의약품 특이적 gap: 킬레이터 복합체 안정성, T/K ratio, 방사분해 취약성, 합성 가능성 **전무**
- D-아미노산/비천연 아미노산 미지원 → Octreotide/DOTATATE 비교 불가
- FWKT 규칙: K9 필수이나 T10은 S/A 허용으로 완화 가능 (문헌 근거)

### 6. 수학/물리학
- 가중합 clip 범위 임의성, 가중치 물리적 근거 부재 → **NSGA-II로 해결**
- Thompson Sampling: 위치 간 독립 가정이 epistatic interaction 미포착 (가장 심각한 한계)
- Mann-Whitney U: n=15에서 검정력 ~0.40-0.50 (Type II 오류 위험)
- FlexPepDock ddG: 엔트로피 항 누락이 가장 심각한 물리적 한계
- ECR tau=0.1: sensitivity analysis 필요
- 수치 안정성: 전반적으로 양호 (division by zero, overflow 방어 완비)
