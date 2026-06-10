const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" x 7.5"
pres.author = "orchestrator-session";
pres.title = "SSTR2 Pipeline 실행 시스템 분석";

// Ocean Gradient palette (도메인 — radiopharmaceutical AI 신뢰감)
const C = {
  navy: "0F172A",      // primary dark
  deep: "065A82",      // primary
  teal: "1C7293",      // secondary
  midnight: "21295C",  // accent dark
  ice: "DBEAFE",       // light bg
  cream: "F8FAFC",     // off-white
  white: "FFFFFF",
  slate: "475569",     // body text
  muted: "94A3B8",     // captions
  // Severity
  critical: "DC2626",  // red
  high: "EA580C",      // orange
  med: "CA8A04",       // amber
  low: "65A30D",       // green
  info: "0891B2",      // cyan
};

const FONT_H = "Calibri";
const FONT_B = "Calibri";

// Helper — header bar for content slides
function addHeader(slide, title, subtitle) {
  slide.background = { color: C.cream };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  slide.addText(title, {
    x: 0.5, y: 0.15, w: 11, h: 0.5,
    fontFace: FONT_H, fontSize: 24, bold: true, color: C.white, margin: 0
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.55, w: 11, h: 0.3,
      fontFace: FONT_B, fontSize: 11, color: C.ice, margin: 0
    });
  }
  // accent strip
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.9, w: 13.3, h: 0.06, fill: { color: C.teal }, line: { color: C.teal }
  });
}

function addPageNumber(slide, n, total) {
  slide.addText(`${n} / ${total}`, {
    x: 12.5, y: 7.15, w: 0.6, h: 0.25,
    fontFace: FONT_B, fontSize: 9, color: C.muted, align: "right", margin: 0
  });
}

const TOTAL = 14;

// ============================================================
// Slide 1 — Title
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // accent stripe
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 2.6, w: 13.3, h: 0.08, fill: { color: C.teal }, line: { color: C.teal }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 2.78, w: 13.3, h: 0.02, fill: { color: C.deep }, line: { color: C.deep }
  });

  s.addText("SSTR2 Pipeline", {
    x: 0.8, y: 1.3, w: 12, h: 1.0,
    fontFace: FONT_H, fontSize: 56, bold: true, color: C.white, margin: 0
  });
  s.addText("실행 시스템 분석 — 더미·미구현·개선·구조", {
    x: 0.8, y: 2.95, w: 12, h: 0.6,
    fontFace: FONT_H, fontSize: 24, color: C.ice, margin: 0
  });

  // Key stats — 3 columns
  const statsY = 4.5;
  const statBoxes = [
    { label: "코드 트리", value: "4", sub: "pipeline_local · AG_src · backend · pyrosetta_flow" },
    { label: "더미·미구현", value: "25+", sub: "Critical 3 · High 8 · Med 10 · Low 4" },
    { label: "개선 권장", value: "8", sub: "단기 5 · 중기 2 · 장기 1" },
  ];
  statBoxes.forEach((b, i) => {
    const x = 0.8 + i * 4.2;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: statsY, w: 3.8, h: 1.8,
      fill: { color: C.deep }, line: { color: C.teal, width: 0 }
    });
    s.addText(b.value, {
      x, y: statsY + 0.15, w: 3.8, h: 0.85,
      fontFace: FONT_H, fontSize: 64, bold: true, color: C.white, align: "center", margin: 0
    });
    s.addText(b.label, {
      x, y: statsY + 1.05, w: 3.8, h: 0.3,
      fontFace: FONT_B, fontSize: 14, bold: true, color: C.ice, align: "center", margin: 0
    });
    s.addText(b.sub, {
      x: x + 0.2, y: statsY + 1.4, w: 3.4, h: 0.3,
      fontFace: FONT_B, fontSize: 9, color: C.ice, align: "center", italic: true, margin: 0
    });
  });

  s.addText("2026-05-19  ·  orchestrator-session  ·  DAG v2.1 Tier 0+1 적용 상태", {
    x: 0.8, y: 6.8, w: 12, h: 0.4,
    fontFace: FONT_B, fontSize: 12, color: C.muted, margin: 0
  });
}

// ============================================================
// Slide 2 — Executive Summary
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "Executive Summary", "한 줄 결론 + 핵심 수치");

  // 한 줄 결론
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 12.3, h: 1.1,
    fill: { color: C.deep }, line: { color: C.teal, width: 0 }
  });
  s.addText("실행 가능 + 일부 정직성 갭", {
    x: 0.8, y: 1.3, w: 11.7, h: 0.5,
    fontFace: FONT_H, fontSize: 22, bold: true, color: C.white, margin: 0
  });
  s.addText('"코어 파이프라인(PyRosetta + Boltz-2 + ESMFold + Ollama)은 실 동작, 그러나 9개 약리 지표는 HEURISTIC + 5개 모듈은 stub fallback + Silo A는 환경 미정비 상태."', {
    x: 0.8, y: 1.75, w: 11.7, h: 0.45,
    fontFace: FONT_B, fontSize: 12, italic: true, color: C.ice, margin: 0
  });

  // 핵심 수치 표
  const rows = [
    ["영역", "수치", "상태"],
    ["실행 가능 모듈", "step01~08 + step03b/05b/05c (10건)", "✓ 동작"],
    ["테스트 통과", "170/170 (어제 sprint 기준)", "✓ Green CI"],
    ["휴리스틱(HEURISTIC) 함수", "9건 (pharmacology_guards.py:209-322)", "⚠ 신뢰등급 명시"],
    ["Stub fallback", "5건 (PyRosetta, Step07 BioPython, dummy scores, mock_wv, ESM-2)", "⚠ 환경 의존"],
    ["FAILURE_ACTION_MAP 매핑", "5건 → 6 카테고리 정규화 적용됨", "✓ Tier 0"],
    ["다음 sprint 후보", "8건 (P14 PDB, G-2 단위, SS-bond Cys, Silo A 등)", "📋 계획됨"],
  ];
  s.addTable(rows, {
    x: 0.5, y: 2.55, w: 12.3,
    fontSize: 11, fontFace: FONT_B, color: C.slate,
    border: { pt: 0.5, color: C.muted },
    fill: { color: C.white },
    rowH: 0.35,
    colW: [3.0, 6.0, 3.3],
  });

  // bottom callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.4, w: 12.3, h: 0.6,
    fill: { color: C.ice }, line: { color: C.teal, width: 0 }
  });
  s.addText("권장 다음 행동: G-2 단위 정정 (5분) → fwkt_contact Phase 2 (1일) → Silo A dogfood (2~3일)", {
    x: 0.8, y: 6.48, w: 11.7, h: 0.45,
    fontFace: FONT_B, fontSize: 13, bold: true, color: C.midnight, margin: 0
  });

  addPageNumber(s, 2, TOTAL);
}

