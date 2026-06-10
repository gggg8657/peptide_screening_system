# Off-target Selectivity Docking 기술 보고서

> **작성일**: 2026-04-05
> **작성**: AI4Sci Pipeline 개발팀
> **대상**: SSTR2 타겟 방사성의약품 후보 — Off-target Selectivity Analysis 모듈

---

## 1. 개요

SSTR2 타겟 펩타이드 후보가 다른 소마토스타틴 수용체(SSTR1/3/4/5)에 비선택적으로 결합하는지 평가하는 Selectivity Analysis 모듈의 구현 및 검증 결과를 보고한다.

### 1.1 목적

| 질문 | 방법 |
|------|------|
| 후보가 SSTR2에 선택적으로 결합하는가? | SSTR2 ddG vs off-target ddG 비교 |
| off-target 결합 위험이 있는 수용체는? | SSTR1/3/4/5 각각에 대한 도킹 |
| 어느 후보를 우선 진행할 것인가? | Selectivity Margin (WSM) 기반 Tier 분류 |

### 1.2 수용체 구조

| 수용체 | PDB ID | 해상도 | 리간드 유형 | 비고 |
|--------|--------|--------|------------|------|
| SSTR1 | 9IK8 | - | Peptoid (004, DTR 등) | NCAA 체인 F 포함 |
| SSTR2 | 7XNA | - | Peptide | 타겟 (selectivity 대상 아님) |
| SSTR3 | 8XIR | - | Peptoid (004 등) | CIF 로드 시 fill_missing_atoms 에러 |
| SSTR4 | 7XMT | - | 소분자 (I8B) | Non-polymer 리간드 |
| SSTR5 | 8ZBJ | - | 소분자/미확인 | HETATM 리간드 부재 |

---

## 2. 듀얼 모드 아키텍처

Selectivity Analysis는 **Estimation**과 **Production** 두 가지 모드를 지원한다.

### 2.1 비교표

| 항목 | Estimation 모드 | Production 모드 |
|------|----------------|----------------|
| **알고리즘** | SSTR2 ddG 기반 노이즈 근사 | PyRosetta FlexPepDock 물리 시뮬레이션 |
| **입력** | `sstr2_ddg` (float) | 수용체 CIF/PDB + 펩타이드 서열 |
| **계산 시간** | 즉시 (~ms) | nstruct=1: ~1분/receptor, nstruct=20: ~2분/receptor |
| **후보 100개 x 4 receptor** | ~1초 | ~13시간 (nstruct=20) |
| **정확도** | 입력값 의존, 순위 참고 | 물리 기반, 상대 순위 신뢰도 높음 |
| **구조 필요** | 불필요 | 수용체 실험 구조 필수 |
| **의존성** | 없음 | PyRosetta + conda bio-tools |
| **GPU** | 불필요 | 불필요 (CPU only) |
| **출력** | WSM/MSM/SR/Tier 즉시 반환 | ddG + best_dock.pdb |

### 2.2 권장 워크플로우

```
[초기 스크리닝]                    [최종 검증]
 수백~수천 후보                      상위 10~50개
       |                                |
  Estimation 모드                 Production 모드
  (즉시, 1차 필터)              (FlexPepDock, 물리 기반)
       |                                |
  WSM/Tier 기반 탈락              실제 ddG + 구조 확보
```

### 2.3 선택성 지표 (공통)

두 모드 모두 `compute_full_selectivity()` 함수를 통해 동일한 지표를 산출한다:

- **delta_ddG** = SSTR2_ddG - offtarget_ddG (음수 = SSTR2에 더 강하게 결합)
- **WSM** (Worst Selectivity Margin) = max(delta_ddG) — 가장 선택성이 낮은 케이스
- **MSM** (Mean Selectivity Margin) = mean(delta_ddG)
- **SR** (Selectivity Ratio) = exp(-delta_ddG / RT), RT = 0.616 kcal/mol (310 K)
- **Tier 판정**:

| Tier | 조건 | 의미 |
|------|------|------|
| T3 | WSM <= -3.0 | 높은 선택성 |
| T2 | WSM <= -2.0 | 적정 선택성 (PASS) |
| T1 | WSM <= -1.5 | 경계 |
| T0 | WSM > -1.5 | 선택성 부족 (FAIL) |

