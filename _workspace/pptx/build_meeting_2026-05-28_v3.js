// 2026-05-28 KAERI-AIRL-MOM-2026-004 (예정) narrative v3 PPTX build
// Source: _workspace/release/meeting-2026-05-28-narrative-v3.md

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const IMG_ADMET_SCATTER = path.join(
  __dirname,
  "..",
  "admet_ai_local",
  "charts",
  "admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png"
);

const OUT = path.join(__dirname, "PRST_N_FM_Meeting_2026-05-28_v3.pptx");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "KAERI AI-RI Lab";
pres.subject = "2026-05-28 meeting narrative v3";
pres.title = "Action Items 9건 — 수행 결과 및 의사결정 요청";
pres.company = "KAERI";
pres.lang = "ko-KR";

const C = {
  primary: "6D2E46",
  secondary: "A26769",
  accent: "028090",
  dark: "1F1B24",
  light: "FAF6F2",
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
const FONT_M = "Consolas";
const TOTAL = 26;
const warnings = [];

if (!fs.existsSync(IMG_ADMET_SCATTER)) {
  warnings.push("ADMET-AI 차트 이미지 없음: Slide 18 이미지 미삽입");
}

function addFooter(s, p, total = TOTAL) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.25, w: 13.3, h: 0.25, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("KAERI-AIRL-MOM-2026-004 (예정) · 2026-05-28 narrative v3", { x: 0.4, y: 7.25, w: 10.5, h: 0.25, fontSize: 9, color: C.light, fontFace: FONT_B, valign: "middle" });
  s.addText(`${p} / ${total}`, { x: 12.35, y: 7.25, w: 0.75, h: 0.25, fontSize: 9, color: C.light, fontFace: FONT_B, valign: "middle", align: "right" });
}

function addTitle(s, t, sub) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.15, h: 7.25, fill: { color: C.primary }, line: { type: "none" } });
  s.addText(t, { x: 0.5, y: 0.3, w: 12.4, h: 0.62, fontSize: 28, bold: true, color: C.dark, fontFace: FONT_H, margin: 0, breakLine: false });
  if (sub) s.addText(sub, { x: 0.5, y: 0.92, w: 12.4, h: 0.35, fontSize: 14, color: C.textMute, fontFace: FONT_B, margin: 0, italic: true });
}

function textBox(s, title, body, x, y, w, h, color = C.secondary, opts = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: opts.fill || C.light }, line: { color: opts.line || C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h, fill: { color }, line: { type: "none" } });
  if (title) s.addText(title, { x: x + 0.18, y: y + 0.12, w: w - 0.35, h: 0.28, fontSize: opts.titleSize || 12.5, bold: true, color, fontFace: FONT_H, margin: 0 });
  s.addText(body, { x: x + 0.18, y: y + (title ? 0.48 : 0.16), w: w - 0.35, h: h - (title ? 0.58 : 0.25), fontSize: opts.fontSize || 10.4, color: opts.color || C.text, fontFace: opts.fontFace || FONT_B, valign: "top", fit: "shrink", margin: 0.04, breakLine: false });
}

function pill(s, label, val, x, y, w, color) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.72, fill: { color }, line: { type: "none" } });
  s.addText(String(val), { x: x + 0.1, y: y + 0.07, w: 0.8, h: 0.55, fontSize: 26, bold: true, color: "FFFFFF", fontFace: FONT_H, align: "center", valign: "middle", margin: 0 });
  s.addText(label, { x: x + 0.95, y: y + 0.13, w: w - 1.1, h: 0.46, fontSize: 11.5, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle", margin: 0 });
}

function addTable(s, rows, x, y, w, colW, fontSize = 9.1, rowH = 0.36) {
  s.addTable(rows, {
    x, y, w, colW,
    fontSize,
    fontFace: FONT_B,
    border: { type: "solid", pt: 0.5, color: C.border },
    rowH,
    valign: "middle",
    margin: 0.05,
    fit: "shrink",
  });
}

function headerRow(cols, fill = C.dark) {
  return cols.map((c) => ({ text: c, options: { bold: true, fill: { color: fill }, color: "FFFFFF" } }));
}

function statusColor(status) {
  if (status.includes("충족") && !status.includes("부분")) return C.pos;
  if (status.includes("부분")) return C.warn;
  if (status.includes("삭제") || status.includes("N/A")) return C.textDim;
  return C.neg;
}

function aiSlide(page, id, name, originalReq, kpi, executed, deliverables, gap, status) {
  const s = pres.addSlide();
  addTitle(s, `${id} — ${name}`, "4월 회의 원문 요구 → 5월 27일 narrative v3 수행 결과");

  textBox(s, "회의 원본 요구", `목표\n${originalReq}\n\nKPI / 완료 기준\n${kpi}`, 0.5, 1.42, 6.0, 5.05, C.secondary, { fontSize: 9.9 });
  textBox(s, "수행 결과", `수행 내용\n${executed}\n\n산출물\n${deliverables}`, 6.8, 1.42, 6.0, 5.05, C.accent, { fontSize: 9.9, fontFace: deliverables.includes("`") ? FONT_B : FONT_B });

  const stColor = statusColor(status);
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.72, w: 12.3, h: 0.42, fill: { color: stColor }, line: { type: "none" } });
  s.addText(`상태: ${status} · 갭: ${gap}`, { x: 0.68, y: 6.79, w: 11.95, h: 0.25, fontSize: 11.2, bold: true, color: "FFFFFF", fontFace: FONT_B, valign: "middle", margin: 0 });
  addFooter(s, page);
}