// ============================================================
// Slide 3 — 시스템 개황도 (high-level)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "시스템 개황도", "FE / BE / Orchestrator / Pipeline / LLM 5 레이어");

  // 5 layers vertical
  const layers = [
    { name: "Frontend (Vite + React 19)", sub: "TanStack Query · OKLCH 토큰 · 5 배지 isLive · ClusterPanel", color: C.deep, icon: "🖥" },
    { name: "Backend API (FastAPI + uvicorn)", sub: "/api/status · /api/experiment/run · /api/selectivity · _enrich_candidates", color: C.teal, icon: "⚙" },
    { name: "Orchestrator (LocalPipelineOrchestrator)", sub: "5-Agent (Planner · Builder · QCRanker · Critic · Reporter) · Step01~08", color: C.midnight, icon: "🧭" },
    { name: "Pipeline (Silo A · Silo B · Combined)", sub: "RFdiff · MPNN · BLOSUM · ESMFold · Boltz-2 · PyRosetta · FoldMason", color: "1E40AF", icon: "🧬" },
    { name: "LLM (Ollama qwen3:8b @ :11435) · STATUS_FILE", sub: "Critic · Planner · Reporter LLM 분기 + rule-based 폴백", color: C.navy, icon: "🤖" },
  ];

  const startY = 1.3;
  const rowH = 0.95;
  const gap = 0.15;
  layers.forEach((L, i) => {
    const y = startY + i * (rowH + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 12.3, h: rowH,
      fill: { color: L.color }, line: { color: L.color, width: 0 }
    });
    s.addText(L.icon, {
      x: 0.6, y: y + 0.2, w: 0.6, h: 0.6,
      fontFace: FONT_H, fontSize: 26, color: C.white, align: "center", margin: 0
    });
    s.addText(L.name, {
      x: 1.3, y: y + 0.1, w: 9, h: 0.45,
      fontFace: FONT_H, fontSize: 16, bold: true, color: C.white, margin: 0
    });
    s.addText(L.sub, {
      x: 1.3, y: y + 0.55, w: 11, h: 0.35,
      fontFace: FONT_B, fontSize: 11, color: C.ice, margin: 0
    });
    // arrow down to next layer
    if (i < layers.length - 1) {
      s.addShape(pres.shapes.LINE, {
        x: 6.65, y: y + rowH, w: 0, h: gap,
        line: { color: C.teal, width: 2, endArrowType: "triangle" }
      });
    }
  });

  // side annotations
  s.addText("⬆ Polling 2s\n(useQuery)", {
    x: 11.5, y: 1.45, w: 1.6, h: 0.65,
    fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, align: "center", margin: 0
  });
  s.addText("⬆ HMR 즉시", {
    x: 11.5, y: 0.95, w: 1.6, h: 0.3,
    fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, align: "center", margin: 0
  });

  addPageNumber(s, 3, TOTAL);
}

// ============================================================
// Slide 4 — 코드 트리 + 활성 모듈 매트릭스
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "코드 트리 + 활성 모듈 매트릭스", "4 트리 / 2 파이프라인 경로 / 신·구 분리");

  // Left: pipeline_local (active)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 6.1, h: 5.7,
    fill: { color: C.white }, line: { color: C.deep, width: 1.5 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 0.08, h: 5.7, fill: { color: C.deep }, line: { color: C.deep }
  });
  s.addText("pipeline_local/  (신, 정식 경로)", {
    x: 0.75, y: 1.3, w: 5.7, h: 0.4,
    fontFace: FONT_H, fontSize: 16, bold: true, color: C.deep, margin: 0
  });
  const pl = [
    { t: "orchestrator.py", d: "LocalPipelineOrchestrator · 5-Agent" },
    { t: "steps/step01_receptor.py", d: "OpenFold3 / data fallback" },
    { t: "steps/step02_backbone.py", d: "RFdiffusion (Silo A)" },
    { t: "steps/step03_proteinmpnn.py", d: "ProteinMPNN (Silo A)" },
    { t: "steps/step03b_blosum_mutation.py", d: "BLOSUM62 (Silo B)" },
    { t: "steps/step04_esmfold.py", d: "QC pLDDT" },
    { t: "steps/step05_docking.py", d: "Boltz-2 docking" },
    { t: "steps/step05b_selectivity.py", d: "PyRosetta off-target" },
    { t: "steps/step05c_boltz_cross.py", d: "Boltz-2 cross-validation" },
    { t: "steps/step06_rosetta.py", d: "PyRosetta FlexPepDock" },
    { t: "steps/step07_analysis.py", d: "FoldMason lDDT + InterfaceReport" },
    { t: "steps/step08_stability.py", d: "Half-life 추정 (HEURISTIC)" },
    { t: "scripts/pharmacology_guards.py", d: "9 HEURISTIC 함수 등록" },
    { t: "scripts/flexpepdock_worker.py", d: "FlexPepDock subprocess + stub fallback" },
  ];
  pl.forEach((row, i) => {
    const y = 1.85 + i * 0.34;
    s.addText(row.t, {
      x: 0.85, y, w: 2.8, h: 0.3,
      fontFace: "Consolas", fontSize: 10, bold: true, color: C.slate, margin: 0
    });
    s.addText(row.d, {
      x: 3.7, y, w: 2.85, h: 0.3,
      fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, margin: 0
    });
  });

  // Right: AG_src + backend (legacy + bridge)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 1.2, w: 6.0, h: 2.7,
    fill: { color: C.white }, line: { color: C.teal, width: 1.5 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 1.2, w: 0.08, h: 2.7, fill: { color: C.teal }, line: { color: C.teal }
  });
  s.addText("AG_src/  (구, 어댑터 축소)", {
    x: 7.05, y: 1.3, w: 5.7, h: 0.4,
    fontFace: FONT_H, fontSize: 16, bold: true, color: C.teal, margin: 0
  });
  const ag = [
    { t: "pipeline/orchestrator.py", d: "1400 LOC 레거시 (수렴 대상)" },
    { t: "agents/{planner,critic,...}.py", d: "5-Agent + FAILURE_ACTION_MAP" },
    { t: "llm/provider.py", d: "OllamaProvider :11435 · NoneProvider 폴백" },
    { t: "config/pipeline_config.yaml", d: "llm.base_url 11435 · qwen3:8b" },
    { t: "config/gate_thresholds.yaml", d: "구 부호 (-10.0) — 별건 정정" },
  ];
  ag.forEach((row, i) => {
    const y = 1.85 + i * 0.34;
    s.addText(row.t, {
      x: 7.15, y, w: 2.8, h: 0.3,
      fontFace: "Consolas", fontSize: 10, bold: true, color: C.slate, margin: 0
    });
    s.addText(row.d, {
      x: 9.95, y, w: 2.8, h: 0.3,
      fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, margin: 0
    });
  });

  // backend (active)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 4.05, w: 6.0, h: 2.85,
    fill: { color: C.white }, line: { color: C.midnight, width: 1.5 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 4.05, w: 0.08, h: 2.85, fill: { color: C.midnight }, line: { color: C.midnight }
  });
  s.addText("backend/  (FastAPI bridge)", {
    x: 7.05, y: 4.15, w: 5.7, h: 0.4,
    fontFace: FONT_H, fontSize: 16, bold: true, color: C.midnight, margin: 0
  });
  const be = [
    { t: "state.py", d: "STATUS_FILE + is_active_run · server_time (P03)" },
    { t: "status_emitter.py", d: "DEFAULT_STEPS 11개 · step06_baseline 분리" },
    { t: "routers/experiment.py", d: "Popen+P02 init · 3-way settings 폴백 (P09)" },
    { t: "routers/selectivity.py", d: "cancel endpoint (P11 soft) · 소문자 키" },
    { t: "routers/status.py", d: "_enrich_candidates on-the-fly 6 필드" },
    { t: "pharmacophore.py", d: "fwkt_contact · chelator_site (Phase 1 휴리스틱)" },
  ];
  be.forEach((row, i) => {
    const y = 4.6 + i * 0.36;
    s.addText(row.t, {
      x: 7.15, y, w: 2.6, h: 0.32,
      fontFace: "Consolas", fontSize: 10, bold: true, color: C.slate, margin: 0
    });
    s.addText(row.d, {
      x: 9.75, y, w: 3.0, h: 0.32,
      fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, margin: 0
    });
  });

  addPageNumber(s, 4, TOTAL);
}

