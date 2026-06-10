/* global React, PROJECT_DATA */
// PipelineFlow — Visualizes a list of stages as a horizontal flow with
// in/out counts, progress bars, gate labels, status pills.
// Three modes: silo="A" | "B" | "Combined"

const { useState: usePF, useEffect: useEffectPF, useRef: useRefPF } = React;

// Color by stage group
const PF_GROUP = {
  input:   { bg: "var(--bg-sunk)",       fg: "var(--text-mute)", accent: "var(--text-mute)" },
  gen:     { bg: "var(--violet-soft)",   fg: "var(--violet)",    accent: "var(--violet)" },
  filter:  { bg: "var(--teal-soft)",     fg: "var(--teal)",      accent: "var(--teal)" },
  score:   { bg: "var(--accent-soft)",   fg: "var(--accent-text)",accent: "var(--accent)" },
  refine:  { bg: "var(--warn-soft)",     fg: "var(--warn)",      accent: "var(--warn)" },
  analyze: { bg: "var(--bg-sunk)",       fg: "var(--text-mute)", accent: "var(--text-mute)" },
};

function PFStatusDot({ status, tick }) {
  if (status === "done") {
    return (
      <span style={{
        width: 14, height: 14, borderRadius: "50%",
        background: "var(--pos)", display: "grid", placeItems: "center",
      }}>
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5"><path d="M5 13l4 4L19 7"/></svg>
      </span>
    );
  }
  if (status === "running") {
    return (
      <span style={{
        position: "relative", width: 14, height: 14, borderRadius: "50%",
        background: "var(--accent)",
      }}>
        <span style={{
          position: "absolute", inset: -3, borderRadius: "50%",
          border: "1.5px solid var(--accent)",
          animation: "bio-pulse 1.4s infinite",
        }} />
      </span>
    );
  }
  if (status === "failed") {
    return <span style={{ width: 14, height: 14, borderRadius: "50%", background: "var(--neg)" }} />;
  }
  return <span style={{ width: 14, height: 14, borderRadius: "50%", border: "1.5px solid var(--border-strong)", background: "var(--bg-elev)" }} />;
}

