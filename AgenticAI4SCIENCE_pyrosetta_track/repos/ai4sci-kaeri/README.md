# SSTR2 펩타이드 바인더 설계 파이프라인

DOTATATE 스캐폴드(AGCKNFFWKTFTSC, 14-aa 환형 펩타이드, Cys3-Cys14 이황화 결합) 기반의 SSTR2(소마토스타틴 수용체 타입 2) 선택적 펩타이드 바인더를 설계하는 에이전트 기반 다단계 최적화 파이프라인입니다.

## 파이프라인 개요

### 실행 단계

| 단계 | 이름 | 엔진 | 설명 |
|------|------|------|------|
| Step 01 | 수용체 준비 | OpenFold3 / PDB | SSTR2 수용체 구조 및 포켓 잔기 준비 |
| Step 02 | RFdiffusion | NVIDIA NIM | 다양한 펩타이드 백본 구조 생성 |
| Step 03 | ProteinMPNN | NVIDIA NIM | 각 백본에 대한 아미노산 서열 설계 |
| Step 03b | BLOSUM 변이 | 규칙 기반 | DOTATATE 시드에서 BLOSUM62 기반 변이체 생성 |
| Step 03b-QC | 안정성 사전심사 | 규칙 기반 | 예측 반감기(>= 50.0h) 기준 변이체 필터링 |
| Step 04 | ESMFold QC | ESMFold API (LIVE) | 구조 예측 + pLDDT 품질 관리 |
| Step 05 | DiffDock | pLDDT 기반 시뮬레이션 | 분자 도킹 점수 예측 |
| Step 06 | PyRosetta FlexPepDock | PyRosetta (LIVE) | 전원자 정밀화 + 결합 에너지(ddG) 계산 |
| Step 05b | 선택성 | PyRosetta (LIVE) | SSTR1/3/4/5 off-target 도킹 (AlphaFold 구조) |
| Step 07 | 분석 | FoldMason + PyMOL | 구조 비교(lDDT) + 시각화 렌더링 |
| Step 08 | GLP-1 안정성 | 규칙 기반 | 화학적 변형을 포함한 반감기 예측 |
| Step 09 | MolMIM | NVIDIA NIM (LIVE) | 펩타이드 스캐폴드에서 소분자 최적화 |

**참고:** Step 06(PyRosetta)이 Step 05b(선택성) 이전에 실행됩니다. 선택성 스크리닝에 Step 06의 정밀화된 복합체 PDB와 SSTR2 ddG가 필요하기 때문입니다.

### 에이전트 (5개)

| 에이전트 | 유형 | 역할 |
|----------|------|------|
| Planner | LLM | 실험 계획 수립 및 가설 생성 |
| QC & Ranker | LLM | 다중 게이트 품질 관리 및 후보 순위 결정 |
| DiversityManager | 코드 | 클러스터 기반 서열 다양성 필터링 |
| ScientistCritic | LLM | 결과 평가 및 파라미터 최적화 |
| Reporter | LLM | 실험 노트북 및 요약 보고서 생성 |

---

## 스코어링 지표

### 1. pLDDT (predicted Local Distance Difference Test)

| 속성 | 값 |
|------|------|
| **출처** | ESMFold API (Step 04) |
| **범위** | 0 - 100 |
| **방향** | 높을수록 좋음 (구조 예측 신뢰도 높음) |
| **단위** | 무차원 (신뢰도 점수) |
| **게이트 기준** | >= 50.0 |

**정의:** ESMFold 구조 예측의 잔기별 신뢰도 점수입니다. 예측된 3D 좌표가 실제 구조와 얼마나 일치하는지를 추정합니다. 70 이상은 높은 신뢰도, 50-70은 보통, 50 미만은 낮은 신뢰도를 의미합니다.

**계산 방법:** ESMFold 출력 PDB의 B-factor 컬럼에서 잔기별 pLDDT 값을 추출하여 전체 잔기 평균을 계산합니다.