// ============================================================
// Slide 5 — 더미/Mock/Placeholder 인벤토리 Top 15
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "더미 · Mock · Placeholder 인벤토리 (Top 15)", "Critical 3 · High 5 · Med 5 · Low 2");

  const items = [
    { sev: "Critical", c: C.critical, file: "scripts/flexpepdock_worker.py:516-538", what: "PyRosetta 미설치 시 _stub_dock_result(ddg 임의값) 반환", impl: "bio-tools env 보장 + CI 가동" },
    { sev: "Critical", c: C.critical, file: "pharmacology_guards.py:209-322", what: "9개 HEURISTIC 함수 (instability/gravy/fwkt/chelator 등)", impl: "Phase 2 PDB 거리 기반 + 실측 캘리브레이션" },
    { sev: "Critical", c: C.critical, file: "AG_src config gate_thresholds.yaml:37", what: "selectivity_margin_min -10.0 (옛 부호) — pipeline_local +10.0과 반대", impl: "yaml + 코드 동시 통일 (별건 PR)" },
    { sev: "High", c: C.high, file: "backend/pharmacophore.py compute_fwkt_contact", what: "Phase 1: 'FWKT' substring 매칭만 (구조 미고려)", impl: "PDB 거리 ≤4.5Å 기반 (PDB 7T11 pocket)" },
    { sev: "High", c: C.high, file: "backend/pharmacophore.py compute_chelator_site", what: "Phase 1: N-term/Lys 존재만, SS-bond 미정밀", impl: "Cys3-Cys14 disulfide 명시적 검사" },
    { sev: "High", c: C.high, file: "steps/step07_analysis.py:259,275,330", what: "FoldMason 실패 시 placeholder lDDT + BioPython 없으면 InterfaceReport stub", impl: "FoldMason 환경 정비 + Biopython 필수 의존성화" },
    { sev: "High", c: C.high, file: "unified_validation.py:308-315", what: "rank_stability/score_consistency/no_dominance 모두 passed=True, skipped=True", impl: "multi-run 데이터 축적 후 실 통계 검증" },
    { sev: "High", c: C.high, file: "Silo A 분기 (--no-approach-b)", what: "코드만 존재. RFdiffusion + ProteinMPNN 환경 미정비", impl: "환경 정비 + dogfood + 1회 실 호출" },
    { sev: "Med", c: C.med, file: "steps/step05_docking.py:211", what: "Boltz 실패 시 fallback dummy scores ([-i for i in range(len)])", impl: "재시도 + 명시 NaN + UI 표시" },
    { sev: "Med", c: C.med, file: "P11 selectivity cancel (soft only)", what: "subprocess timeout 600s 대기 — 즉시 cancel 불가", impl: "SelectivityRunner PID 노출 + os.killpg" },
    { sev: "Med", c: C.med, file: "pepadmet_infer_script.py:9-12", what: "mock_wv weight_visualization 모듈 (utility 미사용)", impl: "PepADMET 비활성 또는 진짜 utility 연결" },
    { sev: "Med", c: C.med, file: "bayesian_optimizer.py:134", what: "Optional ESM-2 Embedder stub (one-hot fallback)", impl: "ESM-2 모델 로드 + GPU 메모리 가드" },
    { sev: "Med", c: C.med, file: "yaml '단위' kcal/mol 레이블", what: "실제 Rosetta REU 가능성, 보고서에 단위 혼동", impl: "yaml \"kcal/mol\"→\"REU\" 정정 + 환산 계수 문서화" },
    { sev: "Low", c: C.low, file: "pyrosetta_flow/pdb_store.py:56", what: "pass 빈 함수 — 미구현 placeholder", impl: "PDB store 본격 구현 또는 제거" },
    { sev: "Low", c: C.low, file: "step07_analysis.py:325 buried_sasa", what: "25 Å² per residue stub (실 SASA 계산 미사용)", impl: "DSSP 또는 BioPython SASA" },
  ];

  // 3 columns x 5 rows
  const cols = 3;
  const rows = 5;
  const cardW = 4.15;
  const cardH = 1.07;
  const xStart = 0.45;
  const yStart = 1.2;
  const xGap = 0.05;
  const yGap = 0.08;

  items.slice(0, 15).forEach((it, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = xStart + col * (cardW + xGap);
    const y = yStart + row * (cardH + yGap);

    // card
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: C.muted, width: 0.5 }
    });
    // severity stripe
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.1, h: cardH, fill: { color: it.c }, line: { color: it.c }
    });
    // severity badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + cardW - 0.85, y: y + 0.08, w: 0.75, h: 0.22,
      fill: { color: it.c }, line: { color: it.c }
    });
    s.addText(it.sev, {
      x: x + cardW - 0.85, y: y + 0.08, w: 0.75, h: 0.22,
      fontFace: FONT_B, fontSize: 8, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
    // file path
    s.addText(it.file, {
      x: x + 0.2, y: y + 0.05, w: cardW - 1.1, h: 0.25,
      fontFace: "Consolas", fontSize: 8, bold: true, color: C.midnight, margin: 0
    });
    // what
    s.addText(it.what, {
      x: x + 0.2, y: y + 0.32, w: cardW - 0.3, h: 0.42,
      fontFace: FONT_B, fontSize: 9, color: C.slate, margin: 0
    });
    // implementation
    s.addText("→ " + it.impl, {
      x: x + 0.2, y: y + 0.76, w: cardW - 0.3, h: 0.28,
      fontFace: FONT_B, fontSize: 8.5, italic: true, color: C.deep, margin: 0
    });
  });

  addPageNumber(s, 5, TOTAL);
}

