# 6월 회의 준비 자료 — meet_preparation/
**작성일**: 2026-06-01 | **회의록 출처**: KAERI-AIRL-MOM-2026-003 (2026-04-06 제3차 월간회의)
**상태**: 초안 / 현재 상태 공유 (최종 성과 발표 아님)

---

## 📂 디렉토리 구조

```
docs/meet_preparation/
├── README.md                                       ← 본 파일 (인덱스)
├── daily_system_inspection_report_20260601.md     ← 종합 보고서 (Exec→분석→반영→종합의견)
│
├── action_items/                                   ← Action Items 5블록 분석
│   ├── 00_master_table.md                          ← P0 종합 비교표 (9건 + 매핑)
│   ├── A-01_SSTR_site_directed_docking.md         ← ✅ PR#61
│   ├── A-02_serum_halflife_tools.md               ← 🟡 D-AA HIGH-BLOCKER (§6 L-AA + §7 D-AA 보강)
│   ├── A-03_fab_admet_validation.md               ← 🟡 HTTP 403, Layer 3 STUB
│   ├── A-04_topk_composite_scoring.md             ← ✅ PR#62 (Tier S/A/B)
│   ├── A-05_sst14_reference_dG.md                 ← ✅ main direct
│   ├── A-06_diffusion_docking_PoC.md              ← 🟡 본격 PoC 미수행
│   ├── A-07_GPU_DGX_quote.md                       ← 🟡 외부 견적 대기
│   ├── A-09_final_candidates.md                    ← ✅ PR#63 (PRST-001~004)
│   └── A-10_SSTR3_docking_fix.md                   ← ✅ PR#60
│
├── reflection_plan/
│   └── 00_master_plan.md                           ← 21건 (committed 10 / proposed 11)
│
├── references/                                     ← 19 검증 통과 / 4 제외
│   ├── references.md                               ← 통합 인용 목록
│   ├── papers/README.md                            ← 논문 13편 평가
│   ├── libraries/README.md                         ← 라이브러리 매트릭스
│   ├── repos/README.md                             ← GitHub repo 신뢰도
│   └── benchmarks/README.md                        ← 도구 비교 6개 표
│
├── expert_opinions/                                ← /team 전문가 4명 견해
│   ├── pharma_review.md                            ← A-02·A-03·A-04·A-09
│   ├── biology_review.md                           ← A-01·A-05·A-10
│   ├── chemistry_review.md                         ← Modification·DOTA·Quencher
│   └── math_review.md                              ← Pareto·MM-GBSA·통계 설계
│
├── inspect_evidence/                               ← 시스템 점검 5종 (에이전트 산출)
│   ├── backend.md
│   ├── frontend.md
│   ├── silo_a.md
│   ├── silo_b_docking.md
│   └── dual_silo_actions.md
│
├── assets/
│   └── design_system.md                            ← §7-0 디자인 토큰 (PPT 공유)
│
└── pptx/
    ├── build_pptx.js                               ← 빌드 스크립트
    ├── main.pptx                                   ← 메인 발표 (18 슬라이드)
    └── appendix.pptx                               ← 부록 발표 (15 슬라이드)
```

---

## 📋 빠른 시작 가이드

### 1. 회의 발표용 보기
- **메인 PPTX**: `pptx/main.pptx` — 18 슬라이드 (제목·시스템·Silo·Action Items·반영계획·종합의견·결론)
- **부록 PPTX**: `pptx/appendix.pptx` — 15 슬라이드 (API·화면·캡처·5블록 카드·전문가 견해·References)

### 2. 사전 검토용 읽기
- **종합 보고서**: `daily_system_inspection_report_20260601.md` (12장 + 부록 참조)
- **Action Items P0 종합표**: `action_items/00_master_table.md`
- **반영 계획**: `reflection_plan/00_master_plan.md`

### 3. 토론용 깊이 자료
- **각 Action Item 5블록**: `action_items/A-XX_*.md` (9개)
- **전문가 4명 견해**: `expert_opinions/*.md`
- **References (검증된 출처)**: `references/references.md`

---

## 🎯 금일 보고 핵심 메시지 (5줄)

1. Action Items 9건 중 **6건 PR 머지 완료, 3건 진행 중** + **본 점검 신규 발견 3건** (K-1/K-2 결함·Silo C 격차·Dual 종단 0건)
2. **🚨 Biology 발견**: 7XNA(octreotide 8-mer) ≠ SST-14(14-mer) ring span 근본 다름 + Boltz 도킹 3종 모두 포켓 외부 → ΔG 기준선 재검증 필요
3. **🚨 Math 발견**: Pareto front 비활성(n=4 < MIN_CANDIDATES=50) — Tier S는 WSS 단일 기준. K-1/K-2 결함 시 다목적 ≡ 단목적
4. **A-02 D-AA HIGH-BLOCKER + Layer 3 STUB**으로 in silico 단독 의사결정 불가 — wet-lab Ki·Stability assay 병행 필수
5. **6월 회의 3대 결정**: ① PR #117 머지 (D-AA enrichment) ② Silo C 정책 (구현 vs A:0.5/B:0.5) ③ wet-lab 시점·protocol

---

## 📌 6월 회의 직전 D-7 체크리스트

- [ ] R-01 MCP filesystem 경로 수정 (5분, 본 보고 발견)
- [ ] R-02 BE silo_a 라우터 404 정정
- [ ] R-03 FE smoke 'More' 테스트 갱신
- [ ] R-04 K-1/K-2 selectivity 결함 정정 (P0)
- [ ] R-08 PRST ranking 재검증 (K-1/K-2 정정 후)
- [ ] R-09 DiffDock PoC 1회 실행 (paired Wilcoxon + n≥31)
- [ ] R-10 GPU 견적서 2건 수령
- [ ] R-12 벤치마크 R²/Spearman 측정
- [ ] R-19 Schrödinger 도입 검토 자료
- [ ] R-13 Silo A 이중 구현 안건 정리
- [ ] R-14 Silo C 정책 안건 정리

---

## 🔗 외부 참조

- **회의록 원본**: `../meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf` (9쪽)
- **5/26 1차 작성**: `../meet_log/2026-04-06_action_items/` (PR 머지 상태 추적)
- **이전 점검 보고서**: `_workspace/release/daily_system_inspection_report_20260601.md`
- **5/27 audit (D-1)**: `_workspace/release/eod-2026-05-27-orchestrator-d1-system-audit.md`

---

## ⚙️ PPTX 재생성 방법

```bash
cd docs/meet_preparation/pptx
NODE_PATH=/home/dongjukim/.npm-global/lib/node_modules node build_pptx.js
```

디자인 토큰 변경 시 `assets/design_system.md` 와 `build_pptx.js` 의 `const C = {...}` 동기화.

---

*orchestrator 세션 · 2026-06-01 · 초안 / 현재 상태 공유 · 최종 성과 발표 아님*
