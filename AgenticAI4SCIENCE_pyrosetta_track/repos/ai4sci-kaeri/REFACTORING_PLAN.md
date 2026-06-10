# Refactoring Plan — AI-Scientist SSTR2 Pipeline Dashboard

**Status**: COMPLETE (22/22 items done)
**Date**: 2026-03-03 ~ 2026-03-04
**Review Team**: viewer-analyst, frontend-reviewer, backend-reviewer, pipeline-reviewer
**Scope**: Frontend (React/Vite), Backend (Python API), PyRosetta Pipeline

---

## Overview

4-agent 병렬 코드 리뷰를 통해 도출된 리팩토링 계획.
총 22개 이슈, 4단계 우선순위 (Critical → Low). **전체 완료.**

---

## Critical — 즉시 수정

| ID | 영역 | 이슈 | 상태 | 완료일 | 커밋 |
|----|------|------|:----:|--------|------|
| C1 | Backend | Path traversal 취약점 | DONE | 2026-03-03 | `79845a8` |
| C2 | Backend | 캐시 뮤테이션 위험 | DONE | 2026-03-03 | `79845a8` |
| C3 | Pipeline | subprocess timeout 없음 | DONE | 2026-03-03 | `79845a8` |
| C4 | Pipeline | JSON stdout 파싱 미보호 | DONE | 2026-03-03 | `79845a8` |
| C5 | Pipeline | StatusEmitter 파일 잠금 없음 | DONE | 2026-03-03 | `79845a8` |

## High — Sprint 1

| ID | 영역 | 이슈 | 상태 | 완료일 | 커밋 |
|----|------|------|:----:|--------|------|
| H1 | 3D Viewer | 아카이브 모드 3D 버튼 | DONE | 2026-03-03 | `860472a` |
| H2 | Frontend | 폴링 레이스 컨디션 | DONE | 2026-03-03 | `99104a7` |
| H3 | Frontend | CandidateTable 분리 (useCandidateSort, useAdmetBatch) | DONE | 2026-03-03 | `99104a7` |
| H4 | Backend | FastAPI 마이그레이션 (6 라우터) | DONE | 2026-03-03 | `10bdc03` |
| H5 | Backend | Validation 엔드포인트 통합 | DONE | 2026-03-03 | `10bdc03` |
| H6 | Pipeline | pytest 스위트 (118 tests, 93% cov) | DONE | 2026-03-03 | `10bdc03` |

## Medium — Sprint 2

| ID | 영역 | 이슈 | 상태 | 완료일 | 커밋 |
|----|------|------|:----:|--------|------|
| M1 | Frontend | PipelineContext 도입 | DONE | 2026-03-03 | `99104a7` |
| M2 | Frontend | 접근성 보완 | DONE | 2026-03-03 | `99104a7` |
| M3 | Frontend | 미사용 mockData.ts 삭제 | DONE | 2026-03-03 | `99104a7` |
| M4 | Backend | JSON 에러 응답 표준화 | DONE | 2026-03-03 | `10bdc03` |
| M5 | Backend | Status 스키마 검증 | DONE | 2026-03-03 | `10bdc03` |
| M6 | Pipeline | 매직 넘버 ConfigClass 추출 | DONE | 2026-03-03 | `10bdc03` |
| M7 | Pipeline | 듀얼 아키텍처 설계 문서 | DONE | 2026-03-04 | `1e1f906` |

## Low — Sprint 3

| ID | 영역 | 이슈 | 상태 | 완료일 | 커밋 |
|----|------|------|:----:|--------|------|
| L1 | Frontend | MetricCard React.memo | DONE | 2026-03-03 | `99104a7` |
| L2 | Frontend | 색상/폰트 통일 | DONE | 2026-03-03 | `99104a7` |
| L3 | Backend | 실험 watchdog + zombie reap | DONE | 2026-03-04 | `ed290aa` |
| L4 | Pipeline | 아카이브 PDB 포함 | DONE | 2026-03-03 | `e4fb807` |

---

## 코드 품질 메트릭 (시작 → 최종)

| 메트릭 | 시작 | 최종 |
|--------|------|------|
| Backend 파일 수 | 1 (735줄) | 8 (main.py + 6 routers + __init__) |
| Frontend 최대 컴포넌트 | 708줄 | ~300줄 (훅 추출) |
| pyrosetta_flow 테스트 커버리지 | 0% | 93% (118 tests) |
| Frontend 테스트 | 0 | 32 tests (Vitest + RTL) |
| 보안 취약점 | 2 (path traversal) | 0 |

---

## 추가 작업 (리팩토링 이후 완료)

| 작업 | 완료일 | 커밋 |
|------|--------|------|
| Vitest 인프라 + 32 프론트엔드 테스트 | 2026-03-04 | `3f95506` |
| MoleculeViewer 4-mode preset 수정 | 2026-03-04 | `3c05269` |
| Mol* applyPreset API 수정 | 2026-03-04 | `3ea0f2e` |
| Legacy server 제거 | 2026-03-04 | `ed290aa` |

---

## 참고: 리뷰 발견사항 상세

### 3D Viewer (Mol*)
- Mol* v5.6.1 정상 설치, MoleculeViewer 코드 정상
- **근본 원인**: 아카이브에 PDB 파일 미포함 → 404 (L4에서 해결)
- 4가지 뷰 모드 (default, cartoon, ball-and-stick, surface) 정상 작동

### Frontend (React 19 + TypeScript)
- CandidateTable → 훅 추출로 ~300줄 축소 (H3)
- 6개 커스텀 훅: useSelection, useCandidateSort, useAdmetBatch, useValidation, usePipelineStatus, useExperiment
- PipelineContext 도입 (M1), 접근성 보강 (M2)
- 32 Vitest 테스트 (hooks + CandidateTable)

### Backend (FastAPI)
- 6개 라우터 모듈 (admet, analysis, experiment, static, status, validation)
- path traversal 수정 (C1), 캐시 deepcopy (C2)
- 통합 validation facade (H5), JSON 에러 표준화 (M4)
- 실험 watchdog + zombie reap (L3)

### Pipeline (pyrosetta_flow)
- subprocess timeout 추가 (C3), JSON 파싱 보호 (C4)
- StatusEmitter fcntl.flock (C5)
- 118 pytest tests, 93% coverage (H6)
- ConfigClass/YAML 매직 넘버 추출 (M6)
- ARCHITECTURE.md 듀얼 파이프라인 설계 문서 (M7)
