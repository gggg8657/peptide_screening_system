import { useState, useCallback } from 'react'
import type { ValidationResult } from '../types'

export interface UseValidationReturn {
  validationResults: Map<string, ValidationResult>
  validating: boolean
  handleValidate: () => Promise<void>
}

export function useValidation(options: {
  selectedIds: Set<string>
  archiveRunId?: string | null
  onValidationComplete?: () => void
}): UseValidationReturn {
  const { selectedIds, archiveRunId, onValidationComplete } = options
  const [validationResults, setValidationResults] = useState<Map<string, ValidationResult>>(new Map())
  const [validating, setValidating] = useState(false)

  const handleValidate = useCallback(async () => {
    if (selectedIds.size === 0) return
    setValidating(true)
    const ids = Array.from(selectedIds)

    // Mark as pending
    setValidationResults(prev => {
      const next = new Map(prev)
      ids.forEach(id => next.set(id, { id, validation: 'pending', checks: [] }))
      return next
    })

    try {
      const res = await fetch('/api/validate/selected', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: ids, ...(archiveRunId ? { run_id: archiveRunId } : {}) }),
      })
      if (res.ok) {
        const data = await res.json()
        const results: ValidationResult[] = data.results ?? []
        setValidationResults(prev => {
          const next = new Map(prev)
          results.forEach(r => next.set(r.id, r))
          return next
        })
      }
    } catch {
      // On error, clear pending state
      setValidationResults(prev => {
        const next = new Map(prev)
        ids.forEach(id => next.delete(id))
        return next
      })
    } finally {
      setValidating(false)
      onValidationComplete?.()
    }
  }, [selectedIds, archiveRunId, onValidationComplete])

  return { validationResults, validating, handleValidate }
}
