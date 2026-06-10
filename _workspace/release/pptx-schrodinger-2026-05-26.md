# PPTX Schrödinger 의제 추가 작업 보고 — 2026-05-26

## 배경

- 회의일: 2026-05-28
- 작업일: 2026-05-26 (D-2)
- 사용자 확인: KAERI Schrödinger 라이센스 미보유
- 목적: 5월 회의 추가 의제로 Schrödinger 도입 검토를 상정하고, 6월 회의까지 KAERI 행정·견적·모듈 범위 검토를 요청

## 산출물

- `_workspace/pptx/build_action_items_audit_2026-05-28_d6_schrodinger.js`
- `_workspace/pptx/PRST_N_FM_ActionItems_Audit_2026-05-28_d6_schrodinger.pptx`
- `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md`
- `_workspace/release/pptx-schrodinger-2026-05-26.md`

## PPTX 변경

- 기존 D-6 20 슬라이드 빌드 스크립트를 복제해 D-2 Schrödinger 의제판을 별도 생성했다.
- 총 슬라이드 수를 21장으로 변경했다.
- footer를 `Deck 2026-05-28 D-2 + Schrödinger 의제` 및 `p/21` 형식으로 갱신했다.
- 21번 슬라이드 제목: `추가 의제 — 슈뢰딩거 도입 검토 (6월 회의까지)`

### 21번 슬라이드 핵심 내용

- 현 도구 한계와 Schrödinger 모듈 매핑:
  - PRST ADMET=1.00 OOD 외삽 → BioLuminate
  - Layer 2 R²=0.022 → Desmond
  - HLE 회귀 계수 부재 → Schrödinger in silico HLE assay
  - DiffPepDock SS bond X → Glide cyclic peptide
  - OpenMM/OpenFE 학습 곡선 → FEP+
  - FlexPepDock vs Boltz-2 단위 충돌 → Glide SP/XP
- 회의 §2.5 7단계 중 (1), (4), (5), (6), (7)에 Glide SP/XP, MM-GBSA (Prime), BioLuminate, Desmond + FEP+, WaterMap을 매핑했다.
- 비용·일정은 확정하지 않고, Schrödinger Korea 영업 연락과 KAERI 외부 SW 도입 승인 검토가 필요하다고 명시했다.
- 의사결정 요청은 `6월 회의까지 도입 검토 진행 동의?`로 정리했다.

## MEETING_PREP 변경

- `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md`의 Q1~Q8 뒤, §4와 §5 사이에 Q9를 추가했다.
- Q9는 현 도구 한계, Schrödinger 모듈 매핑, 회의 7단계 정합성, 비용·일정·KAERI 행정 검토, 6월 회의까지 도입 검토 권고를 4문단으로 정리했다.

## 검증

- Node 빌드 실행:
  - `cd _workspace/pptx && node build_action_items_audit_2026-05-28_d6_schrodinger.js`
- 결과:
  - `Saved: PRST_N_FM_ActionItems_Audit_2026-05-28_d6_schrodinger.pptx`

## 주의

- commit은 수행하지 않았다.
- 비용, 일정, 라이센스 조건은 사용자/KAERI가 Schrödinger Korea 및 내부 행정 절차로 확인해야 한다.
