# 5/27 중간 점검 deck — V1/V2/V3 비교 보고서

> **빌드일**: 2026-05-26 09:00 KST  
> **목적**: 5/27 (D-1) 중간 점검 회의용 PPTX 3 버전 — 사용자 비교 선택  
> **PR #115 (5/28 deck) 영향**: **없음** — 파일명/디렉토리 분리 (`_workspace/pptx/PRST_N_FM_MidCheckup_2026-05-27_V*.pptx`)

---

## 산출물 요약

| 버전 | 디자인 | 슬라이드 | 파일 크기 | 발표 시간 | 컨셉 |
|---|---|---|---|---|---|
| **V1** | Berry & Cream | 15 | 844 KB | ~35분 | Conservative / PR #115 톤 일관성 |
| **V2** | Charcoal Minimal | 12 | 710 KB | ~25분 | Visual / 큰 stat callouts / 임팩트 |
| **V3** | Ocean Gradient | 14 | 788 KB | ~35분 | Data-First / 그래프 풀-블리드 |

### 경로

```
_workspace/pptx/PRST_N_FM_MidCheckup_2026-05-27_V1_BerryCream.pptx
_workspace/pptx/PRST_N_FM_MidCheckup_2026-05-27_V2_CharcoalMinimal.pptx
_workspace/pptx/PRST_N_FM_MidCheckup_2026-05-27_V3_OceanGradient.pptx
```

빌더: `_workspace/pptx-2026-05-27/builders/build_midcheckup_v{1,2,3}_*.js`  
그래프 (8 PNG): `_workspace/pptx-2026-05-27/graphs/G{1,2,3,4,5,6,8,11}_*.png`  
Mermaid 도식 (4 .mmd): `_workspace/pptx-2026-05-27/graphs/G{7,9,10,12}_*.mmd`

---

## 슬라이드 구성 비교

| # | V1 Berry & Cream (15) | V2 Charcoal Minimal (12) | V3 Ocean Gradient (14) |
|---|---|---|---|
| 1 | 타이틀 + Berry 배경 | MID-CHECK 대형 + 4 stat | 타이틀 + Ocean gradient + 4 stat |
| 2 | 9 Action Items + 우측 리스트 | 한 장 요약 4 callout | Action Items 진척 + DATA 박스 |
| 3 | 본 세션 17 PR Timeline | Action Items + 컴팩트 리스트 | PR Timeline (full-bleed) |
| 4 | FE Mol* 4-fix + 2-level selector | 본 세션 17 PR Timeline | PR 누적 비교 (G11) |
| 5 | FlexPepDock Pool + 사항 | 진행 완료 — 6 분야 카드 | pepADMET 재훈련 + DATA |
| 6 | pepADMET 재훈련 OOD | Layer 2/3 재학습 (병행) | pepMSND ρ=0.571 (data emphasis) |
| 7 | pepMSND 재학습 ρ=0.571 | Worker Pool + LLM | FlexPepDock Worker Pool (full) |
| 8 | LLM 인프라 비교 | 결함 매트릭스 (full) | LLM 인프라 (full) |
| 9 | 시스템 아키텍처 (직접 그림) | Fix 결과 (K-1 + PRST) | 시스템 아키텍처 4 layer |
| 10 | 결함 매트릭스 G8 | RI 팀 요청 4 카드 | 결함 매트릭스 (full) |
| 11 | Fix 결과 (K-1 + PRST) | 정직 보고 + H-06 가드 | Fix 결과 (K-1 + PRST) |
| 12 | PR 누적 카운트 G11 | Q&A + 다음 단계 | RI 팀 요청 데이터뷰 |
| 13 | RI 팀 요청 (4 컬럼) | — | H-06 honest reporting (2x3) |
| 14 | 정직 보고 — H-06 가드 | — | Q&A + 6 next steps |
| 15 | 마무리 + stats + 다음 단계 | — | — |

---

## 차별화 포인트

### V1 — Berry & Cream (Conservative, 15 slides)

