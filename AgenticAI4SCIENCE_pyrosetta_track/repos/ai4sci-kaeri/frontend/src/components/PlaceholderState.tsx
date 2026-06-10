interface PlaceholderStateProps {
  children: React.ReactNode
  message?: string
  active?: boolean
}

export function PlaceholderState({ children, message = 'Awaiting pipeline data', active = true }: PlaceholderStateProps) {
  if (!active) return <>{children}</>

  return (
    <div className="relative">
      <div className="opacity-40 pointer-events-none select-none">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="bg-[var(--bg)] border border-dashed border-[var(--border)] rounded-lg px-4 py-2">
          <p className="text-xs text-[var(--text-mute)] font-medium text-center">{message}</p>
        </div>
      </div>
    </div>
  )
}
