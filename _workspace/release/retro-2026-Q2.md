# Quarterly Retrospective — 2026-Q2

> harness 어댑테이션의 첫 분기 회고. `RETROSPECTIVE_GUIDE.md` 6 Phase(A~F) 어젠다 따라 진행.

## 0. 메타

| 항목 | 값 |
|------|---|
| 일시 | 2026-05-11 |
| 참여 | 사용자 + Claude Opus 4.7 (1M context) |
| 분기 범위 | 2026-Q2 (4~6월 — 단, 본 사이클은 5/11 단일 세션에 집중) |
| 직전 회고 | 없음 (첫 회고) |
| 회고 형태 | Full 6-Phase (90분 어젠다 압축 실행) |

---

## Phase A — 사실 정리

### A-1. 본 분기 commit (harness 관련, 17개)

```
7de1e7d VR-cycle-05/06/08 + S5-01 partial closure        (v0.15.0)
4c99bf2 VR-cycle-09 (H-06)                               (v0.14.0)
2022684 VR-cycle-01/04/07 closure                        (v0.13.0)
20205f7 VR-cycle-03 PyRosetta API closure                (v0.12.1)
a3b30f7 Stage 8d End-to-End 사이클 dogfooding             (v0.12.0)
a778bde Stage 8c auto_dispatch.sh                         (v0.11.0)
00b5e9b Stage 8b reviewer-science 4분리                  (v0.10.0)
5af9c68 Stage 8a researcher 신설                          (v0.9.0)
326f9a3 README 쇼케이스                                    (—)
4cc9af7 Stage 7 .claude/agents/ 표준 섹션                 (v0.8.0)
f4f2670 Stage 6 CHANGELOG + 회고 가이드                   (v0.7.0)
81f2141 Stage 4 PR 의무 검증                              (v0.6.0)
3a3a54b Stage 3 위임 트리 ↔ 6패턴 매핑                    (v0.5.0)
a3b3bb8 Stage 2 CLAUDE.md Pointer                         (v0.4.0)
de5fabb Stage 5 약리학 환각 가드 (Critical)               (v0.3.0)
5805109 Stage 1 _workspace/                               (v0.2.0)
2637b1c Stage 0 어댑테이션 + submodule                    (v0.1.0)
```

### A-2. 본 분기 SemVer release

15개 minor cut (v0.1.0 → v0.15.0) + 1 patch (v0.12.1).

### A-3. 본 분기 release 보고서 (5개)

```
_workspace/release/
├── stage5-pharmacology-guards-2026-05-11.md       (Stage 5 검증)
├── agent-researcher-validation-2026-05-11.md      (Stage 8a)
├── agent-reviewer-domain-split-validation-2026-05-11.md  (Stage 8b)
├── auto-dispatch-validation-2026-05-11.md         (Stage 8c)
└── scenario-modification-conflict-2026-05-11.md   (Stage 8d End-to-End 사이클)
```

### A-4. 메트릭 추이

| 메트릭 | 분기 시작 (Stage 0) | 분기 종료 (현재) | 변화 |
|--------|------------------|--------------|------|
| pytest pipeline_local | 0 | **95/95** | 신설 |
| auto_dispatch routing | 0 | **16/16** | 신설 |
| 에이전트 정의 (`.claude/agents/`) | 6 | **11** (+researcher, +reviewer-pharma/biology/chemistry/math) | +83% |
| CLAUDE.md 자동 트리거 행 | 8 | **18** | +125% |
| Conflict rules | 0 | **10** (C-01~C-10) + INTERNAL_ERROR | 신설 |
| LITERATURE_VALUES 카테고리 | 0 | **5** | 신설 |
| HEURISTIC_FUNCTION_DISCLAIMERS entries | 0 | **5** | 신설 |

### A-5. §검증 필요 처리 현황

```
10 items, 100% processed
├─ FULL closed:  5 (50%) — 01/03/04/07/09
├─ ABSORBED:     1 (10%) — 02 → 09
└─ PARTIAL:      4 (40%) — 05/06/08/S5-01
```

### A-6. 차단된 historical defect (실 회귀)

| 결함 | 정답 | 차단 메커니즘 |
|------|------|----------|
| `RW_TRANSFER[P]=0.0` | -2.54 | `pharmacology_guards.audit_table` |
| `RW_TRANSFER[S]=1.15` | 3.40 | 동 |
| `NEND_HALFLIFE[P]=20.0` (yeast) | 30.0 (mammalian) | `test_nend_half_life_pro_is_30_not_20` |
| Boman 부호 역전 | 양수=친수성 | `check_sign_convention` |

추가: 자체 발견 1건 — `boman_index_kcal_per_mol` 범위 `[-5,+5]` 너무 좁음 (all-K=5.55) → `[-5,+15]`로 자체 수정. GATE-C가 자체 가설 부정확성을 catch.

---

