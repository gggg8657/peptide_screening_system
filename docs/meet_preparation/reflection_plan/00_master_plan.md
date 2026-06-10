# 반영 계획 마스터 — 6월 회의까지의 작업 항목
**작성일**: 2026-06-01 | **회의록 출처**: KAERI-AIRL-MOM-2026-003 (2026-04-06) + 본 점검 신규 발견
**원칙**: 모든 항목에 Owner / 완료기준 / 검증방법 / `committed` 또는 `proposed` / 추적성 명시

---

## 1. 정의
- **`committed`**: 본 세션 또는 기존 PR로 실제 진행 가능 (코드/리소스 확보됨)
- **`proposed`**: 6월 회의에서 의사결정 필요 (외부 견적·의견 합의·라이선스 등 차단요소 존재)

---

## 2. 반영 계획 종합표

### 2-1. 🔴 P0 — 즉시 / 금일 대응 (1일 이내)

| ID | 항목 | Owner | 완료 기준 | 검증 방법 | 분류 | 출처 |
|----|------|-------|----------|----------|------|------|
| R-01 | MCP filesystem 경로 수정 (`/home/helloworld/.../PRST_N_FM` → `/home/dongjukim/.../SST14-M_scr`) | DongJu | `.mcp.json` 수정 + Claude Code 재기동 후 filesystem MCP 도구 호출 성공 | `ls` 명령으로 마운트 경로 응답 확인 | `committed` | 본 점검 §4.4 (신규 발견) |
| R-02 | BE silo_a 라우터 404 정정 | engineer-backend | `/api/v1/silo-a/health` 200 응답 | curl 라이브 200 응답 | `committed` | 본 점검 §4.1 |
| R-03 | FE smoke "More" 테스트 갱신 | reviewer-uiux | `App.smoke.test.tsx` 2/2 PASS | `vitest run` 결과 | `committed` | 본 점검 §4.2 |

### 2-2. 🔴 P0 — 차주 대응 (~6월 회의 D-7)

| ID | 항목 | Owner | 완료 기준 | 검증 방법 | 분류 | 출처 |
|----|------|-------|----------|----------|------|------|
| R-04 | K-1/K-2 selectivity 결함 정정 (`_build_pdb_index` 정렬 + `candidate_pdb` 전달) | engineer-backend | 후보별 off-target 결과가 서로 다름을 회귀 테스트로 검증 | `pytest pipeline_local/tests/test_selectivity.py` PASS + 수동 sample 비교 | `committed` | A-04 한계 + 본 점검 신규 발견 |
| R-05 | PR #117 (ADMET divergence guard) 머지 결정 | engineer-backend + reviewer-pharma | Layer 2 R²=0.022 재학습 합의 → PR 머지 또는 정책 결정 후 close | `git log origin/main` PR 머지 확인 | `proposed` | A-02 + A-04 + audit §1.1 |
| R-06 | enrichment 경로 정합 — Option A vs B 결정 | reviewer-science (라우터) | 6월 회의에서 합의 → 코드 변경 PR 생성 | PR 머지 후 `enrich_candidates_from_wrappers`가 `run_routed_halflife` 호출 grep | `proposed` | A-02 + A-04 |
| R-07 | Layer 3 (DOTA ADMET-AI MD proxy) 최소 구현 | engineer-backend + reviewer-pharma | `layer3_dota_admet_ai_md_proxy_stub` → OOD 경고 발행 최소 구현 | `pytest test_layer3_admet_ai.py` 신규 케이스 PASS | `proposed` | A-03 + A-04 + 본 점검 §6.6 |
| R-08 | A-09 PRST-001~004 ranking 재검증 (K-1/K-2 정정 후) | engineer-backend + reviewer-pharma | 재산정된 selectivity로 Tier ranking 보고서 | `runs_local/dual_final_03/` 재실행 + ranking diff 보고 | `committed` | A-09 + 본 점검 §6.1 |
| R-09 | A-06 DiffDock 본격 PoC 1회 실행 | engineer-backend + engineer-infra | RMSD ≤2.0Å 재현율 + wall-clock time per candidate 보고 | `pipeline_local/wrapper_scripts/run_diffpepbuilder.py` 또는 신규 DiffDock 스크립트로 측정 | `committed` | A-06 + A-07 |
| R-10 | A-07 GPU 벤더 견적서 2개 수령 | 서호성·안기범 | 견적서 PDF + 비교표 보강 | docs/meet_log/ 견적서 첨부 | `proposed` | A-07 |

