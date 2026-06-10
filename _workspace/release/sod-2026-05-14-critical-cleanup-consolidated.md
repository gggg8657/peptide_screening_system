# SOD 2026-05-14 — Team `sod-2026-05-14-critical-cleanup` 통합 보고서

> **목표**: F-15 + W-01 + Critical 3건 (C-1/C-2/C-3) 통합 처리
> **워크플로우**: claude 리딩 + codex 5건 위임 (cursor-agent 비사용)
> **결과**: 5/5 task closed, **5 PR 머지** (#22~#26), 총 651K codex 토큰 별도 process

---

## 1. 5 PR 머지 결과

| PR | 제목 | 파일 변경 | codex 토큰 | 검증 |
|----|------|-----------|-----------|------|
| #22 | fix(scripts): agent-wrapper.sh ARGS array + stdin closed (W-01) | wrapper + 신규 test_agent_wrapper.sh | 57K | bash test 통과 |
| #23 | fix(stability): F-15 — /predict endpoint schema 통일 | routers/stability.py + 회귀 테스트 2건 | 139K | 107 passed |
| #24 | refactor(orchestrator): C-3 — SST-14 서열 config 이동 | orchestrator + config 3 + step03b | 116K | 4 passed |
| #25 | refactor(orchestrator): C-2 — anti-pattern 제거 | orchestrator + StepResult dataclass + 신규 test | 73K | 6 passed |
| #26 | refactor(orchestrator): C-1 — God Function 분해 (628→231줄) | orchestrator 12 헬퍼 추출 + 신규 test | 265K | 341 passed / 6 skipped / 2 xfailed |
| **합계** | | | **650K tokens** | **각 PR 회귀 0** |

---

## 2. main 최종 상태

```
b76194a refactor(orchestrator): C-1 — run_single_iteration God Function 분해 (628→231줄) (#26)
cda8a93 refactor(orchestrator): C-2 — locals().get + 익명 클래스 anti-pattern 제거 (#25)
349852a refactor(orchestrator): C-3 — SST-14 서열 config 이동 (#24)
4faae8f fix(stability): F-15 — /predict endpoint schema 통일 (#23)
c15d7ae fix(scripts): agent-wrapper.sh ARGS array + stdin closed (W-01) (#22)
```

---

## 3. 핵심 효과

### 3.1 W-01 (PR #22) — 워크플로우 인프라 fix
- `scripts/agent-wrapper.sh`: `ARGS=("$@")` array + `</dev/null` stdin 차단
- 이후 모든 codex/cursor-agent 위임이 **stuck 없이 작동**
- T4 cursor-agent 핫픽스 commit 가능 (이전 권한 거부 해소)

### 3.2 F-15 (PR #23) — API schema 통일
- `/predict` endpoint이 `StabilityResult.to_dict()` 직접 반환
- `is_unstable` / `stability_class` 노출 (이전 누락)
- /predict, /batch, /cand03 *동일 18 키 schema*
- FE 호환성 확인 (legacy schema 직접 소비 없음)

### 3.3 C-3 (PR #24) — 하드코딩 제거
- `pipeline_local/config/*.yaml` 에 `reference_peptide.sequence` 키 추가
- orchestrator + step03b 양쪽 정리
- 기본값 `AGCKNFFWKTFTSC` 유지 (backwards compatible)
- 다른 변이체 실험 시 config 1 줄로 변경 가능

### 3.4 C-2 (PR #25) — anti-pattern 제거
- `locals().get(...)` → 명시적 `Optional` 변수
- `type('R', (), {...})()` → `StepResult` dataclass
- Rosetta skip 경로 인터페이스 명시화
- 동작 변경 0 (refactor only)

### 3.5 C-1 (PR #26) — God Function 분해
- `run_single_iteration` **628 → 231줄** (60% 감축)
- 12 헬퍼 함수 추출:
  `_run_approach_a`, `_run_approach_b`, `_run_dual_silo`,
  `_run_qc_filter`, `_run_docking`, `_run_selectivity_chain`,
  `_run_diversity_filter`, `_run_rosetta`, `_finalize_rosetta_results`,
  `_run_analysis_reports`, `_compute_gate_stats`, `_build_sequence_map`
- 신규 헬퍼 테스트 `test_orchestrator_refactor_helpers.py`
- **전체 회귀 341 passed / 6 skipped / 2 xfailed**

---

## 4. 워크플로우 PoC 평가

### 4.1 토큰 분포

| Task | 본 세션 직접 시 추정 | codex 위임 실측 | 절약 |
|------|--------------------|---------------|------|
| W-01 wrapper | ~50K | **57K** (별도) | — (수준 유사) |
| F-15 stability | ~80K | **139K** (별도, 회귀 풍부) | 본 세션 0K |
| C-3 SST-14 config | ~30K | **116K** (별도, 다중 파일 정리) | 본 세션 0K |
| C-2 anti-pattern | ~40K | **73K** (별도) | 본 세션 0K |
| C-1 God Function | ~200K (대형) | **265K** (별도, 12 헬퍼 + 테스트) | 본 세션 0K |
| **합계** | **~400K** | **본 세션 ~25K + codex 650K (별도)** | **본 세션 94% 절감** |

본 세션 토큰: PR 머지 + 회귀 확인 + prompt 작성만 사용 (~25K).
codex가 별도 LLM 호출로 650K 처리.

### 4.2 워크플로우 성숙도
- **W-01 fix 적용 효과**: T2~T5 모두 codex 호출이 *stuck 없이* 성공. T1에서 결함 식별 → 즉시 fix → 후속 작업 정상 진행 (자기치유 사이클)
- **별도 worktree 패턴**: codex가 각 PR마다 `SST14-M_scr_c1`, `_c2`, `_c3` worktree 생성 → main 충돌 회피
- **PR 분리 일관성**: 각 작업 = 1 PR (분리 명확)

### 4.3 한계
- codex가 *대화형 추가 질문*에 답할 수 없음 → 첫 prompt가 정확해야 함
- codex가 무엇을 했는지 *본 세션이 검증* 의무 (회귀 테스트 결과 + 코드 read)
- *동일 파일* 동시 작업은 conflict (T3/T4/T5는 orchestrator.py 순차 진행 필수)

---

## 5. 잔존 결함·다음 작업

### 즉시 후속 (다음 SOD)
- **운영 검증**: 5 PR 통합 후 1-iter dogfood 재실행 — refactor가 *실제 동작*에 영향 없는지 확인
- **별도 세션 변경 정리**: working tree에 `critic.py`, `SelectivityTable.tsx` 등 미커밋 변경 (별도 세션 작업) — *본 세션이 손대지 않음* (분리 컨벤션)

### SOD3 개선 계획 잔존 (High 8 / Medium 9)
- **High-1** sys.path 중앙화
- **High-6** orchestrator happy-path 통합 테스트
- **High-7** step01~05 단위 테스트 (~25% → ~40% 커버리지)
- **High-5** `SILO_B_STEPS` step05 라벨 불일치
- 외 12건

### MSA cross-check 잔존 (어제)
- **VB-04** SSTR paralog row 제거 A/B
- **VB-05** `msa: empty` vs deep MSA A/B

---

## 6. 한 줄 결론

**1 SOD에 5 PR 머지 + 본 세션 토큰 94% 절감** — codex 위임 5건 모두 회귀 0 + 별도 worktree로 main 충돌 회피. W-01 fix가 이후 4 task의 안정 실행 보장 (자기치유 사이클 입증).

---

**작성**: orchestrator (Claude Opus 4.7 1M)
**최종**: 2026-05-14 06:35 KST
