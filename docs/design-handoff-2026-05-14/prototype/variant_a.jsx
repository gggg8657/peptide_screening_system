/* global React, PROJECT_DATA */
const { useState: useStateA, useEffect: useEffectA, useRef: useRefA, useMemo: useMemoA } = React;

function VariantA() {
  const data = PROJECT_DATA;
  const rootRef = useRefA(null);
  const [tab, setTab] = useStateA("B"); // Silo A / B / Combined
  const [tick, setTick] = useStateA(0);
  const [hoverGate, setHoverGate] = useStateA(null);
  const [selectedCand, setSelectedCand] = useStateA("cand03");

  // Animate the agent log + step progress
  useEffectA(() => {
    const iv = setInterval(() => setTick(t => (t + 1) % 1000), 1800);
    return () => clearInterval(iv);
  }, []);

  // Which silo data to show in the pipeline
  const siloKey = tab === "A+B" ? "Combined" : tab;

  const visibleLog = data.agentLog.slice(0, Math.min(data.agentLog.length, 4 + (tick % 9)));
  const selected = data.candidates.find(c => c.id === selectedCand);

  return (
    <div ref={rootRef} data-theme="light" style={{
      width: "100%", height: "100%", display: "flex", flexDirection: "column",
      background: "var(--bg)", color: "var(--text)",
      fontFamily: "Inter, sans-serif", fontSize: 13,
    }}>
      {/* TOP BAR */}
      <header style={{
        display: "flex", alignItems: "center", gap: 16,
        padding: "8px 16px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-elev)", minHeight: 44,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 22, height: 22, borderRadius: 3,
            background: "var(--text)", color: "var(--bg-elev)",
            display: "grid", placeItems: "center", fontFamily: "JetBrains Mono", fontWeight: 700, fontSize: 11,
          }}>P*</div>
          <div style={{ fontWeight: 600, letterSpacing: -0.1 }}>PRST_N_FM</div>
          <span style={{ color: "var(--text-dim)" }}>·</span>
          <span style={{ color: "var(--text-mute)" }}>SSTR2 AI Co-Scientist</span>
        </div>
        <nav style={{ display: "flex", gap: 2, marginLeft: 16 }}>
          {["Run", "Candidates", "Selectivity", "Agents", "Settings"].map((n, i) => (
            <button key={n} className={`bio-btn ghost`} style={{
              padding: "4px 10px",
              borderBottom: i === 0 ? "2px solid var(--accent)" : "2px solid transparent",
              borderRadius: 0, color: i === 0 ? "var(--text)" : "var(--text-mute)",
              fontWeight: i === 0 ? 600 : 400,
            }}>{n}</button>
          ))}
        </nav>
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 11, color: "var(--text-mute)" }}>
          <span className="mono">{data.run.id}</span>
          <span className="bio-pill"><span className="bio-dot" />RUNNING · {data.run.duration}</span>
          <ThemeToggle scope={rootRef} />
        </div>
      </header>

      {/* SUBHEADER — run meta + iteration progress */}
      <div style={{
        display: "grid", gridTemplateColumns: "minmax(0, 1fr) 280px",
        gap: 0, borderBottom: "1px solid var(--border)",
        background: "var(--bg-elev)",
      }}>
        <div style={{ padding: "10px 16px", display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
          <Meta label="타겟" value={<span><span className="mono">SSTR2</span> · <span style={{ color: "var(--text-mute)" }} className="mono">{data.target.uniprot} · {data.target.pdb}</span></span>} />
          <Meta label="Silo" value={
            <div style={{ display: "flex", gap: 0, border: "1px solid var(--border-strong)", borderRadius: 3, overflow: "hidden" }}>
              {["A", "B", "A+B"].map(s => (
                <button key={s} onClick={() => setTab(s)} style={{
                  fontFamily: "inherit", fontSize: 11,
                  padding: "2px 10px", border: "0",
                  background: tab === s ? "var(--text)" : "transparent",
                  color: tab === s ? "var(--bg-elev)" : "var(--text-mute)",
                  cursor: "pointer",
                }}>{s === "A" ? "A · de novo" : s === "B" ? "B · mutation" : "Combined"}</button>
              ))}
            </div>
          } />
          <Meta label="Iteration" value={
            <span><span className="mono" style={{ fontSize: 14, fontWeight: 600 }}>{data.run.iteration}</span><span style={{ color: "var(--text-dim)" }}> / {data.run.maxIter}</span></span>
          } />
          <Meta label="LLM" value={<span className="mono">{data.run.llmModel}</span>} />
          <Meta label="GPU" value={<span className="mono">{data.run.gpus}</span>} />
          <Meta label="Seed" value={<span className="mono">{data.run.seed}</span>} />
        </div>
        <div style={{
          padding: "10px 16px", borderLeft: "1px solid var(--border)",
          display: "flex", flexDirection: "column", justifyContent: "center", gap: 4,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10.5, color: "var(--text-mute)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            <span>Iter02 진행</span>
            <span className="mono">{Math.round(data.run.progress * 100)}%</span>
          </div>
          <div style={{ height: 4, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
            <div style={{
              width: `${data.run.progress * 100}%`, height: "100%",
              background: "linear-gradient(90deg, var(--accent) 0%, var(--pos) 100%)",
            }} />
          </div>
        </div>
      </div>

      {/* MAIN AREA */}
      <div style={{
        flex: 1, display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) 360px",
        gridTemplateRows: "auto 1fr",
        minHeight: 0,
      }}>
        {/* LEFT — Pipeline flow + metrics */}
        <div style={{ padding: "12px 16px", borderRight: "1px solid var(--border)", minWidth: 0 }}>
          <PipelineFlow silo={siloKey} />
          {/* Mini metrics row */}
          <div style={{
            marginTop: 10, padding: 10, background: "var(--bg-elev)",
            border: "1px solid var(--border)", borderRadius: 4,
            display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16,
          }}>
            <MiniStat label="Generated" value={tab === "A" ? "80" : tab === "B" ? "240→80" : "160"} sub={tab === "A" ? "ProteinMPNN" : tab === "B" ? "BLOSUM + dedup" : "A + B"} />
            <MiniStat label="QC G1 pass" value={tab === "A+B" ? "146" : "73"} sub={tab === "A+B" ? "of 160 (91%)" : "of 80 (91%)"} tone="pos" />
            <MiniStat label="Docking top%" value={tab === "A+B" ? "32" : "16"} sub={tab === "A+B" ? "of 146 (G2)" : "of 73 (G2)"} tone="warn" />
            <MiniStat label="T2 후보" value="1" sub="cand03" tone="pos" />
            <MiniStat label="ETA" value="4.2m" sub="step05c → 06" />
          </div>
        </div>

        {/* RIGHT — Agent log */}
        <AgentRail
          agents={data.agents}
          log={visibleLog}
          tick={tick}
        />

        {/* LEFT-BOTTOM — candidate table + detail */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) 380px",
          gap: 0,
          borderTop: "1px solid var(--border)",
          minHeight: 0,
        }}>
          <CandidatesTable
            candidates={data.candidates}
            selected={selectedCand}
            onSelect={setSelectedCand}
            silo={tab}
          />
          <RightDetail
            candidate={selected}
            gates={data.gates}
            onHoverGate={setHoverGate}
            hoverGate={hoverGate}
          />
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <span className="bio-label">{label}</span>
      <span style={{ fontSize: 12 }}>{value}</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function PipelineStrip({ steps, currentIdx, tick }) {
  return (
    <div style={{
      borderRight: "1px solid var(--border)",
      background: "var(--bg-elev)",
      padding: "12px 16px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
        <div className="bio-label">파이프라인 — 8 Steps</div>
        <div style={{ fontSize: 11, color: "var(--text-mute)" }} className="mono">
          step {steps[currentIdx]?.id} · {steps[currentIdx]?.tool}
        </div>
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))`,
        gap: 4,
      }}>
        {steps.map((s, i) => {
          const state = i < currentIdx ? "done" : i === currentIdx ? "running" : "queued";
          const color = state === "done" ? "var(--pos)" : state === "running" ? "var(--accent)" : "var(--border-strong)";
          const bg = state === "done" ? "var(--pos-soft)" : state === "running" ? "var(--accent-soft)" : "var(--bg-sunk)";
          return (
            <div key={s.id} className="step-node" style={{
              padding: "6px 8px",
              background: bg,
              border: `1px solid ${state === "running" ? color : "var(--border)"}`,
              borderRadius: 3,
              position: "relative",
              minHeight: 58,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 2 }}>
                <span className="mono" style={{ fontSize: 9.5, color: "var(--text-mute)" }}>{s.id}</span>
                {state === "running" && <span className="bio-dot" style={{ width: 5, height: 5 }} />}
                {state === "done" && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--pos)" strokeWidth="3"><path d="M5 13l4 4L19 7"/></svg>}
              </div>
              <div style={{ fontSize: 11, fontWeight: 500, color: state === "queued" ? "var(--text-mute)" : "var(--text)" }}>{s.name}</div>
              {s.gate && <div className="mono" style={{ fontSize: 9, color: "var(--text-dim)", marginTop: 2 }}>{s.gate}</div>}
              {state === "running" && (
                <div style={{
                  position: "absolute", bottom: -1, left: -1, right: -1, height: 2,
                  background: "var(--accent)",
                  animation: "bio-pulse 1.4s infinite",
                }} />
              )}
            </div>
          );
        })}
      </div>

      {/* Mini metrics row */}
      <div style={{
        marginTop: 16, padding: 12, background: "var(--bg-sunk)",
        border: "1px solid var(--border)", borderRadius: 3,
        display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16,
      }}>
        <MiniStat label="Generated" value="80" sub="sequences" />
        <MiniStat label="Gate G1 pass" value="73" sub="91.3%" tone="pos" />
        <MiniStat label="Docking top%" value="16" sub="of 68 (G2)" tone="warn" />
        <MiniStat label="T2 후보" value="1" sub="cand03" tone="pos" />
        <MiniStat label="ETA" value="4.2m" sub="step05c → 06" />
      </div>
    </div>
  );
}

function MiniStat({ label, value, sub, tone }) {
  const color = tone === "pos" ? "var(--pos)" : tone === "warn" ? "var(--warn)" : "var(--text)";
  return (
    <div>
      <div className="bio-label">{label}</div>
      <div className="mono" style={{ fontSize: 18, fontWeight: 600, color, lineHeight: 1.1, marginTop: 2 }}>{value}</div>
      <div style={{ fontSize: 10.5, color: "var(--text-mute)" }} className="mono">{sub}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function AgentRail({ agents, log, tick }) {
  const scrollRef = useRefA(null);
  useEffectA(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [log.length]);

  const agentMap = Object.fromEntries(agents.map(a => [a.id, a]));
  // Find current active agent (last in log)
  const activeAgent = log.length ? log[log.length - 1].agent : null;

  return (
    <aside style={{
      gridColumn: 2, gridRow: "1 / span 2",
      background: "var(--bg-elev)",
      borderLeft: "1px solid var(--border)",
      display: "flex", flexDirection: "column", minHeight: 0,
    }}>
      <div className="bio-panel-hd" style={{ borderBottom: "1px solid var(--border)" }}>
        <span>5-Agent · iter02</span>
        <span className="bio-pill" style={{ padding: "1px 6px" }}>
          <span className="bio-dot" /> active
        </span>
      </div>

      {/* Agent grid */}
      <div style={{ padding: "10px 12px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, borderBottom: "1px solid var(--border)" }}>
        {agents.map(a => {
          const isActive = activeAgent === a.id;
          return (
            <div key={a.id} style={{
              padding: "5px 8px", borderRadius: 3,
              background: isActive ? `var(--${a.color}-soft, var(--accent-soft))` : "var(--bg-sunk)",
              border: `1px solid ${isActive ? `var(--${a.color}, var(--accent))` : "var(--border)"}`,
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <span style={{
                width: 6, height: 6, borderRadius: "50%",
                background: `var(--${a.color}, var(--accent))`,
                animation: isActive ? "bio-pulse 1.4s infinite" : "none",
              }} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 600, lineHeight: 1.1 }}>{a.name}</div>
                <div style={{ fontSize: 9.5, color: "var(--text-mute)", lineHeight: 1.2 }}>{a.role}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Log */}
      <div className="bio-scroll" ref={scrollRef} style={{
        flex: 1, overflow: "auto", padding: "8px 12px", minHeight: 0,
      }}>
        {log.map((entry, i) => {
          const a = agentMap[entry.agent];
          return (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "52px 60px 1fr",
              gap: 6, padding: "5px 0", borderBottom: "1px dashed var(--border)",
              fontSize: 11, lineHeight: 1.4,
            }}>
              <span className="mono" style={{ color: "var(--text-dim)", fontSize: 10 }}>{entry.t}</span>
              <span className="bio-pill" style={{
                padding: "0px 5px", fontSize: 9.5,
                background: `var(--${a.color}-soft, var(--accent-soft))`,
                color: `var(--${a.color}, var(--accent-text))`, border: 0,
                fontWeight: 600, justifyContent: "center",
              }}>{a.name.toUpperCase()}</span>
              <span style={{ color: "var(--text)", fontSize: 11 }}>{entry.text}</span>
            </div>
          );
        })}
      </div>

      <div style={{
        padding: "8px 12px", borderTop: "1px solid var(--border)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 10.5, color: "var(--text-mute)",
      }}>
        <span>flow: <span className="mono">sequential</span></span>
        <button className="bio-btn ghost" style={{ padding: "2px 6px", fontSize: 10 }}>view full log →</button>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function CandidatesTable({ candidates, selected, onSelect, silo }) {
  const [sortKey, setSortKey] = useStateA("margin");
  const [filterTier, setFilterTier] = useStateA("all");

  const filtered = candidates.filter(c =>
    filterTier === "all" || c.tier === filterTier
  );
  const sorted = [...filtered].sort((a, b) => {
    if (sortKey === "margin") return b.margin - a.margin;
    if (sortKey === "iptm") return b.iptm.SSTR2 - a.iptm.SSTR2;
    if (sortKey === "ddg") return a.ddg - b.ddg;
    return 0;
  });

  return (
    <div className="bio-panel" style={{ borderRadius: 0, border: 0, display: "flex", flexDirection: "column", minHeight: 0 }}>
      <div style={{ padding: "8px 16px", display: "flex", alignItems: "center", gap: 12, borderBottom: "1px solid var(--border)" }}>
        <div className="bio-label" style={{ fontSize: 11 }}>후보 · candidates ({sorted.length})</div>
        <span className="mono" style={{ fontSize: 10.5, color: "var(--text-mute)" }}>silo={silo} · iter02</span>
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", gap: 4 }}>
          {["all", "T2", "T1", "T0"].map(t => (
            <button key={t} onClick={() => setFilterTier(t)} className="bio-btn"
              style={{
                padding: "2px 8px", fontSize: 10.5,
                background: filterTier === t ? "var(--bg-sunk)" : "var(--bg-elev)",
                borderColor: filterTier === t ? "var(--text-mute)" : "var(--border)",
              }}>{t}</button>
          ))}
        </div>
        <select value={sortKey} onChange={e => setSortKey(e.target.value)} className="bio-input" style={{ fontSize: 10.5 }}>
          <option value="margin">sort: margin ↓</option>
          <option value="iptm">sort: iPTM(SSTR2) ↓</option>
          <option value="ddg">sort: ddG ↑</option>
        </select>
      </div>

      <div className="bio-scroll" style={{ overflow: "auto", flex: 1 }}>
        <table className="bio-table">
          <thead style={{ position: "sticky", top: 0, zIndex: 1 }}>
            <tr>
              <th style={{ width: 60 }}>ID</th>
              <th style={{ width: 200 }}>Sequence (vs WT)</th>
              <th style={{ width: 50 }}>Tier</th>
              <th style={{ width: 70 }}>margin</th>
              <th style={{ width: 60 }}>SSTR2</th>
              <th style={{ width: 70 }}>best</th>
              <th>iPTM × 5 SSTR</th>
              <th style={{ width: 70 }}>ddG</th>
              <th style={{ width: 100 }}>source</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(c => (
              <tr key={c.id} onClick={() => onSelect(c.id)}
                className={selected === c.id ? "selected" : ""}
                style={{ cursor: "pointer" }}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <span className="mono" style={{ fontWeight: 600, fontSize: 11.5 }}>{c.id}</span>
                    {c.recommended && <span className="bio-pill pos" style={{ padding: "0 4px", fontSize: 9 }}>★</span>}
                    {c.wildtype && <span className="bio-pill" style={{ padding: "0 4px", fontSize: 9 }}>WT</span>}
                  </div>
                </td>
                <td><Sequence seq={c.seq} /></td>
                <td><TierBadge tier={c.tier} /></td>
                <td>
                  <span className="mono" style={{
                    color: c.margin > 0 ? "var(--pos)" : c.margin > -0.05 ? "var(--warn)" : "var(--text-mute)",
                    fontWeight: 600,
                  }}>
                    {c.margin > 0 ? "+" : ""}{c.margin.toFixed(3)}
                  </span>
                </td>
                <td className="mono" style={{ fontWeight: c.best === "SSTR2" ? 700 : 400, color: c.best === "SSTR2" ? "var(--pos)" : "var(--text)" }}>
                  {c.iptm.SSTR2.toFixed(3)}
                </td>
                <td>
                  <span className="bio-pill" style={{ fontSize: 10, padding: "1px 5px",
                    background: c.best === "SSTR2" ? "var(--pos-soft)" : "var(--bg-sunk)",
                    color: c.best === "SSTR2" ? "var(--pos)" : "var(--text-mute)" }}>
                    {c.best}
                  </span>
                </td>
                <td>
                  <div style={{ display: "flex", gap: 2 }}>
                    {["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"].map(r => (
                      <div key={r} style={{
                        width: 18, height: 18, borderRadius: 2,
                        background: iptmColor(c.iptm[r]),
                        border: c.best === r ? "1px solid var(--text)" : "1px solid var(--border)",
                        fontSize: 8, fontFamily: "JetBrains Mono",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        color: c.iptm[r] > 0.93 ? "white" : "var(--text)",
                      }}
                        title={`${r} ${c.iptm[r].toFixed(3)}`}>
                        {c.iptm[r].toFixed(2).slice(2)}
                      </div>
                    ))}
                  </div>
                </td>
                <td className="mono" style={{ color: "var(--text-mute)" }}>{c.ddg.toFixed(1)}</td>
                <td className="mono" style={{ fontSize: 10.5, color: "var(--text-dim)" }}>{c.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function RightDetail({ candidate, gates, onHoverGate, hoverGate }) {
  return (
    <aside style={{
      borderLeft: "1px solid var(--border)", background: "var(--bg-elev)",
      display: "flex", flexDirection: "column", minHeight: 0,
      position: "relative",
    }}>
      <div className="bio-panel-hd">선택 후보 · {candidate?.id || "—"}</div>
      <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 10, overflow: "auto" }}>
        {candidate && (
          <>
            <div>
              <div className="bio-label" style={{ marginBottom: 4 }}>서열 (vs SST-14 WT)</div>
              <Sequence seq={candidate.seq} showRuler big />
              <div style={{ fontSize: 10.5, color: "var(--text-mute)", marginTop: 4, display: "flex", gap: 10, flexWrap: "wrap" }}>
                <span><span style={{ background: "var(--accent-soft)", color: "var(--accent-text)", padding: "0 3px", borderRadius: 2 }}>변이</span></span>
                <span><span style={{ color: "var(--warn)", fontWeight: 700 }}>C</span> 이황화</span>
                <span><span style={{ background: "var(--violet-soft)", color: "var(--violet)", padding: "0 3px", borderRadius: 2 }}>FWKT</span> pharmacophore</span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <KV k="margin" v={`${candidate.margin > 0 ? "+" : ""}${candidate.margin.toFixed(3)}`} tone={candidate.margin > 0 ? "pos" : "mute"} />
              <KV k="tier" v={<TierBadge tier={candidate.tier} />} />
              <KV k="best receptor" v={<span className="mono">{candidate.best}</span>} />
              <KV k="ddG" v={`${candidate.ddg.toFixed(2)} kcal`} />
            </div>

            <div>
              <div className="bio-label" style={{ marginBottom: 4 }}>iPTM × SSTR1–5</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 3 }}>
                {["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"].map(r => (
                  <div key={r} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 9.5, color: "var(--text-mute)", marginBottom: 2 }}>{r}</div>
                    <HeatmapCell value={candidate.iptm[r]} isBest={candidate.best === r} isTarget={r === "SSTR2"} />
                  </div>
                ))}
              </div>
            </div>

            {candidate.notes && (
              <div style={{
                padding: "8px 10px", borderRadius: 3,
                background: candidate.recommended ? "var(--pos-soft)" : "var(--bg-sunk)",
                border: `1px solid ${candidate.recommended ? "var(--pos)" : "var(--border)"}`,
                fontSize: 11, lineHeight: 1.45,
              }}>
                {candidate.recommended && <strong style={{ color: "var(--pos)" }}>★ RECOMMENDED · </strong>}
                {candidate.notes}
              </div>
            )}

            <div>
              <div className="bio-label" style={{ marginBottom: 4 }}>Gate trail (hover for detail)</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {gates.slice(0, 7).map(g => (
                  <GateChip key={g.id} gate={g} onHover={onHoverGate} />
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {hoverGate && (
        <div style={{
          position: "absolute", left: 12, bottom: 12, right: 12, zIndex: 50,
          background: "var(--text)", color: "var(--bg-elev)",
          padding: "10px 12px", borderRadius: 4, fontSize: 11,
          boxShadow: "0 8px 24px rgba(0,0,0,0.18)",
          lineHeight: 1.5,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <strong>{hoverGate.id} · {hoverGate.name}</strong>
            <span className="mono" style={{ opacity: 0.7 }}>step {hoverGate.step}</span>
          </div>
          <div className="mono" style={{ fontSize: 10.5, opacity: 0.85 }}>임계값 · {hoverGate.threshold}</div>
          <div style={{ marginTop: 6, display: "flex", gap: 6, alignItems: "center" }}>
            <div style={{ flex: 1, height: 5, background: "rgba(255,255,255,0.15)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{
                width: `${(hoverGate.pass / (hoverGate.pass + hoverGate.fail)) * 100}%`,
                height: "100%", background: "var(--pos)",
              }} />
            </div>
            <span className="mono">{hoverGate.pass}<span style={{ opacity: 0.5 }}>/{hoverGate.pass + hoverGate.fail}</span></span>
          </div>
          <div style={{ fontSize: 10, opacity: 0.65, marginTop: 4 }}>
            fail 사유: {hoverGate.id === "G1" ? "disulfide SG-SG > 3 Å (7건)" :
              hoverGate.id === "G2" ? "Boltz iPTM < top 20% (52건)" :
              hoverGate.id === "G3b" ? "T0–T1 margin · pan-receptor binding (7건)" :
              "see step audit log"}
          </div>
        </div>
      )}
    </aside>
  );
}

function KV({ k, v, tone }) {
  const color = tone === "pos" ? "var(--pos)" : tone === "mute" ? "var(--text-mute)" : "var(--text)";
  return (
    <div style={{ padding: "6px 8px", border: "1px solid var(--border)", borderRadius: 3, background: "var(--bg-sunk)" }}>
      <div className="bio-label" style={{ fontSize: 9.5 }}>{k}</div>
      <div className="mono" style={{ color, fontWeight: 600, fontSize: 13, marginTop: 1 }}>{v}</div>
    </div>
  );
}

window.VariantA = VariantA;
