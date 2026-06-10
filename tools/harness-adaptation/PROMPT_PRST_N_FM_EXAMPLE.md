# PROMPT_TEMPLATE 적용 예시 — PRST_N_FM (SST-14 / SSTR2 방사성의약품 스크리닝)

> `PROMPT_TEMPLATE.md`의 `{{...}}` 플레이스홀더를 우리 프로젝트에 채운 **실사용 예시**.
> 이 예시를 그대로 LLM 세션에 붙여 넣어 사용 가능.

---

## 0. 변수 사전 정의

```yaml
DOMAIN: "SST-14(AGCKNFFWKTFTSC, Cys3-Cys14 SS bond, FWKT pharmacophore) 기반 SSTR2 타겟 방사성의약품 후보 펩타이드 in-silico 스크리닝"
PROJECT_ROOT: /home/dongjukim/Documents/workspace/repos/SST14-M_scr
CLI: claude-code (메인) + codex (코드 수정) + cursor-agent (분석)
TEAM_SIZE: 5  # 우리 CLAUDE.md 기존 팀: orchestrator + reviewer-code + reviewer-science + engineer-backend + engineer-infra
EXISTING_AGENTS:
  - CLAUDE.md (팀원 7명 목록: orchestrator/reviewer-code/reviewer-science/engineer-backend/engineer-infra/reviewer-uiux/codex/cursor-agent)
  - scripts/agent-wrapper.sh (codex / cursor-agent 래퍼)
  - scripts/cursor/harness_invoke.sh + tools/harness-adaptation/cursor-cli/stages/ (cursor-agent 파일 기반 Pipeline, 선택)
  - scripts/launch_agent_team.sh (tmux 풀팀)
WORKSPACE_DIR: _workspace/  # 신설 (logs/external_agents/는 호출 로그 전용)
DOMAIN_GUARDS:
  - 약리학 수치는 문헌 라인 인용 의무 (Kyte-Doolittle 1982, Boman 2003 등)
  - PyRosetta 채점 함수 가중치는 ref2015 공식 문서만 인용
  - 부호 규약: Boman Index +는 친수성 (Boman 2003 §3)
  - 펩타이드 modification(D-amino acid, NMe, lactam)은 IUPAC 표기 통일
```

---

## 1. 도메인 어휘 사전 (Variable Glossary 적용)

`G-PRE-02` 준수:

| 척도 | 범위 | 부호 규약 | 출처 |
|------|------|---------|------|
| Kyte-Doolittle 소수성 | -4.5 ~ +4.5 | 양수 = 소수성 | Kyte & Doolittle 1982 J Mol Biol 157:105 |
| Wimley-White 소수성 | -2.5 ~ +2.5 (수치) | 양수 = 소수성 | Wimley & White 1996 Nat Struct Biol 3:842 |
| Eisenberg 양친매성 | 0.0 ~ +1.5 | 양수 클수록 강 양친매성 | Eisenberg 1984 |
| Boman Index | -5 ~ +5 kcal/mol | **+ = 친수성, - = 소수성 (주의)** | Boman 2003 J Intern Med 254:197 |
| Instability Index (DIWV) | 0 ~ 100 | <40 = 안정 | Guruprasad 1990 PEDS 4:155 |
| PyRosetta REF2015 | 가중합 단위 | 음수 = 안정 결합 | Alford 2017 JCTC 13:3031 |

---

## 2. 진입 규칙 적용 (Pre-Guards)

본 세션 진입 시 다음을 선언:

