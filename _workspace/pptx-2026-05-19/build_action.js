const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "orchestrator-session";
pres.title = "2026-04-06 액션 아이템 9건 - 현재 시스템 진척도";

// Berry & Cream palette (도메인 — 임상 PRRT + radiopharma 의사결정)
const C = {
  primary: "6D2E46",   // berry (dark)
  rose: "A26769",      // dusty rose
  cream: "ECE2D0",     // cream
  parchment: "F8F4ED", // light bg
  white: "FFFFFF",
  ink: "1F2937",       // body text
  slate: "475569",
  muted: "9CA3AF",
  // status
  done: "16A34A",      // green ✓
  partial: "D97706",   // amber ⚠
  pending: "DC2626",   // red ✗
  info: "0891B2",
};

const FH = "Calibri";
const FB = "Calibri";

function addHeader(slide, title, subtitle, badge) {
  slide.background = { color: C.parchment };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 0.95, fill: { color: C.primary }, line: { color: C.primary }
  });
  slide.addText(title, {
    x: 0.5, y: 0.15, w: 10, h: 0.5,
    fontFace: FH, fontSize: 22, bold: true, color: C.white, margin: 0
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.6, w: 10, h: 0.3,
      fontFace: FB, fontSize: 11, color: C.cream, margin: 0
    });
  }
  if (badge) {
    // status badge (top-right)
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 11.0, y: 0.2, w: 2.0, h: 0.55,
      fill: { color: badge.color }, line: { color: badge.color }
    });
    slide.addText(badge.text, {
      x: 11.0, y: 0.2, w: 2.0, h: 0.55,
      fontFace: FH, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
    });
  }
  // accent strip
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.95, w: 13.3, h: 0.05, fill: { color: C.rose }, line: { color: C.rose }
  });
}

function pageNum(slide, n, total) {
  slide.addText(`${n} / ${total}`, {
    x: 12.5, y: 7.15, w: 0.6, h: 0.25,
    fontFace: FB, fontSize: 9, color: C.muted, align: "right", margin: 0
  });
}

const TOTAL = 14;

// Helper for 4-section action item slide
function addActionSlide(slide, opt) {
  // Layout: 2 columns
  // Left col: 제안 + 서호성 의견
  // Right col: 현재 + Gap + 개선

  const sectY = 1.15;
  const sectH = 5.9;
  const leftX = 0.5;
  const leftW = 6.2;
  const rightX = 6.85;
  const rightW = 6.0;

  // Left: 회의 제안
  slide.addShape(pres.shapes.RECTANGLE, {
    x: leftX, y: sectY, w: leftW, h: sectH,
    fill: { color: C.white }, line: { color: C.primary, width: 1 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: leftX, y: sectY, w: leftW, h: 0.4,
    fill: { color: C.primary }, line: { color: C.primary }
  });
  slide.addText("📋  회의 제안 (2026-04-06)", {
    x: leftX + 0.15, y: sectY, w: leftW - 0.3, h: 0.4,
    fontFace: FH, fontSize: 13, bold: true, color: C.white, valign: "middle", margin: 0
  });
  slide.addText(opt.proposal, {
    x: leftX + 0.2, y: sectY + 0.5, w: leftW - 0.4, h: 2.5,
    fontFace: FB, fontSize: 11, color: C.ink, margin: 0
  });

  // Left bottom: 서호성 박사 의견
  const seoY = sectY + 3.15;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: leftX + 0.2, y: seoY, w: leftW - 0.4, h: 2.55,
    fill: { color: C.cream }, line: { color: C.rose, width: 0 }
  });
  slide.addText("💬  서호성 박사 의견", {
    x: leftX + 0.35, y: seoY + 0.1, w: leftW - 0.6, h: 0.3,
    fontFace: FH, fontSize: 12, bold: true, color: C.primary, margin: 0
  });
  slide.addText(opt.seo, {
    x: leftX + 0.35, y: seoY + 0.45, w: leftW - 0.6, h: 2.0,
    fontFace: FB, fontSize: 10, italic: true, color: C.ink, margin: 0
  });

  // Right top: 현재 시스템
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: sectY, w: rightW, h: 2.55,
    fill: { color: C.white }, line: { color: opt.status.color, width: 1.5 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: sectY, w: rightW, h: 0.4,
    fill: { color: opt.status.color }, line: { color: opt.status.color }
  });
  slide.addText("🔧  현재 시스템 (2026-05-19)", {
    x: rightX + 0.15, y: sectY, w: rightW - 0.3, h: 0.4,
    fontFace: FH, fontSize: 13, bold: true, color: C.white, valign: "middle", margin: 0
  });
  slide.addText(opt.current, {
    x: rightX + 0.2, y: sectY + 0.5, w: rightW - 0.4, h: 2.0,
    fontFace: FB, fontSize: 11, color: C.ink, margin: 0
  });

  // Right middle: GAP
  const gapY = sectY + 2.7;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: gapY, w: rightW, h: 1.5,
    fill: { color: C.white }, line: { color: C.partial, width: 1 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: gapY, w: rightW, h: 0.35,
    fill: { color: C.partial }, line: { color: C.partial }
  });
  slide.addText("⚠  Gap (제안 vs 현재)", {
    x: rightX + 0.15, y: gapY, w: rightW - 0.3, h: 0.35,
    fontFace: FH, fontSize: 12, bold: true, color: C.white, valign: "middle", margin: 0
  });
  slide.addText(opt.gap, {
    x: rightX + 0.2, y: gapY + 0.43, w: rightW - 0.4, h: 1.05,
    fontFace: FB, fontSize: 10, color: C.ink, margin: 0
  });

  // Right bottom: 개선 방향
  const fixY = sectY + 4.4;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: fixY, w: rightW, h: 1.5,
    fill: { color: C.white }, line: { color: C.info, width: 1 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: fixY, w: rightW, h: 0.35,
    fill: { color: C.info }, line: { color: C.info }
  });
  slide.addText("🎯  개선 방향", {
    x: rightX + 0.15, y: fixY, w: rightW - 0.3, h: 0.35,
    fontFace: FH, fontSize: 12, bold: true, color: C.white, valign: "middle", margin: 0
  });
  slide.addText(opt.fix, {
    x: rightX + 0.2, y: fixY + 0.43, w: rightW - 0.4, h: 1.05,
    fontFace: FB, fontSize: 10, color: C.ink, margin: 0
  });
}

