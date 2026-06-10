import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useValidation } from '../useValidation'

describe('useValidation', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts with empty results and not validating', () => {
    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set<string>() }),
    )
    expect(result.current.validationResults.size).toBe(0)
    expect(result.current.validating).toBe(false)
  })

  it('does nothing when selectedIds is empty', async () => {
    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set<string>() }),
    )

    await act(async () => {
      await result.current.handleValidate()
    })

    expect(fetch).not.toHaveBeenCalled()
    expect(result.current.validating).toBe(false)
  })

  it('sets validating=true during fetch, then false after', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        results: [{ id: 'a', validation: 'pass', checks: [] }],
      }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set(['a']) }),
    )

    let validatePromise: Promise<void>
    act(() => {
      validatePromise = result.current.handleValidate()
    })

    expect(result.current.validating).toBe(true)

    await act(async () => {
      await validatePromise!
    })

    expect(result.current.validating).toBe(false)
  })

  it('sends correct POST request', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: [] }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set(['x', 'y']), archiveRunId: 'run-1' }),
    )

    await act(async () => {
      await result.current.handleValidate()
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/validate/selected', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: expect.any(String),
    })

    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.candidate_ids).toEqual(expect.arrayContaining(['x', 'y']))
    expect(body.run_id).toBe('run-1')
  })

  it('stores validation results on success', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        results: [
          { id: 'a', validation: 'pass', checks: [{ rule: 'FWKT', value: 1, passed: true }] },
          { id: 'b', validation: 'fail', checks: [{ rule: 'FWKT', value: 0, passed: false }] },
        ],
      }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set(['a', 'b']) }),
    )

    await act(async () => {
      await result.current.handleValidate()
    })

    expect(result.current.validationResults.size).toBe(2)
    expect(result.current.validationResults.get('a')?.validation).toBe('pass')
    expect(result.current.validationResults.get('b')?.validation).toBe('fail')
  })

  it('clears pending state on fetch error', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('network'))
    vi.stubGlobal('fetch', mockFetch)

    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set(['a']) }),
    )

    await act(async () => {
      await result.current.handleValidate()
    })

    expect(result.current.validating).toBe(false)
    expect(result.current.validationResults.size).toBe(0)
  })

  it('calls onValidationComplete after success', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: [] }),
    })
    vi.stubGlobal('fetch', mockFetch)
    const onComplete = vi.fn()

    const { result } = renderHook(() =>
      useValidation({ selectedIds: new Set(['a']), onValidationComplete: onComplete }),
    )

    await act(async () => {
      await result.current.handleValidate()
    })

    expect(onComplete).toHaveBeenCalledTimes(1)
  })
})
