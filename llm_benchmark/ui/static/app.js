const app = document.getElementById('app')

const state = {
  overview: null,
  phase: null,
}

function fmtSeconds(value) {
  if (value == null || Number.isNaN(value)) return '—'
  if (value < 60) return `${value.toFixed(1)}s`
  const minutes = Math.floor(value / 60)
  const seconds = Math.round(value % 60)
  return `${minutes}m ${seconds}s`
}

function fmtNum(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

function getPhase() {
  return state.overview?.phases.find((item) => item.phase === state.phase) ?? state.overview?.phases?.[0] ?? null
}

function insightCards(phase) {
  const models = [...phase.model_rows].filter((row) => row.mean_elapsed_s != null).sort((a, b) => a.mean_elapsed_s - b.mean_elapsed_s)
  const gates = [...phase.gate_rows].filter((row) => row.mean_elapsed_s != null).sort((a, b) => a.mean_elapsed_s - b.mean_elapsed_s)
  const fastest = models[0]
  const slowest = models[models.length - 1]
  const gateLead = gates[0]

  return [
    fastest ? `${escapeHtml(fastest.model)} is the fastest LLM in ${escapeHtml(phase.phase)} at ${fmtSeconds(fastest.mean_elapsed_s)} mean runtime.` : 'No completed runs are available for model comparison.',
    gateLead ? `${escapeHtml(gateLead.gate_mode)} gating is currently the fastest gate configuration at ${fmtSeconds(gateLead.mean_elapsed_s)} average runtime.` : 'Gate-mode comparison is not available yet.',
    fastest && slowest && fastest.model !== slowest.model ? `${escapeHtml(slowest.model)} trails ${escapeHtml(fastest.model)} by ${fmtSeconds(slowest.mean_elapsed_s - fastest.mean_elapsed_s)} on mean runtime.` : 'Inter-model separation is not large enough to highlight yet.',
  ]
}

function buildHero(phase, overview) {
  const cards = insightCards(phase)
  return `
    <section class="hero">
      <div class="hero-top">
        <div>
          <span class="badge">LLM Benchmark Observatory</span>
          <h1>LLM 비교 / Flow 비교 / Gate 비교용 독립 UI</h1>
          <p><span class="mono">${escapeHtml(overview.outputs_root)}</span>를 읽고, 기존 <span class="mono">llm_benchmark.scoring.aggregate</span> 로직을 활용해 phase별 LLM 성능 비교, flow 비교, gate mode 비교, raw run coverage를 분리해서 보여줍니다.</p>
        </div>
        <div class="controls">
          <label class="control">Phase
            <select id="phase-select">
              ${overview.available_phases.map((item) => `<option value="${escapeHtml(item)}" ${item === phase.phase ? 'selected' : ''}>${escapeHtml(item)}</option>`).join('')}
            </select>
          </label>
          <button class="control" id="refresh-btn">Refresh</button>
        </div>
      </div>
      <section class="kpis">
        <article class="kpi">
          <div class="eyebrow">Run Dirs</div>
          <div class="value">${phase.total_run_dirs}</div>
          <div class="caption">raw outputs scanned from the selected phase</div>
        </article>
        <article class="kpi">
          <div class="eyebrow">Completed</div>
          <div class="value">${phase.completed_runs}</div>
          <div class="caption">runs accepted by <span class="mono">load_phase_results()</span></div>
        </article>
        <article class="kpi">
          <div class="eyebrow">SES Coverage</div>
          <div class="value">${fmtNum(phase.score_coverage_pct)}%</div>
          <div class="caption">${phase.scored_runs}/${phase.completed_runs} completed runs have <span class="mono">ses_score.json</span></div>
        </article>
        <article class="kpi">
          <div class="eyebrow">Mean Runtime</div>
          <div class="value">${fmtSeconds(phase.elapsed_stats.mean_s)}</div>
          <div class="caption">median ${fmtSeconds(phase.elapsed_stats.median_s)} / spread ${fmtSeconds(phase.elapsed_stats.range_s)}</div>
        </article>
      </section>
      <div class="insights">
        ${cards.map((card) => `<article class="insight">${card}</article>`).join('')}
      </div>
    </section>
  `
}

function buildBarPanel(title, subtitle, rows, labelKey, valueKey) {
  if (!rows.length) {
    return `<section class="panel"><h3>${escapeHtml(title)}</h3><p class="sub">${escapeHtml(subtitle)}</p><div class="empty">No completed runs available.</div></section>`
  }
  const max = Math.max(...rows.map((row) => row[valueKey] || 0), 1)
  return `
    <section class="panel">
      <h3>${escapeHtml(title)}</h3>
      <p class="sub">${escapeHtml(subtitle)}</p>
      <div class="bar-list" style="margin-top:16px;">
        ${rows.map((row) => `
          <div class="bar-row">
            <div>${escapeHtml(row[labelKey])}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${((row[valueKey] || 0) / max) * 100}%"></div></div>
            <div class="mono">${fmtSeconds(row[valueKey])}</div>
          </div>
        `).join('')}
      </div>
    </section>
  `
}

function buildStatePanel(phase) {
  const entries = Object.entries(phase.state_counts)
  const total = entries.reduce((sum, [, value]) => sum + value, 0) || 1
  return `
    <section class="panel">
      <h3>Run State Coverage</h3>
      <p class="sub">phase 디렉터리 전체에서 raw 상태 분포를 보여줍니다.</p>
      <div class="bar-list" style="margin-top:16px;">
        ${entries.map(([key, value]) => `
          <div class="bar-row">
            <div>${escapeHtml(key)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${(value / total) * 100}%; background:${key === 'done' ? 'linear-gradient(90deg, #2dd4bf, #38bdf8)' : 'linear-gradient(90deg, #f59e0b, #fb7185)'}"></div></div>
            <div class="mono">${value}</div>
          </div>
        `).join('')}
      </div>
    </section>
  `
}

function buildModelTable(phase) {
  const rows = [...phase.model_rows].sort((a, b) => (a.mean_elapsed_s ?? Infinity) - (b.mean_elapsed_s ?? Infinity))
  return `
    <section class="panel">
      <h3>LLM Comparison</h3>
      <p class="sub">existing aggregate summary grouped by model</p>
      <div class="table-wrap" style="margin-top:14px;">
        <table class="table">
          <thead><tr><th>Model</th><th>Runs</th><th>Scored</th><th>Mean Time</th><th>SES Mean</th><th>SES Std</th><th>Best ddG</th></tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>${escapeHtml(row.model)}</td>
                <td class="mono">${row.n_runs}</td>
                <td class="mono">${row.n_scored}</td>
                <td class="mono">${fmtSeconds(row.mean_elapsed_s)}</td>
                <td class="mono">${fmtNum(row.ses_mean)}</td>
                <td class="mono">${fmtNum(row.ses_stdev)}</td>
                <td class="mono">${fmtNum(row.best_ddg_mean)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `
}

function buildFlowTable(phase) {
  const rows = [...phase.flow_rows].sort((a, b) => (a.mean_elapsed_s ?? Infinity) - (b.mean_elapsed_s ?? Infinity))
  return `
    <section class="panel">
      <h3>Flow Comparison</h3>
      <p class="sub">aggregate_by_model_flow() output with runtime overlay</p>
      <div class="table-wrap" style="margin-top:14px;">
        <table class="table">
          <thead><tr><th>Model</th><th>Flow</th><th>Runs</th><th>Mean Time</th><th>SES Mean</th><th>SES Std</th></tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>${escapeHtml(row.model)}</td>
                <td>${escapeHtml(row.flow)}</td>
                <td class="mono">${row.n_runs}</td>
                <td class="mono">${fmtSeconds(row.mean_elapsed_s)}</td>
                <td class="mono">${fmtNum(row.ses_mean)}</td>
                <td class="mono">${fmtNum(row.ses_stdev)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `
}

function buildGateTable(phase) {
  const rows = [...phase.gate_rows].sort((a, b) => (a.mean_elapsed_s ?? Infinity) - (b.mean_elapsed_s ?? Infinity))
  return `
    <section class="panel">
      <h3>Gate Mode Comparison</h3>
      <p class="sub">static vs adaptive gate mode comparison across completed runs</p>
      <div class="table-wrap" style="margin-top:14px;">
        <table class="table">
          <thead><tr><th>Gate</th><th>Runs</th><th>Scored</th><th>Mean Time</th><th>SES Mean</th><th>Models</th></tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>${escapeHtml(row.gate_mode)}</td>
                <td class="mono">${row.n_runs}</td>
                <td class="mono">${row.n_scored}</td>
                <td class="mono">${fmtSeconds(row.mean_elapsed_s)}</td>
                <td class="mono">${fmtNum(row.ses_mean)}</td>
                <td>${escapeHtml(row.models.join(', '))}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `
}

function buildHeatmap(phase) {
  const seeds = phase.heatmap_seeds || []
  const rows = phase.heatmap_rows || []
  if (!rows.length) {
    return `<section class="panel"><h3>Model x Seed Heatmap</h3><p class="sub">raw elapsed time matrix</p><div class="empty">No runs found.</div></section>`
  }
  const max = Math.max(...rows.flatMap((row) => row.cells.map((cell) => cell.elapsed_s || 0)), 1)
  const gridTemplate = `220px repeat(${seeds.length}, minmax(120px, 1fr))`
  return `
    <section class="panel">
      <h3>Model x Seed Heatmap</h3>
      <p class="sub">raw run-level runtime matrix grouped by model and gate mode</p>
      <div class="heatmap" style="margin-top:14px;">
        <div class="heatmap-row" style="grid-template-columns:${gridTemplate};">
          <div></div>
          ${seeds.map((seed) => `<div class="heat-label" style="min-height:54px; justify-content:center;">seed ${seed}</div>`).join('')}
        </div>
        ${rows.map((row) => `
          <div class="heatmap-row" style="grid-template-columns:${gridTemplate};">
            <div class="heat-label">${escapeHtml(row.label)}</div>
            ${row.cells.map((cell) => {
              const ratio = (cell.elapsed_s || 0) / max
              const bg = cell.elapsed_s != null ? `rgba(56, 189, 248, ${0.16 + ratio * 0.48})` : 'rgba(7, 17, 31, 0.5)'
              return `<div class="heat-cell" style="background:${bg}"><strong>${fmtSeconds(cell.elapsed_s)}</strong><span class="small-note">${escapeHtml(cell.state)}</span></div>`
            }).join('')}
          </div>
        `).join('')}
      </div>
    </section>
  `
}

function buildRunTable(phase) {
  const rows = [...phase.raw_runs].sort((a, b) => (a.elapsed_s ?? Infinity) - (b.elapsed_s ?? Infinity))
  return `
    <section class="panel">
      <h3>Raw Run Ledger</h3>
      <p class="sub">status/config snapshot 기반의 원본 run view</p>
      <div class="table-wrap" style="margin-top:14px; max-height:520px;">
        <table class="table">
          <thead><tr><th>Model</th><th>Flow</th><th>Gate</th><th>Seed</th><th>State</th><th>Elapsed</th><th>Status</th></tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>${escapeHtml(row.model)}</td>
                <td>${escapeHtml(row.flow)}</td>
                <td>${escapeHtml(row.gate_mode)}</td>
                <td class="mono">${row.seed}</td>
                <td><span class="status-pill ${row.state === 'done' ? '' : 'pending'}">${escapeHtml(row.state)}</span></td>
                <td class="mono">${fmtSeconds(row.elapsed_s)}</td>
                <td class="mono">${escapeHtml(row.status_path)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `
}

function render() {
  const overview = state.overview
  const phase = getPhase()
  if (!overview || !phase) {
    app.innerHTML = '<div class="app-shell"><section class="panel empty">No benchmark data found.</section></div>'
    return
  }

  app.innerHTML = `
    <div class="app-shell">
      ${buildHero(phase, overview)}
      <section class="grid-2">
        ${buildBarPanel('LLM Runtime Leaderboard', 'mean runtime per model from completed runs', [...phase.model_rows].filter((row) => row.mean_elapsed_s != null).sort((a, b) => a.mean_elapsed_s - b.mean_elapsed_s), 'model', 'mean_elapsed_s')}
        ${buildStatePanel(phase)}
      </section>
      <section class="grid-3">
        ${buildModelTable(phase)}
        ${buildFlowTable(phase)}
        ${buildGateTable(phase)}
      </section>
      ${buildHeatmap(phase)}
      ${buildRunTable(phase)}
    </div>
  `

  document.getElementById('phase-select').addEventListener('change', (event) => {
    state.phase = event.target.value
    render()
  })
  document.getElementById('refresh-btn').addEventListener('click', () => load())
}

async function load() {
  app.innerHTML = '<div class="app-shell"><section class="panel empty">Loading benchmark overview...</section></div>'
  const response = await fetch('/api/overview')
  if (!response.ok) {
    app.innerHTML = `<div class="app-shell"><section class="panel empty">Failed to load overview (${response.status}).</section></div>`
    return
  }
  state.overview = await response.json()
  if (!state.phase) state.phase = state.overview.latest_phase
  render()
}

load()