## Phase B — 패턴 적합성 검토

### B-1. CLAUDE.md 위임 트리 1~4순위 운영 매트릭스

| 순위 | 선언 패턴 | 실 운영 빈도 (본 분기) | 일치도 |
|------|----------|------------------|------|
| 1 tmux team-mate | Fan-out/Fan-in 또는 Supervisor | **0회** (미운영) | N/A |
| 2 codex/cursor-agent | Expert Pool | **codex 1회** (사이클 Phase 3) | 일치 — codex가 코드 리뷰 도메인으로 라우팅 |
| 3 Agent tool 서브에이전트 | Pipeline/Producer-Reviewer/Fan-out/Fan-in | **8회+** (Phase 1~5, 분석/검증) | 일치 — 사이클 Phase 2 Fan-out 4명 병렬 사례가 대표 |
| 4 직접 구현 | (없음) + Hierarchical 평탄화 | **다수** (Stage 1/2/3/4/6/7/8e/8f/8g/8h/8i 메타 작업) | ⚠️ 패턴 명세 외 다수 |

### B-2. 발견 — "메타 작업"의 패턴 부재

본 분기 메타 작업(어댑테이션 자체 구축·CHANGELOG·CLAUDE.md 갱신 등)은 패턴 매핑이 없음. 4순위 "직접 구현"으로 흡수되었으나, **사이클 운영의 절반 이상**이 여기에 해당.

**제안 액션**: 다음 분기에 메타 작업용 패턴 식별 또는 4순위 정의 강화. 가능한 명명:
- **Meta-Pipeline** — 어댑테이션 자체의 단계적 진화 (Stage 0~8 같은)
- 또는 4순위에 "Pipeline (메타 / 단계적 자기 구축)" 부속

### B-3. 사이클 dogfooding (Stage 8d) — Fan-out 패턴 검증

✅ 선언과 실 운영 완전 일치:
- engineer-backend (1) + 3 reviewer 병렬 (Fan-out) + codex (외부 Producer-Reviewer) + reviewer-science 통합 (Fan-in)
- 본 사이클이 본 분기 최대 패턴 검증 사례

---

## Phase C — 환각 가드 효과

### C-1. LITERATURE_VALUES 추가 후보 (다음 분기)

본 분기 5개 카테고리 등록. 추가 권장:
- `wimley_white_water_popc` (Wimley & White 1996) — 현재 SCALE만 있고 LITERATURE_VALUES 회귀 없음 (VR-S5-03)
- `eisenberg_consensus` (Eisenberg 1982) — 동상
- `aliphatic_index_aa_coefficients` (Ikai 1980)

### C-2. SCALE_RANGES 보정 사례

본 분기 1건 자체 수정: `boman_index_kcal_per_mol` `[-5,+5]` → `[-5,+15]`. 추가 보정 후보 없음 — 모든 테스트 PASS.

### C-3. 휴리스틱 정량화 진척

- VR-S5-01 (`_PROTEASE_VULNERABILITY` 출처): PARTIAL closure (disclaimer). full closure는 researcher 실 호출로 1차 문헌 조사 필요.
- HEURISTIC_FUNCTION_DISCLAIMERS 5 entries 등록.

### C-4. 가드 자체 자기 검증

GATE-F (Fan-out 독립성) + GATE-G (토큰 비용) — 본 분기 신설. 다음 분기에 실 트래픽으로 효과 측정.

---

## Phase D — Stage 미적용 항목 검토

### D-1. 본 분기 적용 완료

Stage 0/1/2/3/4/5/6/7 + 8a/8b/8c/8d/8e/8f/8g/8h/8i — 본 분기에 **모두 적용**.

### D-2. 새 Stage 후보 (다음 분기)

| ID | 작업 | 가치 | 비용 |
|----|------|------|------|
| **Stage 9 (제안)** | tmux team-mate 1회 실 운영 데모 | 1순위 위임 트리 실 검증 | 중간 |
| **Stage 10 (제안)** | CI 등록 — `pytest pipeline_local/tests/ -q` + `./scripts/test_auto_dispatch_routing.sh` | 회귀 자동 차단 | 작음 |
| **Stage 11 (제안)** | Meta-Pipeline 패턴 식별 + CLAUDE.md 위임 트리 4순위 강화 | 메타 작업의 패턴 명세화 | 중간 |
| **Stage 12 (제안)** | `_workspace/shared_context_*.md` 컨벤션 실제 활용 사례 1회 운영 (VR-cycle-06 partial→full) | 토큰 비용 실측 | 중간 |

---

## Phase E — Action Items (다음 분기 2026-Q3)

