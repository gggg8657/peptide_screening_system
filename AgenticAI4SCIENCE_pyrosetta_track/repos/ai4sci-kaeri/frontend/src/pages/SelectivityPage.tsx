import { useState, useCallback } from 'react'
import { Play, Square, ShieldCheck, AlertTriangle } from 'lucide-react'
import { ReceptorUpload } from '../components/selectivity/ReceptorUpload'
import { SelectivityTable } from '../components/selectivity/SelectivityTable'
import { SelectivityChart } from '../components/selectivity/SelectivityChart'
import { HeuristicBanner } from '../components/HeuristicBanner'
import { ArchivesTopKSlider } from '../components/ArchivesTopKSlider'
import { useSelectivity } from '../hooks/useSelectivity'
import { usePipelineContext } from '../contexts/PipelineContext'
import type { SelectivityResult } from '../hooks/useSelectivity'

/** Boltz iPTM 신뢰도 경고 목록 (M5 결과 반영) */
const BOLTZ_IPTM_WARNINGS = [
  'iPTM ≠ Ki: Boltz-2 iPTM는 구조적 복합체 신뢰도이며, 결합 친화도(Ki/IC50)가 아닙니다.',
  'Spearman ρ ≈ −0.3 (iPTM vs 실험 Ki, SST 유사체 문헌): 순위 일치 낮음.',
  '순위 일치 실험 검증: 현재까지 0/5 케이스 — in-vitro 확인 필수.',
  '동일 수용체 내 상대 비교(selectivity index)는 유효하나 절대 결합력 해석 불가.',
]