function addSectionSlide(page, title, sub, leftTitle, leftText, rightTitle, rightText, footerText) {
  const s = pres.addSlide();
  addTitle(s, title, sub);
  textBox(s, leftTitle, leftText, 0.5, 1.45, 6.0, footerText ? 4.85 : 5.55, C.secondary);
  textBox(s, rightTitle, rightText, 6.8, 1.45, 6.0, footerText ? 4.85 : 5.55, C.accent);
  if (footerText) {
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.55, w: 12.3, h: 0.5, fill: { color: C.dark }, line: { type: "none" } });
    s.addText(footerText, { x: 0.7, y: 6.63, w: 11.9, h: 0.32, fontSize: 11.5, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", valign: "middle", margin: 0 });
  }
  addFooter(s, page);
}

// Slide 1
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.2, w: 13.3, h: 0.3, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("KAERI-AIRL-MOM-2026-004 (예정)", { x: 0.55, y: 1.2, w: 12.2, h: 0.35, fontSize: 14, color: C.secondary, bold: true, fontFace: FONT_B, charSpacing: 4, margin: 0 });
  s.addText("Action Items 9건", { x: 0.55, y: 1.85, w: 12.2, h: 0.76, fontSize: 48, color: "FFFFFF", bold: true, fontFace: FONT_H, margin: 0 });
  s.addText("수행 결과 및 의사결정 요청", { x: 0.55, y: 2.65, w: 12.2, h: 0.62, fontSize: 28, color: "FFFFFF", bold: true, fontFace: FONT_H, margin: 0 });
  s.addText("4월 회의 → 5월 28일 회의 narrative v3", { x: 0.55, y: 3.32, w: 12.2, h: 0.36, fontSize: 16, color: C.secondary, italic: true, fontFace: FONT_B, margin: 0 });

  textBox(s, "회의", "회의일 2026-05-28 (목)\nDeck 갱신일 2026-05-27\n작성: 김동주, KAERI AI-RI Lab", 0.6, 4.55, 5.85, 1.55, C.secondary, { fill: "FFFFFF", line: C.secondary, color: C.light, fontSize: 15 });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.85, y: 4.55, w: 5.85, h: 1.55, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("4월 신규 8건 중 6건 충족, 2건 부분 충족 — Layer 2/3 절대값은 미신뢰. wet-lab 병행 필수.", {
    x: 7.1, y: 4.78, w: 5.35, h: 1.06, fontSize: 19, bold: true, color: "FFFFFF", fontFace: FONT_H, fit: "shrink", valign: "middle", margin: 0.02,
  });
  addFooter(s, 1);
}

// Slide 2
{
  const s = pres.addSlide();
  addTitle(s, "프로젝트 현재 위치 + 7단계 선별 체계", "SST-14 기반 SSTR2 표적 후보를 Gate-2 실험으로 넘기는 계산 단계");
  textBox(s, "현재 위치", "SST-14 기반 SSTR2 표적 방사성의약품 후보를 계산 단계에서 선별하고, ¹⁷⁷Lu 표지와 Gate-2 실험으로 넘길 수 있는 3~4개 후보를 도출하는 것이 현재 파이프라인의 목적이다.\n\n5월 회의의 핵심은 \"어디까지 계산으로 닫혔는가\"와 \"어디부터 실측 또는 외부 도구가 필요한가\"를 구분하는 것이다.", 0.5, 1.45, 5.55, 4.8, C.secondary, { fontSize: 12.2 });
  const rows = [
    headerRow(["단계", "선별 축", "현재 역할"]),
    ["1", "Specificity", "Rosetta/FlexPepDock 및 selectivity 기반 1차 선별"],
    ["2", "Serum Stability", "ProtParam 및 대체 도구, 이후 MD 기반 stability 검토"],
    ["3", "Toxicity", "pepADMET 또는 대체 ADMET 모델"],
    ["4", "Lead", "WSS와 Pareto front 기반 최종 후보 도출"],
    ["5", "AA Modification", "radiolysis 민감 잔기 및 SS bond 안정성 중심 변형"],
    ["6", "RI-MD", "MM-GBSA, FEP/TI, 표지 후 구조 안정성"],
    ["7", "기타", "제형 안정성, RCY/RCP, 실험 패키지 조건"],
  ];
  addTable(s, rows, 6.4, 1.45, 6.4, [0.55, 1.75, 4.1], 9.3, 0.45);
  s.addText("\"7단계 다단계 선별 체계(Specificity → Serum Stability → Toxicity → Lead 확정 → AA Modification → RI-MD simulation → 기타 예측)\" — 회의록 §1", {
    x: 0.65, y: 6.45, w: 12.0, h: 0.34, fontSize: 11.2, italic: true, color: C.textMute, fontFace: FONT_B, align: "center", margin: 0,
  });
  addFooter(s, 2);
}

aiSlide(3, "A-01", "SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹",
  "\"SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 수행 (SSTR3 에러 해결 포함).\"\n\"블라인드 도킹은 전체 수용체 표면을 탐색하므로 연산 시간이 과도하다.\"",
  "binding_pocket_SSTR2.json 생성, SSTR1/3/4/5 정렬 RMSD ≤4 Å, selectivity_runner 인터페이스 반영.",
  "7XNA 기준 포켓 중심 (-5.595, -28.626, 52.210), 반경 13 Å, 박스 26.1 Å. PyMOL cealign 정렬 RMSD: SSTR1 3.125 Å, SSTR3 3.086 Å, SSTR4 3.019 Å, SSTR5 2.770 Å.",
  "PR #61 main merge\nbinding_pocket_SSTR2.json\nSSTR1/3/4/5 aligned PDB\nselectivity_runner.py\n관련 테스트 38건 통과",
  "TM-align 대신 cealign 사용. KPI RMSD는 충족.",
  "✓ 충족");

