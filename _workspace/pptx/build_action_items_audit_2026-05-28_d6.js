// Action Items 9건 원본 요구 vs 실행 결과 비교 PPTX — D-6 갱신본
// 20 슬라이드 — PR #111 매트릭스·ADMET-AI 차트 + PR #113 OOD + PR #112 부록 + 슬라이드 19–20

const path = require("path");
const pptxgen = require("pptxgenjs");

/** PR #111 — matplotlib 산출물 (build_prst_admet_ai_charts.py, raw JSON만 사용) */
const IMG_ADMET_SCATTER = path.join(
  __dirname,
  "..",
  "admet_ai_local",
  "charts",
  "admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png"
);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.author = "PRST_N_FM Team";
pres.title = "Action Items 9건 — Audit · D-6 갱신 (PR #111/#113, 2026-05-28 회의 준비)";

// Berry & Cream 팔레트 (audit/검증 문서에 적합)
const C = {
  primary: "6D2E46",      // berry
  secondary: "A26769",    // dusty rose
  accent: "028090",       // teal (대비 강조)
  dark: "1F1B24",         // 거의 검정
  light: "FAF6F2",        // cream
  bg: "FFFFFF",
  text: "1F1B24",
  textMute: "5C5660",
  textDim: "9C9398",
  border: "E5DCD4",
  warn: "D97706",
  neg: "B91C1C",
  pos: "15803D",
};

const FONT_H = "Palatino";
const FONT_B = "Garamond";

function addFooter(s, p, total) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.25, w: 13.3, h: 0.25, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("Action Items Audit · Deck 2026-05-28 D-6 (PR #111·#113·#112·#109 반영)", { x: 0.4, y: 7.25, w: 10.1, h: 0.25, fontSize: 9, color: C.light, fontFace: FONT_B, valign: "middle" });
  s.addText(`${p} / ${total}`, { x: 12.5, y: 7.25, w: 0.6, h: 0.25, fontSize: 9, color: C.light, fontFace: FONT_B, valign: "middle", align: "right" });
}

function addTitle(s, t, sub) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.15, h: 7.25, fill: { color: C.primary }, line: { type: "none" } });
  s.addText(t, { x: 0.5, y: 0.3, w: 12.5, h: 0.7, fontSize: 28, bold: true, color: C.dark, fontFace: FONT_H, margin: 0 });
  if (sub) s.addText(sub, { x: 0.5, y: 0.95, w: 12.5, h: 0.4, fontSize: 14, color: C.textMute, fontFace: FONT_B, margin: 0, italic: true });
}

