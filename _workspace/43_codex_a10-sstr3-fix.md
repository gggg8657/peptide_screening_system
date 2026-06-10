# A-10 — SSTR3_8XIR 도킹 fix

상세 prompt: `docs/meet_log/2026-04-06_action_items/prompts/A-10_prompt.md` 참조

## 핵심 목표
`data/somatostatin_receptor/SSTR3_8XIR.pdb` 구조의 전처리 문제 진단 + offtarget_dock.py 패치.

## 참고
- @docs/meet_log/2026-04-06_action_items/A-10_SSTR3_docking_fix.md
- @pipeline_local/core/selectivity_runner.py
- @pipeline_local/scripts/offtarget_dock.py
- @pipeline_local/tests/test_offtarget_dock_boltz.py

## 작업 순서
1. SSTR3_8XIR.pdb 파일 존재 + 구조 확인 (chain, residue, non-standard)
2. 도킹 시도 → 실패 로그 확인
3. 전처리 문제 진단 (chain ID 누락, non-standard residue, ATOM 누락 등)
4. offtarget_dock.py 전처리 함수에 SSTR3 대응 패치 추가
5. test 추가 (`test_offtarget_dock_boltz.py`에 SSTR3 case)
6. smoke 실제 도킹 1회 — `bio-tools` env에서

## 출력
- branch `fix/a10-sstr3-docking`
- PR title: `fix(docking): A-10 SSTR3_8XIR 전처리 + 도킹 호환성`
- 변경 파일 + smoke 결과 보고

## 제약
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- conda env: `bio-tools` (PyRosetta + Boltz)
- 마감: PR 생성 + smoke 결과 + 변경 파일 보고
