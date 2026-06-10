import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../stores/theme'

export function ThemeToggle() {
  const theme = useTheme(s => s.theme)
  const toggleTheme = useTheme(s => s.toggleTheme)
  const isDark = theme === 'dark'
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={isDark ? 'Switch to light' : 'Switch to dark'}
      className="hidden sm:inline-flex items-center justify-center rounded-full border h-7 w-7 transition-colors"
      style={{
        background: 'var(--bg-elev)',
        borderColor: 'var(--border)',
        color: 'var(--text-mute)',
      }}
    >
      {isDark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
    </button>
  )
}