```python
# run_pipeline_live.py: extract_plddt_from_pdb()
for line in pdb_text.splitlines():
    if line.startswith("ATOM") and len(line) >= 66:
        bfactor = float(line[60:66].strip())  # B-factor = pLDDT
        plddts.append(bfactor)
mean_plddt = sum(plddts) / len(plddts)
```

**해석:** pLDDT > 70이면 ESMFold가 올바른 폴딩을 예측했다고 확신. pLDDT < 50이면 본질적으로 무질서한 서열이거나 잘못 접힌 구조로, 약물 후보로 부적합합니다.

---

### 2. Dock Score (도킹 친화도)

| 속성 | 값 |
|------|------|
| **출처** | DiffDock 시뮬레이션 (Step 05) |
| **범위** | 보통 -15 ~ -3 |
| **방향** | 더 음수일수록 좋음 (결합 예측 강함) |
| **단위** | kcal/mol (추정) |
| **게이트 기준** | 상위 20% 선별 |

**정의:** 펩타이드가 SSTR2 수용체 포켓에 얼마나 강하게 결합하는지 예측하는 점수입니다. pLDDT 가중 시뮬레이션에서 결합 포즈 품질을 추정합니다.

**계산 방법:** `dock_score = -(pLDDT_mean / 10.0) + 랜덤 노이즈`. 현재는 ESMFold 신뢰도 기반 시뮬레이션이며, 실제 DiffDock API 호출은 아닙니다. 더 음수일수록 결합 예측이 좋습니다.

**해석:** dock_score < -7.0이면 강한 바인더로 간주. 비용이 큰 PyRosetta 정밀화 전 사전 필터 역할을 합니다. 게이트는 점수 기준 상위 20%를 통과시킵니다 (`gate_thresholds.yaml`의 `docking_top_pct`로 설정 가능).

---

### 3. ddG (계면 결합 에너지)

| 속성 | 값 |
|------|------|
| **출처** | PyRosetta InterfaceAnalyzerMover (Step 06) |
| **범위** | 보통 -50 ~ +10 |
| **방향** | 더 음수일수록 좋음 (결합 강함) |
| **단위** | kcal/mol (Rosetta Energy Units) |
| **게이트 기준** | <= -5.0 kcal/mol |

**정의:** PyRosetta의 InterfaceAnalyzerMover로 계산한 계면 결합 자유 에너지입니다. 결합된 복합체와 분리된 수용체 + 펩타이드 간의 에너지 차이를 측정합니다.

**계산 과정:**
1. 수용체-펩타이드 복합체 로드 (참조 구조에서 MutateResidue + FlexPepDock 정밀화)
2. InterfaceAnalyzerMover가 jump_id=1에서 체인 분리
3. ddG = E(복합체) - E(수용체) - E(펩타이드)
4. 반데르발스, 정전기, 용매화, 수소결합 항 포함

**해석:** ddG < -5.0이면 유의미한 결합. ddG < -20.0이면 강한 결합. ddG < -35.0이면 우수한 결합(알려진 고친화도 펩타이드 바인더 수준). 양수 ddG는 에너지적으로 불리한 복합체를 의미합니다. 충돌 점수(fa_rep > 임계값인 잔기 수)도 확인하며, 게이트는 clash_score <= 10을 요구합니다.

---

### 4. lDDT (Local Distance Difference Test)

| 속성 | 값 |
|------|------|
| **출처** | FoldMason 구조 비교 (Step 07) |
| **범위** | 0.0 - 1.0 |
| **방향** | 높을수록 좋음 (참조 구조와 유사) |
| **단위** | 무차원 (유사도 점수) |
| **게이트 기준** | >= 0.6 |

**정의:** 설계된 펩타이드의 예측 구조와 참조 DOTATATE 구조 간의 구조적 유사도를 FoldMason 정렬 알고리즘으로 측정합니다.