function PFNode({ stage, compact, onClick, selected }) {
  const g = PF_GROUP[stage.group] || PF_GROUP.input;
  const isRunning = stage.status === "running";
  const isDone = stage.status === "done";
  const isQueued = stage.status === "queued";
  const total = (stage.inN ?? 0);
  const pass = stage.outN;
  const passRate = total && pass != null ? pass / total : null;

  return (
    <div
      onClick={onClick}
      style={{
        position: "relative",
        minWidth: compact ? 130 : 180,
        background: "var(--bg-elev)",
        border: `1px solid ${selected ? "var(--accent)" : isRunning ? g.accent : "var(--border)"}`,
        borderRadius: 4,
        padding: compact ? "6px 8px" : "8px 10px",
        cursor: onClick ? "pointer" : "default",
        overflow: "hidden",
        opacity: isQueued ? 0.7 : 1,
      }}
    >
      {/* Status indicator strip on top */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 2,
        background: isDone ? "var(--pos)" : isRunning ? g.accent : "var(--border)",
      }} />
      {isRunning && (
        <div style={{
          position: "absolute", top: 0, left: 0, height: 2,
          width: `${(stage.progress || 0.3) * 100}%`,
          background: "var(--accent)",
          boxShadow: "0 0 8px var(--accent)",
        }} />
      )}

      {/* Header: status + id + name */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
        <PFStatusDot status={stage.status} />
        <span className="mono" style={{ fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.02em" }}>{stage.id}</span>
        <span style={{ fontSize: compact ? 11.5 : 12.5, fontWeight: 600 }}>{stage.name}</span>
      </div>

      {/* Tool */}
      <div style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 3, lineHeight: 1.3, minHeight: 13 }}>
        {stage.tool}
      </div>

      {/* IO counts */}
      {!compact && (stage.inN != null || stage.outN != null) && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 6, fontSize: 10 }}>
          {stage.inN != null && (
            <span className="mono" style={{ color: "var(--text-mute)" }}>
              {stage.inN}<span style={{ fontSize: 9, opacity: 0.6 }}> {stage.inUnit || ""}</span>
            </span>
          )}
          {stage.inN != null && stage.outN != null && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          )}
          {stage.outN != null ? (
            <span className="mono" style={{ color: g.fg, fontWeight: 600 }}>
              {stage.outN}<span style={{ fontSize: 9, opacity: 0.6, fontWeight: 400 }}> {stage.outUnit || ""}</span>
            </span>
          ) : stage.status === "running" && (
            <span className="mono" style={{ color: "var(--text-dim)" }}>…running</span>
          )}
        </div>
      )}

      {/* Progress bar if running */}
      {isRunning && stage.progress != null && (
        <div style={{ marginTop: 6 }}>
          <div style={{ height: 3, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
            <div style={{
              width: `${stage.progress * 100}%`, height: "100%",
              background: g.accent,
            }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2, fontSize: 9, color: "var(--text-mute)" }} className="mono">
            <span>{Math.round((stage.progress || 0) * 100)}%</span>
            <span>{stage.time}</span>
          </div>
        </div>
      )}

      {/* Pass/Fail bar for done filter/score stages */}
      {isDone && passRate != null && stage.inN > 0 && (
        <div style={{ marginTop: 6 }}>
          <div style={{ height: 3, background: "var(--neg-soft)", borderRadius: 2, overflow: "hidden", display: "flex" }}>
            <div style={{ width: `${passRate * 100}%`, height: "100%", background: "var(--pos)" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2, fontSize: 9, color: "var(--text-mute)" }} className="mono">
            <span style={{ color: "var(--pos)" }}>pass {pass}</span>
            <span style={{ color: "var(--neg)" }}>fail {stage.inN - pass}</span>
          </div>
        </div>
      )}

      {/* Footer chips */}
      <div style={{ display: "flex", gap: 4, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
        {stage.gate && (
          <span style={{
            fontSize: 9, padding: "1px 4px", borderRadius: 2,
            background: g.bg, color: g.fg, fontWeight: 500,
            fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.01em",
          }}>
            {stage.gate}
          </span>
        )}
        {!compact && isDone && stage.time && (
          <span className="mono" style={{ fontSize: 9, color: "var(--text-dim)", marginLeft: "auto" }}>{stage.time}</span>
        )}
        {!compact && stage.gpu && (
          <span className="mono" style={{ fontSize: 9, color: "var(--text-dim)" }}>{stage.gpu}</span>
        )}
      </div>
    </div>
  );
}

function PFArrow({ active }) {
  return (
    <div style={{
      width: 18, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
    }}>
      <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
        <path d="M0 7h14M10 2l5 5-5 5" stroke={active ? "var(--accent)" : "var(--border-strong)"} strokeWidth="1.2" />
      </svg>
    </div>
  );
}

// Linear pipeline view: A or B
function PFLinear({ stages, compact, onSelectStage, selectedStage }) {
  return (
    <div style={{ display: "flex", alignItems: "stretch", overflowX: "auto", paddingBottom: 4 }} className="bio-scroll">
      {stages.map((s, i) => (
        <React.Fragment key={s.id + i}>
          <PFNode stage={s} compact={compact} onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
          {i < stages.length - 1 && <PFArrow active={s.status === "done"} />}
        </React.Fragment>
      ))}
    </div>
  );
}

// Combined pipeline view: parallel tracks → converge
function PFCombined({ pipeline, compact, onSelectStage, selectedStage }) {
  const { input, tracks, converge } = pipeline;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Top: shared input */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="bio-label" style={{ width: 80 }}>shared</span>
        <PFNode stage={input} compact onClick={() => onSelectStage?.(input)} selected={selectedStage === input.id} />
        <svg width="20" height="12" viewBox="0 0 20 12"><path d="M0 6h16M12 2l4 4-4 4" stroke="var(--text-dim)" strokeWidth="1.2" fill="none"/></svg>
        <span style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace" }}>fork to parallel tracks</span>
      </div>

      {/* Two parallel tracks */}
      <div style={{
        position: "relative",
        display: "grid",
        gridTemplateColumns: "80px 1fr 30px",
        rowGap: 8,
      }}>
        {/* A track */}
        <span className="bio-label" style={{ alignSelf: "center", color: "var(--violet)" }}>silo A · {tracks[0].label}</span>
        <div style={{ display: "flex", alignItems: "stretch", overflowX: "auto" }} className="bio-scroll">
          {tracks[0].stages.map((s, i) => (
            <React.Fragment key={"A" + s.id + i}>
              <PFNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
              {i < tracks[0].stages.length - 1 && <PFArrow active={s.status === "done"} />}
            </React.Fragment>
          ))}
        </div>
        <div style={{ alignSelf: "center" }}>
          <svg width="28" height="40" viewBox="0 0 28 40">
            <path d="M0 4h14V20h10M20 16l4 4-4 4" stroke="var(--text-dim)" strokeWidth="1.2" fill="none"/>
          </svg>
        </div>

        {/* B track */}
        <span className="bio-label" style={{ alignSelf: "center", color: "var(--teal)" }}>silo B · {tracks[1].label}</span>
        <div style={{ display: "flex", alignItems: "stretch", overflowX: "auto" }} className="bio-scroll">
          {tracks[1].stages.map((s, i) => (
            <React.Fragment key={"B" + s.id + i}>
              <PFNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
              {i < tracks[1].stages.length - 1 && <PFArrow active={s.status === "done"} />}
            </React.Fragment>
          ))}
        </div>
        <div style={{ alignSelf: "center" }}>
          <svg width="28" height="40" viewBox="0 0 28 40">
            <path d="M0 36h14V20h10M20 16l4 4-4 4" stroke="var(--text-dim)" strokeWidth="1.2" fill="none"/>
          </svg>
        </div>
      </div>

      {/* Converge label */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 80 }}>
        <span style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace" }}>→ converge: shared scoring · refine · analyze</span>
      </div>

      {/* Converge row */}
      <div style={{ display: "grid", gridTemplateColumns: "80px 1fr", gap: 0 }}>
        <span className="bio-label" style={{ alignSelf: "center" }}>shared</span>
        <div style={{ display: "flex", alignItems: "stretch", overflowX: "auto" }} className="bio-scroll">
          {converge.map((s, i) => (
            <React.Fragment key={"C" + s.id + i}>
              <PFNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
              {i < converge.length - 1 && <PFArrow active={s.status === "done"} />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

// Main entry
function PipelineFlow({ silo = "B", compact = false, onSelectStage, selectedStage }) {
  const pipeline = PROJECT_DATA.pipelines[silo];
  if (!pipeline) return null;

  // Summary stats
  const allStages = pipeline.stages || [
    pipeline.input,
    ...(pipeline.tracks?.[0]?.stages || []),
    ...(pipeline.tracks?.[1]?.stages || []),
    ...(pipeline.converge || []),
  ];
  const doneN = allStages.filter(s => s?.status === "done").length;
  const runningN = allStages.filter(s => s?.status === "running").length;
  const queuedN = allStages.filter(s => s?.status === "queued").length;
  const overall = (doneN + runningN * 0.5) / allStages.length;

  return (
    <div className="bio-panel" style={{ overflow: "hidden" }}>
      <div className="bio-panel-hd">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span>{pipeline.name}</span>
          <span style={{ color: "var(--text-dim)", textTransform: "none", letterSpacing: 0, fontWeight: 400 }}>
            {pipeline.description}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="bio-pill pos" style={{ padding: "1px 6px", fontSize: 9.5 }}>done {doneN}</span>
          {runningN > 0 && <span className="bio-pill accent" style={{ padding: "1px 6px", fontSize: 9.5 }}><span className="bio-dot" />{runningN}</span>}
          <span className="bio-pill" style={{ padding: "1px 6px", fontSize: 9.5 }}>queued {queuedN}</span>
          <div style={{ width: 80, height: 4, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
            <div style={{ width: `${overall * 100}%`, height: "100%", background: "var(--accent)" }} />
          </div>
          <span className="mono" style={{ fontSize: 10, color: "var(--text-mute)", minWidth: 28, textAlign: "right" }}>{Math.round(overall * 100)}%</span>
        </div>
      </div>

      <div style={{ padding: "10px 12px" }}>
        {pipeline.stages
          ? <PFLinear stages={pipeline.stages} compact={compact} onSelectStage={onSelectStage} selectedStage={selectedStage} />
          : <PFCombined pipeline={pipeline} compact={compact} onSelectStage={onSelectStage} selectedStage={selectedStage} />
        }
      </div>

      {/* Group legend */}
      <div style={{
        padding: "8px 12px", borderTop: "1px solid var(--border)",
        display: "flex", gap: 12, fontSize: 10, color: "var(--text-mute)", flexWrap: "wrap",
      }}>
        {Object.entries({ input: "input", gen: "generation", filter: "filter", score: "score", refine: "refine", analyze: "analyze" }).map(([k, label]) => (
          <span key={k} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{
              width: 8, height: 8, borderRadius: 2,
              background: PF_GROUP[k].bg, border: `1px solid ${PF_GROUP[k].accent}`,
            }} />
            <span>{label}</span>
          </span>
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--pos)" }} /> done
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent)" }} /> running
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", border: "1.5px solid var(--border-strong)" }} /> queued
        </span>
      </div>
    </div>
  );
}

window.PipelineFlow = PipelineFlow;
window.PFNode = PFNode;