// ============================================================
// Slide 1 — Title
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.primary };

  // accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 2.7, w: 13.3, h: 0.08, fill: { color: C.rose }, line: { color: C.rose }
  });

  s.addText("2026-04-06 회의 액션 아이템", {
    x: 0.8, y: 1.0, w: 12, h: 0.7,
    fontFace: FH, fontSize: 34, bold: true, color: C.cream, margin: 0
  });
  s.addText("9건 진척도 + Gap 분석 + 개선 로드맵", {
    x: 0.8, y: 1.75, w: 12, h: 0.7,
    fontFace: FH, fontSize: 24, color: C.cream, margin: 0
  });
  s.addText("KAERI-AIRL-MOM-2026-003 (제3차 월간회의) ─ 현재 시스템 매핑", {
    x: 0.8, y: 2.95, w: 12, h: 0.4,
    fontFace: FB, fontSize: 14, italic: true, color: C.rose, margin: 0
  });

  // 3 status stat boxes
  const statsY = 4.0;
  const stats = [
    { label: "완료", value: "1", sub: "A-08 외부망 H100×8 배포", color: C.done },
    { label: "부분 진행", value: "3", sub: "A-01 · A-04 · A-10", color: C.partial },
    { label: "미진행", value: "5", sub: "A-02 · A-03 · A-05 · A-06 · A-09", color: C.pending },
  ];
  stats.forEach((b, i) => {
    const x = 0.8 + i * 4.2;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: statsY, w: 3.8, h: 2.0,
      fill: { color: b.color }, line: { color: b.color, width: 0 }
    });
    s.addText(b.value, {
      x, y: statsY + 0.2, w: 3.8, h: 1.0,
      fontFace: FH, fontSize: 80, bold: true, color: C.white, align: "center", margin: 0
    });
    s.addText(b.label, {
      x, y: statsY + 1.2, w: 3.8, h: 0.35,
      fontFace: FH, fontSize: 16, bold: true, color: C.white, align: "center", margin: 0
    });
    s.addText(b.sub, {
      x: x + 0.2, y: statsY + 1.55, w: 3.4, h: 0.35,
      fontFace: FB, fontSize: 10, color: C.white, align: "center", italic: true, margin: 0
    });
  });

  s.addText("A-07 (DGX 견적) ─ 사용자(서호성/안기범) 담당, 본 분석 범위 밖", {
    x: 0.8, y: 6.4, w: 12, h: 0.3,
    fontFace: FB, fontSize: 11, italic: true, color: C.cream, margin: 0
  });
  s.addText("2026-05-19  ·  orchestrator-session  ·  DAG v2.1 Tier 0+1 적용 상태", {
    x: 0.8, y: 6.85, w: 12, h: 0.3,
    fontFace: FB, fontSize: 11, color: C.rose, margin: 0
  });
}

// ============================================================
// Slide 2 — Executive Summary
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "Executive Summary", "9개 액션 아이템 1개월 진척도 (한 줄 결론 + KPI 표)");

  // Top callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 12.3, h: 1.1,
    fill: { color: C.primary }, line: { color: C.primary }
  });
  s.addText("한 줄 결론", {
    x: 0.7, y: 1.3, w: 11.7, h: 0.35,
    fontFace: FH, fontSize: 18, bold: true, color: C.cream, margin: 0
  });
  s.addText('"인프라(A-07/08) + 도킹 코드(A-01/A-10) 부분 진행. 약리학(A-02/A-03) + 스코어링(A-04/A-09) + ΔG 기준선(A-05) + 디퓨전 PoC(A-06)는 전부 분석/구현 대기 — 회의 후 6주 경과, 5월 회의 시점 기준 미달성."', {
    x: 0.7, y: 1.7, w: 11.7, h: 0.55,
    fontFace: FB, fontSize: 13, italic: true, color: C.white, margin: 0
  });

  // KPI 매핑 표
  const rows = [
    ["KPI", "기준", "관련 액션", "현재 상태"],
    ["결합 친화도 (SSTR2 선택성)", "ΔΔG < −1 kcal/mol", "A-01, A-05, A-10", "⚠ 부분 (Boltz-2 가동, 기준선 미확정)"],
    ["혈청 반감기 TPP-B", "≥ 24시간", "A-02, A-04", "✗ 도구 비교 0건"],
    ["혈청 반감기 TPP-C", "≥ 72시간", "A-02, A-04", "✗ D-AA 도구 미확보"],
    ["ADMET 독성", "Fab-ADMET 또는 대안", "A-03, A-04", "✗ Fab-ADMET URL 미확인"],
    ["최종 후보 수", "3-4개 (Tier-S)", "A-04, A-09", "✗ A-04 미완성 → 자동 트리거 안 됨"],
    ["도킹 가속화", "디퓨전 PoC 성공", "A-06, A-07", "✗ DiffDock 환경 부재"],
  ];
  s.addTable(rows, {
    x: 0.5, y: 2.5, w: 12.3,
    fontSize: 11, fontFace: FB, color: C.ink,
    border: { pt: 0.5, color: C.muted },
    rowH: 0.4,
    colW: [3.6, 2.5, 2.5, 3.7],
    fill: { color: C.white },
  });

  // bottom recommendation
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.7, w: 12.3, h: 1.3,
    fill: { color: C.cream }, line: { color: C.rose, width: 0 }
  });
  s.addText("권장 다음 행동 (우선순위)", {
    x: 0.7, y: 5.8, w: 11.7, h: 0.3,
    fontFace: FH, fontSize: 14, bold: true, color: C.primary, margin: 0
  });
  s.addText([
    { text: "1주 ", options: { bold: true, color: C.info } },
    { text: "A-05 SST14 ΔG 기준선 (n≥10 반복)  +  A-10 SSTR3 전처리 표준화  +  A-02/A-03 researcher 위임\n", options: { color: C.ink } },
    { text: "2주 ", options: { bold: true, color: C.partial } },
    { text: "A-04 composite_scorer.py 구현 (WSS + Pareto) + 단위 테스트 ≥10  +  A-01 결합 포켓 좌표 추출\n", options: { color: C.ink } },
    { text: "4주 ", options: { bold: true, color: C.done } },
    { text: "A-09 최종 후보 3-4개 자동 도출 + 합성 의뢰서  +  A-06 DiffDock PoC (A-07 견적 병행)", options: { color: C.ink } },
  ], {
    x: 0.7, y: 6.15, w: 11.9, h: 0.8,
    fontFace: FB, fontSize: 11, margin: 0
  });

  pageNum(s, 2, TOTAL);
}

