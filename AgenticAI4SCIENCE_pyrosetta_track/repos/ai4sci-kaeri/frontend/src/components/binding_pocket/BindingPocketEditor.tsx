/**
 * BindingPocketEditor — SSTR1~5 바인딩 포켓 좌표·반경·잔기 설정 폼
 *
 * 위치: src/components/binding_pocket/BindingPocketEditor.tsx
 *
 * ─────────────────────────── ASCII 와이어프레임 ───────────────────────────
 *
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  BP  Binding Pocket 설정              [· 미저장 변경사항]           ║
 * ║      SSTR1~5 포켓 좌표 · 반경 · 잔기 수동 편집                     ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ [SSTR1] [SSTR2 ★] [SSTR3] [SSTR4] [SSTR5]                         ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ 📍 포켓 중심 좌표 (Å)                   ⚠ API 연결 안됨 – 기본값  ║
 * ║  ┌────────────┐ ┌────────────┐ ┌────────────┐                      ║
 * ║  │ X: -6.200  │ │ Y: 14.800  │ │ Z:  2.100  │                      ║
 * ║  └────────────┘ └────────────┘ └────────────┘                      ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ ⭕ 반경                                             17.0 Å         ║
 * ║  5 Å ─────────────────|●|──────────────────── 30 Å                 ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ 📦 도킹 박스 크기 (자동)  X:34.0 × Y:34.0 × Z:34.0 Å              ║
 * ║                          (radius × 2, 최소 30)                     ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ 🔬 잔기 ID                               출처: PDB_3SST            ║
 * ║  ── 포켓 중심 (5) ──────────────────────────────────────────────── ║
 * ║  [202 ×] [205 ×] [208 ×] [284 ×] [285 ×]    [___입력___] [+]      ║
 * ║  ── 선택성 잔기 (2) ────────────────────────────────────────────── ║
 * ║  [287 ×] [288 ×]                             [___입력___] [+]      ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║ [↓ PDB 자동 추출]                 [↺ 초기화]    [💾 저장]          ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * ─────────────────────────── 접근성 ───────────────────────────────────
 * · role="tablist" + role="tab" + aria-selected → 수용체 탭 키보드 내비
 * · role="form" + aria-label → 스크린리더 폼 인식
 * · aria-label 모든 입력·버튼에 개별 지정
 * · role="status" aria-live="polite" → 저장 상태 알림
 * · focus-visible 아웃라인 2px → 키보드 포커스 링
 * ─────────────────────────────────────────────────────────────────────
 */

import { useState, useEffect, useId, useRef, type KeyboardEvent } from 'react'
import {
  MapPin,
  Circle,
  Box,
  Dna,
  Trash2,
  Plus,
  Download,
  Save,
  RotateCcw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Trash,
} from 'lucide-react'
import {
  useBindingPocket,
  useUpdateBindingPocket,
  useExtractBindingPocket,
  useDeleteBindingPocket,
  type BindingPocketConfig,
} from '../../hooks/useBindingPocket'
import { cn } from '../../lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// 상수

const RECEPTORS = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const
type ReceptorType = (typeof RECEPTORS)[number]

/** BE API 미연결 시 사용하는 문헌 기반 fallback 설정값 */
const DEFAULT_CONFIGS: Record<ReceptorType, BindingPocketConfig> = {
  SSTR1: {
    receptor: 'SSTR1',
    center_x: -8.4,
    center_y: 12.3,
    center_z: 3.6,
    radius_angstrom: 16.5,
    residue_ids: [199, 202, 205, 282, 283],
    source: 'literature',
  },
  SSTR2: {
    receptor: 'SSTR2',
    center_x: -6.2,
    center_y: 14.8,
    center_z: 2.1,
    radius_angstrom: 17.0,
    residue_ids: [202, 205, 208, 284, 285, 287, 288],
    source: 'PDB_3SST',
  },
  SSTR3: {
    receptor: 'SSTR3',
    center_x: -9.1,
    center_y: 11.5,
    center_z: 4.2,
    radius_angstrom: 15.8,
    residue_ids: [203, 206, 209, 285, 286, 288],
    source: 'literature',
  },
  SSTR4: {
    receptor: 'SSTR4',
    center_x: -7.8,
    center_y: 13.2,
    center_z: 3.0,
    radius_angstrom: 16.0,
    residue_ids: [202, 205, 208, 283, 284],
    source: 'literature',
  },
  SSTR5: {
    receptor: 'SSTR5',
    center_x: -8.9,
    center_y: 12.7,
    center_z: 3.8,
    radius_angstrom: 16.2,
    residue_ids: [204, 207, 210, 285, 286, 289],
    source: 'literature',
  },
}

