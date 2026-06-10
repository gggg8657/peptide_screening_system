# Claude Code 실행 프롬프트 — A-05

## 사용 방법
이 프롬프트를 복사하여 Claude Code 세션에 붙여넣어 실행.
CLAUDE.md의 위임 트리 1~4순위에 따라 자동 분배됨.

---

## 컨텍스트 (Claude Code가 먼저 읽어야 할 파일)
- @CLAUDE.md
- @docs/meet_log/2026-04-06_action_items/A-05_SST14_reference_dG.md
- @pipeline_local/steps/step05_docking.py
- @pipeline_local/scripts/offtarget_dock.py
- @pipeline_local/scripts/pharmacology_guards.py
- @pipeline_local/core/config_loader.py
- 회의록 원문: @docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf

---

## 작업 정의

**목표**: SST14 원형(AGCKNFFWKTFTSC)을 SSTR2(7XNA)에 n=10회 이상 도킹하여
`ddg` 기준선을 실측하고, 파이프라인 하드코딩 `-5` 임계값을 가변 config 구조로 교체한다.

**세부 작업**:
1. SST14 → SSTR2 반복 도킹 실행 스크립트 작성 (`pipeline_local/scripts/run_sst14_ref_docking.py`)
   - `offtarget_dock.py` subprocess 호출 n=10 루프
   - 결과 수집: `ddg` 통계 (mean, std, min, max)
   - 출력: `runs_local/sst14_ref_docking/reference_stats.json`
2. **SSOT 갱신**: `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max` (현재 `-1.0`)를 측정값 기반(`mean × 0.9`)으로 교체
   - **코드 폴백 5곳 일괄 갱신** (모두 `-5.0` 하드코딩 폴백):
     - `pipeline_local/orchestrator.py` lines 1211, 1266, 1524
     - `pipeline_local/steps/step06_rosetta.py` lines 190, 910
     - `pipeline_local/schemas/rank_table.py` line 245
   - 패턴: `config.get("rosetta_ddg_max", <SST14_REF_MEAN * 0.9>)`
   - `sst14_ref_ddg` 는 `config_loader.py`에서 `pipeline_local/core/sst14_ref.json` 읽기
3. `pharmacology_guards.py`의 `LITERATURE_VALUES`에 측정값 등록
4. 기존 테스트(`test_flexpep_dock_wrapper.py`, `test_offtarget_dock_boltz.py`)에서
   하드코딩 `-5` 참조가 있으면 config 기반으로 갱신

---

## 입력 (Input Spec)

| 항목 | 값 |
|------|---|
| SST14 서열 | `AGCKNFFWKTFTSC` |
| 수용체 구조 | `data/somatostatin_receptor/SSTR2_7XNA.cif` |
| 반복 횟수 | n ≥ 10 (서호성 박사 권장) |
| 현재 임계값 SSOT | `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max` (현재 `-1.0`, 회의 시점 `-5.0`) |
| 코드 폴백 위치 (5곳) | `orchestrator.py:1211,1266,1524` / `step06_rosetta.py:190,910` / `rank_table.py:245` — 모두 `-5.0` 폴백 |

---

## 출력 (Output Spec)

| 산출물 | 위치 | 형식 |
|--------|------|------|
| 레퍼런스 통계 | `runs_local/sst14_ref_docking/reference_stats.json` | JSON |
| 레퍼런스 설정 파일 | `pipeline_local/core/sst14_ref.json` | JSON |
| 도킹 스크립트 | `pipeline_local/scripts/run_sst14_ref_docking.py` | Python |
| SSOT 수정 | `pipeline_local/config/gate_thresholds.yaml` | YAML (diff) |
| 코드 폴백 수정 (5곳) | `orchestrator.py` / `step06_rosetta.py` / `rank_table.py` | Python (diff) |
| LITERATURE_VALUES 등록 | `pipeline_local/scripts/pharmacology_guards.py` | Python (diff) |

---

## 검증 기준 (Acceptance Criteria)

- [ ] `runs_local/sst14_ref_docking/reference_stats.json`에 `mean`, `std`, `n` 포함
- [ ] `gate_thresholds.yaml::rosetta_ddg_max` 측정값 반영 + 5곳 코드 폴백 일괄 갱신 (`grep -rn "rosetta_ddg_max\".*-5\.0" pipeline_local/`로 잔여 확인)
- [ ] `pharmacology_guards.py::LITERATURE_VALUES`에 `SST14_SSTR2_ref_ddg` 키 추가
- [ ] `pytest pipeline_local/tests/` 전체 통과 (기존 95개 + 신규 테스트)
- [ ] yaml 미지정 시 폴백 동작 확인

---

## 추천 위임 경로

- **2순위 codex** (주 구현):
  ```bash
  codex exec "pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max를 SST14 측정값 mean*0.9로 갱신. orchestrator.py(1211,1266,1524), step06_rosetta.py(190,910), rank_table.py(245)의 -5.0 폴백도 동일하게 일괄 교체. 타입힌팅 유지."
  ```
- **3순위 서브에이전트**:
  - `engineer-backend` — 반복 도킹 스크립트 + pharmacology_guards 등록
  - `reviewer-pharma` — 측정된 ΔG 값 타당성 검토 (LITERATURE_VALUES 등록 전 필수)
- **4순위 직접 구현**:
  - 도킹 반복은 Bash 루프로 직접 실행하고 통계만 Python으로 계산

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| GPU OOM | `CUDA_VISIBLE_DEVICES=2` 확인, `~/.zshrc` 설정값 참조 |
| Boltz-2 conda 환경 없음 | `conda activate boltz` 확인, engineer-infra에 환경 재구축 요청 |
| n < 10 결과 수집 | timeout 증가 또는 nstruct 파라미터 활용 |
| `ddg` 이상값 (> 0 또는 < -200) | 구조 전처리 문제 — SSTR2_7XNA 전처리 재확인 |
| 기존 테스트 `-5` 참조 | `grep -rn "rosetta_ddg_max\|\-5\.0" pipeline_local/tests/` 로 전체 확인 후 일괄 수정 |

---

## 참고 자료

- 회의록 A-05 원문: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`
- 현행 게이트 함수: `pipeline_local/steps/step06_rosetta.py::apply_rosetta_gate()`
- SSOT: `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max`
- pharmacology_guards 가드 체계: Stage 5 (`CLAUDE.md §Stage 이력`)
- Boltz-2 ddg 정의: `pipeline_local/scripts/offtarget_dock.py` docstring (`-100 * iptm`)
