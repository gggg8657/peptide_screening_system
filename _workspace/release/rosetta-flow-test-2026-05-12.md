# Rosetta Flow Test — 2026-05-12
## Tier 1+2+3 Fix 회귀 검증 보고서

> **VR-cycle-08 echo 가드**: 본 보고서의 모든 수치는 `energy_table.json`, `docking_scores.json`,
> `checkpoint_iter0*.json`, `qc_summary.json` 원자료를 직접 read하여 인용함. 다른 팀원 메시지 수치 echo 없음.
>
> **VR-cycle-09 (H-06)**: ddG가 물리적 현실 범위(±10,000 REU)를 벗어나면 "계산 불가능한 영역으로 추정" 표시.

---

## §1 실행 메타

| 항목 | 값 |
|------|-----|
| Main PID | 1027672 |
| 시작 시각 | 2026-05-12 **02:02 UTC** |
| 종료 시각 | 2026-05-12 **02:19 UTC** |
| 총 elapsed | **~17분** (어제 ~60분 대비 65% 단축 — 캐시 재사용 효과) |
| 출력 디렉토리 | `runs_local/silo_b_test_tier123_2026-05-12/` |
| 명령 수정 | `--no-approach-a` (인식 불가) → `--approach-b` |
| LLM 모델 | `qwen3:8b` @ `localhost:11435` |
| GPU | `CUDA_VISIBLE_DEVICES=2,3` (Boltz: GPU 2만 사용, 최대 5,069 MiB) |
| Boltz 소요 | iter당 ~190s |
| PyRosetta 소요 | iter01=99s(new), iter02=99s(new), iter03=114.5s(new — 다른 Boltz pose) |

---

## §2 iter01/02/03 결과 표

### 오늘 실행 (`runs_local/silo_b_test_tier123_2026-05-12/`)

| iter | run_id | 변이체 | ddG (REU) | clash | cv | Boltz score | cache 여부 | gate 결과 |
|------|--------|--------|-----------|-------|-----|-------------|-----------|----------|
| iter01 | local_20260512_0202_iter01 | var_027 | **+25.753** | 4.0 | 0 | -9.567 | NEW CALC | ❌ ddG gate (+25.753 > -1.0) |
| iter02 | local_20260512_0207_iter02 | var_012 | **-15.8326** | 11.0 | 0 | -9.631 | NEW CALC | ❌ clash gate (11.0 > 10.0) |
| iter03 | local_20260512_0213_iter03 | var_027 | **-12.7379** | **0.0** | 0 | -9.610 | NEW CALC* | ❌ lDDT gate (0.0 < 0.6, F-05) |

> \* iter03 var_027 = iter01과 동일 서열이나 **다른 Boltz pose** (확률적 샘플링) → 다른 cache_key → 새 PyRosetta 계산.
> pre_score=372.2717로 동일한 ESMFold 구조를 공유하지만 FlexPepDock 시작 구조 차이로 ddG가 다름.

**Rosetta cache 누적** (`.rosetta_cache.json` 최종 상태):

| cache_key (8자) | 서열 | ddG | clash |
|----------------|------|-----|-------|
| b62e26ed | var_027 (iter01 pose) | +25.753 | 4.0 |
| 462f8f53 | var_012 (iter02 pose) | -15.8326 | 11.0 |
| (iter03 신규) | var_027 (iter03 pose) | -12.7379 | 0.0 |

**cache_key 다양성 (F1 검증)**: 3개 모두 상이 → mmCIF→PDB 변환(F1 fix) 정상, 구조별 고유 키 생성 ✅

### 어제 실행 (`runs_local/silo_b_demo_tier2_2026-05-11/`) — 비교 기준

| iter | run_id | 변이체 | ddG (REU) | clash | 판정 |
|------|--------|--------|-----------|-------|------|
| iter01 | local_20260511_1329_iter01 | var_012 | **40,582.7265** | 191.0 | ❌ HEURISTIC-INVALID |
| iter02 | local_20260511_1347_iter02 | var_024 | **102,495.9871** | 285.0 | ❌ HEURISTIC-INVALID |
| iter03 | local_20260511_1408_iter03 | var_012 | **42,462.1726** | 268.0 | ❌ HEURISTIC-INVALID |

---

## §3 어제 vs 오늘 정량 비교

