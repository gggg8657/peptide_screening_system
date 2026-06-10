// PRST_N_FM 2026-05-19 SOD 종합 발표 자료
// 16 슬라이드 — Action Items 9건 + Phase 1/2 + PRST-001~004 + Gate-2

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.author = "PRST_N_FM Team";
pres.title = "PRST_N_FM SOD 2026-05-19 — Action Items 종합 + Gate-2 진입";

// Teal Trust 팔레트 (drug discovery 적합)
const C = {
  primary: "028090", // teal
  secondary: "00A896", // seafoam
  accent: "02C39A", // mint
  dark: "1E293B", // slate-900
  light: "F8FAFC", // slate-50
  bg: "FFFFFF",
  text: "0F172A", // slate-950
  textMute: "475569", // slate-600
  textDim: "94A3B8", // slate-400
  border: "E2E8F0", // slate-200
  warn: "F59E0B", // amber
  neg: "DC2626", // red
  pos: "16A34A", // green
};

const FONT_H = "Cambria";
const FONT_B = "Calibri";

// ───────────────────────────────────────────────
// 헬퍼
// ───────────────────────────────────────────────
function addFooter(slide, pageNum, totalPages) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 7.25, w: 13.3, h: 0.25, fill: { color: C.primary }, line: { type: "none" },
  });
  slide.addText("PRST_N_FM · SSTR2 AI Co-Scientist · 2026-05-19", {
    x: 0.4, y: 7.25, w: 8, h: 0.25, fontSize: 9, color: "FFFFFF", fontFace: FONT_B, valign: "middle",
  });
  slide.addText(`${pageNum} / ${totalPages}`, {
    x: 12.5, y: 7.25, w: 0.6, h: 0.25, fontSize: 9, color: "FFFFFF", fontFace: FONT_B, valign: "middle", align: "right",
  });
}

function addTitle(slide, title, subtitle) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.15, h: 7.25, fill: { color: C.primary }, line: { type: "none" } });
  slide.addText(title, {
    x: 0.5, y: 0.3, w: 12.5, h: 0.7, fontSize: 28, bold: true, color: C.dark, fontFace: FONT_H, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.95, w: 12.5, h: 0.4, fontSize: 14, color: C.textMute, fontFace: FONT_B, margin: 0, italic: true,
    });
  }
}

const TOTAL = 16;

// ───────────────────────────────────────────────
// Slide 1 — 타이틀
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  // 큰 강조 도형
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.2, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });

  s.addText("PRST_N_FM", {
    x: 0.5, y: 1.5, w: 12.3, h: 0.9, fontSize: 14, color: C.accent, bold: true, fontFace: FONT_B, charSpacing: 8,
  });
  s.addText("Action Items 종합 보고", {
    x: 0.5, y: 2.0, w: 12.3, h: 1.2, fontSize: 56, color: "FFFFFF", bold: true, fontFace: FONT_H,
  });
  s.addText("Gate-2 진입 준비 완료", {
    x: 0.5, y: 3.2, w: 12.3, h: 0.7, fontSize: 28, color: C.accent, italic: true, fontFace: FONT_H,
  });

  // 좌측 누적 메트릭
  s.addText("24", { x: 0.5, y: 4.5, w: 1.5, h: 1.0, fontSize: 72, bold: true, color: "FFFFFF", fontFace: FONT_H, align: "center" });
  s.addText("PR 머지", { x: 0.5, y: 5.5, w: 1.5, h: 0.3, fontSize: 12, color: C.accent, fontFace: FONT_B, align: "center" });

  s.addText("10/10", { x: 2.2, y: 4.5, w: 1.5, h: 1.0, fontSize: 72, bold: true, color: "FFFFFF", fontFace: FONT_H, align: "center" });
  s.addText("Action Items 완료", { x: 2.2, y: 5.5, w: 1.5, h: 0.3, fontSize: 12, color: C.accent, fontFace: FONT_B, align: "center" });

  s.addText("4", { x: 3.9, y: 4.5, w: 1.5, h: 1.0, fontSize: 72, bold: true, color: "FFFFFF", fontFace: FONT_H, align: "center" });
  s.addText("최종 후보 (PRST-001~004)", { x: 3.9, y: 5.5, w: 1.7, h: 0.3, fontSize: 11, color: C.accent, fontFace: FONT_B, align: "center" });

  // 우측 타이틀 메타
  s.addText("2026-05-19", { x: 9.5, y: 4.5, w: 3.3, h: 0.5, fontSize: 18, color: "FFFFFF", fontFace: FONT_B, align: "right" });
  s.addText("orchestrator session · ~10h", { x: 9.5, y: 5.0, w: 3.3, h: 0.3, fontSize: 11, color: C.accent, fontFace: FONT_B, align: "right" });
}

