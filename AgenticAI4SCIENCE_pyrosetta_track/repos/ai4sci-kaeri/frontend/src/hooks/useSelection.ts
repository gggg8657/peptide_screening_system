import { useState, useCallback } from 'react'

export interface UseSelectionReturn {
  selectedIds: Set<string>
  toggleSelect: (id: string) => void
  toggleSelectPage: (pageIds: string[]) => void
  clearSelection: () => void
}

export function useSelection(onSelectionChange?: (ids: Set<string>) => void): UseSelectionReturn {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      onSelectionChange?.(next)
      return next
    })
  }, [onSelectionChange])

  const toggleSelectPage = useCallback((pageIds: string[]) => {
    setSelectedIds(prev => {
      const allSelected = pageIds.every(id => prev.has(id))
      const next = new Set(prev)
      if (allSelected) {
        pageIds.forEach(id => next.delete(id))
      } else {
        pageIds.forEach(id => next.add(id))
      }
      onSelectionChange?.(next)
      return next
    })
  }, [onSelectionChange])

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  return { selectedIds, toggleSelect, toggleSelectPage, clearSelection }
}
