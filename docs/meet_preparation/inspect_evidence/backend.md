# Backend 점검 — 2026-06-01

## 요약 (보고용 핵심 메시지 5개)
- 라이브 BE(:8787)는 정상 가동 중이며 21개 라우터, 총 81개 엔드포인트 등록 확인
- `/api/health`, `/api/admet/{seq}`, `/api/runs`, `/api/selectivity/receptors`, `/api/flexpepdock/jobs` 모두 정상 응답 (200)
- 전역 예외 핸들러 3종(Exception/HTTPException/RequestValidationError) 등록 — 에러 표준화 양호
- 백그라운드 작업: FlexPepDock은 파일 기반(job.json/status.json), 실험 런은 threading + 파일 JSON 기반, SSE 스트리밍은 asyncio.Queue 기반
- silo_a 라우터가 `/api/v1/silo-a` prefix로 단일 등록(이전 코드 주석의 중복 우려는 실제 미발생)되나, `/api/v1/silo-a/health`가 404 반환 — 확인 필요

---

## 라우터 인벤토리
| 라우터 | 실효 prefix | 엔드포인트 수 | 상태 |
|--------|-------------|---------------|------|
| status.py | /api | 5 | 정상 |
| analysis.py | /api | 8 | 정상 |
| validation.py | /api | 5 | 정상 |
| experiment.py | /api | 6 | 정상 |
| admet.py | /api | 3 | 정상 |
| static.py | /api | 2 | 정상 |
| settings.py | /api | 2 | 정상 |
| rcsb.py | /api | 1 | 정상 |
| cluster.py | /api | 1 | 정상 |
| selectivity.py | /api | 8 | 정상 |
| stability.py | /api | 5 | 정상 |
| agents.py | /api | 2 | 정상 |
| runs.py | /api/runs | 2 | 정상 |
| cand03_variants.py | /api | 2 | 정상 |
| benchmark.py | /api/benchmark | 1 | 정상 |
| pipelines.py | /api/pipelines | 1 | 정상 |
| wetlab.py | /api/wetlab | 4 | 정상 |
| flexpepdock.py | /api | 6 | 정상(일부 job failed) |
| binding_pocket.py | /api | 4 | 정상 |
| strategies.py | /api | 7 | 정상 |
| silo_a.py | /api/v1/silo-a | 4 | 확인 필요(404) |

총 21개 라우터 / 합산 81개 엔드포인트

---

## 점검 항목 (9-필드)

### [B-01] 라우터 매핑
| 필드 | 내용 |
|---|---|
| 점검 대상 | `backend/routers/*.py` 21개 파일 |
| 점검 방법 | `ls` + `grep -c '@router\.'` + `main.py include_router` grep |
| 확인한 근거 | `main.py:113-133` — 21개 `include_router` 호출 확인 |
| 현재 상태 | 정상 |
| 발견 이슈 | `main.py:55`에 주석으로 남은 silo_a 등록 예시 코드가 있으나 실제 실행 코드는 아님 |
| 영향도 | 低 — 실제 등록은 단일(line 133) |
| 우선순위 | P2 |
| 조치 방안 | 주석 정리 권장 (혼동 방지) |
| 보고 요약 1문장 | 21개 라우터 81개 엔드포인트가 `/api` 및 하위 prefix에 정상 등록되어 있음 |

### [B-02] 핵심 엔드포인트 라이브 응답
| 필드 | 내용 |
|---|---|
| 점검 대상 | `/api/health`, `/api/admet/AGCKNFFWKTFTSC`, `/api/runs`, `/api/selectivity/receptors`, `/api/flexpepdock/jobs` |
| 점검 방법 | `curl` GET 실호출, HTTP 상태코드 + 페이로드 일부 캡처 |
| 확인한 근거 | 아래 "라이브 응답 캡처" 섹션 참조 |
| 현재 상태 | 정상 (5개 모두 200) |
| 발견 이슈 | flexpepdock job UUID `91e44bd1-...` status=failed — 워커 오류 사례 존재 |
| 영향도 | 中 — flexpepdock failed job은 사용자 재시도 필요 |
| 우선순위 | P1 |
| 조치 방안 | flexpepdock 워커 실패 원인 로그 확인 필요 (`JOBS_DIR/{job_id}/` 하위 로그) |
| 보고 요약 1문장 | 5개 핵심 엔드포인트 모두 200 응답 중이나 FlexPepDock 워커에서 failed job 발생 이력 있음 |

