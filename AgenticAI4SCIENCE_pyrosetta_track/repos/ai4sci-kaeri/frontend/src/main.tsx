import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { useTheme } from './stores/theme'

{
  const { theme, accentHue, fontSans, fontMono } = useTheme.getState()
  const root = document.documentElement
  root.setAttribute('data-theme', theme)
  root.style.setProperty('--accent-hue', String(accentHue))
  root.style.setProperty('--font-sans', `"${fontSans}", system-ui, sans-serif`)
  root.style.setProperty('--font-mono', `"${fontMono}", ui-monospace, monospace`)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