// ============================================================
// Slide 6 — 미구현 영역 Top 10
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "실제 구현 미완 영역 (Top 10)", "Endpoint·함수는 있지만 본격 사용/구현 안 됨");

  const items = [
    { p: "P1", c: C.high, area: "Silo A pipeline 환경", state: "code path는 분기 구현됨", todo: "RFdiffusion + ProteinMPNN 환경 정비 · 1회 dogfood · 실패 시 명시 fallback" },
    { p: "P1", c: C.high, area: "fwkt_contact Phase 2 (PDB 거리)", state: "Phase 1 substring 매칭만", todo: "PDB 7T11 pocket residue 거리 ≤4.5Å 계산 · 도킹 pose 입력 매핑" },
    { p: "P1", c: C.high, area: "chelator_site SS-bond 정밀", state: "N-term/Lys 단순 boolean", todo: "Cys3-Cys14 disulfide 명시 검증 · DOTA 측쇄 chelation 거리 모델" },
    { p: "P1", c: C.high, area: "metal_coordination SS-bond Cys 제외", state: "H/C 기반 n_strong에 SS-bond Cys 포함", todo: "Cys SS-bond 상태 검출 후 n_strong에서 제외 · pharmacology.py 별건 PR" },
    { p: "P2", c: C.med, area: "Selectivity 즉시 cancel", state: "soft cancel만 (luck timeout 600s)", todo: "SelectivityRunner PID 노출 · os.killpg + cleanup" },
    { p: "P2", c: C.med, area: "Real ESM-2 Embedder", state: "Optional stub (one-hot fallback)", todo: "ESM-2 모델 로드 · GPU 메모리 관리 · Bayesian optimizer 활용" },
    { p: "P2", c: C.med, area: "BLOSUM 모듈화 Phase 1", state: "step03b 단일 함수", todo: "strategy pattern으로 추출 · 다른 mutation algorithm 추가 가능" },
    { p: "P2", c: C.med, area: "Unified Validation 실 통계", state: "rank_stability 등 placeholder passed=True", todo: "multi-run 데이터 축적 후 Spearman ρ · KS test 구현" },
    { p: "P3", c: C.low, area: "Wetlab BE candidate_id 제한 풀기", state: "특정 cand 만 wetlab order 가능", todo: "Manual Selectivity 결과 → wetlab order 자동 통합" },
    { p: "P3", c: C.low, area: "VR-G2-01/02 검증 트랙 등록", state: "별도 sprint로 식별만", todo: "off-target 실측 1회 dogfood · yaml 단위 검증 문서" },
  ];

  const rows = [["P", "영역", "현재 상태", "완성 시 필요 작업"]];
  items.forEach(it => {
    rows.push([
      { text: it.p, options: { bold: true, color: C.white, fill: { color: it.c }, align: "center", valign: "middle" } },
      { text: it.area, options: { bold: true, color: C.midnight } },
      { text: it.state, options: { color: C.slate, italic: true } },
      { text: it.todo, options: { color: C.slate } },
    ]);
  });

  s.addTable(rows, {
    x: 0.5, y: 1.2, w: 12.3,
    fontSize: 10.5, fontFace: FONT_B,
    border: { pt: 0.5, color: C.muted },
    rowH: 0.5,
    colW: [0.6, 3.3, 3.4, 5.0],
    fill: { color: C.white },
  });

  // legend
  s.addText("P1 = High Priority · P2 = Medium · P3 = Low", {
    x: 0.5, y: 6.8, w: 12.3, h: 0.3,
    fontFace: FONT_B, fontSize: 10, italic: true, color: C.muted, margin: 0
  });

  addPageNumber(s, 6, TOTAL);
}

// ============================================================
// Slide 7 — 시스템 개선 방향 Top 8
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "시스템 개선 방향 (Top 8)", "단기 5 · 중기 2 · 장기 1 (영향도 × 구현비용 기준)");

  const items = [
    { time: "단기", c: C.info, area: "단위 정직성", cur: 'yaml "kcal/mol" 표기 vs 실 REU 가능성', fix: 'yaml 레이블 "REU" 정정 + 환산 계수 문서화', eff: "보고서 신뢰성 ↑" },
    { time: "단기", c: C.info, area: "HEURISTIC 뱃지 강화", cur: "9 함수 휴리스틱 — UI에 일관 노출 안 됨", fix: "ValidationPanel + Cluster + ADMET 화면에 HEURISTIC 배지 일괄", eff: "사용자 오해 차단" },
    { time: "단기", c: C.info, area: "STATUS_FILE 컨벤션 lock-in", cur: "P01로 통일됐으나 외부 자동 linter 의존", fix: "PIPELINE_STATUS_FILE env 명시 + start_monitoring.sh + docs lock", eff: "재분기 방지" },
    { time: "단기", c: C.info, area: "Test 커버리지 확장", cur: "pharmacophore/cluster/experiment만 커버", fix: "step03b/05/06/08 + integration smoke 추가", eff: "회귀 발견율 ↑" },
    { time: "단기", c: C.info, area: "다중 세션 충돌 방지", cur: "별도 세션 + 본 세션 동시 push merge 충돌", fix: "git pre-commit hook + PR 머지 lock + 세션 owner 명시", eff: "재작업 0" },
    { time: "중기", c: C.high, area: "Real-data Calibration", cur: "fwkt/chelator/instability 모두 in-silico 휴리스틱", fix: "SST-14 wild-type + 알려진 analog (DOTATATE, DOTANOC) 실 Ki ↔ 계산값 캘리브레이션", eff: "PRRT 임상 직접 환산 가능" },
    { time: "중기", c: C.high, area: "Silo A 통합 환경", cur: "RFdiffusion/ProteinMPNN/ESMFold/Boltz 분리 컨테이너", fix: "단일 conda env or Docker compose + GPU 스케줄링 + cache", eff: "재현성 + 운영 단순화" },
    { time: "장기", c: C.critical, area: "AG_src → pipeline_local 수렴", cur: "두 orchestrator 공존 (1400 LOC 레거시 + 신)", fix: "AG_src → adapter 축소 + pipeline_local 단일 진입", eff: "유지비 -50% · 일관성 ↑" },
  ];

  items.forEach((it, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 6.35;
    const y = 1.2 + row * 1.35;
    const cardW = 6.2;
    const cardH = 1.25;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: it.c, width: 1 }
    });
    // time badge
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 1.0, h: 0.3, fill: { color: it.c }, line: { color: it.c }
    });
    s.addText(it.time, {
      x, y, w: 1.0, h: 0.3,
      fontFace: FONT_B, fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
    // area
    s.addText(it.area, {
      x: x + 1.1, y, w: cardW - 1.2, h: 0.3,
      fontFace: FONT_H, fontSize: 13, bold: true, color: C.midnight, valign: "middle", margin: 0
    });
    // current
    s.addText("현재  " + it.cur, {
      x: x + 0.15, y: y + 0.36, w: cardW - 0.3, h: 0.28,
      fontFace: FONT_B, fontSize: 9.5, italic: true, color: C.slate, margin: 0
    });
    // fix
    s.addText("권장  " + it.fix, {
      x: x + 0.15, y: y + 0.66, w: cardW - 0.3, h: 0.3,
      fontFace: FONT_B, fontSize: 9.5, bold: true, color: C.deep, margin: 0
    });
    // effect
    s.addText("효과  " + it.eff, {
      x: x + 0.15, y: y + 0.98, w: cardW - 0.3, h: 0.24,
      fontFace: FONT_B, fontSize: 9.5, color: C.low, margin: 0
    });
  });

  addPageNumber(s, 7, TOTAL);
}