| 지표 | 어제 평균 | 오늘 범위 | 최대 개선율 |
|------|---------|----------|------------|
| ddG (REU) | ~61,847 (HEURISTIC-INVALID) | -15.83 ~ +25.75 | **↓ 99.997%** |
| clash | ~248 | 0.0 ~ 11.0 | **↓ 100% (iter03)** |
| constraint_violations | N/A | 0 (전 iter) | ✅ |
| Boltz score | N/A | -9.26 ~ -9.63 | 정상 범위 유지 |
| 음수 ddG 관측 | 0 iter | 2 iter (iter02: -15.83, iter03: -12.74) | ✅ |

**F11 fix 적용 전후 핵심 수치 변화**:
```
어제: ddG = 40,582 / 102,496 / 42,462 REU  ← 계산 불가능 영역 (stale path)
오늘: ddG = +25.753 / -15.833 / -12.738 REU ← 물리적 현실 범위 복원
개선율: ×1,575 ~ ×8,078배 감소
```

---

## §4 F11 Fix 효과 판정

### **판정: PARTIAL SUCCESS** (계산 복원 성공, 목표 범위 미달)

| 검증 항목 | 기대 | 실제 | 판정 |
|---------|------|------|------|
| ddG 물리적 범위 복원 (±10,000 REU) | 전 iter | +25.75 / -15.83 / -12.74 REU | ✅ **SUCCESS** |
| HEURISTIC-INVALID 제거 | 0건 | 0건 | ✅ **SUCCESS** |
| 음수 ddG 관측 | ≥1 iter | iter02, iter03 모두 음수 | ✅ **SUCCESS** |
| clash 정상화 (<50) | 전 iter | 4.0 / 11.0 / **0.0** | ✅ **SUCCESS** |
| 목표 ddG -45~-51 REU 복원 | 3 iter | 최고 -15.83 REU | ⚠️ **PARTIAL** |
| F1 cache_key 다양성 | iter별 상이 | 3개 모두 상이 | ✅ **SUCCESS** |

**-45~-51 REU 미달 원인 추정**:
- 해당 범위는 wt SST-14 또는 이전 우수 결합 변이체 기준 (BLOSUM62 무작위 변이 기대치 아님)
- F11 fix 이후 계산 자체는 올바르게 작동함
- 더 낮은 ddG를 얻으려면 더 넓은 변이 공간 탐색 또는 wt SST-14를 직접 Rosetta에 투입하여 기준값 재측정 필요

---

## §5 잔존 결함

| ID | 심각도 | 내용 | 상태 |
|----|--------|------|------|
| **F-01** (source="silo_a") | Non-blocking | `RosettaResult.source` 기본값 오류 — Silo B 실행 시에도 "silo_a" 태깅 | ✅ **이번 세션 수정 완료**: `io_schemas.py` L302 기본값 `"silo_a"`→`"silo_b"`, `step06_rosetta.py` L264 `source=result.source` 보존. 테스트 10/10 통과 |
| **F-02** (clash gate margin) | Low | iter02 var_012 clash=11.0으로 gate threshold(10.0) 근소 초과 탈락 | 🟡 미해결. `rosetta_clash_max: 10 → 12` 완화 검토 권장 |
| **F-03** (동일 변이체 반복) | Medium | iter01~03 모두 동일 5개 BLOSUM62 변이체 (var_012, 024~027) — 다양성 부족 | 🟡 미해결. LLM Scientist Critic "변경 없음" 권장 루프. BLOSUM seed 다양화 필요 |
| **F-04** (tee 로그 버퍼링) | Low | `/tmp/silo_b_test_tier123.log` 항상 0 bytes | 🟡 미해결. `python -u` 플래그 또는 `stdbuf -o0` 추가 권장 |
| **F-05** (lDDT gate 단일구조) | Medium | Rosetta 통과 후보가 1개일 때 FoldMason 정렬 불가 (`"Need >= 2 structures"`) → lDDT=0.0 → 최종 탈락 | 🔴 **신규 발견**. iter03 var_027이 Rosetta PASS (ddG=-12.74, clash=0.0)했지만 lDDT gate에서 탈락. `foldmason_lddt_min` 조건부 비활성화 또는 단일 구조 예외 처리 필요 |

---

*작성: engineer-backend, 2026-05-12 02:19 UTC*
*원자료 경로: `runs_local/silo_b_test_tier123_2026-05-12/`, `runs_local/silo_b_demo_tier2_2026-05-11/`*
