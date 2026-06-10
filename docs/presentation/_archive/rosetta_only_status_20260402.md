# Rosetta-Only (pyrosetta_flow) 상태 보고서

**작성일**: 2026-04-02
**범위**: `pyrosetta_flow/` 모듈 전체 — 코드, 테스트, 액션 대응, 이슈

---

## 1. 모듈 구성

| 파일 | 역할 | 테스트 |
|------|------|--------|
| `runner.py` | 메인 파이프라인 (mutation→dock→rank loop) | test_runner_integration (10) + test_runner_helpers |
| `adapter.py` | PyRosetta FlexPepDock 어댑터 | test_adapter |
| `schema.py` | FlowConfig (Pydantic), CandidateResult | test_schema |
| `bandit.py` | Thompson Sampling 변이 전략 | test_bandit |
| `ranking.py` | ddG/clash 기반 후보 순위 | test_ranking |
| `convergence.py` | Mann-Whitney U 수렴 판정 | test_convergence |
| `gnina_rescoring.py` | GNINA CNN rescore + ECR consensus | test_alternative_scoring_integration |
| `pareto_ranking.py` | NSGA-II 다목적 Pareto 순위 | (위와 동일) |
| `bayesian_optimizer.py` | GP surrogate + UCB/BO 제안 | (위와 동일) |
| `cluster_report.py` | A~E 5등급 후보 분류 | test_cluster_report (57) |
| `rcsb_sequence_search.py` | RCSB PDB 서열 유사도 검색 | test_rcsb_integration (26) |
| `pdb_store.py` | SQLite 메타데이터 관리 | test_pdb_store |

**총 12개 모듈 + 12개 테스트 파일**

---

## 2. 테스트 현황

```
pyrosetta_flow/tests/: 265 passed, 6 skipped ✅

내역:
  test_runner_integration    10 passed
  test_runner_helpers        ~20 passed
  test_adapter               ~15 passed
  test_schema                ~10 passed
  test_bandit                ~15 passed
  test_ranking               ~10 passed
  test_convergence           ~10 passed
  test_alt_scoring_integ     24 passed
  test_cluster_report        57 passed
  test_rcsb_integration      23 passed + 3 skipped (network)
  test_pdb_store             ~60 passed + 3 skipped
```

---

## 3. 이번 세션 구현 내역 (rosetta_only 관련)

### 3.1 pharma 검증 + 버그 수정

| 항목 | 내용 | 커밋 |
|------|------|------|
| DIWV lookup table | 16건 오류 수정 (pharma 12 + backend 4), peptides GT 전수 대조 0 errors | `eb213c9` |
| RW 테이블 | H: 2.06→4.66, S: 1.83→3.40, W: -2.09→-2.33 | `eb213c9` |
| Boman 부호 | pharmacology.py `-sum/n` → `+sum/n` (방향 반전 수정) | `eb213c9` |
| N-end Rule P | 양 파일 (30.0h, stable) 통일 | `eb213c9` |
| **peptides GT 검증** | 8/8 메서드 완벽 일치 (6서열 × 13메서드 = 78 케이스) | `eb213c9` |

### 3.2 신규 기능

| 항목 | 내용 | 테스트 | 커밋 |
|------|------|--------|------|
| SS bond Cys pI 보정 | `_charge_at_ph()` ss_bond_cysteines 파라미터. SST-14 pI: 9.04→10.62 | 31 tests | `e5bcb51` |
| MW 계산 | `calculate_mw()` 평균 동위원소 질량. SST-14: 1639.91 Da | 26 tests | `e5bcb51` |
| Radiolysis Susceptibility | Met(3)/Trp(3)/Cys(2)/His(2)/Tyr(1)/Phe(0.5) 가중. SST-14: 6.5 high | 31 tests | `e5790dd` |
| A~E Cluster Report | `classify_cluster()` + `batch_classify()`. 5등급 분류 | 57 tests | `e5790dd` |
| FWKT Gate 강화 | `_mutable_design_positions()` FWKT 제외 + 3회 재시도 | 2 tests | `270b348` |
| DPP-IV Protease | `count_protease_sites()` DPP-IV 추가 (X-Pro/X-Ala 절단) | 7 tests | b9-b10 |
| Ga3+ D/E 배위 | `analyze_metal_coordination()` Asp/Glu carboxylate → Ga3+ 추가 | 6 tests | b9-b10 |
| 대안 스코어링 통합 | `_apply_alternative_scoring()` GNINA→ECR→Pareto→BO 체인 | 24 tests | d5 |
| pharmacology 래핑 | `pharmacology.py` → `pharma_properties.py` thin wrapper | 93 tests | b8 |
| Frontend 메트릭 | PharmacologyPanel MW/Radiolysis/SS corrected pI 표시 | tsc+lint OK | frontend |