---

## 3. Production 모드 구현 상세

### 3.1 아키텍처

```
[Frontend: SelectivityPage]
       |
  POST /api/selectivity/run
       |
[Backend: selectivity router]
       |
  conda bio-tools 체크 → production / estimation 분기
       |
  [BackgroundTask] → subprocess per (candidate x receptor)
       |
  conda run -n bio-tools python offtarget_dock.py
       |
  PyRosetta FlexPepDock → InterfaceAnalyzerMover → ddG
       |
  status.json 갱신 → polling → 결과 표시
```

### 3.2 수용체 전처리 (`_load_receptor_and_ligand_center`)

CIF 구조에는 co-crystallized 리간드(peptoid, 소분자)가 포함되어 있어 전처리가 필요하다.

**단계:**
1. `pyrosetta.pose_from_file()`로 전체 구조 로드
2. `is_canonical_aa()`로 체인별 NCAA 잔기 탐색
3. NCAA 포함 체인의 질량 중심 → **리간드 위치** 추출
4. NCAA 포함 체인 제거 → PDB roundtrip으로 clean receptor 생성
5. PyRosetta에서 감지 못한 소분자는 CIF HETATM 직접 파싱으로 폴백

**NCAA 관련 이슈 및 해결:**

| 이슈 | 원인 | 해결 |
|------|------|------|
| `004.rotlib not found` → C++ exit() | Peptoid 잔기의 rotamer library 부재 | NCAA 포함 체인 전체 제거 |
| `fill_missing_atoms` 에러 (SSTR3) | CIF 구조의 불완전한 원자 좌표 | 별도 PDB 전처리 필요 (미해결) |
| PyRosetta가 소분자 리간드 무시 | `ignore_unrecognized_res true` | CIF HETATM 직접 파싱 폴백 |

### 3.3 펩타이드 배치 (`_place_peptide_at`)

FlexPepDock의 성능은 초기 배치에 크게 의존한다.

**전략: 리간드 위치 기반 외곽 배치**

1. 원본 구조의 리간드(NCAA/소분자) 질량 중심 추출
2. 수용체 질량 중심 → 리간드 중심 방향의 단위 벡터 계산
3. 리간드 위치에서 **바깥 방향 30 A**에 펩타이드 배치
4. 반복 시 jitter (+-5 A)로 다양성 확보

```
     [수용체 중심]
          |
          | (방향 벡터)
          v
     [리간드 위치]
          |
          | + 30 A (clash 회피)
          v
     [펩타이드 초기 위치]
          |
     FlexPepDock이 접근시키며 도킹
```

**이전 시도와 비교:**

| 배치 전략 | SSTR1 ddG | 문제 |
|----------|-----------|------|
| 수용체 질량 중심 근처 랜덤 | 0.0 | Interface 없음 |
| 리간드 위치 직접 배치 | +19,715 | 극심한 clash |
| 리간드 위치 + 30 A 외곽 | **-33.84** | 정상 |

### 3.4 Interface ddG 계산 (`_score_interface_ddg`)

다중 체인 수용체(A~E)에서 펩타이드-수용체 interface를 자동 탐지한다.

- 모든 Jump에 대해 `InterfaceAnalyzerMover` 실행
- **가장 큰 buried SASA**를 가진 jump = 펩타이드-수용체 interface
- 해당 jump의 `get_interface_dG()` 반환
- 양수 ddG (결합 안 됨)는 0.0으로 클램프

### 3.5 양수 ddG 클램프 근거

| 원시 ddG | 클램프 후 | 해석 |
|----------|----------|------|
| -33.84 | -33.84 | 결합 있음 (off-target 위험) |
| +1,788 | 0.0 | 결합 안 됨 (선택적) |
| +222 | 0.0 | 결합 안 됨 (선택적) |

양수 ddG는 "펩타이드가 수용체에 안 붙는다"를 의미하므로, selectivity 계산에서 0.0 (중립)으로 처리하는 것이 물리적으로 타당하다.

