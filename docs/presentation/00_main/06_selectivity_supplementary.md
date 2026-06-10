> **형식**: 일반 마크다운 (Marp·슬라이드 비사용). 질의 응답용 보충 자료.

# SSTR1/3/4/5 Off-target Selectivity 분석 — 추가 보고 자료

2026-04-05 | AI4Sci Pipeline 개발팀


> **현재 상태**: 시스템 구축완료, 시뮬레이션 진행가능  
> 본 자료는 질의 시 추가 설명용으로 준비한 보충 자료입니다.


*참고 · 관련 부록: selectivity_docking_report.md*


## 수용체 구조 확보 현황

| 수용체 | PDB ID | 구조 유형 | CIF | PDB 변환 | 리간드 | 상태 |
|--------|--------|----------|:---:|:--------:|--------|:----:|
| SSTR1 | 9IK8 | Peptoid co-crystal | ✅ | ✅ | 004, DTR (NCAA) | **완료** |
| SSTR2 | 7XNA | Peptide co-crystal | ✅ | — | 타겟 (비교 기준) | **완료** |
| SSTR3 | 8XIR | Peptoid co-crystal | ✅ | ✅ | 004 (NCAA) | **전처리 필요** |
| SSTR4 | 7XMT | 소분자 co-crystal | ✅ | ✅ | I8B (소분자) | **완료** |
| SSTR5 | 8ZBJ | 실험 구조 | ✅ | ✅ | 미확인 | **완료** |


> 모든 CIF는 RCSB PDB에서 다운로드한 실험 구조. AlphaFold 예측 구조 대신 실험 구조를 사용하여 신뢰도 향상.  
> 회의(2026-03-09) 안건 8에서 AlphaFold를 제안했으나, 실험 구조 확보로 **업그레이드**.


*참고 · 경로: data/somatostatin_receptor/SSTR*_*.cif*


## 듀얼 모드 아키텍처

### Estimation 모드 (1차 스크리닝)

- SSTR2 ddG 기반 **노이즈 근사**
- 계산 시간: **즉시** (~ms)
- 후보 100개 × 4 receptor ≈ **1초**
- 구조 파일 불필요
- **용도**: 수백~수천 후보 1차 필터


----

### Production 모드 (최종 검증)

- PyRosetta **FlexPepDock** 물리 시뮬레이션
- 계산 시간: ~1분/receptor (nstruct=1)
- 후보 100개 × 4 receptor ≈ **13시간** (nstruct=20)
- 수용체 실험 구조 필수
- **용도**: 상위 10~50개 정밀 검증


> **워크플로우**: Estimation으로 대규모 필터링 → 상위 후보만 Production으로 물리 기반 검증


*참고 · 구현: AG_src/pipeline/step05b_selectivity.py, backend/selectivity_endpoints.py*


## 선택성 지표 체계

### 핵심 지표 4종

| 지표 | 정의 | 해석 |
|------|------|------|
| **delta_ddG** | SSTR2_ddG − offtarget_ddG | 음수 = SSTR2에 더 강하게 결합 (좋음) |
| **WSM** (Worst Selectivity Margin) | max(delta_ddG across all off-targets) | 가장 선택성이 낮은 케이스 |
| **MSM** (Mean Selectivity Margin) | mean(delta_ddG) | 평균 선택성 |
| **SR** (Selectivity Ratio) | exp(−delta_ddG / RT), RT=0.616 kcal/mol | 열역학적 선택성 비율 |

### Tier 판정 기준

| Tier | WSM 조건 | 의미 | 조치 |
|------|----------|------|------|
| **T3** | WSM ≤ −3.0 | 높은 선택성 | → Cluster B 후보 |
| **T2** | WSM ≤ −2.0 | 적정 선택성 (PASS) | → 합성 검토 |
| **T1** | WSM ≤ −1.5 | 경계 | → 추가 검증 필요 |
| **T0** | WSM > −1.5 | 선택성 부족 (FAIL) | → 탈락 |

