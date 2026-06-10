# Stage 9 Self-Evolution Proposals

> Stage 9 (Rosetta Flow End-to-End Dogfood, `_workspace/release/scenario-rosetta-flow-2026-05-11.md`) 에서 자가 노출된 6 critical 결함에 대한 권고 7건.
>
> **본 디렉토리의 모든 문서는 *권고 보고서*다 — 코드 수정·개선 X.** 실제 fix는 각 권고별 별도 PR에서 진행.

## 권고 인덱스

| ID | 제목 | 출처 | 우선순위 | 상태 |
|----|------|------|--------|------|
| **R1** | LLM base_url 옵션 의무화·자동 detect | F1 vLLM 8000 connection refused | Critical | ✅ proposed (본 PR) |
| R2 | PyRosetta cache key 결정 로직 진단·fix | F2 cache key 충돌 | **Critical** | pending |
| R3 | `compute_binding_ddg()` silent fallback 진단 | F3 ddG=0.00 미스터리 | **Critical** | pending |
| R4 | ESMFold pLDDT 임계값 domain-calibrate | F4 작은 cyclic peptide 부적합 | High | pending |
| R5 | `source: "silo_a"` 라벨 버그 fix | F5 라벨 버그 | Medium | pending |
| R6 | Convergence detector degraded-mode 구분 | F6 LLM 부재 vs 진짜 수렴 | Medium | pending |
| R7 | 본 발견을 `HEURISTIC_FUNCTION_DISCLAIMERS`에 등록 | Stage 5 가드 절차 적용 | Meta | pending |

## 분리 원칙

본 권고들은 각각 *독립 추적 단위*다. 이유:
- 의존 관계가 일부 있으나(R2/R3은 같은 근본 원인 가능성), 각 fix의 영향 범위가 다름
- code review 시 한 PR이 너무 커지면 검토 품질 저하
- 일부는 critical(R2/R3), 일부는 medium(R5/R6) — 머지 우선순위 분리 필요

## 본 디렉토리의 규칙

- 한 파일 = 한 권고 (`R{N}-{short-slug}.md`)
- 권고 본문 = *fix 방향 제안* (의사 코드 OK, 실 diff는 별도 PR)
- 모든 권고는 Stage 9 발견과 라인 인용 추적 가능
- 진행 상태 추적: 본 README의 표
