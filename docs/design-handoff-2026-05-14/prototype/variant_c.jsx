/* global React, PROJECT_DATA */
const { useState: useStateC, useEffect: useEffectC, useRef: useRefC } = React;

function VariantC() {
  const data = PROJECT_DATA;
  const rootRef = useRefC(null);
  const [viewMode, setViewMode] = useStateC("ribbon");
  const cand = data.candidates.find(c => c.id === "cand03");
  const wt = data.candidates.find(c => c.wildtype);

  return (
    <div ref={rootRef} data-theme="dark" style={{
      width: "100%", height: "100%",
      background: "var(--bg)", color: "var(--text)",
      fontFamily: "Inter, sans-serif", fontSize: 13,
      display: "flex", flexDirection: "column",
    }}>
      {/* Header */}
      <header style={{
        display: "flex", alignItems: "center", gap: 14,
        padding: "10px 20px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-elev)",
      }}>
        <button className="bio-btn ghost" style={{ padding: "2px 8px" }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 18l-6-6 6-6"/></svg>
          <span>candidates</span>
        </button>
        <div style={{ width: 1, height: 18, background: "var(--border)" }} />
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="mono" style={{ fontSize: 16, fontWeight: 600 }}>{cand.id}</span>
            <TierBadge tier={cand.tier} />
            <span className="bio-pill pos" style={{ padding: "1px 7px", fontSize: 10.5 }}>★ RECOMMENDED</span>
            <span className="bio-pill" style={{ padding: "1px 7px" }}>silo B</span>
            <span className="bio-pill" style={{ padding: "1px 7px" }}>iter02</span>
          </div>
          <div style={{ fontSize: 11, color: "var(--text-mute)", marginTop: 2 }}>
            <span className="mono">{cand.seq}</span> · G2I 단일 치환 · source <span className="mono">{cand.source}</span>
          </div>
        </div>
        <div style={{ flex: 1 }} />
        <button className="bio-btn ghost">⇣ PDB</button>
        <button className="bio-btn ghost">⇣ Report</button>
        <button className="bio-btn primary">Wetlab Ki 발주 →</button>
        <ThemeToggle scope={rootRef} defaultTheme="dark" />
      </header>

      <div style={{
        flex: 1, display: "grid",
        gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)",
        gridTemplateRows: "auto 1fr",
        gap: 0,
        minHeight: 0,
        overflow: "auto",
      }}>
        {/* Top-left: 3D viewer + sequence */}
        <section style={{ gridColumn: 1, gridRow: 1, padding: "16px 20px", borderRight: "1px solid var(--border)" }}>
          <div className="bio-panel">
            <div className="bio-panel-hd">
              <span>구조 · cand03 in SSTR2 (7XNA holo)</span>
              <div style={{ display: "flex", gap: 4 }}>
                {["ribbon", "surface", "stick", "interface"].map(m => (
                  <button key={m} className="bio-btn" onClick={() => setViewMode(m)} style={{
                    padding: "2px 7px", fontSize: 10.5,
                    background: viewMode === m ? "var(--bg-sunk)" : "transparent",
                    borderColor: viewMode === m ? "var(--text-mute)" : "var(--border)",
                  }}>{m}</button>
                ))}
              </div>
            </div>
            <div style={{ padding: 12 }}>
              <MolViewer candidate={cand} height={300} caption={`MOLSTAR 5.6 · ${viewMode.toUpperCase()}`} />
              <div style={{
                display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginTop: 12,
              }}>
                <Contact pos="K4" partner="Asp137" dist="2.8 Å" type="salt-bridge" />
                <Contact pos="W8" partner="Phe294" dist="3.4 Å" type="π-stack" />
                <Contact pos="F6/F7" partner="hydrophobic" dist="3.6 Å avg" type="cluster" />
                <Contact pos="T10" partner="Gln138" dist="2.9 Å" type="H-bond" />
              </div>
            </div>
          </div>
        </section>

        {/* Top-right: scores & headline metrics */}
        <section style={{ gridColumn: 2, gridRow: 1, padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
            <BigStat label="iPTM(SSTR2)" value="0.952" tone="pos" sub="best receptor" />
            <BigStat label="margin" value="+0.008" tone="pos" sub="vs max off" />
            <BigStat label="ddG" value="−48.5" sub="kcal/mol" />
            <BigStat label="GRAVY" value="+0.379" sub="vs SST-14 +0.029" tone="warn" />
          </div>

          <div className="bio-panel" style={{ flex: 1 }}>
            <div className="bio-panel-hd">
              <span>Selectivity · 5 SSTR</span>
              <span className="mono" style={{ fontSize: 10 }}>iPTM</span>
            </div>
            <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
              {data.receptors.map(r => {
                const v = cand.iptm[r];
                const isTarget = r === "SSTR2";
                return (
                  <div key={r} style={{ display: "grid", gridTemplateColumns: "70px 1fr 60px 70px", gap: 10, alignItems: "center" }}>
                    <span style={{
                      display: "flex", alignItems: "center", gap: 6,
                      fontFamily: "JetBrains Mono", fontSize: 12, fontWeight: isTarget ? 700 : 500,
                      color: isTarget ? "var(--accent-text)" : "var(--text-mute)",
                    }}>
                      {isTarget && "★"} {r}
                    </span>
                    <div style={{ position: "relative", height: 18, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
                      <div style={{
                        width: `${((v - 0.7) / 0.3) * 100}%`,
                        height: "100%", background: iptmColor(v),
                      }} />
                      {isTarget && (
                        <div style={{ position: "absolute", inset: 0, border: "1.5px dashed var(--accent)", borderRadius: 2, pointerEvents: "none" }} />
                      )}
                    </div>
                    <span className="mono" style={{ textAlign: "right", fontSize: 12, fontWeight: isTarget ? 700 : 500 }}>
                      {v.toFixed(3)}
                    </span>
                    <span style={{
                      fontSize: 10, color: "var(--text-mute)", textAlign: "right", fontFamily: "JetBrains Mono",
                    }}>
                      Ki ~ {r === "SSTR1" ? "≥5" : r === "SSTR2" ? "0.5–5" : r === "SSTR3" ? "≥10" : r === "SSTR4" ? "≥5" : "≥10"} nM
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Bottom-left: sequence comparison + variants */}
        <section style={{ gridColumn: 1, gridRow: 2, padding: "16px 20px", borderRight: "1px solid var(--border)", borderTop: "1px solid var(--border)" }}>
          <div className="bio-panel" style={{ marginBottom: 14 }}>
            <div className="bio-panel-hd"><span>서열 비교 · WT vs cand03</span><span className="mono" style={{ fontSize: 10 }}>14 aa · disulfide C3–C14</span></div>
            <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
              <SeqDiff label="SST-14 (WT)" seq={wt.seq} wt={wt.seq} ki="0.2 nM" />
              <SeqDiff label="cand03" seq={cand.seq} wt={wt.seq} ki="0.5–5 nM (예측)" highlight />
              <SeqDiff label="var12 (T12 → D-Thr)" seq="AICKNFFWKTF*SC" wt={wt.seq} ki="—" mod="D-Thr12" />
              <SeqDiff label="winner ILCKKFFWKTFTSC" seq="ILCKKFFWKTFTSC" wt={wt.seq} ki="—" badge="margin +0.070" />
            </div>
          </div>

          <div className="bio-panel">
            <div className="bio-panel-hd">
              <span>cand03 변이체 카탈로그 · 20종 (chemistry T4)</span>
              <span className="mono" style={{ fontSize: 10 }}>cand03_variants.json v1.1</span>
            </div>
            <div style={{ padding: "8px 0" }}>
              <table className="bio-table">
                <thead>
                  <tr>
                    <th>variant</th>
                    <th>modification</th>
                    <th style={{ textAlign: "right" }}>HL score</th>
                    <th style={{ textAlign: "right" }}>chymo</th>
                    <th style={{ textAlign: "right" }}>tryp</th>
                    <th style={{ textAlign: "right" }}>NEP</th>
                    <th>priority</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { v: "cand03", mod: "Ac-N / NH2-C (base)", hl: 16.60, chymo: 4, tryp: 2, nep: 5, pri: "baseline" },
                    { v: "var12", mod: "D-Thr12", hl: 16.72, chymo: 4, tryp: 2, nep: 5, pri: "★ 1순위", star: true },
                    { v: "var07", mod: "I2K + K4-DOTA", hl: 14.20, chymo: 4, tryp: 3, nep: 5, pri: "2순위" },
                    { v: "var18", mod: "I2Y (Tyr ¹²⁵I 라벨)", hl: 15.80, chymo: 4, tryp: 2, nep: 5, pri: "3순위 · chemistry" },
                    { v: "var09", mod: "Glu1 + K4 lactam (i+3)", hl: 18.10, chymo: 2, tryp: 1, nep: 4, pri: "4순위 · stability" },
                  ].map(r => (
                    <tr key={r.v} style={{ background: r.star ? "var(--pos-soft)" : "transparent" }}>
                      <td className="mono" style={{ fontWeight: 600 }}>{r.v}</td>
                      <td style={{ fontSize: 11 }}>{r.mod}</td>
                      <td className="mono" style={{ textAlign: "right" }}>{r.hl.toFixed(2)}</td>
                      <td className="mono" style={{ textAlign: "right", color: "var(--text-mute)" }}>{r.chymo}</td>
                      <td className="mono" style={{ textAlign: "right", color: "var(--text-mute)" }}>{r.tryp}</td>
                      <td className="mono" style={{ textAlign: "right", color: "var(--text-mute)" }}>{r.nep}</td>
                      <td style={{ fontSize: 11, color: r.star ? "var(--pos)" : "var(--text-mute)", fontWeight: r.star ? 600 : 400 }}>{r.pri}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Bottom-right: decision reasoning + ADMET + actions */}
        <section style={{ gridColumn: 2, gridRow: 2, padding: "16px 20px", borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: 14 }}>

          {/* Agent reasoning summary */}
          <div className="bio-panel">
            <div className="bio-panel-hd">
              <span>5-Agent 결정 트레일</span>
              <span className="bio-pill pos" style={{ padding: "1px 6px" }}><span className="bio-dot" />consensus</span>
            </div>
            <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
              <AgentLine agent="planner" color="violet" text="iter02 pos2 G→I/V/L 친수성 변이 확장 · FWKT 보존 강제" />
              <AgentLine agent="builder" color="blue" text="Boltz-2 batch (10 cand × 5 SSTR), pyrosetta refine 80 → 16 → 1" />
              <AgentLine agent="qcranker" color="cyan" text="cand03 SSTR2 best, margin +0.008 — 10개 중 유일 T2" />
              <AgentLine agent="critic" color="amber" text="ranking 신뢰 등급: iPTM ≠ Ki 경고. wetlab 검증 필요 (R7)" />
              <AgentLine agent="reporter" color="stone" text="cand03 → docs/wetlab/cand03_binding_assay_design.md (₩2.5M, 8주)" />
            </div>
          </div>

          {/* ADMET + Stability */}
          <div className="bio-panel">
            <div className="bio-panel-hd"><span>ADMET · step08 stability prescreen</span></div>
            <div style={{ padding: "12px 16px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <ADMETBar label="t½ (예측)" value={5} max={120} unit="min" warn />
              <ADMETBar label="instability" value={30.65} max={100} unit="" good />
              <ADMETBar label="Boman index" value={0.18} max={2.5} unit="kcal" good />
              <ADMETBar label="aggregation" value={0.42} max={1.0} unit="score" warn />
            </div>
            <div style={{ padding: "8px 16px", borderTop: "1px solid var(--border)", fontSize: 11, color: "var(--text-mute)", display: "flex", alignItems: "center", gap: 6 }}>
              <span className="bio-pill warn" style={{ padding: "0 5px", fontSize: 10 }}>HEURISTIC · LOW</span>
              <span>F6, F7, W8 chymotrypsin 취약. D-Thr12 또는 K4-acyl modification 권장.</span>
            </div>
          </div>

          {/* Decision panel */}
          <div className="bio-panel" style={{ background: "var(--pos-soft)", borderColor: "var(--pos)" }}>
            <div className="bio-panel-hd" style={{ color: "var(--pos)" }}>
              <span>다음 액션 · iter03 계획</span>
              <span className="mono" style={{ fontSize: 10 }}>pending PI approval</span>
            </div>
            <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 6 }}>
              <DecisionItem text="cand03 wetlab Ki 발주 (SSTR1–5 radioligand assay, n=3)" cost="₩2.5M" time="8주" />
              <DecisionItem text="var12 (D-Thr12) 합성 — stability 보강" cost="₩1.2M" time="3주" />
              <DecisionItem text="cand03 변이체 20종 → Boltz-2 batch (G2 친수성 변이 확장)" cost="—" time="4h GPU" />
              <DecisionItem text="step05c Boltz cross-val을 default pipeline에 통합 (CI)" cost="—" time="0.5d eng" />
            </div>
            <div style={{ padding: "8px 16px", borderTop: "1px solid var(--pos)", display: "flex", gap: 6, justifyContent: "flex-end" }}>
              <button className="bio-btn ghost" style={{ color: "var(--text-mute)" }}>defer</button>
              <button className="bio-btn">comment</button>
              <button className="bio-btn primary">approve next iter</button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function Contact({ pos, partner, dist, type }) {
  return (
    <div style={{ padding: "6px 8px", background: "var(--bg-sunk)", borderRadius: 3, border: "1px solid var(--border)" }}>
      <div className="mono" style={{ fontSize: 11, fontWeight: 600 }}>{pos} · {partner}</div>
      <div style={{ fontSize: 10, color: "var(--text-mute)", marginTop: 2, display: "flex", justifyContent: "space-between" }}>
        <span>{type}</span>
        <span className="mono">{dist}</span>
      </div>
    </div>
  );
}

function BigStat({ label, value, sub, tone }) {
  const color = tone === "pos" ? "var(--pos)" : tone === "warn" ? "var(--warn)" : tone === "neg" ? "var(--neg)" : "var(--text)";
  return (
    <div style={{ padding: "10px 12px", border: "1px solid var(--border)", borderRadius: 3, background: "var(--bg-elev)" }}>
      <div className="bio-label">{label}</div>
      <div className="mono" style={{ fontSize: 22, fontWeight: 600, color, marginTop: 2, lineHeight: 1.1 }}>{value}</div>
      <div style={{ fontSize: 10.5, color: "var(--text-mute)", marginTop: 2 }}>{sub}</div>
    </div>
  );
}

function SeqDiff({ label, seq, wt, ki, mod, badge, highlight }) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "180px auto 1fr 90px",
      gap: 10, alignItems: "center",
      padding: highlight ? "5px 6px" : 0,
      background: highlight ? "var(--accent-soft)" : "transparent",
      borderRadius: 3,
    }}>
      <div style={{ fontSize: 11, color: highlight ? "var(--accent-text)" : "var(--text-mute)", fontWeight: highlight ? 600 : 400 }}>
        {label}
      </div>
      <Sequence seq={seq} wildtype={wt} />
      <div style={{ fontSize: 10.5, color: "var(--text-mute)" }}>
        {mod && <span className="bio-pill" style={{ padding: "0 5px", fontSize: 9.5 }}>mod · {mod}</span>}
        {badge && <span className="bio-pill pos" style={{ padding: "0 5px", fontSize: 9.5 }}>{badge}</span>}
      </div>
      <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", textAlign: "right" }}>{ki}</div>
    </div>
  );
}

function AgentLine({ agent, color, text }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "70px 1fr", gap: 8, fontSize: 11, lineHeight: 1.5 }}>
      <span className="bio-pill" style={{
        padding: "0px 5px", fontSize: 9.5, fontWeight: 600,
        background: `var(--${color}-soft, var(--accent-soft))`,
        color: `var(--${color}, var(--accent-text))`, border: 0,
        justifyContent: "center",
      }}>{agent.toUpperCase()}</span>
      <span>{text}</span>
    </div>
  );
}

function ADMETBar({ label, value, max, unit, good, warn }) {
  const color = good ? "var(--pos)" : warn ? "var(--warn)" : "var(--neg)";
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
        <span style={{ color: "var(--text-mute)" }}>{label}</span>
        <span className="mono" style={{ fontWeight: 600, color }}>{value}{unit && ` ${unit}`}</span>
      </div>
      <div style={{ height: 4, background: "var(--bg-sunk)", borderRadius: 2, marginTop: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color }} />
      </div>
    </div>
  );
}

function DecisionItem({ text, cost, time }) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "20px 1fr 60px 60px",
      gap: 8, alignItems: "center", padding: "5px 0",
      borderBottom: "1px solid var(--border)",
      fontSize: 11.5, lineHeight: 1.4,
    }}>
      <span style={{
        width: 14, height: 14, border: "1.5px solid var(--pos)", borderRadius: 3,
        display: "grid", placeItems: "center",
      }}>
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="var(--pos)" strokeWidth="3"><path d="M5 13l4 4L19 7"/></svg>
      </span>
      <span>{text}</span>
      <span className="mono" style={{ textAlign: "right", color: "var(--text-mute)", fontSize: 11 }}>{cost}</span>
      <span className="mono" style={{ textAlign: "right", color: "var(--text-mute)", fontSize: 11 }}>{time}</span>
    </div>
  );
}

window.VariantC = VariantC;