### 2-3. 🟠 P1 — 4주 (audit 권고)

| ID | 항목 | Owner | 완료 기준 | 검증 방법 | 분류 | 출처 |
|----|------|-------|----------|----------|------|------|
| R-11 | A-05 MM-GBSA 도구 검토 결과 (gmx_MMPBSA vs OpenMM 직접 구현) | reviewer-pharma + engineer-backend | 비교표 + 도입 의사결정 권고 | `docs/meet_preparation/references/libraries/` 도구 평가 | `proposed` | A-05 + 서호성 의견 §6 |
| R-12 | A-02 벤치마크 세트 정확도 측정 (R²/Spearman ρ) | engineer-backend + reviewer-pharma | SST14/Octreotide/Lanreotide/RC-160+3-6종 도구별 R² 보고 | 표 + 도구별 매핑 | `committed` | A-02 + 회의록 §4 |
| R-13 | Silo A 이중 구현 통합 또는 역할 분리 결정 | reviewer-science | 6월 회의에서 정책 결정 → narrative 정정 | (정책 결정 문서) | `proposed` | 본 점검 §4.7 (신규 발견) |
| R-14 | Silo C 정책 결정 (구현 vs aggregator 가중치 재설계 A:0.5/B:0.5) | reviewer-science | 6월 회의에서 정책 결정 → policy.py + aggregator.py 변경 | `git diff pipelines/orchestration/policy.py` | `proposed` | 본 점검 §4.9 (신규 발견) |
| R-15 | 25분 SLA 재평가 (demo subset 정의) | engineer-backend | 새 SLA + demo subset 명세 | `pipeline_local/config/demo_subset.yaml` 신규 | `committed` | 본 점검 §4.8 |
| R-16 | orchestrator.py 1차 함수 분리 (audit 권고) | reviewer-code | 4주 일정 audit §5 따름 | refactor PR 머지 | `proposed` | audit §5-1 |
| R-17 | 누락 endpoint 2건 등록 + PR #11 16일 방치 해소 | engineer-backend | endpoint 등록 + PR close | curl 라이브 200 응답 | `committed` | audit §4.5 |
| R-18 | A-03 pepADMET 자체 학습 평가 (데이터·GPU·시간 산정) | engineer-backend + reviewer-pharma | 산정 보고서 + 의사결정 권고 | `docs/meet_preparation/references/libraries/pepADMET.md` | `proposed` | A-03 + 회의록 §4 단계 4 |

### 2-4. 🔵 P2 — 검토 사항 (의사결정 미정)

| ID | 항목 | Owner | 완료 기준 | 검증 방법 | 분류 | 출처 |
|----|------|-------|----------|----------|------|------|
| R-19 | Schrödinger 도입 검토 (라이센스·비용 정량화) | 서호성·DongJu | 라이센스 비용·기능 비교 + 의사결정 권고 | 견적·기능표 | `proposed` | audit §5 권고 |
| R-20 | A-01 7T10 vs 7XNA 구조 ID 정합 | engineer-backend | 정합 결정 + selectivity 배수 재검증 | binding_pocket JSON 재생성 | `committed` | A-01 한계 |
| R-21 | Radiolysis Quencher DOE 구현 (서호성 의견) | engineer-backend + reviewer-pharma | Quencher 4 조합 후보 + RCY/RCP 평가 모듈 | `pipeline_local/scoring/radiolysis_scorer.py` 확장 | `proposed` | 회의록 §7 A-04 보강 |

