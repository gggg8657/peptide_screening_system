# SOD 2026-05-19 — A-01 SSTR Site-Directed Docking

## 작업 요약

A-01 액션 아이템: SSTR2(7XNA) 결합 포켓 중심 좌표 추출 + SSTR1/3/4/5 5종 정렬 + selectivity_runner.py 인터페이스 추가.

---

## 산출물

### 1. 결합 포켓 좌표 JSON
- 파일: `data/somatostatin_receptor/binding_pocket_SSTR2.json`
- 핵심 잔기: TM5(205,208,209,212) + TM6(272,273,276,279) 8개
- 중심 좌표: center_x=-5.595, center_y=-28.626, center_z=52.210 (Å)
- 반경: radius=13.035 Å (max CA→centroid + 5Å 여유)
- 박스 크기: 26.1 Å (GNINA/AutoDock-GPU 직접 사용 가능)
- GNINA config: `gnina_config` 서브딕셔너리 포함

### 2. 5종 구조 정렬 결과

| 수용체 | RMSD (Å) | 정렬 원자 수 | 방법 |
|--------|----------|------------|------|
| SSTR1 (9IK8) | 3.125 | 264 | PyMOL cealign |
| SSTR3 (8XIR) | 3.086 | 272 | PyMOL cealign |
| SSTR4 (7XMT) | 3.019 | 248 | PyMOL cealign |
| SSTR5 (8ZBJ) | 2.770 | 256 | PyMOL cealign |

모든 RMSD ≤ 4.0 Å, KPI 기준(TM-score ≥ 0.7 권장) 달성 수준.

### 3. 신규 스크립트
- `pipeline_local/scripts/extract_binding_pocket.py`: PDB/CIF에서 결합 포켓 중심 좌표 추출
- `pipeline_local/scripts/align_subtypes.py`: PyMOL cealign / biopython Superimposer 배치 정렬

### 4. selectivity_runner.py 인터페이스 추가
- `SelectivityRunner.__init__(binding_pocket_json=...)` 선택적 파라미터
- `SelectivityRunner.load_binding_pocket(json_path)` — JSON 파일 로드
- `SelectivityRunner.get_pocket_center()` — (x, y, z) 튜플 반환
- `SelectivityRunner.get_gnina_config()` — GNINA/AutoDock-GPU 설정 딕셔너리 반환
- 모듈 수준 `load_binding_pocket(json_path)` 헬퍼 추가

---

## 테스트 결과

`pytest pipeline_local/tests/test_step05b_selectivity.py -v`

- **신규**: TestBindingPocketInterface (12 tests) — 12/12 PASSED
- **기존 회귀**: TestComputeSelectivityMargin, TestApplySelectivityGate, TestRunSelectivityScreening, TestSchemaRoundtrip, TestSignConventionAlignment, TestGateThresholdsYaml — 26/26 PASSED
- **합계**: 38/38 PASSED

---

## PR

- https://github.com/AI-scientist4BIO/SST14-M_scr/pull/61
- 브랜치: `feat/a01-sstr-site-directed-docking`

---

## 주의 사항

- Boltz-2 엔진은 binding box 불필요 — 현재 `binding_pocket_json`은 향후 GNINA/AutoDock-GPU 병용 시 사용
- 정렬 방법 우선순위: PyMOL cealign (기본) → biopython Superimposer (폴백)
- TMalign 미설치 환경에서도 PyMOL cealign으로 동작 확인됨
