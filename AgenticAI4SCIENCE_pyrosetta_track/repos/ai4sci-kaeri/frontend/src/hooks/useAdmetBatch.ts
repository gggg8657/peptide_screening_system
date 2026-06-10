import { useState, useEffect, useRef, useMemo } from 'react'
import type { Candidate, AdmetFullResult } from '../types'

export interface UseAdmetBatchReturn {
  admetData: Map<string, AdmetFullResult>
  error: string | null
}

export function useAdmetBatch(candidates: Candidate[]): UseAdmetBatchReturn {
  const [admetData, setAdmetData] = useState<Map<string, AdmetFullResult>>(new Map())
  const [error, setError] = useState<string | null>(null)
  const admetFetchedRef = useRef<string>('')

  const uniqueSequences = useMemo(
    () => [...new Set(candidates.map(c => c.sequence).filter(Boolean))].sort(),
    [candidates],
  )
  const seqKey = uniqueSequences.join(',')

  /* eslint-disable react-hooks/set-state-in-effect -- clear error before fetch lifecycle */
  useEffect(() => {
    if (uniqueSequences.length === 0 || seqKey === admetFetchedRef.current) return
    admetFetchedRef.current = seqKey

    const controller = new AbortController()
    setError(null)
    fetch('/api/admet/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequences: uniqueSequences }),
      signal: controller.signal,
    })
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(data => {
        if (!data?.results) return
        const map = new Map<string, AdmetFullResult>()
        for (const r of data.results as AdmetFullResult[]) {
          if (r.sequence) map.set(r.sequence, r)
        }
        setAdmetData(map)
      })
      .catch(err => {
        if (err.name !== 'AbortError') setError('ADMET data fetch failed')
      })

    return () => controller.abort()
  }, [seqKey, uniqueSequences])
  /* eslint-enable react-hooks/set-state-in-effect */

  return { admetData, error }
}
