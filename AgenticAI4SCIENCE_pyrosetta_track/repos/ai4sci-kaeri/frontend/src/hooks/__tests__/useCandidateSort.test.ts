import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useCandidateSort } from '../useCandidateSort'
import type { Candidate } from '../../types'

function makeCandidates(n: number): Candidate[] {
  return Array.from({ length: n }, (_, i) => ({
    rank: i + 1,
    id: `cand-${i}`,
    sequence: `SEQ${i}`,
    ddG: -(10 + i * 5),
    totalScore: -(500 + i * 10),
    clashScore: i * 2,
    finalScore: 30 - i,
    result: i % 3 === 0 ? 'PASS' as const : i % 3 === 1 ? 'FAIL' as const : 'REF' as const,
  }))
}

describe('useCandidateSort', () => {
  const candidates = makeCandidates(5)

  it('initializes with rank ascending sort', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))
    expect(result.current.sortKey).toBe('rank')
    expect(result.current.sortDir).toBe('asc')
  })

  it('toggles sort direction on same key', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))

    act(() => result.current.handleSort('rank'))
    expect(result.current.sortDir).toBe('desc')

    act(() => result.current.handleSort('rank'))
    expect(result.current.sortDir).toBe('asc')
  })

  it('changes key and resets to asc', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))

    act(() => result.current.handleSort('ddG'))
    expect(result.current.sortKey).toBe('ddG')
    expect(result.current.sortDir).toBe('asc')
  })

  it('resets page on sort change', () => {
    const { result } = renderHook(() => useCandidateSort(makeCandidates(30)))

    act(() => result.current.setPage(2))
    expect(result.current.page).toBe(2)

    act(() => result.current.handleSort('ddG'))
    expect(result.current.page).toBe(0)
  })

  it('filters by result', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))

    act(() => result.current.setFilter('PASS'))
    expect(result.current.sorted.every(c => c.result === 'PASS')).toBe(true)

    act(() => result.current.setFilter('FAIL'))
    expect(result.current.sorted.every(c => c.result === 'FAIL')).toBe(true)
  })

  it('sorted output is actually sorted', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))

    act(() => result.current.handleSort('ddG'))
    const ddGs = result.current.sorted.map(c => c.ddG)
    for (let i = 1; i < ddGs.length; i++) {
      expect(ddGs[i]).toBeGreaterThanOrEqual(ddGs[i - 1])
    }
  })

  it('computes passCount, failCount, refCount correctly', () => {
    const { result } = renderHook(() => useCandidateSort(candidates))
    // indices: 0=PASS, 1=FAIL, 2=REF, 3=PASS, 4=FAIL
    expect(result.current.passCount).toBe(2)
    expect(result.current.failCount).toBe(2)
    expect(result.current.refCount).toBe(1)
  })

  it('paged returns correct page slice', () => {
    const big = makeCandidates(25)
    const { result } = renderHook(() => useCandidateSort(big))

    expect(result.current.paged.length).toBe(12) // PAGE_SIZE=12
    expect(result.current.totalPages).toBe(3)

    act(() => result.current.setPage(2))
    expect(result.current.paged.length).toBe(1) // 25 - 24 = 1
  })
})
