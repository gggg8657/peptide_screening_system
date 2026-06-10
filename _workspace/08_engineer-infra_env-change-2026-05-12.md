# 환경 변경 메모 — archives Boltz 재평가 인프라

**날짜**: 2026-05-12  
**작성자**: engineer-infra  
**작업 ID**: T3

---

## 변경 내용

### 신규 스크립트 추가

| 파일 | 설명 |
|------|------|
| `runs_local/archives_boltz_eval/run_full_eval.py` | 4-GPU 병렬 재평가 메인 스크립트 |
| `runs_local/archives_boltz_eval/test_small.py` | 25페어 mini-test (검증용) |
| `runs_local/archives_boltz_eval/README.md` | 사용법 + GPU 요구사항 |

### 새로운 디렉토리

```
runs_local/archives_boltz_eval/    # 신규 생성
```

---

## 환경 의존성

| 의존성 | 상태 | 비고 |
|--------|------|------|
| `conda env boltz` | ✅ 기존 사용 | boltz 2.2.1, CUDA 11.8+ |
| `runs_local/selectivity_demo_20260511/alphafold_receptors/` | ✅ 5개 MSA | SSTR1-5 |
| `runs/pyrosetta_flow/archives/*_dashboard.json` | ✅ 11개 파일 | 539 후보 |
| H100 NVL ×4 | ✅ GPU 0-3 가용 | 95GB/ea |

---

## 검증 명령

```bash
# 1. dry-run (후보 추출 확인)
python runs_local/archives_boltz_eval/run_full_eval.py --dry-run

# 예상 출력:
#   archives unique 서열: 333
#   top10 제외 후:       323
#   총 페어:             1615 (323 × 5 SSTR)
#   GPU:                 4대 (ids=[0, 1, 2, 3])
#   예상 시간:           ~3h 21m (30초/페어, 4GPU 병렬 기준)

# 2. mini-test (파이프라인 검증)
python runs_local/archives_boltz_eval/test_small.py --gpu 3

# 3. 본격 실행 (사용자 GPU 확인 후)
python runs_local/archives_boltz_eval/run_full_eval.py --n-gpus 4
```

---

## 팀원 영향도

| 팀원 | 영향 |
|------|------|
| engineer-backend | 없음 (신규 디렉토리, 기존 파이프라인 무관) |
| reviewer-science | all_results.json 출력 → selectivity 분석 입력으로 활용 가능 |
| 사용자 | GPU 0-3 점유 시 다른 작업 병렬 실행 주의 (3h 21m) |

---

## 주의사항

1. **본격 실행 전 GPU 가용성 확인 필수** — `nvidia-smi` 로 다른 작업 없음 확인
2. **중단 시 재시작**: `--resume` 플래그 사용 (partial_*.json 기반 자동 SKIP)
3. **GPU 0-3 모두 점유**: 다른 팀원이 GPU 사용 중이면 `--gpu-ids` 로 일부만 사용 가능

---

## 관련 파일 변경 없음

기존 파이프라인 (`pipeline_local/`, `runs_local/selectivity_demo_20260511/`) 수정 없음.  
신규 디렉토리 독립적으로 운영.
