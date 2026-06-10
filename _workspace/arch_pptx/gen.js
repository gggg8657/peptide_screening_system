// SSTR2 무한 발굴 Agentic AI 시스템 아키텍처 — pptxgenjs
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

// ---------- palette (scientific deep-blue / teal / mint) ----------
const C = {
  navy:  "0B1F3A",   // dark bg
  deep:  "0D3B66",   // primary
  teal:  "1C7293",
  mint:  "02C39A",   // accent (success / selectivity)
  amber: "F4A259",   // sharp accent (highlight)
  coral: "EF6F6C",   // warning / off-target
  light: "F4F7FB",   // content bg
  card:  "FFFFFF",
  ink:   "16263D",
  muted: "5A6B82",
  line:  "D6E0EC",
};
const FONT_H = "Georgia";
const FONT_B = "Calibri";

let pres = new pptxgen();
pres.defineLayout({ name: "W", width: 13.333, height: 7.5 });
pres.layout = "W";
pres.author = "SSTR2 Discovery";
pres.title = "SSTR2 무한 발굴 Agentic AI 아키텍처";
const W = 13.333, H = 7.5;

// ---------- icon helper ----------
async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

// ---------- reusable pieces ----------
function header(slide, kicker, title, opts = {}) {
  const dark = opts.dark;
  slide.addText(kicker, { x: 0.6, y: 0.34, w: 12, h: 0.32, fontFace: FONT_B, fontSize: 13, bold: true,
    color: dark ? C.mint : C.teal, charSpacing: 3, margin: 0 });
  slide.addText(title, { x: 0.6, y: 0.62, w: 12.1, h: 0.74, fontFace: FONT_H, fontSize: 30, bold: true,
    color: dark ? "FFFFFF" : C.ink, margin: 0 });
}

function card(slide, x, y, w, h, accent, fill) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill || C.card },
    line: { color: C.line, width: 1 }, shadow: { type: "outer", color: "0B1F3A", blur: 7, offset: 2, angle: 90, opacity: 0.10 } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.09, h, fill: { color: accent }, line: { type: "none" } });
}

function chip(slide, x, y, w, txt, color) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.34, fill: { color }, line: { type: "none" } });
  slide.addText(txt, { x, y, w, h: 0.34, align: "center", valign: "middle", fontFace: FONT_B, fontSize: 11.5, bold: true, color: "FFFFFF", margin: 0 });
}