**계산 방법:** FoldMason이 쿼리와 참조 구조 간 CA 원자 거리를 비교합니다. lDDT = 허용 오차(0.5A, 1A, 2A, 4A) 내에서 보존된 잔기간 거리의 비율.

**해석:** lDDT > 0.8이면 참조와 매우 유사. 0.6-0.8이면 보통 수준. 0.6 미만이면 DOTATATE에서 상당히 벗어난 구조입니다.

**참고:** FoldMason CLI 호환성 문제로 0.0을 반환할 수 있습니다. 사용 불가 시 해당 게이트 없이 파이프라인이 계속 진행되며, 순위표의 lDDT 컬럼에 NaN 또는 대체값이 표시됩니다.

---

### 5. Selectivity Margin (선택성 마진)

| 속성 | 값 |
|------|------|
| **출처** | PyRosetta off-target 도킹 (Step 05b) |
| **범위** | 보통 -3000 ~ 0 |
| **방향** | 더 양수일수록 좋음 (SSTR2에 더 선택적; G-2 SSOT) |
| **단위** | kcal/mol |
| **게이트 기준** | >= 10.0 kcal/mol |

**정의:** 펩타이드가 SSTR2에 가장 유사한 off-target 수용체(SSTR1, SSTR3, SSTR4, SSTR5) 대비 얼마나 더 강하게 결합하는지를 측정합니다.

**계산 방법:**
```
selectivity_margin = ddG(최악의 off-target) - ddG(SSTR2)   # G-2: 양수=SSTR2 더 특이적 (좋음)
```
"최악의 off-target"은 ddG가 가장 낮은(가장 유리한) off-target 수용체입니다. Off-target ddG 계산 과정:
1. SSTR1(P30872), SSTR3(P32745), SSTR4(P31391), SSTR5(P35346)의 AlphaFold 구조 다운로드
2. 각 off-target 수용체를 SSTR2에 구조 정렬 (CA 중첩)
3. 키메라 복합체 조립 (off-target 수용체 + SSTR2 펩타이드)
4. FlexPepDock + InterfaceAnalyzerMover 실행

**해석:** 마진 +10이면 SSTR2 결합이 최고 off-target보다 10 kcal/mol 더 강함 (양수=좋음; G-2 SSOT). 매우 큰 양수 마진(+15 이상)은 우수한 SSTR2 선택성을 의미합니다. 게이트는 개별 off-target ddG가 -15.0 kcal/mol을 초과하지 않을 것도 요구합니다 (`offtarget_max_allowed`).

---

### 6. Final Score (최종 점수)

| 속성 | 값 |
|------|------|
| **출처** | 가중 합산 (전체 단계) |
| **범위** | 0.0 ~ 약 20.0 |
| **방향** | 높을수록 좋은 후보 |
| **단위** | 무차원 (가중 합성 점수) |
| **게이트 기준** | 없음 (순위 결정용) |

**정의:** 5개 지표를 가중 합산하여 하나의 순위 값으로 만든 합성 점수입니다.

**계산 방법:**
```
finalScore = (pLDDT / 100) * 0.15
           + (-dockScore) * 0.25
           + (-ddG) * 0.25
           + lDDT * 0.15
           + selectivity_margin * 0.20    # G-2: 양수=좋음이므로 부호 반전 불필요
```

**가중치:**

| 지표 | 비율 | 근거 |
|------|------|------|
| pLDDT | 15% | 구조 신뢰도 기본값 |
| Dock Score | 25% | 결합 포즈 품질 |
| ddG | 25% | 물리 기반 결합 에너지 (가장 신뢰성 높음) |
| lDDT | 15% | 참조 구조와의 유사도 |
| Selectivity | 20% | 표적 특이성 (안전성 관련 중요) |

**해석:** Final Score가 높을수록 좋은 후보. 높은 pLDDT, 음수 dock/ddG, 높은 lDDT, 양수 selectivity margin(G-2 SSOT)을 가진 후보가 최상위에 위치합니다.

