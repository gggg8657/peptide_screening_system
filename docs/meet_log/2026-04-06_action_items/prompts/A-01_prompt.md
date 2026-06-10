# Claude Code 실행 프롬프트 — A-01

## 사용 방법
이 프롬프트를 복사하여 Claude Code 세션에 붙여넣어 실행.
CLAUDE.md의 위임 트리 1~4순위에 따라 자동 분배됨.

---

## 컨텍스트 (Claude Code가 먼저 읽어야 할 파일)
- @CLAUDE.md
- @docs/meet_log/2026-04-06_action_items/A-01_SSTR_site_directed_docking.md
- @pipeline_local/core/selectivity_runner.py
- @pipeline_local/scripts/offtarget_dock.py
- @pipeline_local/steps/step05b_selectivity.py
- 회의록 원문: @docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf

---

## 작업 정의

**목표**: SSTR2(7XNA) 결합 포켓 중심 좌표를 추출하고, SSTR1/3/4/5를 구조 정렬한 후
`selectivity_runner.py`가 위치 지정 도킹 좌표를 활용할 수 있도록 설정 파일을 추가한다.

**세부 작업**:
1. `data/somatostatin_receptor/SSTR2_7XNA.pdb`에서 결합 포켓 중심 좌표 추출 스크립트 작성
   - 셀렉티비티 핵심 잔기(205, 208, 209, 212, 272, 273, 276, 279) 중심 계산
   - 결과: `data/somatostatin_receptor/binding_pocket_SSTR2.json`
2. TM-align 또는 PyMOL cealign 배치 스크립트 작성
   - SSTR1(9IK8) / SSTR3(8XIR) / SSTR4(7XMT) / SSTR5(8ZBJ) → SSTR2(7XNA) 정렬
   - 정렬 구조: `data/somatostatin_receptor/{SSTRN}_aligned.pdb`
3. `selectivity_runner.py`에 결합 포켓 정보 전달 인터페이스 추가 (선택적 파라미터)
4. `pipeline_local/tests/test_step05b_selectivity.py`에 포켓 좌표 파일 로드 테스트 추가

**A-10 선행 조건 확인**: SSTR3 도킹 에러가 미해결이면 SSTR3 관련 작업은 건너뛰고
A-10 완료 후 재실행.

---

## 입력 (Input Spec)

| 항목 | 경로/값 |
|------|--------|
| SSTR2 수용체 | `data/somatostatin_receptor/SSTR2_7XNA.pdb` |
| SSTR1 수용체 | `data/somatostatin_receptor/SSTR1_9IK8.pdb` |
| SSTR3 수용체 | `data/somatostatin_receptor/SSTR3_8XIR.pdb` (A-10 선행 필요) |
| SSTR4 수용체 | `data/somatostatin_receptor/SSTR4_7XMT.pdb` |
| SSTR5 수용체 | `data/somatostatin_receptor/SSTR5_8ZBJ.pdb` |
| 핵심 잔기 목록 | TM5: 205, 208, 209, 212 / TM6: 272, 273, 276, 279 |

---

## 출력 (Output Spec)

| 산출물 | 위치 | 형식 |
|--------|------|------|
| 결합 포켓 좌표 | `data/somatostatin_receptor/binding_pocket_SSTR2.json` | JSON |
| 정렬 구조 | `data/somatostatin_receptor/SSTR{1,3,4,5}_aligned.pdb` | PDB |
| 포켓 추출 스크립트 | `pipeline_local/scripts/extract_binding_pocket.py` | Python |
| 구조 정렬 스크립트 | `pipeline_local/scripts/align_subtypes.sh` | Bash |
| 테스트 추가 | `pipeline_local/tests/test_step05b_selectivity.py` | pytest |

---

## 검증 기준 (Acceptance Criteria)

- [ ] `binding_pocket_SSTR2.json` 생성 확인 (`center_x`, `center_y`, `center_z`, `radius` 포함)
- [ ] TM-score ≥ 0.7 (SSTR1/3/4/5 vs SSTR2 정렬)
- [ ] `pytest pipeline_local/tests/test_step05b_selectivity.py` 전체 통과
- [ ] `compute_full_selectivity()` 호출 시 SSTR3 에러 없이 실행 (A-10 완료 후)
- [ ] 셀렉티비티 배수 ≥ 100× (최소) 검증 가능한 상태

---

## 추천 위임 경로

- **3순위 서브에이전트** (기본):
  - `engineer-backend` — 포켓 추출 스크립트 + selectivity_runner 인터페이스 수정
  - `reviewer-biology` — 핵심 잔기 선정 및 결합 포켓 범위 타당성 검토
- **2순위 codex** (단순 작업):
  - `codex exec "pipeline_local/scripts/extract_binding_pocket.py 작성, 입력: SSTR2_7XNA.pdb, 잔기 205/208/209/212/272/273/276/279 중심 계산, 출력: binding_pocket_SSTR2.json"`
- **4순위 직접 구현** (파일 1-2개):
  - 포켓 좌표 JSON 수동 생성 (PyMOL 콘솔에서 직접 측정 후 저장)

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| SSTR3 도킹 에러 | A-10 먼저 완료 후 SSTR3 skip하고 SSTR1/4/5 먼저 진행 |
| TM-align 미설치 | `conda install -c bioconda tmalign` 또는 engineer-infra에 요청 |
| PDB 파싱 실패 (CIF vs PDB 불일치) | `structure_io.py`의 `auto_detect_format()` 활용 |
| 핵심 잔기 번호 불일치 (7XNA vs 7T10) | RCSB에서 7T10 SEQRES와 7XNA 잔기 번호 매핑 확인 |

---

## 참고 자료

- 회의록 A-01 원문: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`
- TM-align: https://zhanggroup.org/TM-align/
- PyMOL cealign: https://pymolwiki.org/index.php/CEalign
- SSTR2 7T10 논문: DOI 10.1038/s41586-021-03980-6
- 현행 선택성 계산: `pipeline_local/core/selectivity_runner.py::compute_full_selectivity()`
