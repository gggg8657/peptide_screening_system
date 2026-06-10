import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

export type FlexPepDockFreedom = 'low' | 'med' | 'high'
export type FlexPepDockReceptor = 'SSTR1' | 'SSTR2' | 'SSTR3' | 'SSTR4' | 'SSTR5'
export type FlexPepDockJobState = 'queued' | 'running' | 'done' | 'failed' | 'cancelling' | 'cancelled'

export interface FlexPepDockConfig {
  cycles: number
  nstruct: number
  flex_pep_freedom: FlexPepDockFreedom
  ddg_cycle: number
}

export interface FlexPepDockJobRequest {
  sequence: string
  receptors: FlexPepDockReceptor[]
  config: FlexPepDockConfig
}

export interface FlexPepDockJobCreateResponse {
  job_id: string
  eta_seconds: number
  queue_position: number
}

export interface FlexPepDockJobSummary {
  job_id: string
  sequence: string
  receptors: FlexPepDockReceptor[]
  config: FlexPepDockConfig
  status: FlexPepDockJobState
  progress: number
  eta_seconds: number
  created_at: string
  started_at?: string
  finished_at?: string
  error_message?: string
}

export interface FlexPepDockJobDetail extends FlexPepDockJobSummary {
  queue_position: number
}

export interface FlexPepDockJobsResponse {
  jobs: FlexPepDockJobSummary[]
}

export interface FlexPepDockMatrixRow {
  receptor: FlexPepDockReceptor
  dG_kcal_mol: number
  interface_score: number
  pass: boolean
  /** BE가 stub fallback(PyRosetta 미설치/timeout)으로 채운 경우 true */
  stub?: boolean
  /** stub 원인 (예: "PyRosetta 미설치", "timeout") */
  stub_reason?: string
}

export interface FlexPepDockResults {
  selectivity_matrix: FlexPepDockMatrixRow[]
  selectivity_index: number
  pdb_paths: string[]
}

const BASE = '/api/flexpepdock'
const ACTIVE_STATES = new Set<FlexPepDockJobState>(['queued', 'running'])

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json() as { detail?: string }
    return data.detail ?? `${res.status} ${res.statusText}`
  } catch {
    return `${res.status} ${res.statusText}`
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(await readErrorMessage(res))
  return res.json() as Promise<T>
}

async function send<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) throw new Error(await readErrorMessage(res))
  return res.json() as Promise<T>
}

export function useCreateFlexPepDockJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: FlexPepDockJobRequest) =>
      send<FlexPepDockJobCreateResponse>('/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['flexpepdock-jobs'] })
      qc.invalidateQueries({ queryKey: ['flexpepdock-job', data.job_id] })
    },
  })
}

export function useFlexPepDockJobs(status?: FlexPepDockJobState) {
  return useQuery<FlexPepDockJobsResponse>({
    queryKey: ['flexpepdock-jobs', status ?? 'all'],
    queryFn: () => {
      const search = status ? `?status=${status}` : ''
      return get<FlexPepDockJobsResponse>(`/jobs${search}`)
    },
    refetchInterval: (query) => {
      const jobs = query.state.data?.jobs ?? []
      return jobs.some((job) => ACTIVE_STATES.has(job.status)) ? 2000 : 10_000
    },
  })
}

export function useFlexPepDockJob(jobId: string | null | undefined, options?: { polling: boolean }) {
  return useQuery<FlexPepDockJobDetail>({
    queryKey: ['flexpepdock-job', jobId],
    queryFn: () => get<FlexPepDockJobDetail>(`/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      if (!options?.polling) return false
      const state = query.state.data?.status
      return state && ACTIVE_STATES.has(state) ? 2000 : false
    },
  })
}

export function useFlexPepDockResults(jobId: string | null | undefined) {
  return useQuery<FlexPepDockResults>({
    queryKey: ['flexpepdock-results', jobId],
    queryFn: () => get<FlexPepDockResults>(`/jobs/${jobId}/results`),
    enabled: !!jobId,
    staleTime: 60_000,
  })
}

export function useCancelFlexPepDockJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) =>
      send<{ ok: boolean; job_id: string; action: string }>(`/jobs/${jobId}`, {
        method: 'DELETE',
      }),
    onSuccess: (_data, jobId) => {
      qc.invalidateQueries({ queryKey: ['flexpepdock-jobs'] })
      qc.invalidateQueries({ queryKey: ['flexpepdock-job', jobId] })
      qc.invalidateQueries({ queryKey: ['flexpepdock-results', jobId] })
    },
  })
}

/**
 * selectivity_matrix 에 stub 항목이 하나라도 있으면 true.
 * BE 구 router 시기(PyRosetta 미설치/timeout) 생성 결과 식별용.
 */
export function isStubResults(results: FlexPepDockResults): boolean {
  return results.selectivity_matrix.some((row) => row.stub === true)
}

/**
 * 완료(done) job ID 목록에 대해 각 job의 stub 여부를 병렬로 조회한다.
 *
 * - 이미 캐시된 results는 재요청 없이 재사용 (staleTime: 60s).
 * - 결과를 아직 불러오는 중이면 해당 job ID의 값이 undefined.
 *
 * @returns `Record<jobId, boolean | undefined>`
 *   - true  → stub 결과 (구 router / PyRosetta fallback)
 *   - false → 실 PyRosetta 결과
 *   - undefined → 로딩 중 또는 오류
 */
export function useJobsStubStatus(doneJobIds: string[]): Record<string, boolean | undefined> {
  const queries = useQueries({
    queries: doneJobIds.map((id) => ({
      queryKey: ['flexpepdock-results', id],
      queryFn: () => get<FlexPepDockResults>(`/jobs/${id}/results`),
      staleTime: 60_000,
    })),
  })

  return Object.fromEntries(
    doneJobIds.map((id, index) => {
      const data = queries[index].data
      return [id, data !== undefined ? isStubResults(data) : undefined]
    }),
  )
}