// ============================================================
// Slide 3 — A-01
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-01 · SSTR1/3/4/5 위치 지정 도킹", "결합 포켓 좌표 확정 + 재도킹 + 네거티브 디자인", { color: C.partial, text: "⚠ 부분 진행" });
  addActionSlide(s, {
    proposal: "Boltz-2 + FlexPepDock legacy로 off-target 도킹. SSTR2(7T10/7T11) cryo-EM에서 ECL/TM 핵심 잔기(77-314) 추출. SSTR1/3/4/5 → SSTR2 cealign 정렬, 반경 15-20Å docking box (GNINA/AutoDock-GPU 입력 형식). 선택성 배수 ≥100× (권장 ≥300×).",
    seo: "SSTR2 결합 영역은 ECL/TM 핵심 잔기 표 기준 잔기 77-314. ECL2(192·193·195·197), ECL3(284·286), TM3(122·126), TM5(205·208·209·212), TM6(272·273·276·279), TM7(291·294·298). 블라인드 도킹과 속도 차이는 크지 않으나, 핵심 잔기 정보를 네거티브 디자인의 정량 근거로 활용.",
    status: { color: C.partial },
    current: "✓ Boltz-2 selectivity_runner.py 가동 (Tier 0 P14 — worst off-target FE 데이터 오류 hotfix). 키 소문자 통일 + margin 부호 step05c iPTM 컨벤션 통일 (+10.0, worst_ot - sstr2).\n\n✗ binding_pocket_SSTR2.json 미생성 / 핵심 잔기 표 네거티브 디자인 미반영 / GNINA box 형식 미적용 / FlexPepDock legacy → site-directed 이전 미진행.\n\n⚠ SSTR2 구조 ID 회의(7T10) vs 로컬(7XNA) 불일치 — 담당팀 확정 필요.",
    gap: "1) PyMOL center_of_mass 좌표 추출 + JSON 저장 미진행\n2) cealign SSTR1/3/4/5 → SSTR2 배치 정렬 0건\n3) GNINA/AutoDock-GPU YAML config 미생성\n4) 네거티브 디자인 잔기 마스크 적용 0건\n5) 회의 원문 7T10 vs 로컬 7XNA 의사결정 보류",
    fix: "Step 1) 7XNA pocket residue center_of_mass 추출 → binding_pocket_SSTR2.json\nStep 2) 5 receptor 배치 cealign + TM-score ≥0.7 검증\nStep 3) site-directed YAML 생성 + Boltz-2 추가 호출\nStep 4) ECL2/3·TM3/5/6/7 핵심 잔기 마스크 negative_design.json\nStep 5) A-10 SSTR3 전처리 선행 후 셀렉티비티 배수 재산출",
  });
  pageNum(s, 3, TOTAL);
}

// ============================================================
// Slide 4 — A-02
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-02 · 혈청 반감기 예측 도구 비교", "벤치마크 세트 기반 정확도 평가 (R², Spearman ρ)", { color: C.pending, text: "✗ 미진행" });
  addActionSlide(s, {
    proposal: "ProtParam · HLP · PlifePred · PeptideRanker · PeptideStability ML 비교. SST-14(~3분) / Octreotide(~100분) / Lanreotide(수시간) / RC-160 벤치마크 세트. R² ≥0.5 · Spearman ρ ≥0.7 · D-AA 지원 도구 ≥1개 확보 · 로컬 실행 가능 우선.",
    seo: "1차 Serum Stability는 ProtParam으로, Modification 후에는 MD(RMSD)로 Stability 예측. 최종은 직접 Serum Stability 실험 측정 병행. D-Phe 등 변형된 아미노산 분석 가능한 도구가 더 좋음. 지방산 수식(lipidation) 지원 여부 별도 확인 필수.",
    status: { color: C.pending },
    current: "✓ pharmacology_guards.py에 instability_index · GRAVY · Boman 휴리스틱 등록됨 (HEURISTIC 신뢰등급).\n\n✗ HLP 1.6초 예측 재현 0건 / D-AA 도구 ≥1개 확보 0건 / PeptideStability ML 모델 GitHub 검토 0건.\n\n✗ MD(RMSD) bridge — Modification 후 stability 예측 메커니즘 0건.\n\n✗ ENDPOINT_CONFIDENCE['halflife_<tool>'] 등록 명세 완료, 실 코드 등록 0건.",
    gap: "1) 5개 도구 벤치마크 매트릭스 빈 셀\n2) D-Phe / D-Trp 지원 도구 식별 0건 — 필수 요구사항 미충족\n3) 지방산 수식(lipidation) 지원 도구 확인 안 됨\n4) MD 기반 stability ↔ in silico 도구 상관관계 미정량\n5) 자체 ML 모델 로드맵 미수립 (D-AA 데이터 수집 절차 필요)",
    fix: "Step 1) researcher 에이전트 위임 — 5개 도구 GitHub/API 클론 + SST14·Octreotide·Lanreotide 입력 테스트\nStep 2) R² + Spearman ρ 매트릭스 산출 + 후보 도구 ≥2개 선정\nStep 3) ENDPOINT_CONFIDENCE 등록 (P1~P4 등급)\nStep 4) D-AA 지원 도구 확보 못 시 자체 ML 모델 12주 로드맵 + 데이터셋 수집 계획\nStep 5) HEURISTIC disclaimer + LITERATURE_VALUES 보강",
  });
  pageNum(s, 4, TOTAL);
}

