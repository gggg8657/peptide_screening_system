# 무한 발굴 엔진 (Continuous Discovery Engine) — 사용법

2026-06-10 구축. 기존 단발 `run_pyrosetta_flow` 위에 epoch 루프를 씌워 **STOP 파일이
생길 때까지 무한히 SSTR2-선택성 후보를 발굴**한다. run 간 학습은 디스크에 누적된다.

## 핵심 개념

| 축 | 영속 파일 | 역할 |
|----|----------|------|
| 서열 dedup + bandit | `runs/pyrosetta_flow/experiment_log.jsonl` | 시도한 서열 재생성 회피, 위치 탐색 warm-start (기존) |
| **선택성(Δmargin)** | `runs/pyrosetta_flow/global_selectivity_leaderboard.json` | 역대 Δmargin best, 도킹한 서열 dedup, in-loop warm-start (신규) |
| 진행 상황 | `runs/pyrosetta_flow/discovery_status.json` | epoch·역대 best·통과 후보 수·다양성 레벨 (모니터링용) |

- **Δmargin = margin − native_margin(+13.37)** — home-advantage 보정. >0 = native SST-14 초과 선택성.
- **통과(passing)** = Δmargin>0 & ΔG≤−15 & 독성≤native(hc50). 오늘 GOAL 의 엄격 기준.

## 실행

```bash
ENV=~/miniforge3/envs/bio-tools/bin/python
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

# 무한 (STOP 파일로 정지)
$ENV scripts/run_continuous_discovery.py \
    --input data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb \
    --n-candidates 8 --max-iterations 4 --top-k 5 --selectivity-max-per-iter 2

# 테스트 (2 epoch 만)
$ENV scripts/run_continuous_discovery.py --input <pdb> --max-epochs 2 \
    --n-candidates 4 --max-iterations 1
```

## 사람이 조절하는 법 (재시작 불필요)

### ① 정지 — STOP 파일
```bash
touch _workspace/STOP_DISCOVERY      # 현재 epoch 마치고 graceful 종료
rm _workspace/STOP_DISCOVERY         # 다음 실행 전 반드시 삭제
```

### ② knobs 조절 — `_workspace/discovery_control.json`
매 epoch **시작 시 다시 읽힌다**. 편집만 하면 다음 epoch부터 반영.

| 키 | 의미 | 기본 |
|----|------|------|
| `n_candidates` | epoch 당 변이 후보 수 | 8 |
| `max_iterations` | epoch 당 agentic iteration | 4 |
| `selectivity_max_per_iter` | iteration 당 선택성 도킹 상한(비용) | 2 |
| `rosetta_ddg_max` | ddG 게이트 | −15 |
| `patience` | 정체 판정 epoch 수 (다양성 탈출) | 3 |
| `base_mutations` / `max_mutations_cap` | 변이 다양성 하한/상한 | 3 / 6 |
| `target_pass_count` / `stop_on_target` | 통과 N건 도달 시 자동 정지 | 3 / false |

> 화이트리스트 필드만 반영(`template_pdb` 등 구조적 필드는 무시) — 안전.

## 작동 원리

```
epoch 루프 (STOP 파일까지):
  1. control 파일 재로드 → knobs 반영
  2. 글로벌 리더보드 warm-start: 역대 도킹 서열 dedup + 게이트 기준선 적재
  3. seed_base = base + epoch*1000  (탐색 영역 이동)
  4. 다양성 정책: 역대 best Δ 가 patience epoch 정체 → max_random_mutations↑ (local optimum 탈출)
  5. run_pyrosetta_flow 1회 실행 (in-loop 선택성 ON)
  6. 측정 결과 → 글로벌 리더보드 누적·영속
  7. status 파일 갱신 → 다음 epoch
```

- **epoch 실패는 루프를 죽이지 않는다** (continue + status 에 error 기록).
- 수렴 시 종료가 아니라 **다양성 주입으로 계속 탐색** (무한 발굴의 핵심).

## 모니터링
```bash
cat runs/pyrosetta_flow/discovery_status.json | python -m json.tool   # 실시간 진행
# global_best_delta_margin, passing_count, diversity_level, top[], history[]
```

## 현재 상태 (부트스트랩)
- 글로벌 리더보드는 2026-06-10 in-loop run 8후보로 초기화됨.
- 역대 best: **LGCKFFFWKTFMSC Δ=+0.077** (native 간신히 초과, 단 독성↑).
- 통과(엄격 기준) 후보: **0건** — 진짜 블로커는 선택성. 엔진을 계속 돌려 Δmargin>0 & 비독성 후보를 누적 발굴하는 것이 목표.
