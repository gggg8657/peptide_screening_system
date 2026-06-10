# Silo B 3-iteration 벤치마크 보고서

**날짜**: 2026-03-27
**환경**: H100 NVL ×4, CUDA_VISIBLE_DEVICES=2 (H100 GPU 2), conda: bio-tools
**설정**: Approach B (BLOSUM62 mutation), `--iterations 3`, `--llm-model qwen3:8b`
**Run IDs**: local_20260327_0339_iter01 ~ local_20260327_0352_iter03

---

## 실행 요약

| 항목 | 값 |
|---|---|
| 총 소요시간 | 1190.8s (19.8 min) |
| Iteration 수 | 3 (조기 종료: patience 2/2) |
| 수렴 여부 | False (ddG 개선 없음) |
| 최종 통과 후보 | 0 |

---

## Iteration별 결과

| Iteration | 변이 생성 | ESMFold QC 통과 | Docking 결과 | Rosetta ddG |
|---|---|---|---|---|
| Iter 1 | 128개 | 29/128 (22.7%) | 0 결과 | - |
| Iter 2 | 128개 | 29/128 (22.7%) | 0 결과 | - |
| Iter 3 | 128개 | 29/128 (22.7%) | 0 결과 | - |

---

## Step별 소요시간 (Iteration 1 기준)

| Step | 소요시간 | 비고 |
|---|---|---|
| Planner Agent | ~120s | LLM 타임아웃 → rule-based fallback |
| Step01 receptor | <1s | CIF 파싱 |
| Step03b BLOSUM62 | <1s | 44 single + 84 combo = 128 variants |
| Step04 ESMFold QC | 69.2s | 128 sequences 배치, pLDDT≥60 gate |
| Step05 Docking | 214.3s | DiffPepBuilder+Boltz 전부 실패 |
| **Iter 1 합계** | **~397s (6.6 min)** | |

**Iteration 2**: Step04=73.5s, Step05=208.3s → ~402s
**Iteration 3**: Step04=71.7s, Step05=193.4s → ~385s

---

## 리소스 사용량

### GPU VRAM (GPU 2)
| 단계 | VRAM | 활용률 |
|---|---|---|
| ESMFold 배치 (128 seq) | **14,341 MiB** | ~50-60% |
| Boltz 실행 시도 | 미미 (즉시 실패) | - |
| 아이들 | ~200 MiB | 0% |

### ESMFold 배치 성능
- 128 sequences / ~70s = **0.55s/sequence** (배치 모드)
- GPU 2 기준 VRAM peak: 14,341 MiB

---

## 버그 발견 및 수정

### 수정 완료
| 버그 | 파일 | 수정 내용 |
|---|---|---|
| DiffPepBuilder input JSON key mismatch | `step05_docking.py` | `"protein"` → `"receptor_pdb"`, `"ligand"` (PDB) → `"peptide_sequence"` (서열) |
| `run_boltz.py` FileNotFoundError 미처리 | `wrapper_scripts/run_boltz.py` | `FileNotFoundError`를 `RuntimeError`로 감싸 main() 에서 정상 처리 |
| 이황화결합 게이트 과다 필터링 | `config/gate_thresholds.yaml` | `disulfide: false` (ESMFold는 선형 펩타이드 예측 → 고리형 SS bond 모델링 불가) |

### 미해결 이슈

#### 1. Boltz MSA 필요 에러
```
RuntimeError: Missing MSA's in input and --use_msa_server flag not set.
```
- `boltz` conda env에는 설치되어 있으나 MSA 서버 연결 또는 사전 계산된 MSA 파일 필요
- **해결 방안**: `run_boltz.py`에 `--use_msa_server` 플래그 추가, 또는 MSA-free 모드 확인

#### 2. DiffPepBuilder SSbuilder 실행 실패
```
DiffPepBuilder 출력 PDB를 찾을 수 없음. ESMFold 폴백 시도...
```
- SSbuilder.py 내부 실행 실패 (모델 가중치 또는 환경 문제)
- **해결 방안**: `local_models/DiffPepBuilder/` 설치 상태 점검

#### 3. LLM 타임아웃
- qwen3:8b Ollama 모델이 매 iteration마다 120s 타임아웃
- **해결 방안**: Ollama 서버 재시작, 모델 preload, 또는 타임아웃 설정 조정

#### 4. Docking 엔진 0% 성공률
- DiffPepBuilder 실패 + Boltz MSA 에러 → 모든 후보 docking 결과 없음
- Rosetta 및 Selectivity 단계 미도달
- **해결 방안**: Boltz `--use_msa_server` 활성화 또는 Mock docking 모드 추가

---

## ESMFold QC 분석

**pLDDT 분포** (128개 변이 기준):
- pLDDT ≥ 60 통과: 29/128 (22.7%)
- pLDDT < 60 탈락: 99/128 (77.3%)
- 이황화결합 게이트: 비활성화 (ESMFold 한계)

**원인 분석**: 14-aa 단펩타이드의 ESMFold 예측 pLDDT는 일반적으로 낮음 (45-65 범위). 임계값 60.0은 적절하나, BLOSUM62 변이 적용 후 구조 안정성이 감소할 수 있음.

---

## 수렴 분석

```
Iter 1: best_ddG=0.00, n_passed=0 → patience 0/2
Iter 2: best_ddG=0.00, n_passed=0 → patience 1/2
Iter 3: best_ddG=0.00, n_passed=0 → patience 2/2 → 조기 종료
```

Docking 단계 실패로 Rosetta ddG 미계산 → 개선 불가 → 조기 종료.

---

## 결론 및 권장사항

### 즉시 조치 필요
1. **Boltz MSA 문제 해결**: `--use_msa_server` 플래그 또는 로컬 MSA 제공
2. **DiffPepBuilder 설치 점검**: SSbuilder.py 의존성 확인

### 향후 개선
3. **Planner LLM 타임아웃**: Ollama 연결 안정화 (120s → 30s 타임아웃 권장)
4. **Docking mock 모드**: 도킹 엔진 실패 시 순위 기반 mock score 사용하여 Rosetta 단계까지 도달 가능하게 설정
5. **이황화결합 검사**: ESMFold 단계가 아닌 Rosetta 정제 단계 이후로 이동

### 성공적으로 검증된 항목
- ESMFold 배치 모드: **128 seq / 70s = 0.55s/seq** (정상 동작)
- BLOSUM62 변이 생성: **128 variants / <1s** (정상 동작)
- Orchestrator 3 iteration 루프: 정상 완료
- Checkpoint 저장/조기종료 로직: 정상 동작
- GPU 2 격리 실행: 정상 (peak 14,341 MiB)