// ============================================================
// Slide 8 — 데이터 흐름 (UI → BE → orchestrator → step → emitter → status → UI)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "핵심 데이터 흐름", "UI Run 버튼 → 결과 표시까지 10 단계");

  const flow = [
    { n: "1", who: "FE", what: "POST /api/experiment/run", file: "useStartRun + RunLauncherPage.tsx:109", time: "<100ms" },
    { n: "2", who: "BE", what: "Popen subprocess + STATUS_FILE init", file: "experiment.py:161 + state.STATUS_FILE", time: "<200ms (P02)" },
    { n: "3", who: "BE", what: "run_pyrosetta_flow.py spawn", file: "subprocess.Popen + log redirect (P08)", time: "<1s" },
    { n: "4", who: "Pipeline", what: "Silo B: step01~05 skipped emit", file: "runner.py:534 emitter.update_step", time: "instant" },
    { n: "5", who: "Pipeline", what: "baseline FlexPepDock (step06_baseline)", file: "flexpep_dock.py · PyRosetta", time: "~60s × 3 trial" },
    { n: "6", who: "Pipeline", what: "iter 루프: BLOSUM → ESMFold → Boltz → PyRosetta refine", file: "step03b · step04 · step05 · step06", time: "~25min/iter" },
    { n: "7", who: "Agent", what: "QCRanker → Critic → Reporter (LLM + 규칙 폴백)", file: "agents/{qc_ranker,critic,reporter}.py", time: "~30s/iter" },
    { n: "8", who: "BE", what: "_enrich_candidates on-the-fly 6 필드 머지", file: "routers/status.py:58", time: "<50ms" },
    { n: "9", who: "BE", what: "/api/status read_status + is_active_run/server_time", file: "routers/status.py:get_status", time: "<10ms (cache hit)" },
    { n: "10", who: "FE", what: "isLive 4 상태 → 5 배지 + ClusterPanel 분류", file: "App.tsx + pipelineStateFlags.ts + ClusterPanel.tsx", time: "2s polling" },
  ];

  flow.forEach((step, i) => {
    const y = 1.2 + i * 0.54;
    // step number circle
    s.addShape(pres.shapes.OVAL, {
      x: 0.5, y, w: 0.45, h: 0.45,
      fill: { color: C.deep }, line: { color: C.teal, width: 0 }
    });
    s.addText(step.n, {
      x: 0.5, y, w: 0.45, h: 0.45,
      fontFace: FONT_H, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
    // who badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.1, y: y + 0.07, w: 1.1, h: 0.3,
      fill: { color: C.ice }, line: { color: C.teal, width: 0 }
    });
    s.addText(step.who, {
      x: 1.1, y: y + 0.07, w: 1.1, h: 0.3,
      fontFace: FONT_B, fontSize: 10, bold: true, color: C.midnight, align: "center", valign: "middle", margin: 0
    });
    // what
    s.addText(step.what, {
      x: 2.35, y: y + 0.05, w: 6.5, h: 0.34,
      fontFace: FONT_B, fontSize: 11.5, bold: true, color: C.midnight, margin: 0
    });
    // file
    s.addText(step.file, {
      x: 8.9, y: y + 0.07, w: 2.9, h: 0.3,
      fontFace: "Consolas", fontSize: 8.5, color: C.slate, margin: 0
    });
    // time
    s.addText(step.time, {
      x: 11.85, y: y + 0.07, w: 1.0, h: 0.3,
      fontFace: FONT_B, fontSize: 9.5, italic: true, color: C.low, align: "right", margin: 0
    });
    // connector arrow (except last)
    if (i < flow.length - 1) {
      s.addShape(pres.shapes.LINE, {
        x: 0.725, y: y + 0.45, w: 0, h: 0.09,
        line: { color: C.muted, width: 1.2, endArrowType: "triangle" }
      });
    }
  });

  addPageNumber(s, 8, TOTAL);
}

// ============================================================
// Slide 9 — 5-Agent 호출 시퀀스
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "5-Agent 호출 시퀀스 (per iteration)", "Planner → Builder → QCRanker → Critic → Reporter · LLM 분기 + 규칙 폴백");

  // 5 agent cards horizontal flow
  const agents = [
    { n: "1", name: "Planner", role: "Plan 생성 / 가설 수립", input: "previous_results · gate_thresholds · critic_feedback", output: "ExperimentPlan (parameters · gates · hypothesis)", llm: "LLM 60% / Rule 40%" },
    { n: "2", name: "Builder", role: "Step01~08 실행", input: "ExperimentPlan", output: "Candidates · StepResult", llm: "코드 only" },
    { n: "3", name: "QCRanker", role: "게이트 평가 / 랭킹", input: "Candidates list", output: "RankTable · QCReport (failure_breakdown)", llm: "코드 only" },
    { n: "4", name: "Critic", role: "실패 분석 → 변경 제안", input: "RankTable + QCReport (정규화 적용 P14)", output: "CriticAnalysis · ParameterChange ≤2", llm: "LLM 60% / Rule 40%" },
    { n: "5", name: "Reporter", role: "리포트 생성", input: "iter_results · plans · critics", output: "iter_report.md · final_report.md", llm: "LLM 60% / Rule 40%" },
  ];

  const cardW = 2.4;
  const cardH = 4.2;
  const cardY = 1.4;
  const xStart = 0.45;
  const gap = 0.13;

  agents.forEach((a, i) => {
    const x = xStart + i * (cardW + gap);
    // card
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: C.deep, width: 1.2 }
    });
    // header strip
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: 0.7, fill: { color: C.deep }, line: { color: C.deep }
    });
    s.addText(a.n, {
      x: x + 0.1, y: cardY + 0.05, w: 0.5, h: 0.6,
      fontFace: FONT_H, fontSize: 36, bold: true, color: C.ice, margin: 0
    });
    s.addText(a.name, {
      x: x + 0.65, y: cardY + 0.1, w: cardW - 0.7, h: 0.3,
      fontFace: FONT_H, fontSize: 16, bold: true, color: C.white, margin: 0
    });
    s.addText(a.role, {
      x: x + 0.65, y: cardY + 0.4, w: cardW - 0.7, h: 0.25,
      fontFace: FONT_B, fontSize: 9.5, italic: true, color: C.ice, margin: 0
    });
    // input section
    s.addText("INPUT", {
      x: x + 0.15, y: cardY + 0.85, w: cardW - 0.3, h: 0.22,
      fontFace: FONT_B, fontSize: 9, bold: true, color: C.teal, margin: 0
    });
    s.addText(a.input, {
      x: x + 0.15, y: cardY + 1.1, w: cardW - 0.3, h: 0.95,
      fontFace: FONT_B, fontSize: 9, color: C.slate, margin: 0
    });
    // output
    s.addText("OUTPUT", {
      x: x + 0.15, y: cardY + 2.1, w: cardW - 0.3, h: 0.22,
      fontFace: FONT_B, fontSize: 9, bold: true, color: C.teal, margin: 0
    });
    s.addText(a.output, {
      x: x + 0.15, y: cardY + 2.35, w: cardW - 0.3, h: 1.05,
      fontFace: FONT_B, fontSize: 9, color: C.slate, margin: 0
    });
    // llm
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.1, y: cardY + cardH - 0.5, w: cardW - 0.2, h: 0.35,
      fill: { color: C.ice }, line: { color: C.teal, width: 0 }
    });
    s.addText(a.llm, {
      x: x + 0.1, y: cardY + cardH - 0.5, w: cardW - 0.2, h: 0.35,
      fontFace: FONT_B, fontSize: 9, bold: true, color: C.midnight, align: "center", valign: "middle", margin: 0
    });
    // arrow to next
    if (i < agents.length - 1) {
      s.addShape(pres.shapes.LINE, {
        x: x + cardW, y: cardY + cardH / 2, w: gap, h: 0,
        line: { color: C.teal, width: 2, endArrowType: "triangle" }
      });
    }
  });

  // bottom callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.95, w: 12.3, h: 1.05,
    fill: { color: C.ice }, line: { color: C.teal, width: 0 }
  });
  s.addText("LLM 폴백 메커니즘", {
    x: 0.7, y: 6.05, w: 6, h: 0.3,
    fontFace: FONT_H, fontSize: 12, bold: true, color: C.midnight, margin: 0
  });
  s.addText("Ollama(qwen3:8b)가 실패 시 (timeout / API error) → rule-based 폴백 자동 진입. Critic은 P14 매핑 정규화 적용으로 정규 카테고리 매칭. Planner 폴백은 ExperimentPlan 기본 파라미터로 fallback. Reporter는 markdown 템플릿 사용.", {
    x: 0.7, y: 6.35, w: 11.9, h: 0.55,
    fontFace: FONT_B, fontSize: 10.5, color: C.slate, margin: 0
  });

  addPageNumber(s, 9, TOTAL);
}