**G-PRE-01 적용**: 모든 약리학 수치에 출처 주석.
**G-PRE-02 적용**: 위 사전에 없는 척도는 도입 전 사용자 승인.
**G-PRE-03 적용**: Phase 0~7 중 건너뛰는 단계는 `SKIP: [이유]`로 명시.
**G-PRE-04 적용**: 산출물 각 항목에 `HIGH/MED/LOW` 등급.
**G-PRE-05 적용**: 매 Phase 시작 시 "이전 사용 값: [파일:라인]" 명시.
**G-PRE-06 적용**:
- READ-ONLY: `data/`, `local_models/`, `paper/`, `_backup/`, `pipeline_local/data/`, `bionemo/`, `tools/harness-adaptation/reference/` (submodule)
- WRITE-ALLOWED: `pipeline_local/scripts/`, `_workspace/`, `logs/`, `tools/harness-adaptation/` (reference/ 제외)
**G-PRE-07 적용**: 세션 시작 시 책임 범위 선언 (예: "이번 세션은 Silo B PyRosetta 도킹 스코어만 다룬다. 약리학 파라미터는 다루지 않는다.")

---

## 3. 도메인 환각 위험 (Domain Hallucination Risks)

| ID | 위험 | 실제 사례 / 가드 |
|----|------|--------------|
| **H-01** | 파라미터 테이블 오기재 | Radzicka-Wolfenden S=1.15(정답 1.83), P=0.0(정답 -2.54). 가드: 모든 단일 수치는 원본 논문 표에서 직접 인용 (C-02) |
| **H-02** | 부호·방향 역전 | Boman Index 부호 오류 → NSGA-II 순위 역전. 가드: 사전(§1)의 부호 규약 명시 + 계산 후 부호 일관성 확인 (C-03) |
| **H-03** | 척도 혼용 | Kyte-Doolittle / Wimley-White / Eisenberg 섞임. 가드: 척도명 + 출처 매번 기록, 같은 보고서 안에서 척도 변경 금지 |
| **H-04** | PyRosetta 채점 환각 | ref2015 fa_atr/fa_rep/fa_sol 가중치 기억 재생. 가드: 공식 문서 또는 `pyrosetta -python "..."` 출력 인용 |
| **H-05** | 반감기 참조 종 혼동 | Guruprasad Instability DIWV Pro half-life=20 (정답 30 — 효모 vs 포유류). 가드: 종/조건 명시 |
| **H-06** | **계산 불가능을 계산 가능한 척** (가장 큰 환각 위험) | `predict_half_life()` 같은 휴리스틱 함수가 `hours` 단위 float를 반환하여 "임상 반감기 예측"으로 오인됨. 실제는 ranking score (in-vitro/in-vivo PK assay·알부민 결합 affinity·신장 청소율 부재). **가드**: 휴리스틱 함수는 정직한 명세화 (이름·docstring·신뢰 등급·disclaimer). 도메인 검증의 영역이지 하네스가 정확도를 보장 X — 하네스는 **한계가 노출되도록** 돕는 역할 (feedback_harness_scope 메모리 참조) |

---

## 4. 도메인 특화 게이트 (GATE-C 수치 경계)

| 척도 | 합리적 범위 | 범위 외 시 행동 |
|------|---------|-------------|
| Kyte-Doolittle (평균) | -2.0 ~ +3.0 | 펩타이드 평균이 이 범위 밖이면 시퀀스 재확인 |
| Boman Index | -5 ~ +5 kcal/mol | 범위 외 → 계산 함수 점검 |
| Instability Index | 0 ~ 100 | 음수/100 초과 → 공식 오류 |
| REF2015 total score | -1000 ~ +500 (펩타이드-수용체) | 양의 큰 값 → packing 실패, repack 재실행 |
| pI | 0 ~ 14 | 범위 외 → calc_pI 오류 |
| 분자량 | 500 ~ 5000 Da (펩타이드) | 범위 외 → 시퀀스 길이 재확인 |

---

## 5. Phase 0 — 현황 감사 (우리 프로젝트 적용 시)

**행동**:
1. `CLAUDE.md` 읽음 — 팀원 7명, 자동 트리거 표, 위임 의사결정 트리 5단계 확인
2. `scripts/agent-wrapper.sh` 존재 확인 → codex / cursor-agent 호출 가능
3. `_workspace/` 디렉토리 부재 확인 → 신설 필요
4. `.claude/agents/`, `.claude/skills/` 부재 확인 → harness L1은 도입 안 함
5. **분기 결정**: 우리는 이미 팀 구조 보유 → **확장(L3 통합)** 또는 **유지보수**