aiSlide(4, "A-02", "혈청 반감기 예측 도구 비교 조사",
  "\"혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가).\"\n\"[서호성 의견] 보다 정밀한 Serum Stability 혹은 인체 반감기 측정 프로그램을 찾아 사용할 필요가 있으며, 특히 D-Phe 등 변형된 아미노산을 분석할 수 있으면 더욱 바람직하다.\"",
  "5종 이상 도구 비교, 벤치마크 정확도 표, R²/MAE 정량 비교, 도입 우선순위 권고.",
  "ProtParam, HLP, PlifePred, PeptideRanker, PeptideStability, pepMSND, CAMSOL 등 7종 비교. Octreotide 테스트에서 D-AA 및 terminal modification을 반영하지 못하면 half-life가 4.83배 과대 추정될 수 있음을 확인.",
  "A-02 도구 비교 문서\npredict_halflife_pepmsnd.py wrapper\nENDPOINT_CONFIDENCE 혈청 반감기 항목 7개\nD-AA 미지원 경고",
  "D-AA half-life 예측 도구 확보 미충족. wet-lab serum stability 병행 필요.",
  "△ 부분 충족");

aiSlide(5, "A-03", "Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가",
  "\"Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가.\"\n\"(추가적인 학습에 대한 김동주 선생님의 의견!!)\"",
  "원 논문 endpoint별 정확도, SSTR2 환형 적용 한계, 자체 fine-tuning 가능성, 신뢰 endpoint 식별.",
  "\"Fab-ADMET\" 표기는 pepADMET으로 정정. Tan et al. 2026 JCIM peptide ADMET 플랫폼. toxicity endpoint는 AUC 0.949로 보고. D-AA·비천연 AA 공식 지원 미명시, DOTA 결합 후보는 적용 불가 또는 OOD 가능성 큼. REST API 자동 호출은 HTTP 403.",
  "A-03 조사 보고서\npepADMET 명칭 정정 기록\npepADMET 저자 문의 이메일 초안\nADMET 도구 신뢰도 등급 및 H-06 경고",
  "명칭 정정과 적용 가능성 평가는 충족. PRST 후보 ADMET 의사결정 모델은 미확보.",
  "△ 부분 충족");

aiSlide(6, "A-04", "Top-K 후보 선정 복합 스코어링 체계 설계",
  "\"Top-K 후보 선정 복합 스코어링 체계 설계 (ΔG + 반감기 + 셀렉티비티 + ADMET 통합).\"\n\"Hard cutoff 통과 후보에 대해 가중 합산 스코어(weighted sum) 또는 Pareto front 방식으로 순위 결정.\"",
  "composite_scorer.py, WSS + Pareto front, Tier S/A/B/FAIL, A-09 입력, pharmacology_guards 통합.",
  "Hard Cutoff 5개 정의: ΔG, Selectivity ≥100×, radiolysis-sensitive residue ≤3개, ADMET toxicity ≤0.3, Instability Index <40. WSS 가중치: ΔG 0.35, selectivity 0.25, half-life 0.20, ADMET 0.10, radiolysis 0.10.",
  "pipeline_local/scoring/composite_scorer.py\npipeline_local/scoring/radiolysis_scorer.py\nPR #62 main merge\n테스트 73건 통과",
  "실제 Tier 체계는 S/A/B/FAIL. commit 제목의 C와 다름.",
  "✓ 충족");

aiSlide(7, "A-05", "SST14 reference ΔG 기준선 확립",
  "\"SST14 레퍼런스 ΔG 기준선 확립 및 가변 임계값 적용 (n회 반복 Mean 값 기준).\"\n\"[서호성 의견] Docking simulation을 n회 반복 수행하여 Mean 값을 기준으로 하는 것이 좋다.\"",
  "n≥10 도킹, mean/std/95% CI, KPI σ<5, reference JSON, pharmacology_guards 등록.",
  "SST-14 원형을 SSTR2에 동일 프로토콜로 반복 도킹. FlexPepDock 평균 ΔG 553.857 REU, σ=4.024 REU. Boltz-2 비교 ΔG -95.024 REU. 단위와 스케일이 달라 직접 비교하지 않음.",
  "main commit 8e7e1cc\npharmacology_guards.py::LITERATURE_VALUES\ntool-specific reference ΔG\ngate_thresholds.yaml rosetta_ddg_max=498.4713",
  "SST-14:SSTR2 복합체 cryo-EM ground truth 부재. absolute pose validation 한계.",
  "✓ 충족");

aiSlide(8, "A-06", "디퓨전 모델 기반 도킹 가속화 PoC",
  "\"디퓨전 모델 기반 도킹 가속화 PoC 수행 (정확도 vs Rosetta 비교).\"\n\"RMSD 2.0Å 이내 재현율이 80% 이상이면 파이프라인 1차 필터로 도입을 검토한다.\"",
  "Diffusion 모델 적용, PyRosetta/Boltz 비교, 시간/정확도/SS bond 지원, 도입 권고.",
  "DiffPepDock 검토. SSTR2-SST14 실험 ground truth 부재로 내부 reference pose와 비교. SST-14 및 PRST 후보의 Cys3-Cys14 SS bond 제약을 안정적으로 유지하지 못함. 회의 KPI인 RMSD 2.0 Å 이내 재현율 80% 판단 기준 미충족.",
  "DiffPepDock 평가 보고\nHEURISTIC_FUNCTION_DISCLAIMERS NOT_RECOMMENDED 사유\nA-07 GPU VRAM 120 GB 이상 요구와 병목 연결",
  "속도 이점은 있으나 현 단계 도입은 NOT_RECOMMENDED.",
  "✓ 충족");

aiSlide(9, "A-07", "DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집",
  "\"DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집. 담당: 서호성/안기범.\"\n\"NVIDIA DGX H100(80GB×8) 또는 DGX B200 등 옵션의 견적을 최소 2개 벤더로부터 수집한다.\"",
  "VRAM 총량, NVLink, 전력/냉각, 납기, 유지보수 계약, 외부 벤더 2곳 이상 비교.",
  "비교 매트릭스와 점검 양식 작성. 비교 항목은 VRAM 총량, NVLink, 전력/냉각, 납기, 유지보수 계약, Desmond/FEP+/diffusion docking 연동 가능성으로 정리.",
  "GPU 견적 비교 매트릭스\n점검 양식\nSchrödinger job throughput 추가 필요 항목",
  "외부 벤더 견적 수집은 담당자 영역으로 남아 있음.",
  "△ 부분 충족");

