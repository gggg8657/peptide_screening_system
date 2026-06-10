// 시스템 점검 · Action Items 분석 · 반영 계획 · 종합 의견 발표자료 + 부록
// 디자인 시스템: docs/meet_preparation/assets/design_system.md 토큰을 헬퍼로 공유
// 회의록 출처: KAERI-AIRL-MOM-2026-003 (2026-04-06)

const pptxgen = require("pptxgenjs");

// ===== 디자인 토큰 (assets/design_system.md §1-3) =====
const C = {
  bg: "F2F2F2", bgDark: "1E2A36", bgElev: "FFFFFF",
  text: "1E293B", textOnDark: "FFFFFF", muted: "64748B",
  border: "CBD5E1",
  accent: "028090", accentLight: "00A896",
  good: "27AE60", warn: "D68910", crit: "C0392B", info: "2980B9",
  // 영역색
  domBE: "0E7C7B", domFE: "7B2D8E", domAI: "2E4D8F",
  domMCP: "B45309", domTool: "D97706", domVLLM: "5B21B6",
  domDock: "0891B2", domSiloA: "1D4ED8", domSiloB: "15803D",
  domDual: "BE123C",
};

// ===== 공통 헬퍼 (두 PPT 공유) =====
function addFooter(s, label, n, total) {
  s.addText([
    { text: label, options: { color: C.muted, fontSize: 9 } },
    { text: " · 2026-06-01 · 초안 보고", options: { color: C.muted, fontSize: 9 } },
    { text: `        ${n} / ${total}`, options: { color: C.muted, fontSize: 9 } },
  ], { x: 0.5, y: 7.05, w: 12.3, h: 0.3, fontFace: "Calibri", margin: 0, valign: "middle" });
}

function addSideBar(s, color = C.accent) {
  s.addShape("rect", { x: 0, y: 0.6, w: 0.08, h: 6.3, fill: { color }, line: { color, width: 0 } });
}

function addTitle(s, title, subtitle) {
  s.addText(title, {
    x: 0.4, y: 0.3, w: 12.5, h: 0.7,
    fontFace: "Cambria", fontSize: 26, bold: true, color: C.text, margin: 0, valign: "middle",
  });
  if (subtitle) s.addText(subtitle, {
    x: 0.4, y: 0.95, w: 12.5, h: 0.35,
    fontFace: "Calibri", fontSize: 13, color: C.muted, margin: 0, valign: "middle",
  });
}

function statusBadge(s, x, y, status, label) {
  const colors = { good: C.good, warn: C.warn, crit: C.crit, info: C.info, neutral: C.muted };
  const color = colors[status] || C.muted;
  s.addShape("ellipse", { x, y: y + 0.05, w: 0.18, h: 0.18, fill: { color }, line: { color, width: 0 } });
  s.addText(label, { x: x + 0.25, y, w: 8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0, valign: "middle" });
}