// ============================================================
// Slide 5 — A-03
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-03 · Fab-ADMET 정확도 검증", "환형 / D-아미노산 / DOTA 결합 펩타이드 적용 가능성", { color: C.pending, text: "✗ 미진행" });
  addActionSlide(s, {
    proposal: "Fab-ADMET ML 도구의 펩타이드 ADMET 예측 정확도 검증. AUC ≥0.80, D-AA 지원 필수, 환형 펩타이드 + DOTA 결합 처리 가능 여부. 미지원 시 자체 학습 모델 구축 (H100 NVL 기준 GPU 요구사양 + 예상 학습 시간 산정).",
    seo: "보다 정밀한 Serum Stability 혹은 인체 반감기 측정 프로그램을 찾아 사용할 필요, 특히 D-Phe 등 변형된 아미노산 분석 가능하면 더 좋음. ADMET 독성 외에 혈청 안정성(serum stability) 예측 기능도 탐색.",
    status: { color: C.pending },
    current: "✗ Fab-ADMET GitHub URL 회의록 미명시 — 핵심 블로커.\n\n✗ 원 논문 AUC/Accuracy/F1 수집 0건 / SST14·Octreotide·Lanreotide 입력 테스트 0건.\n\n✗ 학습 데이터에 환형 펩타이드 / D-AA 포함 여부 확인 0건.\n\n✗ ENDPOINT_CONFIDENCE['fab_admet'] 명세만, 실 코드 0건.\n\n⚠ modification_conflict_rules에 C-04 (D-Cys → SS bond) + C-07 (DOTA stoichiometry)는 등록됨.",
    gap: "1) Fab-ADMET GitHub URL 확인 (researcher 위임 필수) — 모든 후속 작업 블로커\n2) 라이선스 확인 (상업적 활용 가능 여부)\n3) SMILES 입력 형식 지원 여부 — DOTA 킬레이터 처리 가능성\n4) 학습 데이터 환형/D-AA/DOTA 비율 미확인\n5) 자체 fine-tuning 옵션 + GPU 요구사양 미산정",
    fix: "Step 1) researcher: Fab-ADMET GitHub URL + 라이선스 + 논문 지표 확보\nStep 2) 클론 후 README/Supplementary로 입력 형식 + 학습 데이터 분포 확인\nStep 3) SST14 · Octreotide · Lanreotide 직접 입력 테스트 (3 후보)\nStep 4) 결과 → ENDPOINT_CONFIDENCE 등급 부여 + HEURISTIC_FUNCTION_DISCLAIMERS 등록\nStep 5) 미지원 시 자체 학습 모델 12주 로드맵 + 대안 도구 (ADMET Lab 2.0, DeepPK 등) 탐색",
  });
  pageNum(s, 5, TOTAL);
}

// ============================================================
// Slide 6 — A-04
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-04 · 복합 스코어링 체계 (Top-K)", "Hard Cutoff + WSS + Pareto front 다목적 최적화", { color: C.partial, text: "⚠ 부분 진행" });
  addActionSlide(s, {
    proposal: "13-metric panel + 7단계 다단계 선별. Hard Cutoff (ΔG · 셀렉티비티 ≥100× · Radiolysis ≤3개 · ADMET ≤0.3 · Instability <40). Soft Ranking (WSS w1~w5 + NSGA-II Pareto). Tier-S/A/B 분류 + Critic/Planner 자동 검증.",
    seo: "Radiolysis 민감도 (Cys·Met=3, Phe·Tyr·Trp=2, Pro·His·Leu=1). Cys3-Cys14 SS bond 예외 처리. Quencher DOE (QC-1 Gentisic·Ascorbic·Ethanol / QC-2 Met·Ethanol / QC-3 Cys·Gentisic / QC-4 4종 복합). 변형 전략 (Met→Nle · Trp→5-F-Trp · Tyr→3-F-Tyr · SS→Thioether/Lactam/Dicarba).",
    status: { color: C.partial },
    current: "✓ cluster_report.py batch_classify 가동 (Tier 1 sprint, A~E 5 클러스터, 65/65 tests). Tier 1 P05로 BE candidate에 6필드(selectivity_margin · instability_index · gravy · net_charge_ph74 · fwkt_contact · chelator_site_available) on-the-fly 머지 (status.py `_enrich_candidates`).\n\n✓ pharmacology_guards.py에 Hard Cutoff 일부 가드 등록.\n\n✗ composite_scorer.py 신규 모듈 미구현 / WSS + Pareto front NSGA-II 0건 / Tier-S/A/B 자동 분류 0건.\n\n✗ radiolysis_scorer.py 미구현 (변이 전략 매핑 표는 회의록에 있음).",
    gap: "1) composite_scorer.py 미구현 — A-09 자동 트리거 차단\n2) WSS 가중치 (0.35/0.25/0.20/0.10/0.10) 검증 안 됨\n3) NSGA-II Pareto front (pymoo) 미통합\n4) radiolysis_scorer.py 별도 모듈 미생성\n5) Critic/Planner 자동 검증 + 다음 세대 변이 규칙 연동 0건",
    fix: "Step 1) composite_scorer.py 신규 + WSS 구현 (min-max 정규화)\nStep 2) pymoo NSGA-II 통합 + Pareto front 추출\nStep 3) radiolysis_scorer.py + Cys3-Cys14 ss_bond_intact 플래그\nStep 4) Tier-S/A/B 분류 + reviewer-math NSGA-II 수렴 검증 위임\nStep 5) Critic + Planner agent 통합 → 다음 세대 변이 BLOSUM/Radiolysis 규칙 자동 갱신",
  });
  pageNum(s, 6, TOTAL);
}