aiSlide(10, "A-08", "서버 마이그레이션 [삭제]",
  "\"라이브러리 서버 마이그레이션 완료 및 검증. 상태: 삭제. 비고: 완료/불요.\"\n\"외부망 서버 배포 완료로 본 항목은 삭제 처리한다.\"",
  "회의 당일 삭제 항목과 정합. 별도 수행 없음.",
  "회의록 결정과 정합. 산출물 또는 후속 KPI 없음.",
  "N/A\n회의 당일 삭제 처리",
  "삭제 항목. 수행 실적으로 산입하지 않음.",
  "N/A 삭제");

aiSlide(11, "A-09", "최종 후보 3~4개 도출 및 합성 의뢰 준비",
  "\"최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행).\"\n\"Gate-1(계산) → Gate-2(표지/제조) 진행을 위한 핵심 마일스톤이다.\"",
  "최종 후보 3~4개, 합성 의뢰서, tier_s_candidates.csv, ADMET/half-life 한계 명시.",
  "A-04 scoring을 전체 후보 라이브러리에 적용. PRST-001~004 네 개로 정리. PRST-001: Tier S, AGCKNIIWKTITSC, WSS=1.000, ΔG=-105.5 REU, II=28.5. PRST-002~004는 Tier B. sequence identity 86~93%로 다양성 WARN.",
  "runs_local/final_candidates/synthesis_orders/PRST-001.md~PRST-004.md\ntier_s_candidates.csv\ntier_b_candidates.csv\nPR #63 main merge",
  "Gate-2 진입 결정은 회의 필요. ADMET/half-life 절대값 근거 아님.",
  "✓ 충족");

aiSlide(12, "A-10", "SSTR3 도킹 에러 원인 분석 및 해결",
  "\"SSTR3 도킹 에러 원인 분석 및 해결. 담당: AI팀. 기한: 5월 회의 전. 상태: 신규 A-01과 연동.\"\n\"SSTR3 PDB 구조의 전처리 상태를 점검한다.\"",
  "SSTR3 PDB 구조 점검, 누락/충돌/B-factor 확인, 필요 시 루프 재구축 및 최소화.",
  "SSTR3 PDB(8XIR) 다중 chain 처리 로직 문제 확인. offtarget_dock.py에 chain 선택 로직 추가. smoke test ddg=-92.09 정상 실행. SSTR1/SSTR4 공유 signature로 인한 subtype mapping 위험 확인 후 고유 signature만 사용하는 방식으로 수정.",
  "PR #60 main merge\npipeline_local/tests/test_offtarget_dock_cif_chain.py\npipeline_local/tests/test_offtarget_dock_boltz.py\n관련 테스트 48건 통과",
  "A-01 위치 지정 도킹과 연동해 해결.",
  "✓ 충족");

// Slide 13
{
  const s = pres.addSlide();
  addTitle(s, "9건 요약 매트릭스", "회의 KPI 기준: 신규 8건 중 6건 충족, 2건 부분 충족. A-08은 삭제 항목");
  const rows = [
    headerRow(["번호", "회의 요구", "수행 결과", "상태"]),
    ["A-01", "SSTR1/3/4/5 위치 지정 도킹 좌표 + 재도킹", "SSTR2 좌표 추출, cealign 정렬, RMSD 2.77~3.13 Å, 인터페이스 구현", { text: "충족", options: { color: C.pos, bold: true } }],
    ["A-02", "반감기 도구 5종 이상 비교 + 정확도 평가", "7종 비교, D-AA 지원 도구 0개, Octreotide 4.83× 과대 추정 확인", { text: "부분", options: { color: C.warn, bold: true } }],
    ["A-03", "Fab-ADMET 정확도 + 자체 학습 가능성", "Fab-ADMET=pepADMET 오기재 정정, D-AA/DOTA OOD 한계 확인", { text: "부분", options: { color: C.warn, bold: true } }],
    ["A-04", "ΔG+반감기+selectivity+ADMET 복합 스코어링", "Hard Cutoff, WSS, Pareto front, Tier S/A/B/FAIL 구현", { text: "충족", options: { color: C.pos, bold: true } }],
    ["A-05", "SST14 reference ΔG n회 평균", "FlexPepDock mean 553.857 REU, σ=4.024", { text: "충족", options: { color: C.pos, bold: true } }],
    ["A-06", "diffusion docking PoC", "DiffPepDock SS bond 처리 한계, NOT_RECOMMENDED", { text: "충족", options: { color: C.pos, bold: true } }],
    ["A-07", "GPU 서버 2벤더 견적", "비교 매트릭스 작성, 외부 견적 대기", { text: "부분", options: { color: C.warn, bold: true } }],
    ["A-08", "서버 마이그레이션", "회의 당일 삭제 항목과 정합", { text: "삭제", options: { color: C.textDim, bold: true } }],
    ["A-09", "최종 후보 3~4개 + 합성 의뢰", "PRST-001~004 및 의뢰서 4건 작성", { text: "충족", options: { color: C.pos, bold: true } }],
    ["A-10", "SSTR3 도킹 에러 해결", "chain 선택 로직 및 subtype signature 수정", { text: "충족", options: { color: C.pos, bold: true } }],
  ];
  addTable(s, rows, 0.5, 1.38, 12.3, [0.72, 3.65, 6.55, 1.38], 8.65, 0.4);
  pill(s, "충족\n(신규 8건 중 6)", 6, 0.5, 6.45, 3.0, C.pos);
  pill(s, "부분 충족", 2, 3.65, 6.45, 3.0, C.warn);
  pill(s, "미달", 0, 6.8, 6.45, 3.0, C.neg);
  pill(s, "삭제", 1, 9.95, 6.45, 2.85, C.textDim);
  addFooter(s, 13);
}

