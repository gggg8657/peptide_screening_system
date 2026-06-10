import { createContext, useContext } from 'react'
import type { PipelineStatus } from '../hooks/usePipelineStatus'

/**
 * Pipeline context: provides live pipeline status to the component tree
 * without prop drilling.
 *
 * FUTURE EXTENSION: To support multiple pipeline types (pyrosetta, 3-arm,
 * combined), expand this context to hold a `pipelineType` discriminator or
 * a `Map<string, PipelineStatus>` keyed by pipeline name. Components can
 * then select the active pipeline via `usePipelineContext(pipelineType)`.
 * For now, a single PipelineStatus is sufficient.
 */

export type PipelineContextValue = PipelineStatus & {
  switchRun: (runId: string | null) => void
}

const PipelineContext = createContext<PipelineContextValue | null>(null)

export const PipelineProvider = PipelineContext.Provider

// eslint-disable-next-line react-refresh/only-export-components
export function usePipelineContext(): PipelineContextValue {
  const ctx = useContext(PipelineContext)
  if (!ctx) {
    throw new Error('usePipelineContext must be used within a PipelineProvider')
  }
  return ctx
}