---

## 3. 통계 요약

| 분류 | committed | proposed | 합계 |
|------|-----------|----------|------|
| P0 즉시 (R-01~03) | 3 | 0 | 3 |
| P0 차주 (R-04~10) | 3 | 4 | 7 |
| P1 4주 (R-11~18) | 3 | 5 | 8 |
| P2 검토 (R-19~21) | 1 | 2 | 3 |
| **합계** | **10** | **11** | **21** |

> **금일 착수 가능 (P0·단기·committed)**: **R-01, R-02, R-03, R-04, R-08, R-09** (6건)

---

## 4. 의존 관계 (선후 작업)

```
R-04 (K-1/K-2 정정) ─┐
                     ├──► R-08 (PRST ranking 재검증)
R-05 (PR #117)  ─────┤
R-07 (Layer 3 최소)  │
                     ├──► R-12 (벤치마크 R²)
R-06 (enrichment)────┘

R-09 (DiffDock PoC) ─►  R-10 (GPU 견적) ─► A-06 의사결정

R-14 (Silo C 정책) ──► R-13 (Silo A 통합) ─► narrative 정정

R-11 (MM-GBSA 검토) ─► A-05 정밀 계산 도입
```

---

## 5. 6월 회의 직전 D-7 체크리스트

- [ ] R-01 ~ R-03 (즉시) 완료 확인
- [ ] R-04 (K-1/K-2) 정정 완료 + R-08 ranking 재검증 결과
- [ ] R-09 DiffDock PoC 결과 (RMSD ≤2.0Å 재현율)
- [ ] R-10 GPU 견적서 2건 수령
- [ ] R-12 벤치마크 R² 보고서
- [ ] R-19 Schrödinger 검토 자료
- [ ] R-14 Silo C 정책 안건 정리
- [ ] R-13 Silo A 이중 구현 안건 정리

---

## 6. 추적성 매핑 (반영 항목 ↔ Action Item ↔ 본 점검 §)

| 반영 항목 | 회의록 Action Item | 본 점검 § | 관련 PR/파일 |
|-----------|------------------|----------|--------------|
| R-01 | (외) | §4.4 MCP | `.mcp.json` |
| R-02 | (외) | §4.1 BE | `backend/main.py:133` |
| R-03 | (외) | §4.2 FE | `App.smoke.test.tsx` |
| R-04, R-08 | A-09 | §6.1 selectivity 결함 | `_build_pdb_index`, `selectivity_runner` |
| R-05, R-06, R-07 | A-02, A-03, A-04 | §6 ⓘ PR #117 | `composite_scorer`, `ensemble_router` |
| R-09 | A-06 | §6.7 SLA 미완 | `run_diffpepbuilder.py`, `step05_docking.py:144` |
| R-10 | A-07 | (외) | (외부 견적) |
| R-11 | A-05 | §6.5 정밀 계산 미구현 | gate_thresholds.yaml |
| R-12 | A-02 | §6 ⓘ Layer 2 | `predict_halflife_pepmsnd.py` |
| R-13 | (외) | §4.7 Silo A 이중 | `pipelines/silo_a/`, `pipeline_local/_run_silo_a()` |
| R-14 | (외) | §4.9 Silo C | `policy.py`, `aggregator.py` |
| R-15 | (외) | §4.8 SLA | `pipeline_local/config/` |
| R-16, R-17 | (audit) | (외) | audit §5 |
| R-18 | A-03 | (외) | pepADMET 자체 학습 |
| R-19 | (audit) | (외) | Schrödinger |
| R-20 | A-01 | §4.7 | binding_pocket JSON |
| R-21 | (회의록 §7 A-04 보강) | (외) | `radiolysis_scorer.py` |

---

*본 반영 계획은 §종합 향후방향 의견(보고서 §11)의 실행 근거이다.*