| ID | 액션 | 책임 | 기한 | 의존 |
|----|------|------|------|------|
| Q-2026-Q3-1 | CI에 pytest + routing test 등록 | engineer-infra | Q3 초 | 없음 |
| Q-2026-Q3-2 | tmux team-mate 1회 실 운영 (Stage 9) | orchestrator | Q3 중반 | 트리거 작업 발생 |
| Q-2026-Q3-3 | VR-cycle-05 full closure — Fan-out 4명+ 호출 N회 echo 측정 | reviewer-science | Q3 말 | 실 트래픽 누적 |
| Q-2026-Q3-4 | VR-cycle-06 full closure — 토큰 비용 실측 + 공유 컨텍스트 컨벤션 적용 1회 | engineer-backend | Q3 말 | 동상 |
| Q-2026-Q3-5 | VR-S5-01 full closure — researcher 실 호출로 `_PROTEASE_VULNERABILITY` 1차 문헌 조사 | researcher | Q3 중반 | 없음 |
| Q-2026-Q3-6 | VR-cycle-08 full closure 검토 — 실 PDB 좌표 인프라 (NMR predictor 또는 X-ray DB) | engineer-infra | Q3 말 | 별도 RFC |
| Q-2026-Q3-7 | Meta-Pipeline 패턴 정의 + CLAUDE.md 위임 트리 4순위 보강 | 메인 | Q3 초 | 없음 |
| Q-2026-Q3-8 | Wimley-White / Eisenberg / Aliphatic Index LITERATURE_VALUES 등록 | reviewer-pharma | Q3 말 | 출처 인용 가능 |

**Critical 우선순위**: Q3-1 (CI 등록) → 회귀 차단 자동화는 운영 단계 진입의 전제.

---

## Phase F — CHANGELOG cut

### F-1. Unreleased 상태

`[Unreleased]` 섹션은 비어 있음 (모든 분기 작업이 v0.15.0까지 cut됨).

### F-2. 본 회고 자체의 cut

본 회고 보고서 자체를 새 minor cut으로 등록: **v0.16.0 — Quarterly Retro 2026-Q2**.

---

## 사이클 메타 평가

### 무엇이 잘 작동했나

- **자기 진화 루프**: 사이클이 자기 §검증 항목을 10/10 처리. 사용자 통찰 1건이 H-06 환각 발견·즉시 closure로 이어진 사례(VR-cycle-09)가 대표.
- **Producer-Reviewer cross-validation**: 4명 reviewer + codex가 같은 critical 이슈를 독립 식별 — 신호 강함.
- **하드웨어/도메인 한계의 정직한 노출**: PyRosetta API 호환 이슈, ref2015 small-peptide 부적합, `_PROTEASE_VULNERABILITY` 출처 부재 등을 *숨기지 않고* disclaimer로 등록.
- **하네스 본질 명확화** (`feedback_harness_scope.md` 메모리 저장): "메타 인프라이지 screening 수행 도구 아님" 원칙이 다음 분기 운영의 가드.

### 무엇이 부족했나

- **실 트래픽 부재**: 본 분기는 dogfooding 1회 + 메타 작업. 실 사용자 요청·외부 트래픽 누적 X. VR-cycle-05/06의 full closure가 이 때문에 partial로 남음.
- **tmux team-mate 1순위 미운영**: 1순위 위임 트리가 본 분기 0회 사용 — 패턴 정합성 검증 불완전.
- **메타 작업의 패턴 부재**: 본 분기 작업 절반 이상이 "4순위 직접"으로 흡수되었으나, 본질은 *어댑테이션의 단계적 자기 구축* (Meta-Pipeline 후보).
- **CI 등록 누락**: 회귀 테스트가 로컬에서만 작동. 다음 분기 1순위 액션.

### 다음 회고 트리거

- 정기: 2026-Q3 마지막 주 (~2026-09-26)
- 비상 트리거 (RETROSPECTIVE_GUIDE §3):
  1. 회귀 테스트 main 머지 차단 우회 사례 발생
  2. 패턴 선언↔실 운영 불일치 3건+
  3. lookup table 변경 PR이 LITERATURE_VALUES 등록 없이 머지된 사례

---

## §검증 필요 (본 회고의)

| ID | 항목 |
|----|------|
| VR-retro-Q2-01 | 본 회고는 dogfooding 사이클 직후 single-session 압축 실행 — 실제 분기 운영 시간(3개월) 데이터 누적 부재. 다음 분기에 *실 사용 데이터*로 보강 후 재회고 권장. |
| VR-retro-Q2-02 | Phase B-2 "메타 작업의 패턴 부재" — 본 분기 모든 메타 작업이 진정한 의미의 4순위인지(즉 위임 오버헤드보다 직접이 효율) 아니면 단순 디폴트인지 정성 평가 필요. |
| VR-retro-Q2-03 | RETROSPECTIVE_GUIDE 90분 어젠다를 single-session 압축으로 진행했으나, 정량 측정(트리거 정확도, 산출물 수치 등)은 부족. 다음 분기에는 실 트래픽 로그 + 측정 자동화 |

---

**End of 2026-Q2 Retrospective.**
