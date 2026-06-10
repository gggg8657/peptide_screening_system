/* global React, PROJECT_DATA */
// Wetlab Order — cand03 binding assay design + procurement
// Inspired by docs/wetlab/cand03_binding_assay_design.md

function ScreenWetlab() {
  const data = PROJECT_DATA;
  const rootRef = React.useRef(null);
  const cand = data.candidates.find(c => c.id === "cand03");
  const [stage, setStage] = React.useState(2); // 0..4

  const stages = ["draft", "review", "approval", "PO", "shipped"];

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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M10 2v6h-3l5 8 5-8h-3V2zM5 22h14"/></svg>
          <div style={{ fontWeight: 600 }}>Wetlab Order · in-vitro Ki assay</div>
          <span className="bio-pill" style={{ padding: "1px 6px" }}>cand03 AICKNFFWKTFTSC</span>
          <span className="bio-pill accent" style={{ padding: "1px 6px" }}>WO-2026-005</span>
        </div>
        <div style={{ flex: 1 }} />
        <button className="bio-btn ghost" style={{ fontSize: 10.5 }}>⇣ binding_assay_design.md</button>
        <ThemeToggle scope={rootRef} />
      </header>

      {/* Status / progress strip */}
      <div style={{
        padding: "8px 20px", display: "flex", alignItems: "center", gap: 6,
        borderBottom: "1px solid var(--border)", background: "var(--bg-elev)",
      }}>
        {stages.map((s, i) => (
          <React.Fragment key={s}>
            <button onClick={() => setStage(i)} style={{
              padding: "3px 12px", borderRadius: 3, cursor: "pointer",
              fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 600,
              background: i <= stage ? "var(--pos)" : "var(--bg-sunk)",
              color: i <= stage ? "white" : "var(--text-mute)",
              border: i === stage ? "1.5px solid var(--text)" : "1px solid transparent",
            }}>{i + 1}. {s}</button>
            {i < stages.length - 1 && <div style={{ width: 16, height: 1, background: i < stage ? "var(--pos)" : "var(--border-strong)" }} />}
          </React.Fragment>
        ))}
        <div style={{ flex: 1 }} />
        <span className="mono" style={{ fontSize: 10.5, color: "var(--text-mute)" }}>last updated 2026-05-12 15:09 KST · reporter</span>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: "16px 20px" }}>
        <div style={{ maxWidth: 1320, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 360px", gap: 16 }}>

          {/* LEFT */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Hypothesis & rationale */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>1 · 가설 · hypothesis</span><span className="mono" style={{ fontSize: 10 }}>§ rationale</span></div>
              <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
                <Hyp tag="H1" tone="pos">
                  <strong>주 가설:</strong> cand03 (AICKNFFWKTFTSC)은 SSTR2에 대해 SST-14 대비 향상된 선택성을 보이며,
                  in-vitro Ki(SSTR2) &lt; 10 nM 이고 log(Ki(SSTR1)/Ki(SSTR2)) &gt; 1.0 이다.
                </Hyp>
                <Hyp tag="H0" tone="mute">
                  <strong>귀무 가설:</strong> cand03의 5개 SSTR Ki 프로파일이 SST-14와 통계적으로 유의미한 차이가 없다 (ANOVA p &gt; 0.05).
                </Hyp>
              </div>
            </div>

            {/* in-silico predictions */}
            <div className="bio-panel">
              <div className="bio-panel-hd">
                <span>2 · in-silico 예측 · Boltz-2 + ADMET</span>
                <span className="mono" style={{ fontSize: 10 }}>2026-05-12</span>
              </div>
              <table className="bio-table">
                <thead>
                  <tr>
                    <th style={{ width: 80 }}>Receptor</th>
                    <th style={{ width: 80, textAlign: "right" }}>iPTM</th>
                    <th style={{ textAlign: "right" }}>SST-14 Ki (lit.)</th>
                    <th style={{ textAlign: "right" }}>cand03 Ki 예측</th>
                    <th>예측 근거</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { r: "SSTR1", iptm: 0.900, wt: "0.4 nM", pred: "≥ 5 nM",     note: "iPTM ↓ 0.075, off-target 신호 약화" },
                    { r: "SSTR2", iptm: 0.952, wt: "0.2 nM", pred: "0.5–5 nM",  note: "Best receptor · ★ 목표", target: true },
                    { r: "SSTR3", iptm: 0.838, wt: "0.8 nM", pred: "≥ 10 nM",    note: "iPTM ↓ 0.12, 가장 큰 회피" },
                    { r: "SSTR4", iptm: 0.944, wt: "1.6 nM", pred: "≥ 5 nM",     note: "iPTM 유지, 약한 cross-reactivity" },
                    { r: "SSTR5", iptm: 0.818, wt: "0.3 nM", pred: "≥ 10 nM",    note: "iPTM ↓ 0.10, off-target 약화" },
                  ].map(row => (
                    <tr key={row.r} style={{ background: row.target ? "var(--accent-soft)" : "transparent" }}>
                      <td>
                        <span className="mono" style={{ fontWeight: row.target ? 700 : 500, color: row.target ? "var(--accent-text)" : "var(--text)" }}>
                          {row.target && "★ "}{row.r}
                        </span>
                      </td>
                      <td className="mono" style={{ textAlign: "right", fontWeight: row.target ? 700 : 500 }}>{row.iptm.toFixed(3)}</td>
                      <td className="mono" style={{ textAlign: "right", color: "var(--text-mute)" }}>{row.wt}</td>
                      <td className="mono" style={{ textAlign: "right", fontWeight: 600, color: row.target ? "var(--pos)" : "var(--text)" }}>{row.pred}</td>
                      <td style={{ fontSize: 11, color: "var(--text-mute)" }}>{row.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{
                padding: "8px 16px", borderTop: "1px solid var(--border)",
                fontSize: 11, color: "var(--text-mute)", display: "flex", alignItems: "center", gap: 8,
              }}>
                <span className="bio-pill warn" style={{ padding: "1px 6px", fontSize: 9.5 }}>⚠ HEURISTIC</span>
                iPTM ≠ Ki — radioligand assay로 cross-validation 필수 (R7).
              </div>
            </div>

            {/* Reagent procurement */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>3 · 합성 · 시약 · procurement</span><span className="mono" style={{ fontSize: 10 }}>Peptron / Bachem</span></div>
              <table className="bio-table">
                <thead>
                  <tr>
                    <th>품목</th>
                    <th>스펙</th>
                    <th>공급</th>
                    <th style={{ textAlign: "right" }}>단가</th>
                    <th style={{ textAlign: "right" }}>수량</th>
                    <th style={{ textAlign: "right" }}>합계</th>
                    <th>리드</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span className="mono" style={{ fontWeight: 600 }}>cand03</span>
                        <span className="bio-pill accent" style={{ padding: "0 4px", fontSize: 9.5 }}>★</span>
                      </div>
                      <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)" }}>AICKNFFWKTFTSC</div>
                    </td>
                    <td style={{ fontSize: 11 }}>14aa · Cys SS bond · ≥95% (HPLC) · 5 mg</td>
                    <td className="mono" style={{ fontSize: 11 }}>Peptron</td>
                    <td className="mono" style={{ textAlign: "right" }}>₩2,500,000</td>
                    <td className="mono" style={{ textAlign: "right" }}>1 lot</td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>₩2,500,000</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>10–14d</td>
                  </tr>
                  <tr>
                    <td>
                      <span className="mono" style={{ fontWeight: 600 }}>Scrambled cand03</span>
                      <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)" }}>ATKCNIFTFWKSC (Cys 고정)</div>
                    </td>
                    <td style={{ fontSize: 11 }}>음성대조 · 동일 조성 · 2 mg</td>
                    <td className="mono" style={{ fontSize: 11 }}>Peptron</td>
                    <td className="mono" style={{ textAlign: "right" }}>₩1,200,000</td>
                    <td className="mono" style={{ textAlign: "right" }}>1 lot</td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>₩1,200,000</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>10d</td>
                  </tr>
                  <tr>
                    <td>
                      <span className="mono" style={{ fontWeight: 600 }}>var12 (D-Thr12)</span>
                      <div className="mono" style={{ fontSize: 10, color: "var(--text-dim)" }}>AICKNFFWKTF[dT]SC</div>
                    </td>
                    <td style={{ fontSize: 11 }}>stability 보강 · 3 mg</td>
                    <td className="mono" style={{ fontSize: 11 }}>Peptron</td>
                    <td className="mono" style={{ textAlign: "right" }}>₩1,200,000</td>
                    <td className="mono" style={{ textAlign: "right" }}>1 lot</td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>₩1,200,000</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>14d</td>
                  </tr>
                  <tr>
                    <td>¹²⁵I-Tyr¹¹ SS-14 (방사성)</td>
                    <td style={{ fontSize: 11 }}>radioligand · 0.5 mCi</td>
                    <td className="mono" style={{ fontSize: 11 }}>Perkin-Elmer</td>
                    <td className="mono" style={{ textAlign: "right" }}>₩4,500,000</td>
                    <td className="mono" style={{ textAlign: "right" }}>1</td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>₩4,500,000</td>
                    <td className="mono" style={{ fontSize: 10.5, color: "var(--warn)" }}>7–10d ⚠</td>
                  </tr>
                  <tr>
                    <td>SSTR1–5 세포주 (CHO/HEK)</td>
                    <td style={{ fontSize: 11 }}>stable transfected · 5 strain</td>
                    <td className="mono" style={{ fontSize: 11 }}>ATCC</td>
                    <td className="mono" style={{ textAlign: "right" }}>₩800,000</td>
                    <td className="mono" style={{ textAlign: "right" }}>5</td>
                    <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>₩4,000,000</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>5d</td>
                  </tr>
                  <tr style={{ background: "var(--bg-sunk)", fontWeight: 600 }}>
                    <td colSpan={5} style={{ textAlign: "right" }}>합계</td>
                    <td className="mono" style={{ textAlign: "right", fontSize: 13, color: "var(--accent-text)" }}>₩13,400,000</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>~3 wk</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Assay design — protocol pulldown */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>4 · Assay protocol · radioligand competition</span></div>
              <div style={{ padding: "12px 16px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                <Protocol label="포맷" v="96-well competition binding" />
                <Protocol label="Tracer" v="¹²⁵I-Tyr¹¹ SS-14 · 0.05 nM final" />
                <Protocol label="Membrane" v="SSTR1–5 stable cell, 2 µg/well" />
                <Protocol label="Concentration range" v="10⁻¹² – 10⁻⁵ M · 11-point" />
                <Protocol label="Replicates" v="n = 3 (technical) × 3 (biological)" />
                <Protocol label="Negative control" v="Scrambled cand03 @ 1 µM" />
                <Protocol label="Read-out" v="γ-counter, 1 min/well, %특이결합" />
                <Protocol label="Analysis" v="GraphPad Prism · log Ki + Welch t-test" />
              </div>
            </div>
          </div>

          {/* RIGHT — Sticky summary */}
          <aside style={{ display: "flex", flexDirection: "column", gap: 14, position: "sticky", top: 0, alignSelf: "flex-start" }}>
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Summary</span></div>
              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
                <SummaryItem label="후보" v={<span className="mono" style={{ fontWeight: 600 }}>cand03 · AICKNFFWKTFTSC</span>} />
                <SummaryItem label="치환" v={<span className="mono">G2 → I (single)</span>} />
                <SummaryItem label="총 비용" v={<span className="mono" style={{ fontWeight: 700, color: "var(--accent-text)" }}>₩13.4M</span>} />
                <SummaryItem label="타임라인" v={<span className="mono">8주 (PO → 결과)</span>} />
                <SummaryItem label="요청자" v="dongjukim@kaeri.re.kr" />
                <SummaryItem label="승인 필요" v={<span className="bio-pill warn" style={{ padding: "0 5px", fontSize: 9.5 }}>PI 검토 대기</span>} />
              </div>
            </div>

            {/* Acceptance criteria */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>합격 기준 · acceptance</span></div>
              <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 6, fontSize: 11.5, lineHeight: 1.4 }}>
                <Crit ok>cand03 Ki(SSTR2) &lt; 10 nM</Crit>
                <Crit ok>log SI(SSTR1/SSTR2) &gt; 1.0</Crit>
                <Crit>tracer Kd 일치 within 2×</Crit>
                <Crit>scrambled 억제율 &lt; 10% @ 1 µM</Crit>
                <Crit>CV (replicate) &lt; 20%</Crit>
              </div>
            </div>

            {/* Timeline */}
            <div className="bio-panel">
              <div className="bio-panel-hd"><span>Timeline · 8주</span></div>
              <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 5 }}>
                {[
                  { w: "1주", task: "PO 발주 · 시약 입하 추적", actor: "연구원" },
                  { w: "2–3주", task: "cand03 + scrambled + var12 합성", actor: "Peptron" },
                  { w: "3주", task: "QC · HPLC · MS · Ellman SS bond", actor: "화학팀" },
                  { w: "4주", task: "SSTR1–5 세포 배양 · membrane 추출", actor: "biology" },
                  { w: "5–6주", task: "Pilot Kd binding (n=1)", actor: "biology" },
                  { w: "6–7주", task: "Full competition (n=3 × 3 biol)", actor: "biology" },
                  { w: "8주", task: "Ki 계산 · 통계 · 보고서", actor: "data" },
                ].map(r => (
                  <div key={r.w} style={{ display: "grid", gridTemplateColumns: "50px 1fr 70px", gap: 6, fontSize: 11, padding: "3px 0", borderBottom: "1px dashed var(--border)" }}>
                    <span className="mono" style={{ color: "var(--text-mute)" }}>{r.w}</span>
                    <span>{r.task}</span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--text-dim)" }}>{r.actor}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: 6 }}>
              <button className="bio-btn ghost" style={{ flex: 1 }}>defer</button>
              <button className="bio-btn" style={{ flex: 1 }}>edit</button>
              <button className="bio-btn primary" style={{ flex: 2 }}>PI 승인 요청 →</button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function Hyp({ tag, tone, children }) {
  const color = tone === "pos" ? "var(--pos)" : "var(--text-mute)";
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "40px 1fr",
      gap: 12, padding: "8px 10px",
      background: tone === "pos" ? "var(--pos-soft)" : "var(--bg-sunk)",
      border: "1px solid var(--border)", borderRadius: 3,
      borderLeft: `3px solid ${color}`,
      fontSize: 11.5, lineHeight: 1.5,
    }}>
      <span className="mono" style={{ fontWeight: 700, color }}>{tag}</span>
      <span>{children}</span>
    </div>
  );
}

function Protocol({ label, v }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2, padding: "5px 0", borderBottom: "1px dashed var(--border)" }}>
      <span className="bio-label">{label}</span>
      <span className="mono" style={{ fontSize: 11.5 }}>{v}</span>
    </div>
  );
}

function SummaryItem({ label, v }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", paddingBottom: 4, borderBottom: "1px dashed var(--border)", fontSize: 11.5 }}>
      <span style={{ color: "var(--text-mute)" }}>{label}</span>
      <span>{v}</span>
    </div>
  );
}

function Crit({ ok, children }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
      <span style={{
        width: 14, height: 14, borderRadius: 3,
        border: ok ? "1.5px solid var(--pos)" : "1.5px solid var(--border-strong)",
        background: ok ? "var(--pos-soft)" : "transparent",
        display: "grid", placeItems: "center", flexShrink: 0,
      }}>
        {ok && <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--pos)" strokeWidth="4"><path d="M5 13l4 4L19 7"/></svg>}
      </span>
      <span>{children}</span>
    </div>
  );
}

window.ScreenWetlab = ScreenWetlab;