---

## 빠른 시작

### 사전 요구사항

- Python 3.12 (`bio-tools` conda 환경)
- PyRosetta v2026.06, PyMOL 3.1.0 (`conda install -n bio-tools`)
- Node.js 20+ / npm 11+ (프론트엔드 대시보드용)
- NVIDIA NIM API 키

### 파이프라인 실행

```bash
conda activate bio-tools
export NVIDIA_NIM_API_KEY="your-key-here"
python run_pipeline_live.py
```

### 대시보드 실행

```bash
# 백엔드 API (FastAPI + uvicorn)
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8787

# 프론트엔드 (별도 터미널)
cd frontend && npm run dev

# 프론트엔드: http://localhost:5173
# API:        http://localhost:8787/api/status
# OpenAPI:    http://localhost:8787/docs
```

`NVIDIA_NIM_API_KEY` 환경변수가 설정되지 않은 경우 `PRST_N_FM/bionemo/.env`에서 API 키를 자동으로 로드합니다.

### 무한 발굴 엔진 (Continuous Discovery) 실행

STOP 파일이 생길 때까지 epoch 를 무한 반복하며 SSTR2-선택성 후보를 누적 발굴한다. run 간 학습은
디스크에 영속된다 (`experiment_log.jsonl` 서열 dedup·bandit + `global_selectivity_leaderboard.json`
Δmargin + `baseline_cache.json` native baseline 1회 측정 후 재사용). 상세: [`_workspace/CONTINUOUS_DISCOVERY.md`](_workspace/CONTINUOUS_DISCOVERY.md).

**전제**: vLLM(Qwen3-32B)이 `localhost:8000`에 떠 있어야 한다.

#### 백그라운드 실행 — 방법 1: tmux (권장, 재접속 가능·SSH 끊겨도 유지)

```bash
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

tmux new -s discovery          # 세션 생성 후, 세션 안에서:
~/miniforge3/envs/bio-tools/bin/python scripts/run_continuous_discovery.py \
  --input data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb \
  --n-candidates 8 --max-iterations 4 --top-k 5 --selectivity-max-per-iter 2 \
  2>&1 | tee runs/pyrosetta_flow/discovery_run.log

# 빠져나오기: Ctrl+b 누른 뒤 d   |   재접속: tmux attach -t discovery
```

#### 백그라운드 실행 — 방법 2: nohup

```bash
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
nohup ~/miniforge3/envs/bio-tools/bin/python scripts/run_continuous_discovery.py \
  --input data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb \
  --n-candidates 8 --max-iterations 4 --top-k 5 --selectivity-max-per-iter 2 \
  > runs/pyrosetta_flow/discovery_run.log 2>&1 &
echo $! > runs/pyrosetta_flow/discovery.pid    # PID 저장
```

#### 모니터링 / 정지 / 실시간 조절

```bash
# 진행 로그 / 상태 요약(역대 best Δmargin, 통과 수, 다양성 레벨)
tail -f runs/pyrosetta_flow/discovery_run.log
cat runs/pyrosetta_flow/discovery_status.json | python -m json.tool

# 정지 (graceful — 현재 epoch 마치고 멈춤)
touch _workspace/STOP_DISCOVERY
#   ※ 다시 돌리기 전 반드시 삭제:  rm _workspace/STOP_DISCOVERY
# 강제 종료(nohup): kill $(cat runs/pyrosetta_flow/discovery.pid)

# 실시간 조절 (재시작 불필요, 다음 epoch 부터 반영)
$EDITOR _workspace/discovery_control.json   # n_candidates, max_iterations, patience 등
```

| 동작 | 명령 |
|------|------|
| 정지 (graceful) | `touch _workspace/STOP_DISCOVERY` |
| 재개 전 정리 | `rm _workspace/STOP_DISCOVERY` |
| 실시간 튜닝 | `_workspace/discovery_control.json` 편집 |
| 진행 모니터 | `runs/pyrosetta_flow/discovery_status.json` |