function titleSlide(pres, title, subtitle, meta) {
  const s = pres.addSlide();
  s.background = { color: C.bgDark };
  s.addShape("rect", { x: 12.7, y: 0, w: 0.6, h: 7.5, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
  s.addText(title, { x: 0.8, y: 2.3, w: 11.5, h: 1.0, fontFace: "Cambria", fontSize: 44, bold: true, color: C.textOnDark, margin: 0 });
  s.addText(subtitle, { x: 0.8, y: 3.3, w: 11.5, h: 0.7, fontFace: "Cambria", fontSize: 28, color: C.accentLight, margin: 0 });
  s.addText("SST14-M_scr · SSTR2 방사성의약품 후보 스크리닝 파이프라인", { x: 0.8, y: 4.5, w: 11.5, h: 0.5, fontFace: "Calibri", fontSize: 14, color: "B0BEC5", margin: 0 });
  s.addText([
    { text: "초안 보고 / 현재 상태 공유", options: { color: C.textOnDark, fontSize: 13 } },
    { text: "  ·  ", options: { color: C.muted } },
    { text: "최종 성과 발표 아님", options: { color: "FFB74D", fontSize: 13, italic: true } },
  ], { x: 0.8, y: 5.2, w: 11.5, h: 0.4, fontFace: "Calibri", margin: 0 });
  s.addText(meta, { x: 0.8, y: 6.6, w: 11.5, h: 0.4, fontFace: "Calibri", fontSize: 11, color: "B0BEC5", margin: 0 });
  return s;
}

function legend(s, x, y) {
  // 영역색 범례 (§7-0-3 그리드 §9)
  const items = [
    ["BE", C.domBE], ["FE", C.domFE], ["AI", C.domAI],
    ["Docking", C.domDock], ["Silo A", C.domSiloA], ["Silo B", C.domSiloB], ["Dual", C.domDual],
  ];
  items.forEach(([lab, col], i) => {
    s.addShape("rect", { x: x + i * 1.3, y, w: 0.15, h: 0.15, fill: { color: col }, line: { color: col, width: 0 } });
    s.addText(lab, { x: x + i * 1.3 + 0.2, y: y - 0.05, w: 1.1, h: 0.25, fontFace: "Calibri", fontSize: 8.5, color: C.muted, margin: 0, valign: "middle" });
  });
}

// ===================================================================
// MAIN PPTX (18 슬라이드)
// ===================================================================
function buildMain() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "orchestrator session";
  pres.title = "시스템 점검 + Action Items 분석 + 종합 의견 (메인) — 2026-06-01";
  const TOTAL = 18;
  const LBL = "메인 발표 — 초안";

  // === S1 Title ===
  titleSlide(pres, "시스템 점검 + Action Items 분석", "그리고 종합 향후 의견",
    "KAERI-AIRL-MOM-2026-003 (2026-04-06) Action Items 9건 + 본 점검 신규 발견 통합 · 2026-06-01");

  // === S2 오늘 보고 목적 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "오늘 보고의 목적", "회의록 ↔ 현재 코드 정합 · 격차 식별 · 6월 회의 안건 정리");

    const purposes = [
      ["1", "4/6 회의 Action Items 9건 정합 평가", "원본 요청 ↔ 현재 대응의 5블록 비교"],
      ["2", "데모 라이브 시연 가능 여부 판정", "서비스 가동 ≠ 파이프라인 완주"],
      ["3", "본 점검 신규 발견 3건 노출", "K-1/K-2 selectivity · Silo C 격차 · Dual 종단 0건"],
      ["4", "6월 회의 의사결정 안건 정리", "P0 6건 · P1 8건 · P2 3건"],
      ["5", "박사 청자에 과장·은폐 없이 전달", "정직한 framework — 한계 노출 정신"],
    ];
    purposes.forEach(([n, h, d], i) => {
      const y = 1.5 + i * 1.05;
      s.addShape("ellipse", { x: 0.6, y: y + 0.1, w: 0.55, h: 0.55, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
      s.addText(n, { x: 0.6, y: y + 0.1, w: 0.55, h: 0.55, fontFace: "Cambria", fontSize: 20, bold: true, color: C.textOnDark, align: "center", valign: "middle", margin: 0 });
      s.addText(h, { x: 1.4, y, w: 11, h: 0.4, fontFace: "Calibri", fontSize: 16, bold: true, color: C.text, margin: 0, valign: "middle" });
      s.addText(d, { x: 1.4, y: y + 0.4, w: 11, h: 0.4, fontFace: "Calibri", fontSize: 12, color: C.muted, italic: true, margin: 0, valign: "middle" });
    });
    addFooter(s, LBL, 2, TOTAL);
  }

  // === S3 전체 시스템 한 장 요약 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "전체 시스템 한 장 요약", "21 라우터 · 16 페이지 · 4d 16h vLLM · 워커 4 idle · Dual 종단 검증 0건");

    // 상부 3 row: UI / BE / AI
    function bar(y, color, h, sub) {
      s.addShape("rect", { x: 0.6, y, w: 12.0, h: 0.8, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x: 0.6, y, w: 0.1, h: 0.8, fill: { color }, line: { color, width: 0 } });
      s.addText(h, { x: 0.85, y: y + 0.05, w: 11.5, h: 0.3, fontFace: "Calibri", fontSize: 14, bold: true, color: C.text, margin: 0 });
      s.addText(sub, { x: 0.85, y: y + 0.35, w: 11.5, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.muted, margin: 0 });
    }
    bar(1.4, C.domFE, "Frontend — React 19 + Vite :5173", "16 페이지 lazy-load · TanStack Query + Zustand · HTTP 200");
    bar(2.4, C.domBE, "Backend — FastAPI :8787", "21 라우터 / 81 엔드포인트 · /api/health 200 · silo_a 라우터만 라이브 404");

    // 하단 4 카드 (AI, Silo A, Silo B, Dual)
    function card(x, y, col, h, sub) {
      s.addShape("rect", { x, y, w: 5.9, h: 1.5, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x, y, w: 0.1, h: 1.5, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(h, { x: x + 0.25, y: y + 0.05, w: 5.5, h: 0.35, fontFace: "Calibri", fontSize: 13, bold: true, color: C.text, margin: 0 });
      s.addText(sub, { x: x + 0.25, y: y + 0.4, w: 5.5, h: 1.1, fontFace: "Calibri", fontSize: 10.5, color: C.muted, margin: 0 });
    }
    card(0.6, 3.4, C.domAI, "AI / LLM  🟢",
      "vLLM :8002 deepseek-r1-distill-32b · GPU 3 83GB · uptime 4d 16h\n5+1 Agent: planner/builder/critic/qc_ranker/reporter/diversity_manager");
    card(6.7, 3.4, C.domSiloA, "Silo A — 3-Arm NIM  🔴",
      "Arm1 MolMIM→DiffDock · Arm2 FlexPepDock · Arm3 RFdiffusion→ProteinMPNN→ESMFold\n실 실행 0건 (NIM 키 부재) + 로컬 1-Arm 축약판 공존");
    card(0.6, 5.0, C.domSiloB, "Silo B — PyRosetta mutation+dock  🟡",
      "step01~08 + Gate 4종 · FlexPepDock 워커 4 idle\n3-Layer Ensemble (L1 PlifePred · L2 pepMSND R²=0.022 · ★L3 STUB)");
    card(6.7, 5.0, C.domDual, "Dual-silo Orchestration  🔴",
      "aggregator.rank_fusion   A:0.34 / B:0.33 / C:0.33\n--dual 기본 False · 종단 검증 기록 0건 · Silo C 구현 없음");

    legend(s, 0.6, 6.85);
    addFooter(s, LBL, 3, TOTAL);
  }

  // === S4 사용자 워크플로 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "사용자 / 연구자 워크플로 (검증된 흐름)", "후보 디자인 → 평가 → 검토 → wet-lab 주문");

    const steps = [
      ["1", "Run 시작", "/run/new", "RunLauncherPage — config + 전략 선택"],
      ["2", "실행 모니터링", "/console", "RunConsolePage — 2s 폴링 (usePipelineStatus)"],
      ["3", "후보 검토", "/candidate/:id", "Mol* 3D · Sequence · ADMET"],
      ["4", "선택성 비교", "/selectivity-explorer", "SSTR1/3/4/5 ⊿G 매트릭스"],
      ["5", "Wet-lab 주문", "/wetlab/orders/:id", "WetlabOrderPage — in-vitro 의뢰서"],
    ];
    steps.forEach(([n, lab, path, desc], i) => {
      const y = 1.5 + i * 1.05;
      s.addShape("ellipse", { x: 0.6, y: y + 0.1, w: 0.55, h: 0.55, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
      s.addText(n, { x: 0.6, y: y + 0.1, w: 0.55, h: 0.55, fontFace: "Cambria", fontSize: 18, bold: true, color: C.textOnDark, align: "center", valign: "middle", margin: 0 });
      s.addText(lab, { x: 1.4, y, w: 3.5, h: 0.35, fontFace: "Calibri", fontSize: 14, bold: true, color: C.text, margin: 0, valign: "middle" });
      s.addText(path, { x: 5.0, y, w: 3.5, h: 0.35, fontFace: "Consolas", fontSize: 11, color: C.accent, margin: 0, valign: "middle" });
      s.addText(desc, { x: 1.4, y: y + 0.4, w: 11, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.muted, margin: 0, valign: "middle" });
    });
    s.addText("★ 라이브: curl :5173/ → 200, curl :8787/api/health → {\"status\":\"ok\",\"mode\":\"local\"}",
      { x: 0.6, y: 6.65, w: 12.5, h: 0.3, fontFace: "Calibri", fontSize: 10, italic: true, color: C.muted, margin: 0 });
    addFooter(s, LBL, 4, TOTAL);
  }

  // === S5 BE/FE 상태 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "Backend · Frontend 상태", "21 라우터 81 엔드포인트 / 16 페이지 lazy-load");

    function card(x, col, h) {
      s.addShape("rect", { x, y: 1.5, w: 6.0, h: 5.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x, y: 1.5, w: 0.08, h: 5.0, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(h, { x: x + 0.25, y: 1.6, w: 5.5, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: C.text, margin: 0 });
      return x + 0.25;
    }
    let bx = card(0.6, C.domBE, "Backend (FastAPI :8787)");
    statusBadge(s, bx, 2.1, "good", "21 라우터 81 엔드포인트, /api/health 200");
    statusBadge(s, bx, 2.5, "good", "전역 예외 핸들러 3종 등록 완료");
    statusBadge(s, bx, 2.9, "good", "fastapi 0.135.1 · uvicorn 0.41.0 · pydantic 2.12.5");
    statusBadge(s, bx, 3.3, "crit", "/api/v1/silo-a/health 라이브 404");
    statusBadge(s, bx, 3.7, "warn", "파일 기반 JSON 상태 관리 (단일 인스턴스)");
    statusBadge(s, bx, 4.1, "warn", "FlexPep 잡 큐 18개 history, 1건 사용자 취소");
    s.addText("핵심 엔드포인트", { x: bx, y: 4.6, w: 5.5, h: 0.3, fontFace: "Calibri", fontSize: 12, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "GET /api/health · /api/status · /api/runs", options: { color: C.muted, fontSize: 10, breakLine: true } },
      { text: "POST /api/experiment/run · /api/flexpepdock", options: { color: C.muted, fontSize: 10, breakLine: true } },
      { text: "POST /api/validate/selected · /api/admet/batch", options: { color: C.muted, fontSize: 10 } },
    ], { x: bx, y: 4.9, w: 5.5, h: 1.4, fontFace: "Consolas", margin: 0 });

    bx = card(6.8, C.domFE, "Frontend (Vite :5173)");
    statusBadge(s, bx, 2.1, "good", "16 페이지 lazy-load, HTTP 200");
    statusBadge(s, bx, 2.5, "good", "TanStack Query v5 + Zustand v5");
    statusBadge(s, bx, 2.9, "good", "8 hook이 /api/* 와 1:1 매핑");
    statusBadge(s, bx, 3.3, "good", "OKLCH 디자인 토큰 마이그레이션 완료");
    statusBadge(s, bx, 3.7, "warn", "스모크 1/2 FAIL: 'More' 버튼 (테스트-구현 불일치)");
    statusBadge(s, bx, 4.1, "warn", "레거시 페이지 4건 미노출");
    s.addText("Primary 페이지 11개", { x: bx, y: 4.6, w: 5.5, h: 0.3, fontFace: "Calibri", fontSize: 12, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "RunConsole · RunLauncher · CandidatePage", options: { color: C.muted, fontSize: 10, breakLine: true } },
      { text: "ManualSelectivity · StrategyRunner · Benchmark", options: { color: C.muted, fontSize: 10, breakLine: true } },
      { text: "WetlabOrder · BindingPocket · Settings · About", options: { color: C.muted, fontSize: 10 } },
    ], { x: bx, y: 4.9, w: 5.5, h: 1.4, fontFace: "Calibri", margin: 0 });

    addFooter(s, LBL, 5, TOTAL);
  }

  // === S6 AI/vLLM + MCP/Tools ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "AI · vLLM · MCP / Tools", "LLM 4d 16h 무중단 / MCP 설정 오류 발견 (5분 수정 가능)");

    // Big stat card
    s.addShape("rect", { x: 0.6, y: 1.5, w: 4.0, h: 2.7, fill: { color: C.bgDark }, line: { color: C.bgDark, width: 0 } });
    s.addText("4d 16h", { x: 0.6, y: 1.7, w: 4.0, h: 1.1, fontFace: "Cambria", fontSize: 60, bold: true, color: C.accentLight, align: "center", margin: 0 });
    s.addText("vLLM uptime", { x: 0.6, y: 2.85, w: 4.0, h: 0.4, fontFace: "Calibri", fontSize: 14, color: C.textOnDark, align: "center", margin: 0 });
    s.addText("deepseek-r1-distill-32b · GPU 3 · 83 GB", { x: 0.6, y: 3.25, w: 4.0, h: 0.4, fontFace: "Calibri", fontSize: 10, color: "B0BEC5", align: "center", margin: 0 });
    s.addText("/v1/models 200 · 5ms · 1.0 tok/s gen", { x: 0.6, y: 3.65, w: 4.0, h: 0.4, fontFace: "Consolas", fontSize: 9, color: "B0BEC5", align: "center", margin: 0 });

    // 5+1 Agent
    s.addShape("rect", { x: 4.8, y: 1.5, w: 4.0, h: 2.7, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addText("5+1 Agent 모듈", { x: 4.95, y: 1.6, w: 3.7, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "planner.py", options: { fontSize: 11, color: C.text, breakLine: true } },
      { text: "builder.py", options: { fontSize: 11, color: C.text, breakLine: true } },
      { text: "critic.py", options: { fontSize: 11, color: C.text, breakLine: true } },
      { text: "qc_ranker.py", options: { fontSize: 11, color: C.text, breakLine: true } },
      { text: "reporter.py", options: { fontSize: 11, color: C.text, breakLine: true } },
      { text: "diversity_manager.py", options: { fontSize: 11, color: C.text } },
    ], { x: 4.95, y: 2.1, w: 3.7, h: 2.0, fontFace: "Consolas", margin: 0 });

    // MCP
    s.addShape("rect", { x: 9.0, y: 1.5, w: 3.8, h: 2.7, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addText("MCP 서버 (3종)", { x: 9.15, y: 1.6, w: 3.5, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    statusBadge(s, 9.15, 2.1, "good", "github");
    statusBadge(s, 9.15, 2.5, "good", "memory");
    statusBadge(s, 9.15, 2.9, "crit", "filesystem (경로 오류)");
    s.addText("/home/helloworld/.../PRST_N_FM 미존재", { x: 9.15, y: 3.35, w: 3.5, h: 0.4, fontFace: "Consolas", fontSize: 9, color: C.crit, italic: true, margin: 0 });
    s.addText("→ 5분 수정 가능 (본 점검 신규 발견)", { x: 9.15, y: 3.7, w: 3.5, h: 0.4, fontFace: "Calibri", fontSize: 10, color: C.muted, margin: 0 });

    // Phase 2 smoke note
    s.addShape("rect", { x: 0.6, y: 4.5, w: 12.2, h: 1.9, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 4.5, w: 0.08, h: 1.9, fill: { color: C.warn }, line: { color: C.warn, width: 0 } });
    s.addText("⚠ Phase 2 smoke (2026-05-27) 시점 기록", { x: 0.85, y: 4.6, w: 11.8, h: 0.4, fontFace: "Calibri", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "에이전트 yaml의 vLLM ", options: { fontSize: 12, color: C.text } },
      { text: "http://localhost:8002", options: { fontSize: 11, color: C.accent, fontFace: "Consolas" } },
      { text: " → Planner 단계에서 ", options: { fontSize: 12, color: C.text } },
      { text: "Connection refused (errno 111)", options: { fontSize: 11, color: C.crit, fontFace: "Consolas" } },
      { text: " 발생 → 규칙 기반 폴백 (파이프라인 계속 진행)", options: { fontSize: 12, color: C.text } },
    ], { x: 0.85, y: 5.05, w: 11.8, h: 0.5, fontFace: "Calibri", margin: 0 });
    s.addText("현재 vLLM은 정상 가동 — smoke 재실행으로 종단 LLM 호출 검증 필요 (P1)", { x: 0.85, y: 5.65, w: 11.8, h: 0.4, fontFace: "Calibri", fontSize: 11, italic: true, color: C.muted, margin: 0 });

    addFooter(s, LBL, 6, TOTAL);
  }

  // === S7 Docking System ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domDock);
    addTitle(s, "Docking System", "Boltz-2 primary · DiffPepBuilder 비활성 · FlexPepDock 워커 4 idle");

    const rows = [
      [{ text: "엔진", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "사용 step", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "conda env", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "상태", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "비고", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["Boltz-2 ★", "step05 / 05c", "boltz", "🟢 가용", "primary · MSA 우회 · CASP16 affinity 1위 (MIT)"],
      ["DiffDock", "step05", "boltz", "🟡 보조", "arXiv:2210.01776 — A-06 PoC 대상"],
      ["DiffPepBuilder", "step05", "diffpepbuilder", "🔴 비활성", "step05_docking.py:144 주석 처리"],
      ["PyRosetta FlexPepDock", "step06", "bio-tools", "🟢 가용", "워커 4 idle · ddG ≤ -1.0 REU Gate"],
      ["FoldMason", "step07", "bio-tools", "🟢 가용", "clustering"],
    ];
    s.addTable(rows, {
      x: 0.6, y: 1.5, w: 12.2, h: 2.5,
      colW: [2.7, 2.4, 2.0, 1.5, 3.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 11, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });

    // FlexPepDock worker pool
    s.addShape("rect", { x: 0.6, y: 4.2, w: 12.2, h: 2.4, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 4.2, w: 0.08, h: 2.4, fill: { color: C.domDock }, line: { color: C.domDock, width: 0 } });
    s.addText("FlexPepDock 워커 풀 (현재 상태)", { x: 0.85, y: 4.3, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    for (let i = 0; i < 4; i++) {
      const x = 1.5 + i * 1.5;
      s.addShape("ellipse", { x, y: 4.85, w: 0.7, h: 0.7, fill: { color: C.good }, line: { color: C.good, width: 0 } });
      s.addText(`W${i + 1}`, { x, y: 4.85, w: 0.7, h: 0.7, fontFace: "Cambria", fontSize: 18, bold: true, color: C.textOnDark, align: "center", valign: "middle", margin: 0 });
      s.addText(`worker-${i + 1}`, { x: x - 0.2, y: 5.6, w: 1.1, h: 0.3, fontFace: "Consolas", fontSize: 9, color: C.muted, align: "center", margin: 0 });
    }
    s.addText("uptime 5d 20h · idle · 큐 비어있음 (18 잡 history, 1건 사용자 취소)",
      { x: 7.6, y: 5.05, w: 5.2, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0 });
    s.addText("로그: /tmp/flexpepdock_worker_{1..4}.log\nPID: 3362210 / 3362349 / 3362433 / 3362573",
      { x: 7.6, y: 5.45, w: 5.2, h: 0.8, fontFace: "Consolas", fontSize: 9, color: C.muted, margin: 0 });

    addFooter(s, LBL, 7, TOTAL);
  }

  // === S8 Silo A 이중 구현 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.crit);
    addTitle(s, "Silo A — ⚠ 이중 구현 발견", "3-Arm 완전판 (실 실행 0건) vs 로컬 1-Arm 축약판");

    function card(x, col, title) {
      s.addShape("rect", { x, y: 1.5, w: 6.0, h: 5.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x, y: 1.5, w: 0.08, h: 5.0, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(title, { x: x + 0.25, y: 1.6, w: 5.8, h: 0.4, fontFace: "Cambria", fontSize: 15, bold: true, color: C.text, margin: 0 });
      return x + 0.25;
    }
    let bx = card(0.6, C.crit, "(A1) pipelines/silo_a/  ─  3-Arm NIM");
    s.addText("코드: 완비 (arms.py L24/L100/L200)", { x: bx, y: 2.0, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0 });
    statusBadge(s, bx, 2.4, "good", "Arm1 MolMIM → DiffDock (소분자)");
    statusBadge(s, bx, 2.8, "good", "Arm2 FlexPepDock (펩타이드 변이체)");
    statusBadge(s, bx, 3.2, "good", "Arm3 RFdiffusion → ProteinMPNN → ESMFold");
    statusBadge(s, bx, 3.6, "good", "UnifiedScorer · 9 PASS 테스트");
    statusBadge(s, bx, 4.0, "crit", "실 실행 0건 — NIM API 키 부재");
    statusBadge(s, bx, 4.4, "crit", "outputs/silo_a/ 미존재");
    statusBadge(s, bx, 4.8, "crit", "POST /api/v1/silo-a/run 은 Phase 1 STUB");
    s.addText("→ NIM 대체 어댑터 결정 필요 (6월 회의)", { x: bx, y: 5.4, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, italic: true, color: C.crit, margin: 0 });
    s.addText("→ diversity 가중치 0.10 사문화", { x: bx, y: 5.8, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, italic: true, color: C.muted, margin: 0 });

    bx = card(6.8, C.warn, "(A2) pipeline_local/_run_silo_a()  ─  로컬 축약판");
    s.addText("코드: 분리 구현 (NIM 의존 없음)", { x: bx, y: 2.0, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0 });
    statusBadge(s, bx, 2.4, "good", "RFdiffusion 호출 (de novo)");
    statusBadge(s, bx, 2.8, "good", "ProteinMPNN 호출 (sequence)");
    statusBadge(s, bx, 3.2, "crit", "Arm1 (소분자) 부재");
    statusBadge(s, bx, 3.6, "crit", "Arm2 (FlexPepDock) 부재");
    statusBadge(s, bx, 4.0, "warn", '"3-Arm" 아니라 사실상 "1-Arm de novo"');
    statusBadge(s, bx, 4.4, "good", "smoke 실행 검증됨 (2026-05-27)");
    statusBadge(s, bx, 4.8, "warn", "전용 단위 테스트 없음");
    s.addText("두 구현의 통합 또는 명확한 역할 분리가 필요", { x: bx, y: 5.4, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, italic: true, color: C.warn, margin: 0 });
    s.addText("(narrative \"3-Arm\" 서술 정정 검토)", { x: bx, y: 5.8, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, italic: true, color: C.muted, margin: 0 });

    addFooter(s, LBL, 8, TOTAL);
  }

  // === S9 Silo B 8-step + Layer 3 STUB ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domSiloB);
    addTitle(s, "Silo B — PyRosetta mutation+dock 8-Step", "코드 완비 · 워커 4 idle · Layer 3 STUB · Boltz 25분 SLA 미완");

    const steps = ["01\nreceptor", "02\nbackbone", "03\nsequence", "03b\nmutation", "04\nQC", "05\ndocking", "06\nrosetta", "07\nanalysis", "08\nstability"];
    const stepW = 1.3, gap = 0.07, startX = 0.6;
    steps.forEach((label, i) => {
      const x = startX + i * (stepW + gap);
      let bar = C.accent;
      if (i === 5) bar = C.warn;
      if (i === 8) bar = C.crit;
      s.addShape("rect", { x, y: 1.6, w: stepW, h: 0.95, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x, y: 1.6, w: stepW, h: 0.08, fill: { color: bar }, line: { color: bar, width: 0 } });
      s.addText(label, { x, y: 1.7, w: stepW, h: 0.85, fontFace: "Calibri", fontSize: 10, bold: true, color: C.text, align: "center", valign: "middle", margin: 0 });
    });
    s.addText("Gate 1 pLDDT  ·  Gate 2 QC  ·  Gate 3 ⊿G  ·  Gate 4 ddG ≤ -1.0 REU",
      { x: 0.6, y: 2.65, w: 12.2, h: 0.3, fontFace: "Calibri", fontSize: 10, italic: true, color: C.muted, align: "center", margin: 0 });

    s.addText("Step08 → 3-Layer Ensemble 스코어링", { x: 0.6, y: 3.1, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    const layerRows = [
      [{ text: "Layer", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "도구", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "도메인", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "상태", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["Layer 1", "PlifePred + HLE 회귀 + pepADMET", "L-AA 펩타이드 혈청 반감기", "🟢 가동"],
      ["Layer 2", "로컬 PEPlife2-GAT", "D-AA / cyclic", "🟡 R²=0.022 (재학습 후, seed 의존)"],
      ["Layer 3", "ADMET-AI MD proxy (★STUB)", "DOTA 라벨링 후보", "🔴 미구현 layer3_dota_admet_ai_md_proxy_stub"],
    ];
    s.addTable(layerRows, {
      x: 0.6, y: 3.55, w: 12.2, h: 1.9,
      colW: [1.5, 3.5, 3.5, 3.7],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 10.5, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });

    s.addShape("rect", { x: 0.6, y: 5.6, w: 12.2, h: 1.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 5.6, w: 0.08, h: 1.0, fill: { color: C.warn }, line: { color: C.warn, width: 0 } });
    s.addText("⚠ 5/27 audit: pipeline_local 1 iter 25분 SLA 미완 (Boltz 32회 후 timeout)", { x: 0.85, y: 5.7, w: 12, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: C.warn, margin: 0 });
    s.addText("→ Step05 Boltz 후보당 30~40s, 55개 ≈ 1500s 초과. demo subset 또는 SLA 재설정 필요",
      { x: 0.85, y: 6.1, w: 12, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.muted, margin: 0 });

    addFooter(s, LBL, 9, TOTAL);
  }

  // === S10 Dual-silo + Silo C 격차 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.crit);
    addTitle(s, "Dual-silo 통합 흐름 — 🚨 코드 가정 vs 실 구현 격차", "분기 :835 · 합류 :981 · 가중 A:0.34 B:0.33 C:0.33 — 그러나 Silo C 구현 없음");

    s.addShape("rect", { x: 0.6, y: 1.5, w: 3.0, h: 1.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addText("CLI --dual flag", { x: 0.7, y: 1.55, w: 2.8, h: 0.3, fontFace: "Calibri", fontSize: 12, bold: true, color: C.text, margin: 0 });
    s.addText("orchestrator.py:835\ndual_silo.enabled (기본 False)", { x: 0.7, y: 1.9, w: 2.8, h: 0.55, fontFace: "Consolas", fontSize: 9.5, color: C.muted, margin: 0 });

    s.addShape("rect", { x: 4.4, y: 1.2, w: 2.5, h: 0.7, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 4.4, y: 1.2, w: 0.08, h: 0.7, fill: { color: C.domSiloA }, line: { color: C.domSiloA, width: 0 } });
    s.addText("Silo A (3-Arm)", { x: 4.55, y: 1.25, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.text, margin: 0 });
    s.addText("실 실행 0건", { x: 4.55, y: 1.55, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 9, color: C.crit, italic: true, margin: 0 });

    s.addShape("rect", { x: 4.4, y: 2.1, w: 2.5, h: 0.7, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 4.4, y: 2.1, w: 0.08, h: 0.7, fill: { color: C.domSiloB }, line: { color: C.domSiloB, width: 0 } });
    s.addText("Silo B (PyRosetta)", { x: 4.55, y: 2.15, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.text, margin: 0 });
    s.addText("코드 정상 · SLA 미완", { x: 4.55, y: 2.45, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 9, color: C.warn, italic: true, margin: 0 });

    s.addShape("rect", { x: 4.4, y: 3.0, w: 2.5, h: 0.7, fill: { color: C.bgElev }, line: { color: C.crit, width: 2, dashType: "dash" } });
    s.addText("Silo C — ???", { x: 4.55, y: 3.05, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.crit, margin: 0 });
    s.addText("policy.py 가정만", { x: 4.55, y: 3.35, w: 2.3, h: 0.3, fontFace: "Calibri", fontSize: 9, color: C.crit, italic: true, margin: 0 });

    s.addShape("rect", { x: 7.8, y: 2.0, w: 5.0, h: 1.5, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 7.8, y: 2.0, w: 0.08, h: 1.5, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
    s.addText("aggregator.rank_fusion_weighted_sum", { x: 7.95, y: 2.1, w: 4.8, h: 0.3, fontFace: "Consolas", fontSize: 10, bold: true, color: C.text, margin: 0 });
    s.addText("silo_weights = {A:0.34, B:0.33, C:0.33}", { x: 7.95, y: 2.45, w: 4.8, h: 0.3, fontFace: "Consolas", fontSize: 10, color: C.accent, margin: 0 });
    s.addText("orchestrator.py:981 _run_dual_silo()\nSilo A seq에 'a_' 접두어 → BranchOutputs", { x: 7.95, y: 2.8, w: 4.8, h: 0.6, fontFace: "Calibri", fontSize: 9, color: C.muted, margin: 0 });

    s.addShape("rect", { x: 0.6, y: 4.1, w: 12.2, h: 2.5, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 4.1, w: 0.08, h: 2.5, fill: { color: C.crit }, line: { color: C.crit, width: 0 } });
    s.addText("🚨 핵심 격차 3가지", { x: 0.85, y: 4.2, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.crit, margin: 0 });

    s.addText([
      { text: "① Silo C 코드 가정 vs 실 구현 ", options: { bold: true, color: C.text, fontSize: 12 } },
      { text: "— policy.py가 ", options: { color: C.text, fontSize: 11 } },
      { text: "required_silos=[\"A\",\"B\",\"C\"]", options: { fontFace: "Consolas", color: C.crit, fontSize: 10 } },
      { text: " 요구, aggregator 가중 0.33 부여 — 그러나 코드/문서/실행 흔적 0건", options: { color: C.text, fontSize: 11 } },
    ], { x: 0.85, y: 4.7, w: 12, h: 0.45, fontFace: "Calibri", margin: 0 });

    s.addText([
      { text: "② --dual 기본 False ", options: { bold: true, color: C.text, fontSize: 12 } },
      { text: "— 2026-05-27 phase 2 smoke도 dual 미활성 → ", options: { color: C.text, fontSize: 11 } },
      { text: "완전 Dual 통합 종단 검증 기록 0건", options: { bold: true, color: C.crit, fontSize: 11 } },
    ], { x: 0.85, y: 5.2, w: 12, h: 0.45, fontFace: "Calibri", margin: 0 });

    s.addText([
      { text: "③ K-1/K-2 selectivity 결함 ", options: { bold: true, color: C.text, fontSize: 12 } },
      { text: "— _build_pdb_index 정렬 + candidate_pdb 미전달로 ", options: { color: C.text, fontSize: 11 } },
      { text: "모든 후보가 동일 off-target 결과", options: { bold: true, color: C.crit, fontSize: 11 } },
      { text: " → selectivity 평가 사실상 무효", options: { color: C.text, fontSize: 11 } },
    ], { x: 0.85, y: 5.7, w: 12, h: 0.65, fontFace: "Calibri", margin: 0 });

    addFooter(s, LBL, 10, TOTAL);
  }

  // === S11 Action Items P0 종합표 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "Action Items P0 종합 비교표 (4/6 회의 9건)", "원본 요구 ↔ 대응 ↔ 달성도 ↔ 현재 문제점 ↔ 향후 방향");

    const rows = [
      [{ text: "No", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "원본 요구", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "관련", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "대응 방법", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "달성도", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "현재 문제점", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "향후 방향", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "상태", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["A-01", "SSTR1/3/4/5 위치 지정 도킹", "Dock/B", "cealign + binding_pocket JSON", "●", "7T10 vs 7XNA 불일치", "7T10 재검증", "✅ PR#61"],
      ["A-02", "혈청 반감기 도구 비교", "AI/B", "L1 PlifePred / L2 pepMSND wrapper", "◑", "D-AA HIGH-BLOCKER, PR#117", "MD(RMSD) 2차 · 실험", "🟡"],
      ["A-03", "Fab-ADMET 검증·자체학습", "AI/B", "pepADMET 로컬 + ADMET-AI", "◑", "HTTP 403, Layer 3 STUB", "pepADMET fine-tuning", "🟡"],
      ["A-04", "Top-K 복합 스코어링", "AI/B", "Tier S/A/B + Critic + ensemble", "◕", "enrichment 분리, PR#117", "정합 / Pareto", "✅ PR#62"],
      ["A-05", "SST14 레퍼런스 ⊿G", "Dock/B", "n회 도킹 Mean + 가변 임계", "●", "MM-GBSA/FEP 미구현", "gmx_MMPBSA·OpenFE", "✅ direct"],
      ["A-06", "디퓨전 도킹 PoC", "Dock/B", "DiffDock or 유사", "◔", "본격 PoC 미수행", "DiffDock + RMSD ≤2.0Å", "🟡"],
      ["A-07", "GPU 견적 수집", "Infra", "DGX H100/B200 매트릭스", "◑", "외부 견적 대기", "6월 회의 의사결정", "🟡"],
      ["A-09", "최종 후보 3-4 + 합성", "All/Dual", "Tier S → PRST-001~004", "●", "wet-lab 미시작, ADMET OOD", "Ki assay + RI 표지", "✅ PR#63"],
      ["A-10", "SSTR3 도킹 에러 해결", "Dock/B", "PDB sanitize", "●", "(회귀 유지)", "—", "✅ PR#60"],
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [0.5, 2.2, 0.8, 2.7, 0.7, 2.3, 2.0, 1.3],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    s.addText("● 완료  ◕ 대부분  ◑ 부분  ◔ 초기  ○ 미착수 / A-08(라이브러리 마이그)는 PDF §2.3 배포 완료로 삭제",
      { x: 0.6, y: 6.85, w: 12.5, h: 0.3, fontFace: "Calibri", fontSize: 9, italic: true, color: C.muted, margin: 0 });
    addFooter(s, LBL, 11, TOTAL);
  }

  // === S12 Action Items 분포 + Top P0 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "Action Items 진행 분포 + Top P0", "4월 회의 원안 8건 + 후속 16건 + 본 점검 신규 발견");

    s.addText("4월 회의 원안 8건", { x: 0.6, y: 1.4, w: 6, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addChart(pres.charts.BAR, [{ name: "건수", labels: ["충족", "부분", "미달"], values: [6, 2, 0] }], {
      x: 0.6, y: 1.8, w: 5.8, h: 2.5, barDir: "bar",
      chartColors: [C.good], chartArea: { fill: { color: C.bgElev } },
      catAxisLabelColor: C.text, valAxisLabelColor: C.muted,
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.text,
      showLegend: false, valGridLine: { color: C.border, size: 0.3 },
    });

    s.addText("후속 발견 8건 포함 총 16건", { x: 7.0, y: 1.4, w: 6, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addChart(pres.charts.BAR, [{ name: "건수", labels: ["충족", "부분", "미달"], values: [7, 4, 5] }], {
      x: 7.0, y: 1.8, w: 5.8, h: 2.5, barDir: "bar",
      chartColors: [C.warn], chartArea: { fill: { color: C.bgElev } },
      catAxisLabelColor: C.text, valAxisLabelColor: C.muted,
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.text,
      showLegend: false, valGridLine: { color: C.border, size: 0.3 },
    });

    s.addShape("rect", { x: 0.6, y: 4.5, w: 12.2, h: 2.2, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 4.5, w: 0.08, h: 2.2, fill: { color: C.crit }, line: { color: C.crit, width: 0 } });
    s.addText("Top P0 액션 (즉시 / 금일 / D-7 대응)", { x: 0.85, y: 4.6, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 15, bold: true, color: C.text, margin: 0 });

    const p0 = [
      ["🔴", "K-1/K-2 selectivity 결함 정정 (R-04) — 모든 후보 동일 off-target"],
      ["🔴", "PRST-001~004 ranking 재검증 (R-08)"],
      ["🟠", "A-02 D-AA HIGH-BLOCKER 해소 (MD 2차 vs 외부 도구)"],
      ["🟠", "PR #117 (ADMET divergence) 머지 결정 (R-05)"],
      ["🟠", "Silo C 정책 결정 (R-14, 구현 vs 가중치 재설계)"],
      ["🟢", "MCP filesystem 경로 수정 (R-01, 5분)"],
    ];
    p0.forEach(([icon, txt], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.85 + col * 6.0, y = 5.1 + row * 0.5;
      s.addText(icon, { x, y, w: 0.3, h: 0.4, fontSize: 14, margin: 0, valign: "middle" });
      s.addText(txt, { x: x + 0.3, y, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0, valign: "middle" });
    });
    addFooter(s, LBL, 12, TOTAL);
  }

  // === S13 Serum Stability L-AA/D-AA Landscape ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domAI);
    addTitle(s, "Serum Stability — L-AA · D-AA Landscape (A-02 보강)", "SST-14 t½ ~3분 vs Octreotide ~100분 — D-AA 도구 격차");

    // L-AA card
    s.addShape("rect", { x: 0.6, y: 1.5, w: 6.0, h: 5.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 1.5, w: 0.08, h: 5.0, fill: { color: C.info }, line: { color: C.info, width: 0 } });
    s.addText("L-AA Serum Stability — 알려진 성능과 한계", { x: 0.85, y: 1.6, w: 5.8, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText("자연 L-AA → 다중 protease 분해", { x: 0.85, y: 2.0, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 10, italic: true, color: C.muted, margin: 0 });
    s.addText([
      { text: "N-end rule (Bachmair 1986) ", options: { bold: true, fontSize: 10, color: C.text } },
      { text: "— DOI:10.1126/science.3018930\n", options: { fontSize: 9, color: C.muted } },
      { text: "ProtParam (ExPASy) ", options: { bold: true, fontSize: 10, color: C.text } },
      { text: "— web.expasy.org\n", options: { fontSize: 9, color: C.muted } },
      { text: "PlifePred (Mathur 2018) ", options: { bold: true, fontSize: 10, color: C.text } },
      { text: "— DOI:10.1371/journal.pone.0196829\n", options: { fontSize: 9, color: C.muted } },
      { text: "HLP (IIITD Raghava) ", options: { bold: true, fontSize: 10, color: C.text } },
      { text: "— L-AA 분류기\n", options: { fontSize: 9, color: C.muted } },
      { text: "PeptideRanker (UCD) ", options: { bold: true, fontSize: 10, color: C.text } },
      { text: "— 반감기 X (bioactivity 점수)", options: { fontSize: 9, color: C.crit, italic: true } },
    ], { x: 0.85, y: 2.4, w: 5.8, h: 2.3, fontFace: "Calibri", margin: 0 });

    s.addText("공통 한계 (4가지)", { x: 0.85, y: 4.8, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "① 자연 L-AA 학습 → modification 외삽 시 신뢰 ↓\n", options: { fontSize: 10, color: C.text } },
      { text: "② 점 추정만 (uncertainty 없음)\n", options: { fontSize: 10, color: C.text } },
      { text: "③ 벤치마크 부족 — 회의록 §4 A-02 구축 요구\n", options: { fontSize: 10, color: C.text } },
      { text: "④ 혈청·위장관·세포내 분해 미구분", options: { fontSize: 10, color: C.text } },
    ], { x: 0.85, y: 5.15, w: 5.8, h: 1.3, fontFace: "Calibri", margin: 0 });

    // D-AA card
    s.addShape("rect", { x: 6.8, y: 1.5, w: 6.0, h: 5.0, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 6.8, y: 1.5, w: 0.08, h: 5.0, fill: { color: C.crit }, line: { color: C.crit, width: 0 } });
    s.addText("D-AA Serum Stability — 알려진 사실과 도구 격차", { x: 7.05, y: 1.6, w: 5.8, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText("D-AA → protease 입체화학 반대 → 저항성 큼", { x: 7.05, y: 2.0, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 10, italic: true, color: C.muted, margin: 0 });

    // 벤치마크 미니 표
    const bench = [
      [{ text: "Peptide", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark, fontSize: 9 } },
       { text: "Mod", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark, fontSize: 9 } },
       { text: "t½", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark, fontSize: 9 } },
       { text: "배수", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark, fontSize: 9 } }],
      ["SST14", "—", "~3분", "1×"],
      ["Octreotide", "D-Phe+Thr(ol)", "~100분", "~33×"],
      ["Lanreotide", "D-Nal+D-Trp", "(더 김)", "?"],
      ["RC-160", "D-Phe+L-Val", "미기재", "—"],
    ];
    s.addTable(bench, {
      x: 7.05, y: 2.4, w: 5.6, h: 1.4,
      colW: [1.4, 1.7, 1.2, 1.3],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });

    s.addText("🔴 핵심 격차: D-AA 신뢰 in silico 도구 부재", { x: 7.05, y: 3.9, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.crit, margin: 0 });
    s.addText([
      { text: "PlifePred/HLP/ProtParam ❌ D-AA 학습 부재\n", options: { fontSize: 10, color: C.text } },
      { text: "PEPlife2-GAT △ R²=0.022 (재학습 후 — 의사결정 불가)\n", options: { fontSize: 10, color: C.crit } },
      { text: "pepADMET [추정] DOI:10.1021/acs.jcim.5c02518\n", options: { fontSize: 10, color: C.text } },
      { text: "MD(RMSD) 2차 ✅ 서호성 의견 — 본 프로젝트 미구현\n", options: { fontSize: 10, color: C.text } },
      { text: "in vitro 실측 ✅ gold standard — wet-lab 병행", options: { fontSize: 10, color: C.good, bold: true } },
    ], { x: 7.05, y: 4.25, w: 5.8, h: 2.0, fontFace: "Calibri", margin: 0 });

    s.addText("→ A-02(stability) + A-04(scoring) + A-09(synthesis) 묶어 의사결정",
      { x: 0.6, y: 6.6, w: 12.2, h: 0.3, fontFace: "Calibri", fontSize: 11, italic: true, bold: true, color: C.accent, align: "center", margin: 0 });

    addFooter(s, LBL, 13, TOTAL);
  }

  // === S14 반영 계획 요약 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "반영 계획 — 21건 (committed 10 / proposed 11)", "P0 즉시 3 · P0 차주 7 · P1 4주 8 · P2 검토 3");

    s.addChart(pres.charts.BAR, [
      { name: "committed", labels: ["P0 즉시", "P0 차주", "P1 4주", "P2 검토"], values: [3, 3, 3, 1] },
      { name: "proposed", labels: ["P0 즉시", "P0 차주", "P1 4주", "P2 검토"], values: [0, 4, 5, 2] },
    ], {
      x: 0.6, y: 1.4, w: 6.0, h: 3.0,
      barDir: "bar", barGrouping: "stacked",
      chartColors: [C.accent, C.muted],
      chartArea: { fill: { color: C.bgElev } },
      catAxisLabelColor: C.text, valAxisLabelColor: C.muted,
      showValue: true, dataLabelPosition: "ctr", dataLabelColor: C.textOnDark,
      showLegend: true, legendPos: "b", valGridLine: { color: C.border, size: 0.3 },
    });

    // 금일 착수 카드
    s.addShape("rect", { x: 6.9, y: 1.4, w: 6.0, h: 5.3, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 6.9, y: 1.4, w: 0.08, h: 5.3, fill: { color: C.good }, line: { color: C.good, width: 0 } });
    s.addText("금일 착수 가능 (committed)", { x: 7.05, y: 1.5, w: 5.8, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    const cmt = [
      "R-01 MCP filesystem 경로 수정 (5분)",
      "R-02 BE silo_a 라우터 404 정정",
      "R-03 FE smoke 'More' 테스트 갱신",
      "R-04 K-1/K-2 selectivity 정정",
      "R-08 PRST ranking 재검증",
      "R-09 DiffDock PoC 1회 실행",
    ];
    cmt.forEach((t, i) => {
      s.addText(`✓  ${t}`, { x: 7.05, y: 2.0 + i * 0.45, w: 5.8, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0, valign: "middle" });
    });

    s.addText("상세: docs/meet_preparation/reflection_plan/00_master_plan.md", { x: 0.6, y: 4.7, w: 6.0, h: 0.3, fontFace: "Consolas", fontSize: 10, italic: true, color: C.muted, margin: 0 });

    // 의존 관계
    s.addShape("rect", { x: 0.6, y: 5.1, w: 6.0, h: 1.6, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 5.1, w: 0.08, h: 1.6, fill: { color: C.warn }, line: { color: C.warn, width: 0 } });
    s.addText("핵심 의존 관계 (선후 작업)", { x: 0.85, y: 5.2, w: 5.8, h: 0.3, fontFace: "Calibri", fontSize: 12, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "R-04 K-1/K-2 정정 → R-08 PRST 재검증\n", options: { fontSize: 10, color: C.text, fontFace: "Consolas" } },
      { text: "R-05 PR #117 머지 → R-06 enrichment 정합\n", options: { fontSize: 10, color: C.text, fontFace: "Consolas" } },
      { text: "R-14 Silo C 정책 → R-13 Silo A 통합\n", options: { fontSize: 10, color: C.text, fontFace: "Consolas" } },
      { text: "R-09 DiffDock PoC → R-10 GPU 견적 → A-06 결정", options: { fontSize: 10, color: C.text, fontFace: "Consolas" } },
    ], { x: 0.85, y: 5.55, w: 5.8, h: 1.1, fontFace: "Consolas", margin: 0 });

    addFooter(s, LBL, 14, TOTAL);
  }

  // === S15 리스크 매트릭스 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "리스크 매트릭스 (영향도 × 발생 가능성)", "P0 4건 / P1 5건 / P2 4건");

    const matX = 1.5, matY = 1.6, cellW = 3.6, cellH = 1.55;
    const probLabels = ["낮음", "보통", "높음"];
    const impactLabels = ["低", "中", "高"];
    probLabels.forEach((p, i) => {
      s.addText(p, { x: matX + i * cellW, y: matY - 0.4, w: cellW, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.muted, align: "center", margin: 0 });
    });
    impactLabels.forEach((imp, i) => {
      s.addText(imp, { x: matX - 0.5, y: matY + (2 - i) * cellH + 0.5, w: 0.4, h: 0.3, fontFace: "Calibri", fontSize: 11, bold: true, color: C.muted, align: "center", margin: 0 });
    });

    const cells = [
      [matX, matY, "FBE9E7", ""],
      [matX + cellW, matY, "FFCDD2", "Layer 3 STUB\nDOTA 평가 공백"],
      [matX + 2*cellW, matY, "F44336", "K-1/K-2 selectivity\nSilo A 실행 0건\nDual SLA 미완"],
      [matX, matY + cellH, "FFFDE7", "vLLM downtime"],
      [matX + cellW, matY + cellH, "FFF59D", "silo_a 404\nDiffPepBuilder OFF\nSilo C 격차"],
      [matX + 2*cellW, matY + cellH, "FFE082", "PR #117 미머지\n→ enrichment 불일치"],
      [matX, matY + 2*cellH, "E8F5E9", "워커 OOM"],
      [matX + cellW, matY + 2*cellH, "C8E6C9", "FE smoke 1 FAIL\ndiversity 사문화"],
      [matX + 2*cellW, matY + 2*cellH, "A5D6A7", "MCP fs path\n(5분 수정)"],
    ];
    cells.forEach(([x, y, fill, text]) => {
      s.addShape("rect", { x, y, w: cellW - 0.05, h: cellH - 0.05, fill: { color: fill }, line: { color: C.border, width: 0.5 } });
      if (text) s.addText(text, { x: x + 0.1, y: y + 0.05, w: cellW - 0.25, h: cellH - 0.15, fontFace: "Calibri", fontSize: 10, color: C.text, margin: 0, valign: "top" });
    });

    s.addShape("rect", { x: 1.5, y: 6.4, w: 12, h: 0.5, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addText([
      { text: "🔴 P0 (즉시)    🟠 P1 (4주 audit 권고)    🟢 P2 (낮은 영향, 즉시 수정)", options: { color: C.text, fontSize: 11 } },
    ], { x: 1.6, y: 6.45, w: 11.5, h: 0.4, fontFace: "Calibri", margin: 0, valign: "middle" });

    addFooter(s, LBL, 15, TOTAL);
  }

  // === S16 종합 향후 방향 의견 (전문가 통합) ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.accent);
    addTitle(s, "종합 향후 방향 의견 (전문가 4명 통합)", "약리학 / 생명공학 / 화학 / 수학·통계 견해");

    const opinions = [
      ["💊 약리학 (reviewer-pharma)", C.domBE,
       "회귀 76/76 PASS. A-02 D-AA HIGH-BLOCKER + A-03 Layer 3 STUB로 in silico 단독 의사결정 불가. PRST Tier S는 ΔG·L-AA ADMET 편중 잠정 순위 — PR #117 + enrichment 결정 + wet-lab 시점 3대 의사결정.",
       "참조: pepADMET DOI:10.1021/acs.jcim.5c02518, Lutathera NDA 208700"],
      ["🧬 생명공학 (reviewer-biology)", C.domSiloB,
       "🚨 7XNA(octreotide 8-mer Cys2-Cys7) ≠ SST-14(14-mer Cys3-Cys14) ring span 근본 다름 + Boltz 3종 도킹 모두 포켓 외부 배치(78/66/79Å)로 ΔG 기준선 553 REU 재검증 필요. R-04 + R-20 동시 선행 필수.",
       "참조: Gervasoni 2023 JCIM DOI:10.1021/acs.jcim.3c00712, 2024 CSBJ DOI:10.1016/j.csbj.2024.03.005"],
      ["⚗️ 화학 (reviewer-chemistry)", C.domTool,
       "Met→Nle, Lys→Orn 즉시 SPPS 가능. ⚠ Cys SS bond 내 D-AA는 ERROR (Veber 1978 ~10× 활성↓). DOTA 라벨링 pH 4.0-4.5/95°C/15-30분. Quencher: Gentisic 0.63 + Ascorbic 2.8 mg/mL (Lutathera 검증).",
       "참조: Lutathera FDA DailyMed NDA 208700, Veber 1978 PNAS"],
      ["📊 수학·통계 (reviewer-math)", C.domAI,
       "🚨 Pareto front 현재 비활성 (MIN_CANDIDATES=50, n=4 운영) — Tier S는 WSS top 20% 단일 기준. K-1/K-2 결함 시 selectivity_ratio = ΔG 단조 변환 → 다목적이 단목적. ref*0.9 부호 재확인 + n회 SE/95% CI 표기.",
       "참조: gmx_MMPBSA DOI:10.1021/acs.jctc.1c00645, OpenFE openfree.energy 1.0, pymoo.org"],
    ];
    opinions.forEach(([h, col, body, src], i) => {
      const y = 1.4 + i * 1.3;
      s.addShape("rect", { x: 0.6, y, w: 12.2, h: 1.2, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x: 0.6, y, w: 0.08, h: 1.2, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(h, { x: 0.85, y: y + 0.05, w: 11.8, h: 0.35, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
      s.addText(body, { x: 0.85, y: y + 0.4, w: 11.8, h: 0.45, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0 });
      s.addText(src, { x: 0.85, y: y + 0.85, w: 11.8, h: 0.3, fontFace: "Consolas", fontSize: 9, italic: true, color: C.muted, margin: 0 });
    });
    s.addText("상세: docs/meet_preparation/expert_opinions/{pharma,biology,chemistry,math}_review.md",
      { x: 0.6, y: 6.7, w: 12.2, h: 0.3, fontFace: "Consolas", fontSize: 10, italic: true, color: C.muted, margin: 0 });

    addFooter(s, LBL, 16, TOTAL);
  }

  // === S17 금일 보고 핵심 결론 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bgDark };
    s.addShape("rect", { x: 12.7, y: 0, w: 0.6, h: 7.5, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
    s.addText("금일 보고 핵심 결론 (5줄)", { x: 0.6, y: 0.5, w: 11.5, h: 0.7, fontFace: "Cambria", fontSize: 30, bold: true, color: C.textOnDark, margin: 0 });
    s.addText("초안 보고 / 현재 상태 공유 — 최종 성과 발표 아님", { x: 0.6, y: 1.2, w: 11.5, h: 0.4, fontFace: "Calibri", fontSize: 13, italic: true, color: C.accentLight, margin: 0 });

    const msgs = [
      "Action Items 9건 중 6건 PR 머지 완료, 3건 진행 중. 본 점검 신규 발견 3건(K-1/K-2 결함·Silo C 격차·Dual 종단 0건)이 추가됨.",
      "🚨 Biology 발견: 7XNA(octreotide 8-mer Cys2-Cys7) ≠ SST-14(14-mer Cys3-Cys14) ring span 근본 다름 + Boltz 도킹 3종 모두 포켓 외부(78/66/79Å) → ΔG 기준선 553 REU 재검증 필요.",
      "🚨 Math 발견: Pareto front 현재 비활성(MIN=50, n=4) — Tier S는 WSS 단일 기준. K-1/K-2 결함 시 다목적이 단목적과 동치. ref*0.9 부호 재확인.",
      "A-02 D-AA HIGH-BLOCKER + Layer 3 STUB 으로 in silico 단독 의사결정 불가. PRST-001~004는 도출되었으나 wet-lab Ki·Stability assay 병행 필수.",
      "6월 회의 3대 결정: ① PR #117 머지 (D-AA enrichment) ② Silo C 정책 (구현 vs A:0.5/B:0.5) ③ wet-lab 시점·protocol. 전문가 4명 견해 통합 권고.",
    ];
    msgs.forEach((m, i) => {
      const y = 1.95 + i * 0.95;
      s.addShape("rect", { x: 0.6, y, w: 0.5, h: 0.8, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
      s.addText(String(i + 1), { x: 0.6, y, w: 0.5, h: 0.8, fontFace: "Cambria", fontSize: 24, bold: true, color: C.textOnDark, align: "center", valign: "middle", margin: 0 });
      s.addText(m, { x: 1.3, y, w: 11.3, h: 0.8, fontFace: "Calibri", fontSize: 13, color: C.textOnDark, valign: "middle", margin: 0 });
    });
    addFooter(s, LBL, 17, TOTAL);
  }

  // === S18 다음 단계 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "다음 단계", "오늘 즉시 / 차주 / 4주 P1 / 검토 사항");

    const cards = [
      ["🟢 오늘 즉시 (committed 3건)", C.good, [
        "R-01 MCP filesystem 경로 수정 (5분, 본 보고 발견)",
        "R-02 BE 재기동 후 silo_a 404 재확인",
        "R-03 FE smoke 'More' 테스트 갱신",
      ]],
      ["🟠 차주 (D-7)", C.warn, [
        "R-04 K-1/K-2 selectivity 결함 정정",
        "R-08 PRST ranking 재검증",
        "R-09 DiffDock PoC 1회 실행 (RMSD ≤2.0Å)",
        "R-12 벤치마크 R²/Spearman (회의록 §4 A-02)",
      ]],
      ["🔵 4주 P1 (audit 권고)", C.accent, [
        "R-05 PR #117 머지 결정 + R-06 enrichment 정합",
        "R-07 Layer 3 (DOTA proxy) 최소 구현",
        "R-11 MM-GBSA 도구 검토 (gmx_MMPBSA·OpenFE)",
        "R-13 Silo A 통합 / R-14 Silo C 정책 결정",
      ]],
      ["⚪ 검토 사항 (proposed)", C.muted, [
        "R-19 Schrödinger 도입 검토 (라이센스·비용 정량화)",
        "R-18 pepADMET 자체 학습 (D-AA fine-tuning)",
        "R-21 Radiolysis Quencher DOE (Lutathera 참조)",
      ]],
    ];
    cards.forEach(([h, color, items], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 6.2, y = 1.5 + row * 2.7;
      s.addShape("rect", { x, y, w: 6.0, h: 2.5, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x, y, w: 6.0, h: 0.4, fill: { color }, line: { color, width: 0 } });
      s.addText(h, { x: x + 0.15, y: y + 0.05, w: 5.7, h: 0.35, fontFace: "Cambria", fontSize: 13, bold: true, color: C.textOnDark, margin: 0, valign: "middle" });
      const txt = items.map((it, k) => ({ text: "• " + it, options: { fontSize: 10.5, color: C.text, breakLine: k < items.length - 1 } }));
      s.addText(txt, { x: x + 0.2, y: y + 0.5, w: 5.7, h: 1.95, fontFace: "Calibri", margin: 0, valign: "top" });
    });
    addFooter(s, LBL, 18, TOTAL);
  }

  return pres.writeFile({ fileName: "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/docs/meet_preparation/pptx/main.pptx" });
}

// ===================================================================
// APPENDIX PPTX (15 슬라이드)
// ===================================================================
function buildAppendix() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "orchestrator session";
  pres.title = "시스템 점검 + Action Items 부록 — 2026-06-01";
  const TOTAL = 15;
  const LBL = "부록 — 초안";

  titleSlide(pres, "Appendix", "상세 점검 · Action Items 5블록 · References",
    "API 점검표 · 화면 인벤토리 · 코드 라인 인용 · 검증된 출처 · 2026-06-01");

  // === A-2 BE API 점검표 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domBE);
    addTitle(s, "BE API 점검표 (대표 라우터·엔드포인트)", "총 21 라우터 · 81 엔드포인트");
    const rows = [
      [{ text: "라우터", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "주요 엔드포인트", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "라이브", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "비고", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["status", "GET /api/status, /api/health", "🟢 200", "service id 식별"],
      ["runs", "GET /api/runs, /api/runs/{id}", "🟢", "TanStack 30s"],
      ["experiment", "POST /api/experiment/run /stop", "🟢", "3s 폴링"],
      ["admet", "POST /api/admet/batch", "🟢", "3-Layer 호출"],
      ["selectivity", "POST /api/selectivity/upload", "🟡", "K-1/K-2 영향"],
      ["flexpepdock", "GET/POST /api/flexpepdock/*", "🟢", "워커풀 연동"],
      ["strategies", "/api/strategies/*", "🟢", "blosum/esm/dual"],
      ["binding_pocket", "/api/binding_pocket/{recv}", "🟢", "—"],
      ["benchmark", "/api/benchmark/*", "🟡", "FE 일부 에러"],
      ["silo-a (v1)", "GET /api/v1/silo-a/health", "🔴 404", "등록 됐으나 실패"],
      ["archives", "GET /api/archives/top-k", "🔴", "stub → FE 에러"],
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [2.4, 4.5, 1.6, 4.0],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 10, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    addFooter(s, LBL, 2, TOTAL);
  }

  // === A-3 FE 화면 인벤토리 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domFE);
    addTitle(s, "FE 화면 인벤토리 (16 페이지)", "Primary 11 / Legacy 4 / 확인 필요 1");
    const rows = [
      [{ text: "#", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "페이지", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "라우트", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "역할", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Nav", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["1", "RunConsolePage", "/console", "실시간 모니터링", "Primary"],
      ["2", "RunLauncherPage", "/run/new", "새 런 설정", "Primary"],
      ["3", "CandidatePage", "/candidate/:id", "후보 상세 Mol* + ADMET", "Primary"],
      ["4", "SelectivityExplorer", "/selectivity-explorer", "SSTR 선택성 Mol* 3D", "Primary"],
      ["5", "ManualSelectivity", "/manual-selectivity", "수동 선택성 실행", "Primary"],
      ["6", "StrategyRunner", "/strategy-runner", "전략 선택/실행", "Primary"],
      ["7", "Benchmark", "/benchmark", "모델/전략 히트맵", "Secondary"],
      ["8", "WetlabOrder", "/wetlab/orders", "습식 주문서", "Secondary"],
      ["9", "BindingPocket", "/binding-pocket", "결합 포켓 파라미터", "Secondary"],
      ["10", "Settings", "/settings", "런타임 설정", "Secondary"],
      ["11", "About", "/about", "프로젝트 소개", "Secondary"],
      ["12-15", "Silo*/Combined/Selectivity (Legacy)", "—", "레거시 뷰", "미노출"],
      ["16", "CandidatePage (id 없음)", "/candidate", "id 필수 처리 `확인 필요`", "Primary"],
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [0.7, 3.0, 2.8, 4.5, 1.5],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9.5, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    addFooter(s, LBL, 3, TOTAL);
  }

  // === A-4 AI/vLLM 라이브 캡처 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domAI);
    addTitle(s, "AI / vLLM 상세 — 라이브 캡처", "실제 curl·ps·nvidia-smi 응답");

    s.addText("라이브 응답 캡처 (curl)", { x: 0.6, y: 1.4, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addShape("rect", { x: 0.6, y: 1.85, w: 12.2, h: 1.7, fill: { color: "263238" }, line: { color: "263238", width: 0 } });
    s.addText(
      "$ curl -s -w \"%{http_code} %{time_total}s\\n\" http://127.0.0.1:8002/v1/models\n200 0.005205s\n\n$ curl -X POST http://127.0.0.1:8002/v1/chat/completions -d '{...max_tokens=10}'\n{\"choices\":[{\"message\":{\"content\":\"Okay, so I need to figure out how to\"}}]}\n\n$ ps -o etime -p 1027766\n4-16:57:07",
      { x: 0.75, y: 1.95, w: 12, h: 1.6, fontFace: "Consolas", fontSize: 10.5, color: "B2DFDB", margin: 0 }
    );

    const gpuRows = [
      [{ text: "GPU", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Used", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Free", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Util", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Temp", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "비고", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["0", "14 MiB", "95317 MiB", "0%", "39°C", "타인 점유 (idle)"],
      ["1", "14 MiB", "95317 MiB", "0%", "41°C", "타인 점유 (idle)"],
      ["2", "14 MiB", "95317 MiB", "0%", "37°C", "본인 가용"],
      ["3", "83469 MiB", "11862 MiB", "72%", "47°C", "vLLM 로드"],
    ];
    s.addText("GPU 분포 (현재)", { x: 0.6, y: 3.85, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addTable(gpuRows, {
      x: 0.6, y: 4.2, w: 12.2, h: 1.0,
      colW: [0.8, 1.6, 1.8, 1.0, 1.0, 6.0],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 10, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });

    s.addText("vLLM 가동 로그 (마지막 라인)", { x: 0.6, y: 5.4, w: 12, h: 0.3, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addShape("rect", { x: 0.6, y: 5.75, w: 12.2, h: 1.15, fill: { color: "263238" }, line: { color: "263238", width: 0 } });
    s.addText(
      "INFO 06-01 05:10:09 [loggers.py:259] Engine 000:\n  Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 0.0 tokens/s,\n  Running: 0 reqs, Waiting: 0 reqs, GPU KV cache usage: 0.0%",
      { x: 0.75, y: 5.85, w: 12, h: 1.05, fontFace: "Consolas", fontSize: 10, color: "B2DFDB", margin: 0 }
    );
    addFooter(s, LBL, 4, TOTAL);
  }

  // === A-5 Action Item 카드 5블록 압축 (A-01~A-05) ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "Action Item 5블록 카드 (A-01 ~ A-05)", "① 원본 ② 방법 ③ 구현 ④ AI 관점 ⑤ 한 줄");

    const items = [
      ["A-01", "SSTR1/3/4/5 위치 지정 도킹", "cealign + binding_pocket JSON", "PR#61 머지, 5 receptor 좌표", "7T10 재검증 + selectivity 배수", "🟢 PR머지·구조ID 정합 6월"],
      ["A-02", "혈청 반감기 도구 비교", "L1 PlifePred + L2 pepMSND wrapper", "wrapper 통합, PR #117 미머지", "MD(RMSD) 2차, 실험 병행", "🔴 D-AA HIGH-BLOCKER"],
      ["A-03", "Fab-ADMET 검증·자체학습", "pepADMET 로컬 + ADMET-AI", "wrapper, HTTP 403, Layer 3 STUB", "pepADMET fine-tuning 산정", "🟡 검증 차단"],
      ["A-04", "Top-K 복합 스코어링", "Tier S/A/B + Critic + ensemble_router", "PR#62, enrichment 미정합", "PR#117 / Pareto 도입", "✅ PR머지·정합 6월"],
      ["A-05", "SST14 레퍼런스 ⊿G", "n회 도킹 Mean + 가변 임계", "main direct push, MM-GBSA 미", "gmx_MMPBSA·OpenFE 검토", "✅ baseline 확보"],
    ];
    const rows = [
      [{ text: "ID", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "원본", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "방법(②)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "구현(③)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "AI 관점(④)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "한 줄(⑤)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ...items,
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [0.7, 2.5, 2.4, 2.5, 2.2, 2.2],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    s.addText("→ 각 항목 상세 5블록: docs/meet_preparation/action_items/A-XX_*.md", { x: 0.6, y: 6.85, w: 12, h: 0.3, fontFace: "Consolas", fontSize: 9, italic: true, color: C.muted, margin: 0 });
    addFooter(s, LBL, 5, TOTAL);
  }

  // === A-6 Action Item 카드 5블록 (A-06~A-10) ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "Action Item 5블록 카드 (A-06 ~ A-10)", "디퓨전 도킹 · GPU 견적 · 최종 후보 · SSTR3 fix");
    const items = [
      ["A-06", "디퓨전 도킹 PoC", "DiffDock or 유사", "스크립트 존재, 본격 PoC 미", "Rosetta 대비 RMSD ≤2.0Å 평가", "🟡 미수행"],
      ["A-07", "GPU 견적 수집", "DGX H100/B200 매트릭스", "매트릭스 작성, 외부 견적 대기", "6월 회의 의사결정", "🟡 견적 대기"],
      ["A-08", "라이브러리 서버 마이그", "—", "PDF §2.3 배포 완료", "—", "❌ 삭제"],
      ["A-09", "최종 후보 3-4 + 합성 의뢰", "Tier S → PRST-001~004", "PR#63, wet-lab 미시작", "Ki assay + RI 표지", "✅ 후보 도출"],
      ["A-10", "SSTR3 도킹 에러 해결", "PDB sanitize", "PR#60 fix `5f5f7af`", "(회귀 테스트 유지)", "✅ 완료"],
    ];
    const rows = [
      [{ text: "ID", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "원본", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "방법(②)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "구현(③)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "AI 관점(④)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "한 줄(⑤)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ...items,
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 3.5,
      colW: [0.7, 2.5, 2.4, 2.5, 2.2, 2.2],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9.5, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });

    // 회의록 추가 결정 사항
    s.addShape("rect", { x: 0.6, y: 5.0, w: 12.2, h: 1.9, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 5.0, w: 0.08, h: 1.9, fill: { color: C.info }, line: { color: C.info, width: 0 } });
    s.addText("4/6 회의 핵심 결정 (Action Items 외 보조)", { x: 0.85, y: 5.1, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "7단계 다단계 선별 (서호성 제안): ", options: { bold: true, fontSize: 10.5, color: C.text } },
      { text: "Specificity → Serum Stability → Toxicity → Lead 확정 → AA Modification → RI-MD → 기타 예측\n", options: { fontSize: 10, color: C.muted } },
      { text: "SSTR2 결합 영역 77-314 한정 (ECL/TM 핵심 잔기 표 — 네거티브 디자인 정량 근거)\n", options: { fontSize: 10, color: C.text } },
      { text: "Radiolysis Quencher 4 조합: ", options: { bold: true, fontSize: 10.5, color: C.text } },
      { text: "Gentisic + Ascorbic + Methionine + Cysteine + Ethanol\n", options: { fontSize: 10, color: C.muted } },
      { text: "AA Modification 전략: ", options: { bold: true, fontSize: 10.5, color: C.text } },
      { text: "Met→Nle, Trp→5-F-Trp, Tyr→3-F-Tyr, Cys-Cys→Thioether/Lactam/Dicarba", options: { fontSize: 10, color: C.muted } },
    ], { x: 0.85, y: 5.5, w: 12, h: 1.3, fontFace: "Calibri", margin: 0 });
    addFooter(s, LBL, 6, TOTAL);
  }

  // === A-7 Dual-silo 핸드오프 코드 라인 인용 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.crit);
    addTitle(s, "Dual-silo 핸드오프 상세 (코드 라인 인용)", "분기 :835 → 병합 :981 → 공통 → aggregator");

    s.addShape("rect", { x: 0.6, y: 1.4, w: 12.2, h: 5.4, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 1.4, w: 0.08, h: 5.4, fill: { color: C.crit }, line: { color: C.crit, width: 0 } });

    s.addText("분기 — pipeline_local/orchestrator.py:835", { x: 0.85, y: 1.5, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "if dual_silo.enabled:  ", options: { fontSize: 11, color: C.text, fontFace: "Consolas" } },
      { text: "# 기본 False, CLI --dual 플래그 필요", options: { fontSize: 10, color: C.muted, italic: true } },
    ], { x: 1.0, y: 1.9, w: 11.5, h: 0.35, fontFace: "Consolas", margin: 0 });
    s.addText([
      { text: "    self._run_silo_a()    # (A2) 로컬 축약판", options: { fontSize: 11, color: C.text, fontFace: "Consolas" } },
    ], { x: 1.0, y: 2.2, w: 11.5, h: 0.35, fontFace: "Consolas", margin: 0 });
    s.addText([
      { text: "    self._run_silo_b()    # Silo B 본 흐름", options: { fontSize: 11, color: C.text, fontFace: "Consolas" } },
    ], { x: 1.0, y: 2.5, w: 11.5, h: 0.35, fontFace: "Consolas", margin: 0 });

    s.addText("합류 — orchestrator.py:981  _run_dual_silo()", { x: 0.85, y: 3.0, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "# Silo A 후보 seq_id 에 'a_' 접두어\n", options: { fontSize: 10, color: C.muted, italic: true, fontFace: "Consolas" } },
      { text: "merged = BranchOutputs(dual_mode=True)\n", options: { fontSize: 11, color: C.text, fontFace: "Consolas" } },
      { text: "# → Step04 ESMFold → Step05 Boltz → Step06 Rosetta 공통 경로\n", options: { fontSize: 10, color: C.muted, italic: true, fontFace: "Consolas" } },
      { text: "# Step06:1175  _build_rosetta_chain_result()  로 silo별 집계", options: { fontSize: 10, color: C.muted, italic: true, fontFace: "Consolas" } },
    ], { x: 1.0, y: 3.4, w: 11.5, h: 1.3, fontFace: "Consolas", margin: 0 });

    s.addText("랭킹 — pipelines/orchestration/aggregator.py", { x: 0.85, y: 4.85, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "rank_fusion_weighted_sum(candidates, silo_weights)\n", options: { fontSize: 11, color: C.text, fontFace: "Consolas" } },
      { text: "silo_weights = {\"A\": 0.34, \"B\": 0.33, \"C\": 0.33}\n", options: { fontSize: 11, color: C.accent, fontFace: "Consolas" } },
      { text: "# policy.py:  required_silos = [\"A\", \"B\", \"C\"]  ← Silo C 실 구현 없음", options: { fontSize: 10, color: C.crit, italic: true, fontFace: "Consolas" } },
    ], { x: 1.0, y: 5.25, w: 11.5, h: 1.1, fontFace: "Consolas", margin: 0 });

    s.addText("⚠ 2026-05-27 phase 2 smoke는 --dual 미활성 → 위 흐름의 종단 라이브 검증 0건", { x: 0.85, y: 6.4, w: 12, h: 0.35, fontFace: "Calibri", fontSize: 11, italic: true, color: C.crit, margin: 0 });

    addFooter(s, LBL, 7, TOTAL);
  }

  // === A-8 Reflection plan 전체 (요약) ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "반영 계획 — 21건 전체 표 (R-01 ~ R-21)", "Owner · 완료기준 · committed/proposed · 추적성");

    const rows = [
      [{ text: "ID", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "항목", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "Owner", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "P", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "분류", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["R-01", "MCP filesystem 경로 수정", "DongJu", "P0", "committed"],
      ["R-02", "BE silo_a 404 정정", "engineer-backend", "P0", "committed"],
      ["R-03", "FE smoke 'More' 갱신", "reviewer-uiux", "P0", "committed"],
      ["R-04", "K-1/K-2 selectivity 정정", "engineer-backend", "P0", "committed"],
      ["R-05", "PR #117 머지 결정", "engineer-backend+pharma", "P0", "proposed"],
      ["R-06", "enrichment 정합", "reviewer-science", "P0", "proposed"],
      ["R-07", "Layer 3 최소 구현", "engineer-backend+pharma", "P0", "proposed"],
      ["R-08", "PRST ranking 재검증", "engineer-backend+pharma", "P0", "committed"],
      ["R-09", "DiffDock PoC 실행", "engineer-backend+infra", "P0", "committed"],
      ["R-10", "GPU 견적 2건 수령", "서호성·안기범", "P0", "proposed"],
      ["R-11", "MM-GBSA 검토 (gmx_MMPBSA/OpenFE)", "reviewer-pharma+backend", "P1", "proposed"],
      ["R-12", "A-02 벤치마크 R²/Spearman", "engineer-backend+pharma", "P1", "committed"],
      ["R-13", "Silo A 이중 구현 통합", "reviewer-science", "P1", "proposed"],
      ["R-14", "Silo C 정책 결정", "reviewer-science", "P1", "proposed"],
      ["R-15", "25분 SLA 재평가", "engineer-backend", "P1", "committed"],
      ["R-16", "orchestrator.py 분리", "reviewer-code", "P1", "proposed"],
      ["R-17", "endpoint 2건 + PR #11", "engineer-backend", "P1", "committed"],
      ["R-18", "pepADMET 자체 학습 산정", "engineer-backend+pharma", "P1", "proposed"],
      ["R-19", "Schrödinger 도입 검토", "서호성·DongJu", "P2", "proposed"],
      ["R-20", "A-01 7T10 vs 7XNA 정합", "engineer-backend", "P2", "committed"],
      ["R-21", "Radiolysis Quencher DOE", "engineer-backend+pharma", "P2", "proposed"],
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [0.7, 4.5, 3.2, 0.7, 3.4],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    addFooter(s, LBL, 8, TOTAL);
  }

  // === A-9 References 검증 통과 목록 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.info);
    addTitle(s, "References — 검증 통과 19건 / 제외 4건", "모든 인용은 공식 출처·DOI·repo 검증 (할루시네이션 0)");

    const rows = [
      [{ text: "분류", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "자원", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "출처 (DOI / URL)", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } },
       { text: "AI", options: { bold: true, fill: { color: C.bgDark }, color: C.textOnDark } }],
      ["📑 논문", "Gervasoni 2023 JCIM", "DOI: 10.1021/acs.jcim.3c00712", "A-01"],
      ["📑 논문", "Gervasoni 2024 CSBJ", "DOI: 10.1016/j.csbj.2024.03.005", "A-01"],
      ["📑 논문", "PlifePred (Mathur 2018)", "DOI: 10.1371/journal.pone.0196829", "A-02"],
      ["📑 논문", "N-end Rule (Bachmair 1986)", "DOI: 10.1126/science.3018930", "A-02"],
      ["📑 논문", "pepADMET", "DOI: 10.1021/acs.jcim.5c02518", "A-03"],
      ["📑 논문", "ADMET-AI (Swanson)", "academic.oup.com/bioinformatics btae416", "A-03"],
      ["📑 논문", "gmx_MMPBSA", "DOI: 10.1021/acs.jctc.1c00645", "A-05"],
      ["📑 논문", "DiffDock (Corso 2023)", "arXiv:2210.01776", "A-06"],
      ["📑 논문", "Boltz-2 (CASP16 1위)", "PMC12262699", "A-05·A-06"],
      ["📦 Repo", "pepADMET", "github.com/ifyoungnet/pepADMET (GPL-3.0)", "A-03"],
      ["📦 Repo", "gmx_MMPBSA", "github.com/Valdes-Tresanco-MS/gmx_MMPBSA", "A-05"],
      ["📦 Repo", "Boltz-2", "github.com/jwohlwend/boltz (MIT)", "A-05·A-06"],
      ["📦 Repo", "DiffDock", "github.com/gcorso/DiffDock", "A-06"],
      ["🔧 도구", "OpenFE 1.0", "openfree.energy (2024-05 안정)", "A-05"],
      ["🔧 도구", "ADMETlab 3.0", "admetlab3.scbdd.com", "A-03"],
      ["🔧 도구", "pymoo (Pareto/NSGA-II)", "pymoo.org", "A-04"],
      ["🔧 도구", "NVIDIA H100", "nvidia.com/en-us/data-center/h100/", "A-07"],
      ["⚖ 규제", "Lutathera FDA DailyMed", "NDA 208700 (2026-01-15 갱신)", "Radiolysis"],
    ];
    s.addTable(rows, {
      x: 0.4, y: 1.4, w: 12.5, h: 5.5,
      colW: [1.4, 3.0, 6.7, 1.4],
      border: { type: "solid", pt: 0.5, color: C.border },
      fontFace: "Calibri", fontSize: 9, color: C.text,
      align: "left", valign: "middle", autoPage: false,
    });
    s.addText("제외: PeptideStability(ML 도구명 미발견), PeptideRanker URL(timeout), NVIDIA DGX B200(추가 확인), openfree-energy.org→openfree.energy",
      { x: 0.6, y: 6.85, w: 12.5, h: 0.3, fontFace: "Calibri", fontSize: 9, italic: true, color: C.crit, margin: 0 });
    addFooter(s, LBL, 9, TOTAL);
  }

  // === A-10 약리학 전문가 의견 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s, C.domBE);
    addTitle(s, "약리학 전문가 견해 (reviewer-pharma)", "A-02 · A-03 · A-04 · A-09 — D-AA · Layer 3 · OOD framework");

    s.addShape("rect", { x: 0.6, y: 1.4, w: 12.2, h: 5.4, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
    s.addShape("rect", { x: 0.6, y: 1.4, w: 0.08, h: 5.4, fill: { color: C.domBE }, line: { color: C.domBE, width: 0 } });
    s.addText("총평 + 핵심 권고", { x: 0.85, y: 1.5, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 14, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "D-AA HIGH-BLOCKER는 본 프로젝트의 약리학 핵심 격차이며, Layer 3 (DOTA proxy) STUB과 함께 ", options: { fontSize: 11, color: C.text } },
      { text: "in silico 단독 의사결정이 불가능한 상태", options: { fontSize: 11, color: C.crit, bold: true } },
      { text: "이다. PRST-001~004는 도출되었으나 ADMET=1.00은 OOD 외삽 위험이므로 wet-lab Ki / Stability assay 병행이 필수이다.", options: { fontSize: 11, color: C.text } },
    ], { x: 0.85, y: 1.85, w: 12, h: 0.8, fontFace: "Calibri", margin: 0 });

    s.addText("Action Item별 향후 방향", { x: 0.85, y: 2.8, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addText([
      { text: "▸ A-02 (반감기)", options: { bold: true, fontSize: 11, color: C.text } },
      { text: ": pepADMET D-AA 처리 정밀 검증 + MD(RMSD) 2차 구현. 벤치마크 R²/Spearman 측정 (R-12).\n", options: { fontSize: 10.5, color: C.text } },
      { text: "▸ A-03 (ADMET)", options: { bold: true, fontSize: 11, color: C.text } },
      { text: ": Layer 3 STUB → OOD 경고 최소 구현 (R-07). pepADMET fine-tuning 데이터·GPU 산정 (R-18).\n", options: { fontSize: 10.5, color: C.text } },
      { text: "▸ A-04 (스코어링)", options: { bold: true, fontSize: 11, color: C.text } },
      { text: ": PR #117 머지 결정 후 enrichment 정합 (R-05, R-06). Pareto front 검토.\n", options: { fontSize: 10.5, color: C.text } },
      { text: "▸ A-09 (후보)", options: { bold: true, fontSize: 11, color: C.text } },
      { text: ": K-1/K-2 정정 후 ranking 재검증 (R-08). wet-lab Ki·Stability·Hemolysis assay 설계.", options: { fontSize: 10.5, color: C.text } },
    ], { x: 0.85, y: 3.15, w: 12, h: 2.7, fontFace: "Calibri", margin: 0 });

    s.addText("6월 회의 의사결정 요청 (약리학 관점)", { x: 0.85, y: 6.0, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addText("① D-AA 해소 전략 (MD 2차 vs 외부 도구)   ② pepADMET 자체 학습 진행 여부   ③ wet-lab assay 시점·protocol",
      { x: 0.85, y: 6.35, w: 12, h: 0.4, fontFace: "Calibri", fontSize: 11, color: C.text, margin: 0 });

    s.addText("상세: docs/meet_preparation/expert_opinions/pharma_review.md (별도 작성 예정)", { x: 0.6, y: 6.85, w: 12.2, h: 0.3, fontFace: "Consolas", fontSize: 9, italic: true, color: C.muted, margin: 0 });
    addFooter(s, LBL, 10, TOTAL);
  }

  // === A-11 생명공학·화학·수학 전문가 의견 통합 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "생명공학 · 화학 · 수학 전문가 견해 통합", "각 도메인의 향후 방향 + 타개 방법 (검증된 출처)");

    const exps = [
      ["🧬 생명공학 (reviewer-biology) — 🚨 HIGH 영향 발견", C.domSiloB, [
        "🚨 7XNA = octreotide 8-mer (Cys2-Cys7 ring) — SST-14 14-mer (Cys3-Cys14 12-잔기 루프)와 ring span 근본 다름. 회의록 §2.1이 7T10 명시한 이유",
        "🚨 Boltz 도킹 3종 모두 포켓 외부 배치: centroid-pocket 거리 78.2/66.4/79.7 Å (포켓 반경 13.0 Å의 5-6배) — ΔG 기준선 553.857 REU는 결합 상태 에너지 아님",
        "⚠ Boltz_2의 CYS A3-CYS A14 SG-SG 거리 0.712 Å (표준 2.03±0.05) — geometry 실패로 폐기 대상",
        "ECL/TM 잔기 표(`negative_design_residues_SSTR2.json`)는 정의됐으나 per-residue energy decomposition 미구현 — 정량적 네거티브 디자인 미완",
        "R-04(K-1/K-2 정정) + R-20(7T10 재검증) 동시 선행 필수. 참조: Gervasoni 2023 JCIM DOI:10.1021/acs.jcim.3c00712, 2024 CSBJ DOI:10.1016/j.csbj.2024.03.005",
      ]],
      ["⚗️ 화학 (reviewer-chemistry)", C.domTool, [
        "Met→Nle, Lys→Orn ✅ 표준 Fmoc SPPS 즉시 가능 / 5-F-Trp·3-F-Tyr △ 국내 빌딩블록 조달 변수 (벤더 확인)",
        "⚠ Cys SS bond 내 Cys에 D-AA 적용 = ERROR (Veber 1978 PNAS, 실측 활성 ~10× 감소)",
        "¹⁷⁷Lu DOTA 라벨링: pH 4.0-4.5, 95°C, 15-30분 (Lutathera NDA 208700 검증). DOTA는 펩타이드당 1개 (stoichiometry C-07)",
        "Quencher 정확 농도: Gentisic acid 0.63 mg/mL + Ascorbic acid 2.8 mg/mL (Lutathera 제형에서 직접 검증된 유일 조합)",
        "modification_conflict.py 3개 갭: ① C-07 mod_type 어휘 단절, ② thioether/lactam/dicarba 전용 규칙 부재, ③ 불소화 AA 위치 경고 부재",
      ]],
      ["📊 수학·통계 (reviewer-math) — 🚨 다목적 최적화 격차", C.domAI, [
        "🚨 Pareto front 현재 비활성: PARETO_MIN_CANDIDATES = 50, PRST-001~004 (n=4) 운영에서 미계산 → Tier-S는 WSS top 20% 단일 기준",
        "🚨 K-1/K-2 결함 시 selectivity_ratio = ΔG_SSTR2 의 단조 변환 → WSS 가중 0.35+0.25=0.60이 단일 지표에 집중 → 다목적 ≡ 단목적",
        "⚠ `ref * 0.9` 가변 임계값: REU 음수이므로 -85.5 REU는 더 느슨함. '10% 허용'이 더 엄격한 의도였다면 `ref * 1.1 = -104.5 REU` 정정 필요",
        "n회 반복 레퍼런스: 단일 -95.024 REU만 보고 → SE + 95% CI + n 명시 필수 (현재 단일 점 추정)",
        "DiffDock PoC 통계 설계: paired Wilcoxon + n ≥ 31 pose. unpaired·n<20은 Wilson 95% CI 너무 넓어 KPI 검증 불가. 참조: gmx_MMPBSA DOI:10.1021/acs.jctc.1c00645",
      ]],
    ];
    exps.forEach(([h, col, items], i) => {
      const y = 1.4 + i * 1.75;
      s.addShape("rect", { x: 0.6, y, w: 12.2, h: 1.65, fill: { color: C.bgElev }, line: { color: C.border, width: 1 } });
      s.addShape("rect", { x: 0.6, y, w: 0.08, h: 1.65, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(h, { x: 0.85, y: y + 0.05, w: 12, h: 0.35, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
      const txt = items.map((t, k) => ({ text: "▸ " + t, options: { fontSize: 10, color: C.text, breakLine: k < items.length - 1 } }));
      s.addText(txt, { x: 0.85, y: y + 0.42, w: 12, h: 1.2, fontFace: "Calibri", margin: 0, valign: "top" });
    });
    addFooter(s, LBL, 11, TOTAL);
  }

  // === A-12 알려진 이슈 + 근거 로그 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "알려진 이슈 — 근거 로그 발췌", "코드 라인 + 로그 직접 인용");

    s.addText("실패 잡 샘플 — runs_local/flexpepdock_jobs/91e44bd1-.../status.json", { x: 0.6, y: 1.4, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addShape("rect", { x: 0.6, y: 1.85, w: 12.2, h: 1.4, fill: { color: "263238" }, line: { color: "263238", width: 0 } });
    s.addText(
      "{\n  \"state\": \"failed\",\n  \"progress\": 0.2,\n  \"error_message\": \"사용자에 의해 취소됨\",\n  \"started_at\": \"2026-05-21T01:39:28Z\",\n  \"finished_at\": \"2026-05-21T03:03:11Z\"\n}",
      { x: 0.75, y: 1.95, w: 12, h: 1.3, fontFace: "Consolas", fontSize: 10, color: "B2DFDB", margin: 0 }
    );
    s.addText("→ 실제 실패 아닌 의도된 취소. 7개월 전 기록.", { x: 0.6, y: 3.3, w: 12, h: 0.3, fontFace: "Calibri", fontSize: 10, italic: true, color: C.muted, margin: 0 });

    s.addText("워커 로그 — /tmp/flexpepdock_worker_1.log (마지막)", { x: 0.6, y: 3.7, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addShape("rect", { x: 0.6, y: 4.15, w: 12.2, h: 1.2, fill: { color: "263238" }, line: { color: "263238", width: 0 } });
    s.addText(
      "2026-05-26 09:04:29,800 [INFO] flexpepdock_worker: SIGTERM 수신 — graceful 종료 예약\n2026-05-26 09:04:31,617 [INFO] flexpepdock_worker: [worker-1] FlexPepDock 워커 종료\n2026-05-26 09:05:17,147 [INFO] flexpepdock_worker: FlexPepDock 워커 시작 (worker_id=worker-1, PID=3362310)",
      { x: 0.75, y: 4.25, w: 12, h: 1.1, fontFace: "Consolas", fontSize: 9.5, color: "B2DFDB", margin: 0 }
    );

    s.addText("BE health 응답 — :8787/api/health", { x: 0.6, y: 5.5, w: 12, h: 0.4, fontFace: "Cambria", fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addShape("rect", { x: 0.6, y: 5.95, w: 12.2, h: 0.9, fill: { color: "263238" }, line: { color: "263238", width: 0 } });
    s.addText(
      "$ curl -s http://127.0.0.1:8787/api/health\n{\"status\":\"ok\",\"timestamp\":1780022995.32,\"mode\":\"local\"}",
      { x: 0.75, y: 6.05, w: 12, h: 0.8, fontFace: "Consolas", fontSize: 10, color: "B2DFDB", margin: 0 }
    );
    addFooter(s, LBL, 12, TOTAL);
  }

  // === A-13 확인 필요 항목 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSideBar(s);
    addTitle(s, "확인 필요 항목 (정직 명시)", "본 점검에서 단정하지 못한 부분 — 추후 검증 대상");
    const items = [
      "Silo C 실체 — policy.py·aggregator의 가중 0.33 가정만 있고 구현/문서/실행 흔적 0건. 의도된 placeholder인지, 미완 작업인지 확인 필요",
      "Step05 Boltz 25분 SLA — audit(5/27) 미완 보고. 본 점검(6/1) 시점 재검증 기록 없음",
      "BE /api/v1/silo-a/health 404 — 1회성 import 오류인지, 영구 문제인지 BE 재기동 후 재현",
      "PR #117/#112/#11 — audit 시점(5/27) 상태와 6/1 현재 상태 비교 필요",
      "FE 레거시 컴포넌트 OKLCH 토큰 마이그레이션 완료 여부 미확인",
      "usePipelineStatus 이중 폴링 가능성 (setInterval + TanStack refetchInterval)",
      "Lanreotide t½ 정확치 — 회의록 미기재, 외부 출처 확인 필요",
      "PeptideStability(ML) 공식 도구 존재 여부 — 검증 실패",
      "NVIDIA DGX B200 사양·납기·가격 — H100 외 추가 확인",
      "스크린샷 캡처는 브라우저 환경 필요 — 본 점검은 라이브 curl·로그·코드로 대체",
    ];
    s.addText(items.map((it, i) => ({
      text: `${i + 1}. ${it}`,
      options: { color: C.text, fontSize: 11, breakLine: i < items.length - 1 },
    })), {
      x: 0.6, y: 1.4, w: 12.2, h: 5.5,
      fontFace: "Calibri", paraSpaceAfter: 5, margin: 0, valign: "top",
    });
    addFooter(s, LBL, 13, TOTAL);
  }

  // === A-14 종합 의견 (마지막 — 보고서·메인·부록 공통) ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bgDark };
    s.addShape("rect", { x: 12.7, y: 0, w: 0.6, h: 7.5, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
    s.addText("종합 향후 진행 방향 의견 (3 권고)", { x: 0.6, y: 0.5, w: 11.5, h: 0.7, fontFace: "Cambria", fontSize: 28, bold: true, color: C.textOnDark, margin: 0 });
    s.addText("의견·제언 — 모든 핵심 주장에 검증된 출처 연결", { x: 0.6, y: 1.2, w: 11.5, h: 0.4, fontFace: "Calibri", fontSize: 13, italic: true, color: C.accentLight, margin: 0 });

    const recs = [
      ["권고 1: wet-lab 실측 사이클의 빠른 진입",
        "PRST-001~004 합성 + Ki / Serum Stability / Hemolysis assay 시작. K-1/K-2 정정 후 ranking 재검증.",
        "근거: audit §1.1 ④ (3 reviewer 공통), 서호성 의견 (PDF p.7), Lutathera FDA DailyMed NDA 208700"],
      ["권고 2: 정밀 계산 단계 도입 — gmx_MMPBSA → OpenFE 단계적",
        "1차 MM-GBSA (gmx_MMPBSA v1.6.5), 2차 OpenFE 1.0 FEP/TI. A-07 GPU와 연동. 서호성 의견 (PDF p.8) 반영.",
        "근거: gmx_MMPBSA DOI:10.1021/acs.jctc.1c00645, OpenFE openfree.energy (2024-05 안정)"],
      ["권고 3: D-AA / cyclic / DOTA 도메인 격차 해소",
        "Layer 3 OOD 경고 최소 구현 + pepADMET D-AA 처리 정밀 확인 + 자체 학습 자원 산정.",
        "근거: pepADMET DOI:10.1021/acs.jcim.5c02518 (19 ADMET 엔드포인트, GPL-3.0)"],
    ];
    recs.forEach(([h, body, src], i) => {
      const y = 1.95 + i * 1.55;
      s.addShape("rect", { x: 0.6, y, w: 12.2, h: 1.4, fill: { color: "263238" }, line: { color: C.accent, width: 1 } });
      s.addText(h, { x: 0.85, y: y + 0.05, w: 11.7, h: 0.4, fontFace: "Cambria", fontSize: 14, bold: true, color: C.accentLight, margin: 0 });
      s.addText(body, { x: 0.85, y: y + 0.45, w: 11.7, h: 0.5, fontFace: "Calibri", fontSize: 11, color: C.textOnDark, margin: 0 });
      s.addText(src, { x: 0.85, y: y + 0.95, w: 11.7, h: 0.4, fontFace: "Consolas", fontSize: 9, italic: true, color: "B2DFDB", margin: 0 });
    });

    s.addText("연구·운영 종합 의견: AI 모델 정확도는 항상 OOD 외삽 위험을 안고 있으므로, 인간 전문가 (서호성·김유종·김동주 박사 등) 검토를 최종 의사결정에 의무화",
      { x: 0.6, y: 6.85, w: 12.2, h: 0.4, fontFace: "Calibri", fontSize: 10.5, italic: true, color: "B0BEC5", align: "center", margin: 0 });
  }

  // === A-15 참조 자료 목록 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bgDark };
    s.addShape("rect", { x: 12.7, y: 0, w: 0.6, h: 7.5, fill: { color: C.accent }, line: { color: C.accent, width: 0 } });
    s.addText("Appendix 참조 자료", { x: 0.6, y: 0.5, w: 11.5, h: 0.7, fontFace: "Cambria", fontSize: 26, bold: true, color: C.textOnDark, margin: 0 });
    s.addText("본 보고의 모든 진술은 아래 파일·로그·라이브 응답·검증된 출처에 근거", { x: 0.6, y: 1.2, w: 11.5, h: 0.4, fontFace: "Calibri", fontSize: 12, italic: true, color: C.accentLight, margin: 0 });

    const refs = [
      "docs/meet_preparation/daily_system_inspection_report_20260601.md  ← 본 부록 출처 보고서",
      "docs/meet_preparation/action_items/{00_master_table.md, A-01~A-07,A-09,A-10}.md  ← 9개 Action Item 5블록 카드",
      "docs/meet_preparation/reflection_plan/00_master_plan.md  ← 21건 반영 계획 (committed 10 / proposed 11)",
      "docs/meet_preparation/references/{references.md, papers/, libraries/, repos/, benchmarks/}  ← 19 검증 통과 / 4 제외",
      "docs/meet_preparation/expert_opinions/{pharma,biology,chemistry,math}_review.md  ← 전문가 4명 견해",
      "docs/meet_preparation/inspect_evidence/{backend, frontend, silo_a, silo_b_docking, dual_silo_actions}.md",
      "docs/meet_preparation/assets/design_system.md  ← 본 PPT 디자인 토큰",
      "docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf  ← 회의록 원본 (9쪽)",
      "docs/meet_log/2026-04-06_action_items/  ← 5/26 1차 작성 (PR 머지 상태 추적)",
      "/tmp/vllm_8002.log  ·  /tmp/flexpepdock_worker_{1..4}.log  ← 라이브 로그",
      "runs_local/dual_final_03/local_20260402_1055_iter01/  ← PRST-001~004 산출물",
    ];
    s.addText(refs.map((r, i) => ({
      text: "·  " + r,
      options: { color: C.textOnDark, fontSize: 10, breakLine: i < refs.length - 1, fontFace: "Calibri" },
    })), {
      x: 0.6, y: 2.0, w: 12.5, h: 4.5,
      paraSpaceAfter: 3, margin: 0, valign: "top",
    });
    s.addText("orchestrator 세션 · 2026-06-01 · 초안 / 현재 상태 공유 · 최종 성과 발표 아님",
      { x: 0.6, y: 7.0, w: 12.5, h: 0.4, fontFace: "Calibri", fontSize: 10, italic: true, color: "B0BEC5", margin: 0 });
  }

  return pres.writeFile({ fileName: "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/docs/meet_preparation/pptx/appendix.pptx" });
}

(async () => {
  console.log("Building main PPTX...");
  await buildMain();
  console.log("Building appendix PPTX...");
  await buildAppendix();
  console.log("Done.");
})();