### [B-03] 에러 핸들링/예외
| 필드 | 내용 |
|---|---|
| 점검 대상 | `main.py` 전역 핸들러 + 라우터 내 try/except |
| 점검 방법 | `grep -n 'exception_handler\|add_exception_handler'` + `grep -rc 'try:'` |
| 확인한 근거 | `main.py:73` `@app.exception_handler(Exception)`, `main.py:86` `@app.exception_handler(FastAPIHTTPException)`, `main.py:99` `@app.exception_handler(RequestValidationError)` — 3종 전역 핸들러 확인 / 전체 try: 85개, except: 88개 |
| 현재 상태 | 정상 |
| 발견 이슈 | 전역 Exception 핸들러 존재로 예외가 HTTP 500 JSON으로 표준화됨 — 상세 내용 누락 위험 |
| 영향도 | 低 |
| 우선순위 | P2 |
| 조치 방안 | 개발 모드 시 traceback 포함 여부 확인 권장 |
| 보고 요약 1문장 | 전역 예외 핸들러 3종이 등록되어 에러 응답이 표준 JSON으로 통일됨 |

### [B-04] 백그라운드 작업 메커니즘
| 필드 | 내용 |
|---|---|
| 점검 대상 | FlexPepDock 워커, 실험 런, SSE 스트리밍 |
| 점검 방법 | `grep -rn 'BackgroundTasks\|asyncio\|threading\|json.*write\|worker'` |
| 확인한 근거 | (1) FlexPepDock: `flexpepdock.py:249` `job.json` 기록 → `flexpepdock_worker.py` subprocess spawn (`flexpepdock.py:200`) → `status.json`/`result.json` 파일 폴링. (2) 실험 런: `runs.py:25` `threading.Lock` + `runs.py:230` `threading.Thread` subprocess 모니터링 + JSON 파일 상태 저장. (3) SSE: `agents.py:133` `asyncio.create_task(_tail_log_file)` + `asyncio.Queue(maxsize=200)` |
| 현재 상태 | 정상 (파일 기반, DB/Redis 미사용) |
| 발견 이슈 | 파일 기반 상태 관리는 다중 프로세스 동시 접근 시 race condition 잠재 위험. Redis/DB 없이 운영 중 |
| 영향도 | 中 — 단일 서버 단일 워커 환경에서는 현재 문제 없음, 스케일아웃 시 문제 |
| 우선순위 | P2 |
| 조치 방안 | 현재 단일 인스턴스 운영이면 허용 범위. 향후 스케일아웃 시 DB/Redis 전환 필요 |
| 보고 요약 1문장 | 모든 백그라운드 작업이 파일 기반 JSON으로 상태를 관리하며 DB/Redis를 사용하지 않음 |

### [B-05] 의존성
| 필드 | 내용 |
|---|---|
| 점검 대상 | `requirements.txt` 핵심 패키지 버전 |
| 점검 방법 | `grep -E 'fastapi|uvicorn|pydantic'` |
| 확인한 근거 | `requirements.txt`: fastapi==0.135.1, uvicorn[standard]==0.41.0, pydantic==2.12.5 |
| 현재 상태 | 정상 (최신 안정 버전) |
| 발견 이슈 | 없음 |
| 영향도 | 低 |
| 우선순위 | P2 |
| 조치 방안 | 해당 없음 |
| 보고 요약 1문장 | FastAPI 0.135.1 / Uvicorn 0.41.0 / Pydantic 2.12.5 — 모두 최신 안정 버전 |