// 액션 아이템 1건 슬라이드 헬퍼
function aiSlide(id, name, originalReq, kpi, executed, deliverables, gap, status) {
  const s = pres.addSlide();
  addTitle(s, `${id} — ${name}`, `회의 KAERI-AIRL-MOM-2026-003 (2026-04-06) → 실행 스냅샷 2026-05-19`);

  // 좌측: 원본 요구
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 0.1, h: 5.3, fill: { color: C.secondary }, line: { type: "none" } });
  s.addText("회의 원본 요구", { x: 0.8, y: 1.6, w: 5.6, h: 0.4, fontSize: 14, bold: true, color: C.secondary, fontFace: FONT_H });

  s.addText("목표", { x: 0.8, y: 2.0, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(originalReq, { x: 0.8, y: 2.3, w: 5.6, h: 2.0, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "top" });

  s.addText("KPI / 완료 기준", { x: 0.8, y: 4.6, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(kpi, { x: 0.8, y: 4.9, w: 5.6, h: 1.8, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "top" });

  // 우측: 실행 결과
  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 1.5, w: 0.1, h: 5.3, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("실행 결과 (2026-05-19 스냅샷)", { x: 7.1, y: 1.6, w: 5.6, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });

  s.addText("수행 + 산출물", { x: 7.1, y: 2.0, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(executed, { x: 7.1, y: 2.3, w: 5.6, h: 2.0, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "top" });

  s.addText("산출 파일 / PR", { x: 7.1, y: 4.6, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(deliverables, { x: 7.1, y: 4.9, w: 5.6, h: 1.4, fontSize: 10, color: C.text, fontFace: "Consolas", valign: "top" });

  // 하단: 갭 + 상태
  const stColor = status === "✓ 달성" ? C.pos : status.includes("부분") ? C.warn : C.neg;
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.9, w: 12.3, h: 0.3, fill: { color: stColor }, line: { type: "none" } });
  s.addText(`상태: ${status}  ·  갭: ${gap}`, { x: 0.7, y: 6.9, w: 12.0, h: 0.3, fontSize: 11, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
}

const TOTAL = 20;

// ───────────────────────────────────────────────
// Slide 1 — 타이틀
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.2, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });

  s.addText("KAERI-AIRL-MOM-2026-003", { x: 0.5, y: 1.5, w: 12.3, h: 0.6, fontSize: 14, color: C.secondary, bold: true, fontFace: FONT_B, charSpacing: 8 });
  s.addText("Action Items 9건", { x: 0.5, y: 2.1, w: 12.3, h: 1.0, fontSize: 56, color: "FFFFFF", bold: true, fontFace: FONT_H });
  s.addText("원본 요구 vs 실행 결과 — Audit", { x: 0.5, y: 3.2, w: 12.3, h: 0.7, fontSize: 24, color: C.secondary, italic: true, fontFace: FONT_H });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.5, w: 6.0, h: 2.0, fill: { color: "FFFFFF", transparency: 90 }, line: { color: C.secondary, width: 1 } });
  s.addText("회의일", { x: 0.7, y: 4.6, w: 5.6, h: 0.3, fontSize: 11, color: C.secondary, fontFace: FONT_B });
  s.addText("2026-04-06", { x: 0.7, y: 4.9, w: 5.6, h: 0.5, fontSize: 24, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("Deck 갱신일", { x: 0.7, y: 5.5, w: 5.6, h: 0.3, fontSize: 11, color: C.secondary, fontFace: FONT_B });
  s.addText("2026-05-28", { x: 0.7, y: 5.8, w: 5.6, h: 0.5, fontSize: 24, bold: true, color: "FFFFFF", fontFace: FONT_H });

  s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: 4.5, w: 6.0, h: 2.0, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("회의 · 2026-05-28 (목)", { x: 7.1, y: 4.55, w: 5.6, h: 0.26, fontSize: 10, color: C.light, fontFace: FONT_B });
  s.addText("발표 준비 D-6 deck", { x: 7.1, y: 4.78, w: 5.6, h: 0.45, fontSize: 22, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("PR #85·#111·#113 main", { x: 7.1, y: 5.28, w: 5.6, h: 0.38, fontSize: 18, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("9 / 9 audit + 매트릭스·OOD·OOD 차트 반영\n(정직 표기 · 외삽 한계 명시)", { x: 7.1, y: 5.62, w: 5.6, h: 0.78, fontSize: 11, color: C.light, fontFace: FONT_B });

  s.addText("3-Layer Ensemble framework 완성. 시도한 도구·학습·외부 컨택 모두 정직히 보고. 단독 결정 X, 다중 도구 견제 + wet-lab 병행 권고.",
    { x: 0.5, y: 6.72, w: 12.3, h: 0.55, fontSize: 10, color: C.secondary, fontFace: FONT_B, italic: true, align: "center" });
}

// ───────────────────────────────────────────────
// Slide 2 — Audit 매트릭스
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Audit 매트릭스 — 9건 종합", "회의 요구 충족도 + 갭 + 후속 작업");

  const rows = [
    [{ text: "ID", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "회의 요구 (요약)", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "충족도", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
     { text: "갭 / 후속", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["A-01", "SSTR1/3/4/5 위치 지정 도킹 좌표 + 정렬", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "TM-align 미설치 → PyMOL cealign 사용 (RMSD 2.77-3.13Å 충족)"],
    ["A-02", "혈청 반감기 도구 5종+ 비교 + 정확도", { text: "△ 부분", options: { color: C.warn, bold: true } }, "도구 7종 비교 완료, but D-AA 지원 도구 0개 (HIGH-BLOCKER)"],
    ["A-03", "Fab-ADMET 정확도 + 자체 학습 가능성", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "\"Fab-ADMET\"=pepADMET 오기재 확정, D-AA 한계 식별"],
    ["A-04", "복합 스코어링 + Tier 분류", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "Pareto+WSS+Tier S/A/B/FAIL, 73 tests pass"],
    ["A-05", "SST14 reference dG (n≥10)", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "mean 553.857 σ=4.024 (KPI σ<5 충족), complex 부재 한계 명시"],
    ["A-06", "Diffusion 도킹 PoC", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "DiffPepDock 평가 완료 → NOT_RECOMMENDED (SS bond X)"],
    ["A-07", "GPU 인프라 견적 수집", { text: "△ 부분", options: { color: C.warn, bold: true } }, "템플릿 + 점검 완료, 실 견적은 사용자 책임"],
    ["A-08", "(회의 당일 삭제)", { text: "N/A", options: { color: C.textDim, bold: true } }, "외부망 H100×8 배포 완료로 불필요 — 정상 종료"],
    ["A-09", "최종 후보 3-4개 + 합성 의뢰서", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "PRST-001~004 (Tier S/B/B/B) + 의뢰서 4건"],
    ["A-10", "SSTR3_8XIR 도킹 fix", { text: "✓ 달성", options: { color: C.pos, bold: true } }, "chain 선택 + 24 tests, smoke ddg=-92.09"],
  ];

  s.addTable(rows, {
    x: 0.5, y: 1.55, w: 12.3,
    colW: [0.7, 4.0, 1.3, 6.3],
    fontSize: 10, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.42,
    valign: "middle",
  });

  // 하단 통계
  const counts = [
    { label: "✓ 완전 달성", val: 7, color: C.pos },
    { label: "△ 부분 달성", val: 2, color: C.warn },
    { label: "✕ 미달성", val: 0, color: C.neg },
    { label: "N/A 삭제", val: 1, color: C.textDim },
  ];
  counts.forEach((c, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 6.4, w: 3.0, h: 0.7, fill: { color: c.color }, line: { type: "none" } });
    s.addText(`${c.val}`, { x, y: 6.4, w: 0.8, h: 0.7, fontSize: 28, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_H });
    s.addText(c.label, { x: x + 0.8, y: 6.4, w: 2.2, h: 0.7, fontSize: 12, color: "FFFFFF", valign: "middle", fontFace: FONT_B });
  });

  addFooter(s, 2, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 3 — A-01
// ───────────────────────────────────────────────
aiSlide("A-01", "SSTR site-directed docking + 5종 정렬",
  "SSTR2(7XNA) 결합 포켓 중심 좌표 추출 + SSTR1/3/4/5 → SSTR2 구조 정렬. selectivity_runner.py에 binding pocket 정보 전달 인터페이스 추가.\n\n핵심 잔기: TM5(205,208,209,212) + TM6(272,273,276,279).\n선행: A-10 SSTR3 도킹 fix 필요.",
  "• binding_pocket_SSTR2.json 생성\n• 4 SSTR aligned.pdb 생성 (RMSD ≤ 4Å)\n• selectivity_runner 인터페이스 확장\n• step05b_selectivity 테스트 추가",
  "PR #61 머지 (5/19)\n• Center: (-5.595, -28.626, 52.210)\n• Radius: 13.0Å / Box: 26.1Å\n• 5종 정렬 (PyMOL cealign):\n  - SSTR1 RMSD 3.125Å\n  - SSTR3 RMSD 3.086Å\n  - SSTR4 RMSD 3.019Å\n  - SSTR5 RMSD 2.770Å\n• 모두 ≤4.0Å 충족",
  "• extract_binding_pocket.py\n• align_subtypes.py\n• selectivity_runner.py (get_pocket_center, get_gnina_config)\n• 38/38 tests pass\n• PR #61",
  "TM-align 미설치로 PyMOL cealign 대체 (결과 동등)",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 3, TOTAL);

// ───────────────────────────────────────────────
// Slide 4 — A-02
// ───────────────────────────────────────────────
aiSlide("A-02", "혈청 반감기 예측 도구 5종+ 비교",
  "SST14, Octreotide, Lanreotide, RC-160 벤치마크에 5종 이상 반감기 예측 도구 적용 + 정확도(R², MAE) 비교 보고서. D-AA 지원 여부 명시.",
  "• 5종+ 도구 검토\n• 벤치마크 정확도 표\n• R²/MAE 정량 비교\n• 권고 (도입 우선순위)",
  "researcher + follow-up 2건 완료\n• 7종 도구 비교 (ProtParam, HLP, PlifePred, PlifePred2, pepADMET, Tan2024 TL, PepMSND, Cavaco 2021)\n• pepADMET R²=0.84-0.90 가장 우수\n• 즉시+로컬+R²≥0.5 도구 0개\n• pepADMET D-AA 실 테스트 (Octreotide):\n  D-AA 절대값 4.83× 과대",
  "• sod-2026-05-19-A02-halflife-tools-comparison.md (28KB)\n• sod-2026-05-19-A02-followup-pepadmet-daa-test.md\n• ENDPOINT_CONFIDENCE 4건 등록 권고",
  "D-AA half-life 도구 0개 — HIGH-BLOCKER, 자체 모델 필요 (3-6개월)",
  "△ 부분 달성");
addFooter(pres.slides[pres.slides.length - 1], 4, TOTAL);

// ───────────────────────────────────────────────
// Slide 5 — A-03
// ───────────────────────────────────────────────
aiSlide("A-03", "Fab-ADMET 정확도 검증",
  "Fab-ADMET 도구 원 논문 정확도 정리 + SSTR2 환형 펩타이드(D-AA, 비천연 AA) 적용 시 한계 + 자체 학습 가능성 평가.",
  "• 원 논문 endpoint별 ROC AUC, MAE\n• SSTR2 환형 적용 한계\n• 자체 fine-tuning 가능성\n• 신뢰 가능 endpoint 식별",
  "researcher 완료 + V-01 사용자 확인\n• \"Fab-ADMET\" 학술 DB 미확인\n• 후보 분석: FP-ADMET vs pepADMET\n• 사용자 V-01 확인: pepADMET 오기재 확정\n• pepADMET 29 endpoint 분석\n• D-AA/DOTA 지원 도구 모두 0개\n• 자체 fine-tuning: ToxTeller (CC-BY) 가능",
  "• sod-2026-05-19-A03-fab-admet-validation.md\n• V-01 RESOLVED (pepADMET 확정)\n• 신뢰 endpoint 매트릭스 (수단별)",
  "회의록 오기재 — 명확화 완료. SSTR2 D-AA 후보에 신뢰 ADMET 도구 없음 (wet-lab 필수)",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 5, TOTAL);

// ───────────────────────────────────────────────
// Slide 6 — A-04
// ───────────────────────────────────────────────
aiSlide("A-04", "복합 스코어링 + Tier 분류",
  "ΔG 단일 지표 한계 극복. 13-metric panel + 7단계 다단계 선별 체계 기반 복합 스코어링. ADMET/반감기/radiolysis/selectivity 통합 평가.",
  "• composite_scorer.py 신규\n• WSS + Pareto front\n• Tier S/A/B/C 분류\n• A-09 입력 (tier_s_candidates.csv)\n• pharmacology_guards 통합",
  "PR #62 머지 — 6 신규 파일\n• composite_scorer.py (WSS + Pareto)\n• radiolysis_scorer.py (¹⁷⁷Lu)\n• CLI 진입점\n• 73/73 tests pass\n• Hard Cutoff 5게이트:\n  G1 ΔG ≤ -95 / G2 sel ≥ 100× /\n  G3 radiolysis ≤ 3 / G4 tox ≤ 0.3 / G5 II < 40\n• Smoke: 11 후보 → S=1/B=5/FAIL=5",
  "• pipeline_local/scoring/{composite,radiolysis}_scorer.py\n• pipeline_local/scripts/composite_scorer.py + _cli.py\n• 34 신규 tests + 39 회귀\n• PR #62",
  "P1 sprint wrapper (predict_halflife/admet) 통합은 Task #52 (이월)",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 6, TOTAL);

// ───────────────────────────────────────────────
// Slide 7 — A-05
// ───────────────────────────────────────────────
aiSlide("A-05", "SST14 reference dG (n≥10)",
  "SST14 원형(AGCKNFFWKTFTSC)을 SSTR2(7XNA)에 n≥10회 도킹 → 평균/표준편차 dG 산출 + reference 값 저장. 변이 후보 평가 기준선 제공.",
  "• n ≥ 10 도킹 실행\n• mean, std, 95% CI 통계\n• KPI: σ < 5\n• reference JSON 저장\n• pharmacology_guards 등록",
  "engineer-backend 직접 main push (8e7e1cc)\n• n = 10 FlexPepDock + InterfaceAnalyzer\n• mean ΔG = 553.857 REU\n• σ = 4.024 (KPI σ<5 충족 ✓)\n• 95% CI [550.978, 556.735]\n• min/max 550.565 / 564.492\n• 59/59 tests pass",
  "• data/somatostatin_receptor/SST14_SSTR2_reference_dG.json\n• pharmacology_guards.SST14_SSTR2_ref_ddg_flexpep\n• run_sst14_reference_docking.py\n• 커밋 8e7e1cc",
  "complex 부재로 양수 ΔG (553.857) — 절대값 신뢰 불가, 상대 비교만 유효",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 7, TOTAL);

// ───────────────────────────────────────────────
// Slide 8 — A-06
// ───────────────────────────────────────────────
aiSlide("A-06", "Diffusion 도킹 PoC",
  "DiffDock(또는 유사 디퓨전 모델)을 SSTR2-SST14 complex에 적용. PyRosetta/Boltz와 비교. 정밀도/속도/신뢰도 평가 후 도입 가치 보고.",
  "• Diffusion 모델 SSTR2-SST14 적용\n• PyRosetta/Boltz 비교\n• 시간/정확도/SS bond 지원\n• 도입 권고 (운영/PoC/미도입)",
  "engineer-backend 직접 main push (6054ea9)\n• DiffPepBuilder v1 모델 사용 (1.2GB)\n• 10 포즈 생성 77.9초\n• inter-pose Cα RMSD 0.36-2.26Å\n• 3 engine 비교:\n  FlexPepDock 6-13초 (Rosetta ddG)\n  Boltz 60-90초 (iPTM)\n  DiffPepDock 77.9초 (점수 없음)",
  "• pipeline_local/scripts/run_diffpepdock_inference.py\n• run_diffpepdock_poc.py\n• runs_local/diffdock_poc/poc_report.{json,md}\n• 12/12 tests pass\n• 커밋 6054ea9",
  "openmm GLIBCXX_3.4.30 비호환 → postprocess 비활성화 (engineer-infra 후속)",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 8, TOTAL);

// ───────────────────────────────────────────────
// Slide 9 — A-07
// ───────────────────────────────────────────────
aiSlide("A-07", "GPU 인프라 견적 수집",
  "H100 NVL ×4 또는 추가 GPU 견적 비교 자료 정리. 실 구매·결재는 사용자(서호성/안기범) 책임. 견적 자동화 + 시스템 점검만 수행.",
  "• 벤더별 견적 표 (NVIDIA, SuperMicro, Dell)\n• 단가, 리드타임, NVLink 여부\n• 현 워크로드 적합 옵션\n• 시스템 점검 결과",
  "engineer-infra 완료\n• 점검: H100 NVL ×4\n  GPU 0/1: 87GB 점유 (컨테이너)\n  GPU 2/3: 14MiB 유휴\n• NVLink 없음 (SYS topology)\n  → 120GB+ 모델 단일 GPU 불가\n• 즉시 가능: CUDA_VISIBLE_DEVICES=2,3 (192GB)\n• 견적 템플릿: DGX H100 ~4.8-5.5억\n  자체 빌드 H100 SXM ×8 ~2.0-2.7억",
  "• sod-2026-05-19-A07-gpu-infra-quote.md (13KB)\n• 견적 체크리스트\n• 시스템 점검 보고서",
  "벤더 실 견적 수집은 사용자 책임 (~/.zshrc 192GB는 사용자가 이미 설정)",
  "△ 부분 달성");
addFooter(pres.slides[pres.slides.length - 1], 9, TOTAL);

// ───────────────────────────────────────────────
// Slide 10 — A-08 (삭제)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-08 — 회의 당일 삭제됨", "정상 종료 (실수 누락 아님)");

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 12.3, h: 4.0, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("원본 항목 (PDF §3 Action Items, p.5)", { x: 0.8, y: 1.7, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.primary, fontFace: FONT_H });
  s.addText("\"라이브러리 서버 마이그레이션 완료 및 검증\" (담당: AI팀)", { x: 0.8, y: 2.2, w: 12.0, h: 0.5, fontSize: 18, italic: true, color: C.dark, fontFace: FONT_H });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.9, w: 11.7, h: 0.05, fill: { color: C.neg }, line: { type: "none" } });

  s.addText("삭제 사유 (PDF §2.3, p.4 + §4 수행 가이드, p.9)", { x: 0.8, y: 3.1, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: C.primary, fontFace: FONT_H });
  s.addText("외부망 서버(H100 ×8장)에 전체 시스템 배포 완료로 본 항목은 삭제 처리한다.", { x: 0.8, y: 3.6, w: 12.0, h: 0.5, fontSize: 14, color: C.text, fontFace: FONT_B });

  s.addText("§3 표 비고: \"완료/불요\" — 취소선(strikethrough) 처리됨", { x: 0.8, y: 4.2, w: 12.0, h: 0.4, fontSize: 12, italic: true, color: C.textMute, fontFace: FONT_B });

  // 결과
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.7, w: 12.3, h: 1.2, fill: { color: C.pos }, line: { type: "none" } });
  s.addText("정상 종료 — prompts/A-08_prompt.md 부재가 정상 상태", { x: 0.7, y: 5.7, w: 12.0, h: 1.2, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: FONT_H });

  addFooter(s, 10, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 11 — A-09
// ───────────────────────────────────────────────
aiSlide("A-09", "최종 후보 3-4개 + 합성 의뢰서",
  "A-04 composite_scorer 결과 기반 최종 후보 3-4개 선정 + 합성 의뢰서 작성. Gate-2 진입 준비 완료. h0/h1 가설 + 검증 protocol + acceptance criteria + timeline 포함.",
  "• 후보 3-4개 선정 (Tier S 우선)\n• 다양성 확보 (hamming 분포)\n• 합성 의뢰서 각 후보별 1건\n• wetlab BE 통합 검증",
  "PR #63 머지 — reviewer-pharma 검증\n• 4 후보 선정:\n  PRST-001 (Tier S, WSS=1.000)\n    AGCKNIIWKTITSC, ΔG -105.5, rad=1\n  PRST-002 (Tier B, WSS=0.582)\n  PRST-003 (Tier B, K4→R, N-말단 DOTA 전용)\n  PRST-004 (Tier B, WSS=0.365)\n• Hard Cutoff 5게이트 4/4 PASS\n• H-06 HEURISTIC 가드 적용\n• pepADMET D-AA HIGH-BLOCKER 반영",
  "• runs_local/final_candidates/synthesis_orders/PRST-{001,002,003,004}.md\n• sod-2026-05-19-A09-final-candidates-synthesis.md\n• PR #63",
  "다양성 86% (목표 80% 미달 — 14aa 구조 제약, A-09 정책상 WARN 후 진행)",
  "✓ 달성");
addFooter(pres.slides[pres.slides.length - 1], 11, TOTAL);

// ───────────────────────────────────────────────
// Slide 12 — A-10 + 다음 단계
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "A-10 + Gate-2 진입 로드맵", "SSTR3 fix → 5종 정렬 활성화 + 다음 단계");

  // A-10
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 6.0, h: 3.0, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 0.1, h: 3.0, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("A-10 SSTR3_8XIR 도킹 fix", { x: 0.8, y: 1.6, w: 5.6, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });
  s.addText("원본 요구: SSTR3 PDB 전처리 + 도킹 정상화", { x: 0.8, y: 2.0, w: 5.6, h: 0.3, fontSize: 10, color: C.textMute, fontFace: FONT_B });

  s.addText("실행 결과 (PR #60)", { x: 0.8, y: 2.4, w: 5.6, h: 0.3, fontSize: 11, bold: true, color: C.primary, fontFace: FONT_B });
  s.addText("• chain B 선택 패치\n• 23+1 tests pass\n• boltz env smoke OK\n  ddg=-92.09, iptm=0.9209\n• A-01 SSTR3 정렬 활성화 가능", { x: 0.8, y: 2.7, w: 5.6, h: 1.5, fontSize: 11, color: C.text, fontFace: FONT_B });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.2, w: 6.0, h: 0.3, fill: { color: C.pos }, line: { type: "none" } });
  s.addText("✓ 달성", { x: 0.8, y: 4.2, w: 5.6, h: 0.3, fontSize: 11, bold: true, color: "FFFFFF", valign: "middle", fontFace: FONT_B });

  // 다음 단계 (3 단계)
  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 1.5, w: 6.0, h: 3.0, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("Gate-2 로드맵 (RI팀)", { x: 7.0, y: 1.6, w: 5.6, h: 0.4, fontSize: 14, bold: true, color: C.secondary, fontFace: FONT_H });

  const roadmap = [
    "1. PRST-001~004 합성 (Peptron, 4-6주)",
    "2. SSTR1-5 binding Ki (n=3×3 biological)",
    "3. pepADMET 예측 × 실측 상관 분석",
    "4. V-A09-01/03/05/06 모두 해결",
    "5. Gate-3 진입 (¹⁷⁷Lu 라벨링 + in vivo PK)",
  ];
  roadmap.forEach((step, i) => {
    const y = 2.1 + i * 0.45;
    s.addText(step, { x: 7.0, y, w: 5.6, h: 0.4, fontSize: 11, color: "FFFFFF", fontFace: FONT_B });
  });

  // V-검증 잔여
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.8, w: 12.3, h: 2.0, fill: { color: C.warn }, line: { type: "none" } });
  s.addText("미진 — wet-lab Gate-2 의존 (자동화 불가)", { x: 0.7, y: 4.9, w: 12.0, h: 0.4, fontSize: 14, bold: true, color: "FFFFFF", fontFace: FONT_H });

  const pending = [
    "V-A09-01: PRST-001 F6→I 치환 시 SSTR2 Ki 변화",
    "V-A09-03: pepADMET selectivity margin × 실측 Ki",
    "V-A09-05: predict_half_life() ranking wet-lab 검증",
    "V-A09-06: Boltz2 ΔG -105.5 × 실험 IC50/Ki 상관",
  ];
  pending.forEach((p, i) => {
    const x = 0.7 + (i % 2) * 6.0;
    const y = 5.4 + Math.floor(i / 2) * 0.55;
    s.addShape(pres.shapes.OVAL, { x, y: y + 0.05, w: 0.2, h: 0.2, fill: { color: "FFFFFF" }, line: { type: "none" } });
    s.addText(p, { x: x + 0.3, y, w: 5.5, h: 0.4, fontSize: 11, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
  });
  s.addText("→ 4건 모두 wet-lab Ki/IC50 측정 후 자동 해결", {
    x: 0.7, y: 6.45, w: 12.0, h: 0.3, fontSize: 11, italic: true, color: C.light, fontFace: FONT_B,
  });

  addFooter(s, 12, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 13 — Ensemble 갱신 (PR #85) 브리지
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "3-Layer Ensemble + 후속 PR — 브리지", "PR #85·#108·#109·#111·#112·#113 (문서·코드 근거만)");
  s.addText("슬라이드 14–18: 재검증 Markdown·EOD 수치만 (할루시네이션 금지). 슬라이드 19–20: D-6 매트릭스·6월 로드맵 보강.", {
    x: 0.5, y: 1.45, w: 12.3, h: 0.4, fontSize: 11, color: C.textMute, fontFace: FONT_B, italic: true,
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.95, w: 12.3, h: 4.95, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  const b13 = [
    "PRST pepADMET: 의뢰서 0.10~0.25 vs pepADMET 재측 binary_toxicity=1.00 — 양측 수치 모순 보존 (§매트릭스 2026-05-21)",
    "PR #113 (merge f72c48e): 재훈련 + OOD(Mahalanobis·MC Dropout) — sanity Octreotide 0.132, SST-14 0.402, PRST 간 max-min 0.217 간신히, PRST 4건 예측 동일값 (ranking만, in vitro 필수)",
    "PR #111: PRST 종합 매트릭스 + `_workspace/admet_ai_local/charts/` ADMET-AI 시각화 (raw JSON 근거)",
    "Layer 2 PR #112: Spearman ρ=0.571, R²=0.022 (순위 신호 보강) — 여전히 Hard Cutoff 직결 금지 (슬라이드 17 부록)",
    "PR #108: composite_scorer fallback WARN + cyclic SS-bond OOD 가드 · PR #109: silent (0.0) fallback 제거(부분) — selectivity K-1/K-2(Task #14) 본체는 잔존",
    "운영: 단독 Gate 금지 · 다중 도구 견제 + wet-lab (MEETING_PREP §4 Q1~Q8과 정합)",
  ];
  b13.forEach((t, i) => {
    s.addText(`• ${t}`, { x: 0.72, y: 2.02 + i * 0.72, w: 11.9, h: 0.68, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" });
  });
  addFooter(s, 13, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 14 — PRST pepADMET 재검증 (CRITICAL)
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "PRST-001~004 pepADMET 재검증 + PR #113 OOD·재훈련", "_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md · EOD action-items-closure 2026-05-21");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.42, w: 12.3, h: 0.42, fill: { color: C.neg }, line: { type: "none" } });
  s.addText(
    "합성 의뢰서 ADMET 수치는 pepADMET 실측이 아닐 수 있음: CSV 0.10/0.12/0.20/0.25 + enrichment \"admet wrapper returned no toxicity score\" → composite 입력/fallback 전파 가능성",
    { x: 0.65, y: 1.45, w: 12.0, h: 0.38, fontSize: 10, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" }
  );

  const t14 = [
    [{ text: "후보", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "의뢰서값", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "binary_toxicity", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "toxicity / neuro", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["PRST-001", "0.10", { text: "1.00", options: { bold: true, color: C.neg } }, "hemostasis / Na_inhibitor"],
    ["PRST-002", "0.12", { text: "1.00", options: { bold: true, color: C.neg } }, "hemostasis / Na_inhibitor"],
    ["PRST-003", "0.20", { text: "1.00", options: { bold: true, color: C.neg } }, "hemostasis / Na_inhibitor"],
    ["PRST-004", "0.25", { text: "1.00", options: { bold: true, color: C.neg } }, "hemostasis / Na_inhibitor"],
  ];
  s.addTable(t14, {
    x: 0.5, y: 1.95, w: 12.3,
    colW: [1.2, 1.3, 2.2, 7.6],
    fontSize: 10, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.32,
    valign: "middle",
  });

  s.addText("막대: 동일 스케일(0–1) 비교 · pepADMET 재추론(4건 available: true). 상단 표는 문서 기록값 그대로.", { x: 0.5, y: 3.52, w: 12.3, h: 0.28, fontSize: 10, color: C.textMute, fontFace: FONT_B });
  s.addChart(
    pres.ChartType.bar,
    [
      { name: "의뢰서 admet (전파값)", labels: ["PRST-001", "PRST-002", "PRST-003", "PRST-004"], values: [0.1, 0.12, 0.2, 0.25] },
      { name: "pepADMET binary_toxicity", labels: ["PRST-001", "PRST-002", "PRST-003", "PRST-004"], values: [1.0, 1.0, 1.0, 1.0] },
    ],
    { x: 0.45, y: 3.78, w: 12.4, h: 1.88, barDir: "col", barGrouping: "clustered", chartColors: [C.secondary, C.neg], valAxisMaxVal: 1, showLegend: true, legendPos: "b" }
  );

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.72, w: 12.3, h: 0.52, fill: { color: C.accent }, line: { type: "none" } });
  s.addText(
    "PR #113 (머지 f72c48e): 재훈련 GNN + `pipeline_local/pepadmet_ood/ood_detection.py`(Mahalanobis·MC Dropout). Sanity(EOD 기록): Octreotide≈0.132, SST-14≈0.402; PRST-001~004 예측 동일≈0.402, 후보 간 max-min≈0.217(간신히). 외삽·OOD 한계 여전 — ranking·경고 신호만, 단독 합성 근거 금지·in vitro 교차검증 필수(PR disclaimer와 동일).",
    { x: 0.62, y: 5.74, w: 12.0, h: 0.48, fontSize: 8.8, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" }
  );

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.32, w: 12.3, h: 0.68, fill: { color: C.warn }, line: { type: "none" } });
  s.addText(
    "결론: 의뢰서 저독성 수치와 pepADMET 1.00을 함께 보존(매트릭스 문서화). CSV hard_cutoff_pass=True 와 재측값은 상충 가능. PR #113으로 동일 신호(1.00) 과신은 완화되나 PRST 간 분해능 약함·절대 독성 단정 불가.",
    { x: 0.65, y: 6.34, w: 12.0, h: 0.64, fontSize: 10, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" }
  );

  addFooter(s, 14, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 15 — 3-Layer Ensemble 개요
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "3-Layer Ensemble Framework", "라우터 자동 분기 — 코드: pipeline_local/scoring/ensemble_router.py");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.45, w: 4.0, h: 5.45, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.45, w: 0.08, h: 5.45, fill: { color: C.secondary }, line: { type: "none" } });
  s.addText("Layer 1", { x: 0.65, y: 1.52, w: 3.7, h: 0.35, fontSize: 14, bold: true, color: C.secondary, fontFace: FONT_H });
  s.addText("L-aa / 선형 우선\n• PlifePred(확률)\n• HLE (wrapper 경로)\n• pepADMET blood / half-life 계열", { x: 0.65, y: 1.95, w: 3.7, h: 2.3, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" });
  s.addText("비고: Hour ensemble는 도구별 가용성에 따라 가중 — 문서 2026-05-20", { x: 0.65, y: 4.35, w: 3.7, h: 1.0, fontSize: 9.5, color: C.textMute, fontFace: FONT_B, valign: "top", italic: true });

  s.addShape(pres.shapes.RECTANGLE, { x: 4.65, y: 1.45, w: 4.0, h: 5.45, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 4.65, y: 1.45, w: 0.08, h: 5.45, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("Layer 2", { x: 4.8, y: 1.52, w: 3.7, h: 0.35, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });
  s.addText("D-AA / Cyclic\n• 로컬 PEPlife2 → GAT 회귀\n• conda 격리 subprocess\n• 등급 P4 (test R²<0)", { x: 4.8, y: 1.95, w: 3.7, h: 2.0, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" });

  s.addShape(pres.shapes.RECTANGLE, { x: 8.8, y: 1.45, w: 4.0, h: 5.45, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 8.8, y: 1.45, w: 0.08, h: 5.45, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("Layer 3", { x: 8.95, y: 1.52, w: 3.75, h: 0.35, fontSize: 14, bold: true, color: C.primary, fontFace: FONT_H });
  s.addText("DOTA conjugate / 소분자형 입력\n• ADMET-AI (사전학습)\n• CPU 추론·104 endpoint\n• 외삽 가드 H-06", { x: 8.95, y: 1.95, w: 3.75, h: 2.1, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.25, w: 12.3, h: 0.85, fill: { color: C.dark }, line: { type: "none" } });
  s.addText(
    "라우터(텍스트 트리): 입력(서열·수식어) → (DOTA?) L3 : (D-AA/환형?) L2 : L1 → ensemble_halflife / ADMET 보조 출력 (가드 플래그와 함께)",
    { x: 0.65, y: 6.3, w: 12.0, h: 0.75, fontSize: 11, color: "FFFFFF", fontFace: FONT_B, valign: "middle" }
  );
  addFooter(s, 15, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 16 — Layer 1 정직한 보고
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Layer 1 — 정직한 보고", "_workspace/plifepred_hour_conversion_2026-05-20.md");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("PlifePred2 / Halflife 열", { x: 0.65, y: 1.58, w: 5.7, h: 0.4, fontSize: 14, bold: true, color: C.secondary, fontFace: FONT_H });
  s.addText(
    "• PyPI·설치 소스: CSV \"Halflife\" = Predicted probability (시간 아님)\n• 일반 입력: predict_proba → rank-only; predicted_hours는 기본 None\n• SST-14 단 한 점: calibration_table → 3 min 벤치 = 0.05 h (NCBI Bookshelf/StatPearls 1–3 min 인용 범위)",
    { x: 0.65, y: 2.05, w: 5.7, h: 3.3, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" }
  );
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.45, w: 6.0, h: 0.45, fill: { color: C.textDim }, line: { type: "none" } });
  s.addText("Score→시간 임의 스케일링 없음 (정직)", { x: 0.65, y: 5.48, w: 5.7, h: 0.4, fontSize: 10, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });

  s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 1.5, w: 6.0, h: 5.3, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText("HLE · pepADMET blood / half-life", { x: 6.95, y: 1.58, w: 5.7, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });
  s.addText(
    "• HLE 및 pepADMET blood/half-life 모듈: 본 문서 시점에서 \"시간(h) 합의 출력\" unavailable 또는 제약 (Four-Benchmark / wrapper 경로)\n• Octreotide/Lanreotide/RC-160: 비표준 잔기·환형 → 시간 환산 보고 불가\n• pepADMET D-AA·도메인 이슈는 A-02 follow-up에 이미 문서화",
    { x: 6.95, y: 2.05, w: 5.7, h: 3.5, fontSize: 11.5, color: C.text, fontFace: FONT_B, valign: "top" }
  );
  addFooter(s, 16, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 17 — Layer 2 P4 한계
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Layer 2 — PEPlife2 / pepMSND · P4 + PR #112 부록", "_workspace/pepmsnd_local/training_2026-05-20.md · eod-2026-05-21-orchestrator-3layer-and-followup.md");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 12.3, h: 5.15, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  const lines = [
    "데이터: PEPlife2 병합 id 기준 4500건; API chiral 필드 D=25건 — 문서 \"213건\"과 불일치 → 정의/버전 검증 필요",
    "공식 PepMSND Models/model.py: BCE·3D PDB 필수 → 본 세션 데이터와 비호환 → PyG GAT 백본만 차용한 log1p 회귀",
    "초기 hold-out (문서 2026-05-20 / PR #85 시점): R² = -0.0283, Spearman ρ = -0.1191 — 예측력 없음에 가깝다",
    "부록 — PR #112 재학습(EOD 2026-05-21): Spearman ρ = 0.571, R² = 0.022 — 순위(ranking) 신호 큰 개선; 반감기 절대값 회귀는 여전히 Hard Cutoff·Gate 직결 금지",
    "DGL/libnvrtc: GraphBolt 로드 실패 사례 → PyG SMILES 경로 사용; env 정비·재학습은 6월 로드맵",
    "PRST-001~004 추론 ~1.83 h + ENDPOINT_CONFIDENCE grade P4(이전 문서) — 운영: 보조 지표 전용",
  ];
  lines.forEach((t, i) => {
    s.addText(`• ${t}`, { x: 0.68, y: 1.58 + i * 0.72, w: 12.0, h: 0.68, fontSize: 10.8, color: C.text, fontFace: FONT_B, valign: "top" });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.28, w: 12.3, h: 0.52, fill: { color: C.neg }, line: { type: "none" } });
  s.addText("운영: 보조 지표 전용 · pharmacology_guards ENDPOINT_CONFIDENCE P4 (Hard Cutoff 반영 금지). PR #112는 부록 수치 인용.", {
    x: 0.65, y: 6.3, w: 12.0, h: 0.48, fontSize: 11, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle",
  });
  addFooter(s, 17, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 18 — Layer 3 + PR #111 차트
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "Layer 3 — ADMET-AI · PR #111 차트", "installation_test_2026-05-20.md · PRST_comprehensive_matrix_2026-05-21.md · charts/README.md");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.45, w: 12.3, h: 1.22, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addText(
    "• PRST-001~004 + Octreotide — CPU 추론 ok=True, endpoints=104 (표) · 104×5=520 스칼라 (문서 산술)\n"
      + "• 매 compound extrapolation_warning=True, recommended_for_decision=False (H-06)\n"
      + "• 우측: matplotlib `admet_ai_tier_scatter_…png` — tier 라벨은 tier_*_candidates.csv (PR #111)",
    { x: 0.62, y: 1.5, w: 12.05, h: 1.1, fontSize: 10, color: C.text, fontFace: FONT_B, valign: "top" }
  );

  const t18 = [
    [{ text: "compound", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "ok", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "endpoints", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "predict_sec", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["PRST-001", "True", "104", "0.301"],
    ["PRST-002", "True", "104", "0.239"],
    ["PRST-003", "True", "104", "0.278"],
    ["PRST-004", "True", "104", "0.285"],
    ["Octreotide", "True", "104", "0.201"],
  ];
  s.addTable(t18, {
    x: 0.5, y: 2.78, w: 7.25,
    colW: [2.0, 1.05, 1.25, 2.95],
    fontSize: 9.5, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.32,
    valign: "middle",
  });

  s.addImage({ path: IMG_ADMET_SCATTER, x: 8.0, y: 2.72, w: 4.95, h: 2.78 });

  s.addText("GPU used: False · init ~0.14 s (설치 테스트 문서).", { x: 0.5, y: 5.48, w: 7.25, h: 0.3, fontSize: 9, color: C.textMute, fontFace: FONT_B });
  s.addText("H-06: ADMET-AI LOW-confidence extrapolation — raw ≠ measurement (차트·README)", { x: 8.0, y: 5.52, w: 4.95, h: 0.36, fontSize: 8.5, color: C.textMute, fontFace: FONT_B, italic: true, valign: "top" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.9, w: 12.3, h: 1.1, fill: { color: C.primary }, line: { type: "none" } });
  s.addText(
    "3-Layer + PR #111 시각화로 Layer3를 한눈에. 단독 결정 금지 — 다중 도구 견제 + wet-lab (MEETING_PREP §4 Q1·Q7).",
    { x: 0.65, y: 5.96, w: 12.0, h: 0.98, fontSize: 13, bold: true, color: "FFFFFF", fontFace: FONT_H, align: "center", valign: "middle" }
  );

  addFooter(s, 18, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 19 — 핵심 결함 + 처리 매트릭스
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "핵심 결함 — 처리 매트릭스", "PRST_comprehensive_matrix_2026-05-21 · EOD action-items-closure · eod-2026-05-21-master-integrated");
  s.addText("의뢰서 ADMET=0.10~0.25(전파/fallback 가능)과 pepADMET 재측 1.00을 동시에 보존 — 어느 한쪽으로 덮어쓰지 않음.", {
    x: 0.5, y: 1.42, w: 12.3, h: 0.38, fontSize: 10.5, color: C.textMute, fontFace: FONT_B, italic: true,
  });
  const rows19 = [
    [{ text: "항목", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "실측·문서 근거", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } },
      { text: "처리", options: { bold: true, fill: { color: C.dark }, color: "FFFFFF" } }],
    ["ADMET 수치 이중성", "의뢰서 전파 0.10~0.25 vs pepADMET binary_toxicity 1.00 (재검증 MD)", "PR #108 WARN + PR #113 재훈련·OOD"],
    ["Hard Cutoff 상충", "CSV hard_cutoff_pass=True vs 재측 1.00 — 매트릭스 §Hard Cutoff 모순", "회의에서 게이트 정의 분리·해석 공유 (Q7)"],
    ["pepADMET OOD", "학습 도메인 밖·PRST 구별력 약함 (EOD sanity max-min 0.217)", "ranking·경고만, in vitro 필수 (PR #113 disclaimer)"],
    ["K-1 / K-2 selectivity", "run 디렉터리 정렬·candidate_pdb 미사용 (EOD §4)", "Task #14; PR #109 silent 0.0 제거 = 부분 fix, 본체 잔존"],
  ];
  s.addTable(rows19, {
    x: 0.5, y: 1.88, w: 12.3,
    colW: [1.85, 5.35, 5.1],
    fontSize: 9.5, fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH: 0.58,
    valign: "middle",
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.22, w: 12.3, h: 0.82, fill: { color: C.dark }, line: { type: "none" } });
  s.addText(
    "정직성: 외삽·OOD 한계를 발표에서 먼저 밝힘. 수치는 문서·JSON·EOD에 있는 것만 인용.",
    { x: 0.65, y: 6.28, w: 12.0, h: 0.72, fontSize: 12, bold: true, color: C.secondary, fontFace: FONT_H, align: "center", valign: "middle" }
  );
  addFooter(s, 19, TOTAL);
}

// ───────────────────────────────────────────────
// Slide 20 — 6월 회의 로드맵
// ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  addTitle(s, "6월 회의 로드맵 (제안)", "MEETING_PREP §4 Q8 · 인프라·RI 결정 필요 항목");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.5, w: 12.3, h: 5.15, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  const items = [
    "1. DGL libnvrtc 환경 정비 + Layer 2(PEPlife2 / pepMSND) 재학습 — Q6·Q8과 정합",
    "2. HBM(High-quality bench) 데이터 — pepADMET 저자 문의 메일 발송 여부 결정 (A-03 초안: docs/meet_log/.../A-03_pepadmet_author_email_draft.md)",
    "3. PRST-001 (및 후보) wet-lab assay 범위·발주 결정 — Gate-2·Q7",
    "4. A-02 D-AA: 자체 모델 구축 승인 vs 실측 병행 — RI 의사결정 (도구 0개 블로커)",
  ];
  items.forEach((t, i) => {
    s.addText(t, { x: 0.72, y: 1.65 + i * 1.12, w: 11.9, h: 1.0, fontSize: 14, color: C.text, fontFace: FONT_B, valign: "top" });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.25, w: 12.3, h: 0.78, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("목표: 6월에는 “실측으로 보정되는 의사결정 루프” 중심 보고 (MEETING_PREP Q8).", {
    x: 0.65, y: 6.3, w: 12.0, h: 0.68, fontSize: 12, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle", align: "center",
  });
  addFooter(s, 20, TOTAL);
}

pres.writeFile({ fileName: "PRST_N_FM_ActionItems_Audit_2026-05-28_d6.pptx" })
  .then((f) => console.log(`Saved: ${f}`));