// ───────────────────────────────────────────────
// Slide 2 — 핵심 요약 (Executive)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Executive Summary", "2026-05-19 단일 세션 — Phase 1/2 + Action Items 9건 + BLOSUM 5 Phase 완성");

  // 4 stat cards
  const stats = [
    { num: "24", label: "PR 머지 누적", sub: "본 세션 20 + 직접 4" },
    { num: "10/10", label: "Action Items 완료", sub: "4/6 회의 기준 (A-08 삭제 포함)" },
    { num: "5 Phase", label: "BLOSUM 재설계", sub: "default → dual_b1_b2 (drug-design)" },
    { num: "4", label: "최종 후보", sub: "PRST-001 Tier S + 002/003/004 Tier B" },
  ];
  stats.forEach((stat, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 3.0, h: 2.5, fill: { color: C.light }, line: { color: C.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 0.1, h: 2.5, fill: { color: C.primary }, line: { type: "none" } });
    s.addText(stat.num, { x: x + 0.3, y: 1.7, w: 2.7, h: 1.2, fontSize: 60, bold: true, color: C.primary, fontFace: FONT_H, valign: "middle" });
    s.addText(stat.label, { x: x + 0.3, y: 3.0, w: 2.7, h: 0.4, fontSize: 14, bold: true, color: C.dark, fontFace: FONT_B });
    s.addText(stat.sub, { x: x + 0.3, y: 3.4, w: 2.7, h: 0.6, fontSize: 10, color: C.textMute, fontFace: FONT_B });
  });

  // 핵심 발견 (하단)
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.3, w: 12.3, h: 2.5, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("핵심 결정 사항", { x: 0.8, y: 4.4, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });

  const decisions = [
    { label: "BLOSUM은 평가만", desc: "변이 생성은 dual_b1_b2 (ProteinMPNN ∪ ESM-Scan) — drug design 적합" },
    { label: "Manual Selectivity 풀스택", desc: "PyRosetta FlexPepDock 실 inference 활성화 — stub: false 확인" },
    { label: "DiffDock NOT_RECOMMENDED", desc: "SS bond 미지원 + 친화도 점수 없음 — Boltz+FlexPepDock 유지" },
    { label: "PRST-001 Tier S", desc: "AGCKNIIWKTITSC, WSS=1.000, ΔG=-105.5 REU, radiolysis_count=1" },
  ];
  decisions.forEach((d, i) => {
    const y = 4.85 + i * 0.45;
    s.addText("▸", { x: 0.8, y, w: 0.3, h: 0.4, fontSize: 14, color: C.accent, fontFace: FONT_B, valign: "middle" });
    s.addText(d.label, { x: 1.1, y, w: 3.5, h: 0.4, fontSize: 12, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
    s.addText(d.desc, { x: 4.7, y, w: 8.0, h: 0.4, fontSize: 11, color: C.textDim, fontFace: FONT_B, valign: "middle" });
  });
  addFooter(s, 2, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 3 — Action Items 9건 진행표
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Action Items 9건 — 모두 완료", "4/6 회의 기반 (A-08은 회의 당일 삭제)");

  const rows = [
    [{ text: "ID", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "주제", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "위임", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "PR / 커밋", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "결과", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["A-01", "SSTR site-directed docking", "engineer-backend", "#61", "RMSD 2.77-3.13Å (5종 정렬)"],
    ["A-02", "혈청 반감기 도구 7종 비교", "researcher", "보고서", "D-AA HIGH-BLOCKER 확정"],
    ["A-03", "pepADMET 정확도 검증", "researcher", "보고서", "\"Fab-ADMET\" 오기재 확정"],
    ["A-04", "복합 스코어링 (Tier S/A/B/FAIL)", "engineer-backend", "#62", "WSS+Pareto, 73 tests pass"],
    ["A-05", "SST14 reference dG (n=10)", "engineer-backend", "8e7e1cc", "mean 553.857 REU, σ=4.024"],
    ["A-06", "DiffDock PoC", "engineer-backend", "6054ea9", "NOT_RECOMMENDED (SS bond X)"],
    ["A-07", "GPU 견적 + 점검", "engineer-infra", "보고서", "CUDA 2,3 = 192GB 활용 중"],
    ["A-08", "(삭제됨)", "researcher", "—", "회의 당일 삭제 (H100×8 배포)"],
    ["A-09", "최종 후보 + 합성 의뢰서", "reviewer-pharma", "#63", "PRST-001~004 (Tier S/B/B/B)"],
    ["A-10", "SSTR3_8XIR docking fix", "codex", "#60", "chain 선택 + 24 tests, smoke OK"],
  ];

  s.addTable(rows, {
    x: 0.5, y: 1.55, w: 12.3,
    colW: [0.8, 4.0, 2.0, 1.5, 4.0],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.42,
    valign: "middle",
  });
  addFooter(s, 3, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 4 — Manual Selectivity 풀스택
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Manual Selectivity 풀스택", "어제 5/15 시작 → 오늘 PR #41-#49 통해 BE+FE+PyRosetta 완성");

  // 좌측: 아키텍처
  s.addText("아키텍처", { x: 0.5, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  const arch = [
    { layer: "FE", desc: "/manual-selectivity 페이지\nArchivesTopKSlider + HeuristicBanner + SSTR1-5 체크박스" },
    { layer: "BE", desc: "POST /api/flexpepdock/jobs\n큐 + worker + ETA 학습 + 동시 1개 lock" },
    { layer: "Worker", desc: "PyRosetta FlexPepDocking + InterfaceAnalyzer\n실 inference (stub: false 확인)" },
    { layer: "Output", desc: "selectivity_matrix per SSTR1-5\nwetlab order 직접 생성 (cand03 제한 해제)" },
  ];
  arch.forEach((a, i) => {
    const y = 2.0 + i * 0.9;
    s.addShape(pres.shapes.OVAL, { x: 0.5, y, w: 0.5, h: 0.5, fill: { color: C.primary }, line: { type: "none" } });
    s.addText(a.layer, { x: 0.5, y, w: 0.5, h: 0.5, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_B });
    s.addText(a.desc, { x: 1.2, y, w: 5.0, h: 0.8, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "top" });
  });

  // 우측: 핵심 PR 카드
  s.addText("핵심 PR (오늘 5/19까지 8건)", { x: 7.0, y: 1.5, w: 5.8, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  const prs = [
    { id: "#41", t: "FlexPepDock BE 큐+워커+ETA", d: "60/60 tests" },
    { id: "#43", t: "ManualSelectivityPage FE", d: "wetlab 통합" },
    { id: "#49", t: "flexpep_dock.py wrapper", d: "stub: false 활성화" },
    { id: "#53", t: "wetlab cand03 제한 해제", d: "Manual Selectivity 통합" },
  ];
  prs.forEach((p, i) => {
    const y = 2.0 + i * 0.9;
    s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y, w: 5.8, h: 0.7, fill: { color: C.light }, line: { color: C.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y, w: 0.08, h: 0.7, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(p.id, { x: 7.2, y, w: 1.0, h: 0.7, fontSize: 18, bold: true, color: C.primary, fontFace: FONT_H, valign: "middle" });
    s.addText(p.t, { x: 8.2, y, w: 3.5, h: 0.4, fontSize: 12, bold: true, color: C.dark, fontFace: FONT_B, valign: "middle" });
    s.addText(p.d, { x: 8.2, y: y + 0.35, w: 3.5, h: 0.3, fontSize: 10, color: C.textMute, fontFace: FONT_B, valign: "middle" });
  });
  addFooter(s, 4, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 5 — BLOSUM 5 Phase 완성
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "BLOSUM 변이 전략 재설계 — 5 Phase 완성", "PR #54-#59 — \"BLOSUM은 평가만\" 사용자 결정 적용");

  // 5 Phase 가로 흐름
  const phases = [
    { p: "Phase 1", t: "모듈화", d: "Strategy Protocol\n+ registry + blosum 이전", pr: "#54" },
    { p: "Phase 2", t: "ESM-Scan", d: "zero-shot scoring\nESM-2 LM", pr: "#55" },
    { p: "Phase 3", t: "ProteinMPNN", d: "structure-aware\npeptide-only fallback", pr: "#56" },
    { p: "Phase 4", t: "DualB1B2", d: "ProteinMPNN ∪ ESM-Scan\nUnion 정책", pr: "#57" },
    { p: "Phase 5", t: "A/B 실험", d: "4 strategy 비교\n+ default 결정", pr: "#58+#59" },
  ];
  phases.forEach((p, i) => {
    const x = 0.5 + i * 2.55;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 2.4, h: 2.6, fill: { color: C.light }, line: { color: C.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 2.4, h: 0.4, fill: { color: C.primary }, line: { type: "none" } });
    s.addText(p.p, { x, y: 1.5, w: 2.4, h: 0.4, fontSize: 12, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_B });
    s.addText(p.t, { x: x + 0.1, y: 2.05, w: 2.2, h: 0.5, fontSize: 18, bold: true, color: C.dark, align: "center", fontFace: FONT_H });
    s.addText(p.d, { x: x + 0.1, y: 2.7, w: 2.2, h: 0.9, fontSize: 10, color: C.textMute, align: "center", fontFace: FONT_B });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.6, y: 3.55, w: 1.2, h: 0.4, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(p.pr, { x: x + 0.6, y: 3.55, w: 1.2, h: 0.4, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_B });
    if (i < 4) {
      s.addShape(pres.shapes.RIGHT_TRIANGLE, { x: x + 2.45, y: 2.65, w: 0.1, h: 0.4, fill: { color: C.primary }, line: { type: "none" }, rotate: 90 });
    }
  });

  // 하단: 사용자 결정 인용
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.5, w: 12.3, h: 2.3, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("사용자 도메인 지적 (2026-05-19)", { x: 0.8, y: 4.6, w: 12.0, h: 0.4, fontSize: 12, color: C.accent, fontFace: FONT_B });
  s.addText("“보수 진화 탐색... 블로섬 기반으로 탐색 → 약품용 합성 펩타이드 탐색에 부적합 아님?”", {
    x: 0.8, y: 5.0, w: 12.0, h: 0.6, fontSize: 18, italic: true, color: "FFFFFF", fontFace: FONT_H,
  });
  s.addText("BLOSUM은 자연 진화 mutation 빈도 기반 — drug design 공간(D-AA, NMe, retro-inverso) 못 봄.", {
    x: 0.8, y: 5.7, w: 12.0, h: 0.4, fontSize: 12, color: C.textDim, fontFace: FONT_B,
  });
  s.addText("→ default = dual_b1_b2 (structure-aware ProteinMPNN ∪ sequence-context ESM-Scan)", {
    x: 0.8, y: 6.15, w: 12.0, h: 0.4, fontSize: 13, bold: true, color: C.accent, fontFace: FONT_B,
  });

  addFooter(s, 5, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 6 — 4 Strategy A/B 실험 결과 (chart)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "4 Strategy A/B 실험 — Hamming Distance + 다양성", "동일 seed AGCKNFFWKTFTSC, max_variants=50, fixed_positions 보존 100%");

  // BAR chart — hamming distance
  s.addChart(pres.charts.BAR, [{
    name: "Hamming distance from SST-14",
    labels: ["blosum", "esm_scan", "proteinmpnn", "dual_b1_b2"],
    values: [1.12, 2.00, 7.60, 7.32],
  }], {
    x: 0.5, y: 1.5, w: 6.5, h: 5.5, barDir: "col",
    chartColors: [C.warn, C.secondary, C.pos, C.primary],
    chartArea: { fill: { color: "FFFFFF" } },
    catAxisLabelColor: C.textMute,
    valAxisLabelColor: C.textMute,
    valGridLine: { color: C.border, size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.dark,
    dataLabelFontSize: 14,
    showLegend: false,
    showTitle: true,
    title: "변이 다양성 비교 (높을수록 drug-design 적합)",
    titleColor: C.dark,
    titleFontSize: 14,
  });

  // 우측: 메트릭 표
  s.addText("Strategy 별 메트릭", { x: 7.3, y: 1.5, w: 5.5, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  const rows = [
    [{ text: "Strategy", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "BLOSUM", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "Hamming", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "시간", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["blosum", "81.74", "1.12", "0.0s"],
    ["esm_scan", "78.04", "2.00", "5.2s"],
    ["proteinmpnn", "36.34", "7.60", "8.2s"],
    [{ text: "dual_b1_b2 ★", options: { bold: true, fill: { color: C.accent }, color: "FFFFFF" } },
     "38.30", "7.32", "12.1s"],
  ];
  s.addTable(rows, {
    x: 7.3, y: 2.0, w: 5.5, colW: [1.9, 1.2, 1.2, 1.2],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.4,
    valign: "middle",
    align: "center",
  });

  // 결정
  s.addShape(pres.shapes.RECTANGLE, { x: 7.3, y: 4.5, w: 5.5, h: 2.5, fill: { color: C.light }, line: { color: C.accent, width: 2 } });
  s.addText("운영 default 결정", { x: 7.5, y: 4.6, w: 5.1, h: 0.4, fontSize: 14, bold: true, color: C.primary, fontFace: FONT_B });
  s.addText("dual_b1_b2 ★", { x: 7.5, y: 5.05, w: 5.1, h: 0.6, fontSize: 28, bold: true, color: C.dark, fontFace: FONT_H });
  s.addText("structure-aware (ProteinMPNN) + sequence-context (ESM-Scan)\n→ 가장 광범위 drug-design 공간 탐색", {
    x: 7.5, y: 5.7, w: 5.1, h: 0.8, fontSize: 11, color: C.textMute, fontFace: FONT_B,
  });
  s.addText("적용: pipeline_config_local.yaml strategy 키 (PR #59)", { x: 7.5, y: 6.55, w: 5.1, h: 0.4, fontSize: 10, italic: true, color: C.textDim, fontFace: FONT_B });

  addFooter(s, 6, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 7 — UI 라이트 모드 가시성 fix
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "UI 라이트 모드 가시성 — ~1,300건 일괄 토큰화", "사용자 보고 → reviewer-uiux 분석 → mechanical fix");

  // 좌측: Before/After 비교
  s.addText("처리 규모", { x: 0.5, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  const items = [
    { cat: "slate-*", before: 431, after: 0, color: C.neg },
    { cat: "색조-300/400", before: 372, after: 0, color: C.neg },
    { cat: "inline hex", before: 17, after: 0, color: C.warn },
    { cat: "bg-black", before: 1, after: 0, color: C.warn },
    { cat: "text-white (의도)", before: 5, after: 5, color: C.pos },
  ];
  items.forEach((item, i) => {
    const y = 2.0 + i * 0.55;
    s.addText(item.cat, { x: 0.5, y, w: 2.5, h: 0.4, fontSize: 12, bold: true, color: C.dark, fontFace: FONT_B, valign: "middle" });
    s.addText(`${item.before} → ${item.after}`, {
      x: 3.0, y, w: 2.0, h: 0.4, fontSize: 14, bold: true, color: item.after === 0 ? C.pos : C.textMute, fontFace: FONT_H, align: "center", valign: "middle",
    });
    // 막대
    const maxW = 3.0;
    const ratio = item.before / 431;
    s.addShape(pres.shapes.RECTANGLE, { x: 5.0, y: y + 0.08, w: maxW * ratio, h: 0.25, fill: { color: item.color }, line: { type: "none" } });
  });

  // 우측: OKLCH 토큰 명도 조정
  s.addText("OKLCH 토큰 명도 조정 (WCAG AA)", { x: 8.5, y: 1.5, w: 4.3, h: 0.4, fontSize: 14, bold: true, color: C.dark, fontFace: FONT_H });
  const tokens = [
    { name: "--accent", before: "0.58", after: "0.50", ratio: "3.53 → 5.13" },
    { name: "--pos", before: "0.55", after: "0.47", ratio: "3.16 → 4.80" },
    { name: "--warn", before: "0.62", after: "0.50", ratio: "3.05 → 4.81" },
    { name: "--teal", before: "0.55", after: "0.47", ratio: "3.59 → 5.24" },
  ];
  tokens.forEach((t, i) => {
    const y = 2.0 + i * 0.55;
    s.addText(t.name, { x: 8.5, y, w: 1.5, h: 0.4, fontSize: 11, bold: true, color: C.primary, fontFace: "Consolas", valign: "middle" });
    s.addText(`${t.before} → ${t.after}`, { x: 10.0, y, w: 1.2, h: 0.4, fontSize: 11, color: C.textMute, fontFace: "Consolas", valign: "middle" });
    s.addText(t.ratio + " :1", { x: 11.2, y, w: 1.6, h: 0.4, fontSize: 11, color: C.pos, fontFace: "Consolas", valign: "middle" });
  });

  // 하단: PR 누적
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.9, w: 12.3, h: 2.0, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("관련 PR (5건 머지)", { x: 0.8, y: 5.0, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_B });
  const prList = [
    { id: "#46", desc: "UI P1B 등급 C 11 컴포넌트" },
    { id: "#47", desc: "UI P0 Tooltip + text-dim 상향" },
    { id: "#48", desc: "UI P1A Recharts hex → CSS var" },
    { id: "#50", desc: "라이트 모드 가시성 ~1,300건" },
    { id: "#51", desc: "Benchmark + 카드 라이트 모드" },
    { id: "#52", desc: "Benchmark ToggleGroup active" },
  ];
  prList.forEach((p, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 4.1;
    const y = 5.5 + row * 0.6;
    s.addText(p.id, { x, y, w: 0.8, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H, valign: "middle" });
    s.addText(p.desc, { x: x + 0.8, y, w: 3.2, h: 0.4, fontSize: 10, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
  });

  addFooter(s, 7, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 8 — A-01 SSTR 5종 정렬
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-01 SSTR site-directed docking", "결합 포켓 좌표 + 5종 정렬 — PR #61");

  // 좌측: 결합 포켓 정보
  s.addText("SSTR2 결합 포켓 (7XNA)", { x: 0.5, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 2.0, w: 6.0, h: 2.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("Center coordinates", { x: 0.7, y: 2.1, w: 5.6, h: 0.35, fontSize: 11, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText("(-5.595, -28.626, 52.210)", { x: 0.7, y: 2.45, w: 5.6, h: 0.45, fontSize: 18, bold: true, color: C.primary, fontFace: "Consolas" });
  s.addText("Radius / Box size", { x: 0.7, y: 3.0, w: 5.6, h: 0.35, fontSize: 11, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText("13.0 Å / 26.1 Å", { x: 0.7, y: 3.35, w: 5.6, h: 0.45, fontSize: 18, bold: true, color: C.primary, fontFace: "Consolas" });
  s.addText("핵심 잔기 (TM5+TM6)", { x: 0.7, y: 3.85, w: 5.6, h: 0.35, fontSize: 11, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText("205, 208, 209, 212, 272, 273, 276, 279", { x: 0.7, y: 4.0, w: 5.6, h: 0.3, fontSize: 10, color: C.text, fontFace: "Consolas" });

  // 우측: 5종 정렬 RMSD 차트
  s.addChart(pres.charts.BAR, [{
    name: "RMSD (Å)",
    labels: ["SSTR1\n(9IK8)", "SSTR3\n(8XIR)", "SSTR4\n(7XMT)", "SSTR5\n(8ZBJ)"],
    values: [3.125, 3.086, 3.019, 2.770],
  }], {
    x: 6.8, y: 1.5, w: 6.0, h: 5.3, barDir: "col",
    chartColors: [C.primary, C.secondary, C.accent, C.pos],
    chartArea: { fill: { color: "FFFFFF" } },
    catAxisLabelColor: C.textMute,
    valAxisLabelColor: C.textMute,
    valGridLine: { color: C.border, size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.dark,
    showLegend: false,
    showTitle: true,
    title: "SSTR2 정렬 RMSD (목표 ≤ 4.0 Å, 전체 충족)",
    titleColor: C.dark,
    titleFontSize: 12,
  });

  // 하단: 도구
  s.addText("도구: PyMOL cealign (TM-align 미설치 fallback) · 산출물: data/somatostatin_receptor/{SSTRN}_aligned.pdb", {
    x: 0.5, y: 6.85, w: 12.3, h: 0.3, fontSize: 10, italic: true, color: C.textMute, fontFace: FONT_B,
  });

  addFooter(s, 8, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 9 — A-04 composite scoring
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-04 복합 스코어링 + Tier 분류", "PR #62 — composite_scorer + radiolysis_scorer, 73 tests pass");

  // 좌측: 5 Hard Cutoff
  s.addText("Hard Cutoff 5게이트", { x: 0.5, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  const gates = [
    { n: "G1", label: "ΔG", crit: "≤ -95.024 REU", color: C.primary },
    { n: "G2", label: "selectivity", crit: "≥ 100× (SSTR1/2)", color: C.secondary },
    { n: "G3", label: "radiolysis", crit: "민감 잔기 ≤ 3", color: C.accent },
    { n: "G4", label: "admet_tox", crit: "pepADMET ≤ 0.3", color: C.pos },
    { n: "G5", label: "instability index", crit: "II < 40", color: C.warn },
  ];
  gates.forEach((g, i) => {
    const y = 2.0 + i * 0.65;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.7, h: 0.55, fill: { color: g.color }, line: { type: "none" } });
    s.addText(g.n, { x: 0.5, y, w: 0.7, h: 0.55, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_H });
    s.addText(g.label, { x: 1.4, y, w: 2.0, h: 0.55, fontSize: 12, bold: true, color: C.dark, fontFace: FONT_B, valign: "middle" });
    s.addText(g.crit, { x: 3.5, y, w: 3.0, h: 0.55, fontSize: 11, color: C.textMute, fontFace: "Consolas", valign: "middle" });
  });

  // 우측: Tier 분류 결과
  s.addText("Tier 분류 (smoke test, 11 후보)", { x: 7.0, y: 1.5, w: 5.8, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });

  const tiers = [
    { tier: "S", n: 1, ratio: 9, color: C.accent, desc: "전 게이트 PASS + Pareto front" },
    { tier: "A", n: 0, ratio: 0, color: C.primary, desc: "—" },
    { tier: "B", n: 5, ratio: 46, color: C.secondary, desc: "일부 게이트 통과" },
    { tier: "FAIL", n: 5, ratio: 45, color: C.neg, desc: "Hard Cutoff 위반" },
  ];
  tiers.forEach((t, i) => {
    const y = 2.0 + i * 0.85;
    s.addShape(pres.shapes.OVAL, { x: 7.0, y, w: 0.7, h: 0.7, fill: { color: t.color }, line: { type: "none" } });
    s.addText(t.tier, { x: 7.0, y, w: 0.7, h: 0.7, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_H });
    s.addText(`${t.n} 후보 (${t.ratio}%)`, { x: 7.9, y, w: 2.5, h: 0.7, fontSize: 14, bold: true, color: C.dark, fontFace: FONT_B, valign: "middle" });
    s.addText(t.desc, { x: 10.5, y, w: 2.3, h: 0.7, fontSize: 10, color: C.textMute, fontFace: FONT_B, valign: "middle" });
  });

  // 하단: 구현 핵심
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.7, w: 12.3, h: 1.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("구현 핵심", { x: 0.7, y: 5.8, w: 12.0, h: 0.3, fontSize: 12, bold: true, color: C.primary, fontFace: FONT_B });
  s.addText("Pareto non-dominated sort (O(n²M) 자체 구현, pymoo 의존성 X)  ·  WSS = ΣWi·Mi (ENDPOINT_CONFIDENCE 가중치)  ·  ¹⁷⁷Lu radiolysis: F/W 민감, Cys3-Cys14 SS bond 예외  ·  A-09 자동 입력 생성 (tier_s_candidates.csv)", {
    x: 0.7, y: 6.15, w: 12.0, h: 0.85, fontSize: 11, color: C.text, fontFace: FONT_B,
  });

  addFooter(s, 9, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 10 — A-05 SST14 reference dG
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-05 SST14 reference dG (n=10)", "FlexPepDock + InterfaceAnalyzer · KPI σ<5 충족 · 커밋 8e7e1cc");

  // 큰 stat
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("mean ΔG", { x: 0.8, y: 1.7, w: 5.4, h: 0.4, fontSize: 14, color: C.accent, fontFace: FONT_B });
  s.addText("553.857", { x: 0.8, y: 2.1, w: 5.4, h: 1.5, fontSize: 96, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("REU (Rosetta Energy Unit)", { x: 0.8, y: 3.6, w: 5.4, h: 0.4, fontSize: 14, color: C.textDim, fontFace: FONT_B });
  s.addText("σ = 4.024", { x: 0.8, y: 4.3, w: 5.4, h: 0.5, fontSize: 24, bold: true, color: C.accent, fontFace: FONT_H });
  s.addText("KPI σ < 5  ✓  충족", { x: 0.8, y: 4.85, w: 5.4, h: 0.4, fontSize: 13, italic: true, color: C.pos, fontFace: FONT_B });
  s.addText("95% CI", { x: 0.8, y: 5.4, w: 5.4, h: 0.4, fontSize: 12, color: C.textDim, fontFace: FONT_B });
  s.addText("[550.978, 556.735]", { x: 0.8, y: 5.7, w: 5.4, h: 0.5, fontSize: 20, color: "FFFFFF", fontFace: "Consolas" });

  // 우측: 알려진 한계 + 활용
  s.addText("알려진 한계", { x: 6.8, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 1.95, w: 6.0, h: 2.0, fill: { color: C.light }, line: { color: C.warn, width: 2 } });
  s.addText("SST14 reference complex 부재 → Fallback 모드 → 양수 ΔG (553.857 REU). 절대값 신뢰 불가, **상대 비교만 유효** (candidate.ΔG < 553.857 → SST-14 대비 유리한 결합).", {
    x: 6.95, y: 2.05, w: 5.7, h: 1.85, fontSize: 11, color: C.text, fontFace: FONT_B,
  });

  s.addText("활용", { x: 6.8, y: 4.15, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 4.6, w: 6.0, h: 2.2, fill: { color: C.light }, line: { color: C.primary, width: 2 } });
  s.addText("pharmacology_guards.SST14_SSTR2_ref_ddg_flexpep 등록\n+ A-04 composite_scorer ΔG 게이트 자동 비교\n+ PRST-001~004 모든 후보 SST-14 대비 우월 (ΔG -105 ~ -99 REU)", {
    x: 6.95, y: 4.7, w: 5.7, h: 2.0, fontSize: 12, color: C.text, fontFace: FONT_B,
  });

  addFooter(s, 10, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 11 — A-02/A-03 pepADMET D-AA 불가 (HIGH-BLOCKER)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-02/A-03 핵심 발견 — pepADMET D-AA HIGH-BLOCKER", "Octreotide/Lanreotide ADMET 예측 도구 부재 확정");

  // 좌측: 발견 사항
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.neg }, line: { type: "none" } });
  s.addText("⚠️ HIGH-BLOCKER", { x: 0.7, y: 1.7, w: 5.6, h: 0.5, fontSize: 24, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("D-아미노산 half-life 예측 불가", { x: 0.7, y: 2.3, w: 5.6, h: 0.5, fontSize: 20, color: "FFFFFF", fontFace: FONT_H });
  s.addText("실 테스트 결과 (2026-05-19, pepADMET 웹서버)", { x: 0.7, y: 3.0, w: 5.6, h: 0.35, fontSize: 11, color: C.textDim, fontFace: FONT_B });

  const findings = [
    "Half-life 엔드포인트: natural seq 전용",
    "Modification 40종 중 D-AA 0개",
    "SS bond 항목 0개",
    "비표준 AA \"B\" → silent error",
    "환형 SMILES → 서버 파싱 오류",
  ];
  findings.forEach((f, i) => {
    const y = 3.5 + i * 0.55;
    s.addShape(pres.shapes.OVAL, { x: 0.7, y: y + 0.1, w: 0.3, h: 0.3, fill: { color: "FFFFFF" }, line: { type: "none" } });
    s.addText("✕", { x: 0.7, y: y + 0.1, w: 0.3, h: 0.3, fontSize: 13, bold: true, color: C.neg, align: "center", valign: "middle", fontFace: FONT_B });
    s.addText(f, { x: 1.15, y, w: 5.1, h: 0.5, fontSize: 13, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
  });

  // 우측: 정량 검증
  s.addText("SST-14 예측값 vs 실측", { x: 7.0, y: 1.5, w: 5.8, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });

  s.addChart(pres.charts.BAR, [
    { name: "pepADMET HBN (min)", labels: ["SST-14", "Octreotide"], values: [14.484, 84.008] },
    { name: "실측 t½ (min)", labels: ["SST-14", "Octreotide"], values: [3, 90] },
  ], {
    x: 7.0, y: 2.0, w: 5.8, h: 3.0, barDir: "col",
    chartColors: [C.warn, C.primary],
    chartArea: { fill: { color: "FFFFFF" } },
    catAxisLabelColor: C.textMute,
    valAxisLabelColor: C.textMute,
    valGridLine: { color: C.border, size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.dark,
    dataLabelFontSize: 10,
    showLegend: true,
    legendPos: "b",
    legendFontSize: 10,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 5.15, w: 5.8, h: 1.7, fill: { color: C.light }, line: { color: C.warn, width: 1 } });
  s.addText("권고", { x: 7.2, y: 5.25, w: 5.4, h: 0.3, fontSize: 12, bold: true, color: C.warn, fontFace: FONT_B });
  s.addText("• D-AA 후보(Octreotide·Lanreotide): pepADMET 적용 금지\n• L-AA 후보: 상대 순위만 허용 (절대값 4.83× 과대)\n• 자체 D-AA 모델 개발 (ToxTeller fine-tune, CC-BY)", {
    x: 7.2, y: 5.55, w: 5.4, h: 1.25, fontSize: 11, color: C.text, fontFace: FONT_B,
  });

  addFooter(s, 11, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 12 — A-06 DiffDock NOT_RECOMMENDED
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-06 DiffPepDock PoC — NOT_RECOMMENDED", "환경 OK · 실행 OK · 그러나 SS bond + 친화도 점수 부재로 기각");

  // 좌측: 비교 표
  s.addText("3 docking engine 비교", { x: 0.5, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.dark, fontFace: FONT_H });

  const rows = [
    [{ text: "엔진", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "런타임 (10 포즈)", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "친화도 점수", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "SS bond", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["FlexPepDock", "6~13초", "Rosetta ddG", "✓"],
    ["Boltz", "60~90초", "ipTM (0~1)", "✓"],
    [{ text: "DiffPepDock", options: { fill: { color: "FEE2E2" } } },
     { text: "77.9초", options: { fill: { color: "FEE2E2" } } },
     { text: "✕ 없음", options: { fill: { color: "FEE2E2" }, color: C.neg, bold: true } },
     { text: "✕ 미지원", options: { fill: { color: "FEE2E2" }, color: C.neg, bold: true } }],
  ];
  s.addTable(rows, {
    x: 0.5, y: 2.0, w: 6.0, colW: [1.8, 1.6, 1.5, 1.1],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.5,
    valign: "middle",
    align: "center",
  });

  // 결과 정량 메트릭
  s.addText("DiffPepDock 산출 메트릭", { x: 0.5, y: 4.5, w: 6.0, h: 0.4, fontSize: 14, bold: true, color: C.dark, fontFace: FONT_H });
  s.addText("10개 포즈 생성, inter-pose Cα RMSD 0.36 ~ 2.26 Å (평균 0.75 Å)", { x: 0.5, y: 5.0, w: 6.0, h: 0.5, fontSize: 12, color: C.textMute, fontFace: FONT_B });
  s.addText("⚠️ openmm GLIBCXX_3.4.30 비호환 → postprocess 비활성화", { x: 0.5, y: 5.5, w: 6.0, h: 0.5, fontSize: 11, italic: true, color: C.warn, fontFace: FONT_B });

  // 우측: 결정
  s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 1.5, w: 5.8, h: 5.3, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("결정", { x: 7.2, y: 1.7, w: 5.4, h: 0.4, fontSize: 14, color: C.accent, fontFace: FONT_B });
  s.addText("NOT_RECOMMENDED", { x: 7.2, y: 2.1, w: 5.4, h: 0.8, fontSize: 28, bold: true, color: C.neg, fontFace: FONT_H });
  s.addText("기각 사유", { x: 7.2, y: 3.0, w: 5.4, h: 0.4, fontSize: 12, color: C.accent, fontFace: FONT_B });
  s.addText("① SST14 Cys3-Cys14 SS bond 미지원 — pharmacophore 재현 불가\n\n② 친화도/신뢰도 점수 없음 — 후보 순위화 불가\n\n③ openmm 비호환 — postprocessing 전면 비활성화", {
    x: 7.2, y: 3.4, w: 5.4, h: 2.0, fontSize: 12, color: "FFFFFF", fontFace: FONT_B,
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 7.2, y: 5.6, w: 5.4, h: 1.1, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("Boltz + FlexPepDock 현 파이프라인 유지", {
    x: 7.2, y: 5.6, w: 5.4, h: 1.1, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_H,
  });

  addFooter(s, 12, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 13 — PRST-001~004 최종 후보
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-09 최종 후보 4개 — Gate-2 진입", "PR #63 · composite_scorer Tier S/A/B/FAIL 결과");

  const rows = [
    [{ text: "순위", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "ID", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "서열 (14aa)", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "Tier", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "WSS", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "ΔG (REU)", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "radiolysis", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "주의", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    [{ text: "1", options: { fill: { color: "ECFEFF" }, bold: true } },
     { text: "PRST-001", options: { fill: { color: "ECFEFF" }, bold: true, color: C.primary } },
     { text: "AGCKNIIWKTITSC", options: { fill: { color: "ECFEFF" }, fontFace: "Consolas", bold: true } },
     { text: "S ★", options: { fill: { color: C.accent }, color: "FFFFFF", bold: true } },
     { text: "1.000", options: { fill: { color: "ECFEFF" }, bold: true } },
     { text: "-105.5", options: { fill: { color: "ECFEFF" } } },
     { text: "1", options: { fill: { color: "ECFEFF" } } },
     { text: "—", options: { fill: { color: "ECFEFF" } } }],
    ["2", "PRST-002", { text: "AGCKNFIWKTITSC", options: { fontFace: "Consolas" } }, { text: "B", options: { fill: { color: C.secondary }, color: "FFFFFF", bold: true } }, "0.582", "-101.8", "2", "—"],
    ["3", "PRST-004", { text: "AICKNFIWKTITSC", options: { fontFace: "Consolas" } }, { text: "B", options: { fill: { color: C.secondary }, color: "FFFFFF", bold: true } }, "0.365", "-100.0", "2", "—"],
    ["4", "PRST-003", { text: "AGCRNFIWKTITSC", options: { fontFace: "Consolas" } }, { text: "B", options: { fill: { color: C.secondary }, color: "FFFFFF", bold: true } }, "0.271", "-99.2", "2", { text: "K4→R, N-말단 DOTA 전용", options: { color: C.warn, italic: true } }],
  ];

  s.addTable(rows, {
    x: 0.5, y: 1.55, w: 12.3,
    colW: [0.6, 1.4, 2.5, 1.0, 1.0, 1.3, 1.3, 3.2],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.55,
    valign: "middle",
    align: "center",
  });

  // 하단 검증
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.0, w: 12.3, h: 1.9, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("검증 결과 (전 후보)", { x: 0.8, y: 5.1, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.primary, fontFace: FONT_B });
  const checks = [
    "✓ Hard Cutoff 5게이트 전항목 PASS (4/4)",
    "✓ pharmacology_guards 39/39 회귀 테스트",
    "✓ H-06 HEURISTIC + D-AA HIGH-BLOCKER 가드 강제 적용",
    "✓ SST-14 ref ΔG (-95.024 REU) 대비 모두 우월",
  ];
  checks.forEach((c, i) => {
    const x = 0.8 + (i % 2) * 6.0;
    const y = 5.55 + Math.floor(i / 2) * 0.45;
    s.addText(c, { x, y, w: 5.8, h: 0.4, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "middle" });
  });

  addFooter(s, 13, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 14 — PRST-001 상세
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "PRST-001 상세 — Tier S 후보", "AGCKNIIWKTITSC · F6→I + F11→I, FWKT 중 W/K/T 보존");

  // 시퀀스 정렬 (모노스페이스)
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 12.3, h: 1.5, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("Position", { x: 0.8, y: 1.65, w: 1.5, h: 0.3, fontSize: 11, color: C.accent, fontFace: "Consolas" });
  s.addText("1  2  3  4  5  6  7  8  9 10 11 12 13 14", { x: 2.3, y: 1.65, w: 10.0, h: 0.3, fontSize: 14, color: C.textDim, fontFace: "Consolas" });

  s.addText("SST-14 (WT)", { x: 0.8, y: 2.05, w: 1.5, h: 0.4, fontSize: 11, color: "FFFFFF", fontFace: "Consolas", bold: true });
  s.addText("A  G  C  K  N  F  F  W  K  T  F  T  S  C", { x: 2.3, y: 2.05, w: 10.0, h: 0.4, fontSize: 16, bold: true, color: "FFFFFF", fontFace: "Consolas" });

  s.addText("PRST-001", { x: 0.8, y: 2.55, w: 1.5, h: 0.4, fontSize: 11, color: C.accent, fontFace: "Consolas", bold: true });
  s.addText([
    { text: "A  G  ", options: { color: "FFFFFF" } },
    { text: "C  ", options: { color: C.pos, bold: true } },
    { text: "K  N  ", options: { color: "FFFFFF" } },
    { text: "I  ", options: { color: C.warn, bold: true } },
    { text: "F  W  K  T  ", options: { color: C.pos, bold: true } },
    { text: "I  ", options: { color: C.warn, bold: true } },
    { text: "T  S  ", options: { color: "FFFFFF" } },
    { text: "C", options: { color: C.pos, bold: true } },
  ], { x: 2.3, y: 2.55, w: 10.0, h: 0.4, fontSize: 16, fontFace: "Consolas" });

  // 핵심 메트릭
  const metrics = [
    { label: "WSS", val: "1.000", color: C.accent },
    { label: "ΔG (Boltz REU)", val: "-105.5", color: C.primary },
    { label: "radiolysis count", val: "1", color: C.pos },
    { label: "selectivity (SSTR1/2)", val: "250×", color: C.secondary },
  ];
  metrics.forEach((m, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 3.3, w: 3.0, h: 1.7, fill: { color: C.light }, line: { color: C.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 3.3, w: 3.0, h: 0.08, fill: { color: m.color }, line: { type: "none" } });
    s.addText(m.label, { x: x + 0.2, y: 3.5, w: 2.6, h: 0.3, fontSize: 10, color: C.textMute, fontFace: FONT_B });
    s.addText(m.val, { x: x + 0.2, y: 3.8, w: 2.6, h: 1.0, fontSize: 36, bold: true, color: m.color, fontFace: FONT_H, valign: "middle" });
  });

  // 디자인 근거
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.3, w: 12.3, h: 1.6, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("디자인 근거", { x: 0.7, y: 5.4, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_B });
  s.addText("• F6→I, F11→I: ¹⁷⁷Lu radiolysis 민감 Phe 잔기 2개 제거 (radiolysis count 6 → 1)\n• FWKT 중 W8/K9/T10 보존 — SSTR2 binding pharmacophore 유지\n• Cys3-Cys14 SS bond 보존 (환형 구조 + 안정성)\n• §검증: V-A09-01 — F6→I 치환이 SSTR2 binding에 미치는 영향 wet-lab Ki 측정 HIGH", {
    x: 0.7, y: 5.75, w: 12.0, h: 1.15, fontSize: 11, color: "FFFFFF", fontFace: FONT_B,
  });

  addFooter(s, 14, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 15 — 미진 사항 (V-검증 HIGH)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "미진 사항 — V-검증 HIGH 6건", "대부분 wet-lab Gate-2 단계에서 RI팀이 처리");

  const rows = [
    [{ text: "#", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "검증 항목", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "자동화", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "담당", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["V-A09-01", "PRST-001 F6→I 치환 시 SSTR2 Ki 실측 변화", { text: "NO (wet-lab)", options: { color: C.neg, bold: true } }, "RI팀 (Gate-2)"],
    ["V-A09-03", "pepADMET selectivity margin × 실측 Ki 상관 검증", { text: "NO (wet-lab)", options: { color: C.neg, bold: true } }, "RI팀 (Gate-2)"],
    ["V-A09-05", "predict_half_life() ranking 순서 wet-lab 검증", { text: "NO (wet-lab)", options: { color: C.neg, bold: true } }, "RI팀 (wet-lab 병행)"],
    ["V-A09-06", "Boltz2 ΔG -105.5 REU × 실험 IC50/Ki 상관 (최소 1건)", { text: "NO (wet-lab)", options: { color: C.neg, bold: true } }, "AI팀 + RI팀"],
    ["V-02", "pepADMET 논문 전문 접근 (DOI 10.1021/acs.jcim.5c02518 paywall)", { text: "△ (저자 문의)", options: { color: C.warn } }, "reviewer-pharma"],
    ["V-03", "pepADMET D-AA Octreotide SMILES 테스트", { text: "✓ A-02 follow-up 일부 해결", options: { color: C.pos } }, "reviewer-chemistry"],
  ];

  s.addTable(rows, {
    x: 0.5, y: 1.55, w: 12.3,
    colW: [1.4, 6.2, 2.5, 2.2],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.55,
    valign: "middle",
  });

  // 하단: Gate-2 접근 방향
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.45, w: 12.3, h: 1.5, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("Gate-2 wet-lab 검증 계획 (RI팀)", { x: 0.8, y: 5.55, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_B });
  s.addText("① PRST-001~004 합성 (Peptron, 4-6주)  →  ② SSTR1-5 binding Ki competition (n=3×3 biol)  →  ③ pepADMET 예측값 × 실측 상관 분석  →  ④ V-A09-01/03/05/06 모두 해결 → Gate-3 (¹⁷⁷Lu 라벨링 + in vivo)", {
    x: 0.8, y: 5.95, w: 12.0, h: 0.9, fontSize: 11, color: "FFFFFF", fontFace: FONT_B,
  });

  addFooter(s, 15, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 16 — 다음 단계 + Closing
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.2, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });

  s.addText("Gate-2 진입 준비 완료", { x: 0.5, y: 0.7, w: 12.3, h: 0.6, fontSize: 14, color: C.accent, bold: true, fontFace: FONT_B, charSpacing: 6 });
  s.addText("다음 단계", { x: 0.5, y: 1.2, w: 12.3, h: 1.0, fontSize: 48, bold: true, color: "FFFFFF", fontFace: FONT_H });

  // 3 컬럼: 즉시 / 중기 / 장기
  const cols = [
    {
      title: "즉시 (이번 주)",
      color: C.accent,
      items: [
        "PRST-001~004 합성 의뢰",
        "Peptron 발주 + QC (HPLC, MS)",
        "wetlab order BE 등록",
        "RI팀 사전 협의 (PRST-003 K4→R)",
      ],
    },
    {
      title: "중기 (4-6주)",
      color: C.secondary,
      items: [
        "SSTR1-5 binding Ki (n=3×3)",
        "V-A09-01/03/05/06 해결",
        "pepADMET 예측값 상관 검증",
        "Tier B → S 재분류 검토",
      ],
    },
    {
      title: "장기 (3-6개월)",
      color: C.primary,
      items: [
        "¹⁷⁷Lu 라벨링 + in vivo PK",
        "D-AA 자체 모델 (ToxTeller fine-tune)",
        "Boltz로 complex 생성 (Task #38)",
        "취사선택 시스템 FE/BE (Task #39)",
      ],
    },
  ];

  cols.forEach((col, i) => {
    const x = 0.5 + i * 4.3;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.6, w: 4.0, h: 0.5, fill: { color: col.color }, line: { type: "none" } });
    s.addText(col.title, { x: x + 0.2, y: 2.6, w: 3.8, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", valign: "middle", fontFace: FONT_H });

    s.addShape(pres.shapes.RECTANGLE, { x, y: 3.1, w: 4.0, h: 3.4, fill: { color: "FFFFFF" }, line: { type: "none" } });
    col.items.forEach((item, j) => {
      const y = 3.3 + j * 0.7;
      s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.1, w: 0.3, h: 0.3, fill: { color: col.color }, line: { type: "none" } });
      s.addText(String(j + 1), { x: x + 0.2, y: y + 0.1, w: 0.3, h: 0.3, fontSize: 12, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_B });
      s.addText(item, { x: x + 0.6, y, w: 3.3, h: 0.5, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "middle" });
    });
  });

  // 하단 인용
  s.addText("PRST_N_FM · pre-wet-lab AI screening · 2026-05-19 SOD orchestrator session", {
    x: 0.5, y: 6.75, w: 12.3, h: 0.4, fontSize: 10, italic: true, color: C.textDim, fontFace: FONT_B, align: "center",
  });

  // footer (다크 위에 다크 footer 안 어울리니 생략)
  s.addText("16 / 16", { x: 12.4, y: 7.25, w: 0.7, h: 0.3, fontSize: 9, color: "FFFFFF", fontFace: FONT_B, valign: "middle", align: "right" });
}

// ───────────────────────────────────────────────
// 저장
// ───────────────────────────────────────────────
pres.writeFile({ fileName: "PRST_N_FM_SOD_2026-05-19.pptx" })
  .then((fileName) => console.log(`Saved: ${fileName}`));
