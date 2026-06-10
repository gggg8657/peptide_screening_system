# 종합 진행 계획 — 2026-05-19 후반

> **작성**: orchestrator (본 세션)
> **시점**: Phase 1+2 완료 후 추가 진행 계획 수립

## 1. 다른 세션 활동 분석

### 1.1 main 직접 push 4건
| Commit | 작업 | 추정 세션 | 영향 |
|--------|------|----------|------|
| `91eaef8` | flake8 F821 TYPE_CHECKING fix | 다른 세션 | CI 복구 |
| `6054ea9` | A-06 DiffPepDock PoC | engineer-backend | NOT_RECOMMENDED 권고 |
| `39b6e39` | **P1 sprint — A-02/A-03 wrapper** | 4팀원 (be-a04/be-a01-cif/infra/reviewer-pharma) | **3 wrapper 신설 + ENDPOINT_CONFIDENCE 16건** |
| `8e7e1cc` | A-05 SST14 ref dG | engineer-backend | reference 등록 |

### 1.2 P1 sprint 산출물 (39b6e39)
```
pipeline_local/scripts/
├── predict_halflife_pepmsnd.py    (PlifePred2 + PepMSND)
├── predict_admet_pepadmet.py      (pepADMET + modlamp fallback)
└── sequence_to_smiles.py          (L-AA→SMILES + D-AA 19종 + DOTA)
```
- 55/55 tests pass
- `ENDPOINT_CONFIDENCE` 신규 6건 (halflife) + 추가 (admet)
- D-AA 미지원 명시 + UNKNOWN grade 등록

## 2. Action Items 9건 — 모두 완료 (오늘 5/19 종결)

| ID | 본 세션 | 다른 세션 | 최종 결과 |
|----|--------|----------|----------|
| A-01 | PR #61 | - | RMSD 2.77-3.13Å |
| A-02 | researcher + follow-up | P1 sprint wrapper | D-AA 불가 확정 |
| A-03 | researcher | - | "Fab-ADMET"=pepADMET 확정 |
| A-04 | PR #62 | - | composite_scorer Tier 분류 |
| A-05 | - | `8e7e1cc` | n=10 mean=553.857 σ=4.024 |
| A-06 | - | `6054ea9` | NOT_RECOMMENDED |
| A-07 | engineer-infra | - | 192GB 확인 |
| A-08 | researcher | - | 회의 당일 삭제 확정 |
| A-09 | PR #63 | - | PRST-001~004 최종 후보 |
| A-10 | PR #60 | - | SSTR3 fix |

## 3. 미진 사항 (V-검증 HIGH 6건)

대부분 **wet-lab 의존** — Gate-2 단계에서 RI팀이 처리.

| # | 사항 | 자동화 가능? |
|---|------|------------|
| V-A09-01 | PRST-001 F6→I Ki 실측 | **NO (wet-lab)** |
| V-A09-03 | pepADMET selectivity Ki 상관 | **NO (wet-lab)** |
| V-A09-05 | half-life ranking wet-lab 검증 | **NO (wet-lab)** |
| V-A09-06 | Boltz2 ΔG -105.5 vs 실험 IC50 | **NO (wet-lab)** |
| V-02 | pepADMET 논문 paywall | △ (저자 문의) |
| V-03 | pepADMET D-AA SMILES 테스트 | ✅ (A-02 follow-up에서 일부 해결) |

→ **V-검증은 wet-lab Gate-2 대기**. 본 세션 system 작업으로 추가 진행 불가.

## 4. 추가 작업 4건 (오늘 안 진행 가능)

### A. /pptx 통합 발표 자료 (사용자 명시 요청)
- 모든 보고서 + PR + 결과 시각화
- Gate-2 진입 준비 상태 명시
- PRST-001~004 후보 강조

### B. #38 Boltz docking으로 SSTR2-SST14 complex 생성
- Phase 3 ProteinMPNN receptor_context 모드 활성화
- V-A09-06 ΔG 검증 일부 해결 (실 complex 기반 dG)
- engineer-backend 위임

### C. #39 사용자 취사선택 시스템 — Strategy mode/complex/variant 선택 API + FE UI
- 사용자 명시 요청 (5/19 ProteinMPNN 결정 시)
- BE API + FE 패널 신설
- engineer-backend (BE) + 별도 codex (FE)

### D. P1 sprint 통합
- `predict_halflife_pepmsnd.py` + `predict_admet_pepadmet.py`를 composite_scorer에 자동 연결
- A-04 composite_scorer 입력 enrichment
- 본 세션 또는 codex 위임

## 5. 실행 우선순위 (사용자 명시 1+4+추가)

```
즉시 병렬 시작:
  - /pptx 작성 (가장 시간 김, 결과 통합)
  - #38 Boltz complex 위임 (engineer-backend)
  - #39 취사선택 시스템 위임 (engineer-backend BE)
  - D. P1 sprint 통합 위임 (codex)

대기:
  - V-검증 HIGH 6건 — wet-lab Gate-2 (자동화 불가)
```

## 6. Gate-2 진입 명시 — 합성 의뢰서 4건

| ID | 서열 | Tier | 즉시 발주 가능? |
|----|------|------|---------------|
| PRST-001 | AGCKNIIWKTITSC | **S** | ✅ |
| PRST-002 | AGCKNFIWKTITSC | B | ✅ |
| PRST-003 | AGCRNFIWKTITSC | B | △ (K4→R, N-말단 DOTA 전용, RI팀 사전 협의 필요) |
| PRST-004 | AICKNFIWKTITSC | B | ✅ |

`runs_local/final_candidates/synthesis_orders/` 디렉토리에 4개 의뢰서 파일 위치.

## 7. 다음 SOD 후보 (오늘 마감 후)

- E. Gate-2 PRST-001~004 wetlab order 등록 + 발주 (RI팀)
- F. P1 sprint wrapper의 BE/FE 통합 (`/api/admet`, `/api/halflife` 신규 endpoint)
- G. 회의록 4/6 후 차기 회의 (5월 말 예정?) 액션 아이템 사전 정리