(async () => {
  const ic = {};
  ic.dna     = await icon(FA.FaDna, "#" + C.mint);
  ic.robot   = await icon(FA.FaRobot, "#" + C.teal);
  ic.brain   = await icon(FA.FaBrain, "#" + C.deep);
  ic.flask   = await icon(FA.FaFlask, "#" + C.teal);
  ic.atom    = await icon(FA.FaAtom, "#" + C.deep);
  ic.target  = await icon(FA.FaBullseye, "#" + C.coral);
  ic.scale   = await icon(FA.FaBalanceScale, "#" + C.teal);
  ic.db      = await icon(FA.FaDatabase, "#" + C.deep);
  ic.infinity= await icon(FA.FaInfinity, "#" + C.mint);
  ic.sync    = await icon(FA.FaSyncAlt, "#" + C.teal);
  ic.shield  = await icon(FA.FaShieldAlt, "#" + C.mint);
  ic.filter  = await icon(FA.FaFilter, "#" + C.amber);
  ic.chart   = await icon(FA.FaChartLine, "#" + C.mint);
  ic.stop    = await icon(FA.FaStopCircle, "#" + C.coral);
  ic.gears   = await icon(FA.FaCogs, "#" + C.teal);
  ic.vial    = await icon(FA.FaVial, "#" + C.coral);
  ic.white_dna = await icon(FA.FaDna, "#FFFFFF");

  // ============ SLIDE 1 — TITLE ============
  let s = pres.addSlide();
  s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.16, fill: { color: C.mint }, line: { type: "none" } });
  // motif: nested helix circles (화면 안에 완전 포함)
  s.addShape(pres.shapes.OVAL, { x: 10.55, y: 0.62, w: 2.45, h: 2.45, fill: { color: C.deep, transparency: 35 }, line: { type: "none" } });
  s.addShape(pres.shapes.OVAL, { x: 10.95, y: 1.02, w: 1.65, h: 1.65, fill: { color: C.teal, transparency: 20 }, line: { type: "none" } });
  s.addImage({ data: ic.white_dna, x: 11.32, y: 1.39, w: 0.9, h: 0.9 });
  s.addText("AGENTIC AI · RADIOPHARMACEUTICAL DISCOVERY", { x: 0.7, y: 1.7, w: 9, h: 0.4,
    fontFace: FONT_B, fontSize: 14, bold: true, color: C.mint, charSpacing: 3, margin: 0 });
  s.addText("SSTR2 선택성 후보\n무한 발굴 Agentic AI 시스템", { x: 0.65, y: 2.15, w: 10, h: 1.9,
    fontFace: FONT_H, fontSize: 44, bold: true, color: "FFFFFF", lineSpacingMultiple: 1.02, margin: 0 });
  s.addText("SST-14 (AGCKNFFWKTFTSC · Cys3–Cys14 이황화 · FWKT 파마코포어) 변이체를 PyRosetta 실측 도킹 + LLM 에이전트 루프로 무한 탐색",
    { x: 0.7, y: 4.25, w: 11.3, h: 0.7, fontFace: FONT_B, fontSize: 15, color: "C7D6EA", margin: 0 });
  // bottom stat strip
  const tstats = [["목표", "SSTR2 선택성 ↑"], ["엔진", "PyRosetta + Qwen3-32B"], ["운영", "STOP 까지 무한 epoch"]];
  tstats.forEach((t, i) => {
    const x = 0.7 + i * 4.0;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 5.55, w: 3.7, h: 1.05, fill: { color: "11294A" }, line: { color: C.teal, width: 1 } });
    s.addText(t[0], { x: x + 0.25, y: 5.68, w: 3.2, h: 0.3, fontFace: FONT_B, fontSize: 11, bold: true, color: C.mint, charSpacing: 2, margin: 0 });
    s.addText(t[1], { x: x + 0.25, y: 5.98, w: 3.25, h: 0.5, fontFace: FONT_H, fontSize: 16, bold: true, color: "FFFFFF", margin: 0 });
  });

  // ============ SLIDE 2 — 개요 & 목표 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "OVERVIEW · 무엇을, 왜", "개요와 성공 기준");
  s.addText("천연 SST-14 는 SSTR1~5 에 고루 결합하는 pan-agonist 다. 본 시스템은 SST-14 를 변이시켜 SSTR2 에는 강하게, 나머지 아형(SSTR1/3/4/5)에는 약하게 결합하는 후보를 발굴한다.",
    { x: 0.6, y: 1.55, w: 7.1, h: 1.0, fontFace: FONT_B, fontSize: 14.5, color: C.ink, lineSpacingMultiple: 1.1, margin: 0 });
  // success criteria card (right)
  card(s, 8.0, 1.5, 4.7, 2.05, C.mint);
  s.addImage({ data: ic.target, x: 8.25, y: 1.7, w: 0.5, h: 0.5 });
  s.addText("성공 기준 (오늘 GOAL)", { x: 8.9, y: 1.72, w: 3.6, h: 0.45, fontFace: FONT_H, fontSize: 16, bold: true, color: C.ink, margin: 0 });
  s.addText([
    { text: "Δmargin > 0", options: { bold: true, color: C.deep, breakLine: true } },
    { text: "  (native SST-14 초과 선택성)", options: { fontSize: 11, color: C.muted, breakLine: true } },
    { text: "ΔG ≤ −15 kcal/mol", options: { bold: true, color: C.deep, breakLine: true } },
    { text: "  (강한 SSTR2 결합)", options: { fontSize: 11, color: C.muted, breakLine: true } },
    { text: "독성 ≤ native (hc50)", options: { bold: true, color: C.deep } },
  ], { x: 8.9, y: 2.2, w: 3.6, h: 1.25, fontFace: FONT_B, fontSize: 13.5, lineSpacingMultiple: 1.05, margin: 0 });

  // 4 pillar stats
  const pillars = [
    [ic.atom, "실측 ΔG", "PyRosetta\nFlexPepDock + InterfaceAnalyzer"],
    [ic.target, "선택성", "off-target 5종 도킹\nΔmargin (home-advantage 보정)"],
    [ic.chart, "혈중 반감기", "log-multiplicative + RF\n(PEPlife2, CV ρ=0.78) 앙상블"],
    [ic.shield, "ADMET·독성", "surrogate + pepADMET\nhc50 native 대비"],
  ];
  pillars.forEach((p, i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 3.95, 2.85, 2.75, C.teal);
    s.addImage({ data: p[0], x: x + 0.25, y: 4.2, w: 0.62, h: 0.62 });
    s.addText(p[1], { x: x + 0.22, y: 4.95, w: 2.5, h: 0.45, fontFace: FONT_H, fontSize: 18, bold: true, color: C.ink, margin: 0 });
    s.addText(p[2], { x: x + 0.22, y: 5.45, w: 2.55, h: 1.1, fontFace: FONT_B, fontSize: 12.5, color: C.muted, lineSpacingMultiple: 1.05, margin: 0 });
  });

  // ============ SLIDE 3 — 전체 아키텍처 / 데이터 흐름 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "SYSTEM ARCHITECTURE · 데이터 흐름", "전체 아키텍처 — 계층 + 흐름");
  const layers = [
    ["① 입력", "SSTR2–SST-14 복합체 PDB (Boltz) · 천연 서열 AGCKNFFWKTFTSC", C.deep],
    ["② LLM 레이어", "vLLM Qwen3-32B (port 8000) · Planner / Critic / Reporter", C.teal],
    ["③ Agentic 루프 (epoch)", "baseline → mutate&dock → scoring → in-loop 선택성 → QC/bandit/BO → critic → reporter", C.mint],
    ["④ 다목적 스코어링", "ΔG · 반감기 · Δmargin 선택성 · ADMET/hc50  →  NSGA-II Pareto + scalar", C.amber],
    ["⑤ 영속성 (run 간 기억)", "experiment_log.jsonl · global_selectivity_leaderboard.json · baseline_cache.json", C.deep],
    ["⑥ 오케스트레이터 / UI", "무한 epoch (STOP·control·다양성탈출) · FastAPI 8787 + React 5173 대시보드", C.teal],
  ];
  let yy = 1.55;
  layers.forEach((L, i) => {
    const h = 0.82;
    card(s, 0.6, yy, 10.9, h, L[2]);
    s.addText(L[0], { x: 0.85, y: yy, w: 3.0, h, valign: "middle", fontFace: FONT_H, fontSize: 16, bold: true, color: C.ink, margin: 0 });
    s.addText(L[1], { x: 3.95, y: yy, w: 7.45, h, valign: "middle", fontFace: FONT_B, fontSize: 12.5, color: C.muted, margin: 0 });
    if (i < layers.length - 1) {
      s.addShape(pres.shapes.RECTANGLE, { x: 5.95, y: yy + h - 0.005, w: 0.12, h: 0.135, fill: { color: C.muted }, line: { type: "none" } });
    }
    yy += h + 0.135;
  });
  // right rail: fail-closed + parallel
  card(s, 11.75, 1.55, 1.4, 5.55, C.coral, "0D3B66");
  s.addText("핵심 원칙", { x: 11.78, y: 1.72, w: 1.34, h: 0.4, align: "center", fontFace: FONT_H, fontSize: 13, bold: true, color: "FFFFFF", margin: 0 });
  s.addText([
    { text: "fail-closed", options: { bold: true, color: C.mint, breakLine: true } },
    { text: "실패 도킹→999/NaN, 랭킹 제외", options: { fontSize: 9.5, color: "C7D6EA", breakLine: true } },
    { text: "\n실측 우선", options: { bold: true, color: C.mint, breakLine: true } },
    { text: "가짜 점수 금지", options: { fontSize: 9.5, color: "C7D6EA", breakLine: true } },
    { text: "\n병렬화", options: { bold: true, color: C.mint, breakLine: true } },
    { text: "수용체 5종 동시 도킹", options: { fontSize: 9.5, color: "C7D6EA" } },
  ], { x: 11.85, y: 2.2, w: 1.22, h: 4.8, fontFace: FONT_B, fontSize: 10.5, lineSpacingMultiple: 1.0, align: "left", margin: 0 });

  // ============ SLIDE 4 — LLM 레이어 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "LLM LAYER · 추론 두뇌", "LLM 레이어 — vLLM Qwen3-32B");
  card(s, 0.6, 1.55, 12.1, 1.15, C.teal);
  s.addImage({ data: ic.robot, x: 0.85, y: 1.78, w: 0.7, h: 0.7 });
  s.addText([
    { text: "vLLM 서빙 — Qwen3-32B  ", options: { bold: true, fontSize: 17, color: C.ink } },
    { text: "@ localhost:8000 · H100(GPU2) · ~40 tok/s · enable_thinking=false (no-think, content만) · OpenAI 호환 API", options: { fontSize: 12.5, color: C.muted } },
  ], { x: 1.7, y: 1.62, w: 10.8, h: 1.0, valign: "middle", fontFace: FONT_B, lineSpacingMultiple: 1.1, margin: 0 });

  const agents = [
    [ic.brain, "Planner", C.deep, "변이 가설 + focus 위치 생성", ["SSTR2-고유 잔기(ECL2/ECL3/TM5/TM6) 상보 유도", "FWKT(7-10)·Cys3/14 보존 강제", "선택성 리더보드·Δmargin 표시 반영"]],
    [ic.scale, "Critic", C.teal, "결과 분석 → 파라미터 조정 ≤2", ["실패 분류: 구조/서열/도킹/안정성/선택성", "Δmargin≤0 = 캠페인 미성공 진단", "off-target 회피 변이 제안"]],
    [ic.flask, "Reporter", C.mint, "실험 노트 엔트리 생성", ["iteration 요약 · 핵심 지표", "top 후보 ID·점수·선택성", "QC 게이트 통과/실패 기록"]],
  ];
  agents.forEach((a, i) => {
    const x = 0.6 + i * 4.08;
    card(s, x, 3.0, 3.85, 3.75, a[2]);
    s.addImage({ data: a[0], x: x + 0.25, y: 3.25, w: 0.6, h: 0.6 });
    s.addText(a[1], { x: x + 0.95, y: 3.25, w: 2.7, h: 0.6, valign: "middle", fontFace: FONT_H, fontSize: 21, bold: true, color: C.ink, margin: 0 });
    s.addText(a[3], { x: x + 0.25, y: 3.95, w: 3.4, h: 0.5, fontFace: FONT_B, fontSize: 13, bold: true, color: a[2], margin: 0 });
    s.addText(a[4].map((t, j) => ({ text: t, options: { bullet: { code: "2022" }, breakLine: true, color: C.muted } })),
      { x: x + 0.3, y: 4.5, w: 3.4, h: 2.1, fontFace: FONT_B, fontSize: 12, lineSpacingMultiple: 1.12, margin: 0 });
  });

  // ============ SLIDE 5 — Agentic 루프 8단계 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "AGENTIC LOOP · epoch 1회", "epoch 당 Agentic 루프 — 8 단계");
  const steps = [
    ["1", "Baseline", "native SST-14 도킹(첫 epoch만, 이후 캐시 재사용)", C.deep],
    ["2", "Planner", "LLM 변이 가설·focus 위치 (선택성 인지)", C.teal],
    ["3", "Mutate → Dock", "PyRosetta FlexPepDock 병렬 · scaffold 가드", C.mint],
    ["4", "Scoring", "ΔG + 반감기 + ADMET/hc50 + GNINA + ECR", C.amber],
    ["5", "In-loop 선택성", "유망 후보만 off-target 도킹 → Δmargin", C.coral],
    ["6", "QC · Bandit · BO", "QCRanker + Thompson + 베이지안 + 수렴감지", C.teal],
    ["7", "Critic", "결과 분석 → 다음 iteration 파라미터 조정", C.deep],
    ["8", "Reporter", "실험 노트 + 글로벌 리더보드 영속", C.mint],
  ];
  steps.forEach((st, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = 0.6 + col * 3.08, y = 1.7 + row * 2.4;
    card(s, x, y, 2.88, 2.05, st[3]);
    s.addShape(pres.shapes.OVAL, { x: x + 0.22, y: y + 0.22, w: 0.62, h: 0.62, fill: { color: st[3] }, line: { type: "none" } });
    s.addText(st[0], { x: x + 0.22, y: y + 0.22, w: 0.62, h: 0.62, align: "center", valign: "middle", fontFace: FONT_H, fontSize: 22, bold: true, color: "FFFFFF", margin: 0 });
    s.addText(st[1], { x: x + 0.98, y: y + 0.26, w: 1.8, h: 0.6, valign: "middle", fontFace: FONT_H, fontSize: 15.5, bold: true, color: C.ink, margin: 0 });
    s.addText(st[2], { x: x + 0.24, y: y + 0.98, w: 2.55, h: 0.95, fontFace: FONT_B, fontSize: 12, color: C.muted, lineSpacingMultiple: 1.06, margin: 0 });
    // arrow between within-row
    if (col < 3) s.addText("→", { x: x + 2.84, y: y + 0.5, w: 0.3, h: 0.5, align: "center", valign: "middle", fontFace: FONT_B, fontSize: 22, bold: true, color: st[3], margin: 0 });
  });
  s.addText("수렴 시 종료가 아니라 다양성 주입으로 계속 — 무한 발굴의 핵심", { x: 0.6, y: 6.75, w: 12, h: 0.4,
    italic: true, fontFace: FONT_B, fontSize: 13, color: C.teal, margin: 0 });

  // ============ SLIDE 6 — PyRosetta 도킹 파이프라인 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "DOCKING ENGINE · PyRosetta", "PyRosetta 도킹 파이프라인");
  // on-target flow (left)
  card(s, 0.6, 1.55, 6.0, 2.5, C.deep);
  s.addImage({ data: ic.atom, x: 0.85, y: 1.78, w: 0.55, h: 0.55 });
  s.addText("On-target (SSTR2)", { x: 1.5, y: 1.8, w: 4.8, h: 0.5, valign: "middle", fontFace: FONT_H, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  s.addText([
    { text: "변이 적용 ", options: { bold: true, color: C.deep } }, { text: "(template_pdb 기준, Rosetta resfile)", options: { color: C.muted, breakLine: true } },
    { text: "FlexPepDock refine ", options: { bold: true, color: C.deep } }, { text: "(전원자 정밀화)", options: { color: C.muted, breakLine: true } },
    { text: "InterfaceAnalyzer ", options: { bold: true, color: C.deep } }, { text: "→ ΔG(실측) · clash · total", options: { color: C.muted } },
  ], { x: 0.9, y: 2.45, w: 5.5, h: 1.5, fontFace: FONT_B, fontSize: 13, lineSpacingMultiple: 1.35, margin: 0 });

  // scaffold guard (right top)
  card(s, 6.8, 1.55, 5.9, 2.5, C.mint);
  s.addImage({ data: ic.shield, x: 7.05, y: 1.78, w: 0.55, h: 0.55 });
  s.addText("Scaffold 가드 (변이 제약)", { x: 7.7, y: 1.8, w: 4.8, h: 0.5, valign: "middle", fontFace: FONT_H, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  s.addText([
    { text: "보존: ", options: { bold: true, color: C.mint } }, { text: "Cys3·Cys14 이황화 + FWKT(7-10) 파마코포어", options: { color: C.muted, breakLine: true } },
    { text: "변이 가능: ", options: { bold: true, color: C.mint } }, { text: "위치 1·2·4·5·6·11·12 만", options: { color: C.muted, breakLine: true } },
    { text: "거부: ", options: { bold: true, color: C.coral } }, { text: "이황화/파마코포어 파괴 변이 (자동 reject)", options: { color: C.muted } },
  ], { x: 7.1, y: 2.45, w: 5.4, h: 1.5, fontFace: FONT_B, fontSize: 13, lineSpacingMultiple: 1.35, margin: 0 });

  // off-target receptors (bottom)
  card(s, 0.6, 4.3, 12.1, 2.4, C.coral);
  s.addImage({ data: ic.vial, x: 0.85, y: 4.52, w: 0.55, h: 0.55 });
  s.addText("Off-target 선택성 도킹 (동일 프로토콜 · 병렬)", { x: 1.5, y: 4.54, w: 8, h: 0.5, valign: "middle", fontFace: FONT_H, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  s.addText("curated 단일사슬 수용체로 펩타이드 이식(transplant) → 서열정렬(BLOSUM62) → pre-relax(FastRelax) → FlexPepDock. on-target SSTR2 도 동일 프로토콜로 측정해야 margin 편향이 없다.",
    { x: 0.9, y: 5.05, w: 11.6, h: 0.7, fontFace: FONT_B, fontSize: 12.5, color: C.muted, lineSpacingMultiple: 1.05, margin: 0 });
  ["SSTR1", "SSTR3", "SSTR4", "SSTR5"].forEach((r, i) => chip(s, 0.9 + i * 1.55, 5.95, 1.4, r, C.deep));
  s.addText("selectivity_margin = min(off-target ΔG) − SSTR2 ΔG", { x: 7.4, y: 5.92, w: 5.1, h: 0.4, valign: "middle", fontFace: FONT_B, fontSize: 13, bold: true, color: C.ink, align: "right", margin: 0 });

  // ============ SLIDE 7 — 다목적 스코어링 + home-advantage ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "MULTI-OBJECTIVE SCORING", "다목적 스코어링 & home-advantage 보정");
  const objs = [
    [ic.atom, "ΔG (결합)", "PyRosetta 실측 · 강할수록 ↓", C.deep],
    [ic.chart, "혈중 반감기", "log-multiplicative + RF 앙상블", C.teal],
    [ic.target, "선택성 Δmargin", "off-target 회피 · native 대비", C.coral],
    [ic.shield, "ADMET / 독성", "surrogate + pepADMET hc50", C.mint],
  ];
  objs.forEach((o, i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 1.55, 2.85, 1.85, o[3]);
    s.addImage({ data: o[0], x: x + 0.22, y: 1.75, w: 0.5, h: 0.5 });
    s.addText(o[1], { x: x + 0.82, y: 1.74, w: 1.9, h: 0.52, valign: "middle", fontFace: FONT_H, fontSize: 15, bold: true, color: C.ink, margin: 0 });
    s.addText(o[2], { x: x + 0.24, y: 2.35, w: 2.5, h: 0.9, fontFace: FONT_B, fontSize: 12, color: C.muted, lineSpacingMultiple: 1.05, margin: 0 });
  });
  s.addText("→ NSGA-II Pareto + scalar 통합 랭킹", { x: 0.6, y: 3.55, w: 12, h: 0.4, fontFace: FONT_B, fontSize: 13, bold: true, color: C.teal, margin: 0 });

  // home-advantage explainer
  card(s, 0.6, 4.15, 5.9, 2.55, C.amber);
  s.addText("Δmargin — home-advantage 보정", { x: 0.85, y: 4.32, w: 5.4, h: 0.45, fontFace: FONT_H, fontSize: 16, bold: true, color: C.ink, margin: 0 });
  s.addText([
    { text: "curated SSTR2 는 source 복합체 유래 → native 자체가 margin ", options: { color: C.muted } },
    { text: "+13.37", options: { bold: true, color: C.deep } },
    { text: " (baseline).", options: { color: C.muted, breakLine: true } },
    { text: "Δmargin = margin − 13.37", options: { bold: true, color: C.deep, breakLine: true } },
    { text: "> 0 이어야 ", options: { color: C.muted } },
    { text: "native SST-14 를 진짜로 능가", options: { bold: true, color: C.coral } },
    { text: " 한 선택성.", options: { color: C.muted } },
  ], { x: 0.9, y: 4.85, w: 5.35, h: 1.7, fontFace: FONT_B, fontSize: 13.5, lineSpacingMultiple: 1.25, margin: 0 });

  // hc50 explainer
  card(s, 6.8, 4.15, 5.9, 2.55, C.mint);
  s.addText("독성 — hc50 native 대비", { x: 7.05, y: 4.32, w: 5.4, h: 0.45, fontFace: FONT_H, fontSize: 16, bold: true, color: C.ink, margin: 0 });
  s.addText([
    { text: "pepADMET binary(is_toxic)는 비변별적 — 옥시토신·native 까지 toxic 판정.", options: { color: C.muted, breakLine: true } },
    { text: "→ 연속값 hc50 을 native(−55.68) 대비로 게이트.", options: { bold: true, color: C.deep, breakLine: true } },
    { text: "native ±5 = 동급(무페널티), 초과 독성만 선형 감점.", options: { color: C.muted } },
  ], { x: 7.1, y: 4.85, w: 5.35, h: 1.7, fontFace: FONT_B, fontSize: 13.5, lineSpacingMultiple: 1.25, margin: 0 });

  // ============ SLIDE 8 — In-loop 선택성 게이트 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "IN-LOOP SELECTIVITY · 조건부 게이트", "In-loop 선택성 — 비용 제어 게이트");
  s.addText("선택성 도킹(후보×5수용체)은 비싸다. 매 iteration 전체 후보가 아니라, 기존 리더보드 최약체보다 ddG가 강한 유망 후보만(iter당 ≤2) 도킹한다. 선택성은 도킹 전엔 모르므로 ddG 를 유망도 프록시로 쓴다.",
    { x: 0.6, y: 1.5, w: 12.1, h: 0.95, fontFace: FONT_B, fontSize: 14, color: C.ink, lineSpacingMultiple: 1.12, margin: 0 });
  const gate = [
    ["변이 후보", "이번 iteration", C.deep],
    ["scaffold·clash 통과?", "이황화·FWKT 보존 + clash≤10", C.teal],
    ["ddG가 리더보드\n최약체보다 강한가?", "warm-start: 역대 도킹분 dedup", C.amber],
    ["off-target 5종\n병렬 도킹", "→ margin → Δmargin", C.coral],
    ["글로벌 리더보드\n갱신·영속", "다음 epoch warm-start", C.mint],
  ];
  gate.forEach((g, i) => {
    const x = 0.6 + i * 2.5;
    card(s, x, 2.75, 2.3, 2.3, g[2]);
    s.addText(g[0], { x: x + 0.2, y: 2.95, w: 2.0, h: 1.0, fontFace: FONT_H, fontSize: 14.5, bold: true, color: C.ink, lineSpacingMultiple: 1.0, margin: 0 });
    s.addText(g[1], { x: x + 0.2, y: 3.95, w: 2.0, h: 0.95, fontFace: FONT_B, fontSize: 11.5, color: C.muted, lineSpacingMultiple: 1.05, margin: 0 });
    if (i < gate.length - 1) s.addText("▸", { x: x + 2.26, y: 3.6, w: 0.28, h: 0.5, align: "center", valign: "middle", fontFace: FONT_B, fontSize: 20, bold: true, color: g[2], margin: 0 });
  });
  // cost note
  card(s, 0.6, 5.4, 12.1, 1.25, C.teal);
  s.addImage({ data: ic.filter, x: 0.85, y: 5.62, w: 0.55, h: 0.55 });
  s.addText([
    { text: "비용 효과: ", options: { bold: true, color: C.ink, fontSize: 14 } },
    { text: "전체 8후보×5수용체 순차(~수 시간) → 유망 ≤2후보×5수용체 병렬(~6–12분/iter). 게이트 + 수용체 병렬화로 in-loop 선택성을 실용화.", options: { color: C.muted, fontSize: 13 } },
  ], { x: 1.6, y: 5.55, w: 10.9, h: 1.0, valign: "middle", fontFace: FONT_B, lineSpacingMultiple: 1.1, margin: 0 });

  // ============ SLIDE 9 — 영속성 3종 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "PERSISTENCE · run 간 기억", "영속성 3종 — 무한 발굴의 기억");
  const stores = [
    [ic.db, "experiment_log.jsonl", C.deep, "모든 run의 모든 후보 누적", ["서열 cross-run dedup (재생성 회피)", "Thompson bandit 위치 warm-start", "기존 백본 — 결합 탐색 기억"]],
    [ic.target, "global_selectivity_\nleaderboard.json", C.coral, "Δmargin 역대 best (신규)", ["선택성 측정 서열 dedup", "in-loop 게이트 warm-start", "post-loop margin→Δ backfill", "count_passing(엄격 기준)"]],
    [ic.atom, "baseline_cache.json", C.mint, "native baseline 1회 측정", ["첫 epoch만 native SST-14 도킹", "이후 epoch 재사용(재도킹 생략)", "template+서열 일치 시만 (안전)"]],
  ];
  stores.forEach((st, i) => {
    const x = 0.6 + i * 4.08;
    card(s, x, 1.6, 3.85, 5.05, st[2]);
    s.addImage({ data: st[0], x: x + 0.25, y: 1.85, w: 0.6, h: 0.6 });
    s.addText(st[1], { x: x + 0.25, y: 2.55, w: 3.4, h: 0.8, fontFace: FONT_H, fontSize: 16.5, bold: true, color: C.ink, lineSpacingMultiple: 0.95, margin: 0 });
    s.addText(st[3], { x: x + 0.25, y: 3.35, w: 3.4, h: 0.45, fontFace: FONT_B, fontSize: 13, bold: true, color: st[2], margin: 0 });
    s.addText(st[4].map(t => ({ text: t, options: { bullet: { code: "2022" }, breakLine: true, color: C.muted } })),
      { x: x + 0.3, y: 3.9, w: 3.4, h: 2.6, fontFace: FONT_B, fontSize: 12.5, lineSpacingMultiple: 1.18, margin: 0 });
  });

  // ============ SLIDE 10 — 무한 오케스트레이터 ============
  s = pres.addSlide(); s.background = { color: C.light };
  header(s, "CONTINUOUS ENGINE · 무한 운영", "무한 발굴 오케스트레이터");
  // central loop
  card(s, 0.6, 1.6, 7.5, 5.05, C.teal);
  s.addImage({ data: ic.sync, x: 0.85, y: 1.82, w: 0.55, h: 0.55 });
  s.addText("epoch 루프 (STOP 파일까지)", { x: 1.5, y: 1.84, w: 6.4, h: 0.5, valign: "middle", fontFace: FONT_H, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  const loop = [
    "control 파일 재로드 → knobs 반영 (라이브 조절)",
    "글로벌 리더보드 warm-start (dedup + 게이트 기준선)",
    "seed_base = base + epoch×1000 (탐색 영역 이동)",
    "다양성 정책: best Δ 정체(patience) → 변이수↑ (탈출)",
    "run_pyrosetta_flow 1회 (in-loop 선택성 ON)",
    "측정 → 글로벌 리더보드 누적·영속",
    "status 파일 갱신 → 다음 epoch",
  ];
  s.addText(loop.map((t, j) => ({ text: t, options: { bullet: { type: "number" }, breakLine: true, color: C.ink } })),
    { x: 1.0, y: 2.55, w: 6.9, h: 3.9, fontFace: FONT_B, fontSize: 14, lineSpacingMultiple: 1.45, margin: 0 });

  // control panel (right)
  const ctrl = [
    [ic.stop, "정지", C.coral, "touch _workspace/STOP_DISCOVERY — 현재 epoch 마치고 graceful 종료"],
    [ic.gears, "조절", C.amber, "discovery_control.json 편집 — 다음 epoch 부터 반영(재시작 불필요)"],
    [ic.infinity, "다양성 탈출", C.mint, "best Δ 정체 시 max_random_mutations↑ → local optimum 탈출"],
    [ic.chart, "모니터", C.deep, "discovery_status.json — 역대 best Δ·통과 수·다양성 레벨"],
  ];
  ctrl.forEach((c, i) => {
    const y = 1.6 + i * 1.29;
    card(s, 8.3, y, 4.4, 1.12, c[2]);
    s.addImage({ data: c[0], x: 8.5, y: y + 0.28, w: 0.55, h: 0.55 });
    s.addText(c[1], { x: 9.15, y: y + 0.12, w: 3.4, h: 0.4, fontFace: FONT_H, fontSize: 15, bold: true, color: C.ink, margin: 0 });
    s.addText(c[3], { x: 9.15, y: y + 0.5, w: 3.45, h: 0.58, fontFace: FONT_B, fontSize: 10.8, color: C.muted, lineSpacingMultiple: 0.98, margin: 0 });
  });

  // ============ SLIDE 11 — 현황 & 사용법 ============
  s = pres.addSlide(); s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.16, fill: { color: C.mint }, line: { type: "none" } });
  header(s, "STATUS & USAGE", "현황 · 가동 방법", { dark: true });
  // stat callouts
  const sc = [["+0.077", "역대 best Δmargin\n(LGCKFFFWKTFMSC)"], ["0건", "엄격 기준 동시충족\n(Δ>0 & ΔG≤−15 & 비독성)"], ["∞", "epoch (STOP 까지)\n하룻밤 ~10–15"]];
  sc.forEach((t, i) => {
    const x = 0.7 + i * 4.0;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.7, w: 3.7, h: 1.85, fill: { color: "11294A" }, line: { color: C.teal, width: 1 } });
    s.addText(t[0], { x: x + 0.2, y: 1.88, w: 3.3, h: 0.95, fontFace: FONT_H, fontSize: 46, bold: true, color: C.mint, margin: 0 });
    s.addText(t[1], { x: x + 0.22, y: 2.85, w: 3.35, h: 0.6, fontFace: FONT_B, fontSize: 12, color: "C7D6EA", lineSpacingMultiple: 1.0, margin: 0 });
  });
  // run command
  s.addText("백그라운드 가동 (tmux 권장)", { x: 0.7, y: 3.95, w: 12, h: 0.4, fontFace: FONT_H, fontSize: 16, bold: true, color: "FFFFFF", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.4, w: 11.93, h: 1.95, fill: { color: "071528" }, line: { color: C.teal, width: 1 } });
  s.addText([
    { text: "$ tmux new -s discovery", options: { color: C.mint, breakLine: true } },
    { text: "$ ~/miniforge3/envs/bio-tools/bin/python scripts/run_continuous_discovery.py \\", options: { color: "E6EEF8", breakLine: true } },
    { text: "    --input data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb \\", options: { color: "E6EEF8", breakLine: true } },
    { text: "    --n-candidates 8 --max-iterations 4 --top-k 5 --selectivity-max-per-iter 2", options: { color: "E6EEF8", breakLine: true } },
    { text: "# 정지: touch _workspace/STOP_DISCOVERY   |   모니터: discovery_status.json", options: { color: C.amber } },
  ], { x: 0.95, y: 4.55, w: 11.5, h: 1.7, fontFace: "Consolas", fontSize: 12.5, lineSpacingMultiple: 1.22, margin: 0 });
  s.addText("전제: vLLM(Qwen3-32B) @ localhost:8000 가동 중", { x: 0.7, y: 6.5, w: 12, h: 0.4, italic: true, fontFace: FONT_B, fontSize: 13, color: "C7D6EA", margin: 0 });

  await pres.writeFile({ fileName: "/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/_workspace/SSTR2_Architecture.pptx" });
  console.log("WROTE SSTR2_Architecture.pptx (" + pres.slides.length + " slides)");
})();