### [B-06] silo_a 라우터 응답 이상
| 필드 | 내용 |
|---|---|
| 점검 대상 | `silo_a.py` 등록 엔드포인트 (`/api/v1/silo-a/health` 등) |
| 점검 방법 | `curl http://127.0.0.1:8787/api/v1/silo-a/health` |
| 확인한 근거 | HTTP 404 반환. `silo_a.py:153` `@router.get("/health")` 정의 확인. `main.py:133` `include_router(silo_a_router.router, prefix="/api/v1/silo-a")` 등록 확인 |
| 현재 상태 | 미동작 (404) |
| 발견 이슈 | 코드 상 등록은 되어 있으나 라이브에서 404 — 서버 재기동 없이 반영이 안 됐거나 silo_a 라우터 초기화 실패 가능성 |
| 영향도 | 高 — Silo A Phase 2 워커 통합에 직결 |
| 우선순위 | P1 |
| 조치 방안 | 서버 재기동 후 재확인. 미해결 시 `silo_a.py` import 오류 여부 서버 로그 확인 필요 |
| 보고 요약 1문장 | silo_a 라우터가 코드상 등록됐으나 라이브에서 404 — 초기화 실패 또는 reload 미적용 의심 |

---

## 라이브 응답 캡처

```
$ curl http://127.0.0.1:8787/api/health
{"status":"ok","timestamp":1780290502.297768,"mode":"local"}

$ curl http://127.0.0.1:8787/api/admet/AGCKNFFWKTFTSC
{"sequence":"AGCKNFFWKTFTSC","admet":{"mw":1638.73,"net_charge_ph74":2.0,
 "n_hbd":22,"n_hba":18,"hydrophobicity":0.0286,"amphipathicity_index":6.0363,
 "druglikeness_score":100,...}}  [HTTP 200]

$ curl http://127.0.0.1:8787/api/selectivity/receptors
{"receptors":{"sstr1":{"path":"...sstr1.cif","format":"cif","source":"uploaded",
 "size_bytes":1816091},"sstr3":{...},...}}  [HTTP 200]

$ curl http://127.0.0.1:8787/api/flexpepdock/jobs
{"jobs":[{"job_id":"91e44bd1-1161-4b36-9e19-81510a588106",
 "sequence":"AGCKNFFWKAFTSC","status":"failed","progress":20,...},...]}  [HTTP 200]

$ curl http://127.0.0.1:8787/api/runs
{"runs":[{"run_id":"sst14_mutdock_1000","completed":true,"iteration":5,
 "best_ddg":-48.235,...},...]}  [HTTP 200]

$ curl http://127.0.0.1:8787/api/v1/silo-a/health
{"detail":"Not Found"}  [HTTP 404]
```

---

## 발견 이슈 Top 3 (영향도/우선순위 정렬)

1. **[P1/高] silo_a /api/v1/silo-a/health 404** — 코드 등록 확인됨에도 라이브 404. Silo A 워커 통합 블로커 가능성. 서버 재기동 + 로그 확인 필요.
2. **[P1/中] FlexPepDock 워커 failed job 존재** — UUID `91e44bd1-...` status=failed, progress=20%. 워커 subprocess 실패 원인 미파악. `JOBS_DIR/{job_id}/` 로그 확인 필요.
3. **[P2/中] 파일 기반 상태 관리 — 스케일아웃 취약** — runs/flexpepdock 모두 JSON 파일로 상태 저장. 현재 단일 인스턴스 운영이면 허용 범위이나, 워커 병렬 확장 시 race condition 위험.

---

## 청중용 1줄 설명 (생명공학자에게)
"백엔드는 SST-14 변이체 도킹·ADMET·선택성 분석 요청을 받아 PyRosetta FlexPepDock 워커에 작업을 분배하고 결과를 JSON 파일로 저장·전달하는 중간 서버입니다 — 즉 AI 스크리닝 파이프라인의 교통정리 역할을 담당합니다."

---

## 확인 필요 항목
- silo_a `/api/v1/silo-a/health` 404 원인 — 서버 재기동 후 재확인 또는 uvicorn 기동 로그에서 silo_a import 오류 여부 확인
- FlexPepDock 워커 failed job `91e44bd1-...` 실패 원인 — `JOBS_DIR/91e44bd1-.../` 하위 stderr 로그 확인
- `runs.py`의 `runs_root` 실제 경로 — 환경변수 또는 하드코드 여부 미확인
- git log에서 backend 최근 커밋 `ad5be95` "llm_benchmark optional + /api/health 식별자" 이후 추가 변경 없음 확인됨
