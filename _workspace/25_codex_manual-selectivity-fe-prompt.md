# Manual Selectivity 페이지 — FE 구현 (Phase 1+2)

## 설계서
`/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/release/sod-2026-05-15-flexpepdock-selectivity-page-design.md`

## BE 스키마 (PR #41로 머지됨, main에 반영)

### endpoints (모두 `/api/flexpepdock/` prefix)
```
POST   /jobs                    # 201, body: FlexPepDockJobRequest, resp: { job_id, eta_seconds, queue_position }
GET    /jobs?status=...          # 200, resp: { jobs: list[FlexPepDockJobSummary] }
GET    /jobs/{job_id}            # 200, resp: full state (request + status + progress + eta + result if done)
GET    /jobs/{job_id}/results    # 200, resp: { selectivity_matrix, selectivity_index, pdb_paths }
GET    /jobs/{job_id}/ensemble.tar.gz   # 200, FileResponse
DELETE /jobs/{job_id}            # 200, queued|running → 취소
```

### request schema (POST /jobs body)
```python
class FlexPepDockConfig:
    cycles: int = 10           # 1~200
    nstruct: int = 50          # 1~500
    flex_pep_freedom: "low" | "med" | "high" = "med"
    ddg_cycle: int = 5         # 1~50

class FlexPepDockJobRequest:
    sequence: str              # 14aa, Cys3-Cys14 SS bond 검증
    receptors: list[Literal["SSTR1","SSTR2","SSTR3","SSTR4","SSTR5"]]  # min 1
    config: FlexPepDockConfig = default
```

### status state machine
`queued` → `running` → `done` | `failed` | `cancelling` → `cancelled`

### POST /jobs 응답
```json
{ "job_id": "<uuid>", "eta_seconds": 1800, "queue_position": 1 }
```

### GET /jobs/{id} 응답 (예시)
```json
{
  "job_id": "<uuid>",
  "sequence": "AGCKNFFWKTFTSC",
  "receptors": ["SSTR1","SSTR2"],
  "config": {...},
  "state": "running",
  "progress": 0.45,
  "eta_seconds": 600,
  "created_at": "2026-05-15T03:00:00Z",
  "started_at": "2026-05-15T03:00:30Z",
  "result": null
}
```

### GET /jobs/{id}/results 응답 (state=done 시)
```json
{
  "selectivity_matrix": [
    { "receptor": "SSTR1", "dG_kcal_mol": -8.2, "interface_score": -42.5, "pass": false },
    { "receptor": "SSTR2", "dG_kcal_mol": -11.5, "interface_score": -68.3, "pass": true }
  ],
  "selectivity_index": 3.3,
  "pdb_paths": ["runs_local/flexpepdock_jobs/<job_id>/ensemble/SSTR2/model_0.pdb"]
}
```

## FE 구현 의뢰

### 1. 신규 페이지 `src/pages/ManualSelectivityPage.tsx`

설계서 §2 UI 구조 그대로 구현:
- **HeuristicBanner** (grade="B") — `FlexPepDock는 in-silico estimation입니다. wet-lab 검증 전까지 Ki 절대값으로 가정하지 마세요.`
- **Section 1: 후보 선택**
  - `ArchivesTopKSlider` (기존 컴포넌트 재사용) — 후보 클릭 시 sequence 자동 채움
  - 수동 입력 textarea (14aa 직접 입력 + validate)
- **Section 2: Receptor + Params**
  - SSTR1-5 체크박스 (5개 모두 default off, 사용자 명시 선택 필요)
  - FlexPepDockConfig 입력 (cycles/nstruct/flex_pep_freedom/ddg_cycle)
- **Section 3: 실행 + 진행**
  - Run 버튼 (sequence+receptors 검증 후 활성)
  - ETA 표시 (POST 응답의 `eta_seconds`)
  - Job 진행률 (polling 또는 SSE — polling 2초 간격 충분)
- **Section 4: 결과**
  - Selectivity Matrix Table (receptor / ΔG / interface_score / pass)
  - Selectivity Index 계산값
  - 버튼: [CSV Export] [PDB ensemble Download] [Wetlab Order 생성]
- **Job 리스트** (페이지 하단 또는 사이드바)
  - GET /jobs 결과 표시, 취소 버튼

### 2. 신규 hook `src/hooks/useFlexPepDockJob.ts`

```ts
export function useCreateFlexPepDockJob() // POST /jobs
export function useFlexPepDockJobs(status?) // GET /jobs?status=
export function useFlexPepDockJob(jobId, { polling: boolean })  // GET /jobs/{id} with 2s polling if state in (queued, running)
export function useFlexPepDockResults(jobId)  // GET /jobs/{id}/results (only when state=done)
export function useCancelFlexPepDockJob()    // DELETE /jobs/{id}
```

### 3. App.tsx NAV_ITEMS 추가
- `{ to: '/manual-selectivity', label: 'Manual Selectivity', icon: FlaskConical }`
- `/manual-selectivity` Route 등록

### 4. wetlab order 통합
- 결과 페이지의 [Wetlab Order 생성] 버튼이 `POST /api/wetlab/orders`에 `flexpepdock_job_id: jobId` 함께 전달
- 기존 `useTransitionWetlabOrder` 또는 `useCreateWetlabOrder` 등 hook 재사용

### 5. 사용자 결정 4건 반영
- 동시 1개 lock — BE에서 큐로 처리됨. FE는 `queue_position` 표시.
- 영구 retention — FE는 retention 표시 없음, 모든 완료 job 표시.
- 동적 ETA — POST 응답 `eta_seconds` 그대로 사용. 매 polling 시 GET 응답의 `eta_seconds` 갱신.
- wetlab 직접 통합 — §4.

## 제약
- **branch 신설**: `feat/manual-selectivity-page`
- **PR title**: `feat(fe): Manual Selectivity Page — FlexPepDock job UI + 결과 매트릭스 + wetlab 통합`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 (특히 `frontend/src/components/__tests__/*.test.tsx`) 손대지 않음
- TypeScript 0 에러
- BE는 `http://localhost:8787` 살아있음 (PR #41 머지됨, 라우터 동작 확인)
- FE는 `http://localhost:5173` Vite dev server 살아있음 (HMR 자동)
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 (`gh pr create`) 후 PR URL + 변경 파일 리스트 + 스모크 테스트 결과 (curl 또는 fetch 호출) 보고
