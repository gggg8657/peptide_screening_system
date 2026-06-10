import { useState, useMemo } from 'react'
import type { Candidate } from '../types'

export type SortKey = keyof Pick<Candidate, 'rank' | 'ddG' | 'totalScore' | 'clashScore' | 'finalScore'>
export type SortDir = 'asc' | 'desc'
export type FilterValue = 'all' | 'PASS' | 'FAIL' | 'REF'

const PAGE_SIZE = 12

export interface UseCandidateSortReturn {
  sortKey: SortKey
  sortDir: SortDir
  filter: FilterValue
  setFilter: (f: FilterValue) => void
  page: number
  setPage: (p: number | ((prev: number) => number)) => void
  handleSort: (key: SortKey) => void
  sorted: Candidate[]
  paged: Candidate[]
  totalPages: number
  passCount: number
  failCount: number
  refCount: number
}

export function useCandidateSort(candidates: Candidate[]): UseCandidateSortReturn {
  const [sortKey, setSortKey] = useState<SortKey>('rank')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [filter, setFilter] = useState<FilterValue>('all')
  const [page, setPage] = useState(0)

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
    setPage(0)
  }

  const sorted = useMemo(() => {
    const filtered = filter === 'all' ? candidates : candidates.filter(c => c.result === filter)
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] as number
      const bv = b[sortKey] as number
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [sortKey, sortDir, filter, candidates])

  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const passCount = candidates.filter(c => c.result === 'PASS').length
  const failCount = candidates.filter(c => c.result === 'FAIL').length
  const refCount = candidates.filter(c => c.result === 'REF').length

  return {
    sortKey, sortDir, filter, setFilter,
    page, setPage, handleSort,
    sorted, paged, totalPages,
    passCount, failCount, refCount,
  }
}
