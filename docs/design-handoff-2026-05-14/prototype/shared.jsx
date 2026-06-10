/* global React */
const { useState, useEffect, useRef, useMemo, Fragment, useCallback } = React;

// ─────────────────────────────────────────────────────────────────────────────
// Tier badge
function TierBadge({ tier }) {
  return <span className={`bio-pill tier-${tier}`} style={{ fontWeight: 600 }}>{tier}</span>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Sequence — mark mutations relative to wildtype, highlight cys + pharmacophore
function Sequence({ seq, wildtype = "AGCKNFFWKTFTSC", showRuler = false, big = false }) {
  const aa = seq.split("");
  const wt = wildtype.split("");
  return (
    <div style={{ display: "inline-flex", flexDirection: "column" }}>
      {showRuler && (
        <div style={{ display: "flex", marginBottom: 2 }}>
          {aa.map((_, i) => (
            <div key={i} style={{
              width: big ? 26 : 18, textAlign: "center",
              fontSize: 9, color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace"
            }}>{i + 1}</div>
          ))}
        </div>
      )}
      <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 3, overflow: "hidden" }}>
        {aa.map((c, i) => {
          const isMut = wt[i] && wt[i] !== c;
          const isCys = c === "C";
          const isPharm = i >= 5 && i <= 8; // FWKT positions 6-9 (0-indexed 5-8)
          let cls = "aa";
          if (isMut) cls += " mut";
          else if (isCys) cls += " cys";
          else if (isPharm) cls += " pharm";
          return (
            <div key={i} className={cls} style={big ? { width: 26, height: 30, lineHeight: "30px", fontSize: 14 } : null}>
              {c}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Score bar — horizontal bar w/ value
function ScoreBar({ value, max = 1, min = 0, color = "var(--accent)", label }) {
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, width: "100%" }}>
      <div style={{
        flex: 1, height: 4, background: "var(--bg-sunk)",
        borderRadius: 2, overflow: "hidden", minWidth: 40
      }}>
        <div style={{ width: `${pct * 100}%`, height: "100%", background: color }} />
      </div>
      {label && <span className="mono" style={{ fontSize: 11, color: "var(--text-mute)", minWidth: 36, textAlign: "right" }}>{label}</span>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// iPTM heatmap cell (0.75 - 1.0 typical range)
function iptmColor(v) {
  // Map 0.75 → cool stone, 0.85 → mid, 0.98 → hot accent
  const t = Math.max(0, Math.min(1, (v - 0.75) / 0.25));
  // interpolate between low (cool) and high (warm accent)
  // Use oklch-like steps via mixing soft + strong
  if (t < 0.33) return `oklch(0.92 0.04 220 / ${0.4 + t})`;
  if (t < 0.66) return `oklch(0.82 0.10 200 / ${0.5 + t * 0.4})`;
  return `oklch(0.7 0.14 195 / ${0.65 + t * 0.35})`;
}

function HeatmapCell({ value, isBest, isTarget, onClick, selected }) {
  return (
    <div
      onClick={onClick}
      style={{
        width: "100%", aspectRatio: 1, position: "relative",
        background: iptmColor(value),
        border: selected ? "2px solid var(--accent)" : isBest ? "1.5px solid var(--text)" : "1px solid var(--border)",
        borderRadius: 2,
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: "pointer", fontSize: 11, fontFamily: "JetBrains Mono, monospace",
        color: value > 0.92 ? "white" : "var(--text)",
        fontWeight: isBest ? 700 : 500,
        outline: isTarget ? "1.5px dashed var(--accent)" : "none",
        outlineOffset: -3,
      }}
      title={`iPTM ${value.toFixed(3)}`}
    >
      {value.toFixed(2).slice(1)}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Theme toggle (per-artboard, persists on document via data-theme)
function ThemeToggle({ scope, defaultTheme = "light" }) {
  const [theme, setTheme] = useState(defaultTheme);
  useEffect(() => {
    if (scope.current) scope.current.setAttribute("data-theme", theme);
  }, [theme, scope]);
  return (
    <button className="bio-btn ghost" onClick={() => setTheme(t => t === "light" ? "dark" : "light")}
      title="Toggle theme">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        {theme === "light"
          ? <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          : <g><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></g>
        }
      </svg>
      <span style={{ fontSize: 11 }}>{theme === "light" ? "Dark" : "Light"}</span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Gate chip with hover tooltip
function GateChip({ gate, onHover }) {
  const total = gate.pass + gate.fail;
  const passRate = total ? gate.pass / total : 0;
  const tone = passRate > 0.8 ? "pos" : passRate > 0.4 ? "warn" : "neg";
  return (
    <div
      className="bio-pill"
      onMouseEnter={(e) => onHover && onHover(gate, e)}
      onMouseLeave={() => onHover && onHover(null)}
      style={{ cursor: "help", padding: "3px 7px", gap: 6, fontSize: 11 }}
    >
      <span style={{ color: "var(--text-mute)", fontWeight: 500 }}>{gate.id}</span>
      <span style={{ color: "var(--text)" }}>{gate.name}</span>
      <span className={`bio-pill ${tone}`} style={{ padding: "0 5px", fontSize: 10, border: 0 }}>
        {gate.pass}/{total}
      </span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Molecular viewer — uses real Mol* if loaded, else stripe placeholder
function MolViewer({ candidate, height = 320, caption = "MOLSTAR · 3D POSE" }) {
  if (window.MolstarViewer) {
    return <window.MolstarViewer pdbId="7XNA" height={height} caption={caption} fallbackCandidate={candidate} />;
  }
  return (
    <div style={{ position: "relative", height, width: "100%" }}>
      <div className="bio-placeholder" style={{ height: "100%", width: "100%", borderRadius: 3, position: "relative" }}>
        {/* Drop a faux helix structure using radial gradient */}
        <div style={{
          position: "absolute", inset: 0,
          background: `radial-gradient(circle at 35% 45%, oklch(0.7 0.13 195 / 0.25) 0%, transparent 35%),
                       radial-gradient(circle at 60% 55%, oklch(0.65 0.12 290 / 0.18) 0%, transparent 30%)`,
          pointerEvents: "none",
        }} />
        <div style={{ textAlign: "center", lineHeight: 1.6 }}>
          <div style={{ fontWeight: 600, color: "var(--text-mute)" }}>{caption}</div>
          <div style={{ fontSize: 10, marginTop: 4 }}>
            {candidate ? `${candidate.id} · ${candidate.seq}` : "wildtype peptide"}<br/>
            SSTR2 (7XNA holo) · ribbon + ligand
          </div>
        </div>
        <div style={{
          position: "absolute", top: 8, left: 8, fontSize: 9,
          fontFamily: "JetBrains Mono, monospace", color: "var(--text-dim)"
        }}>
          chain A · receptor
        </div>
        <div style={{
          position: "absolute", bottom: 8, right: 8, fontSize: 9,
          fontFamily: "JetBrains Mono, monospace", color: "var(--text-dim)"
        }}>
          chain P · peptide
        </div>
      </div>
    </div>
  );
}

// Inline-ish helix svg for fun
function HelixIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 4c6 0 10 4 10 8s4 8 6 8" />
      <path d="M4 12c6 0 10-4 10-8" opacity="0.5" />
      <path d="M14 20c-2 0-4-2-4-4" opacity="0.7" />
    </svg>
  );
}

Object.assign(window, {
  TierBadge, Sequence, ScoreBar, HeatmapCell, ThemeToggle,
  GateChip, MolViewer, HelixIcon, iptmColor
});