addSectionSlide(14, "문제 재정의", "serum stability/ADMET 병목은 도구 부재가 아니라 학습 범위 밖 화학 공간",
  "PRST 후보의 동시 특성",
  "• SST-14 유사 14 aa peptide\n• Cys3-Cys14 SS bond 기반 cyclic constraint\n• D-AA 또는 비천연 AA 치환 가능성\n• DOTA 등 chelator 결합 가능성\n• SSTR2 selectivity와 radiolysis stability를 동시에 만족해야 하는 다목적 조건",
  "결론",
  "일반 L-AA peptide 또는 small molecule ADMET 모델은 이 조합에 대해 절대값 보정을 제공하지 못한다.\n\n따라서 serum stability와 ADMET 문제는 단일 모델로 닫히지 않는다.",
  "Layer 2/3 출력은 합성 go/no-go의 절대 근거가 아니다.");

{
  const s = pres.addSlide();
  addTitle(s, "PR #85 3-Layer 구조", "main 반영은 모듈 존재를 의미한다. enrichment 호출은 다음 슬라이드에서 분리해 보고");
  const boxes = [
    ["Layer 1", "휴리스틱 계층\nProtParam, Instability Index, radiolysis-sensitive residue count, N-end rule 계열 값.\n장점: 해석 가능성과 속도.\n한계: D-AA, cyclic constraint, DOTA를 물리적으로 직접 다루지 못함.", C.secondary],
    ["Layer 2", "ML regression 계층\nhalf-life 연속값 예측. PEPlife2-GAT 재학습 검토.\n초기 R²=-0.028 / Spearman ρ=-0.119 / MAE=33.12 h.\n재학습 R²=0.022 / Spearman ρ=0.571 (실험 브랜치, seed 의존).", C.warn],
    ["Layer 3", "ML classification 계층\ntoxicity, binary ADMET flag, OOD guard.\nPRST 후보 ADMET=1.00은 D-AA·cyclic·DOTA 조합에 대해 외삽 가능성이 큼.\nrecommended_for_decision=False guard 필요.", C.accent],
  ];
  boxes.forEach((b, i) => textBox(s, b[0], b[1], 0.5 + i * 4.15, 1.6, 3.9, 4.65, b[2], { fontSize: 10.3 }));
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.48, w: 12.3, h: 0.48, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("모듈 main 반영 ≠ enrichment 호출. 상세는 다음 슬라이드.", { x: 0.7, y: 6.57, w: 11.9, h: 0.28, fontSize: 12, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 15);
}

addSectionSlide(16, "3-Layer는 타개책인가", "해결책이 아니라 의사결정 오류 억제 framework",
  "판단",
  "3-Layer Ensemble은 serum stability와 ADMET 문제의 해결책이 아니다.\n\n현재 한계를 수치와 상태 플래그로 노출하고, 단일 도구 출력이 합성 결정으로 직행하지 못하게 막는 framework이다.\n\n의미는 \"예측 정확도 확보\"보다 \"의사결정 오류 억제\"에 있다.",
  "Layer별 역할",
  "Layer 1: 빠른 제외 기준을 제공한다.\n\nLayer 2: 현재 실패를 계량화한다.\n\nLayer 3: OOD와 binary toxicity 경고를 부착한다.\n\nADMET/half-life 실측 없이 통과 판정을 받지 않는다.",
  null);

// Slide 17
{
  const s = pres.addSlide();
  addTitle(s, "⚠ 코드 실태와 narrative의 격차", "PR #85 main 반영과 표준 후보 enrichment 호출은 동치가 아니다");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.42, y: 1.28, w: 12.45, h: 3.05, fill: { color: "FFF7ED" }, line: { color: C.warn, width: 1 } });
  s.addText(
    "• enrich_candidates_from_wrappers는 run_routed_halflife / compute_layer1_halflife / predict_admet_layer3를 호출하지 않는다.\n"
    + "• run_routed_halflife는 Layer 2만 실구현이고, Layer 1·3 반감기 경로는 스텁 메시지와 경고만 반환한다.\n"
    + "• D-AA 표기 후보는 enrichment 진입 단계에서 스킵되어 UNAVAILABLE만 남는다. Layer 2 라우팅도 받지 않는다.\n"
    + "• recommended_for_decision은 predict_admet_ai_wrapper.py에서만 항상 False이며 Tier/Hard Cutoff와 자동 결합되어 있지 않다.\n"
    + "• PR #117(ADMET divergence guard)은 현재 브랜치 및 main 양쪽 모두에 포함되어 있지 않다.\n"
    + "• PR #112(pepMSND Layer 2 재학습)는 OPEN이며 main 머지 commit이 없다.\n"
    + "• PRST-001~004 합성 의뢰서에 Layer 1/2/3, ensemble_halflife_hours, ADMET-AI Layer 3 표기는 없다.",
    { x: 0.65, y: 1.45, w: 11.9, h: 2.65, fontSize: 10.05, color: C.text, fontFace: FONT_B, fit: "shrink", valign: "top", margin: 0.02 }
  );
  const rows = [
    headerRow(["항목", "PRST 의뢰서 표현", "동일 명칭 코드 산출", "정합 여부"], C.warn),
    ["반감기 수치 근거", "step08_stability.py::predict_half_life, HEURISTIC", "enrichment 선택 시 predict_halflife_pepmsnd; Layer 모듈은 비호출", { text: "부분 불일치", options: { color: C.warn, bold: true } }],
    ["독성 1.00", "pepADMET 로컬 재검증 + OOD 문구", "재훈련 GNN 출력 + 레지스트리 경고 정합", { text: "의미상 일치", options: { color: C.pos, bold: true } }],
    ["3-Layer 용어", "미사용", "모듈·테스트 존재", { text: "문서 간 갭", options: { color: C.warn, bold: true } }],
    ["recommended_for_decision", "없음", "ADMET-AI wrapper에만 False 고정", { text: "서로 무관 레이어", options: { color: C.neg, bold: true } }],
  ];
  addTable(s, rows, 0.5, 4.55, 12.3, [1.85, 3.25, 4.55, 2.65], 8.35, 0.43);
  s.addText("6월 회의까지 진행해야 할 항목은 \"어느 엔진이 canonical인가\"의 합의이다.", { x: 0.65, y: 6.72, w: 12.0, h: 0.28, fontSize: 11.2, bold: true, color: C.warn, fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 17);
}

