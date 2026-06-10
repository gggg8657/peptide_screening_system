import { useState, useRef, useCallback } from 'react'
import { HelpCircle, X } from 'lucide-react'
import { useClickOutside } from '../../hooks/useClickOutside'

interface HelpTooltipProps {
  title: string
  children: React.ReactNode
}

export function HelpTooltip({ title, children }: HelpTooltipProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(false), [])
  useClickOutside(ref, close, open)

  return (
    <div className="relative inline-flex" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-label={`${title} 도움말`}
        className="text-[var(--text-dim)] hover:text-[var(--text-mute)] transition-colors p-0.5 rounded-full hover:bg-[var(--bg-sunk)]"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>
      {open && (
        <div className="absolute right-0 top-6 z-50 w-80 bg-[var(--bg-elev)] border border-[var(--border)] rounded-xl p-3 shadow-2xl text-xs text-[var(--text-mute)] leading-relaxed">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-[var(--text-mute)] text-xs">{title}</span>
            <button onClick={close} aria-label="닫기" className="text-[var(--text-dim)] hover:text-[var(--text-mute)]">
              <X className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-1.5">{children}</div>
        </div>
      )}
    </div>
  )
}
