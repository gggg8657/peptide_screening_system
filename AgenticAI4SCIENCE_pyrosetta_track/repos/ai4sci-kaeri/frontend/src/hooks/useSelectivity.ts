import { useState, useCallback, useRef, useEffect } from 'react'

const RECEPTOR_NAMES = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const
export const OFFTARGET_RECEPTORS = ['sstr1', 'sstr3', 'sstr4', 'sstr5'] as const

export interface ReceptorStatus {
  name: string
  loaded: boolean
  fileName?: string
  format?: string
  pdb_id?: string
  size_kb?: number
}

export type ReceptorDockResult = {
  ddg: number | null       // null = 도킹 안 됨
  status: 'done' | 'failed' | 'pending'
  failReason?: string      // 실패 이유
}

export interface SelectivityResult {
  seq_id: string
  candidate_id: string
  sequence: string
  sstr2_ddg: number
  offtarget_scores: Record<string, number>
  receptorDetails: Record<string, ReceptorDockResult>  // 수용체별 상세
  offtarget_max_receptor: string
  offtarget_max_score: number
  selectivity_margin: number
  tier: number
  gate_pass: boolean
  mode: string
}

export interface ReceptorProgress {
  name: string
  completed: number
  total: number
}

interface UseSelectivityReturn {
  receptors: ReceptorStatus[]
  candidates: SelectivityResult[]
  isRunning: boolean
  progress: number
  receptorProgress: ReceptorProgress[]
  error: string | null
  uploadReceptor: (target: string, file: File) => Promise<void>
  runAnalysis: (candidateIds: string[], candidateSequences: string[] | Record<string, string>, sstr2Ddgs?: Record<string, number>) => Promise<void>
  stopAnalysis: () => void
  fetchReceptors: () => Promise<void>
}

const DEFAULT_RECEPTORS: ReceptorStatus[] = RECEPTOR_NAMES.map(name => ({
  name,
  loaded: false,
}))

function _mapCandidates(raw: Record<string, unknown>[], mode: string): SelectivityResult[] {
  return raw.map((c) => {
    const ot = (c.offtarget_ddg ?? {}) as Record<string, number>

    // 수용체별 상세 결과
    const receptorDetails: Record<string, ReceptorDockResult> = {}
    for (const r of OFFTARGET_RECEPTORS) {
      if (r in ot) {
        receptorDetails[r] = { ddg: ot[r], status: 'done' }
      } else {
        receptorDetails[r] = { ddg: null, status: 'failed', failReason: 'Docking failed or skipped' }
      }
    }

    return {
      seq_id: (c.seq_id ?? c.candidate_id ?? '') as string,
      candidate_id: (c.seq_id ?? c.candidate_id ?? '') as string,
      sequence: (c.sequence ?? '') as string,
      sstr2_ddg: (c.sstr2_ddg ?? 0) as number,
      offtarget_scores: ot,
      receptorDetails,
      // P14: BE가 min(scores) 기준으로 계산한 worst off-target 사용 (FE 재계산 제거)
      offtarget_max_receptor: (c.offtarget_max_receptor as string) ?? '',
      offtarget_max_score: (c.offtarget_max_score as number) ?? 0,
      selectivity_margin: (c.wsm ?? 0) as number,
      tier: (c.tier ?? 0) as number,
      gate_pass: (c.passed ?? false) as boolean,
      mode,
    }
  })
}

