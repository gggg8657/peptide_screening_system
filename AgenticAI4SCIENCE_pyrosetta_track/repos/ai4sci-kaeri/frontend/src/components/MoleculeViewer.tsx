import { useEffect, useRef, useState, useCallback } from 'react'
import { X, RotateCcw, Maximize2, Minimize2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { useFocusTrap } from '../hooks/useFocusTrap'

// Mol* imports
import { PluginContext } from 'molstar/lib/mol-plugin/context'
import { DefaultPluginSpec } from 'molstar/lib/mol-plugin/spec'
import { PluginConfig } from 'molstar/lib/mol-plugin/config'
import { PdbProvider } from 'molstar/lib/mol-plugin-state/formats/trajectory'
import { PresetStructureRepresentations } from 'molstar/lib/mol-plugin-state/builder/structure/representation-preset'
import { Asset } from 'molstar/lib/mol-util/assets'
import { Color } from 'molstar/lib/mol-util/color'

import 'molstar/build/viewer/molstar.css'

export type ViewMode = 'complex' | 'cartoon' | 'ball-and-stick' | 'surface'

interface MoleculeViewerProps {
  pdbUrl: string
  candidateId: string
  onClose: () => void
}

const VIEW_MODES: { key: ViewMode; label: string; desc: string }[] = [
  { key: 'complex', label: 'Complex', desc: 'Cartoon for polymer chains, sticks for ligands/waters/ions' },
  { key: 'cartoon', label: 'Cartoon', desc: 'Clean backbone ribbon only' },
  { key: 'ball-and-stick', label: 'Ball & Stick', desc: 'All atoms shown as spheres and bonds' },
  { key: 'surface', label: 'Surface', desc: 'Molecular surface representation' },
]

export function MoleculeViewer({ pdbUrl, candidateId, onClose }: MoleculeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const pluginRef = useRef<PluginContext | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('complex')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fullscreen, setFullscreen] = useState(false)

  useFocusTrap(dialogRef)

  // Initialize Mol* plugin
  useEffect(() => {
    if (!containerRef.current) return

    let disposed = false
    const container = containerRef.current

    async function init() {
      try {
        const plugin = new PluginContext(DefaultPluginSpec())

        if (disposed) { plugin.dispose(); return }

        // Configure for dark theme
        plugin.config.set((PluginConfig.Background as Record<string, unknown>).StyleOverwrite as never, { name: 'flat', params: { color: Color(0x0f172a) } })

        await plugin.init()

        if (disposed) { plugin.dispose(); return }

        // Use mountAsync which handles canvas creation internally
        const ok = await plugin.mountAsync(container as HTMLDivElement)
        if (!ok) {
          throw new Error('Failed to mount Mol* viewer')
        }

        if (disposed) { plugin.dispose(); return }

        pluginRef.current = plugin

        // Load PDB
        const data = await plugin.builders.data.download(
          { url: Asset.Url(pdbUrl) },
          { state: { isGhost: true } }
        )
        const trajectory = await plugin.builders.structure.parseTrajectory(data, PdbProvider)
        await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default')

        if (!disposed) {
          setLoading(false)
          applyViewMode(plugin, 'complex')
        }
      } catch (err) {
        if (!disposed) {
          setError(err instanceof Error ? err.message : 'Failed to load structure')
          setLoading(false)
        }
      }
    }

    init()

    return () => {
      disposed = true
      if (pluginRef.current) {
        pluginRef.current.unmount()
        pluginRef.current.dispose()
        pluginRef.current = null
      }
    }
  }, [pdbUrl])

  // Apply view mode changes
  useEffect(() => {
    if (pluginRef.current && !loading) {
      applyViewMode(pluginRef.current, viewMode)
    }
  }, [viewMode, loading])

  const handleReset = useCallback(() => {
    if (pluginRef.current) {
      pluginRef.current.managers.camera.reset()
    }
  }, [])

  const toggleFullscreen = useCallback(() => {
    setFullscreen(f => !f)
  }, [])

  // Handle escape key to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`3D Structure — ${candidateId}`}
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center',
        'bg-[var(--bg-sunk)]/80 backdrop-blur-sm'
      )}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        ref={dialogRef}
        className={cn(
          'bg-[var(--bg)] border border-[var(--border)] rounded-xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300',
          fullscreen ? 'w-full h-full rounded-none' : 'w-[90vw] h-[85vh] max-w-[1400px]'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--bg)] flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-[var(--text-mute)]">3D Structure</span>
            <span className="text-xs text-[var(--text-mute)] font-mono">{candidateId}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {/* View mode buttons */}
            {VIEW_MODES.map(mode => (
              <button
                key={mode.key}
                onClick={() => setViewMode(mode.key)}
                title={mode.desc}
                className={cn(
                  'px-2.5 py-1 rounded-md text-xs font-medium transition-all border',
                  viewMode === mode.key
                    ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                    : 'bg-[var(--bg-elev)] text-[var(--text-dim)] border-[var(--border)] hover:border-[var(--border)] hover:text-[var(--text-mute)]'
                )}
              >
                {mode.label}
              </button>
            ))}

            <div className="w-px h-5 bg-[var(--bg-sunk)] mx-1" />

            <button
              onClick={handleReset}
              title="Reset camera"
              className="p-1.5 rounded-md text-[var(--text-dim)] hover:text-[var(--text-mute)] hover:bg-[var(--bg-elev)] transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={toggleFullscreen}
              title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
              className="p-1.5 rounded-md text-[var(--text-dim)] hover:text-[var(--text-mute)] hover:bg-[var(--bg-elev)] transition-colors"
            >
              {fullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={onClose}
              title="Close (Esc)"
              className="p-1.5 rounded-md text-[var(--text-dim)] hover:text-[var(--neg)] hover:bg-[var(--bg-elev)] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Viewer container */}
        <div className="flex-1 relative overflow-hidden">
          <div
            ref={containerRef}
            className="absolute inset-0"
            style={{ backgroundColor: 'var(--bg-sunk)' }}
          />

          {/* Loading overlay */}
          {loading && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg)]">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-[var(--text-mute)]">Loading structure...</span>
              </div>
            </div>
          )}

          {/* Error overlay */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg)]">
              <div className="flex flex-col items-center gap-3 text-center px-4">
                <span className="text-[var(--neg)] text-sm font-semibold">Failed to load structure</span>
                <span className="text-xs text-[var(--text-mute)] max-w-md">{error}</span>
                <span className="text-[10px] text-[var(--text-mute)] font-mono">{pdbUrl}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between px-4 py-1.5 border-t border-[var(--border)] bg-[var(--bg)] text-[10px] text-[var(--text-mute)] flex-shrink-0">
          <span>Mol* Viewer &middot; Drag to rotate, Scroll to zoom, Shift+Drag to translate</span>
          <span className="font-mono">{pdbUrl.split('/').pop()}</span>
        </div>
      </div>
    </div>
  )
}

async function applyViewMode(plugin: PluginContext, mode: ViewMode) {
  const structures = plugin.managers.structure.hierarchy.current.structures
  if (structures.length === 0) return

  const struct = structures[0]

  try {
    const presetMap = {
      'complex':        PresetStructureRepresentations['polymer-and-ligand'],
      'cartoon':        PresetStructureRepresentations['polymer-cartoon'],
      'ball-and-stick': PresetStructureRepresentations['atomic-detail'],
      'surface':        PresetStructureRepresentations['molecular-surface'],
    } as const

    const provider = presetMap[mode] ?? presetMap.complex

    await plugin.managers.structure.component.applyPreset(
      [struct],
      provider,
    )

    plugin.managers.camera.reset()
  } catch (err) {
    console.warn(`[MoleculeViewer] applyViewMode(${mode}) failed:`, err)
  }
}