// ============================================================
// Slide 7 — A-05
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-05 · SST14 레퍼런스 ΔG 기준선", "n≥10 반복 도킹 + 하드코딩 임계값 교체 + 3단계 스크리닝", { color: C.pending, text: "✗ 미진행" });
  addActionSlide(s, {
    proposal: "step05_docking.py의 하드코딩 `-5` 임계값 → SST14 원형 SSTR2 도킹 n≥10 반복 Mean으로 교체. 임계값 = ref_ddg × 0.9 (10% 허용). LITERATURE_VALUES 등록 + 3단계 스크리닝 (FlexPepDock → MM-GBSA → FEP/TI).",
    seo: "n회 반복 Mean 값 사용 (단일 도킹의 분산 큼). MD simulation 검토. 3단계 스크리닝 — 1차 FlexPepDock 200-500개 → 2차 MM-GBSA 20-50개 (킬레이터 부착 후) → 3차 FEP/TI 최종 후보 (OpenMM/OpenFE/gmx_MMPBSA).",
    status: { color: C.pending },
    current: "✗ pipeline_local/steps/step05_docking.py에 DOCKING_GATE_THRESHOLD=-5.0 그대로 하드코딩.\n\n✗ SST14 n=10 반복 도킹 0건 / Mean·σ 산출 0건.\n\n✗ LITERATURE_VALUES['SST14_SSTR2_ref_ddg_boltz2_mean'] 미등록.\n\n✗ config_loader.py 통한 동적 임계값 로드 0건.\n\n✗ 2차 MM-GBSA · 3차 FEP/TI 로드맵 미작성.",
    gap: "1) 가장 단순한 작업이지만 미진행 (1주 작업)\n2) 하드코딩 임계값은 생물학적 근거 없음 — 모든 후속 게이트 판정의 신뢰성 영향\n3) MM-GBSA · FEP/TI 정밀 스크리닝 계획 부재\n4) yaml 단위 표기 'kcal/mol' vs 실 REU 가능성 (어제 reviewer-science 분석)",
    fix: "Step 1) offtarget_dock.py 반복 실행 (n≥10, SST14 → SSTR2_7XNA)\nStep 2) ddg Mean/σ 계산 + ref_ddg × 0.9 임계값 산출\nStep 3) step05_docking.py 하드코딩 → config 기반 (docking_gate_threshold)\nStep 4) LITERATURE_VALUES 등록 + yaml '단위' kcal/mol→REU 정정 (G-2)\nStep 5) MM-GBSA + FEP/TI 별도 Action Item 등록 (12주 로드맵)",
  });
  pageNum(s, 7, TOTAL);
}

// ============================================================
// Slide 8 — A-06
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-06 · 디퓨전 모델 기반 도킹 가속화 PoC", "DiffDock · RMSD ≤2.0Å 80% · ≥10× speedup", { color: C.pending, text: "✗ 미진행" });
  addActionSlide(s, {
    proposal: "DiffDock SE(3) diffusion 모델로 1 inference 수십 초 처리. RMSD ≤2.0Å Top-1 성공률 ≥80% (40 포즈 중 32개+). Wall-clock speedup ≥10× vs FlexPepDock. VRAM ≤80GB 단일 H100 NVL, 회의록 원문 VRAM ≥120GB 시 A-07 연동.",
    seo: "DiffDock은 소분자 리간드 기본 설계 — 펩타이드(14aa) 적용 시 DiffDock-PP 변형 검토. NeuralPLexer / AlphaFold3도 후보. PoC 성공 시 Silo B FlexPepDock 전단에 DiffDock pre-filter 배치.",
    status: { color: C.pending },
    current: "✗ DiffDock conda env 미설치 / 모델 다운로드 0건.\n\n✗ Ground truth SST14 cryo-EM 포즈 추출 0건 (7T10/7T11 펩타이드 체인 또는 7XNA 펩타이드 포함).\n\n✗ RMSD 비교 (BioPython Superimposer) 0건.\n\n✗ 속도 비교 (wall-clock time) 0건.\n\n⚠ H100 NVL ×4 가용 (CUDA_VISIBLE_DEVICES=2,3, 총 188GB). VRAM 120GB Multi-GPU 모드 가능 여부 미검증.",
    gap: "1) DiffDock 환경 자체 부재 — engineer-infra 요청 필요\n2) Ground truth 포즈 (7T10/7T11 펩타이드 체인) 데이터 미준비\n3) DiffDock-PP 또는 펩타이드 변형 모델 선정 안 됨\n4) VRAM 실측 0건 — A-07 견적 결정의 핵심 입력 누락\n5) Silo B 통합 시 step05_docking.py 대체 전략 미수립",
    fix: "Step 1) engineer-infra: conda diffdock env 구축 + 모델 weight 다운로드\nStep 2) RCSB 7T10/7T11 펩타이드 체인 추출 → ground_truth.pdb\nStep 3) DiffDock-PP 또는 NeuralPLexer 중 펩타이드 적합 모델 선정\nStep 4) PoC 실행 (40 포즈 × 5 후보) + RMSD + Wall-clock 비교\nStep 5) VRAM 실측 → A-07 견적 보고 + poc_report.json 작성",
  });
  pageNum(s, 8, TOTAL);
}