// ─────────────────────────────────────────────────────────────────────────────
// 헬퍼

/** 잔기 목록을 포켓 중심 / 선택성 그룹으로 분리 (첫 5개 = pocket, 나머지 = selectivity) */
function splitResidues(ids: number[]): { pocket: number[]; selectivity: number[] } {
  const pivot = Math.min(5, ids.length)
  return {
    pocket: ids.slice(0, pivot),
    selectivity: ids.slice(pivot),
  }
}

/** 도킹 박스 사이즈 자동 계산 — radius × 2, 최소 30 Å */
function calcBoxSize(radius: number) {
  const side = Math.max(radius * 2, 30)
  return side
}

// ─────────────────────────────────────────────────────────────────────────────
// 편집 상태 타입 (폼 내부)

interface EditState {
  center_x: number
  center_y: number
  center_z: number
  radius_angstrom: number
  pocketResidues: number[]
  selectivityResidues: number[]
  source: string
}

function configToEditState(cfg: BindingPocketConfig): EditState {
  const { pocket, selectivity } = splitResidues(cfg.residue_ids)
  return {
    center_x: cfg.center_x,
    center_y: cfg.center_y,
    center_z: cfg.center_z,
    radius_angstrom: cfg.radius_angstrom,
    pocketResidues: pocket,
    selectivityResidues: selectivity,
    source: cfg.source,
  }
}

