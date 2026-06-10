---
marp: true
theme: default
paginate: true
backgroundColor: "#ffffff"
---

# SST14-M 로컬 파이프라인 마이그레이션 보고

2026-03-30

---

## Before: NIM Cloud API 의존 구조

```
사용자 요청
    │
    ▼
AG_src / pipeline_local
    │
    ├─── nim_client.py ──► NVIDIA NGC API ──► OpenFold3
    │                                    ──► RFdiffusion
    │                                    ──► ProteinMPNN
    │                                    ──► ESMFold
    │                                    ──► DiffDock
    │                                    ──► Boltz2
    │                                    ──► MolMIM
    │
    └─── 인터넷 필수, API Key 필수, 과금 발생
```

**7개 외부 API 호출 — 문제점**

| 문제 | 영향 |
|------|------|
| 인터넷 의존 | 오프라인 실행 불가 |
| API 레이턴시 | 단계별 수초~수십초 지연 |
| 과금 | 대규모 실험 비용 제한 |
| NGC Key 관리 | 보안 부담 |

---

## After: pipeline_local 아키텍처

```
사용자 요청
    │
    ▼
pipeline_local/
    ├── orchestrator.py         (LocalModelRunner)
    ├── wrapper_scripts/        (8개 --input-json 래퍼)
    │     run_esmfold.py
    │     run_rfdiffusion.py
    │     run_proteinmpnn.py
    │     run_boltz.py
    │     run_diffpepbuilder.py
    │     run_openfold3.py
    │     run_genmol.py
    │     run_esm2.py
    └── envs/                   (9개 conda 환경)

로컬 GPU: H100 NVL × 4  (CUDA_VISIBLE_DEVICES=2)
LLM (Ollama): qwen3:8b/14b/32b/235b, deepseek-r1:70b,
              llama4:scout, + 8개 총 운용
```

---

## 마이그레이션 성과

| 모델 | Before (NIM) | After (Local) | 상태 |
|------|-------------|--------------|------|
| ESMFold | NGC API | `esm` conda env | 완료 |
| RFdiffusion | NGC API | `rfdiffusion` env | 완료 |
| ProteinMPNN | NGC API | `proteinmpnn` env | 완료 |
| Boltz2 | NGC API | `boltz` env | 완료 (MSA 수정) |
| DiffPepBuilder | NGC API | `diffpepbuilder` env | 환경 검증 중 |
| OpenFold3 | NGC API | `openfold3` env | 완료 |
| MolMIM/GenMol | NGC API | `genmol` env | 완료 |
| ESM-2 | NGC API | `esm2` env | 완료 |
| PyRosetta | 없음 | `pyrosetta` env | 신규 추가 |

**ESMFold 배치 성능: 128서열 기준 20분 → 70초 (17x)**

---

## 파이프라인 피드백 루프 구조

```
Iteration N
┌─────────────────────────────────────────────────────┐
│  Planner                                            │
│    │ Step01 (RFdiffusion backbone)                  │
│    │ Step03b (ProteinMPNN × 128)                    │
│    │ Step04 (ESMFold 배치 + pLDDT QC)               │
│    │ Step05 (Docking: Boltz2 / DiffPepBuilder)      │
│    │ Step06 (Rosetta ddG + relax)                   │
│    │ Step07 (Selectivity + ADMET)                   │
│    ▼                                                │
│  QC & Ranker ──► Reporter (rank_table.csv)          │
│                      │                              │
│                  Critic (실패 분석)                  │
│                      │                              │
└──────── 파라미터 변경 (최대 2개) ◄──────────────────┘

Iteration N+1 : 수정된 파라미터로 재실행
```

---

## 평가 기준: 4단계 Gate

```
후보 서열 128개
    │
    ▼ Gate 1: pLDDT ≥ 60          (구조 신뢰도)
    │         통과: ~29/128 (22.7%)
    ▼ Gate 2: Docking 상위 20%     (결합 가능성)
    │         현재: Step05 실패 → 미도달
    ▼ Gate 3: Rosetta ddG ≤ -5.0  (결합 에너지)
    │              clash ≤ 10      (입체 충돌)
    ▼ Gate 4: Selectivity margin ≤ -10.0
              (SSTR2 vs SSTR1/3/4/5 특이성)
```

