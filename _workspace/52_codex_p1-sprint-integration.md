# Task #52 — P1 sprint wrapper × composite_scorer 통합

## 배경
다른 세션 (39b6e39, 5/19) P1 sprint 4팀원이 작성:
- `pipeline_local/scripts/predict_halflife_pepmsnd.py` — PlifePred2 + PepMSND wrapper (peptools env)
- `pipeline_local/scripts/predict_admet_pepadmet.py` — pepADMET 웹 stub + modlamp fallback
- `pipeline_local/scripts/sequence_to_smiles.py` — L-AA→SMILES + D-AA 19종 + DOTA

A-04 composite_scorer (PR #62)는 admet_tox + halflife_score 필드 받음. 현재 입력은 mock — 실 wrapper 호출 통합 필요.

## 의뢰
1. **composite_scorer.py 입력 보강**:
   - 후보 sequence list → predict_halflife_pepmsnd.predict_halflife() 자동 호출 → halflife_score 채움
   - sequence → sequence_to_smiles.peptide_to_smiles() → predict_admet_pepadmet.predict_admet() → admet_tox 채움
   - 신뢰도 등급 (P1-P4) ENDPOINT_CONFIDENCE 자동 적용

2. **D-AA 가드** (A-02 follow-up HIGH-BLOCKER 반영):
   - D-AA 포함 sequence (lowercase 또는 'd-' 표기) → halflife/admet *적용 금지* + grade=UNAVAILABLE 등록
   - 또는 SMILES 경로 fallback (linear D-AA SMILES만)

3. **CLI 옵션**:
   - `composite_scorer_cli.py`에 `--enrich-from-wrappers` 플래그 추가
   - 기본은 mock (회귀 보존), enrich 시 실 wrapper 호출

4. **검증**:
   - 기존 73 tests 모두 통과 유지
   - 신규 test: P1 sprint wrapper 통합 (mock + 실 호출 분기)
   - smoke: PRST-001~004 sequence로 enrich 실행 (D-AA 없는 후보들이라 정상 동작 가능)

## 참고
- @pipeline_local/scoring/composite_scorer.py (A-04)
- @pipeline_local/scripts/composite_scorer.py + _cli.py
- @pipeline_local/scripts/predict_halflife_pepmsnd.py (P1 sprint)
- @pipeline_local/scripts/predict_admet_pepadmet.py (P1 sprint)
- @pipeline_local/scripts/sequence_to_smiles.py (P1 sprint)
- @pipeline_local/scripts/pharmacology_guards.py (ENDPOINT_CONFIDENCE)
- @runs_local/final_candidates/tier_s_candidates.csv (PRST-001~004)

## 제약
- branch: `feat/p1-sprint-integration`
- PR title: `feat(scoring): P1 sprint wrapper × composite_scorer 자동 enrichment 통합`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것 (P1 sprint 파일들은 main에 머지된 상태라 OK)
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- conda env: `bio-tools`
- 마감: PR 생성 + smoke 결과 보고