function editStateToConfig(state: EditState, receptor: string): BindingPocketConfig {
  const boxSide = calcBoxSize(state.radius_angstrom)
  return {
    receptor,
    center_x: state.center_x,
    center_y: state.center_y,
    center_z: state.center_z,
    radius_angstrom: state.radius_angstrom,
    residue_ids: [...state.pocketResidues, ...state.selectivityResidues],
    box_size: { size_x: boxSide, size_y: boxSide, size_z: boxSide },
    source: state.source,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Props

export interface BindingPocketEditorProps {
  /** 초기 선택 수용체 (기본: SSTR2) */
  defaultReceptor?: ReceptorType
}

// ─────────────────────────────────────────────────────────────────────────────
// 메인 컴포넌트

export function BindingPocketEditor({
  defaultReceptor = 'SSTR2',
}: BindingPocketEditorProps) {
  const formId = useId()

  // ── 수용체 선택 ──────────────────────────────────────────────────────────
  const [receptor, setReceptor] = useState<ReceptorType>(defaultReceptor)

  // ── 서버 상태 ────────────────────────────────────────────────────────────
  const { data, isLoading, isError } = useBindingPocket(receptor)
  const updateMutation = useUpdateBindingPocket()
  const extractMutation = useExtractBindingPocket()
  const deleteMutation = useDeleteBindingPocket()

  // ── 폼 편집 상태 ─────────────────────────────────────────────────────────
  const [editState, setEditState] = useState<EditState>(() =>
    configToEditState(DEFAULT_CONFIGS[defaultReceptor]),
  )
  const [touched, setTouched] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [extractError, setExtractError] = useState<string | null>(null)
  const [newPocketInput, setNewPocketInput] = useState('')
  const [newSelectivityInput, setNewSelectivityInput] = useState('')
  const prevReceptorRef = useRef<ReceptorType>(defaultReceptor)

  // ── 수용체 변경 → 편집 상태 리셋 ─────────────────────────────────────────
  useEffect(() => {
    if (prevReceptorRef.current === receptor) return
    prevReceptorRef.current = receptor
    const cfg = data ?? DEFAULT_CONFIGS[receptor]
    setEditState(configToEditState(cfg))
    setTouched(false)
    setSaveStatus('idle')
    setNewPocketInput('')
    setNewSelectivityInput('')
  }, [receptor, data])

  // ── API 데이터 도착 → 미수정 시에만 편집 상태 갱신 ─────────────────────
  useEffect(() => {
    if (data && !touched) {
      setEditState(configToEditState(data))
    }
  }, [data, touched])

  // ── 폼 값 업데이트 ───────────────────────────────────────────────────────
  const update = (patch: Partial<EditState>) => {
    setEditState((prev) => ({
      ...prev,
      ...patch,
      // 수동 편집 시 출처를 user_override 로 자동 표시
      source: patch.source ?? 'user_override',
    }))
    setTouched(true)
    setSaveStatus('idle')
  }

  // ── 잔기 추가/제거 ────────────────────────────────────────────────────────
  const addResidue = (type: 'pocket' | 'selectivity') => {
    const raw = type === 'pocket' ? newPocketInput : newSelectivityInput
    const id = parseInt(raw, 10)
    if (!id || id <= 0) return

    if (type === 'pocket') {
      if (editState.pocketResidues.includes(id)) return
      update({ pocketResidues: [...editState.pocketResidues, id].sort((a, b) => a - b) })
      setNewPocketInput('')
    } else {
      if (editState.selectivityResidues.includes(id)) return
      update({ selectivityResidues: [...editState.selectivityResidues, id].sort((a, b) => a - b) })
      setNewSelectivityInput('')
    }
  }

  const removeResidue = (type: 'pocket' | 'selectivity', id: number) => {
    if (type === 'pocket') {
      update({ pocketResidues: editState.pocketResidues.filter((r) => r !== id) })
    } else {
      update({ selectivityResidues: editState.selectivityResidues.filter((r) => r !== id) })
    }
  }

  // ── 초기화 ───────────────────────────────────────────────────────────────
  const handleReset = () => {
    const cfg = data ?? DEFAULT_CONFIGS[receptor]
    setEditState(configToEditState(cfg))
    setTouched(false)
    setSaveStatus('idle')
    setNewPocketInput('')
    setNewSelectivityInput('')
  }

  // ── 저장 ─────────────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      await updateMutation.mutateAsync(editStateToConfig(editState, receptor))
      setTouched(false)
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch {
      setSaveStatus('error')
    }
  }

  // ── PDB 자동 추출 ────────────────────────────────────────────────────────
  const handleExtract = async () => {
    const residue_ids = [
      ...editState.pocketResidues,
      ...editState.selectivityResidues,
    ]
    // BE: residue_ids 1개 이상 필수
    if (residue_ids.length === 0) {
      setExtractError('잔기를 하나 이상 입력해야 자동 추출이 가능합니다.')
      return
    }
    setExtractError(null)
    try {
      const result = await extractMutation.mutateAsync({ receptor, residue_ids })
      setEditState(configToEditState(result))
      setTouched(false)
      setSaveStatus('idle')
    } catch (e) {
      setExtractError(e instanceof Error ? e.message : '추출 실패')
    }
  }

  // ── 기본값 복원 (DELETE) ─────────────────────────────────────────────────
  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(receptor)
      // onSuccess → 쿼리 무효화 → 재조회 (404 시 isError=true → DEFAULT_CONFIGS 폴백)
      setTouched(false)
      setSaveStatus('idle')
      setExtractError(null)
    } catch {
      /* 에러는 deleteMutation.error로 표시 */
    }
  }

  // ── 파생 값 ──────────────────────────────────────────────────────────────
  const boxSide = calcBoxSize(editState.radius_angstrom)
  const canSave = touched && saveStatus !== 'saving'

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <section
      className="overflow-hidden rounded-xl border border-border-base bg-bg-elev"
      aria-labelledby={`${formId}-title`}
    >
      {/* ── 헤더 ─────────────────────────────────────────────────────────── */}
      <header className="flex flex-wrap items-center gap-3 border-b border-border-base px-4 py-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-text-base font-mono text-[10px] font-bold text-bg">
          BP
        </div>
        <div>
          <h2
            id={`${formId}-title`}
            className="text-sm font-semibold text-text-base"
          >
            Binding Pocket 설정
          </h2>
          <p className="text-[11px] text-text-mute">
            SSTR1~5 포켓 좌표 · 반경 · 잔기 수동 편집
          </p>
        </div>

        {touched && (
          <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-warn-soft px-2 py-0.5 text-[10px] font-semibold text-warn">
            <span
              className="inline-block h-1.5 w-1.5 rounded-full bg-warn"
              aria-hidden="true"
            />
            미저장 변경사항
          </span>
        )}
      </header>

      {/* ── 수용체 탭 ──────────────────────────────────────────────────────── */}
      <div
        role="tablist"
        aria-label="수용체 선택"
        className="flex gap-0.5 border-b border-border-base px-4 pt-2"
      >
        {RECEPTORS.map((r) => (
          <button
            key={r}
            role="tab"
            aria-selected={receptor === r}
            aria-controls={`${formId}-panel`}
            id={`${formId}-tab-${r}`}
            onClick={() => setReceptor(r)}
            className={cn(
              'relative px-3 py-2 text-xs font-medium transition-colors',
              'border-b-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--accent)]',
              receptor === r
                ? 'border-[var(--accent)] text-text-base font-semibold'
                : 'border-transparent text-text-mute hover:text-text-base',
            )}
          >
            {r}
            {r === 'SSTR2' && (
              <span
                className="ml-0.5 text-[9px] text-[var(--accent)]"
                aria-label="타겟 수용체"
              >
                ★
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── 폼 패널 ────────────────────────────────────────────────────────── */}
      <div
        role="tabpanel"
        id={`${formId}-panel`}
        aria-labelledby={`${formId}-tab-${receptor}`}
      >
        {isLoading ? (
          <div className="flex items-center justify-center gap-2 py-12">
            <Loader2
              className="h-5 w-5 animate-spin text-[var(--accent)]"
              aria-hidden="true"
            />
            <span className="text-sm text-text-mute">포켓 설정 로딩 중...</span>
          </div>
        ) : (
          <form
            role="form"
            aria-label={`${receptor} 바인딩 포켓 설정`}
            onSubmit={(e) => {
              e.preventDefault()
              void handleSave()
            }}
            className="divide-y divide-border-base"
          >
            {/* ── 좌표 입력 (3열) ───────────────────────────────────────── */}
            <section className="px-4 py-4">
              <div className="mb-3 flex items-center gap-1.5">
                <MapPin
                  className="h-3.5 w-3.5 text-[var(--accent)]"
                  aria-hidden="true"
                />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-text-base">
                  포켓 중심 좌표 (Å)
                </h3>
                {isError && (
                  <span className="ml-auto text-[10px] text-warn">
                    ⚠ API 연결 안됨 — 기본값 표시
                  </span>
                )}
              </div>

              <div className="grid grid-cols-3 gap-3">
                {(
                  [
                    ['center_x', 'X'],
                    ['center_y', 'Y'],
                    ['center_z', 'Z'],
                  ] as const
                ).map(([field, label]) => (
                  <div key={field}>
                    <label
                      htmlFor={`${formId}-${field}`}
                      className="mb-1 block text-[10px] font-medium text-text-mute"
                    >
                      {label} 축
                    </label>
                    <input
                      id={`${formId}-${field}`}
                      type="number"
                      step="0.001"
                      value={editState[field]}
                      onChange={(e) =>
                        update({ [field]: parseFloat(e.target.value) || 0 })
                      }
                      aria-label={`${receptor} 포켓 중심 ${label}축 좌표 (옹스트롬)`}
                      className={cn(
                        'w-full rounded-md border bg-bg-sunk px-2.5 py-1.5',
                        'font-mono text-xs text-text-base',
                        'border-border-base',
                        'focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]',
                        'transition-colors',
                      )}
                    />
                  </div>
                ))}
              </div>
            </section>

            {/* ── 반경 슬라이더 ─────────────────────────────────────────── */}
            <section className="px-4 py-4">
              <div className="mb-3 flex items-center gap-1.5">
                <Circle
                  className="h-3.5 w-3.5 text-[var(--teal)]"
                  aria-hidden="true"
                />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-text-base">
                  반경
                </h3>
                <span
                  className="ml-auto font-mono text-sm font-semibold text-[var(--accent)]"
                  aria-live="polite"
                  aria-label={`현재 반경 ${editState.radius_angstrom.toFixed(1)} 옹스트롬`}
                >
                  {editState.radius_angstrom.toFixed(1)} Å
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="shrink-0 text-[10px] tabular-nums text-text-dim">
                  5 Å
                </span>
                <input
                  id={`${formId}-radius`}
                  type="range"
                  min={5}
                  max={30}
                  step={0.5}
                  value={editState.radius_angstrom}
                  onChange={(e) =>
                    update({ radius_angstrom: parseFloat(e.target.value) })
                  }
                  aria-label={`${receptor} 포켓 반경 슬라이더 (5~30 Å)`}
                  aria-valuemin={5}
                  aria-valuemax={30}
                  aria-valuenow={editState.radius_angstrom}
                  aria-valuetext={`${editState.radius_angstrom.toFixed(1)} 옹스트롬`}
                  className="flex-1 cursor-pointer accent-[var(--accent)]"
                />
                <span className="shrink-0 text-[10px] tabular-nums text-text-dim">
                  30 Å
                </span>
              </div>
            </section>

            {/* ── 박스 크기 (읽기 전용) ─────────────────────────────────── */}
            <section className="bg-bg-sunk/60 px-4 py-3">
              <div className="mb-2 flex items-center gap-1.5">
                <Box
                  className="h-3.5 w-3.5 text-text-dim"
                  aria-hidden="true"
                />
                <h3 className="text-[10px] font-medium uppercase tracking-wide text-text-mute">
                  도킹 박스 크기 (자동 계산)
                </h3>
              </div>

              <div
                role="status"
                aria-label={`도킹 박스 크기 ${boxSide.toFixed(1)} × ${boxSide.toFixed(1)} × ${boxSide.toFixed(1)} 옹스트롬`}
                className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-text-mute"
              >
                {(['X', 'Y', 'Z'] as const).map((axis, i) => (
                  <span key={axis} className="flex items-center gap-1">
                    {i > 0 && (
                      <span className="text-border-strong" aria-hidden="true">
                        ×
                      </span>
                    )}
                    <span>
                      {axis}:{' '}
                      <strong className="text-text-base">
                        {boxSide.toFixed(1)}
                      </strong>
                    </span>
                  </span>
                ))}
                <span className="text-text-dim">Å</span>
                <span className="ml-1 text-[9px] text-text-dim">
                  (radius × 2, 최소 30)
                </span>
              </div>
            </section>

            {/* ── 잔기 ID ──────────────────────────────────────────────── */}
            <section className="px-4 py-4">
              <div className="mb-3 flex items-center gap-1.5">
                <Dna
                  className="h-3.5 w-3.5 text-[var(--violet)]"
                  aria-hidden="true"
                />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-text-base">
                  잔기 ID
                </h3>
                <span className="ml-auto text-[10px] text-text-dim">
                  출처: {editState.source}
                </span>
              </div>

              <div className="space-y-3">
                {/* 포켓 중심 잔기 그룹 */}
                <ResidueGroup
                  label="포켓 중심"
                  residues={editState.pocketResidues}
                  inputValue={newPocketInput}
                  onInputChange={setNewPocketInput}
                  onAdd={() => addResidue('pocket')}
                  onRemove={(id) => removeResidue('pocket', id)}
                  inputId={`${formId}-pocket-input`}
                  chipColor="text-[var(--accent-text)] border-[var(--accent)]/40 bg-accent-soft"
                  groupLabel={`${receptor} 포켓 중심 잔기`}
                />

                {/* 선택성 잔기 그룹 */}
                <ResidueGroup
                  label="선택성"
                  residues={editState.selectivityResidues}
                  inputValue={newSelectivityInput}
                  onInputChange={setNewSelectivityInput}
                  onAdd={() => addResidue('selectivity')}
                  onRemove={(id) => removeResidue('selectivity', id)}
                  inputId={`${formId}-selectivity-input`}
                  chipColor="text-[var(--violet)] border-[var(--violet)]/40 bg-violet-soft"
                  groupLabel={`${receptor} 선택성 잔기`}
                />
              </div>
            </section>

            {/* ── 액션 버튼 ─────────────────────────────────────────────── */}
            <footer className="flex flex-wrap items-center gap-2 px-4 py-3">
              {/* PDB 자동 추출 */}
              <div className="flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => void handleExtract()}
                  disabled={extractMutation.isPending}
                  aria-label={`${receptor} PDB 파일에서 포켓 좌표 자동 추출`}
                  aria-describedby={extractError ? `${formId}-extract-error` : undefined}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium',
                    'border-border-base bg-bg-sunk text-text-mute',
                    'hover:border-border-strong hover:text-text-base',
                    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]',
                    'transition-colors disabled:cursor-not-allowed disabled:opacity-50',
                  )}
                >
                  {extractMutation.isPending ? (
                    <Loader2
                      className="h-3.5 w-3.5 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <Download className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  PDB에서 자동 추출
                </button>
                {extractError && (
                  <p
                    id={`${formId}-extract-error`}
                    role="alert"
                    className="text-[10px] text-[var(--neg)]"
                  >
                    {extractError}
                  </p>
                )}
              </div>

              {/* 기본값 복원 (DELETE) */}
              <button
                type="button"
                onClick={() => void handleDelete()}
                disabled={deleteMutation.isPending}
                aria-label={`${receptor} 서버 설정 삭제 및 기본값 복원`}
                title="사용자 오버라이드를 삭제하고 원본 기본값을 복원합니다"
                className={cn(
                  'flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium',
                  'border-[var(--neg)]/30 text-[var(--neg)]/70',
                  'hover:border-[var(--neg)]/60 hover:text-[var(--neg)]',
                  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--neg)]',
                  'transition-colors disabled:cursor-not-allowed disabled:opacity-50',
                )}
              >
                {deleteMutation.isPending ? (
                  <Loader2
                    className="h-3.5 w-3.5 animate-spin"
                    aria-hidden="true"
                  />
                ) : (
                  <Trash className="h-3.5 w-3.5" aria-hidden="true" />
                )}
                기본값 복원
              </button>

              <div className="ml-auto flex items-center gap-2">
                {/* 초기화 */}
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={!touched}
                  aria-label="변경사항 초기화"
                  className={cn(
                    'flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium',
                    'border-border-base text-text-mute',
                    'hover:border-[var(--neg)]/40 hover:text-[var(--neg)]',
                    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--neg)]',
                    'transition-colors disabled:cursor-not-allowed disabled:opacity-40',
                  )}
                >
                  <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
                  초기화
                </button>

                {/* 저장 */}
                <button
                  type="submit"
                  disabled={!canSave}
                  aria-label={`${receptor} 바인딩 포켓 설정 저장`}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-white',
                    saveStatus === 'error'
                      ? 'bg-[var(--neg)] hover:opacity-90'
                      : saveStatus === 'saved'
                        ? 'bg-[var(--pos)] hover:opacity-90'
                        : 'bg-[var(--accent)] hover:opacity-90',
                    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]',
                    'transition-all disabled:cursor-not-allowed disabled:opacity-50',
                  )}
                >
                  {saveStatus === 'saving' ? (
                    <>
                      <Loader2
                        className="h-3.5 w-3.5 animate-spin"
                        aria-hidden="true"
                      />
                      저장 중...
                    </>
                  ) : saveStatus === 'saved' ? (
                    <>
                      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                      저장됨
                    </>
                  ) : saveStatus === 'error' ? (
                    <>
                      <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                      재시도
                    </>
                  ) : (
                    <>
                      <Save className="h-3.5 w-3.5" aria-hidden="true" />
                      저장
                    </>
                  )}
                </button>
              </div>
            </footer>

            {/* ── 저장 상태 알림 ───────────────────────────────────────── */}
            <div role="status" aria-live="polite" aria-atomic="true">
              {saveStatus === 'error' && (
                <div className="border-t border-[var(--neg)]/20 bg-neg-soft px-4 py-2">
                  <p className="text-[11px] text-[var(--neg)]">
                    저장 실패:{' '}
                    {updateMutation.error instanceof Error
                      ? updateMutation.error.message
                      : '알 수 없는 오류'}
                  </p>
                </div>
              )}
            </div>
          </form>
        )}
      </div>
    </section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// 잔기 그룹 서브컴포넌트

