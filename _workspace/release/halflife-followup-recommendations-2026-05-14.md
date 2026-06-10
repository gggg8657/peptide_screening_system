# Half-Life 후속 권고 — 2026-05-14

> EOD 직전 검토. 기존 보고서 4건 (`META_stability_halflife_integrated.md`, `halflife_methodology.md`, `cand_stability_analysis.md`, `half-life-tool-evaluation-2026-05-14.md`)에 대한 *추가 방법* 권고.

---

## 1. 현 상태 요약

### 기 검토·합의됨
- **SST-14 분해 메커니즘** (NEP F6-F7/T10-F11 + Trypsin K4-N5/K9-T10 + Chymotrypsin F6,F7,W8,F11)
- **Octreotide 안정화 원리** (D-Trp8 단독 30× 효과)
- **4-도메인 합의 후보**: 🥇 `Ac-AGCKNDFWKT[Cha]TSC-NH2` / 🥈 `Ac-AICKNFFWKTF[dT]SC-NH2` (var12) / 🥉 ILCKK 변형
- **In-silico 휴리스틱** (`step08_stability.predict_half_life` + `stability_predictor.hl_score_heuristic`) HEURISTIC 등급
- **PlifePred 도구 평가**: natural subset R=0.743 / natural+modified R=0.692, 미통합

### 통합 미완료
- PlifePred / PlifePred2 wrapper 미구현 (현재 in-silico는 heuristic-only)
- in-vitro serum t½ 실측 (LC-MS/MS) 미진행
- in-vitro Ki binding assay (cand03_binding_assay_design.md) 발주 미진행

---

## 2. 추가 방법 권고 (우선순위 순)

### 권고 1 — PlifePred 통합 (in-silico 정확도 ↑) **[HIGH]**
- 현 `stability_predictor.hl_score_heuristic` 는 *ranking 전용*. PlifePred는 *예측 t½ 분 단위 출력*.
- 구현 위치: `pipeline_local/scripts/stability_predictor/plifepred_wrapper.py`
- 의존성: PlifePred GitHub release + 모델 weights (별도 conda env `plifepred` 권장)
- 응답 schema: `stability_predictor`의 `hl_warnings` 와 정합 (HEURISTIC 등급 명시 유지)
- 예상 PR: 1건 (S, ~150K codex)

### 권고 2 — D-AA 치환 시뮬레이션 정량화 **[MED]**
- Octreotide D-Trp8 30× 효과를 *본 프로젝트 후보*에 일반화
- `pipeline_local/scripts/modification_conflict.py` 의 D-AA 위치별 *예상 t½ 가중치* 추가
- 입력: 위치 + D-AA 타입, 출력: 예상 t½ multiplier (1.0 = 무변경, 30 = D-Trp8)
- 한계: 실측 30×는 *Octreotide-specific*, 일반화 시 LOW confidence (HEURISTIC)

### 권고 3 — Boltz iPTM × stability 상관관계 분석 **[MED]**
- 본 SOD에서 *iPTM은 Ki proxy 아님* 확인 (어제 MSA cross-check)
- 동일 검증을 *t½*과의 상관관계로 확장:
  - Ki↔iPTM 순위 일치 0/5 (geometry 신뢰도 ≠ affinity)
  - t½↔iPTM 상관관계는? (별도 분석)
- 분석 결과를 README iPTM 한계 섹션에 *t½ 무관성*도 명시

### 권고 4 — RCSB title scraping (보조) **[LOW]**
- RCSB는 *구조 metadata*만 제공 — half-life는 *title/abstract*에 텍스트로만
- 자동 스크래핑은 *키워드 매칭* (예: "half-life", "stability", "min")
- 가치: cross-reference용. 의존하지 말 것

### 권고 5 — Wet-lab serum stability assay 발주 가속 **[HIGH]**
- 현 8 후보 중 합의 후보 3종 + cand03 + ILCKK = 5종 LC-MS/MS 의뢰
- 기간: 1-2주, 비용 ₩수백만
- 산출: 진짜 t½ (분) — heuristic ranking 검증의 *grand truth*
- 의뢰서: `docs/wetlab/halflife_methodology.md` 활용

---

## 3. 통합 BE/FE 연동

### BE
- `/api/stability/halflife/predict?seq=...` 신규 endpoint:
  - 입력: 서열 + modifications
  - 출력: heuristic + (가능시) PlifePred 예측 + 합의 후보 ranking
  - 권고 1+2 통합

### FE
- C Candidate Review 화면에 *t½ 패널* 추가:
  - heuristic ranking (현재)
  - PlifePred 예측 (권고 1 통합 후)
  - wet-lab 실측 (발주 후, manual entry 또는 외부 import)

---

## 4. 다음 SOD 후보 작업

| 우선 | 작업 | 위임 | 예상 PR |
|------|------|------|---------|
| 1 | PlifePred wrapper 구현 + 통합 | codex | 1 PR (M) |
| 2 | D-AA 시뮬레이션 가중치 | codex | 1 PR (S) |
| 3 | t½↔iPTM 상관관계 분석 (실측 + 보고서) | cursor-agent | 1 PR (S) |
| 4 | C Candidate Review에 t½ 패널 추가 | codex | 1 PR (M) |
| 5 | wet-lab serum stability 발주 (KAERI) | 사용자 | (시스템 작업 X) |

---

**작성**: orchestrator
**근거 문서**: `docs/wetlab/META_stability_halflife_integrated.md`, `_workspace/release/half-life-tool-evaluation-2026-05-14.md`
