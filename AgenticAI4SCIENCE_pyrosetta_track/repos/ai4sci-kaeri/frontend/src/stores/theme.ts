/**
 * Theme store — zustand + persist
 *
 * 위치: src/stores/theme.ts
 *
 * 사용:
 *   const { theme, setTheme } = useTheme();
 *
 * main.tsx 에서 첫 로드 시:
 *   const { theme, accentHue } = useTheme.getState();
 *   document.documentElement.setAttribute('data-theme', theme);
 *   document.documentElement.style.setProperty('--accent-hue', String(accentHue));
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark';
type Density = 'compact' | 'normal' | 'spacious';

interface ThemeState {
  theme: Theme;
  accentHue: number; // 0–360
  density: Density;
  fontSans: string;
  fontMono: string;

  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  setAccentHue: (h: number) => void;
  setDensity: (d: Density) => void;
  setFontSans: (f: string) => void;
  setFontMono: (f: string) => void;
}

function apply(state: Pick<ThemeState, 'theme' | 'accentHue' | 'fontSans' | 'fontMono'>) {
  const r = document.documentElement;
  r.setAttribute('data-theme', state.theme);
  r.style.setProperty('--accent-hue', String(state.accentHue));
  r.style.setProperty('--font-sans', `"${state.fontSans}", system-ui, sans-serif`);
  r.style.setProperty('--font-mono', `"${state.fontMono}", ui-monospace, monospace`);
}

export const useTheme = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'light',
      accentHue: 200,
      density: 'normal',
      fontSans: 'Inter',
      fontMono: 'JetBrains Mono',

      setTheme: (theme) => { set({ theme }); apply({ ...get(), theme }); },
      toggleTheme: () => {
        const next = get().theme === 'light' ? 'dark' : 'light';
        set({ theme: next });
        apply({ ...get(), theme: next });
      },
      setAccentHue: (accentHue) => { set({ accentHue }); apply({ ...get(), accentHue }); },
      setDensity: (density) => set({ density }),
      setFontSans: (fontSans) => { set({ fontSans }); apply({ ...get(), fontSans }); },
      setFontMono: (fontMono) => { set({ fontMono }); apply({ ...get(), fontMono }); },
    }),
    {
      name: 'sstr2-theme',
      onRehydrateStorage: () => (state) => {
        if (state) apply(state);
      },
    },
  ),
);