export function SelectivityPage() {
  const live = usePipelineContext()
  const {
    receptors,
    candidates,
    isRunning,
    progress,
    receptorProgress,
    error,
    uploadReceptor,
    runAnalysis,
    stopAnalysis,
    fetchReceptors,
  } = useSelectivity(3000)

  // Candidate selection from existing pipeline results
  const pipelineCandidates = live.candidates.length > 0
    ? live.candidates
    : live.historicalCandidates

  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(new Set())
  const [selectedResultIds, setSelectedResultIds] = useState<Set<string>>(new Set())

  const toggleCandidate = useCallback((id: string) => {
    setSelectedCandidateIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleAll = useCallback(() => {
    if (selectedCandidateIds.size === pipelineCandidates.length) {
      setSelectedCandidateIds(new Set())
    } else {
      setSelectedCandidateIds(new Set(pipelineCandidates.map(c => c.id)))
    }
  }, [selectedCandidateIds.size, pipelineCandidates])

  const handleRowClick = useCallback((c: SelectivityResult) => {
    setSelectedResultIds(prev => {
      const next = new Set(prev)
      if (next.has(c.seq_id)) next.delete(c.seq_id)
      else next.add(c.seq_id)
      return next
    })
  }, [])

  const handleRun = useCallback(async () => {
    if (isRunning) { stopAnalysis(); return }
    const ids = [...selectedCandidateIds]
    const seqs = ids.map(id => {
      const cand = pipelineCandidates.find(c => c.id === id)
      return cand?.sequence ?? ''
    }).filter(Boolean)
    if (ids.length === 0) return
    // 수정 4: pipelineCandidates의 ddG 값을 sstr2_ddgs로 전달 (백엔드 -15.0 fallback 방지)
    const sstr2Ddgs: Record<string, number> = {}
    for (const id of ids) {
      const cand = pipelineCandidates.find(c => c.id === id)
      if (cand && typeof cand.ddG === 'number') sstr2Ddgs[id] = cand.ddG
    }
    await runAnalysis(ids, seqs, sstr2Ddgs)
  }, [isRunning, selectedCandidateIds, pipelineCandidates, runAnalysis, stopAnalysis])

  // SSTR2는 타겟 수용체 — 메인 파이프라인에서 스코어 자동 조회되므로 체크 제외
  const offTargetReceptors = receptors.filter(r => r.name !== 'SSTR2')
  const receptorsAllLoaded = offTargetReceptors.every(r => r.loaded)
  const canRun = !isRunning && selectedCandidateIds.size > 0 && receptorsAllLoaded

  return (
    <div className="space-y-5">
      {/* Page title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500/30 to-teal-500/30 border border-[var(--pos)]/30 flex items-center justify-center">
          <ShieldCheck className="w-4 h-4 text-[var(--pos)]" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-[var(--text-mute)]">Selectivity Analysis</h1>
          <p className="text-[10px] text-[var(--text-dim)]">
            Multi-receptor ΔΔG scoring — SSTR2 vs off-targets (SSTR1/3/4/5)
          </p>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-lg border border-[var(--neg)]/30 bg-[var(--neg-soft)] px-3 py-2.5 text-xs text-[var(--neg)]">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Section 1: Receptor Status */}
      <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-elev)] p-4">
        <ReceptorUpload
          receptors={receptors}
          onUpload={uploadReceptor}
          onRefresh={fetchReceptors}
        />
      </section>

      {/* Section 2: Candidate Selection */}
      <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-elev)] p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-[var(--text-mute)]">Candidate Selection</h2>
            <p className="text-[10px] text-[var(--text-dim)] mt-0.5">
              Choose from existing pipeline results ({pipelineCandidates.length} available)
            </p>
          </div>
          {pipelineCandidates.length > 0 && (
            <button
              onClick={toggleAll}
              className="text-[10px] text-[var(--accent)] hover:text-[var(--accent)] transition-colors"
            >
              {selectedCandidateIds.size === pipelineCandidates.length ? 'Deselect all' : 'Select all'}
            </button>
          )}
        </div>

        {pipelineCandidates.length === 0 ? (
          <p className="text-xs text-[var(--text-dim)] py-4 text-center">
            No pipeline candidates available. Run Silo B pipeline first.
          </p>
        ) : (
          <div className="rounded-lg border border-[var(--border)] overflow-hidden max-h-56 overflow-y-auto">
            <table className="w-full text-xs" aria-label="Pipeline candidates for selection">
              <thead className="sticky top-0 bg-[var(--bg)] backdrop-blur-sm">
                <tr className="border-b border-[var(--border)]">
                  <th scope="col" className="px-3 py-1.5 w-8">
                    <input
                      type="checkbox"
                      checked={selectedCandidateIds.size === pipelineCandidates.length && pipelineCandidates.length > 0}
                      onChange={toggleAll}
                      aria-label="Select all candidates"
                      className="accent-cyan-400"
                    />
                  </th>
                  <th scope="col" className="px-3 py-1.5 text-left text-[10px] text-[var(--text-dim)] font-medium">ID</th>
                  <th scope="col" className="px-3 py-1.5 text-left text-[10px] text-[var(--text-dim)] font-medium">Sequence</th>
                  <th scope="col" className="px-3 py-1.5 text-right text-[10px] text-[var(--text-dim)] font-medium">ΔG (kcal/mol)</th>
                  <th scope="col" className="px-3 py-1.5 text-center text-[10px] text-[var(--text-dim)] font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {pipelineCandidates.map(c => {
                  const checked = selectedCandidateIds.has(c.id)
                  return (
                    <tr
                      key={c.id}
                      onClick={() => toggleCandidate(c.id)}
                      className={`border-b border-[var(--border)] cursor-pointer transition-colors ${
                        checked ? 'bg-[var(--accent-soft)]' : 'hover:bg-[var(--bg-sunk)]'
                      }`}
                    >
                      <td className="px-3 py-1.5 text-center">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleCandidate(c.id)}
                          onClick={e => e.stopPropagation()}
                          aria-label={`Select candidate ${c.id}`}
                          className="accent-cyan-400"
                        />
                      </td>
                      <td className="px-3 py-1.5 font-mono text-[var(--text-mute)] text-[10px] whitespace-nowrap">{c.id}</td>
                      <td className="px-3 py-1.5 font-mono text-[var(--text-dim)] text-[10px] max-w-[160px] truncate" title={c.sequence}>
                        {c.sequence}
                      </td>
                      <td className={`px-3 py-1.5 text-right tabular-nums text-[10px] ${
                        c.ddG <= -8.5 ? 'text-[var(--pos)]' : c.ddG <= -6 ? 'text-[var(--warn)]' : 'text-[var(--neg)]'
                      }`}>
                        {c.ddG.toFixed(2)}
                      </td>
                      <td className="px-3 py-1.5 text-center">
                        <span className={`text-[10px] font-semibold ${
                          c.result === 'PASS' ? 'text-[var(--pos)]' : c.result === 'FAIL' ? 'text-[var(--neg)]' : 'text-[var(--text-dim)]'
                        }`}>
                          {c.result}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="mt-2 text-[10px] text-[var(--text-dim)]">
          {selectedCandidateIds.size} candidate{selectedCandidateIds.size !== 1 ? 's' : ''} selected
        </p>
      </section>

      {/* Section 3: Run Controls */}
      <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-elev)] p-4">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] mb-3">Run Controls</h2>

        {!receptorsAllLoaded && (
          <div className="flex items-center gap-2 mb-3 text-[10px] text-[var(--warn)]">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            Load all 4 off-target receptor structures (SSTR1/3/4/5) before running analysis.
          </div>
        )}

        <div className="flex items-center gap-4">
          <button
            onClick={handleRun}
            disabled={!canRun && !isRunning}
            aria-label={isRunning ? 'Stop selectivity analysis' : 'Run selectivity analysis'}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
              isRunning
                ? 'bg-[var(--neg-soft)] border border-[var(--neg)]/30 text-[var(--neg)] hover:bg-[var(--neg-soft)]'
                : canRun
                  ? 'bg-[var(--pos-soft)] border border-[var(--pos)]/30 text-[var(--pos)] hover:bg-[var(--pos-soft)]'
                  : 'bg-[var(--bg-sunk)] border border-[var(--border)] text-[var(--text-dim)] cursor-not-allowed'
            }`}
          >
            {isRunning ? (
              <><Square className="w-3.5 h-3.5" /> Stop Analysis</>
            ) : (
              <><Play className="w-3.5 h-3.5" /> Run Selectivity Analysis</>
            )}
          </button>

          {isRunning && (
            <div className="flex-1 max-w-md space-y-1.5">
              <div className="flex items-center justify-between text-[10px] text-[var(--text-dim)]">
                <span>Analyzing {selectedCandidateIds.size} candidate{selectedCandidateIds.size !== 1 ? 's' : ''} vs 4 receptors</span>
                <span className="tabular-nums">{progress}%</span>
              </div>
              {receptorProgress.length > 0 ? (
                <div className="grid grid-cols-4 gap-2">
                  {receptorProgress.map(rp => {
                    const pct = rp.total > 0 ? Math.round((rp.completed / rp.total) * 100) : 0
                    const done = pct === 100
                    return (
                      <div key={rp.name}>
                        <div className="flex items-center justify-between text-[9px] text-[var(--text-dim)] mb-0.5">
                          <span className={done ? 'text-[var(--pos)]' : ''}>{rp.name}</span>
                          <span className="tabular-nums">{rp.completed}/{rp.total}</span>
                        </div>
                        <div className="h-1 rounded-full bg-[var(--bg-sunk)] overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              done ? 'bg-green-500' : 'bg-gradient-to-r from-emerald-500 to-teal-400'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="h-1.5 rounded-full bg-[var(--bg-sunk)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {!isRunning && candidates.length > 0 && (
            <span className="text-[10px] text-[var(--pos)]">
              Analysis complete — {candidates.length} results
            </span>
          )}
        </div>
      </section>

      {/* Section 4: Results */}
      {candidates.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-[var(--text-mute)]">Results</h2>

          {/* HeuristicBanner — Boltz iPTM 신뢰도 등급 C 경고 */}
          <HeuristicBanner
            grade="C"
            warnings={BOLTZ_IPTM_WARNINGS}
          />

          {/* Charts */}
          <SelectivityChart candidates={candidates} selectedIds={selectedResultIds} />

          {/* Table */}
          <SelectivityTable candidates={candidates} onRowClick={handleRowClick} />
        </section>
      )}

      {/* Section 5: Archives Top-K — 1,615 페어 평가 결과 */}
      <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-elev)] p-4">
        <ArchivesTopKSlider />
      </section>
    </div>
  )
}