| Gate | 메트릭 | 기준값 | 의미 |
|------|--------|--------|------|
| 1 | pLDDT | ≥ 60 | 구조 신뢰도 |
| 2 | dock_score | 상위 20% | 결합 가능성 |
| 3 | ddG / clash | ≤ -5.0 / ≤ 10 | 결합 에너지 |
| 4 | selectivity | ≤ -10.0 | 표적 특이성 |

---

## Critic 현재 — 5/18 메트릭만 참조

**보는 것 (5개)**

| 메트릭 | 실패 유형 | 대응 액션 |
|--------|---------|----------|
| mean_plddt | LOW_PLDDT | mpnn_temperature↓ |
| ddG + dock_score | GOOD_DOCK_BAD_DDG | hotspot_res 강화 |
| clash_count | HIGH_CLASH | relax_cycles↑ |
| selectivity | POOR_SELECTIVITY | hotspot 추가 |
| 서열 중복 | LOW_SEQUENCE_DIVERSITY | temperature↑ |

**안 보는 것 (13개)** interface_pLDDT, disulfide_intact, total_score,
constraint_violations, lddt, Boltz confidence, ADMET 독성,
half_life, WSM per-receptor, MW/pI/GRAVY, 프로테아제 사이트,
Boltz binding_affinity, QED 약물성

---

## Critic 확장 방향

```
현재 Critic (6 실패 유형)          확장 후 Critic (19 실패 유형)
─────────────────────────          ────────────────────────────
LOW_PLDDT                          LOW_PLDDT
GOOD_DOCK_BAD_DDG                  GOOD_DOCK_BAD_DDG
HIGH_CLASH                         HIGH_CLASH
POOR_SELECTIVITY                   POOR_SELECTIVITY
LOW_SEQUENCE_DIVERSITY             LOW_SEQUENCE_DIVERSITY
POCKET_SPECIFIC                    POCKET_SPECIFIC
                              +    WEAK_INTERFACE
                              +    BROKEN_DISULFIDE
                              +    UNSTABLE_STRUCTURE
                              +    GEOMETRIC_VIOLATION
                              +    FOLD_DEVIATION
                              +    LOW_DOCK_CONFIDENCE
                              +    ADMET_FAILURE         ◄ Gate 5
                              +    SHORT_HALFLIFE        ◄ Gate 5
                              +    SPECIFIC_OFFTARGET
                              +    PHYSICOCHEMICAL_OOB
                              +    PROTEASE_VULNERABLE
                              +    LOW_PREDICTED_AFFINITY
                              +    LOW_DRUGLIKENESS
```

---

## 긍정 피드백 루프 (신규 제안)

```
현재 (음성 피드백만)
  Critic (실패 분석) ──► Planner (파라미터 감소/증가)

제안 (양성 + 음성)
  Reporter.extract_success_patterns()   ◄── NEW
      │ rank_table.csv 상위 5개 서열 분석
      │ 위치별 아미노산 빈도 추출
      ▼
  SuccessPattern {position_preferences: {5: "Trp", 8: "Arg"}}
      │
      ▼
  orchestrator._last_success_patterns   ◄── NEW
      │
      ▼
  Planner ──► ProteinMPNN bias_AA_per_residue 업데이트
      │
      ▼
  "position 5 → Trp 편향" 서열 설계
      │
      ▼
  더 나은 ddG / pLDDT 후보 ──► 루프 반복
```

- 탐색 공간 "지향" (편향): 성공 패턴 방향으로 집중
- 탐색 공간 "축소": 비효율 영역 제거
- iteration 간 성공 정보 누적 가중치

---

## 도킹 이슈 현황

**Step05 전부 실패 → Gate 2/3/4 미도달**

| 엔진 | 에러 내용 | 원인 | 상태 |
|------|---------|------|------|
| Boltz2 | `Missing MSA's — use --use_msa_server` | 로컬 MSA DB 미구축 | `--use_msa_server` 추가 완료 |
| DiffPepBuilder | SSbuilder 환경 실패 | 모델 가중치/input key 불일치 | input key 수정 완료, 환경 재검증 필요 |

**영향**

```
Step04 (QC 29/128 통과)
    │
    ▼ Step05 ← 전부 실패 (Boltz2 + DiffPepBuilder)
    ✗
    Step06, Step07 미실행
    3 iteration 모두 동일 결과
```

---

## 도킹 해결 방안

**1. Boltz2 — `--use_msa_server` (수정 완료)**