> WSM/MSM/SR은 Estimation·Production 양 모드에서 동일하게 산출 (`compute_full_selectivity` 함수)


*참고 · 상세: 01_appendix/selectivity_docking_report.md §2.3*


## SST-14 Baseline 도킹 결과 (참고)

### Production 모드 시험 실행 (test_full_pipeline_20260402)

| 수용체 | ddG (REU) | 결합 여부 | 비고 |
|--------|:---------:|:--------:|------|
| SSTR1 (9IK8) | **−33.84** | ✅ 결합 | Peptoid 위치 기반 배치, 가장 정확 |
| SSTR3 (8XIR) | N/A | — | CIF fill_missing_atoms 에러 (전처리 필요) |
| SSTR4 (7XMT) | 0.0 | ❌ 비결합 | 소분자 리간드 구조, 펩타이드 pocket 미노출 |
| SSTR5 (8ZBJ) | 0.0 | ❌ 비결합 | 리간드 위치 정보 부족 → 표면 폴백 |


> **물리적 해석**: SST-14는 모든 SSTR 서브타입에 비선택적 결합이 알려져 있음. SSTR4/5의 비결합은 소분자 기반 결정 구조에서 펩타이드 결합 부위가 닫혀있는 conformational 문제로 추정. 변이체에서는 다른 결과가 나올 수 있음.


> 양수 ddG는 "결합 안 됨"을 의미하므로 0.0으로 클램프 처리. 도킹 결과 PDB: runs/pyrosetta_flow/test_full_pipeline_20260402/sst14_agentic_mutdock/ot_SSTR*.pdb


*참고 · REU = Rosetta Energy Unit. 상대 비교용 지표이며 절대 kcal/mol과 1:1 대응 아님.*


## 논의: 블라인드 도킹 vs 위치 지정 도킹

| 항목 | 현재 (블라인드) | 제안 (위치 지정) |
|------|---------------|-----------------|
| 방식 | 수용체 표면 전체 탐색 | 리간드 결합 부위 지정 후 도킹 |
| FlexPepDock | 초기 배치 랜덤 | **co-crystal 리간드 위치 기반 배치** |
| 정확도 | 낮음 (SSTR4/5에서 비결합) | 높음 (결합 부위 사전 정의) |
| 계산 시간 | 동일 | 동일 (초기 배치만 변경) |
| 근거 | — | SSTR1 도킹 성공 = peptoid 위치 기반 배치 |


> **논의 포인트**: FlexPepDock은 위치 지정 도킹이 가능합니다. 현재 SSTR1에서 -33.84 REU가 나온 것도 co-crystal peptoid 위치를 기반으로 30Å 외곽 배치한 덕분입니다. SSTR4/5에서 비결합인 것은 소분자 리간드 위치가 펩타이드와 다르기 때문이며, 위치 지정 전환 시 개선 가능합니다.


## 알려진 제한사항 및 향후 과제

| 항목 | 상태 | 대안/계획 |
|------|:----:|----------|
| SSTR3 CIF 로드 실패 | **미해결** | protein chain만 추출한 PDB 사전 생성 |
| SSTR4/5 도킹 부정확 | **부분** | **위치 지정 도킹 전환** 또는 homology modeling |
| FlexPepDock nstruct 부족 | 인지 | 현재 20, 논문 권장 ≥100 |
| 도킹 병렬화 미구현 | 인지 | subprocess CPU 코어 기반 병렬화 예정 |
| 블라인드 도킹 한계 | 인지 | **위치 지정 전환 논의 필요** |


> **핵심**: 시스템 인프라는 **구축 완료**. 위치 지정 도킹 전환과 nstruct 상향은 논의 후 즉시 적용 가능.


*참고 · 참고문헌: Raveh et al. (2011) PLoS ONE; London et al. (2011) NAR*

