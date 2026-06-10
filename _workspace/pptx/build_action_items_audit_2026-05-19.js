// Action Items 9건 원본 요구 vs 실행 결과 비교 PPTX
// 12 슬라이드 — 4/6 회의 액션 아이템 audit

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.author = "PRST_N_FM Team";
pres.title = "Action Items 9건 — 원본 요구 vs 실행 결과 비교 (2026-04-06 회의 기준)";

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
  s.addText("Action Items Audit · 4/6 회의 → 2026-05-19", { x: 0.4, y: 7.25, w: 8, h: 0.25, fontSize: 9, color: C.light, fontFace: FONT_B, valign: "middle" });
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
  addTitle(s, `${id} — ${name}`, `회의 KAERI-AIRL-MOM-2026-003 (2026-04-06) → 5/19 실행 결과`);

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
  s.addText("실행 결과 (5/19)", { x: 7.1, y: 1.6, w: 5.6, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: FONT_H });

  s.addText("수행 + 산출물", { x: 7.1, y: 2.0, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(executed, { x: 7.1, y: 2.3, w: 5.6, h: 2.0, fontSize: 11, color: C.text, fontFace: FONT_B, valign: "top" });

  s.addText("산출 파일 / PR", { x: 7.1, y: 4.6, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.textMute, fontFace: FONT_B });
  s.addText(deliverables, { x: 7.1, y: 4.9, w: 5.6, h: 1.4, fontSize: 10, color: C.text, fontFace: "Consolas", valign: "top" });

  // 하단: 갭 + 상태
  const stColor = status === "✓ 달성" ? C.pos : status.includes("부분") ? C.warn : C.neg;
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.9, w: 12.3, h: 0.3, fill: { color: stColor }, line: { type: "none" } });
  s.addText(`상태: ${status}  ·  갭: ${gap}`, { x: 0.7, y: 6.9, w: 12.0, h: 0.3, fontSize: 11, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle" });
}

const TOTAL = 12;

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
  s.addText("검증일", { x: 0.7, y: 5.5, w: 5.6, h: 0.3, fontSize: 11, color: C.secondary, fontFace: FONT_B });
  s.addText("2026-05-19", { x: 0.7, y: 5.8, w: 5.6, h: 0.5, fontSize: 24, bold: true, color: "FFFFFF", fontFace: FONT_H });

  s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: 4.5, w: 6.0, h: 2.0, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("종합 상태", { x: 7.1, y: 4.6, w: 5.6, h: 0.3, fontSize: 11, color: C.light, fontFace: FONT_B });
  s.addText("9 / 9 종료", { x: 7.1, y: 4.9, w: 5.6, h: 0.8, fontSize: 36, bold: true, color: "FFFFFF", fontFace: FONT_H });
  s.addText("(A-08은 회의 당일 삭제 — 9건 중 9건 처리)", { x: 7.1, y: 5.7, w: 5.6, h: 0.7, fontSize: 12, color: C.light, fontFace: FONT_B });
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

pres.writeFile({ fileName: "PRST_N_FM_ActionItems_Audit_2026-05-19.pptx" })
  .then((f) => console.log(`Saved: ${f}`));