// ============================================================
// Slide 9 — A-07
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-07 · DGX/고성능 GPU 서버 견적", "옵션 A DGX H100 · B DGX B200 · C 자체 빌드 · 6 셀 매트릭스", { color: C.pending, text: "✗ TBD (사용자)" });
  addActionSlide(s, {
    proposal: "최소 2개 벤더 공식 견적. DGX H100 (VRAM 640GB / FP8 3.9 PFLOPS / 10U) vs DGX B200 (1440GB / 9.0 PFLOPS / 10U) vs 자체 빌드 H100. NVLink 토폴로지 점검 → 기존 H100×8 단일 fabric 통합 가능 시 추가 구매 보류.",
    seo: "VRAM 120GB 이상이 디퓨전 모델 단일 로딩에 필요. H100×8 NVLink 통합 시 640GB 확보 가능 → 우선 점검. 실패 시 DGX H100 vs B200 ROI 비교 (B200은 단일 GPU 180GB로 단일 모델 로딩 최적).",
    status: { color: C.pending },
    current: "✓ H100 NVL ×4 (각 96GB, 총 384GB) 사용자 로컬 확보 (CUDA_VISIBLE_DEVICES=2,3).\n\n✓ A-08 외부망 H100×8 (80GB×8 = 640GB) 배포 완료 (회의록 §2.3).\n\n✗ 비교 매트릭스 전 셀 TBD — 벤더 견적 0건.\n\n✗ 외부망 nvidia-smi topo -m 점검 0건 — NVLink fabric 통합 여부 미확인.\n\n✗ A-06 VRAM 실측값 0건 (A-06 미진행으로 인한 의존성 차단).",
    gap: "1) 본 항목은 사용자(서호성/안기범) 책임 — AI팀이 직접 수행 불가\n2) A-06 PoC VRAM 실측이 견적 결정의 핵심 입력 (의존성)\n3) NVIDIA·HPE·Dell·Supermicro 견적 의뢰 0건\n4) 외부망 H100×8 NVLink 통합 점검 0건 (AI팀이 nvidia-smi 점검 가능)",
    fix: "Step 1) AI팀 — 외부망 H100×8 nvidia-smi topo -m + free VRAM 점검 (즉시 가능)\nStep 2) A-06 PoC 진행 → peak VRAM 기록 (engineer-infra 협업)\nStep 3) 사용자 — NVIDIA 공식 + 공인 리셀러 견적 의뢰 (2 벤더)\nStep 4) HPE/Dell/Supermicro 자체 빌드 견적 의뢰\nStep 5) 6 셀 매트릭스 완성 → 의사결정 회의 안건 등록",
  });
  pageNum(s, 9, TOTAL);
}

// ============================================================
// Slide 10 — A-09
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-09 · 최종 후보 3-4개 + 합성 의뢰서", "Gate-1 (계산) → Gate-2 (표지/제조) 진입 마일스톤", { color: C.pending, text: "✗ 미진행" });
  addActionSlide(s, {
    proposal: "A-04 composite_scorer.py 실행 → Tier-S 3-4개 + 서열 다양성 ≤80%. RI팀 합성 가능성 협의 (비천연 AA · 고리화 전략 · 수율 ≥20% · 킬레이터 접합). 합성 의뢰서 7 항목 (서열 · modification · 순도 ≥95% · 납기 · 수량 · 특이사항).",
    seo: "최종 후보는 합성 가능성이 계산 점수만큼 중요 — RI팀과 사전 협의 없이 합성 의뢰서 발송 금지. Radiolysis 72시간 RCP ≥90% 미달 시 Step 5 Amino Acid Modification 재진입. DOTA vs DFO 선택: ¹⁷⁷Lu에는 DOTA 우선, ⁶⁸Ga PET는 둘 다.",
    status: { color: C.pending },
    current: "✗ A-04 composite_scorer.py 미구현 → A-09 자동 트리거 불가.\n\n✗ tier_s_candidates.csv · synthesis_feasibility.md · synthesis_request_<date>.md 0건.\n\n⚠ 별도 세션 PR #43 manual-selectivity 페이지 (FlexPepDock UI)는 부분 — wetlab BE candidate_id 제한 풀기 필요.\n\n✗ 서열 다양성 ≤80% 필터 미구현 / Tier-S 우선 선별 로직 0건.\n\n✗ MOM-002 A-10 킬레이터 벤더 리스트 연동 0건.",
    gap: "1) A-04 의존성 — 선행 필수\n2) RI팀 합성 가능성 협의 채널 미구축\n3) 비천연 AA (Nle · 5-F-Trp · Abu · Orn 등) 국내 조달 가능성 확인 0건\n4) DOTA/DFO 킬레이터 접합 위치 결정 절차 0건\n5) Quencher DOE 조합 (QC-1~QC-4) 의뢰서 기재 표준 0건",
    fix: "Step 1) A-04 완료 후 자동 트리거 — composite_scorer 결과 → tier_s_candidates.csv\nStep 2) RI팀 협의 양식 표준화 (synthesis_feasibility 템플릿)\nStep 3) select_final_candidates.py 신규 — Tier-S 우선 + 서열 다양성 ≤80%\nStep 4) synthesis_checker.py — 비천연 AA 조달·수율 가능성 자동 체크\nStep 5) generate_synthesis_request.py — 7 항목 의뢰서 자동 생성 + Quencher 4 조합 + DOTA/DFO 선택란",
  });
  pageNum(s, 10, TOTAL);
}

