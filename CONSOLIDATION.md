# 코드베이스 통합 (Consolidation) — 2026-06-09

SSTR2 AI-Scientist 스크리닝 시스템의 중복 코드베이스 통합 결과.

## 통합 후 아키텍처 (SSOT)

```
SST14-M_scr/                                  # 프로젝트 루트
├── AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/   ← ★ SSOT (작동 시스템)
│   ├── AG_src/          # 에이전트(Planner/Critic/Reporter) + 8-step 파이프라인 + LLM provider
│   ├── pyrosetta_flow/  # mutate→dock→ddG 에이전트 루프 (+ multiobjective.py 다목적 통합)
│   ├── backend/         # FastAPI (UI API, 실험 제어, 상태)
│   └── frontend/        # React + Vite 대시보드
├── pipeline_local/      ← 컴퓨트 레이어 (backend 가 런타임 의존)
│   └── scripts/         #   flexpepdock_worker, extract_binding_pocket, stability_predictor ...
├── _backup/orphaned_20260609/   ← 격리된 미사용 코드
│   ├── pipelines/       #   silo_a, silo_b (실행 시스템 미사용, 자기 테스트만 import)
│   └── bionemo/         #   초기 탐색 튜토리얼 (미사용)
└── .venv/               # 전용 가상환경
```

## 두 레이어의 역할
- **ai4sci-kaeri (SSOT)**: UI + LLM 에이전트 오케스트레이션 + 에이전트 도킹 루프. order.txt 우선순위 0.
- **pipeline_local (컴퓨트 레이어)**: backend 의 수동 도구 엔드포인트(flexpepdock 잡 큐, binding pocket 추출, stability 예측)가 import 하는 워커. **실제 런타임 의존성** — 제거 불가.

## 변경 사항

### 1. pipeline_local 의존성 버그 수정 (`backend/state.py`)
- `OUTER_REPO_ROOT`: `REPO_ROOT.parent×4`(=`/tmp`, 오답) → `×3`(=`SST14-M_scr`, pipeline_local 보유).
- `OUTER_REPO_ROOT` 를 `sys.path` 에 **append**(insert(0) 금지 — 최상위 동명 패키지 `pyrosetta_flow`/`scripts` 가 중첩 ai4sci-kaeri 모듈을 shadow 하는 충돌 방지).
- **효과**: 이전엔 `ModuleNotFoundError` 로 깨져 있던 `/api/flexpepdock/*`, `/api/binding_pocket/*`, `/api/stability/*` 엔드포인트가 정상 작동 (HTTP 200 검증).

### 2. orphan 격리
- `pipelines/`(silo_a/b), `bionemo/` → `_backup/orphaned_20260609/`. 실행 시스템이 import 하지 않음(검증됨).

## 미통합 (의도적 보류)
- **pipeline_local 을 ai4sci-kaeri 안으로 물리 병합하지 않음**: 135 모듈의 import 경로 대량 변경 + 동명 패키지 충돌 리스크 대비 ROI 낮음. sibling 컴퓨트 레이어로 유지가 안전.
- **고유 과학 모듈 포팅(선택)**: `pipeline_local/steps/step05c_boltz_cross.py`(오프라인 Boltz 선택성), `pepadmet_ood/`, `strategies/`, `scoring/composite_scorer.py` 는 에이전트 루프로 포팅 시 가치 있음. 향후 enhancement.

## 검증
- 통합 후 `backend.main` + `pyrosetta_flow.runner`(중첩) + `pipeline_local.scripts.*`(최상위) 모두 정상 import.
- backend 83 routes, `/api/flexpepdock/jobs` 200, `/api/status` 200.