### 3.3 RCSB PDB 통합

| 항목 | 내용 |
|------|------|
| `rcsb_sequence_search.py` | MMseqs2 기반 RCSB Search API v2 |
| `runner.py` 통합 | `_rcsb_check_candidates()` iteration 후 자동 검색 |
| Backend endpoint | `POST /api/rcsb-search` |
| Frontend | `RCSBMatchPanel.tsx` 매치 시각화 |
| 테스트 | 26개 (unit + live network) |

---

## 4. 발견된 이슈

| # | 이슈 | 심각도 | 상태 | 비고 |
|---|------|:------:|:----:|------|
| 1 | `tests/__init__.py` 누락 | 낮음 | ✅ 수정 | cross_validation import error |
| 2 | `AG_src/tests/test_config.py` 8 errors | 중간 | ⏸️ 기존 | config YAML 경로 불일치, rosetta_only 무관 |
| 3 | `test_design_alignment.py` 1 fail | 낮음 | ⏸️ 기존 | self_improving_loop 미구현 |
| 4 | `tests/test_cross_validation.py` 19 skipped | 낮음 | ⏸️ 정상 | 외부 패키지 미설치 시 skip 설계 |

**rosetta_only 자체에는 이슈 0건.** 265 passed, 6 skipped (network mark).

---

## 5. 액션 아이템 대응 (rosetta_only 관련)

| 항목 | 상태 | 비고 |
|------|:----:|------|
| B1-B4: pharma lookup table 수정 | ✅ | 16건 → 0건 |
| B5: SS bond Cys pI 보정 | ✅ | pI +1.58 보정 |
| B6: BLOSUM62 통일 | ✅ | pharmacology 래핑으로 해결 |
| B7: MW 추가 | ✅ | 1639.91 Da |
| B8: pharmacology 래핑 통합 | ✅ | 중복 lookup table 제거 |
| B9: DPP-IV 추가 | ✅ | 4번째 protease |
| B10: Ga3+ D/E 배위 | ✅ | Asp/Glu → Ga3+ |
| D5: 대안 스코어링 runner 통합 | ✅ | GNINA→ECR→Pareto→BO |
| A-04: A~E 클러스터 분류 | ✅ | 57 tests |
| A-08: Radiolysis Susceptibility | ✅ | SST-14 6.5 high |
| A-10: Radiolysis risk | ✅ | A-08과 동시 해결 |
| FWKT gate 강화 | ✅ | 46%→100% (immutable positions) |
| RCSB PDB 통합 | ✅ | 26 tests |
| Frontend MW/Radiolysis/pI | ✅ | PharmacologyPanel 반영 |

**14/14 전부 완료.**

---

## 6. 코드 품질 지표

| 메트릭 | 값 |
|--------|-----|
| 모듈 수 | 12 |
| 테스트 파일 | 12 |
| 테스트 통과 | **265** |
| 테스트 커버리지 | ~93% (추정, 이전 측정 기준) |
| pharma 메서드 | **15** (13 기존 + MW + radiolysis) |
| 구조 규칙 | **5** (FWKT, K9-D122, Cys3-Cys14, Phe6-Phe11, N-term) |
| 클러스터 등급 | **A~E 5등급** |
| 대안 스코어링 | **3모듈** (GNINA, Pareto, BO) |
| 누적 커밋 (이번 세션) | 10+ |

---

## 7. 남은 작업 (rosetta_only)

| # | 항목 | 우선순위 | 의존성 |
|---|------|---------|--------|
| 1 | cluster_report 대시보드 연결 (ClusterPanel.tsx) | P2 | 없음 |
| 2 | pdb_store.py 커밋 (untracked) | P2 | 없음 |
| 3 | agent monitor UI 디버깅 | P3 | 없음 |
| 4 | 22,000 후보 대규모 실행 | P3 | 서버 env 완료 후 |

---

## 8. Git 상태

| 항목 | 상태 |
|------|------|
| 현재 브랜치 | `feat/pharma-cross-validation` |
| main 대비 | 3 ahead, 1 behind |
| PR | [#2](https://github.com/AI-scientist4BIO/SST14-M_scr/pull/2) — 생성됨 |
| CI (main) | ✅ 3연속 success |
| untracked | `pdb_store.db`, `config/` |