interface ResidueGroupProps {
  label: string
  residues: number[]
  inputValue: string
  onInputChange: (v: string) => void
  onAdd: () => void
  onRemove: (id: number) => void
  inputId: string
  chipColor: string
  groupLabel: string
}

function ResidueGroup({
  label,
  residues,
  inputValue,
  onInputChange,
  onAdd,
  onRemove,
  inputId,
  chipColor,
  groupLabel,
}: ResidueGroupProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      onAdd()
    }
  }

  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-text-dim">
          {label}
        </span>
        <span
          className="rounded bg-bg-sunk px-1 py-0.5 font-mono text-[9px] text-text-dim"
          aria-label={`${label} 잔기 ${residues.length}개`}
        >
          {residues.length}
        </span>
      </div>

      <div
        role="group"
        aria-label={groupLabel}
        className={cn(
          'flex min-h-[2.5rem] flex-wrap gap-1.5 rounded-md border border-border-base',
          'bg-bg-sunk p-2',
        )}
      >
        {/* 잔기 칩 */}
        {residues.map((id) => (
          <span
            key={id}
            className={cn(
              'inline-flex items-center gap-0.5 rounded border px-1.5 py-0.5',
              'font-mono text-[10px] font-semibold',
              chipColor,
            )}
          >
            {id}
            <button
              type="button"
              onClick={() => onRemove(id)}
              aria-label={`잔기 ${id} 제거`}
              className={cn(
                'ml-0.5 rounded-sm opacity-60 hover:opacity-100',
                'focus-visible:outline focus-visible:outline-1 focus-visible:outline-current',
                'transition-opacity',
              )}
            >
              <Trash2 className="h-2.5 w-2.5" aria-hidden="true" />
            </button>
          </span>
        ))}

        {/* 추가 인풋 */}
        <div className="flex items-center gap-1">
          <input
            id={inputId}
            type="number"
            min={1}
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="번호"
            aria-label={`${label} 잔기 번호 입력 (Enter 또는 + 버튼으로 추가)`}
            className={cn(
              'w-16 rounded border border-dashed border-border-strong',
              'bg-transparent px-1.5 py-0.5 font-mono text-[10px] text-text-base',
              'placeholder:text-text-dim',
              'focus:border-[var(--accent)] focus:outline-none',
            )}
          />
          <button
            type="button"
            onClick={onAdd}
            aria-label={`${label} 잔기 추가`}
            className={cn(
              'flex items-center rounded-sm p-0.5 text-text-mute',
              'hover:text-text-base',
              'focus-visible:outline focus-visible:outline-1 focus-visible:outline-[var(--accent)]',
              'transition-colors',
            )}
          >
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