// ============================================================
// Slide 11 — A-10
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "A-10 · SSTR3 도킹 에러 해결", "구조 전처리 (missing residues · clashes · B-factor) → 재도킹", { color: C.partial, text: "⚠ 부분 진행" });
  addActionSlide(s, {
    proposal: "SSTR3 도킹 에러 재현 → 원인 분류 (KeyError · clash · B-factor · CIF 파싱). PDB 검사 (REMARK 465 · find_clashes · 체인) → 전처리 (Modeller/SWISS-MODEL · PyRosetta MinMover · BioPython B-factor 클램핑) → SSTR3_8XIR_preprocessed.pdb 별도 등록.",
    seo: "회의록에서 A-10을 별도 언급한 만큼 SSTR3 구조 품질 문제 실재. 필수 점검 — (1) 누락 잔기 (2) 충돌 원자 (3) 비정상 B-factor. data/ 디렉토리 READ-ONLY 원칙 — 원본 보존, 전처리본은 별도 파일.",
    status: { color: C.partial },
    current: "✓ Boltz-2 기반 selectivity 시나리오 #9 PASS 확인 (어제 Tier 1 회귀, A~E 클러스터 분포 정상). SSTR3 (8XIR) 자체는 도킹 가동.\n\n✓ 데이터 디렉토리에 SSTR3_8XIR.pdb/cif 배치됨.\n\n⚠ 명시적 구조 전처리 절차 (Modeller / MinMover / B-factor) 0건 — 도킹은 가동하지만 품질 보장은 안 됨.\n\n✗ SSTR3_8XIR_preprocessed.pdb 별도 등록 0건 / data/README.md 변경 이력 0건.\n\n✗ 에러 재현 절차 표준화 0건.",
    gap: "1) 도킹 자체는 통과되지만 구조 품질 점검 절차 부재 (REMARK 465 · clashes · B-factor)\n2) 전처리 표준 절차 (Modeller / MinMover / B-factor 클램핑) 코드화 안 됨\n3) data/ READ-ONLY 경계 명시 안 됨 — 원본 vs 전처리본 구분 절차\n4) test_offtarget_dock_boltz.py에 SSTR3 전처리 검증 케이스 없음",
    fix: "Step 1) offtarget_dock.py SSTR3 1회 dogfood → 에러 메시지 분류표 작성\nStep 2) PyMOL find_clashes + REMARK 465 + B-factor>100 점검 스크립트 표준화\nStep 3) preprocess_sstr_structure.py 신규 — Modeller / MinMover / B-factor 클램핑 자동\nStep 4) SSTR3_8XIR_preprocessed.pdb 등록 + data/README.md 변경 이력\nStep 5) test_offtarget_dock_boltz.py SSTR3 케이스 추가 + selectivity_runner.py 경로 갱신",
  });
  pageNum(s, 11, TOTAL);
}

// ============================================================
// Slide 12 — 통합 갭 매트릭스
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "통합 갭 매트릭스", "9 액션 × 5 차원 (제안·현재·진척·gap·priority)");

  const rows = [
    ["ID", "주제", "회의 제안 핵심", "현재 시스템 (Tier 0+1)", "진척률", "P"],
    ["A-01", "SSTR1/3/4/5 위치 지정", "결합 포켓 좌표 + cealign", "Boltz-2 selectivity 가동 / 좌표 미생성", "30%", "P1"],
    ["A-02", "혈청 반감기 도구 비교", "5 도구 R²·Spearman ρ + D-AA", "휴리스틱만 (instability·GRAVY·Boman)", "10%", "P1"],
    ["A-03", "Fab-ADMET 검증", "GitHub 클론 + 환형/D-AA/DOTA", "URL 미확인 (블로커)", "0%", "P1"],
    ["A-04", "복합 스코어링", "Hard Cutoff + WSS + Pareto", "cluster_report (A~E) + 6필드 머지", "40%", "P1"],
    ["A-05", "SST14 ΔG 기준선", "n≥10 반복 Mean + 임계값 교체", "DOCKING_GATE_THRESHOLD=-5 하드코딩", "0%", "P0"],
    ["A-06", "DiffDock PoC", "RMSD ≤2Å 80% + ≥10× speedup", "DiffDock 환경 부재", "0%", "P2"],
    ["A-07", "DGX 견적", "6 셀 매트릭스", "TBD 전부 (사용자 책임)", "0%", "P2"],
    ["A-08", "외부망 서버", "(완료)", "H100×8 배포 완료", "100%", "✓"],
    ["A-09", "최종 후보 3-4개", "Tier-S + 합성 의뢰서", "A-04 의존성으로 차단", "5%", "P2"],
    ["A-10", "SSTR3 에러 해결", "구조 전처리 + 재등록", "도킹 가동 / 전처리 표준 0건", "40%", "P0"],
  ];

  s.addTable(rows, {
    x: 0.4, y: 1.15, w: 12.5,
    fontSize: 10.5, fontFace: FB, color: C.ink,
    border: { pt: 0.5, color: C.muted },
    rowH: 0.46,
    colW: [0.7, 2.2, 3.5, 3.8, 1.2, 1.1],
    fill: { color: C.white },
  });

  // Bottom legend
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.75, w: 12.3, h: 0.4,
    fill: { color: C.cream }, line: { color: C.rose, width: 0 }
  });
  s.addText("P0 = 즉시(1주, 가장 단순) · P1 = 단기(2-4주, 핵심) · P2 = 중기(4-8주, 의존성) · ✓ = 완료", {
    x: 0.7, y: 6.78, w: 11.9, h: 0.35,
    fontFace: FB, fontSize: 11, italic: true, color: C.primary, margin: 0
  });

  pageNum(s, 12, TOTAL);
}

