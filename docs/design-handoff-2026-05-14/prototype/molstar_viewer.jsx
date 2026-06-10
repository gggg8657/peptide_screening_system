/* global React */
// Real Mol* viewer — loads SSTR2 (7XNA) from RCSB.
// Falls back to the stripe placeholder if molstar lib isn't loaded.

function MolstarViewer({ pdbId = "7XNA", height = 320, caption, fallbackCandidate, viewMode = "ribbon" }) {
  const ref = React.useRef(null);
  const viewerRef = React.useRef(null);
  const [status, setStatus] = React.useState("init"); // init | loading | ready | error

  React.useEffect(() => {
    let cancelled = false;
    if (!ref.current) return;
    if (typeof window.molstar === "undefined") {
      // library hasn't loaded yet — retry in a bit
      const handle = setTimeout(() => setStatus(s => s === "init" ? "no-lib" : s), 2000);
      return () => clearTimeout(handle);
    }
    setStatus("loading");
    (async () => {
      try {
        // Create viewer
        const viewer = await window.molstar.Viewer.create(ref.current, {
          layoutIsExpanded: false,
          layoutShowControls: false,
          layoutShowRemoteState: false,
          layoutShowSequence: false,
          layoutShowLog: false,
          layoutShowLeftPanel: false,
          viewportShowExpand: false,
          viewportShowAnimation: false,
          viewportShowSettings: false,
          viewportShowSelectionMode: false,
          viewportShowTrajectoryControls: false,
          pdbProvider: "rcsb",
          emdbProvider: "rcsb",
        });
        if (cancelled) return;
        viewerRef.current = viewer;
        await viewer.loadPdb(pdbId);
        if (!cancelled) setStatus("ready");
      } catch (e) {
        console.warn("molstar load failed", e);
        if (!cancelled) setStatus("error");
      }
    })();
    return () => { cancelled = true; };
  }, [pdbId]);

  // If no library, show placeholder
  if (status === "no-lib" || status === "error") {
    return (
      <div className="bio-placeholder" style={{ height, width: "100%", borderRadius: 3, position: "relative" }}>
        <div style={{
          position: "absolute", inset: 0,
          background: `radial-gradient(circle at 35% 45%, oklch(0.7 0.13 195 / 0.25) 0%, transparent 35%),
                       radial-gradient(circle at 60% 55%, oklch(0.65 0.12 290 / 0.18) 0%, transparent 30%)`,
          pointerEvents: "none",
        }} />
        <div style={{ textAlign: "center", lineHeight: 1.6 }}>
          <div style={{ fontWeight: 600, color: "var(--text-mute)" }}>
            {caption || `MOLSTAR · ${pdbId}`}
          </div>
          <div style={{ fontSize: 10, marginTop: 4 }}>
            {fallbackCandidate ? `${fallbackCandidate.id} · ${fallbackCandidate.seq}` : `${pdbId} holo`}<br/>
            SSTR2 · ribbon + peptide ligand
          </div>
          <div style={{ fontSize: 9, color: "var(--text-dim)", marginTop: 8, fontFamily: "JetBrains Mono, monospace" }}>
            [ placeholder — Mol* lib not loaded ]
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: "relative", height, width: "100%", background: "var(--bg-sunk)", borderRadius: 3, overflow: "hidden", border: "1px solid var(--border)" }}>
      <div ref={ref} style={{ position: "absolute", inset: 0 }} />
      {status === "loading" && (
        <div style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center",
          background: "var(--bg-sunk)", color: "var(--text-mute)", fontSize: 11,
        }}>
          <div style={{ textAlign: "center", lineHeight: 1.5 }}>
            <div className="bio-dot" style={{ display: "inline-block" }} />
            <div className="mono" style={{ marginTop: 6 }}>loading {pdbId}…</div>
            <div style={{ fontSize: 10, color: "var(--text-dim)" }}>RCSB · {pdbId} holo (SSTR2 + ligand)</div>
          </div>
        </div>
      )}
      <div style={{
        position: "absolute", top: 6, left: 8, fontSize: 9,
        fontFamily: "JetBrains Mono, monospace", color: "var(--text-dim)",
        pointerEvents: "none", zIndex: 1,
      }}>
        molstar 4.7 · {pdbId}
      </div>
    </div>
  );
}

window.MolstarViewer = MolstarViewer;