// ============================================================
// Slide 10 — 라이브러리 상호작용 (15 핵심)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "라이브러리 상호작용 (15 핵심 노드)", "Python 9 · Frontend 4 · LLM/Infra 2");

  const libs = [
    // Pipeline core
    { n: "PyRosetta", cat: "Pipeline", c: C.deep, where: "step06_rosetta · flexpep_dock.py · selectivity (off-target)", deps: "bio-tools conda env" },
    { n: "Boltz-2", cat: "Pipeline", c: C.deep, where: "step05_docking · step05c_boltz_cross", deps: "Apptainer 또는 conda boltz · AF MSA cache" },
    { n: "ESMFold", cat: "Pipeline", c: C.deep, where: "step04 (pLDDT QC)", deps: "esm 모듈 + GPU" },
    { n: "ProteinMPNN", cat: "Pipeline", c: C.deep, where: "step03 (Silo A sequence design)", deps: "환경 미정비 [G-8]" },
    { n: "RFdiffusion", cat: "Pipeline", c: C.deep, where: "step02 (Silo A backbone)", deps: "환경 미정비 [G-8]" },
    { n: "FoldMason", cat: "Pipeline", c: C.deep, where: "step07_analysis (lDDT)", deps: "binary 외부 호출 · 실패 시 placeholder" },
    { n: "Biopython", cat: "Pipeline", c: C.deep, where: "step07 (Interface) · pharmacology (instability/GRAVY)", deps: "requirements 명시 (Tier 0 P08)" },
    { n: "peptides.py", cat: "Pipeline", c: C.deep, where: "pharmacology_guards 일부", deps: "v0.5.0 API 사용 (gravy 메서드 없음 - Biopython 사용)" },
    { n: "scikit-learn", cat: "Pipeline", c: C.deep, where: "pareto_ranking · 분포 통계", deps: "선택적, Bayesian optimizer 일부" },

    { n: "FastAPI", cat: "Backend", c: C.teal, where: "backend/main.py + routers/*", deps: "uvicorn + python-multipart (P08)" },
    { n: "Pydantic v2", cat: "Backend", c: C.teal, where: "router schemas · ExperimentRunRequest", deps: "FastAPI 통합" },

    { n: "React 19", cat: "Frontend", c: C.midnight, where: "frontend/src/* · pages 8개", deps: "TanStack Query · Recharts · Lucide" },
    { n: "TanStack Query", cat: "Frontend", c: C.midnight, where: "useStartRun · useSettings · useSelectivity · useCandidates", deps: "polling 2s · cache 30s" },
    { n: "Vite", cat: "Frontend", c: C.midnight, where: "frontend dev server + production build", deps: "HMR + tsc 빌드" },

    { n: "Ollama (qwen3:8b)", cat: "LLM/Infra", c: C.critical, where: "Critic · Planner · Reporter LLM 분기 · OllamaProvider :11435", deps: "OLLAMA_HOST env + GPU" },
  ];

  // 3 columns x 5 rows
  const cols = 3;
  const cardW = 4.15;
  const cardH = 1.05;
  const xStart = 0.45;
  const yStart = 1.2;
  const xGap = 0.05;
  const yGap = 0.08;

  libs.forEach((it, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = xStart + col * (cardW + xGap);
    const y = yStart + row * (cardH + yGap);

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: it.c, width: 0.75 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: cardH, fill: { color: it.c }, line: { color: it.c }
    });
    // name
    s.addText(it.n, {
      x: x + 0.2, y: y + 0.05, w: cardW - 1.0, h: 0.3,
      fontFace: FONT_H, fontSize: 13, bold: true, color: C.midnight, margin: 0
    });
    // category badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + cardW - 0.95, y: y + 0.08, w: 0.85, h: 0.22,
      fill: { color: it.c }, line: { color: it.c }
    });
    s.addText(it.cat, {
      x: x + cardW - 0.95, y: y + 0.08, w: 0.85, h: 0.22,
      fontFace: FONT_B, fontSize: 8, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
    // where
    s.addText(it.where, {
      x: x + 0.2, y: y + 0.38, w: cardW - 0.3, h: 0.42,
      fontFace: FONT_B, fontSize: 9, color: C.slate, margin: 0
    });
    // deps
    s.addText("⚙ " + it.deps, {
      x: x + 0.2, y: y + 0.79, w: cardW - 0.3, h: 0.24,
      fontFace: FONT_B, fontSize: 8.5, italic: true, color: C.deep, margin: 0
    });
  });

  addPageNumber(s, 10, TOTAL);
}

// ============================================================
// Slide 11 — 툴 시퀀스 (5 시나리오)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "툴 시퀀스 (5 시나리오)", "Silo A · Silo B · Combined · Selectivity · Cluster Classification");

  const scenarios = [
    {
      name: "Silo A (de novo)",
      color: C.high,
      status: "⚠ 환경 미정비 (G-8)",
      seq: ["step01 OpenFold3", "step02 RFdiffusion", "step03 ProteinMPNN", "step04 ESMFold QC", "step05 Boltz-2 dock", "step06 PyRosetta refine", "step07 FoldMason lDDT", "step08 stability"]
    },
    {
      name: "Silo B (mutation, 활성)",
      color: C.low,
      status: "✓ Production 가동",
      seq: ["step01 OpenFold3 / data fallback", "[skip step02·03]", "step03b BLOSUM62 mutation", "step04 ESMFold QC", "step05 Boltz-2 dock", "step06_baseline FlexPepDock", "step06 PyRosetta refine", "step07 + step08"]
    },
    {
      name: "Combined (dual)",
      color: C.high,
      status: "⚠ regex로 차단됨 (Tier 0 P10)",
      seq: ["--dual flag", "Silo A 병렬", "Silo B 병렬", "결과 머지 (diverse_top)", "step06 통합 refine", "step07 + step08", "리포트 통합"]
    },
    {
      name: "Selectivity (PyRosetta off-target)",
      color: C.info,
      status: "✓ Tier 0 P11 cancel · P14 hotfix",
      seq: ["POST /api/selectivity/run", "후보별 PyRosetta dock vs SSTR1/3/4/5", "margin = worst_ot - sstr2 (+ = 선택적)", "gate: margin≥10 & worst_ot≥-15", "_enrich offtarget_max_receptor"]
    },
    {
      name: "Cluster Classification (A~E)",
      color: C.info,
      status: "✓ Tier 1 P05 6필드 머지",
      seq: ["POST /api/cluster/classify (candidates 6필드)", "cluster_report.batch_classify", "criteria A (fwkt_contact 등) · B (selectivity) · C (stability) · D (chelator)", "Tier A~E 할당 + 통계"]
    },
  ];

  // Vertical list: scenarios as expandable rows
  const cardH = 1.05;
  const cardW = 12.3;
  const xStart = 0.5;
  const yStart = 1.2;
  const yGap = 0.09;

  scenarios.forEach((sc, i) => {
    const y = yStart + i * (cardH + yGap);

    s.addShape(pres.shapes.RECTANGLE, {
      x: xStart, y, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: sc.color, width: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: xStart, y, w: 0.08, h: cardH, fill: { color: sc.color }, line: { color: sc.color }
    });
    // name + status
    s.addText(sc.name, {
      x: xStart + 0.2, y: y + 0.08, w: 5.0, h: 0.32,
      fontFace: FONT_H, fontSize: 14, bold: true, color: C.midnight, margin: 0
    });
    s.addText(sc.status, {
      x: xStart + 5.2, y: y + 0.08, w: 7.0, h: 0.32,
      fontFace: FONT_B, fontSize: 11, italic: true, color: sc.color, margin: 0
    });
    // sequence as chips
    const chipText = sc.seq.map((step, k) => (k > 0 ? "→  " : "") + step).join("    ");
    s.addText(chipText, {
      x: xStart + 0.2, y: y + 0.42, w: cardW - 0.3, h: cardH - 0.5,
      fontFace: "Consolas", fontSize: 10, color: C.slate, margin: 0
    });
  });

  addPageNumber(s, 11, TOTAL);
}