// ============================================================
// Slide 13 — 우선순위 로드맵
// ============================================================
{
  const s = pres.addSlide();
  addHeader(s, "우선순위 로드맵", "P0 (1주) · P1 (2-4주) · P2 (4-8주) — 의존성 그래프 반영");

  const phases = [
    {
      title: "P0  ·  1주 (즉시)",
      c: C.done,
      items: [
        "A-05 SST14 n≥10 반복 도킹 + Mean·σ 산출",
        "A-05 step05_docking.py 임계값 config 기반",
        "A-05 LITERATURE_VALUES 등록 + yaml 단위 정정 (G-2)",
        "A-10 SSTR3 전처리 표준화 (Modeller·MinMover·B-factor)",
        "A-10 preprocess_sstr_structure.py + test 추가",
        "A-02·A-03 researcher 위임 (Fab-ADMET URL + 5 도구 매트릭스)",
      ],
    },
    {
      title: "P1  ·  2-4주 (핵심)",
      c: C.partial,
      items: [
        "A-04 composite_scorer.py (WSS + Pareto)",
        "A-04 radiolysis_scorer.py + ss_bond_intact",
        "A-04 NSGA-II (pymoo) + reviewer-math 검증",
        "A-01 binding_pocket_SSTR2.json + cealign",
        "A-01 site-directed YAML + 네거티브 디자인",
        "A-02 5 도구 R²·Spearman ρ 매트릭스",
        "A-02 D-AA 지원 도구 ≥1개 확보 또는 자체 모델 로드맵",
        "A-03 Fab-ADMET SST14 직접 테스트 + ENDPOINT_CONFIDENCE",
      ],
    },
    {
      title: "P2  ·  4-8주 (의존성)",
      c: C.info,
      items: [
        "A-09 select_final_candidates.py + synthesis_checker.py",
        "A-09 generate_synthesis_request.py (7 항목 + Quencher)",
        "A-09 RI팀 합성 가능성 협의 (비천연 AA 조달)",
        "A-06 DiffDock conda env 구축 + ground truth 추출",
        "A-06 PoC 실행 (RMSD + Wall-clock + VRAM)",
        "A-07 외부망 NVLink 점검 + 견적 6 셀 매트릭스",
        "MM-GBSA · FEP/TI 2·3차 스크리닝 별도 트랙",
      ],
    },
  ];

  phases.forEach((p, i) => {
    const x = 0.45 + i * 4.25;
    const y = 1.2;
    const w = 4.15;
    const h = 5.85;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: C.white }, line: { color: p.c, width: 1.5 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.75, fill: { color: p.c }, line: { color: p.c }
    });
    s.addText(p.title, {
      x: x + 0.2, y: y + 0.18, w: w - 0.4, h: 0.45,
      fontFace: FH, fontSize: 16, bold: true, color: C.white, margin: 0
    });

    const bulletItems = p.items.map((it, k) => ({
      text: it,
      options: { bullet: true, breakLine: k < p.items.length - 1, fontSize: 10.5, color: C.ink, paraSpaceAfter: 5 }
    }));
    s.addText(bulletItems, {
      x: x + 0.2, y: y + 0.95, w: w - 0.4, h: h - 1.1,
      fontFace: FB,
    });
  });

  pageNum(s, 13, TOTAL);
}

// ============================================================
// Slide 14 — Closing
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.primary };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.9, w: 13.3, h: 0.06, fill: { color: C.rose }, line: { color: C.rose }
  });

  s.addText("Closing · 다음 회의 안건", {
    x: 0.8, y: 0.6, w: 12, h: 0.8,
    fontFace: FH, fontSize: 38, bold: true, color: C.cream, margin: 0
  });

  const cols = [
    {
      title: "이번 주 (P0)",
      c: C.done,
      items: [
        "A-05 SST14 n=10 반복 도킹",
        "A-05 임계값 config 기반 교체",
        "A-10 전처리 표준화 + test",
        "researcher: Fab-ADMET URL 확보",
      ],
    },
    {
      title: "이번 달 (P1)",
      c: C.partial,
      items: [
        "A-04 composite_scorer.py",
        "A-01 결합 포켓 좌표 + cealign",
        "A-02 5 도구 매트릭스",
        "A-03 Fab-ADMET 테스트 + 등급",
        "Critic/Planner 자동 검증 통합",
      ],
    },
    {
      title: "5월 회의 안건",
      c: C.info,
      items: [
        "A-04/A-09 → Tier-S 3-4개 시연",
        "A-02/A-03 도구 채택 결정",
        "A-07 견적 매트릭스 의사결정",
        "Gate-2 진입 준비 (RI팀)",
        "MM-GBSA·FEP/TI 로드맵",
      ],
    },
  ];

  cols.forEach((col, i) => {
    const x = 0.8 + i * 4.05;
    const y = 1.85;
    const w = 3.9;
    const h = 4.5;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: C.rose }, line: { color: col.c, width: 0 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.08, fill: { color: col.c }, line: { color: col.c }
    });
    s.addText(col.title, {
      x: x + 0.25, y: y + 0.2, w: w - 0.5, h: 0.55,
      fontFace: FH, fontSize: 19, bold: true, color: C.white, margin: 0
    });

    const bulletItems = col.items.map((it, k) => ({
      text: it,
      options: { bullet: true, breakLine: k < col.items.length - 1, fontSize: 13, color: C.white, paraSpaceAfter: 6 }
    }));
    s.addText(bulletItems, {
      x: x + 0.25, y: y + 0.95, w: w - 0.5, h: h - 1.1,
      fontFace: FB,
    });
  });

  s.addText("회의록  ·  docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf", {
    x: 0.8, y: 6.6, w: 12, h: 0.3,
    fontFace: FB, fontSize: 11, color: C.cream, italic: true, margin: 0
  });
  s.addText("액션 아이템 디렉토리  ·  docs/meet_log/2026-04-06_action_items/  (10 markdown + 9 prompts)", {
    x: 0.8, y: 6.85, w: 12, h: 0.3,
    fontFace: FB, fontSize: 11, color: C.rose, italic: true, margin: 0
  });
  s.addText("2026-05-19  ·  orchestrator-session  ·  현재 시스템 진척도 (Tier 0+1 완료 기준)", {
    x: 0.8, y: 7.1, w: 12, h: 0.3,
    fontFace: FB, fontSize: 10, color: C.rose, margin: 0
  });
}

// ============================================================
// Save
// ============================================================
pres.writeFile({ fileName: "action-items-2026-04-06-progress-2026-05-19.pptx" })
  .then(name => console.log("created:", name))
  .catch(err => { console.error("ERR:", err); process.exit(1); });
