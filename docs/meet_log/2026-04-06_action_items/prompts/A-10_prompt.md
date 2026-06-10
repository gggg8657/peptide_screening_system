# Claude Code 실행 프롬프트 — A-10

## 사용 방법
이 프롬프트를 복사하여 Claude Code 세션에 붙여넣어 실행.
CLAUDE.md의 위임 트리 1~4순위에 따라 자동 분배됨.

---

## 컨텍스트 (Claude Code가 먼저 읽어야 할 파일)
- @CLAUDE.md
- @docs/meet_log/2026-04-06_action_items/A-10_SSTR3_docking_fix.md
- @pipeline_local/core/selectivity_runner.py
- @pipeline_local/scripts/offtarget_dock.py
- @pipeline_local/tests/test_offtarget_dock_boltz.py
- 회의록 원문: @docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf

---

## 작업 정의

**목표**: `data/somatostatin_receptor/SSTR3_8XIR.pdb` 구조의 전처리 문제를 진단하고,
누락 잔기·충돌 원자·비정상 B-factor를 해소하여 Boltz-2 도킹이 정상 완료되는
전처리 완료 구조 파일(`SSTR3_8XIR_preprocessed.pdb`)을 생성한다.

**세부 작업**:
1. SSTR3 도킹 에러 재현 및 에러 유형 분류
   ```bash
   conda run -n boltz python pipeline_local/scripts/offtarget_dock.py \
       --receptor data/somatostatin_receptor/SSTR3_8XIR.cif \
       --sequence AGCKNFFWKTFTSC --nstruct 1 \
       --output-dir runs_local/sstr3_debug
   ```
2. PDB 구조 검사 스크립트 작성 (`pipeline_local/scripts/check_receptor_structure.py`)
   - REMARK 465 (누락 잔기), clash atom, B-factor 이상치 검출
3. 에러 유형에 따른 전처리 적용
   - 누락 잔기: Modeller 또는 SWISS-MODEL
   - 충돌 원자: PyRosetta MinMover 에너지 최소화
   - B-factor: BioPython 클램핑
4. 전처리 완료 구조로 도킹 재실행 및 결과 검증
5. `selectivity_runner.py`의 SSTR3 경로 참조 갱신
6. `test_offtarget_dock_boltz.py`에 SSTR3 정상 도킹 테스트 추가

**READ-ONLY 경계 준수**: `data/` 원본 파일(`SSTR3_8XIR.pdb/cif`) 수정 금지.
전처리 완료본은 `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.pdb`로 신규 생성.

---

## 입력 (Input Spec)

| 항목 | 경로 |
|------|------|
| SSTR3 원본 구조 (READ-ONLY) | `data/somatostatin_receptor/SSTR3_8XIR.pdb` |
| SSTR3 원본 CIF (READ-ONLY) | `data/somatostatin_receptor/SSTR3_8XIR.cif` |
| 에러 로그 참조 | `runs_local/sstr3_debug/` (신규 생성) |

---

## 출력 (Output Spec)

| 산출물 | 위치 | 형식 |
|--------|------|------|
| 전처리 완료 구조 | `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.pdb` | PDB |
| 전처리 완료 CIF | `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.cif` | CIF (선택) |
| 구조 검사 스크립트 | `pipeline_local/scripts/check_receptor_structure.py` | Python |
| 에러 진단 보고 | `runs_local/sstr3_debug/diagnosis.json` | JSON |
| 테스트 추가 | `pipeline_local/tests/test_offtarget_dock_boltz.py` | pytest diff |

---

## 검증 기준 (Acceptance Criteria)

- [ ] `conda run -n boltz python offtarget_dock.py --receptor SSTR3_8XIR_preprocessed.cif ...` 에러 없이 완료
- [ ] 결과 JSON에 `ddg` 값이 -200 < ddg < 0 범위 내
- [ ] `iptm` 값이 0.0 < iptm ≤ 1.0 범위 내
- [ ] `check_receptor_structure.py` 실행 시 SSTR3 구조 이상 없음 출력
- [ ] `pytest pipeline_local/tests/test_offtarget_dock_boltz.py` 전체 통과
- [ ] `data/somatostatin_receptor/README.md`에 전처리 이력 기록

---

## 추천 위임 경로

- **3순위 서브에이전트** (진단 우선):
  - `engineer-backend` — 에러 재현 + 전처리 스크립트 구현
  - `reviewer-biology` — SSTR3 구조 품질 문제 타당성 검토 (누락 루프가 결합 포켓에 영향 미치는지)
- **2순위 codex** (스크립트 단독 작성):
  ```bash
  codex exec "pipeline_local/scripts/check_receptor_structure.py 작성: PDB 파일에서 REMARK 465 파싱, clash atom 검출(BioPython), B-factor > 100 원자 목록, JSON 리포트 출력"
  ```
- **4순위 직접 구현** (에러 재현만):
  - Bash 직접 실행으로 에러 메시지 확인 후 원인별 대응

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| `REMARK 465` 누락 잔기가 결합 포켓 근처 | Modeller 루프 재구축 필수 (reviewer-biology 확인 요청) |
| Modeller 미설치 | `conda install -c salilab modeller` — 라이선스 등록 필요, engineer-infra 요청 |
| PyRosetta init 실패 | `conda activate bio-tools` 확인, `pyrosetta.init()` 옵션 조정 |
| CIF vs PDB 파싱 불일치 | `structure_io.py::auto_detect_format()` 활용 |
| 전처리 후에도 도킹 실패 | RCSB AlphaFold DB에서 SSTR3 예측 구조(`AF-P32745-F1`)로 대체 검토 |

---

## 참고 자료

- 회의록 A-10 원문: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`
- SSTR3 RCSB 구조: https://www.rcsb.org/structure/8XIR
- SSTR3 AlphaFold DB: https://alphafold.ebi.ac.uk/entry/P32745
- MolProbity 구조 품질 평가: http://molprobity.biochem.duke.edu/
- SWISS-MODEL 루프 재구축: https://swissmodel.expasy.org/
- Modeller 루프 재구축: https://salilab.org/modeller/
- `data/` READ-ONLY 경계: `CLAUDE.md §READ-ONLY 경계`
