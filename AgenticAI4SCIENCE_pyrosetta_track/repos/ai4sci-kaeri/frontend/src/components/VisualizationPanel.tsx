import { useCallback, useEffect, useRef, useState } from 'react'
import { Image, ZoomIn, X } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { VisualizationImage } from '../types'

const LABELS: Record<string, string> = {
  overview: 'Overview',
  closeup: 'Close-up',
  interface: 'Interface',
  electrostatics: 'Electrostatics',
}

interface VisualizationPanelProps {
  images: VisualizationImage[]
  iteration?: number
}

export function VisualizationPanel({ images, iteration }: VisualizationPanelProps) {
  const [selected, setSelected] = useState<VisualizationImage | null>(null)
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set())
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const dialogRef = useRef<HTMLDivElement | null>(null)

  const openLightbox = useCallback((img: VisualizationImage, button: HTMLButtonElement) => {
    triggerRef.current = button
    setSelected(img)
  }, [])

  const closeLightbox = useCallback(() => {
    setSelected(null)
    triggerRef.current?.focus()
  }, [])

  // Focus trap + Escape handler for lightbox
  useEffect(() => {
    if (!selected) return
    const dialog = dialogRef.current
    if (!dialog) return

    // Focus the close button on open
    const closeBtn = dialog.querySelector<HTMLButtonElement>('[aria-label="Close"]')
    closeBtn?.focus()

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeLightbox()
        return
      }
      if (e.key === 'Tab') {
        const focusable = dialog.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [selected, closeLightbox])

  if (images.length === 0) {
    return (
      <section className="card flex flex-col gap-3" aria-label="Structure Visualization">
        <div className="flex items-center gap-2">
          <Image className="w-4 h-4 text-[var(--text-mute)]" />
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Structure Visualization
            <HelpTooltip title="Structure Visualization">
              <p>PyMOL로 생성된 3D 구조 렌더링 이미지입니다.</p>
              <p>수용체-펩타이드 복합체의 결합 모드를 시각적으로 확인할 수 있습니다.</p>
              <p><strong>이미지 없음</strong>: PyMOL이 설치되지 않았거나 렌더링이 아직 완료되지 않은 경우.</p>
            </HelpTooltip>
          </h2>
        </div>
        <div className="flex items-center justify-center py-8 text-[var(--text-mute)] text-xs">
          No visualization images available yet
        </div>
      </section>
    )
  }

  return (
    <section className="card flex flex-col gap-3" aria-label="Structure Visualization">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Image className="w-4 h-4 text-[var(--accent)]" />
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Structure Visualization
            <HelpTooltip title="Structure Visualization">
              <p>PyMOL로 생성된 3D 구조 렌더링 이미지입니다.</p>
              <p>수용체-펩타이드 복합체의 결합 모드를 시각적으로 확인할 수 있습니다.</p>
              <p><strong>이미지 없음</strong>: PyMOL이 설치되지 않았거나 렌더링이 아직 완료되지 않은 경우.</p>
            </HelpTooltip>
          </h2>
          {iteration != null && (
            <span className="text-[10px] bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 px-2 py-0.5 rounded-full font-medium">
              Iter {iteration}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {images.map(img => (
          <button
            key={img.type}
            onClick={e => openLightbox(img, e.currentTarget)}
            className="group relative aspect-square rounded-lg overflow-hidden border border-[var(--border)] hover:border-[var(--accent)]/30 transition-all bg-[var(--bg)]"
          >
            {failedImages.has(img.type) ? (
              <div className="w-full h-full flex flex-col items-center justify-center gap-1 text-[var(--text-mute)]">
                <Image className="w-6 h-6" />
                <span className="text-[10px]">{LABELS[img.type] || img.label}</span>
              </div>
            ) : (
              <img
                src={img.url}
                alt={LABELS[img.type] || img.label}
                className="w-full h-full object-cover"
                loading="lazy"
                onError={() => setFailedImages(prev => new Set(prev).add(img.type))}
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-sunk)]/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
              <div className="flex items-center justify-between w-full">
                <span className="text-[10px] text-[var(--text)] font-medium">
                  {LABELS[img.type] || img.label}
                </span>
                <ZoomIn className="w-3 h-3 text-[var(--text-mute)]" />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 p-1.5 bg-[var(--bg-sunk)]/70 text-center">
              <span className="text-[10px] text-[var(--text-mute)] font-medium uppercase tracking-wider">
                {LABELS[img.type] || img.label}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {selected && (
        <div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="lightbox-title"
          className="fixed inset-0 z-50 bg-[var(--bg-sunk)]/90 flex items-center justify-center p-8"
          onClick={closeLightbox}
        >
          <div className="relative max-w-4xl max-h-[80vh]" onClick={e => e.stopPropagation()}>
            <button
              onClick={closeLightbox}
              className="absolute -top-3 -right-3 w-7 h-7 rounded-full bg-[var(--bg-elev)] border border-[var(--border)] flex items-center justify-center hover:bg-[var(--bg-elev)] transition-colors z-10"
              aria-label="Close"
            >
              <X className="w-4 h-4 text-[var(--text-mute)]" />
            </button>
            {failedImages.has(selected.type) ? (
              <div className="flex flex-col items-center justify-center gap-3 w-96 h-64 rounded-lg border border-[var(--border)] bg-[var(--bg)] text-[var(--text-mute)]">
                <Image className="w-10 h-10" />
                <span className="text-sm">Image not available</span>
              </div>
            ) : (
              <img
                src={selected.url}
                alt={LABELS[selected.type] || selected.label}
                className="max-w-full max-h-[80vh] rounded-lg border border-[var(--border)]"
                onError={() => setFailedImages(prev => new Set(prev).add(selected.type))}
              />
            )}
            <div id="lightbox-title" className="text-center mt-2 text-sm text-[var(--text-mute)]">
              {LABELS[selected.type] || selected.label}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
