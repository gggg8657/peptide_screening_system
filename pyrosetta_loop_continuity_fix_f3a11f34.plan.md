---
name: PyRosetta Loop Continuity Fix
overview: 실패 후에도 iteration을 계속 진행하도록 실행 정책을 강화하고, Planner를 PyRosetta 전용 컨텍스트로 제한해 RFdiffusion/MPNN 언급을 제거합니다. 동시에 스텝별 아웃풋/3D 확인 루틴을 표준화합니다.
todos:
  - id: loop-continue-policy
    content: Rosetta 실패를 run 중단이 아닌 per-candidate 실패로 처리하고 5회 iteration 연속 실행 보장
    status: in_progress
  - id: planner-pyrosetta-scope
    content: Planner 프롬프트/스키마를 PyRosetta-only 문맥으로 제한하여 RFdiffusion/MPNN 언급 제거
    status: pending
  - id: cli-planner-mode
    content: run_pyrosetta_flow CLI에 planner mode 전달 인자 추가
    status: pending
  - id: artifact-visibility-check
    content: 스텝별 산출물 및 3D 확인 루틴 검증/정리
    status: pending
  - id: e2e-iter5-validation
    content: 5회 실행 E2E로 timeline/iterations/문구 정합성 검증
    status: pending
isProject: false
---

# PyRosetta 실패 연속 실행 + Planner 컨텍스트 정합성 계획

## 확인된 원인

- 현재 `pyrosetta_flow/runner.py`에서 Rosetta 단계 예외 시 `break`로 루프를 끊기 때문에, `max_iterations=5`여도 1회차 실패 후 종료됩니다.
- `PlannerAgent`는 공용 프롬프트/스키마(전체 파이프라인: RFdiffusion/ProteinMPNN 포함)를 사용해, PyRosetta-only 실행에서도 해당 용어를 말합니다.
- 스텝 아웃풋은 이미 파일로 생성되며, 대표 경로는 아래와 같습니다.
  - 도킹 구조: `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/cand_YYY.pdb`
  - 3D 렌더 스크립트: `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/07_viz/*_render.pml`
  - 리포트: `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/08_reports/summary.md`, `rank_table.csv`

## 구현 계획

- `pyrosetta_flow/runner.py`
  - Rosetta candidate refine 실패를 per-candidate 실패로 기록하고 다음 candidate/다음 iteration으로 계속 진행하도록 예외 처리 재구성
  - iteration 레벨에서 실패 요약만 남기고 루프는 끝까지 수행
  - `summary.run_status`를 전체 run 기준(부분실패 허용)으로 재정의하고, `timeline`에 `continue_to_next_iteration` 이벤트 추가
- `AG_src/agents/planner.py` (+ 필요 시 `AG_src/llm/prompts.py`)
  - PyRosetta-only 모드 입력 플래그를 지원하고, 해당 모드에서 허용된 액션/용어를 mutate->dock/QC/critic/reporter로 제한
  - 금지 키워드(RFdiffusion, ProteinMPNN, ESMFold 등) 필터링/후처리 적용
- `scripts/run_pyrosetta_flow.py`
  - Planner 모드 선택 인자(예: `--planner-mode pyrosetta-only`)를 추가해 실행 시 명시적으로 주입
- 결과 확인 UX 정리(문서/가이드)
  - 3D 확인 절차를 고정
    - PyMOL GUI: `pymol runs/.../iter_XX/cand_YYY.pdb`
    - 렌더 재생성: `pymol -c runs/.../iter_XX/07_viz/*_render.pml`
  - API 상태 확인: `http://localhost:8787/api/status`의 `timeline`, `rosetta_substeps`, `historical_candidates`

## 검증

- 5회 루프 강제 검증
  - `--max-iterations 5` 실행 후 결과 JSON의 `iterations` 길이와 `timeline` iteration 카운트가 5인지 확인
- Planner 문구 검증
  - 각 iteration hypothesis에서 RFdiffusion/ProteinMPNN 키워드 미출현 확인
- 산출물 검증
  - 최소 1개 iteration에서 `cand_*.pdb`, `*_render.pml`, `summary.md`, `rank_table.csv` 존재 확인
- 정적 검증
  - `python -m compileall pyrosetta_flow AG_src scripts`