```python
# run_boltz.py _run_boltz_predict()
cmd = [
    "boltz", "predict", input_yaml,
    "--out_dir", str(output_dir),
    "--override",
    "--use_msa_server",   # ColabFold MMseqs2 서버
]
print("[Boltz] 로컬 MSA DB 없음 → ColabFold MSA 서버 사용", ...)
```

**2. DiffPepBuilder — 환경 검증 필요**
- `receptor_pdb` / `peptide_seq` input key 수정 완료
- SSbuilder.py 실행 환경 재검증 예정

**3. 폴백: PyRosetta FlexPepDock**

```
Boltz2 실패 → DiffPepBuilder 실패
    → step05_docking.py 폴백 체인
    → PyRosetta FlexPepDock (nstruct=5, ~15분/29개)
```

---

## Selectivity 모듈 (신규)

**SSTR1~5 실험구조 기반 off-target 평가**

```
peptide 후보
    │
    ├──► SSTR2 도킹 (타겟)        dock_score_sstr2
    ├──► SSTR1 도킹 (off-target)  dock_score_sstr1
    ├──► SSTR3 도킹 (off-target)  dock_score_sstr3
    ├──► SSTR4 도킹 (off-target)  dock_score_sstr4
    └──► SSTR5 도킹 (off-target)  dock_score_sstr5
                │
                ▼
    WSM / MSM / SR 스코어링
    selectivity_margin = min(off_target) - sstr2_score
    Tier 분류: A(≤-15) / B(-15~-10) / C(>-10)
```

| 시각화 | 내용 |
|--------|------|
| Radar chart | 5개 수용체 결합 프로파일 |
| Heatmap | 후보별 × 수용체별 점수 |

API: `/api/selectivity/score`, `/api/selectivity/batch`, `/api/selectivity/radar`, `/api/selectivity/heatmap`, `/api/selectivity/tier`

---

## Silo B 벤치마크 결과

**3 iteration, 128서열/iter**

| 항목 | 결과 |
|------|------|
| ESMFold 배치 속도 | 70초 / 128서열 |
| GPU peak 메모리 | 14.3 GB |
| QC 통과 (Gate 1) | 29 / 128 (22.7%) |
| 도킹 (Gate 2) | 미도달 (Step05 전부 실패) |
| 총 소요 시간 (3 iter) | ~6분 (도킹 제외) |

**도킹 정상화 후 예상 1 iteration 소요 시간**

| 단계 | 예상 시간 |
|------|---------|
| ESMFold 배치 | ~70초 |
| 도킹 29개 (FlexPepDock 폴백) | ~15분 |
| Rosetta ddG + relax | ~20분 |
| Selectivity 5개 수용체 | ~10분 |
| **총 1 iteration** | **~47분** |

---

## 향후 로드맵

```
현재 (2026-03-30)
    Phase 1.5 완료: Silo B 3-iter 벤치마크
        │
        ▼
    Phase 1.6 (진행 예정)
        도킹 정상화 (Boltz MSA 서버 + FlexPepDock 폴백)
        파이프라인 3 iter E2E 완전 실행
        │
        ▼
    Phase 2 (LLM 테스트벤치)
        per-agent 모델 선택 (Planner/Critic/Reporter 분리)
        Ollama 8개 모델 성능 비교
        │
        ▼
    Phase 3 (문서화)
        API 문서, 사용 가이드
        │
        ▼
    Critic 확장 + 긍정 피드백 루프 (병행)
        19개 실패 유형 + Gate 5 ADMET
        Reporter → Planner 성공 패턴 경로
```

---

## Git 이력

| 커밋 | 메시지 | 날짜 |
|------|--------|------|
| `fd6cdf7` | docs: 2026-03-30 발표 자료 — 마이그레이션 현황 + 긍정 피드백 루프 분석 | 03-30 |
| `f5333a0` | feat: Silo B 3-iter 벤치마크 완료 + docking 버그 수정 3건 | 03-28 |
| `25cc809` | docs: 2026-03-27 진행보고서 — Phase 0~1.5 완료, 1.6부터 재개 예정 | 03-27 |
| `ec76ce4` | wip: Phase 1 진행 중 — Silo B 3iter 실행 전 저장 | 03-26 |
| `b436fc8` | fix: Phase 1 검증 — ESMFold 배치+이황화결합+pLDDT+CIF 수정 6건 | 03-25 |
| `51bb441` | fix: Phase 0 검증 — 모듈 테스트 버그 수정 2건 | 03-24 |
| `6350078` | feat: Off-target Selectivity 모듈 — 백엔드 + 프론트엔드 | 03-22 |