// ============================================================
// Slide 12 — 시스템 구조도 (정밀, 컴포넌트 그래프)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "시스템 구조도 (정밀)", "컴포넌트 노드 · 데이터 경로 · 외부 의존성");

  // Three swim lanes: FE (top) / BE (mid) / Pipeline (bottom)
  // Lane backgrounds
  const lanes = [
    { y: 1.2, h: 1.85, name: "Frontend", c: C.midnight },
    { y: 3.15, h: 1.85, name: "Backend API", c: C.teal },
    { y: 5.10, h: 1.85, name: "Pipeline + LLM", c: C.deep },
  ];
  lanes.forEach((L) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y: L.y, w: 12.5, h: L.h,
      fill: { color: C.cream }, line: { color: L.c, width: 0.5 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y: L.y, w: 0.15, h: L.h, fill: { color: L.c }, line: { color: L.c }
    });
    s.addText(L.name, {
      x: 0.62, y: L.y + 0.05, w: 3.0, h: 0.3,
      fontFace: FONT_H, fontSize: 11, bold: true, color: L.c, margin: 0
    });
  });

  // FE nodes
  const feNodes = [
    { x: 0.9, y: 1.55, w: 1.6, h: 1.3, name: "App.tsx", sub: "isLive 4 상태\n5 배지" },
    { x: 2.7, y: 1.55, w: 1.7, h: 1.3, name: "PipelineContext", sub: "usePipelineStatus\npolling 2s" },
    { x: 4.6, y: 1.55, w: 1.7, h: 1.3, name: "Run Console", sub: "useCandidates\nuseAgentLog SSE" },
    { x: 6.5, y: 1.55, w: 1.9, h: 1.3, name: "Selectivity Explorer", sub: "useSelectivity\nHeatmap + Molstar" },
    { x: 8.6, y: 1.55, w: 1.8, h: 1.3, name: "ClusterPanel", sub: "POST /cluster/classify\n6 필드 payload" },
    { x: 10.6, y: 1.55, w: 2.2, h: 1.3, name: "ValidationPanel", sub: "Skipped 뱃지 · aria-label\nrank/score/dominance" },
  ];
  feNodes.forEach(n => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: n.x, y: n.y, w: n.w, h: n.h,
      fill: { color: C.white }, line: { color: C.midnight, width: 1 }
    });
    s.addText(n.name, {
      x: n.x + 0.1, y: n.y + 0.1, w: n.w - 0.2, h: 0.4,
      fontFace: FONT_H, fontSize: 11, bold: true, color: C.midnight, margin: 0
    });
    s.addText(n.sub, {
      x: n.x + 0.1, y: n.y + 0.5, w: n.w - 0.2, h: 0.7,
      fontFace: FONT_B, fontSize: 8.5, color: C.slate, italic: true, margin: 0
    });
  });

  // BE nodes
  const beNodes = [
    { x: 0.9, y: 3.45, w: 1.7, h: 1.3, name: "state.py", sub: "STATUS_FILE · cache\n_with_runtime_fields" },
    { x: 2.8, y: 3.45, w: 1.7, h: 1.3, name: "routers/status.py", sub: "_enrich_candidates\n6필드 머지" },
    { x: 4.7, y: 3.45, w: 1.9, h: 1.3, name: "routers/experiment.py", sub: "Popen · STATUS init\n3-way settings" },
    { x: 6.8, y: 3.45, w: 1.9, h: 1.3, name: "routers/selectivity.py", sub: "run · cancel\n_jobs lock + soft cancel" },
    { x: 8.9, y: 3.45, w: 1.5, h: 1.3, name: "pharmacophore.py", sub: "fwkt_contact\nchelator_site" },
    { x: 10.6, y: 3.45, w: 2.2, h: 1.3, name: "status_emitter.py", sub: "DEFAULT_STEPS\nstep06_baseline 분리" },
  ];
  beNodes.forEach(n => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: n.x, y: n.y, w: n.w, h: n.h,
      fill: { color: C.white }, line: { color: C.teal, width: 1 }
    });
    s.addText(n.name, {
      x: n.x + 0.1, y: n.y + 0.1, w: n.w - 0.2, h: 0.4,
      fontFace: FONT_H, fontSize: 11, bold: true, color: C.teal, margin: 0
    });
    s.addText(n.sub, {
      x: n.x + 0.1, y: n.y + 0.5, w: n.w - 0.2, h: 0.7,
      fontFace: FONT_B, fontSize: 8.5, color: C.slate, italic: true, margin: 0
    });
  });

  // Pipeline nodes
  const plNodes = [
    { x: 0.9, y: 5.4, w: 1.6, h: 1.3, name: "orchestrator", sub: "5-Agent · step01~08\nrule fallback" },
    { x: 2.7, y: 5.4, w: 1.5, h: 1.3, name: "step03b BLOSUM", sub: "변이 후보 생성\n(Silo B)" },
    { x: 4.4, y: 5.4, w: 1.4, h: 1.3, name: "step04 ESMFold", sub: "pLDDT · pTM\n(GPU)" },
    { x: 6.0, y: 5.4, w: 1.5, h: 1.3, name: "step05 Boltz-2", sub: "iPTM · pose\n(AF MSA cache)" },
    { x: 7.7, y: 5.4, w: 1.7, h: 1.3, name: "step06 PyRosetta", sub: "FlexPepDock · ddG\nbio-tools env" },
    { x: 9.6, y: 5.4, w: 1.4, h: 1.3, name: "step07/08", sub: "FoldMason · half-life\nstability" },
    { x: 11.2, y: 5.4, w: 1.6, h: 1.3, name: "Ollama qwen3:8b", sub: ":11435 · GPU 2,3\nLLM 분기" },
  ];
  plNodes.forEach(n => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: n.x, y: n.y, w: n.w, h: n.h,
      fill: { color: C.white }, line: { color: C.deep, width: 1 }
    });
    s.addText(n.name, {
      x: n.x + 0.1, y: n.y + 0.1, w: n.w - 0.2, h: 0.4,
      fontFace: FONT_H, fontSize: 11, bold: true, color: C.deep, margin: 0
    });
    s.addText(n.sub, {
      x: n.x + 0.1, y: n.y + 0.5, w: n.w - 0.2, h: 0.7,
      fontFace: FONT_B, fontSize: 8.5, color: C.slate, italic: true, margin: 0
    });
  });

  // Cross-lane arrows (key flows)
  // FE PipelineContext → BE state.py (polling)
  s.addShape(pres.shapes.LINE, {
    x: 3.55, y: 2.85, w: 0, h: 0.6,
    line: { color: C.midnight, width: 1.5, endArrowType: "triangle" }
  });
  s.addText("polling 2s", {
    x: 3.65, y: 2.95, w: 1.2, h: 0.25, fontFace: FONT_B, fontSize: 8, italic: true, color: C.muted, margin: 0
  });

  // BE experiment.py → Pipeline orchestrator
  s.addShape(pres.shapes.LINE, {
    x: 5.65, y: 4.75, w: -4.0, h: 0.65,
    line: { color: C.teal, width: 1.5, endArrowType: "triangle" }
  });
  s.addText("Popen", {
    x: 3.0, y: 4.78, w: 1.0, h: 0.25, fontFace: FONT_B, fontSize: 8, italic: true, color: C.muted, margin: 0
  });

  // Pipeline orchestrator → Ollama
  s.addShape(pres.shapes.LINE, {
    x: 2.5, y: 6.05, w: 8.7, h: 0,
    line: { color: C.deep, width: 1.5, endArrowType: "triangle", dashType: "dash" }
  });

  addPageNumber(s, 12, TOTAL);
}

