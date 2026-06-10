/**
 * BindingPocketPage — /binding-pocket 라우트
 *
 * 위치: src/pages/BindingPocketPage.tsx
 *
 * SSTR1~5 바인딩 포켓 설정 편집 전용 페이지.
 * BindingPocketEditor 컴포넌트를 페이지 레이아웃으로 감쌈.
 *
 * 통합 위치: App.tsx NAV_ITEMS + Routes에 추가.
 */

import { MapPin } from 'lucide-react'
import { BindingPocketEditor } from '../components/binding_pocket/BindingPocketEditor'

export function BindingPocketPage() {
  return (
    <div className="space-y-4">
      {/* 페이지 헤더 (App.tsx 다른 페이지와 동일한 패턴) */}
      <div className="flex flex-wrap items-center gap-2">
        <MapPin
          className="h-4 w-4 text-[var(--teal)]"
          aria-hidden="true"
        />
        <h1 className="text-sm font-semibold text-text-base">
          Binding Pocket 설정
        </h1>
        <span className="text-[11px] text-text-mute">
          도킹 좌표 · 반경 · 잔기 수동 편집 — SSTR1~5
        </span>
        <span
          className="ml-auto rounded bg-bg-sunk px-2 py-0.5 font-mono text-[10px] text-text-dim"
          aria-label="대상 수용체"
        >
          SSTR1 · SSTR2★ · SSTR3 · SSTR4 · SSTR5
        </span>
      </div>

      {/* 에디터 */}
      <BindingPocketEditor defaultReceptor="SSTR2" />

      {/* 안내 */}
      <p className="text-[10px] text-text-dim">
        ※ 설정값은 도킹 시뮬레이션(DiffDock / Boltz / FlexPepDock)에 직접 적용됩니다.
        &nbsp;변경 후 반드시 저장 버튼을 클릭하세요.
        &nbsp;PDB 자동 추출 기능은 BE API(task #1) 완료 후 활성화됩니다.
      </p>
    </div>
  )
}