// Slide 18
{
  const s = pres.addSlide();
  addTitle(s, "Layer 3 ADMET-AI 차트", "PR #111: ADMET=1.00은 절대 독성 판정이 아니라 OOD 외삽 가능성 경고와 함께 해석");
  if (fs.existsSync(IMG_ADMET_SCATTER)) {
    s.addImage({ path: IMG_ADMET_SCATTER, x: 0.55, y: 1.45, w: 7.2, h: 4.95 });
  } else {
    textBox(s, "이미지 없음", IMG_ADMET_SCATTER, 0.55, 1.45, 7.2, 4.95, C.neg);
  }
  textBox(s, "해석 기준", "• ADMET-AI wrapper는 recommended_for_decision=False를 항상 강제한다.\n• D-AA·cyclic·DOTA 조합은 학습 분포 밖(OOD) 외삽 가능성이 크다.\n• ADMET=1.00은 절대 독성 판정으로 해석하지 않는다.\n• Tier 결정 또는 Hard Cutoff 분기와 자동 결합되어 있지 않다.\n• 합성 의뢰서에는 H-06 disclaimer와 OOD 해석 문장으로 정책을 흡수했다.", 8.0, 1.45, 4.8, 4.95, C.accent, { fontSize: 11.2 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 6.58, w: 12.25, h: 0.38, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("Layer 3의 현재 역할은 판정이 아니라 외삽 위험을 표시하는 guard이다.", { x: 0.75, y: 6.65, w: 11.85, h: 0.22, fontSize: 11.2, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 18);
}

{
  const s = pres.addSlide();
  addTitle(s, "의사결정 루프 — 의도 vs 현실", "§5.5 + §5.7: 자동화된 다중 조건은 아직 닫히지 않았다");
  textBox(s, "의도된 루프", "1. Hard Cutoff와 WSS/Pareto로 후보 축소\n2. Layer 1에서 즉시 산출 가능한 지표 부착\n3. Layer 2 regression이 유효하지 않으면 수치로 남김\n4. Layer 3 classification OOD이면 risk flag 전환\n5. 합성 의뢰서에 Ki, serum stability, ADMET, hemolysis, cytotoxicity 실측 항목 포함\n6. 실측값으로 다음 후보 생성과 scoring weight 보정", 0.5, 1.45, 6.0, 4.6, C.secondary, { fontSize: 10.3 });
  textBox(s, "현실", "현재 1·5·6은 작동한다.\n\n2·3·4는 모듈은 존재하지만 표준 후보 enrichment 경로와 분리되어 있다.\n\n사람이 H-06 disclaimer 문장과 OOD 해석으로 같은 기능을 수동 수행하고 있다.\n\nPRST-001은 Tier S로 유지. PRST-002~004는 Tier B이며 실측 패키지 없이 백업 lead로 승격하지 않는다.", 6.8, 1.45, 6.0, 4.6, C.accent, { fontSize: 10.8 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.25, w: 12.3, h: 0.72, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("파급효과: ΔG 중심에서 다중 조건 중심으로 이동 · OOD 후보도 실측 패키지로 넘기는 경로 · canonical 엔진 합의 시급", { x: 0.7, y: 6.39, w: 11.9, h: 0.38, fontSize: 11.2, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 19);
}

addSectionSlide(20, "Schrödinger 검토 전제 + 현재 도구 한계", "현재는 구매 결정이 아니라 6월까지 검토 진행 여부의 문제",
  "검토 전제",
  "• KAERI가 현재 Schrödinger 라이센스를 보유하지 않는 것으로 확인.\n• Schrödinger Korea 영업 연락과 라이센스 조건 확인은 아직 진행되지 않음.\n• 아래 내용은 실제 적용 결과가 아니라 일반 문헌 벤치마크와 Schrödinger 공식 자료 기반 예상.\n• 비용, 모듈 범위, 서버 연동, 첫 산출물 형식은 별도 정량화 필요.",
  "현재 자체 도구 한계",
  "1. PRST 후보 ADMET=1.00은 Layer 3 OOD 외삽 가능성이 큼.\n2. Layer 2 half-life regression은 R²=-0.028로 의사결정용이 아님.\n3. Layer 1은 시간 단위 half-life 합의값을 제공하지 못함.\n4. DiffPepDock은 SS bond 처리 한계로 NOT_RECOMMENDED.\n5. OpenMM/OpenFE/FlexPepDock/Boltz-2 조합은 cross-tool calibration 필요.",
  null);

{
  const s = pres.addSlide();
  addTitle(s, "Schrödinger 모듈별 예상 효과", "일반 벤치마크/공식 자료 기반 예상. 우리 시스템 적용 결과 아님");
  const rows = [
    headerRow(["모듈", "일반 벤치마크/공식 자료 기반", "SST-14/SSTR2 적용 시 기대", "검증 필요 사항"]),
    ["Glide SP/XP", "peptide protocol에서 RMSD ≤2 Å 성공률 58%, FlexPepDock 63% 근접 보고", "cyclic SST-14 계열 pose generation 비교 축", "SS bond와 DOTA 처리"],
    ["FEP+", "pairwise RMSE 약 1.25 kcal/mol, edgewise RMSE 약 1.17 kcal/mol", "A-05 reference와 modification 후보 ΔΔG 우선순위 보조", "pose, parameterization, sampling"],
    ["Desmond", "GPU 기반 MD. ns/day는 system size와 GPU 의존", "SS bond, DOTA 전후, RI 표지 후 stability MD", "GPU throughput, trajectory 품질"],
    ["Prime MM-GBSA", "Glide pose rescoring과 relative binding free energy estimate", "PRST-001~004 재랭킹 및 후보 압축 보조", "절대 affinity로 쓰지 않음"],
    ["WaterMap", "pocket water 위치/에너지 및 high-energy water 분석", "subtype pocket hydration 차이를 selectivity 해석에 연결", "직접 ADMET 해결 아님"],
    ["BioLuminate", "biopolymer modeling, peptide/protein engineering workflow", "cyclic peptide, D-AA, DOTA 세팅 전처리 축", "parameterization 가능성"],
  ];
  addTable(s, rows, 0.45, 1.38, 12.4, [1.4, 3.55, 4.0, 3.45], 7.8, 0.54);
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 6.55, w: 12.3, h: 0.42, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("벤치마크 출처는 부록 참조. 우리 시스템 적용 결과 아님.", { x: 0.7, y: 6.62, w: 11.9, h: 0.25, fontSize: 11.2, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 21);
}

{
  const s = pres.addSlide();
  addTitle(s, "6월까지 가능한 산출물 + GPU 연계 + 대안", "도입 검토 승인 시에도 6월 산출물은 sanity 수준으로 제한");
  textBox(s, "6월까지 단계", "1. 라이센스 조건 확인: 학술/비상업/기관 과제 범위, 모듈 포함 여부.\n2. 설치 및 환경 셋업: Maestro, Glide, Prime, Desmond, FEP+, BioLuminate, WaterMap 중 대상 확인.\n3. GPU/CPU 연동 확인: Desmond/FEP+ scheduler, A-07 GPU 견적 연동.\n4. 입력 구조 준비: SSTR2, PRST-001, SST-14 reference, SS bond, DOTA 여부.\n5. 첫 산출물: docking pose, Prime MM-GBSA rescoring, 짧은 Desmond sanity MD.", 0.5, 1.45, 5.75, 4.95, C.secondary, { fontSize: 9.7 });
  const rows = [
    headerRow(["항목", "Schrödinger 도입", "자체 ML/오픈소스 경로"]),
    ["비용", "라이센스 비용 및 모듈별 견적 필요", "직접 라이센스 비용은 낮으나 인력 시간이 큼"],
    ["일정", "설치 후 sanity output은 빠를 수 있으나 계약 리드타임 존재", "즉시 착수 가능하나 안정화와 검증 시간이 길다"],
    ["정확도", "FEP+ 등 벤치마크 존재, system validation 필요", "현재 Layer 2 R²=-0.028로 출발점 낮음"],
    ["인력", "상용 workflow 학습 필요", "모델 학습, 데이터 큐레이션, force field 세팅 역량 필요"],
    ["재현성", "Maestro project/job 중심 관리", "코드 기반 재현성은 높일 수 있으나 운영 부담 큼"],
    ["D-AA/DOTA", "parameterization 확인 필요", "직접 parameterization 및 검증 필요"],
  ];
  addTable(s, rows, 6.55, 1.45, 6.25, [0.9, 2.55, 2.8], 7.55, 0.58);
  s.addText("A-07 견적 비교에는 Desmond GPU support, FEP+ 병렬화, NVLink 필요성, 라이센스 token과 GPU 수 병목을 추가한다.", { x: 0.65, y: 6.72, w: 12.0, h: 0.26, fontSize: 10.8, bold: true, color: C.textMute, fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 22);
}

{
  const s = pres.addSlide();
  addTitle(s, "5월 28일 회의 의사결정", "누가 어느 결정을 내려야 하는지 한 번에 확인");
  const rows = [
    headerRow(["항목", "결정 주체", "결정 내용"]),
    ["§7.1 PRST-001~004 합성 진행 범위", "서호성 박사 + RI팀", "네 후보 전체를 보낼지, PRST-001 우선으로 줄일지. 실험 패키지 포함 필요."],
    ["§7.2 pepADMET 라이센스 및 저자 문의", "KAERI 행정·법무 + AI팀", "GPL-3.0 / CC BY-NC-SA 4.0 조건 법무 검토, half-life endpoint weight 또는 training data 문의."],
    ["§7.3 A-07 GPU 견적", "서호성 박사 + 안기범 박사", "DGX H100, DGX B200 또는 기존 외부망 서버 확장 여부 비교."],
    ["§7.4 Schrödinger 도입 검토", "회의 참석 전원", "6월까지 검토를 진행할지. 구매 결정은 6월 정량화 후 판단."],
    ["§7.5 6월 회의 기준 산출물", "본 발표 후 회의 합의", "산출물 범위를 제한하고 선행조건을 합의."],
  ];
  addTable(s, rows, 0.55, 1.55, 12.2, [3.05, 2.65, 6.5], 9.4, 0.72);
  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 6.35, w: 12.2, h: 0.55, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("PRST-001은 Tier S이나 ADMET/half-life 계산값은 절대 근거가 아니다.", { x: 0.75, y: 6.47, w: 11.8, h: 0.28, fontSize: 12, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 23);
}

{
  const s = pres.addSlide();
  addTitle(s, "6월 회의 기준 산출물", "§7.1 합성 발주 결정이 실측 항목의 선행 조건");
  textBox(s, "선행 조건", "§7.1 PRST-001~004 합성 발주 결정\n\n→ 합성 진행 상태가 있어야 실측 항목 4~6이 의미를 갖는다.", 0.65, 1.7, 4.2, 3.0, C.secondary, { fontSize: 15 });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 5.15, y: 2.62, w: 1.1, h: 0.55, fill: { color: C.accent }, line: { type: "none" } });
  textBox(s, "6월 산출물 체크리스트", "□ PRST-001~004 합성 진행 상태 또는 발주 결정 결과\n□ pepADMET 법무/저자 문의 진행 상태\n□ Layer 2 half-life 개선 여부 또는 실패 원인\n□ Schrödinger 도입 검토 결과\n□ A-07 GPU 견적 비교표\n□ 실측 데이터가 확보되면 계산값과의 불일치 분석", 6.55, 1.45, 5.9, 4.7, C.accent, { fontSize: 12.2 });
  s.addText("6월 회의부터는 \"예측값 보고\"가 아니라 \"예측값과 실측값의 불일치 보고\"가 중요해진다.", { x: 0.65, y: 6.62, w: 12.0, h: 0.28, fontSize: 11.8, bold: true, color: C.dark, fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 24);
}

{
  const s = pres.addSlide();
  addTitle(s, "발표 종료", "narrative v3 §8");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.55, w: 11.75, h: 4.7, fill: { color: C.light }, line: { color: C.border, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.55, w: 0.1, h: 4.7, fill: { color: C.primary }, line: { type: "none" } });
  s.addText("4월 회의에서 받은 신규 Action Item 8건 중 6건은 충족했고, A-02/A-03은 D-AA·cyclic·DOTA 조합의 도구 부재로 부분 충족에 머물렀다.\n최종 후보 PRST-001~004는 도출되었고 합성 의뢰서도 작성되었다.\n다만 이 후보들은 ADMET과 serum stability 계산값만으로 통과 판정을 받을 수 없다.\nPR #85의 3-Layer Ensemble 모듈은 이 한계를 해결하지 않는다.\n대신 한계를 수치와 경고 플래그로 노출하고, 단일 도구 출력의 과신을 막고, wet-lab 실측의 필요성을 명시하는 framework이다.\n현재 표준 enrichment 경로가 이 framework를 호출하지 않는 상태이므로, 6월 회의까지 enrichment 정합 작업이 함께 진행되어야 narrative와 코드 사이의 격차가 닫힌다.\nSchrödinger 도입 검토는 이 한계 중 docking, rescoring, MD, FEP, hydration analysis를 상용 workflow로 줄일 수 있는지 확인하는 선택지이다.\n현재는 라이센스와 비용이 확인되지 않았으므로 결정 사항이 아니라 검토 사항이다.\n5월 28일 회의에서 필요한 결정은 합성 범위, 실측 패키지, pepADMET 법무/저자 문의, GPU 견적 진행, Schrödinger 도입 검토 승인이다.", {
    x: 1.1, y: 1.82, w: 11.15, h: 3.95, fontSize: 13.1, color: C.text, fontFace: FONT_B, fit: "shrink", valign: "mid", margin: 0.05, breakLine: false,
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 6.45, w: 11.75, h: 0.42, fill: { color: C.dark }, line: { type: "none" } });
  s.addText("PR #85 모듈은 해결책이 아니라 한계 노출 framework. enrichment 정합 작업이 6월 회의까지 진행되어야 한다.", { x: 1.0, y: 6.52, w: 11.35, h: 0.25, fontSize: 11.3, bold: true, color: "FFFFFF", fontFace: FONT_B, align: "center", margin: 0 });
  addFooter(s, 25);
}

{
  const s = pres.addSlide();
  addTitle(s, "Schrödinger 벤치마크 참고", "부록 C: SST-14/SSTR2 실측값이 아니라 일반 문헌 및 공식 자료 기반 참고값");
  const rows = [
    headerRow(["항목", "참고"]),
    ["Glide peptide docking", "Tubert-Brohman et al., 2013 JCIM: enhanced peptide protocol에서 top-10 pose 기준 RMSD ≤2 Å 성공률 58%, FlexPepDock 63%와 비교"],
    ["FEP+", "large-scale FEP+ benchmark: pairwise RMSE 1.25 kcal/mol, edgewise RMSE 1.17 kcal/mol; Schrödinger 공식 자료는 ~1 kcal/mol 수준 제시"],
    ["Desmond", "Schrödinger 공식 GPU performance table은 GPU별 ns/day 성능을 제시하나 system size 의존성이 큼"],
    ["Prime MM-GBSA", "Glide pose 후처리 및 relative free energy estimate에 사용. docking score 단독의 affinity 한계를 보완하나 절대값 모델은 아님"],
    ["WaterMap", "binding pocket water location/energetics 및 high-energy displaceable water 분석"],
    ["BioLuminate", "biopolymer/peptide modeling workflow. D-AA·DOTA 처리는 실제 parameterization 검토 필요"],
  ];
  addTable(s, rows, 0.55, 1.45, 12.2, [2.25, 9.95], 8.6, 0.62);
  s.addText("참고 URL: Schrödinger FEP+, WaterMap, Desmond GPU performance table, Glide docking white paper, FEP+ benchmark, Glide peptide docking paper", {
    x: 0.65, y: 6.55, w: 12.0, h: 0.35, fontSize: 8.4, color: C.textMute, fontFace: FONT_M, fit: "shrink", align: "center", margin: 0,
  });
  addFooter(s, 26);
}

async function main() {
  await pres.writeFile({ fileName: OUT });
  const size = fs.statSync(OUT).size;
  const sizeMb = (size / 1024 / 1024).toFixed(2);
  console.log(`총 슬라이드 수: ${TOTAL}`);
  console.log("핵심 차별점: 이전 21장 deck 대비 narrative v3 전체 흐름을 26장으로 확장하고, A-03 부분 충족·§5.4 코드 격차·6월 canonical 엔진 합의를 분리 표기");
  console.log(`파일 경로 + 크기: ${OUT} (${sizeMb} MB)`);
  console.log(`빌드 시 발생한 경고: ${warnings.length ? warnings.join("; ") : "없음"}`);
  console.log("회의 전 확인 1가지: §7.1 PRST-001~004 합성 범위를 전체 4건으로 둘지 PRST-001 우선으로 줄일지 결정 필요");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
