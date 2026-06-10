# EOD — 2026-05-27 (수, D-1) orchestrator 세션 (시스템 전체 점검 + 발표 자료 v3 + BE P0 fix)

> **세션 명명**: orchestrator (본 세션)
> **시작**: 2026-05-27 05:00 KST
> **마침**: 2026-05-27 ~09:50 KST
> **회의**: 2026-05-28 (목) KAERI-AIRL-MOM-2026-004 (예정)
> **브랜치**: `docs/schrodinger-proposal-d2-20260526`
> **다음 세션 핸드오프**: 본 EOD 끝의 §10 체크리스트로 5/28 회의 진행

---

## 1. 오늘의 한 줄

5/28 회의 D-1에 (1) 박사 청자용 narrative v3 + PPTX v3 26슬라이드 완성, (2) 시스템 전체 점검(Phase 0~5)으로 BE 부팅 P0 fix 적용, (3) Phase 4 다관점 분석 + 5-1 리팩토링 플랜 수립을 완료했다. 추가로 dual silo smoke 결과 narrative §5.4 "코드 격차" 챕터가 코드 실태와 정합함을 검증했다.

---

## 2. 주요 산출물 (절대경로)

### 2.1 발표 자료 (5/28 회의 직접 사용)
- **PPTX v3 (최종)**: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pptx/PRST_N_FM_Meeting_2026-05-28_v3.pptx` (26슬라이드, 875KB)
- **PPTX 빌드 스크립트**: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pptx/build_meeting_2026-05-28_v3.js` (40KB)
- **narrative v3 (최종)**: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/release/meeting-2026-05-28-narrative-v3.md` (596줄, 박사 청자 톤, §5.4 코드 격차 7항 명시)
- **narrative v2** (codex 톤 재작성 단계, 571줄): `_workspace/release/meeting-2026-05-28-narrative-v2.md`
- **narrative v1** (초안, 594줄): `_workspace/release/meeting-2026-05-28-narrative.md`

### 2.2 시연 시나리오
- **`_workspace/release/demo-scenario-2026-05-28.md`** — 투명 시연 5단계 + 한계 명시 + 백업 시나리오 A/B/C

### 2.3 시스템 점검 보고서 (Phase 0~3)
- `_workspace/release/phase2-dual-silo-smoke-2026-05-27.md` (15KB, cursor-agent 작성)
- `_workspace/release/phase3-ui-ux-2026-05-27.md` (15KB, codex 작성)
- `_workspace/release/be-p0-fix-2026-05-27.md` (7.5KB, codex 작성)

### 2.4 코드 격차 + Phase 4 분석 (4명 reviewer 산출)
- `_workspace/release/3layer-admet-serum-impact-analysis.md` (274줄, cursor-agent — 3-Layer 코드 격차 7항)
- `_workspace/release/phase4-pharma-tech-limits-goals.md` (reviewer-pharma — 도메인 한계 + 6~12개월 목표)
- `_workspace/release/phase4-code-audit-refactor.md` (reviewer-code — 16건 충족 매트릭스 + 리팩토링 13주 일정)
- `_workspace/release/phase4-uiux-integration.md` (reviewer-uiux — FE-BE 연동 + 시연 P0 3건)
- `_workspace/release/phase4-integration-and-refactor-plan.md` (reviewer-science — 통합 판정 + 5-1 리팩토링 플랜)

### 2.5 운영 도구 신설
- `scripts/session_report.sh` — 다른 세션·worktree·OPEN PR·EOD/SOD·PPTX 통합 보고
- `.claude/commands/report.md` — `/report` 슬래시 (`save`, `pr`, `eod`, `pptx`, `worktree`, `dirty` 섹션)
- `_workspace/release/session-overview-2026-05-27.md` — 오늘 새 도구로 생성한 첫 세션 통합 보고

### 2.6 코드 변경 (적용됨, 머지 안 됨)
| 파일 | 변경 | 목적 |
|------|------|------|
| `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/benchmark.py` | `llm_benchmark` import optional 처리 | BE 부팅 P0 |
| `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/status.py` | `/api/health`에 service/version 식별자 추가 | `/health` false positive 방지 |

---

## 3. 시간순 진행

| 시각 | 작업 | 위임 |
|------|------|------|
| 05:00~05:20 | dirty worktree 4개 점검 + PPT 위치 정리 + 통합 보고 도구 신설 | 본 세션 |
| 05:20~05:50 | 회의록 PDF(9p) 분석 → narrative v1 (594줄) | 본 세션 |
| 05:50~06:10 | narrative v2 (codex 톤 재작성, 369초) + 3-Layer 코드 격차 분석 (cursor-agent, 151초) | codex + cursor-agent 병렬 |
| 06:10~06:30 | reviewer-science 검증 (20건 이슈) + narrative v3 통합 (Critical 2 + Important 5 fix) | reviewer-science (Agent tool) |
| 06:30~06:50 | PPTX v3 빌드 스크립트 + 빌드 (26슬라이드, 875KB, 333초) | codex |
| 07:30~08:38 | Phase 0 환경 + Phase 1 pytest 3건 (총 777 PASS) + Phase 3 UI/UX 점검 (440초) | 본 세션 + codex |
| 07:30~08:59 | Phase 2 dual silo smoke (1500초 timeout) — pipeline_local 1 iter Boltz 32회 + Silo B PyRosetta 1건 성공 | cursor-agent |
| 08:50~09:05 | BE P0 fix (llm_benchmark optional + /api/health 식별자) | codex |
| 09:25 | 시연 시나리오 합의 (투명 시연) | 본 세션 |
| 09:30~09:41 | Phase 4 fan-out 3명 + reviewer-science 통합 | reviewer-* Agent tool |
| 09:50 | 본 EOD 작성 | 본 세션 |

---

## 4. Phase 0~5 결과 종합

### 4.1 환경 (Phase 0)
- conda env: `bio-tools` (PyRosetta·Bio·rdkit·torch 2.10.0+cu128·transformers·PyMOL 모두 OK)
- 도구별 격리 env 14개: boltz, rfdiffusion, proteinmpnn, esmfold, openfold3, diffpepbuilder, genmol, pepadmet (×2), peptools, pybamm-inv (×2), vllm-server
- GPU H100 NVL ×4 — 본인 가용 GPU 2,3. **GPU 0/1은 타인 점유, 손대지 말 것** (memory에 박힘)

### 4.2 테스트 통과 (Phase 1)
- pipeline_local: **736 PASS / 5 skip / 2 xfail / 0 fail** (58.6s)
- Silo A: **9 PASS** (0.2s)
- Silo B: **32 PASS** (0.65s, Pydantic v2 경고 82건)
- **총 777 PASS, 0 fail** — 5/20 STATUS 대비 크게 개선

### 4.3 Dual silo smoke (Phase 2)
- pipeline_local 1 iter: **25분 SLA 내 미완** (Boltz 32회 후 timeout) — 라이브 시연 불가
- Silo A (NIM): NGC API key 부재로 NIM 번들 초기화 실패
- Silo B (modular): PyRosetta `PyRosettaDockingRunner` 단건 8.6초 성공 — **라이브 시연 가능**
- `--dual` flag 비활성 → `_run_silo_a + _run_silo_b` 통합 흐름 미트리거
- pepADMET env 존재하나 패키지 import 실패
- vLLM 8002 connection refused (Planner 폴백)

### 4.4 UI/UX (Phase 3 + reviewer-uiux 보강)
- FE: build/lint 통과 (test 1건 실패 — "more" smoke는 낡은 테스트로 확인)
- BE: 부팅 실패 → **fix 적용 후 정상**. 83 routes
- FE-BE 누락 endpoint: `/api/archives/top-k`, `/api/candidate/{id}/report`
- 시연 P0 3건 (총 90분 작업): Report 버튼 disabled / Mol* "reference fallback" 라벨 / Benchmark 503 메시지

### 4.5 4월 액션 9건 충족 (Phase 4 reviewer-code)
- **원래 8건** (A-08 삭제 제외): 충족 6 / 부분 2 / 미달 0 — narrative v3 §4와 정합
- **후속 발견 8건 포함 16건**: 충족 7 / 부분 4 / **미달 5** (PR #117 미머지, PR #112 OPEN, PR #11 16일 방치, FE smoke 1건, 누락 endpoint 2건)

### 4.6 5-1 리팩토링 플랜 (reviewer-science 통합)
- **진행 권고**: Y. enrichment-code 격차 방치 비용 > 리팩토링 비용
- **단, 5/28 이전 코드 수정 금지** — P0 착수는 5/29부터
- **P0 (1주, 5/29~6/4)**: 저위험·고가시성 10항 — pharmacology_guards 중복 키 / UX 3건 / BE stub / smoke test 갱신 / 정리
- **P1 (4주)**: 결정적 격차 — PR #117 머지 / **enrichment Option A(코드를 narrative에 맞춤) vs Option B(narrative를 코드에 맞춤) 선택** / orchestrator 1차 분리
- **P2 (8주)**: Pydantic v2 / adapter.py / orchestrator 1,200 LOC 이하
- **P3 (미정)**: 단일 pytest suite / Layer 2 재학습 (실측 데이터 확보 조건부)
- **총 13주** (5/29~8월 말)

---

## 5. 5/28 회의 D-1 핵심 메시지 (narrative v3 §8 그대로)

> 4월 회의에서 받은 신규 Action Item 8건 중 6건은 충족했고, A-02/A-03은 D-AA·cyclic·DOTA 조합의 도구 부재로 부분 충족에 머물렀다. 최종 후보 PRST-001~004는 도출되었고 합성 의뢰서도 작성되었다. 다만 이 후보들은 ADMET과 serum stability 계산값만으로 통과 판정을 받을 수 없다. PR #85의 3-Layer Ensemble 모듈은 이 한계를 해결하지 않는다. 대신 한계를 수치와 경고 플래그로 노출하고, 단일 도구 출력의 과신을 막고, wet-lab 실측의 필요성을 명시하는 framework이다. 현재 표준 enrichment 경로가 이 framework를 호출하지 않는 상태이므로, 6월 회의까지 enrichment 정합 작업이 함께 진행되어야 narrative와 코드 사이의 격차가 닫힌다. Schrödinger 도입 검토는 이 한계 중 docking, rescoring, MD, FEP, hydration analysis를 상용 workflow로 줄일 수 있는지 확인하는 선택지이다. 현재는 라이센스와 비용이 확인되지 않았으므로 결정 사항이 아니라 검토 사항이다.

---

## 6. 5/28 회의에서 박사 청자 의사결정 요청 항목 (§7)

| § | 요청 | 결정 주체 |
|---|------|---------|
| 7.1 | PRST-001~004 합성 발주 범위 (전체 vs PRST-001 우선) | 서호성 박사 + RI팀 |
| 7.2 | pepADMET 라이센스 법무 검토 | KAERI 행정·법무 + AI팀 |
| 7.3 | DGX/B200 GPU 견적 결정 | 서호성 박사 + 안기범 박사 |
| 7.4 | Schrödinger 도입 검토 진행 승인 (구매 X, 6월까지 검토) | 회의 참석 전원 |
| 7.5 | 6월 회의 일자 사전 합의 | 본 회의 후 합의 |
| **추가** (reviewer-pharma 권고) | **Ki/serum/hemolysis assay 담당 기관 (KAERI RI팀 내부 vs CRO 외주)** | 서호성 박사 + RI팀 |

---

## 7. 시연 시나리오 (5/28, 투명 시연)

자세히는 `_workspace/release/demo-scenario-2026-05-28.md` 참조.

요약: BE/FE 라이브 부팅 (1분) → 기존 PRST 산출물 화면 시연 (2~3분) → Silo B PyRosetta 단건 라이브 (~10초) → 한계 화면 (Slide 17 ⚠) 2분 → Schrödinger 의제 + §7 의사결정 3~4분. 총 8~10분.

**라이브 시연 가능**: BE/FE 부팅, 기존 산출물 화면, Silo B PyRosetta 단건
**라이브 시연 불가**: pipeline_local 1 iter (40+분), Silo A 3-Arm (NGC key), `--dual` 통합

---

## 8. 미커밋 변경 사항 (위험 평가)

| 항목 | 상태 | 5/28 회의 영향 | 처리 권고 |
|------|------|---------------|---------|
| BE benchmark.py / status.py (P0 fix) | M | **시연 필수** | 회의 후 PR로 머지 |
| PDB 4개 (도킹 출력 재현) | M | 영향 0 | 의도 없으면 `git checkout` 으로 원복 |
| `_workspace/release/eod-2026-05-27-...md` 외 untracked 30+개 | ?? | 영향 0 | 다른 세션 결과물, 일부 PR로 분리 |
| `runs_local/phase2_smoke_20260527_083233/` | ?? | 영향 0 | Phase 2 산출물, gitignore 또는 별도 처리 |
| FE smoke test 1건 실패 (낡은 테스트) | — | 영향 0 | P0 fix에 포함 (5/29 이후) |

---

## 9. tmux agent-team 세션 상태

- 세션 `agent-team` 떠 있음 — orchestrator + reviewer-code + reviewer-science + engineer-backend + engineer-infra + reviewer-uiux 6명
- 사용자 attach 가능: `tmux attach -t agent-team`
- 본 EOD 이후 사용 안 하면 `tmux kill-session -t agent-team`

---

## 10. 5/28 회의 D-Day 직전 체크리스트

### 회의 30분 전
- [ ] BE 부팅 명령 실행 (`demo-scenario-2026-05-28.md §사전 준비.1`)
- [ ] BE `/api/health` 응답 `service: "ai4sci-kaeri-backend"` 검증
- [ ] FE `npm run dev` 부팅
- [ ] FE 메인 화면 `/console` 진입 확인
- [ ] 기존 산출물 `runs_local/dual_final_03/local_20260402_1055_iter01/` 접근 가능 확인
- [ ] Silo B PyRosetta 단건 명령 dry-run (`demo-scenario-2026-05-28.md §시연 흐름 Step 3`)
- [ ] PPTX 열어 슬라이드 17 ⚠ 정직 슬라이드 확인 + 슬라이드 21 슈뢰딩거 모듈 표 확인
- [ ] 다른 사용자 GPU 0/1 점유 확인 (`nvidia-smi`) — 손대지 말 것

### 회의 5분 전
- [ ] 백업 시나리오 A/B/C 점검 (PPTX 단독 진행도 가능한 상태)
- [ ] 시연 시 사용할 절대경로 6건 메모지 준비 (`demo-scenario.md` 부록)

### 회의 진행 시
- [ ] §7 5건(+1) 의사결정 항목 답변 받기
- [ ] 다음 회의 일자 합의

---

## 11. 5/28 회의 직후 본 세션 첫 작업

1. **EOD 신설** (`eod-2026-05-28-meeting.md`) — 의사결정 결과 + Q&A 기록
2. **P0 리팩토링 착수 결정** — 5/29 새 세션에서 P0 10항 작업
3. **PR 분리**:
   - BE P0 fix (benchmark.py + status.py) → 단독 PR
   - narrative v3 + PPTX v3 → `docs/meeting-2026-05-28-v3` PR
   - Phase 2~4 보고서들 → `docs/system-audit-2026-05-27` PR
4. **NGC API key 확보 진행** (Silo A 회귀용)
5. **PR #117 머지 결정** (Layer 2 R²=0.022 재학습 합의 시)

---

## 12. 다음 세션 핸드오프

본 세션이 진행한 작업의 결과는 모두 `_workspace/release/`에 있으며, 본 EOD가 단일 진실원(SSOT)이다. 다음 세션(2026-05-28 회의 진행 또는 5/29 P0 착수)은 다음 명령 한 줄로 본 세션 상태를 복원할 수 있다:

```bash
bash scripts/session_report.sh --save  # 전체 worktree·PR·EOD/SOD·PPTX 매트릭스 갱신
cat _workspace/release/eod-2026-05-27-orchestrator-d1-system-audit.md  # 본 EOD
cat _workspace/release/demo-scenario-2026-05-28.md  # 시연 순서
cat _workspace/release/phase4-integration-and-refactor-plan.md  # 5-1 리팩토링 플랜 (P0~P3)
```

---

## 13. 한계 (정직 명시)

본 세션에서 처리하지 못했거나 위임으로만 끝낸 항목:

- **Phase 5 별도 산출물 작성 안 함**: reviewer-science의 phase4-integration-and-refactor-plan.md가 §3 5-1 리팩토링 플랜을 포함하므로 별도 Phase 5 문서 생략. 필요 시 5/29 새 세션이 작성
- **P0~P3 작업 실제 착수 X**: 5/28 이전 코드 수정 금지 원칙에 따라 플랜만 수립
- **NGC API key 확보 시도 X**: 사용자 책임 영역으로 분류
- **pepADMET env import 실패 디버깅 X**: Phase 2에서 발견만, 수정은 P0 작업으로 이월
- **PR 분리 X**: 5/28 회의 후 진행 권고

---

*작성: 2026-05-27 09:50 KST · 본 세션 토큰 추적 가능 — Phase 4 fan-out 시점에 가장 큰 토큰 소모, 그 외 대부분은 codex/cursor-agent 외부 위임으로 본 세션 토큰 절약*