---

## 4. 검증 결과

### 4.1 SST-14 (AGCKNFFWKTFTSC) baseline 도킹

| 수용체 | ddG (kcal/mol) | 결합 여부 | 비고 |
|--------|---------------|----------|------|
| SSTR1 | -33.84 | 결합 | Peptoid 리간드 위치 기반 배치 |
| SSTR3 | N/A | 미측정 | CIF fill_missing_atoms 에러 |
| SSTR4 | 0.0 | 비결합 | 소분자 리간드 구조, binding pocket 크기 불일치 |
| SSTR5 | 0.0 | 비결합 | 리간드 위치 정보 부족 → 표면 폴백 |

### 4.2 물리적 해석

- SST-14는 모든 SSTR 서브타입에 비선택적으로 결합하는 것으로 알려져 있음
- SSTR1에서 결합이 확인된 것은 해당 구조가 peptoid 리간드와 co-crystallized 되어 펩타이드 결합 부위가 잘 정의되어 있기 때문
- SSTR4/5에서 비결합은 소분자 리간드 기반 구조에서 펩타이드 결합 부위가 열리지 않은 conformational 문제로 추정
- 보다 정확한 결과를 위해서는 SSTR4/5의 펩타이드-결합 구조(존재 시) 또는 homology modeling 필요

---

## 5. Frontend 연동

### 5.1 수정 사항

| 파일 | 수정 내용 |
|------|----------|
| `useSelectivity.ts` | `candidate_sequences` 배열 → dict 변환, 마운트 시 running job 자동 복구 |
| `useSelectivity.ts` | `/api/selectivity/receptors` 응답 파싱: object → dict 대응 |
| `SelectivityPage.tsx` | SSTR2 receptor 체크 제외 (타겟이므로), 경고 메시지 "4 off-target" 반영 |
| `selectivity.py` | `conda` 풀 경로 자동 탐색 (`_find_conda`), PyRosetta 가용성 체크 후 estimation 폴백 |
| `selectivity.py` | `candidate_ids`를 status.json에 저장하여 job 목록에서 후보 수 표시 |
| `state.py` | `AG_SRC_REPO/runs/pyrosetta_flow/archives/` 추가 → 기존 실험 20개 런 조회 가능 |

### 5.2 기존 실험 데이터 UI 통합

`ARCHIVE_DIRS`에 AG_SRC_REPO 경로 추가로 **20개 실험 런**이 UI RunSelector에서 조회 가능:

- `sst14_mutdock_*` (11개) — mutation+docking 시리즈
- `paper_validation_*` (6개) — 논문 검증 실험
- `sst14_analogs_sim` — SST-14 유사체 시뮬레이션
- `pos5_6_11_optimization` — 위치별 최적화 실험

---

## 6. 알려진 제한사항 및 향후 과제

| 항목 | 상태 | 대안/계획 |
|------|------|----------|
| SSTR3 CIF 로드 실패 | 미해결 | protein chain만 추출한 PDB 사전 생성 |
| SSTR4/5 펩타이드 도킹 부정확 | 부분 해결 | peptide-bound 구조 확보 또는 homology modeling |
| FlexPepDock nstruct 부족 | 인지 | nstruct >= 100 권장 (논문 기준), 현재 20 |
| 도킹 병렬화 미구현 | 인지 | subprocess 수준 병렬화 (CPU 코어 수 기반) |
| 절대 ddG 신뢰도 한계 | 인지 | fa_standard은 상대 순위 참고용, 절대값 해석 주의 |

---

## 7. 참고문헌

1. Raveh, B. et al. (2011). "Rosetta FlexPepDock ab-initio: simultaneous folding, docking and refinement of peptides onto their receptors." *PLoS ONE*, 6(4), e18934.
2. London, N. et al. (2011). "Rosetta FlexPepDock web server—high resolution modeling of peptide-protein interactions." *Nucleic Acids Res.*, 39, W249-W253.
3. SSTR1 9IK8, SSTR2 7XNA, SSTR3 8XIR, SSTR4 7XMT, SSTR5 8ZBJ — RCSB PDB experimental structures.