**보고 형식**:
```markdown
## Phase 0 Audit Report
- Existing agents (CLAUDE.md): 7 (orchestrator, reviewer-code, reviewer-science, engineer-backend, engineer-infra, reviewer-uiux, codex, cursor-agent)
- Existing trigger table: yes (CLAUDE.md L46~55)
- Existing delegation tree: yes (CLAUDE.md L11~42, 5-tier)
- _workspace/: NOT EXIST — 신설 필요
- .claude/agents|skills/: NOT EXIST — harness L1 폐기 (CLI-agnostic 운영)
- Branch: 확장 (Phase 2 패턴 명시화 + Phase 6 검증 도입 + Phase 7 진화 메커니즘 추가)
```

**확인 요청**: 사용자에게 분기 결정 동의 요청.

---

## 6. Phase 1~7 우리 도메인 적용

### Phase 1 — 도메인 분석 (예시 출력)

```markdown
## Domain Analysis (PRST_N_FM)

### Core Tasks
1. SST-14 변이 생성 (PyRosetta mutation, RFAA generation)
2. SSTR2 결합 친화도 평가 (도킹, 채점)
3. 펩타이드 안정성 평가 (약리학 파라미터)
4. 오프타겟 회피 평가 (SSTR1/3/4/5 도킹)
5. 다목적 최적화 (NSGA-II 또는 베이지안)

### Tech Stack
- Python 3.10 (pipeline_local/scripts/)
- PyRosetta (Silo B)
- NIM (Silo A — 3-Arm: PepADMET, ESM-2, AF2/3)
- vLLM 로컬 모델 (llm_benchmark/)

### Conflicts/Overlap
| 기존 | 신규 (harness) | 중복도 | 권고 |
|------|------------|------|------|
| CLAUDE.md 트리거 표 | harness Phase 매트릭스 | 높음 | 우리 트리거 표 유지, harness Phase는 6패턴 명칭만 인용 |
| scripts/agent-wrapper.sh | harness Agent tool 가정 | 부분 | 우리 래퍼가 L1 추상화 어댑터 역할 |
| logs/external_agents/ | _workspace/ | 부분 | 둘 다 유지: logs는 호출 추적, _workspace는 산출물 |

### Hallucination Risks
H-01~05: §3 참조
```

### Phase 2 — 팀 아키텍처 설계 (예시 결정)

```markdown
## Architecture Decision
- Execution Mode: hybrid
  - Reason: 메인 오케스트레이션은 Claude Code 본 세션, 코드 수정은 codex, 분석/문서는 cursor-agent.
            CLAUDE.md 5단계 트리에 이미 구현.

- Pattern (per phase):
  - 후보 생성 + 채점: **Fan-out/Fan-in**
    - Silo A 3-Arm + Silo B를 병렬, integrator가 통합
    - Reason: 동일 입력(시퀀스) → 다른 관점(NIM 3개 + PyRosetta 1개) 분석
  - 약리학 평가 ↔ 검증: **Producer-Reviewer**
    - engineer-backend 생성 + reviewer-science 검증, 재시도 ≤3
    - Reason: 약리학 수치는 객관 검증 기준(문헌)이 존재
  - 단일 변이 시퀀스 분석: **Pipeline**
    - 시퀀스 검증 → 변이 적용 → 도킹 → 채점
    - Reason: 순차 의존 강함, 병렬 이득 없음

- Separation Axes:
  - 전문성: 화공학(reviewer-science) ↔ 코드(reviewer-code) ↔ 인프라(engineer-infra)
  - 병렬성: Silo A/B 동시 실행 가능
  - 컨텍스트: PyRosetta context는 large, NIM context는 medium
  - 재사용성: 시퀀스 검증 모듈은 모든 파이프라인에서 재사용

- Team Size: 5 (이미 CLAUDE.md에 정의)
```

### Phase 3 — 에이전트 정의 (이미 보유)

