/* global React */
// LLM Benchmark — 5 sLLM × 3 flow comparison
// Inspired by docs/experiment_final_report.md and llm_benchmark/

function ScreenBenchmark() {
  const rootRef = React.useRef(null);
  const [phase, setPhase] = React.useState("V2");
  const [metric, setMetric] = React.useState("pass_rate");
  const [hoverCell, setHoverCell] = React.useState(null);

  const llms = [
    { id: "qwen3-32b", short: "q32", vram: "80 GB", color: "var(--accent)" },
    { id: "qwen3-14b", short: "q14", vram: "40 GB", color: "var(--teal)" },
    { id: "qwen3-7b", short: "q7", vram: "20 GB", color: "var(--violet)" },
    { id: "gpt-oss-120b", short: "g120", vram: "240 GB", color: "var(--warn)" },
    { id: "deepseek-r1-distill-32b", short: "ds32", vram: "80 GB", color: "var(--pos)" },
  ];
  const flows = [
    { id: "sequential", name: "Sequential", desc: "P→B→Q→C→R 단방향" },
    { id: "collaborative", name: "Collaborative", desc: "DebatingPlanner · 다중 합의" },
    { id: "hierarchical", name: "Hierarchical", desc: "Orchestrator · 승인/통합" },
  ];

  // Synthetic but plausible results matrix (model × flow)
  const results = {
    "qwen3-32b": {
      sequential:    { pass: 87, time: 38, candidates: 12, t2: 1, cost: 1.0,  rank: 1 },
      collaborative: { pass: 82, time: 51, candidates: 14, t2: 1, cost: 1.4,  rank: 2 },
      hierarchical:  { pass: 78, time: 49, candidates: 11, t2: 0, cost: 1.5,  rank: 4 },
    },
    "qwen3-14b": {
      sequential:    { pass: 81, time: 32, candidates: 10, t2: 0, cost: 0.5,  rank: 3 },
      collaborative: { pass: 76, time: 43, candidates: 12, t2: 0, cost: 0.7,  rank: 5 },
      hierarchical:  { pass: 71, time: 41, candidates: 9,  t2: 0, cost: 0.7,  rank: 7 },
    },
    "qwen3-7b": {
      sequential:    { pass: 62, time: 22, candidates: 7,  t2: 0, cost: 0.25, rank: 10 },
      collaborative: { pass: 57, time: 31, candidates: 8,  t2: 0, cost: 0.35, rank: 12 },
      hierarchical:  { pass: 52, time: 30, candidates: 6,  t2: 0, cost: 0.36, rank: 14 },
    },
    "gpt-oss-120b": {
      sequential:    { pass: 90, time: 58, candidates: 13, t2: 1, cost: 2.8,  rank: 1 },
      collaborative: { pass: 88, time: 75, candidates: 15, t2: 2, cost: 3.7,  rank: 1 },
      hierarchical:  { pass: 84, time: 71, candidates: 12, t2: 1, cost: 3.8,  rank: 3 },
    },
    "deepseek-r1-distill-32b": {
      sequential:    { pass: 79, time: 42, candidates: 10, t2: 0, cost: 1.1,  rank: 6 },
      collaborative: { pass: 81, time: 56, candidates: 13, t2: 1, cost: 1.5,  rank: 5 },
      hierarchical:  { pass: 73, time: 53, candidates: 10, t2: 0, cost: 1.6,  rank: 8 },
    },
  };

  function cellValue(llm, flow) {
    const r = results[llm][flow];
    if (metric === "pass_rate") return { v: r.pass, label: `${r.pass}%`, max: 100 };
    if (metric === "time") return { v: r.time, label: `${r.time}m`, max: 80, inverse: true };
    if (metric === "candidates") return { v: r.candidates, label: `${r.candidates}`, max: 16 };
    if (metric === "t2") return { v: r.t2, label: `${r.t2}`, max: 2 };
    if (metric === "cost") return { v: r.cost, label: `${r.cost}×`, max: 4, inverse: true };
    return { v: 0, label: "" };
  }

  function cellColor(v) {
    const t = Math.max(0, Math.min(1, v));
    if (t < 0.4) return `oklch(0.94 0.06 ${PROJECT_DATA && 25})`;
    if (t < 0.7) return `oklch(0.9 0.08 70)`;
    return `oklch(0.88 0.12 var(--pos-hue))`;
  }

  return (
    <div ref={rootRef} data-theme="light" style={{
      width: "100%", height: "100%",
      background: "var(--bg)", color: "var(--text)",
      fontFamily: "Inter, sans-serif", fontSize: 13,
      display: "flex", flexDirection: "column",
    }}>
      <header style={{
        display: "flex", alignItems: "center", gap: 14,
        padding: "10px 20px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-elev)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 3v18h18M7 14l4-4 4 4 5-5"/></svg>
          <div style={{ fontWeight: 600 }}>LLM Benchmark · 5 sLLM × 3 flow</div>
          <span className="bio-pill" style={{ padding: "1px 6px", fontSize: 10 }}>199 runs · Phase 1–3 + V2</span>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", gap: 0, border: "1px solid var(--border-strong)", borderRadius: 3, overflow: "hidden" }}>
          {["Phase1", "Phase2", "Phase3", "V2"].map(p => (
            <button key={p} onClick={() => setPhase(p)} className="bio-btn"
              style={{
                padding: "3px 10px", fontSize: 11, borderRadius: 0, border: 0,
                background: phase === p ? "var(--text)" : "var(--bg-elev)",
                color: phase === p ? "var(--bg-elev)" : "var(--text-mute)",
              }}>{p}</button>
          ))}
        </div>
        <ThemeToggle scope={rootRef} />
      </header>

      <div style={{ flex: 1, overflow: "auto", padding: "16px 20px" }}>
        <div style={{ maxWidth: 1320, margin: "0 auto", display: "flex", flexDirection: "column", gap: 14 }}>

          {/* Top stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
            <BigCard label="Total runs" value="199" sub="Phase 1–3 + V2 P1/P2" />
            <BigCard label="Best model" value="gpt-oss-120b" sub="92% mean pass" tone="pos" mono />
            <BigCard label="Best flow" value="sequential" sub="가장 안정적" mono />
            <BigCard label="Speed champ" value="qwen3-7b" sub="22 min · seq" tone="warn" mono />
            <BigCard label="Cost champ" value="qwen3-7b" sub="0.25× cost / run" tone="warn" mono />
          </div>

          {/* Metric toggle */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span className="bio-label">Metric</span>
            <div style={{ display: "flex", gap: 2, border: "1px solid var(--border-strong)", borderRadius: 3, overflow: "hidden" }}>
              {[
                { id: "pass_rate", label: "Pass rate" },
                { id: "candidates", label: "후보 수" },
                { id: "t2", label: "T2 hits" },
                { id: "time", label: "Time" },
                { id: "cost", label: "Cost" },
              ].map(m => (
                <button key={m.id} onClick={() => setMetric(m.id)} className="bio-btn" style={{
                  padding: "3px 12px", fontSize: 11, borderRadius: 0, border: 0,
                  background: metric === m.id ? "var(--accent)" : "var(--bg-elev)",
                  color: metric === m.id ? "white" : "var(--text-mute)",
                }}>{m.label}</button>
              ))}
            </div>
            <div style={{ flex: 1 }} />
            <span className="mono" style={{ fontSize: 10.5, color: "var(--text-mute)" }}>
              source: llm_benchmark/run_v2_all.sh · seeds × 6
            </span>
          </div>

          {/* Heatmap */}
          <div className="bio-panel">
            <div className="bio-panel-hd">
              <span>Model × Flow Matrix</span>
              <span className="mono" style={{ fontSize: 10 }}>cell = mean over 6 seeds</span>
            </div>
            <div style={{ padding: "16px 20px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "200px repeat(3, 1fr) 70px", gap: 8 }}>
                {/* Header */}
                <div />
                {flows.map(f => (
                  <div key={f.id} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 12, fontWeight: 600 }}>{f.name}</div>
                    <div style={{ fontSize: 10, color: "var(--text-mute)" }}>{f.desc}</div>
                  </div>
                ))}
                <div className="bio-label" style={{ textAlign: "right" }}>best</div>

                {/* Rows */}
                {llms.map(llm => {
                  const flowResults = flows.map(f => ({ flow: f.id, ...cellValue(llm.id, f.id), res: results[llm.id][f.id] }));
                  const bestFlow = flowResults.reduce((b, c) => {
                    const cv = metric === "time" || metric === "cost" ? -c.v : c.v;
                    const bv = metric === "time" || metric === "cost" ? -b.v : b.v;
                    return cv > bv ? c : b;
                  });
                  return (
                    <React.Fragment key={llm.id}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 2, padding: "10px 0" }}>
                        <div className="mono" style={{ fontWeight: 600, fontSize: 12.5 }}>{llm.id}</div>
                        <div style={{ fontSize: 10, color: "var(--text-mute)" }} className="mono">{llm.vram}</div>
                      </div>
                      {flowResults.map((r, i) => {
                        const t = Math.min(1, r.v / r.max);
                        const effective = r.inverse ? 1 - t : t;
                        const isHover = hoverCell?.llm === llm.id && hoverCell?.flow === r.flow;
                        const isBest = bestFlow.flow === r.flow;
                        return (
                          <div key={r.flow}
                            onMouseEnter={() => setHoverCell({ llm: llm.id, flow: r.flow, res: r.res })}
                            onMouseLeave={() => setHoverCell(null)}
                            style={{
                              padding: "10px 12px", borderRadius: 4,
                              background: `oklch(${0.95 - effective * 0.15} ${effective * 0.13} ${effective > 0.5 ? "var(--pos-hue)" : "var(--warn-hue)"})`,
                              border: isBest ? "2px solid var(--text)" : "1px solid var(--border)",
                              cursor: "pointer", position: "relative",
                              transition: "transform 0.15s", transform: isHover ? "translateY(-1px)" : "none",
                            }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                              <span className="mono" style={{ fontSize: 17, fontWeight: 700 }}>{r.label}</span>
                              {isBest && <span style={{ fontSize: 9, color: "var(--text-mute)" }} className="mono">★ best</span>}
                            </div>
                            <div style={{ height: 3, background: "rgba(0,0,0,0.05)", marginTop: 6, borderRadius: 2, overflow: "hidden" }}>
                              <div style={{ width: `${effective * 100}%`, height: "100%", background: "rgba(0,0,0,0.4)" }} />
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "var(--text-mute)", marginTop: 3 }} className="mono">
                              <span>cand {r.res.candidates}</span>
                              <span>T2 {r.res.t2}</span>
                              <span>{r.res.time}m</span>
                            </div>
                          </div>
                        );
                      })}
                      <div className="mono" style={{ textAlign: "right", padding: "10px 0", color: "var(--accent-text)", fontWeight: 600, fontSize: 12 }}>
                        {bestFlow.flow.slice(0, 3)}
                      </div>
                    </React.Fragment>
                  );
                })}
              </div>
            </div>

            {/* Hover detail */}
            {hoverCell && (
              <div style={{
                padding: "10px 20px", borderTop: "1px solid var(--border)",
                background: "var(--bg-sunk)", fontSize: 11,
                display: "flex", gap: 14, alignItems: "center",
              }}>
                <span className="mono" style={{ fontWeight: 600 }}>{hoverCell.llm} × {hoverCell.flow}</span>
                <span style={{ color: "var(--text-mute)" }}>pass <strong style={{ color: "var(--pos)" }}>{hoverCell.res.pass}%</strong></span>
                <span style={{ color: "var(--text-mute)" }}>time <strong>{hoverCell.res.time}m</strong></span>
                <span style={{ color: "var(--text-mute)" }}>candidates <strong>{hoverCell.res.candidates}</strong></span>
                <span style={{ color: "var(--text-mute)" }}>T2 hits <strong style={{ color: "var(--pos)" }}>{hoverCell.res.t2}</strong></span>
                <span style={{ color: "var(--text-mute)" }}>cost <strong>{hoverCell.res.cost}×</strong></span>
                <span style={{ flex: 1 }} />
                <button className="bio-btn ghost" style={{ fontSize: 10 }}>open run trace →</button>
              </div>
            )}
          </div>

          {/* Bottom: per-flow stacked bar comparison + cost/perf scatter */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Flow별 평균 pass rate</span><span className="mono" style={{ fontSize: 10 }}>across 5 LLMs</span></div>
              <div style={{ padding: "14px 20px", display: "flex", flexDirection: "column", gap: 10 }}>
                {flows.map(f => {
                  const avg = llms.reduce((sum, l) => sum + results[l.id][f.id].pass, 0) / llms.length;
                  return (
                    <div key={f.id}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                        <span style={{ fontWeight: 500 }}>{f.name}</span>
                        <span className="mono" style={{ fontWeight: 600 }}>{avg.toFixed(1)}%</span>
                      </div>
                      <div style={{ display: "flex", height: 18, marginTop: 4, background: "var(--bg-sunk)", borderRadius: 3, overflow: "hidden" }}>
                        {llms.map(l => (
                          <div key={l.id} style={{
                            width: `${results[l.id][f.id].pass / 5}%`,
                            height: "100%", background: l.color, opacity: 0.85,
                            borderRight: "1px solid var(--bg-elev)",
                          }}
                            title={`${l.short}: ${results[l.id][f.id].pass}%`} />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ padding: "8px 20px", borderTop: "1px solid var(--border)", display: "flex", gap: 12, flexWrap: "wrap", fontSize: 10 }}>
                {llms.map(l => (
                  <span key={l.id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <span style={{ width: 10, height: 10, background: l.color, borderRadius: 2 }} />
                    <span className="mono">{l.short}</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Cost / Performance scatter</span><span className="mono" style={{ fontSize: 10 }}>x · 비용 ↑ · y · 후보 수 ↑</span></div>
              <CostScatter llms={llms} results={results} flows={flows} />
            </div>
          </div>

          {/* Take-aways */}
          <div className="bio-panel">
            <div className="bio-panel-hd"><span>핵심 발견</span></div>
            <div style={{ padding: "12px 20px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
              <Finding
                title="GPT-OSS-120B + Collaborative" tone="pos"
                text="유일하게 2개 T2 후보 산출 (cand03 + 후속 변이). 비용 3.7×이나 quality는 최고."
              />
              <Finding
                title="Qwen3-32B + Sequential 추천" tone="accent"
                text="평균 87% pass / 38m / 후보 12개. 비용 1× — 일상 dev 권장."
              />
              <Finding
                title="Hierarchical은 어디서나 −5%" tone="warn"
                text="Orchestrator overhead, 합의 지연. 복잡 의사결정 외엔 비추천."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BigCard({ label, value, sub, tone, mono }) {
  const color = tone === "pos" ? "var(--pos)" : tone === "warn" ? "var(--warn)" : "var(--text)";
  return (
    <div style={{ padding: "10px 12px", background: "var(--bg-elev)", border: "1px solid var(--border)", borderRadius: 4 }}>
      <div className="bio-label">{label}</div>
      <div className={mono ? "mono" : ""} style={{ fontSize: 16, fontWeight: 600, color, marginTop: 2, lineHeight: 1.15 }}>{value}</div>
      <div style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 2 }}>{sub}</div>
    </div>
  );
}

function CostScatter({ llms, results, flows }) {
  // x: cost 0-4 ; y: candidates 0-16
  return (
    <div style={{ padding: "16px 20px", position: "relative", height: 200 }}>
      {/* Grid lines */}
      {[0.25, 0.5, 0.75].map(p => (
        <div key={p} style={{ position: "absolute", left: 0, right: 30, top: `${p * 100}%`, height: 1, background: "var(--border)" }} />
      ))}
      {/* dots */}
      {llms.map(l => flows.map(f => {
        const r = results[l.id][f.id];
        const x = (r.cost / 4) * 100;
        const y = (1 - r.candidates / 16) * 100;
        return (
          <div key={l.id + f.id} title={`${l.short} × ${f.id} · $${r.cost}× · ${r.candidates}cand`}
            style={{
              position: "absolute",
              left: `calc(${x}% - 5px)`, top: `${y}%`,
              width: 10, height: 10, borderRadius: "50%",
              background: l.color, opacity: 0.85,
              border: f.id === "sequential" ? "1.5px solid white" : f.id === "collaborative" ? "1.5px dashed white" : "none",
              boxShadow: "0 0 0 1px var(--border)",
            }} />
        );
      }))}
      {/* axes */}
      <div style={{ position: "absolute", bottom: -2, left: 0, right: 30, height: 1, background: "var(--border-strong)" }} />
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 1, background: "var(--border-strong)" }} />
      <div style={{ position: "absolute", bottom: -18, left: 0, fontSize: 9 }} className="mono">0×</div>
      <div style={{ position: "absolute", bottom: -18, right: 30, fontSize: 9 }} className="mono">4× cost</div>
      <div style={{ position: "absolute", top: 0, right: 0, fontSize: 9, transform: "translate(0, -8px)" }} className="mono">16 cand</div>
      <div style={{ position: "absolute", bottom: 0, right: 0, fontSize: 9, transform: "translate(0, 8px)" }} className="mono">0</div>
    </div>
  );
}

function Finding({ title, text, tone }) {
  const color = tone === "pos" ? "var(--pos)" : tone === "accent" ? "var(--accent-text)" : tone === "warn" ? "var(--warn)" : "var(--text)";
  const bg = tone === "pos" ? "var(--pos-soft)" : tone === "accent" ? "var(--accent-soft)" : tone === "warn" ? "var(--warn-soft)" : "var(--bg-sunk)";
  return (
    <div style={{ padding: "10px 12px", background: bg, borderRadius: 3, borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: 12, fontWeight: 600, color, marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 11.5, lineHeight: 1.5 }}>{text}</div>
    </div>
  );
}

window.ScreenBenchmark = ScreenBenchmark;
