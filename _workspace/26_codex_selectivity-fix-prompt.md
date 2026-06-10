# Selectivity Fix — useSelectivity hook 재설계

## 문제
`AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/src/hooks/dashboard.ts:303-309` 의 `useSelectivity(runId)` hook이 다음을 호출:
```ts
get(`/selectivity/${runId}`)
```

그러나 backend (`AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/selectivity.py`)는 다음만 제공:
- `GET /selectivity/receptors`
- `GET /selectivity/structure/{receptor_name}`
- `GET /selectivity/status/{job_id}`
- `GET /selectivity/results/{job_id}`
- `GET /selectivity/jobs`

따라서 `/selectivity/{runId}` 호출은 **404**. SelectivityExplorerPage 사용 불가.

## 해결 방향 (사용자 결정 채택)
**옵션 B**: FE `useSelectivity`를 재설계. archive JSON (`/api/runs/{run_id}` 응답) 에 이미 selectivity 데이터가 있을 것으로 추정. backend가 새 endpoint 만들 필요 없음.

## 의뢰
1. **archive JSON에 selectivity 데이터가 있는지 확인** — `runs_local/sst14_mutdock_9999/` (또는 다른 archive run) 디렉토리에서 selectivity 결과 파일 찾고 `/api/runs/{run_id}` 응답에 포함되는지 검증.
2. **포함되어 있다면**: `useSelectivity` 를 `useRunStatus` 또는 `useCandidates` 응답에서 selectivity 필드 추출하도록 재설계 (별도 fetch 없이 `useQuery` 데이터 변환).
3. **포함되어 있지 않다면**: `backend/routers/dashboard.py` (또는 `backend/main.py`)의 `/api/runs/{run_id}` 응답에 selectivity 필드 추가. 그리고 `useSelectivity`를 그 필드 사용하도록 변경.
4. **SelectivityExplorerPage** 가 `useSelectivity` 결과를 어떻게 쓰는지 확인하고 새 데이터 형식이 일치하도록 조정.

## TypeScript 타입 정의 위치
- `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/src/types/` 또는 `hooks/dashboard.ts` 내 inline type

## 검증
- `npx tsc --noEmit` 0 에러
- BE는 `OLLAMA_HOST=127.0.0.1:11435 PYTHONPATH=.:/home/dongjukim/Documents/workspace/repos/SST14-M_scr conda run --no-capture-output -n bio-tools uvicorn backend.main:app --host 127.0.0.1 --port 8787` 로 실행 중 (`http://localhost:8787`)
- `curl http://localhost:8787/api/runs/sst14_mutdock_9999 | jq 'keys'` 로 응답 스키마 확인
- FE는 :5173 Vite HMR로 자동 반영. 변경 후 SelectivityExplorerPage 가 404 없이 데이터 표시.

## 제약
- 본 세션 컨벤션: 다른 세션 미커밋 파일 (예: `frontend/src/components/__tests__/*.test.tsx`) 손대지 않음
- branch 신설: `fix/selectivity-endpoint`
- PR title: `fix(fe): useSelectivity 재설계 — archive JSON 필드 사용으로 404 해결`
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
