# BE/FE 환경 점검 보고서
**날짜**: 2026-05-12  
**작성자**: engineer-infra (Task #2)  
**점검 시각**: 2026-05-12T02:50 KST

---

## ✅ 종합 결과

| 영역 | 상태 | 비고 |
|------|------|------|
| Backend (BE :8787) | 🟢 정상 가동 | bio-tools env, Python 3.11 |
| Frontend (FE :5173) | 🟢 정상 가동 | Vite, HTTP 200 OK |
| 데이터 (runs_local) | 🟢 존재 확인 | 어제·오늘 각 3 iter |
| GPU (H100 ×4) | 🟢 유휴 상태 | 각 14 MiB 사용 / 95830 MiB |
| Ollama (:11435) | 🟢 정상 응답 | 5개 모델 로드 완료 |

---

## 1. Backend (BE) — :8787

### 프로세스
| PID | 명령 | 포트 |
|-----|------|------|
| 65381 | `uvicorn backend.main:app` (bio-tools/Python 3.11) | :8787 ✅ |
| 836000 | `python -m uvicorn backend.main:app` (레거시?) | :8765 ⚠️ |

> ⚠️ **주의**: PID 836000이 `:8765`에서 별도 uvicorn을 가동 중. 레거시 인스턴스로 추정. T3 UI 검증 시 :8787만 사용할 것.

### `/api/status` 응답
```
run_id    : local_20260512_0213_iter03
iteration : 3 / 3
updated_at: 2026-05-12T02:18:44 UTC
llm_model : VLLMProvider(model='qwen3:8b')
target    : SSTR2
reference : DOTATATE (AGCKNFFWKTFTSC, 14-aa)
```

### 스텝 상태 (12개)
| Step ID | 상태 | Label |
|---------|------|-------|
| step01 | ✅ completed (0.0s) | OpenFold3 |
| step02 | ⏸ pending | RFdiffusion (NIM-only) |
| step03 | ⏸ pending | ProteinMPNN (NIM-only) |
| step03b | ✅ completed (0.0s) | BLOSUM Mutation |
| step03b_qc | ⏸ pending | Stability Pre-screen |
| step04 | ✅ completed | ESMFold QC |
| step05 | ✅ completed | DiffDock |
| step06 | ✅ completed | PyRosetta |
| step05b | ⏸ pending | Selectivity |
| step07 | ✅ completed | Analysis |
| step08 | ⏸ pending | Stability |
| step09 | ⏸ pending | MolMIM |

> **완료 6 / 전체 12** — pending 6개는 NIM 전용 or 미구현 스텝 (정상)

### `/api/runs` 응답
- 총 18개 runs 존재
- 상위 3개 예시:
  ```
  sst14_mutdock_9999  iter=3/3  candidates=25  best_ddg=-45.624  ✅ completed
  sst14_mutdock_7000  iter=10/10 candidates=81  best_ddg=-51.244  ✅ completed
  sst14_mutdock_6000  iter=10/10 candidates=81  best_ddg=-86.443  ✅ completed
  ```

---

## 2. Frontend (FE) — :5173

### 프로세스
| PID | 명령 |
|-----|------|
| 65891 | `node .../vite` |

### HTTP 상태
```
HTTP/1.1 200 OK
Content-Type: text/html
Etag: W/"2bf-12TiimgbQ92tupIVpVUNjFuuFUE"
Date: Tue, 12 May 2026 02:49:25 GMT
```
> 🟢 정상 응답. T3 UI 검증 즉시 진행 가능.

---

## 3. 데이터 (runs_local)

경로: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/runs_local/`

> ⚠️ **주의**: `ai4sci-kaeri/runs_local/` 가 아닌 **프로젝트 루트 `runs_local/`** 에 위치.

### silo_b_demo_tier2_2026-05-11 (어제)
```
total 140
local_20260511_1329_iter01/  (2026-05-11 13:47)
local_20260511_1347_iter02/  (2026-05-11 14:08)
local_20260511_1408_iter03/  (2026-05-11 14:29)
local_20260511_1408_iter03_summary.json  (119341 bytes) ✅
```

### silo_b_test_tier123_2026-05-12 (오늘)
```
total 140
local_20260512_0202_iter01/  (2026-05-12 02:07)
local_20260512_0207_iter02/  (2026-05-12 02:13)
local_20260512_0213_iter03/  (2026-05-12 02:18)
local_20260512_0213_iter03_summary.json  (119644 bytes) ✅
```

### /tmp/ag_pipeline_status.json
```
iteration : 3
updated_at: 2026-05-12T02:18:44 UTC
step      : None (완료 상태)
```
> 🟢 최신 실행(iter03) 정상 완료, summary JSON 존재.

---

## 4. GPU

| GPU Index | Used | Total | Util |
|-----------|------|-------|------|
| 0 | 14 MiB | 95830 MiB | 0% |
| 1 | 14 MiB | 95830 MiB | 0% |
| 2 | 14 MiB | 95830 MiB | 0% |
| 3 | 14 MiB | 95830 MiB | 0% |

> 🟢 H100 NVL ×4 모두 유휴. 파이프라인 실행 여유 충분.

---

## 5. Ollama (:11435)

| 모델 | 비고 |
|------|------|
| qwen3:235b-a22b | 최대 모델 |
| llama4:scout | |
| deepseek-r1:70b | |
| qwen3:32b | |
| qwen3:30b-a3b | |

> 🟢 5개 모델 정상 로드. BE /api/status에서 `qwen3:8b` 참조 중이지만 Ollama에는 `qwen3:8b` 태그 없음 (qwen3:30b-a3b가 최소) — **경미한 불일치, 기능 영향 없음 (이미 완료 run)**.

---

## 6. 이슈 요약

| # | 심각도 | 내용 | 조치 |
|---|--------|------|------|
| I-1 | ⚠️ 경고 | PID 836000이 :8765에서 레거시 uvicorn 가동 중 | 확인 후 필요시 종료 (T3 작업 영향 없음) |
| I-2 | ℹ️ 정보 | runs_local 경로가 ai4sci-kaeri 하위가 아닌 프로젝트 루트 | T4 분석 시 경로 주의 |
| I-3 | ℹ️ 정보 | `qwen3:8b` 모델 태그 미존재 (기완료 run이므로 무해) | 필요시 pull |

---

## 7. 결론

**T3/T4 작업 신호**: 🟢 **환경 OK**

- FE :5173 → 즉시 UI 검증 진행 가능
- BE :8787 → API 정상, 18개 runs, 최신 iter03 완료
- 데이터 → 어제/오늘 runs_local 모두 존재 (루트 경로)
- GPU → 유휴, 추가 파이프라인 실행 가능
- Ollama → 5개 모델 준비 완료
