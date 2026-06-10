# _workspace/ — 다단계 작업 중간 산출물 디렉토리

> harness Stage 1 채택 결과 (`tools/harness-adaptation/INTEGRATION_PLAN.md`).
> 다단계(multi-phase) 작업의 중간 산출물을 표준화된 컨벤션으로 보관.

---

## 목적

`logs/external_agents/`와 명확히 분리:

| 디렉토리 | 책임 | 내용 예시 |
|---------|------|---------|
| `logs/external_agents/` | **호출 추적** (when, who, what command) | codex/cursor-agent 호출 시각, 인자, 종료 코드 |
| `_workspace/` | **산출물 자체** (artifact content) | 후보 펩타이드 JSON, 도킹 스코어 CSV, 통합 보고서 MD |

후속 단계는 `@_workspace/01_*.md` 형태로 선행 산출물을 직접 참조한다.

---

## 파일명 컨벤션

```
{NN}_{agent}_{artifact}.{ext}
```

| 토큰 | 의미 | 예 |
|------|------|---|
| `NN` | 2자리 단계 번호 (01~99, 순차 의존 표현) | `01`, `02`, `10` |
| `agent` | 산출물 생성 에이전트 역할 (소문자, 하이픈 가능) | `seqgen`, `pyrosetta-dock`, `nim-3arm`, `integrator` |
| `artifact` | 산출물 종류 (명사) | `candidates`, `scores`, `ranking`, `report` |
| `ext` | 확장자 | `json`, `csv`, `md`, `pkl` |

### Cursor CLI 하네스 (`harness_invoke.sh`)와의 관계

[`scripts/cursor/harness_invoke.sh`](../scripts/cursor/harness_invoke.sh) 가 치환하는 기본 패턴은 다음 형태이다 (토픽 슬러그·stage 파일명 stem 포함):

```
NN_cursor-<topic_slug>_01_explore.md
```

본 디렉터리 규칙(`NN`, 역할 문자열, 확장자)과 호환되도록 두었다.

### 예시 (PRST_N_FM 듀얼 파이프라인)

```
_workspace/
├── 01_seqgen_candidates.json          # SST-14 변이 후보 목록 (Silo 공통 입력)
├── 02_pyrosetta_dock_scores.csv       # Silo B 도킹 결과
├── 03_nim_3arm_results.json           # Silo A 3-Arm 결과
├── 04_pharmacology_eval.md            # 약리학 파라미터 평가
├── 05_integrator_ranking.md           # 통합 순위 (Silo A+B 통합)
└── release/
    └── audit-2026-05-11.md            # 검증 보고서 (git에 보존)
```

---

## 에이전트 간 의존 표기 의무

후속 산출물이 선행 산출물을 참조할 때 **명시적 인용** 필수:

```markdown
## 05_integrator_ranking.md

### 입력
- `_workspace/02_pyrosetta_dock_scores.csv:1-50` (Silo B 상위 50개)
- `_workspace/03_nim_3arm_results.json` (Silo A 전체)

### Audit 권고 반영
- Audit R4: 오프타겟 회피율 < 0.3인 후보 제외
- Audit R7: 분자량 5000Da 초과 후보 경고 표시
```

`Audit R4`, `R7` 같은 인용은 `release/audit-*.md`의 권고 번호를 가리킨다 (harness Producer-Reviewer 패턴).

---

## Git 추적 정책

`.gitignore`에 정의:

| 패턴 | 추적 여부 |
|------|--------|
| `_workspace/README.md` | ✅ 추적 (본 파일) |
| `_workspace/release/*.md` | ✅ 추적 (검증 보고서) |
| `_workspace/*.{json,csv,md,...}` 일반 산출물 | ❌ ignore |

**원칙**: 산출물은 재현 가능(시드+코드+입력으로 다시 생성)해야 하므로 git에 보존하지 않음. 단, **검증/감사 보고서**(`release/`)는 사후 추적 가능성을 위해 보존.

산출물을 강제로 추적해야 하는 경우(논문 figure 원본 등): `git add -f _workspace/<file>` 사용.

---

## 사용 워크플로우

### 1. 다단계 작업 시작 시
- 단계 목록 사전 정의 (`01`, `02`, ...)
- 각 단계의 입력/출력 파일명을 사전 선언

### 2. 단계 실행 시
- 산출물을 위 컨벤션대로 저장
- 후속 단계 시작 시 "이전 단계 사용 값: [파일:라인]" 명시 (G-PRE-05, `PROMPT_TEMPLATE.md`)

### 3. 작업 종료 시
- 검증 보고서를 `release/audit-YYYY-MM-DD.md` 또는 `release/<topic>-YYYY-MM-DD.md`로 보존
- 일반 산출물은 ignore되어 작업 트리에서 자연 정리됨

---

## 관련 문서

- `tools/harness-adaptation/PROMPT_TEMPLATE.md` — Phase 5 데이터 전달 컨벤션
- `tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md` §6 — 우리 도메인 적용 예
- `tools/harness-adaptation/INTEGRATION_PLAN.md` Stage 1 — 본 디렉토리 도입 결정
- `CLAUDE.md` — 위임 의사결정 트리 (어느 단계를 어느 CLI에 위임할지)