`CLAUDE.md` 팀원 목록이 이미 정의 역할 수행. harness 표준에 맞춰 6개 필수 섹션을 채우려면 옵션으로 `.claude/agents/{name}.md` 신설 가능. **권장**: 우선 `CLAUDE.md`만으로 시작, 필요 시 점진적 분리.

### Phase 4 — 스킬 생성

우리는 `.claude/skills/`를 사용하지 않으므로, **본 `tools/harness-adaptation/` 디렉토리 자체가 우리 첫 "스킬"**. PROMPT_TEMPLATE.md가 SKILL.md 역할, adapters/가 references/ 역할.

### Phase 5 — 통합·오케스트레이션

데이터 전달: **파일 기반** (`_workspace/`) — Codex/Cursor가 SendMessage 없으므로 강제.

파일명: `_workspace/{NN}_{agent}_{artifact}.md`. 예:
- `_workspace/01_seqgen_candidates.json` — SST-14 변이 후보 목록
- `_workspace/02_pyrosetta_dock_scores.csv` — PyRosetta 도킹 결과
- `_workspace/03_nim_3arm_results.json` — Silo A 3-Arm 결과
- `_workspace/04_integrator_ranking.md` — 통합 순위
- `_workspace/release/audit-YYYY-MM-DD.md` — 검증 보고

### Phase 6 — 검증 (도입 가치 ★)

**should-trigger** 10개:
1. "후보 펩타이드 10개 생성해줘"
2. "이 시퀀스 도킹 점수 계산해줘"
3. "SST-14 변이 평가 시작"
4. "오프타겟 회피율 확인"
5. "Silo A/B 통합 보고서"
... (이하 5개)

**should-NOT-trigger** 10개 (near-miss):
1. "이 PR 코드 리뷰해" (코드 리뷰는 codex)
2. "EOD 보고서" (cursor-agent)
3. "환경 설정" (engineer-infra 단독)
... (이하 7개)

**A/B**: harness PROMPT_TEMPLATE 적용 전/후 시퀀스 10개에 대한 후보 다양성 + 부적합 candidate 비율 비교.

### Phase 7 — 진화

변경 이력 테이블을 `tools/harness-adaptation/CHANGELOG.md`에 유지 (CLAUDE.md 오염 방지).

---

## 7. 사후 검증 체크리스트 (PRST_N_FM 적용)

- [ ] **C-01** 약리학 수치를 별도 `codex exec "pharmacology 재계산"`로 대조
- [ ] **C-02** 모든 수치에 논문 직접 인용 플래그
- [ ] **C-03** Boman Index 부호 일관성 (§1 사전 vs 계산 함수)
- [ ] **C-04** PyRosetta NULL vs 0 vs 계산 실패 구분
- [ ] **C-05** 모든 산출 수치에 `(생성 단계: Phase-X, 파일:라인)` 표기
- [ ] **C-06** §4 GATE-C 범위 일괄 재적용
- [ ] **C-07** Silo A vs Silo B 동일 파라미터 사용 일관성 비교

---

## 8. CLAUDE.md 포인터 블록 추가 제안 (Phase 5 끝)

`CLAUDE.md` 적절한 위치에 다음을 추가:

```markdown
## Harness Pointer (2026-05-11 추가)
- 본 프로젝트 harness 어댑테이션: `tools/harness-adaptation/`
- 범용 프롬프트: `tools/harness-adaptation/PROMPT_TEMPLATE.md`
- 우리 적용 예시: `tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md`
- 변경 이력: `tools/harness-adaptation/CHANGELOG.md` (Phase 7)

| 날짜 | 변경 | 대상 | 사유 |
|------|------|------|------|
| 2026-05-11 | 초기 도입 | tools/harness-adaptation/ | revfactory/harness의 L2 IP 추출 적용 |
```

**금지**: 이 블록에 에이전트·스킬 **목록**을 직접 기재하지 않음 (`SKILL.md:264-265` 원칙 — 목록은 별도 파일).

---

**End of PRST_N_FM Example.**