**선택 기준**: 5/28 deck (PR #115)과 같은 톤 유지가 필요할 때

**장점**:
- PR #115 색상 (Berry #6D2E46 + Cream #ECE2D0) 일치 → 회의 자료 일관성
- 가장 상세 (15 슬라이드) — 모든 사안 균등 다룸
- 시스템 아키텍처 박스+화살표 직접 그림 (G7 대체)
- RI 팀 요청 4 컬럼 시각적

**단점**:
- 가장 길다 (~35분) — 시간 압박 가능
- PR #115와 비슷해서 차별성 약함

### V2 — Charcoal Minimal (Visual, 12 slides)

**선택 기준**: 짧고 임팩트 있는 발표가 필요할 때 (D-1 중간 점검 컨셉에 적합)

**장점**:
- 가장 짧음 (~25분) — Q&A 시간 충분
- 큰 stat callouts (17 / 5/9 / 6 / 2 — 40~80pt) → 시각적 임팩트
- Charcoal #36454F + Accent Orange #FF6B35 → PR #115와 완전 차별화
- "MID-CHECK" 대문자 모노크롬 디자인 → 모던

**단점**:
- 일부 사안 압축 (Layer 2/3 같은 슬라이드)
- 색상이 너무 강해 진지함 부족하다는 인상 가능

### V3 — Ocean Gradient (Data-First, 14 slides)

**선택 기준**: 그래프 / 데이터 중심 발표 — 청자가 수치 검증 원할 때

**장점**:
- 그래프 풀-블리드 + 우측 DATA 박스 → 데이터 검증 가능
- Deep Blue #065A82 → 학술/검증 컨셉 잘 맞음
- 큰 수치 emphasis (0.571 64pt, 4 stats 50pt)
- Q&A 슬라이드에 6 next steps 카드 시각화

**단점**:
- 그래프 의존 → 그래프가 부정확하면 임팩트 손상
- Cambria 폰트가 일부 환경에서 fallback 가능

---

## 데이터 일관성 (3 버전 공통)

| 항목 | 값 | 출처 |
|---|---|---|
| 본 세션 PR | 17건 | EOD #114 + 본 세션 5/26 신규 3건 |
| Action Items 완료 | 5/9 (55.6%) | docs/meet_log/2026-04-06_action_items/00_MASTER_INDEX.md |
| pepMSND ρ | 0.571 | PR #112 commit 299b100 |
| pepADMET PRST | 0.402 (×4) 균일 | PR #113 commit f72c48e |
| Tests PASS (본 세션 신규) | 60/60 | K-1 (9) + PRST divergence (51) |
| 결함 노출 | 6건 | G8 매트릭스 (K-1/K-2/PRST/A-03/A-06/V-07) |
| 시스템 재가동 | uvicorn 8787 + worker pool 4 | 5/26 09:05 KST |

---

## 알려진 한계 (3 버전 공통)

1. **UI 캡쳐 10건 (C1-C10) 미생성** — vite 가동 중이나 브라우저 자동 캡쳐 도구 미구비. PPTX엔 placeholder 텍스트만.
2. **Mermaid PNG 미생성** — `mmdc` puppeteer libglib 부재로 실패. G7/G9/G10/G12는 PptxGenJS shapes로 직접 그림 (V1 슬라이드 9, V3 슬라이드 9).
3. **soffice 미설치** — 시각 QA(자동 PDF→이미지 변환) 불가. 사용자가 PowerPoint/Google Slides로 직접 확인 필요.
4. **PR #112 conflict** — 다른 세션 영역, 본 세션 rebase 보류 (해당 세션에 위임).
5. **K-2 selectivity 0%** — 다른 세션 영역. 결함 매트릭스에 정직 노출만.

---

## 사용자 결정 필요

| 항목 | 옵션 |
|---|---|
| **버전 선택** | V1 (안전) / V2 (임팩트) / V3 (데이터) / 또는 3개 중 슬라이드 mix |
| **UI 캡쳐 10건** | (A) 사용자 직접 캡쳐 (vite 5173) / (B) cursor-agent dispatch / (C) placeholder 유지 |
| **PR 푸시** | K-1 + PRST divergence fix 2개 branch를 PR로 만들지 여부 |
| **5/28 deck 통합** | V1/V2/V3 중 하나를 PR #115 deck 보강으로 통합 vs 별도 deck 유지 |

---

## 다음 단계 (사용자 결정 후)

1. 선택 버전 시각 검토 (PowerPoint/Google Slides)
2. UI 캡쳐 10건 보강 (시간 허용 시)
3. 슬라이드 미세 조정 (텍스트 overflow, alignment)
4. fix branch 푸시 → PR 2건 생성 (K-1, PRST divergence)
5. 5/27 회의 dry-run 30분 시뮬레이션
