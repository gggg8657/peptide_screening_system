/* global React, PROJECT_DATA */
const { useState: useStateB, useEffect: useEffectB, useRef: useRefB, useMemo: useMemoB } = React;

function VariantB() {
  const data = PROJECT_DATA;
  const rootRef = useRefB(null);
  const [selectedCell, setSelectedCell] = useStateB({ cand: "cand03", receptor: "SSTR2" });
  const [drawerOpen, setDrawerOpen] = useStateB(true);
  const [tierFilter, setTierFilter] = useStateB(new Set(["T0", "T1", "T2"]));
  const [showWT, setShowWT] = useStateB(true);

  const filtered = data.candidates.filter(c => tierFilter.has(c.tier) && (showWT || !c.wildtype));
  const sortedByMargin = [...filtered].sort((a, b) => b.margin - a.margin);

  const selCand = data.candidates.find(c => c.id === selectedCell.cand);
  const selValue = selCand?.iptm[selectedCell.receptor];

  function toggleTier(t) {
    setTierFilter(prev => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t); else next.add(t);
      return next;
    });
  }

  return (
    <div ref={rootRef} data-theme="light" style={{
      width: "100%", height: "100%", display: "flex", flexDirection: "column",
      background: "var(--bg)", color: "var(--text)",
      fontFamily: "Inter, sans-serif", fontSize: 13,
    }}>
      {/* HEADER */}
      <header style={{
        display: "flex", alignItems: "center", gap: 16,
        padding: "8px 16px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-elev)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 22, height: 22, borderRadius: 3,
            background: "var(--text)", color: "var(--bg-elev)",
            display: "grid", placeItems: "center", fontFamily: "JetBrains Mono", fontWeight: 700, fontSize: 11,
          }}>P*</div>
          <div style={{ fontWeight: 600 }}>Selectivity Explorer</div>
          <span style={{ color: "var(--text-dim)" }}>·</span>
          <span style={{ color: "var(--text-mute)" }}>step05c Boltz-2 + AF MSA</span>
        </div>
        <nav style={{ display: "flex", gap: 2, marginLeft: 16 }}>
          {["Run", "Candidates", "Selectivity", "Agents", "Settings"].map((n, i) => (
            <button key={n} className={`bio-btn ghost`} style={{
              padding: "4px 10px",
              borderBottom: i === 2 ? "2px solid var(--accent)" : "2px solid transparent",
              borderRadius: 0, color: i === 2 ? "var(--text)" : "var(--text-mute)",
              fontWeight: i === 2 ? 600 : 400,
            }}>{n}</button>
          ))}
        </nav>
        <div style={{ flex: 1 }} />
        <span className="bio-pill mono" style={{ fontSize: 10 }}>
          50 pairs · 10 cand × 5 SSTR
        </span>
        <ThemeToggle scope={rootRef} />
      </header>

      {/* CONTROL BAR */}
      <div style={{
        padding: "8px 16px", display: "flex", alignItems: "center", gap: 14,
        borderBottom: "1px solid var(--border)", background: "var(--bg-elev)",
        flexWrap: "wrap",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span className="bio-label">Target</span>
          <div style={{ display: "flex", gap: 0, border: "1px solid var(--border-strong)", borderRadius: 3, overflow: "hidden" }}>
            {data.receptors.map(r => (
              <button key={r} className="bio-btn" style={{
                padding: "2px 10px", fontSize: 11, fontFamily: "JetBrains Mono",
                background: r === "SSTR2" ? "var(--accent)" : "var(--bg-elev)",
                color: r === "SSTR2" ? "white" : "var(--text-mute)",
                border: 0, borderRadius: 0,
              }}>{r}</button>
            ))}
          </div>
        </div>

        <div style={{ width: 1, height: 22, background: "var(--border)" }} />

        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span className="bio-label">Tier</span>
          {["T2", "T1", "T0"].map(t => (
            <label key={t} style={{
              display: "flex", alignItems: "center", gap: 4,
              padding: "2px 7px", borderRadius: 3,
              background: tierFilter.has(t) ? `var(--${t === "T2" ? "pos" : t === "T1" ? "warn" : "neg"}-soft)` : "var(--bg-sunk)",
              border: `1px solid ${tierFilter.has(t) ? "transparent" : "var(--border)"}`,
              fontSize: 11, cursor: "pointer",
            }}>
              <input type="checkbox" checked={tierFilter.has(t)} onChange={() => toggleTier(t)}
                style={{ accentColor: t === "T2" ? "var(--pos)" : t === "T1" ? "var(--warn)" : "var(--neg)", margin: 0 }} />
              <span style={{ color: t === "T2" ? "var(--pos)" : t === "T1" ? "var(--warn)" : "var(--neg)", fontWeight: 600 }}>{t}</span>
            </label>
          ))}
        </div>

        <div style={{ width: 1, height: 22, background: "var(--border)" }} />

        <label style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}>
          <input type="checkbox" checked={showWT} onChange={e => setShowWT(e.target.checked)} style={{ accentColor: "var(--accent)" }} />
          <span>show wildtype</span>
        </label>

        <div style={{ flex: 1 }} />

        <span className="mono" style={{ fontSize: 10.5, color: "var(--text-mute)" }}>
          source: <span style={{ color: "var(--text)" }}>boltz_summary.json</span> ·
          <span style={{ marginLeft: 4 }}>2026-05-11</span>
        </span>
        <button className="bio-btn">⇣ CSV</button>
      </div>

      {/* MAIN — heatmap + side */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: drawerOpen ? "minmax(0, 1fr) 380px" : "1fr", minHeight: 0 }}>
        <main style={{ padding: "16px 20px", overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Notice */}
          <div style={{
            padding: "10px 14px", borderRadius: 4,
            background: "var(--accent-soft)", border: "1px solid var(--accent)",
            display: "flex", alignItems: "center", gap: 12,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-text)" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg>
            <div style={{ flex: 1, fontSize: 11.5, lineHeight: 1.4 }}>
              <strong>iPTM ≠ Ki:</strong> iPTM은 구조 geometry 신뢰도. SST-14 × SSTR1–5 실측 Ki 순위 일치 0/5 (Spearman ρ ≈ −0.3).
              본 매트릭스는 <em>geometry 기반 1차 필터</em>; 정량 selectivity는 FEP / MM-GBSA / radioligand Ki assay 필수.
            </div>
            <button className="bio-btn ghost" style={{ fontSize: 10 }}>see audit →</button>
          </div>

          {/* Heatmap */}
          <div className="bio-panel">
            <div className="bio-panel-hd">
              <span>iPTM Matrix · 10 후보 × 5 SSTR</span>
              <span className="mono" style={{ fontSize: 10 }}>cell = SSTR best margin · ✦ = on-target hit</span>
            </div>
            <div style={{ padding: "16px 20px 12px" }}>
              <HeatmapBig
                candidates={sortedByMargin}
                receptors={data.receptors}
                selectedCell={selectedCell}
                onSelect={(cand, receptor) => { setSelectedCell({ cand, receptor }); setDrawerOpen(true); }}
              />
            </div>

            {/* Legend */}
            <div style={{
              padding: "10px 20px", borderTop: "1px solid var(--border)",
              display: "flex", alignItems: "center", gap: 16,
              fontSize: 10.5, color: "var(--text-mute)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span>iPTM</span>
                <div style={{ display: "flex" }}>
                  {[0.78, 0.85, 0.90, 0.93, 0.96, 0.98].map(v => (
                    <div key={v} style={{
                      width: 22, height: 14, background: iptmColor(v),
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 8.5, fontFamily: "JetBrains Mono",
                      color: v > 0.93 ? "white" : "var(--text)",
                    }}>{v.toFixed(2).slice(1)}</div>
                  ))}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 12, height: 12, border: "1.5px solid var(--text)", display: "inline-block", borderRadius: 2 }} />
                <span>best receptor</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 12, height: 12, outline: "1.5px dashed var(--accent)", outlineOffset: -2, display: "inline-block", borderRadius: 2 }} />
                <span>target SSTR2</span>
              </div>
              <div style={{ flex: 1 }} />
              <span className="mono">tier = SSTR2 − max(off) iPTM margin</span>
            </div>
          </div>

          {/* Margin distribution + gate funnel */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Margin distribution</span><span className="mono" style={{ fontSize: 10 }}>margin = iPTM(SSTR2) − max(off)</span></div>
              <MarginPlot candidates={data.candidates} selected={selectedCell.cand} onSelect={(id) => setSelectedCell({ cand: id, receptor: "SSTR2" })} />
            </div>
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Gate funnel · iter02</span><span className="mono" style={{ fontSize: 10 }}>80 → 1</span></div>
              <GateFunnel gates={data.gates} />
            </div>
          </div>
        </main>

        {drawerOpen && (
          <SelectivityDrawer
            candidate={selCand}
            receptor={selectedCell.receptor}
            value={selValue}
            onClose={() => setDrawerOpen(false)}
          />
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function HeatmapBig({ candidates, receptors, selectedCell, onSelect }) {
  // Layout: row per candidate, columns: ID, seq, then 5 cells, then margin/tier
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "70px 250px repeat(5, 1fr) 80px 50px",
        gap: 6, paddingBottom: 6, borderBottom: "1px solid var(--border)",
      }}>
        <div className="bio-label">cand</div>
        <div className="bio-label">sequence</div>
        {receptors.map(r => (
          <div key={r} className="bio-label" style={{ textAlign: "center", color: r === "SSTR2" ? "var(--accent)" : "var(--text-dim)", fontWeight: r === "SSTR2" ? 700 : 500 }}>
            {r}{r === "SSTR2" && " ★"}
          </div>
        ))}
        <div className="bio-label" style={{ textAlign: "right" }}>margin</div>
        <div className="bio-label" style={{ textAlign: "center" }}>tier</div>
      </div>

      {/* Rows */}
      {candidates.map(c => (
        <div key={c.id} style={{
          display: "grid",
          gridTemplateColumns: "70px 250px repeat(5, 1fr) 80px 50px",
          gap: 6, padding: "6px 0", borderBottom: "1px solid var(--border)",
          alignItems: "center",
        }}>
          <div className="mono" style={{ fontSize: 11.5, fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>
            {c.id}{c.recommended && <span style={{ color: "var(--pos)" }}>★</span>}
            {c.wildtype && <span className="bio-pill" style={{ padding: "0 3px", fontSize: 8.5 }}>WT</span>}
          </div>
          <Sequence seq={c.seq} />
          {receptors.map(r => {
            const isSelected = selectedCell.cand === c.id && selectedCell.receptor === r;
            return (
              <div key={r}>
                <HeatmapCell
                  value={c.iptm[r]}
                  isBest={c.best === r}
                  isTarget={r === "SSTR2"}
                  selected={isSelected}
                  onClick={() => onSelect(c.id, r)}
                />
              </div>
            );
          })}
          <div className="mono" style={{
            textAlign: "right",
            color: c.margin > 0 ? "var(--pos)" : c.margin > -0.05 ? "var(--warn)" : "var(--text-mute)",
            fontWeight: 600,
          }}>
            {c.margin > 0 ? "+" : ""}{c.margin.toFixed(3)}
          </div>
          <div style={{ textAlign: "center" }}><TierBadge tier={c.tier} /></div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function MarginPlot({ candidates, selected, onSelect }) {
  // Horizontal axis: margin -0.2 → +0.05
  const min = -0.2, max = 0.05;
  return (
    <div style={{ padding: "14px 20px", position: "relative", height: 240 }}>
      {/* Zero line */}
      <div style={{
        position: "absolute", left: `${((0 - min) / (max - min)) * 100}%`,
        top: 0, bottom: 30, width: 1, background: "var(--text)", opacity: 0.4,
      }}>
        <span style={{ position: "absolute", top: -2, left: 4, fontSize: 9, color: "var(--text-mute)" }} className="mono">selective →</span>
      </div>
      {/* Tier zones */}
      <div style={{
        position: "absolute", inset: "0 0 30px 0",
        background: `linear-gradient(90deg,
          var(--neg-soft) 0%, var(--neg-soft) ${((-0.05 - min) / (max - min)) * 100}%,
          var(--warn-soft) ${((-0.05 - min) / (max - min)) * 100}%, var(--warn-soft) ${((0 - min) / (max - min)) * 100}%,
          var(--pos-soft) ${((0 - min) / (max - min)) * 100}%, var(--pos-soft) 100%)`,
        opacity: 0.4, borderRadius: 3,
      }} />

      {/* Candidate dots */}
      {candidates.map((c, i) => {
        const x = ((c.margin - min) / (max - min)) * 100;
        const y = 10 + i * 18;
        const isSel = selected === c.id;
        return (
          <div key={c.id}
            onClick={() => onSelect(c.id)}
            style={{
              position: "absolute",
              left: `calc(${x}% - 4px)`, top: y,
              width: 8, height: 8, borderRadius: "50%",
              background: c.tier === "T2" ? "var(--pos)" : c.tier === "T1" ? "var(--warn)" : "var(--neg)",
              cursor: "pointer",
              border: isSel ? "2px solid var(--text)" : "1px solid var(--bg-elev)",
              transform: isSel ? "scale(1.5)" : "none",
              zIndex: isSel ? 5 : 1,
            }} title={`${c.id} · ${c.margin.toFixed(3)}`}>
            {isSel && <span style={{
              position: "absolute", left: 12, top: -2,
              fontSize: 10, whiteSpace: "nowrap", color: "var(--text)",
              fontFamily: "JetBrains Mono",
            }}>{c.id} {c.margin > 0 ? "+" : ""}{c.margin.toFixed(3)}</span>}
          </div>
        );
      })}

      {/* X-axis */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, paddingTop: 6, borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9.5, color: "var(--text-dim)" }} className="mono">
          {[-0.2, -0.15, -0.10, -0.05, 0.0, 0.05].map(v => (
            <span key={v}>{v > 0 ? "+" : ""}{v.toFixed(2)}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function GateFunnel({ gates }) {
  // Approximate funnel: 80 → 73 → 16 → 8 → 1 → 1 → 1
  const stages = [
    { id: "Generated", count: 80, color: "var(--text-mute)" },
    { id: "G1 pLDDT", count: 73, color: "var(--accent)" },
    { id: "G2 Docking", count: 16, color: "var(--accent)" },
    { id: "G3 Selectivity", count: 8, color: "var(--warn)" },
    { id: "G3b Boltz-cross", count: 1, color: "var(--pos)" },
    { id: "G4 Rosetta", count: 1, color: "var(--pos)" },
    { id: "G5 Stability", count: 1, color: "var(--pos)" },
  ];
  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 6 }}>
      {stages.map((s, i) => {
        const w = (s.count / 80) * 100;
        const dropped = i > 0 ? stages[i-1].count - s.count : 0;
        return (
          <div key={s.id} style={{ display: "grid", gridTemplateColumns: "100px 1fr 50px 50px", gap: 8, alignItems: "center", fontSize: 11 }}>
            <span style={{ color: "var(--text-mute)" }}>{s.id}</span>
            <div style={{ height: 14, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ width: `${w}%`, height: "100%", background: s.color, transition: "width 0.4s" }} />
            </div>
            <span className="mono" style={{ fontWeight: 600 }}>{s.count}</span>
            {dropped > 0 ? (
              <span className="mono" style={{ color: "var(--neg)", fontSize: 10 }}>−{dropped}</span>
            ) : <span />}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function SelectivityDrawer({ candidate, receptor, value, onClose }) {
  if (!candidate) return null;
  const data = PROJECT_DATA;
  // Compute margin against other receptors for this candidate
  const isTarget = receptor === "SSTR2";
  const offMax = Math.max(...data.receptors.filter(r => r !== receptor).map(r => candidate.iptm[r]));
  const cellMargin = value - offMax;

  return (
    <aside style={{
      borderLeft: "1px solid var(--border)", background: "var(--bg-elev)",
      display: "flex", flexDirection: "column", overflow: "auto", minHeight: 0,
    }}>
      <div className="bio-panel-hd" style={{ position: "sticky", top: 0, background: "var(--bg-elev)", zIndex: 2 }}>
        <span>{candidate.id} × {receptor}</span>
        <div style={{ display: "flex", gap: 4 }}>
          <button className="bio-btn ghost" style={{ padding: "2px 6px", fontSize: 10 }}>full report ↗</button>
          <button className="bio-btn ghost" onClick={onClose} style={{ padding: "2px 6px" }}>✕</button>
        </div>
      </div>

      <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Cell value */}
        <div style={{
          padding: "10px 12px", borderRadius: 4,
          background: isTarget ? "var(--accent-soft)" : "var(--bg-sunk)",
          border: `1px solid ${isTarget ? "var(--accent)" : "var(--border)"}`,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span className="bio-label">iPTM</span>
            <span className="mono" style={{ fontSize: 22, fontWeight: 600 }}>{value.toFixed(3)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 11, color: "var(--text-mute)" }}>
            <span>vs max off-target</span>
            <span className="mono" style={{
              color: cellMargin > 0 ? "var(--pos)" : "var(--neg)", fontWeight: 600,
            }}>{cellMargin > 0 ? "+" : ""}{cellMargin.toFixed(3)}</span>
          </div>
        </div>

        {/* 3D viewer */}
        <div>
          <div className="bio-label" style={{ marginBottom: 4 }}>Docked pose · Boltz-2</div>
          <MolViewer candidate={candidate} height={200} />
          <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
            <button className="bio-btn" style={{ flex: 1, fontSize: 10.5 }}>ribbon</button>
            <button className="bio-btn" style={{ flex: 1, fontSize: 10.5, background: "var(--bg-sunk)" }}>surface</button>
            <button className="bio-btn" style={{ flex: 1, fontSize: 10.5 }}>contacts</button>
          </div>
        </div>

        {/* Sequence breakdown */}
        <div>
          <div className="bio-label" style={{ marginBottom: 4 }}>서열 · 변이 위치</div>
          <Sequence seq={candidate.seq} showRuler big />
          {candidate.mut.length > 0 && (
            <div style={{ marginTop: 6, fontSize: 11, color: "var(--text-mute)" }}>
              <span className="bio-label" style={{ marginRight: 6 }}>변이</span>
              {candidate.mut.map((m, i) => (
                <span key={i} className="bio-pill accent" style={{ marginRight: 4, padding: "1px 5px" }}>{m}</span>
              ))}
            </div>
          )}
        </div>

        {/* Scores */}
        <div>
          <div className="bio-label" style={{ marginBottom: 6 }}>Score breakdown</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            <ScoreRow label="iPTM" value={value} max={1} color="var(--accent)" />
            <ScoreRow label="pTM" value={0.869} max={1} color="var(--teal)" />
            <ScoreRow label="confidence" value={0.859} max={1} color="var(--violet)" />
            <ScoreRow label="QED" value={0.74} max={1} color="var(--warn)" />
          </div>
        </div>

        {/* Cross-receptor */}
        <div>
          <div className="bio-label" style={{ marginBottom: 6 }}>vs other SSTR</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {data.receptors.map(r => (
              <div key={r} style={{ display: "grid", gridTemplateColumns: "60px 1fr 50px", alignItems: "center", gap: 8, fontSize: 11 }}>
                <span className="mono" style={{ fontWeight: r === receptor ? 700 : 400 }}>{r}</span>
                <div style={{ height: 10, background: "var(--bg-sunk)", borderRadius: 2, position: "relative", overflow: "hidden" }}>
                  <div style={{
                    width: `${((candidate.iptm[r] - 0.75) / 0.25) * 100}%`,
                    height: "100%", background: iptmColor(candidate.iptm[r]),
                    border: r === candidate.best ? "1px solid var(--text)" : "none",
                  }} />
                </div>
                <span className="mono" style={{ textAlign: "right", fontWeight: r === receptor ? 700 : 400 }}>{candidate.iptm[r].toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>

        {candidate.notes && (
          <div style={{
            padding: "10px 12px", borderRadius: 3,
            background: candidate.recommended ? "var(--pos-soft)" : "var(--bg-sunk)",
            border: `1px solid ${candidate.recommended ? "var(--pos)" : "var(--border)"}`,
            fontSize: 11, lineHeight: 1.5,
          }}>
            {candidate.recommended && <strong style={{ color: "var(--pos)" }}>★ RECOMMENDED · </strong>}
            {candidate.notes}
          </div>
        )}

        <div style={{ display: "flex", gap: 6 }}>
          <button className="bio-btn primary" style={{ flex: 1 }}>Wetlab Ki 발주 →</button>
          <button className="bio-btn">Variants</button>
        </div>
      </div>
    </aside>
  );
}

function ScoreRow({ label, value, max, color }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "70px 1fr 50px", alignItems: "center", gap: 8, fontSize: 11 }}>
      <span style={{ color: "var(--text-mute)" }}>{label}</span>
      <ScoreBar value={value} max={max} color={color} />
      <span className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{value.toFixed(3)}</span>
    </div>
  );
}

window.VariantB = VariantB;
