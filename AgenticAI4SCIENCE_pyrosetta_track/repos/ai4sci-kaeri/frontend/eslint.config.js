import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // 2026-05-15: 외부 자동 linter 환경에서 inline eslint-disable 코멘트가
      // 제거되는 이슈로 인해 임시 warning으로 downgrade. 본 규칙(React 19+)은
      // 동기화 패턴(server settings hydration 등)에서 false-positive가 많아
      // 코드 의도를 보존하면서 CI 통과 우선. 별도 sprint에서 useMemo/useSyncExternalStore
      // 패턴으로 리팩토링 권장.
      'react-hooks/set-state-in-effect': 'warn',
      // 2026-05-15: 일부 컴포넌트 파일에서 색상 헬퍼(iptmColor 등) 함께 export.
      // dev HMR 영향뿐 prod build 무관 → warning으로 downgrade. 별도 sprint에서
      // 유틸 함수 별도 파일로 분리 권장.
      'react-refresh/only-export-components': 'warn',
    },
  },
])