// ============================================================
// Slide 13 — 권장 로드맵 (단기/중기/장기)
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "권장 로드맵", "단기 (오늘~1주) · 중기 (1개월) · 장기 (분기)");

  const phases = [
    {
      title: "단기  ·  오늘 ~ 1주",
      c: C.info,
      items: [
        "G-2 yaml 단위 정정 (kcal/mol → REU) · 1줄 + 문서",
        "Silo A dogfood (G-5/G-8) · env 정비 + 1회 실 호출",
        "fwkt_contact Phase 2 (PDB 거리 ≤4.5Å)",
        "metal_coordination SS-bond Cys 제외 (별건 PR)",
        "HEURISTIC 뱃지 UI 일괄 노출",
      ],
    },
    {
      title: "중기  ·  1개월",
      c: C.high,
      items: [
        "Real-data calibration: SST-14 + DOTATATE/DOTANOC 실 Ki 매칭",
        "Silo A 통합 환경 (Docker compose + GPU 스케줄러)",
        "BLOSUM 모듈화 (strategy pattern + 추가 algorithm)",
        "Unified Validation 실 통계 (Spearman ρ, KS test)",
        "Selectivity 즉시 cancel (PID kill) · BE 리팩토링",
      ],
    },
    {
      title: "장기  ·  분기",
      c: C.critical,
      items: [
        "AG_src → pipeline_local 수렴 (1400 LOC 레거시 → adapter)",
        "다중 세션 컨벤션 lock-in · git hook · CI lock",
        "BO + NSGA-II 통합 (ESM-2 embedder 실 모델)",
        "wet-lab 후보 자동 추천 → in-vitro Ki 검증 사이클",
      ],
    },
  ];

  phases.forEach((p, i) => {
    const x = 0.5 + i * 4.2;
    const y = 1.2;
    const w = 4.05;
    const h = 5.7;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: C.white }, line: { color: p.c, width: 1.2 }
    });
    // header
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.7, fill: { color: p.c }, line: { color: p.c }
    });
    s.addText(p.title, {
      x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.4,
      fontFace: FONT_H, fontSize: 15, bold: true, color: C.white, margin: 0
    });

    // items as bulleted list
    const bulletItems = p.items.map((it, k) => ({
      text: it,
      options: { bullet: true, breakLine: k < p.items.length - 1, fontSize: 11, color: C.slate }
    }));
    s.addText(bulletItems, {
      x: x + 0.2, y: y + 0.95, w: w - 0.4, h: h - 1.1,
      fontFace: FONT_B,
    });
  });

  addPageNumber(s, 13, TOTAL);
}

// ============================================================
// Slide 14 — Closing
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.9, w: 13.3, h: 0.06, fill: { color: C.teal }, line: { color: C.teal }
  });

  s.addText("Closing · 다음 결정", {
    x: 0.8, y: 0.7, w: 12, h: 0.7,
    fontFace: FONT_H, fontSize: 38, bold: true, color: C.white, margin: 0
  });

  // 3 columns: 즉시 / 결정 게이트 / 검증 트랙
  const cols = [
    {
      title: "즉시 실행 (오늘)",
      c: C.info,
      items: [
        "G-2 yaml 단위 정정",
        "Silo A dogfood 환경 점검",
        "회귀 #4/#8 시각 검증 (사용자)",
      ],
    },
    {
      title: "결정 게이트",
      c: C.high,
      items: [
        "G-5/G-8 Silo A 활성 vs Coming Soon",
        "fwkt_contact Phase 2 sprint 시작",
        "Real-data calibration 우선순위",
        "AG_src 수렴 일정 확정",
      ],
    },
    {
      title: "검증 트랙",
      c: C.critical,
      items: [
        "VR-G2-01 off-target 실측",
        "VR-G2-02 yaml 단위 검증",
        "VR-cycle 5 항목 closure",
        "다음 sprint EOD 보고서",
      ],
    },
  ];

  cols.forEach((col, i) => {
    const x = 0.8 + i * 4.05;
    const y = 2.0;
    const w = 3.9;
    const h = 4.3;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: C.deep }, line: { color: col.c, width: 0 }
    });
    // accent strip on top
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.08, fill: { color: col.c }, line: { color: col.c }
    });
    s.addText(col.title, {
      x: x + 0.25, y: y + 0.2, w: w - 0.5, h: 0.55,
      fontFace: FONT_H, fontSize: 18, bold: true, color: C.white, margin: 0
    });
    // items
    const bulletItems = col.items.map((it, k) => ({
      text: it,
      options: { bullet: true, breakLine: k < col.items.length - 1, fontSize: 13, color: C.ice }
    }));
    s.addText(bulletItems, {
      x: x + 0.25, y: y + 0.95, w: w - 0.5, h: h - 1.1,
      fontFace: FONT_B,
    });
  });

  // bottom signature
  s.addText("orchestrator-session  ·  2026-05-19  ·  DAG v2.1 Tier 0+1 적용 상태", {
    x: 0.8, y: 6.65, w: 12, h: 0.3,
    fontFace: FONT_B, fontSize: 12, color: C.muted, italic: true, margin: 0
  });
  s.addText("관련 문서  _workspace/release/eod-2026-05-14-dag-v21-execution.md  ·  liverun-integration-analysis-v2-2026-05-13.md", {
    x: 0.8, y: 6.95, w: 12, h: 0.3,
    fontFace: FONT_B, fontSize: 9, color: C.muted, italic: true, margin: 0
  });
}

// ============================================================
// Save
// ============================================================
pres.writeFile({ fileName: "sstr2-pipeline-analysis-2026-05-19.pptx" })
  .then(name => console.log("created:", name))
  .catch(err => { console.error("ERR:", err); process.exit(1); });
