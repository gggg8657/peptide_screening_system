# PR #21 추가 검증 & codex 결과 대조 보고서

**브랜치**: `refactor/tier-thresholds-delta`  
**대상 커밋/PR**: PR #21 `refactor(step05c): TIER_THRESHOLDS Δ-기반 재설계`  
**작성일**: 2026-05-14  
**검증 실행자**: Cursor agent (직접 수행 요청 안내문 기준)

---

## §1 코드 정합성 평가

**판정: PASS**

| 항목 | 결과 |
|------|------|
| `DEFAULT_TIER_THRESHOLDS` Δ-기반 정의 | `T3: 0.03`, `T2: 0.00`, `T1: -0.03` — `Δ = iPTM(SSTR2) - max(iPTM(off-target))`와 정합 (`pipeline_local/steps/step05c_boltz_cross.py`) |
| `classify_tier(margin, thresholds)` docstring | T3≥0.03, `0.00 ≤ margin < 0.03`→T2, `-0.03 ≤ margin < 0.00`→T1, `< -0.03`→T0 로 구간이 명시됨 |
| `compute_selectivity_margin(...)` 로직 변경 | 변경 없음. `best_receptor = argmax(offtarget)`, `margin = sstr2_iptm - best_iptm` 유지 |
| 모듈 상단 Tier 설명 | `selectivity_margin`과 Δ 동치 명시 및 T0~T3 구간이 요약 형태로 기재됨 |
| HEURISTIC disclaimer | 모듈 docstring 및 `compute_selectivity_margin` docstring 내 HEURISTIC/상단 disclaimer 참조 유지 |

**조건부 메모**: 본 세션에서는 IDE 측 터미널 명령 실행이 차단되어 `pytest`를 직접 돌리지 못하였다. §2는 테스트 파일 정적 분석·카운트로 대체하였으며, **로컬에서 동일 명령 재실행**이 최종 GATE다.

---

## §2 회귀 테스트 결과 (전체 카운트)

**요청 명령** (브랜치 루트에서):

```bash
conda run -n bio-tools pytest pipeline_local/tests/test_step05c_boltz_cross.py -v --tb=short 2>&1 | tail -30
```

**정적 분석 결과**: `pipeline_local/tests/test_step05c_boltz_cross.py` 내 테스트 메서드 **합계 45개** (`TestTierDeltaRedesign` 5건, `TestF06SequenceMapFallback` 4건, `TestRunBoltzCrossValidation` 3건 포함). Codex 보고의 **45 passed**와 건수가 일치한다.

**세션별 런타임 실행**: 수행 불가(환경 제약). 회귀 0 목표 확인은 위 커맨드로 작성자 검증 필요.

요청 클래스별 존재 확인:

- `TestTierDeltaRedesign`: 5케이스 (wild→T1, selective→T3, boundary, equal→T2, extreme→T0)
- `TestF06SequenceMapFallback`: 4케이스
- `TestRunBoltzCrossValidation`: `test_*` 3케이스

---

## §3 T1 dogfood 정합성 대조 (예측 tier vs 실 분류)

T1 제공 수치만으로 `classify_tier(margin)` 적용 시 예측은 아래와 같다. 코드 분기와 완전히 일치해야 한다.

| variant | margin | 규칙 적용 | 예측 tier | 제공 tier |
|---------|--------|-----------|-----------|-----------|
| var_012 | -0.001 | `-0.03 ≤ Δ < 0` | **T1** | T1 |
| var_024 | -0.008 | 동일 | **T1** | T1 |
| var_025 | -0.030 | 경계: `Δ ≥ -0.03` 포함 → T1 (`classify_tier(-0.03) == "T1"`) | **T1** | T1 |
| var_026 | +0.003 | `0 ≤ Δ < 0.03` | **T2** | T2 |
| var_027 | -0.015 | `-0.03 ≤ Δ < 0` | **T1** | T1 |

**판정: PASS (전변수 일치).**

동일 디렉터리의 실제 JSON 부재 확인: 현재 리포토리 검색에서는 `runs_local/silo_b_f06_validation_2026-05-14/.../boltz_cross_validation.json` 경로가 없어 파일 단위 교차 검증은 수행하지 못하였다. 수치·tier 대조 자체는 위 표로 충분히 정합된다.

---

## §4 누락 식별

| 구분 | 내용 | 조치 여부 |
|------|------|-----------|
| README vs 코드 | 루트 `README.md`에서 T2만 `Δ >= 0.00`으로 서술할 경우 상한(`< 0.03`) 가독성이 떨어짐·`classify_tier`와 문장 레벨 1:1 정합 필요 | 핫픽스: T2/T1/T3를 **닫힌·반개방 구간**으로 명시하고 `classify_tier`와 동일 문구 추가 |
| `compute_selectivity_margin` HEURISTIC | 공식 함수 docstring만 보면 geometry 한계 노출이 약했음 | 문서 헤더/Disclaimer 참조하는 **HEURISTIC** 단락 유지·보강 |
| typing | `classify_tier` 반환 `str` — `Literal["T3","T2","T1","T0"]` 미사용 | 선택 사항(스타일). 필수 아님 |
| 단위 변환 | iPTM 0~1 스케일, margin 동일 스케일 — kcal/mol 혼입 없음 | 문제 없음 |
| `pipeline_local/README.md` | step05c tier Δ 문구 없음(요약 수준) | 루트 README가 SSOT 역할 — §5 범위 밖으로 유지 가능 |

---

## §5 추가 commit 권장

**권장 커밋 (이미 작업 디렉터리에 반영된 핫픽스)**

- `README.md`: step05c tier 구간을 `classify_tier`와 동일하게 정리
- `pipeline_local/steps/step05c_boltz_cross.py`: 모듈 상단·`compute_selectivity_margin` docstring의 Δ/HEURISTIC 정합 (검증 시점 기준)

**제안 커밋 메시지**

```
docs: align step05c tier intervals with classify_tier

- README: explicit Δ bands for T3/T2/T1/T0 (match step05c)
- step05c: tier summary and margin HEURISTIC cross-ref
```

**Push**: `refactor/tier-thresholds-delta`에 **추가 커밋만** 적용, force-push 금지.

> **본 에이전트 한계**: 이 세션에서 `git`/`conda` CLI가 실행되지 않아 **commit·push는 사용자가 위 메시지로 직접 완료**해야 한다. 적용 후 아래로 재검증 권장.

```bash
conda activate bio-tools
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
pytest pipeline_local/tests/test_step05c_boltz_cross.py -q
```

---

## §6 종합 판정

**MERGE 권고: CONDITIONAL APPROVE → 로컬 pytest 재통과 시 APPROVE**

- Δ 임계값·`classify_tier`·`compute_selectivity_margin`·dogfood 5건 tier는 **논리·경계값 모두 정합**.
- Codex 45 passed와 테스트 파일 45개가 **건수 일치**.
- 남은 리스크: **본 보고서 작성 환경에서 pytest 미실행** — 1회 로컬 실행으로 소거 가능.
- 문서·docstring 정합 핫픽스는 PR 본문 외 **추가 커밋**으로 처리하는 것이 요구사항과 일치한다.

---

**I propose**: (1) 워킹트리에서 `README.md`·`step05c_boltz_cross.py` diff 확인 후 위 커밋 메시지로 커밋, (2) `pytest pipeline_local/tests/test_step05c_boltz_cross.py` 실행해 45 passed 확인, (3) 원격에 일반 push.
