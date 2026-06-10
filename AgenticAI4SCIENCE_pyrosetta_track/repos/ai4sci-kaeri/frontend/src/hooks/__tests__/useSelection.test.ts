import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useSelection } from '../useSelection'

describe('useSelection', () => {
  it('starts with empty selection', () => {
    const { result } = renderHook(() => useSelection())
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('toggleSelect adds and removes an id', () => {
    const { result } = renderHook(() => useSelection())

    act(() => result.current.toggleSelect('a'))
    expect(result.current.selectedIds.has('a')).toBe(true)

    act(() => result.current.toggleSelect('a'))
    expect(result.current.selectedIds.has('a')).toBe(false)
  })

  it('toggleSelectPage selects all when not all selected', () => {
    const { result } = renderHook(() => useSelection())

    act(() => result.current.toggleSelectPage(['a', 'b', 'c']))
    expect(result.current.selectedIds.size).toBe(3)
    expect(result.current.selectedIds.has('a')).toBe(true)
    expect(result.current.selectedIds.has('b')).toBe(true)
    expect(result.current.selectedIds.has('c')).toBe(true)
  })

  it('toggleSelectPage deselects all when all are already selected', () => {
    const { result } = renderHook(() => useSelection())

    act(() => result.current.toggleSelectPage(['a', 'b']))
    expect(result.current.selectedIds.size).toBe(2)

    act(() => result.current.toggleSelectPage(['a', 'b']))
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('clearSelection empties the set', () => {
    const { result } = renderHook(() => useSelection())

    act(() => result.current.toggleSelect('x'))
    act(() => result.current.toggleSelect('y'))
    expect(result.current.selectedIds.size).toBe(2)

    act(() => result.current.clearSelection())
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('calls onSelectionChange callback on toggleSelect', () => {
    const cb = vi.fn()
    const { result } = renderHook(() => useSelection(cb))

    act(() => result.current.toggleSelect('a'))
    expect(cb).toHaveBeenCalledTimes(1)
    expect(cb).toHaveBeenCalledWith(new Set(['a']))
  })

  it('calls onSelectionChange callback on toggleSelectPage', () => {
    const cb = vi.fn()
    const { result } = renderHook(() => useSelection(cb))

    act(() => result.current.toggleSelectPage(['a', 'b']))
    expect(cb).toHaveBeenCalledTimes(1)
    expect(cb).toHaveBeenCalledWith(new Set(['a', 'b']))
  })
})
