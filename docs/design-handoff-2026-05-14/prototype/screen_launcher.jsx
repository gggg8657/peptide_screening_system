/* global React, PROJECT_DATA */
// Run Launcher — start a new pipeline run, edit gates, choose silo

function ScreenLauncher() {
  const data = PROJECT_DATA;
  const rootRef = React.useRef(null);
  const [silo, setSilo] = React.useState("B");
  const [iterations, setIterations] = React.useState(3);
  const [nBackbone, setNBackbone] = React.useState(10);
  const [kSeq, setKSeq] = React.useState(8);
  const [topM, setTopM] = React.useState(10);
  const [llm, setLlm] = React.useState("qwen3-32b");
  const [seed, setSeed] = React.useState(42);
  const [boltzCross, setBoltzCross] = React.useState(true);
  const [offTargets, setOffTargets] = React.useState(new Set(["SSTR1", "SSTR3", "SSTR4", "SSTR5"]));
  const [gates, setGates] = React.useState({
    plddt: 60, plddt_iface: 45, dock_top: 20, ddg: -1.0, selectivity: -10,
    iptm_margin: 0, stability_hl: 50,
  });
  const [name, setName] = React.useState("local_20260512_iter03");

  const designSpace = silo === "A" ? nBackbone * kSeq : silo === "B" ? 240 : nBackbone * kSeq + 240;
  const eta = silo === "A" ? "32m" : silo === "B" ? "28m" : "47m";

  function toggleOffTarget(r) {
    setOffTargets(prev => {
      const next = new Set(prev);
      if (next.has(r)) next.delete(r); else next.add(r);
      return next;
    });
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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 2v6m0 0l-3-3m3 3l3-3M5 12v8a2 2 0 002 2h10a2 2 0 002-2v-8"/></svg>
          <div style={{ fontWeight: 600 }}>새 실행 · run launcher</div>
          <span className="bio-pill" style={{ padding: "1px 6px" }}>iter03 draft</span>
        </div>
        <div style={{ flex: 1 }} />
        <ThemeToggle scope={rootRef} />
      </header>

      <div style={{ flex: 1, overflow: "auto", padding: "20px 24px" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 360px", gap: 20 }}>

          {/* LEFT — Form */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Run identity */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>1 · Identity</span></div>
              <div style={{ padding: "12px 16px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                <Field label="Run name">
                  <input value={name} onChange={e => setName(e.target.value)} className="bio-input mono" style={{ width: "100%", fontSize: 12 }} />
                </Field>
                <Field label="Iterations">
                  <input type="number" min={1} max={20} value={iterations} onChange={e => setIterations(+e.target.value)} className="bio-input mono" style={{ width: "100%" }} />
                </Field>
                <Field label="Seed">
                  <input type="number" value={seed} onChange={e => setSeed(+e.target.value)} className="bio-input mono" style={{ width: "100%" }} />
                </Field>
              </div>
            </div>

            {/* Silo choice */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>2 · Silo · 파이프라인 전략</span></div>
              <div style={{ padding: "12px 16px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                <SiloCard active={silo === "A"} onClick={() => setSilo("A")}
                  id="A" name="De Novo" tools={["RFdiffusion", "ProteinMPNN", "ESMFold", "Boltz-2"]}
                  pros="다양성 ↑ · novel scaffold" cons="합성 어려움" />
                <SiloCard active={silo === "B"} onClick={() => setSilo("B")}
                  id="B" name="Mutation+Dock" tools={["BLOSUM62 + LLM", "DiffDock", "Boltz-2", "PyRosetta"]}
                  pros="안정성 ↑ · 합성 가능" cons="다양성 제한" />
                <SiloCard active={silo === "A+B"} onClick={() => setSilo("A+B")}
                  id="A+B" name="Dual silo" tools={["A + B 병렬", "통합 scoring"]}
                  pros="검증 dual + 다양성" cons="비용 2×" />
              </div>
            </div>

            {/* Generation params — depends on silo */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>3 · Generation 파라미터</span></div>
              <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 12 }}>
                {(silo === "A" || silo === "A+B") && (
                  <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: 10, alignItems: "center" }}>
                    <span style={{ color: "var(--text-mute)", display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="bio-pill violet" style={{ padding: "0 5px", fontSize: 9.5 }}>A</span>
                      n_backbone
                    </span>
                    <input type="range" min={2} max={30} value={nBackbone} onChange={e => setNBackbone(+e.target.value)} style={{ accentColor: "var(--accent)" }} />
                    <span className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{nBackbone} backbones</span>
                  </div>
                )}
                {(silo === "A" || silo === "A+B") && (
                  <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: 10, alignItems: "center" }}>
                    <span style={{ color: "var(--text-mute)", display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="bio-pill violet" style={{ padding: "0 5px", fontSize: 9.5 }}>A</span>
                      k_seq / bb
                    </span>
                    <input type="range" min={1} max={32} value={kSeq} onChange={e => setKSeq(+e.target.value)} style={{ accentColor: "var(--accent)" }} />
                    <span className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{kSeq} seq/bb</span>
                  </div>
                )}
                {(silo === "B" || silo === "A+B") && (
                  <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: 10, alignItems: "center" }}>
                    <span style={{ color: "var(--text-mute)", display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="bio-pill teal" style={{ padding: "0 5px", fontSize: 9.5 }}>B</span>
                      mutation strategy
                    </span>
                    <select className="bio-input" defaultValue="ga_bo">
                      <option value="ga_bo">ga_bo · GA + Bayesian opt</option>
                      <option value="enumerate">enumerate · 전수 탐색</option>
                      <option value="sampling">sampling · random constrained</option>
                    </select>
                    <span />
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: 10, alignItems: "center" }}>
                  <span style={{ color: "var(--text-mute)" }}>top_m_rosetta</span>
                  <input type="range" min={1} max={30} value={topM} onChange={e => setTopM(+e.target.value)} style={{ accentColor: "var(--accent)" }} />
                  <span className="mono" style={{ textAlign: "right", fontWeight: 600 }}>{topM} for refine</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 120px", gap: 10, alignItems: "center" }}>
                  <span style={{ color: "var(--text-mute)" }}>LLM model</span>
                  <select value={llm} onChange={e => setLlm(e.target.value)} className="bio-input">
                    <option value="qwen3-32b">qwen3-32b · 80GB</option>
                    <option value="qwen3-14b">qwen3-14b · 40GB</option>
                    <option value="qwen3-7b">qwen3-7b · 20GB</option>
                    <option value="gpt-oss-120b">gpt-oss-120b</option>
                  </select>
                  <span className="mono" style={{ textAlign: "right", color: "var(--text-mute)" }}>vLLM</span>
                </div>
              </div>
            </div>

            {/* Gates */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>4 · Gate 임계값</span><span className="mono" style={{ fontSize: 10 }}>pipeline_local/config/gate_thresholds.yaml</span></div>
              <div style={{ padding: "12px 16px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <GateSlider label="pLDDT (mean)" value={gates.plddt} min={30} max={90} step={1} unit="" onChange={v => setGates({ ...gates, plddt: v })} />
                <GateSlider label="pLDDT (interface)" value={gates.plddt_iface} min={30} max={70} step={1} unit="" onChange={v => setGates({ ...gates, plddt_iface: v })} />
                <GateSlider label="Docking top%" value={gates.dock_top} min={5} max={50} step={1} unit="%" onChange={v => setGates({ ...gates, dock_top: v })} />
                <GateSlider label="Rosetta ddG" value={gates.ddg} min={-5} max={0} step={0.1} unit="kcal/mol" onChange={v => setGates({ ...gates, ddg: v })} />
                <GateSlider label="Selectivity margin" value={gates.selectivity} min={-30} max={0} step={0.5} unit="kcal/mol" onChange={v => setGates({ ...gates, selectivity: v })} />
                <GateSlider label="Boltz iPTM margin" value={gates.iptm_margin} min={-0.05} max={0.1} step={0.005} unit="" onChange={v => setGates({ ...gates, iptm_margin: v })} />
                <GateSlider label="Stability t½" value={gates.stability_hl} min={5} max={200} step={5} unit="h" onChange={v => setGates({ ...gates, stability_hl: v })} />
              </div>
            </div>

            {/* Off-targets */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>5 · Off-target 수용체 · selectivity</span></div>
              <div style={{ padding: "12px 16px", display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.offTargets.map(t => (
                  <button key={t.name} onClick={() => toggleOffTarget(t.name)} style={{
                    padding: "6px 10px", borderRadius: 4, cursor: "pointer",
                    background: offTargets.has(t.name) ? "var(--accent-soft)" : "var(--bg-sunk)",
                    border: `1px solid ${offTargets.has(t.name) ? "var(--accent)" : "var(--border)"}`,
                    color: offTargets.has(t.name) ? "var(--accent-text)" : "var(--text-mute)",
                    fontFamily: "inherit", fontSize: 12, display: "flex", alignItems: "center", gap: 6,
                  }}>
                    <input type="checkbox" checked={offTargets.has(t.name)} readOnly style={{ margin: 0, accentColor: "var(--accent)" }} />
                    <span className="mono" style={{ fontWeight: 600 }}>{t.name}</span>
                    <span style={{ color: "var(--text-mute)", fontSize: 10 }}>{t.uniprot} · {t.pdb}</span>
                  </button>
                ))}
              </div>
              <div style={{ padding: "8px 16px", borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 11, color: "var(--text-mute)" }}>
                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input type="checkbox" checked={boltzCross} onChange={e => setBoltzCross(e.target.checked)} style={{ accentColor: "var(--accent)" }} />
                  <span>step05c Boltz-2 cross-validation 활성</span>
                </label>
                <span className="mono">+ ~8min/iter</span>
              </div>
            </div>
          </div>

          {/* RIGHT — Summary + Submit */}
          <aside style={{ display: "flex", flexDirection: "column", gap: 16, position: "sticky", top: 0, alignSelf: "flex-start" }}>
            <div className="bio-panel" style={{ background: "var(--bg-elev)" }}>
              <div className="bio-panel-hd"><span>Plan · 사전 미리보기</span></div>
              <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
                <SummaryRow label="silo" value={silo === "A" ? "A · de novo" : silo === "B" ? "B · mutation+dock" : "Dual A+B"} />
                <SummaryRow label="design space" value={`~${designSpace}`} unit="seq" />
                <SummaryRow label="iterations" value={iterations} unit="× iter" />
                <SummaryRow label="off-target" value={offTargets.size} unit="receptors" />
                <SummaryRow label="LLM" value={llm} mono />
                <SummaryRow label="GPU" value="H100 NVL × 4" mono />
                <SummaryRow label="ETA" value={eta} unit="per iter" tone="accent" />
              </div>
              <div style={{ borderTop: "1px solid var(--border)", padding: "10px 12px", display: "flex", gap: 6 }}>
                <button className="bio-btn" style={{ flex: 1 }}>save config</button>
                <button className="bio-btn primary" style={{ flex: 2 }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21" /></svg>
                  실행 시작
                </button>
              </div>
            </div>

            <div className="bio-panel">
              <div className="bio-panel-hd"><span>예상 게이트 통과율</span><span className="mono" style={{ fontSize: 10 }}>iter02 데이터 기반</span></div>
              <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                <PredictBar label="G1 pLDDT" value={91} />
                <PredictBar label="G2 Docking" value={22} />
                <PredictBar label="G3 Selectivity" value={50} />
                <PredictBar label="G3b iPTM margin" value={12} warn />
                <PredictBar label="G4 Rosetta ddG" value={100} />
                <PredictBar label="G5 Stability" value={100} />
              </div>
            </div>

            <div style={{
              padding: "10px 14px", border: "1px solid var(--warn)",
              background: "var(--warn-soft)", borderRadius: 4, fontSize: 11.5, lineHeight: 1.5,
            }}>
              <strong style={{ color: "var(--warn)" }}>⚠ G3b 경고</strong> · iter02에서 8 → 1 통과. iPTM margin 임계값을 −0.005까지 완화 시 통과율 ≈ 38% 예상.
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function SiloCard({ active, onClick, id, name, tools, pros, cons }) {
  return (
    <button onClick={onClick} style={{
      textAlign: "left", padding: "10px 12px", borderRadius: 4, cursor: "pointer",
      background: active ? "var(--accent-soft)" : "var(--bg-elev)",
      border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
      fontFamily: "inherit", fontSize: 12,
      display: "flex", flexDirection: "column", gap: 6,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="mono" style={{
          width: 26, height: 22, borderRadius: 3,
          background: active ? "var(--accent)" : "var(--text-mute)",
          color: active ? "white" : "var(--bg-elev)",
          display: "grid", placeItems: "center", fontWeight: 700, fontSize: 11,
        }}>{id}</span>
        <span style={{ fontWeight: 600 }}>{name}</span>
      </div>
      <div style={{ fontSize: 10.5, color: "var(--text-mute)", display: "flex", flexWrap: "wrap", gap: 4 }}>
        {tools.map(t => <span key={t} className="mono" style={{ background: "var(--bg-sunk)", padding: "0 4px", borderRadius: 2 }}>{t}</span>)}
      </div>
      <div style={{ fontSize: 10.5, color: "var(--pos)" }}>+ {pros}</div>
      <div style={{ fontSize: 10.5, color: "var(--neg)" }}>− {cons}</div>
    </button>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="bio-label" style={{ marginBottom: 3 }}>{label}</div>
      {children}
    </div>
  );
}

function GateSlider({ label, value, min, max, step, unit, onChange }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: "var(--text-mute)" }}>{label}</span>
        <span className="mono" style={{ fontSize: 11, fontWeight: 600 }}>{typeof value === "number" ? value.toFixed(step < 1 ? 3 : 0) : value} {unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(+e.target.value)}
        style={{ width: "100%", accentColor: "var(--accent)" }} />
    </div>
  );
}

function SummaryRow({ label, value, unit, mono, tone }) {
  const color = tone === "accent" ? "var(--accent-text)" : "var(--text)";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", paddingBottom: 4, borderBottom: "1px dashed var(--border)" }}>
      <span style={{ fontSize: 11, color: "var(--text-mute)" }}>{label}</span>
      <span style={{ fontFamily: mono || typeof value === "number" ? "JetBrains Mono, monospace" : "inherit", fontWeight: 600, color, fontSize: 12 }}>
        {value} {unit && <span style={{ fontSize: 10, color: "var(--text-mute)", fontWeight: 400 }}>{unit}</span>}
      </span>
    </div>
  );
}

function PredictBar({ label, value, warn }) {
  const color = value > 80 ? "var(--pos)" : value > 40 ? "var(--accent)" : warn ? "var(--warn)" : "var(--neg)";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
        <span style={{ color: "var(--text-mute)" }}>{label}</span>
        <span className="mono" style={{ fontWeight: 600, color }}>{value}%</span>
      </div>
      <div style={{ height: 4, background: "var(--bg-sunk)", borderRadius: 2, marginTop: 2, overflow: "hidden" }}>
        <div style={{ width: `${value}%`, height: "100%", background: color }} />
      </div>
    </div>
  );
}

window.ScreenLauncher = ScreenLauncher;