export function useSelectivity(pollInterval = 3000): UseSelectivityReturn {
  const [receptors, setReceptors] = useState<ReceptorStatus[]>(DEFAULT_RECEPTORS)
  const [candidates, setCandidates] = useState<SelectivityResult[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [receptorProgress, setReceptorProgress] = useState<ReceptorProgress[]>([])
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const stoppedRef = useRef(false)
  const jobIdRef = useRef<string | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const fetchReceptors = useCallback(async () => {
    try {
      const res = await fetch('/api/selectivity/receptors')
      if (!res.ok) return
      const data = await res.json()
      if (data?.receptors) {
        const rec = data.receptors as Record<string, { path?: string; format?: string; source?: string; size_bytes?: number }>
        setReceptors(RECEPTOR_NAMES.map(name => {
          const key = name.toLowerCase()
          const found = rec[key]
          return found
            ? { name, loaded: true, fileName: found.path?.split('/').pop(), format: found.format, size_kb: found.size_bytes ? Math.round(found.size_bytes / 1024) : undefined }
            : { name, loaded: false }
        }))
      }
    } catch {
      // ignore
    }
  }, [])

  // Load receptor status on mount
  useEffect(() => {
    fetchReceptors()
  }, [fetchReceptors])

  const uploadReceptor = useCallback(async (target: string, file: File) => {
    setError(null)
    try {
      const formData = new FormData()
      formData.append('target', target)
      formData.append('file', file)
      const res = await fetch('/api/selectivity/upload', { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(err.detail ?? 'Upload failed')
      }
      // Optimistically update local state
      setReceptors(prev => prev.map(r =>
        r.name === target
          ? { ...r, loaded: true, fileName: file.name, format: file.name.endsWith('.pdb') ? 'pdb' : 'cif' }
          : r
      ))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    }
  }, [])

  const startPolling = useCallback((jobId: string) => {
    stopPolling()
    stoppedRef.current = false

    intervalRef.current = setInterval(async () => {
      if (stoppedRef.current) { stopPolling(); return }
      try {
        const res = await fetch(`/api/selectivity/status/${jobId}`)
        if (!res.ok) return
        const data = await res.json()
        const total = data.total_tasks ?? 1
        const completed = data.completed_tasks ?? 0
        setProgress(total > 0 ? Math.round((completed / total) * 100) : 0)

        // 수용체별 진행률 계산 (총 tasks = 후보수 x 수용체수)
        const perReceptor = Math.ceil(total / 4)
        setReceptorProgress(OFFTARGET_RECEPTORS.map((r, idx) => ({
          name: r.toUpperCase(),
          completed: Math.max(0, Math.min(perReceptor, completed - idx * perReceptor)),
          total: perReceptor,
        })))

        if (data.status === 'completed') {
          stopPolling()
          setIsRunning(false)
          setProgress(100)
          // 새 결과를 기존 누적 결과에 머지 (같은 seq_id면 최신 덮어쓰기)
          const rRes = await fetch(`/api/selectivity/results/${jobId}`)
          if (rRes.ok) {
            const rData = await rRes.json()
            if (rData?.candidates) {
              const newResults = _mapCandidates(rData.candidates, rData.mode ?? '')
              setCandidates(prev => {
                const merged = new Map(prev.map(c => [c.seq_id, c]))
                for (const c of newResults) merged.set(c.seq_id, c)
                return [...merged.values()]
              })
            }
          }
        } else if (data.status === 'failed') {
          stopPolling()
          setIsRunning(false)
          setError(data.error ?? 'Analysis failed')
        }
      } catch {
        // network hiccup — keep polling
      }
    }, pollInterval)
  }, [pollInterval, stopPolling])

  // 마운트 시 진행 중인 잡 자동 복구
  useEffect(() => {
    const resumeRunningJob = async () => {
      try {
        const res = await fetch('/api/selectivity/jobs')
        if (!res.ok) return
        const data = await res.json()
        const running = (data.jobs ?? []).find((j: { status: string }) =>
          j.status === 'running' || j.status === 'started'
        )
        // 1) 모든 completed 잡 결과를 항상 누적 로드
        const completedJobs = (data.jobs ?? [])
          .filter((j: { status: string }) => j.status === 'completed')
        if (completedJobs.length > 0) {
          const allMapped: SelectivityResult[] = []
          const seen = new Set<string>()
          for (const job of completedJobs) {
            try {
              const rRes = await fetch(`/api/selectivity/results/${job.job_id}`)
              if (!rRes.ok) continue
              const rData = await rRes.json()
              if (!rData?.candidates) continue
              const mapped = _mapCandidates(rData.candidates, rData.mode ?? '')
              for (const c of mapped) {
                if (!seen.has(c.seq_id)) {
                  seen.add(c.seq_id)
                  allMapped.push(c)
                }
              }
            } catch { /* skip */ }
          }
          if (allMapped.length > 0) setCandidates(allMapped)
        }

        // 2) running 잡이 있으면 polling 시작
        if (running) {
          jobIdRef.current = running.job_id
          setIsRunning(true)
          setProgress(running.progress ?? 0)
          startPolling(running.job_id)
        }
      } catch { /* ignore */ }
    }
    resumeRunningJob()
    return () => stopPolling()
  }, [startPolling, stopPolling])

  const runAnalysis = useCallback(async (candidateIds: string[], candidateSequences: string[] | Record<string, string>, sstr2Ddgs?: Record<string, number>) => {
    setError(null)
    setCandidates([])
    setProgress(0)
    setIsRunning(true)
    try {
      const res = await fetch('/api/selectivity/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_ids: candidateIds,
          candidate_sequences: Array.isArray(candidateSequences)
            ? Object.fromEntries(candidateIds.map((id, i) => [id, candidateSequences[i] ?? '']))
            : candidateSequences,
          sstr2_ddgs: sstr2Ddgs ?? {},
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'Failed to start analysis' }))
        throw new Error(err.error ?? 'Failed to start analysis')
      }
      const data = await res.json()
      jobIdRef.current = data.job_id
      startPolling(data.job_id)
    } catch (e) {
      setIsRunning(false)
      setError(e instanceof Error ? e.message : 'Failed to start analysis')
    }
  }, [startPolling])

  const stopAnalysis = useCallback(() => {
    stoppedRef.current = true
    stopPolling()
    setIsRunning(false)
  }, [stopPolling])

  return { receptors, candidates, isRunning, progress, receptorProgress, error, uploadReceptor, runAnalysis, stopAnalysis, fetchReceptors }
}