> **성공 기준**: Δmargin>0 (native SST-14 초과 선택성) & ΔG≤−15 & 독성≤native(hc50). epoch 당 ~1~1.5시간(8후보×4iter), 하룻밤 ~10–15 epoch 누적.

### 프로젝트 구조

```
AG_src/                 # 핵심 파이프라인 소스
  agents/               # 5개 에이전트 (Planner, QCRanker 등)
  config/               # 파이프라인 및 게이트 임계값 설정
  pipeline/             # 단계별 구현 (step01-09)
  schemas/              # 데이터 스키마 (io_schemas, rank_table)
  scripts/              # 독립 PyRosetta 스크립트
frontend/               # React 19 / TypeScript 대시보드 (Vite)
  src/
    components/         # UI 컴포넌트 (CandidateTable, MoleculeViewer 등)
      __tests__/        # 컴포넌트 테스트 (Vitest + RTL)
    hooks/              # 커스텀 훅 6개
      __tests__/        # 훅 테스트
    contexts/           # PipelineContext (전역 상태)
    types/              # TypeScript 타입 정의
backend/                # FastAPI API 서버
  routers/              # 6개 라우터 모듈
    admet.py            #   ADMET 예측
    analysis.py         #   분석 엔드포인트
    experiment.py       #   실험 관리 (watchdog 포함)
    static.py           #   정적 파일 서빙
    status.py           #   파이프라인 상태
    validation.py       #   통합 검증
pyrosetta_flow/         # PyRosetta mutate→dock→ddG 파이프라인
  tests/                # pytest 스위트 (118 tests, 93% coverage)
runs/                   # 파이프라인 출력 (실행별 결과)
run_pipeline_live.py    # 메인 파이프라인 진입점
ARCHITECTURE.md         # 듀얼 파이프라인 아키텍처 설계 문서
```

### 테스트

```bash
# 프론트엔드 (32 tests — Vitest + React Testing Library)
cd frontend && npx vitest run

# 백엔드 + 파이프라인 (118 tests — pytest)
python -m pytest pyrosetta_flow/tests/ -v
```

### 프론트엔드 훅

| 훅 | 역할 |
|------|------|
| `useSelection` | 후보 선택 상태 관리 |
| `useCandidateSort` | 테이블 정렬 로직 |
| `useAdmetBatch` | ADMET 일괄 예측 |
| `useValidation` | 검증 데이터 관리 |
| `usePipelineStatus` | 파이프라인 상태 폴링 (AbortController) |
| `useExperiment` | 실험 실행/모니터링 |

### MoleculeViewer (Mol* v5.6.1)

4가지 뷰 모드: `default` | `cartoon` | `ball-and-stick` | `surface`
— `plugin.managers.structure.component.applyPreset()` API 사용

### PyRosetta Notebook Fitted Flow

`PRST_N_FM/notebooks/SSTR2_SST14_demo.ipynb`의 mutation 실험 흐름을
`mutate -> dock -> ddG` 기준으로 agentic loop에 이식한 경로입니다.
Planner가 iteration별 목표 모드를 선택(`ddg_only` 또는 `ddg_plus_constraints`)하고,
Critic/Reporter가 결과 분석과 기록을 수행합니다.

```bash
# dedicated runner
python scripts/run_pyrosetta_flow.py \
  --input <template_complex.pdb> \
  --n-candidates 8 \
  --max-iterations 2 \
  --objective-mode auto \
  --top-k 5 \
  --output-json runs/pyrosetta_flow/pyrosetta_flow_artifacts.json

# entrypoint flag wiring
python run_pipeline_live.py \
  --enable-pyrosetta-flow \
  --pyrosetta-input <template_complex.pdb>
```

산출물은 JSON artifact(`runs/pyrosetta_flow/pyrosetta_flow_artifacts.json`)로 저장됩니다.
