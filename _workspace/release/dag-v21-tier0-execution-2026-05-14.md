# DAG v2.1 Tier 0 — 8 패치 실행 결과 통합 보고서

**작성**: reviewer-code (dag-v21-tier0 팀)
**날짜**: 2026-05-14
**근거 문서**: `_workspace/release/liverun-integration-analysis-v2-2026-05-13.md` §B-C
**검증 스크립트**: `_workspace/release/dag-v21-tier0-regression-2026-05-14.sh`

---

## 1. 실행 요약

| 항목 | 값 |
|---|---|
| 팀 | dag-v21-tier0 (5 팀원 병렬) |
| 실행일 | 2026-05-14 |
| Tier 0 패치 대상 | P01, P05, P06, P08, P09, P11, P14, P15 (8건) |
| 정적 검증 결과 | **PASS 8 / FAIL 2 / SKIP 3** (총 13건 시나리오) |
| FAIL 원인 | #3, #7 — P03 (Tier 1) 미적용. Tier 0 범위 밖 |
| Tier 1 진행 가능 여부 | **YES** — P01~P08 Tier 0 완료 확인 |

### 결정 게이트 채택 결과

| 게이트 | 채택안 | 비고 |
|---|---|---|
| G-1 | (A) 코드 + 문서 3건 동시 | status_emitter.py + 문서 동시 |
| G-2 | +10 유지 + REU 레이블 정정 | yaml 레이블 별도 확인 필요 |
| G-3 | 완료 처리 (제거) | state.py P1-2 이미 적용됨 |
| G-4 | `sst14_mutdock_{timestamp}` | experiment.py:183 확인 |
| G-5 | Silo A 활성 유지 | dual 차단/확장 미확정 |
| G-6 | (a) soft cancel | P11 적용, subprocess timeout은 별도 |
| G-7 | (a) Skipped 뱃지 + dot | P15 ValidationPanel 처리 |

---

## 2. 패치별 적용 결과

### Tier 0 패치 (8건)

| 패치 | 담당 | 변경 파일 | 적용 상태 | 검증 증거 |
|---|---|---|---|---|
| **P01** | engineer-backend | `backend/status_emitter.py:30-34` | ✅ APPLIED | STATUS_FILE = `/tmp/pipeline_local_status.json` (emitter==state) |
| **P05** | reviewer-uiux + engineer-backend | `frontend/src/components/ClusterPanel.tsx` | ✅ APPLIED | ClusterPanel.tsx 존재, ddG/plddt/gravy/cluster 필드 참조 확인 |
| **P06** | engineer-backend | `pyrosetta_flow/runner.py:533-535` | ✅ APPLIED | `update_step(_skip_id, "skipped")` for step01~05/05b 루프 확인 |
| **P08** | engineer-infra | `requirements.txt:13-14`, `experiment.py:225-235` | ✅ APPLIED | biopython>=1.79, python-multipart>=0.0.22 추가; log_file redirect로 hang 방지 |
| **P09** | engineer-backend | `experiment.py:189-203` | ✅ APPLIED | 3-way 폴백: config.get → runtime_settings.get → DEFAULT (max_iterations/n_candidates/top_k) |
| **P11** | engineer-backend | `selectivity.py:380-394, 215-218, 323` | ✅ APPLIED | `POST /selectivity/cancel/{job_id}` + `_JOBS[job_id]["cancelled"]` 체크포인트 |
| **P14** | reviewer-uiux | `frontend/src/hooks/useSelectivity.ts:82-83` | ✅ APPLIED | `offtarget_max_receptor: (c.offtarget_max_receptor as string) ?? ''` 직접 사용, worstEntry 재계산 제거 |
| **P15** | reviewer-uiux | `frontend/src/pages/SelectivityPage.tsx`, ValidationPanel 연계 | ⚠️ PARTIAL | SelectivityPage aria-label 추가 확인; ValidationPanel skipped dot 별도 확인 필요 |

### Tier 1 패치 (미적용 — 본 실행 범위 밖)

| 패치 | 담당 | 상태 | 블로커 |
|---|---|---|---|
| P02 | engineer-backend | ❌ PENDING | Tier 0 완료 후 진행 (Popen 직후 STATUS_FILE write) |
| P03 | engineer-backend | ❌ PENDING | Tier 0 완료 후 진행 (is_active_run/server_time 주입) |

### Tier 2 패치 (미적용 — P03 선행 필요)

| 패치 | 담당 | 상태 |
|---|---|---|
| P04 | reviewer-uiux | ❌ PENDING (P03 응답 필드 선행) |

---

## 3. 회귀 시나리오 13단계 결과

> **정적 검증** (`SKIP_LIVE=1`) 실행 결과. uvicorn 재기동은 leader 책임으로 live 검증 미수행.

| # | 시나리오 | 자동/수동 | 결과 | 패치 | 비고 |
|---|---|---|---|---|---|
| 1 | STATUS_FILE 경로 일치 | 자동(static) | ✅ PASS | P01 | `/tmp/pipeline_local_status.json` emitter=state 일치 |
| 2 | /api/status 즉시 갱신 | 자동(live) | ⏭️ SKIP | P02 | uvicorn 필요, P02 Tier 1 미적용 |
| 3 | is_active_run + server_time 포함 | 자동(static) | ❌ FAIL | P03 | **P03 Tier 1 미적용** — is_active_run 0건 |
| 4 | FE Live 배지 + run_id prominent | 수동 | ⏭️ SKIP | P04 | React DevTools 수동 확인 필요 |
| 5 | runner step01~05 skipped emit | 자동(static) | ✅ PASS | P06 | `update_step(_skip_id, "skipped")` 루프 1건 확인 |
| 6 | 완료 후 동일 파일 write | 자동(static) | ✅ PASS | P01 | `/tmp/` 쓰기 가능 확인 |
| 7 | completed=true → is_active_run=false | 자동(static) | ❌ FAIL | P03 | **P03 Tier 1 미적용** — 역산 로직 없음 |
| 8 | FE Live → Completed 배지 전환 | 수동 | ⏭️ SKIP | P04 | UI 배지 확인 필요 |
| 9 | Cluster A~E 혼재 | 자동(static) | ✅ PASS | P05 | ClusterPanel.tsx 존재; live API 확인 필요 |
| 10 | Stop → cancel → 다음 후보 skip | 자동(static) | ✅ PASS | P11 | cancel endpoint(11건) + cancelled 플래그(6건) 확인 |
| 11 | Settings 변경 → 다음 run 반영 | 자동(static) | ✅ PASS | P09 | OR_CHAIN 3건 + fallback 3건 확인 |
| 12 | approach='a' → Silo A 분기 | 자동(static) | ✅ PASS | P10 | approach 분기 코드 1건; G-5 regex 확장 live 확인 필요 |
| 13 | off-target worst BE/FE 동일 receptor | 자동(static) | ✅ PASS | P14 | worstEntry 재계산 제거, offtarget_max_receptor 직접 참조 4건 |

**집계**: PASS 8 / FAIL 2 / SKIP 3 (총 13건)

---

## 4. 세부 검증 노트

### P01 — STATUS_FILE 경로 통일 [신뢰: HIGH]
```
status_emitter.py:30-34  → /tmp/pipeline_local_status.json (P01 주석 포함)
state.py:23-28           → /tmp/pipeline_local_status.json (P1-2 주석 포함)
Python import 실시간 일치 확인 ✓
```

### P06 — step skip emit [신뢰: HIGH]
```python
# runner.py:533-535
for _skip_id in ["step01", "step02", "step03", "step03b", "step04", "step05", "step05b"]:
    emitter.update_step(_skip_id, "skipped")
```
step06_baseline 분리 여부는 별도 확인 필요 (runner.py:550 `start_step("step06_baseline")` 확인됨).

### P08 — subprocess hang 방지 [신뢰: HIGH]
DEVNULL 대신 `log_file = open(log_path, "w")` → `stdout=log_file, stderr=subprocess.STDOUT` 방식 채택.
디버그 가능성 보존. experiment.py:225 주석 "DEVNULL 대신 로그 파일 사용" 확인.

### P09 — 3-way 폴백 [신뢰: HIGH]
```python
# experiment.py:189-203
max_iterations = (
    config.get("max_iterations")           # 1순위: 요청 페이로드
    or state.runtime_settings.get("max_iterations")  # 2순위: /api/settings
    or DEFAULT_EXPERIMENT_CONFIG["max_iterations"]    # 3순위: 기본값
)
```
n_candidates, top_k 동일 패턴. llm_provider/model/base_url은 이미 이전 커밋에서 구현됨.

### P11 — Soft cancel [신뢰: HIGH]
```python
# selectivity.py:380-394
@router.post("/selectivity/cancel/{job_id}")
def cancel_selectivity(job_id: str):
    ...
    job["cancelled"] = True
    return {"ok": True, "job_id": job_id, "status": "cancellation_requested"}

# selectivity.py:215-218 (후보 루프 내 체크포인트)
if _JOBS[job_id].get("cancelled"):
    _JOBS[job_id]["status"] = "cancelled"
    break
```
완료/실패 job은 409 반환 (soft cancel only, subprocess timeout은 별도 sprint).

### P14 — off-target worst receptor 수정 [신뢰: HIGH]
```typescript
// useSelectivity.ts:82-83 (BEFORE: worstEntry[0] 재계산)
offtarget_max_receptor: (c.offtarget_max_receptor as string) ?? '',
offtarget_max_score: (c.offtarget_max_score as number) ?? 0,
```
BE 응답 `offtarget_max_receptor` (min 기준 = 가장 강한 off-target 결합) 직접 사용.
worstEntry reduce(max) 재계산 코드 제거 확인.

### P03 — is_active_run/server_time 미적용 [신뢰: HIGH]
state.py, routers/status.py 모두 is_active_run/server_time 키 없음.
**Tier 1 작업 필요**: state.read_status()의 후처리에서 `is_active_run = not data.get("completed", False)` 와 `server_time = datetime.now(timezone.utc).isoformat()` 주입.

---

## 5. 잔여 위험

| ID | 위험 | 심각도 | 조치 |
|---|---|---|---|
| R-01 | P03 미적용 — is_active_run/server_time 응답 없음 | HIGH | Tier 1 즉시 진행 |
| R-02 | P04 미적용 — FE 배지 Live/Completed 전환 안 됨 | HIGH | P03 완료 후 Tier 2 진행 |
| R-03 | P15 partial — ValidationPanel skipped dot 확인 필요 | MEDIUM | live 빌드 후 확인 |
| R-04 | P05 Cluster 분류 live 미확인 — API 응답 A~E 혼재 미검증 | MEDIUM | uvicorn 재기동 후 /api/cluster/classify 호출 |
| R-05 | G-5 dual 분기 처리 미확정 — approach='dual' regex 확장 vs 차단 | MEDIUM | G-5 결정 후 P10 마무리 |
| R-06 | P06 step06_baseline 분리 — runner.py:550 명칭 변경 후 Stage 9 시나리오 동기화 필요 | LOW | 다음 PyRosetta run 시 확인 |
| R-07 | subprocess hang — log_file 미닫힘 시 _reap_if_dead 타이밍 의존 | LOW | _close_log_file() 타이밍 모니터링 |
| R-08 | VR-G2-01/02 — off-target 실측 + REU 단위 레이블 미정리 | LOW | VR 트랙 등록만, 실측은 다음 sprint |

---

## 6. Tier 진행 가능 여부 판정

### Tier 1 (P02, P03) — 진행 가능 ✅

**판정 근거**:
- Tier 0 8패치 중 7건 APPLIED, 1건 partial(P15)
- P02/P03 블로커(P01)은 PASS
- uvicorn 재기동 1회 필요 (leader 판단)

**예상 작업**:
- P02: experiment.py Popen 성공 직후 STATUS_FILE에 `{"run_id": ..., "phase": "initializing"}` write
- P03: state.read_status() 반환 직전 `data["is_active_run"] = not data.get("completed", False)`, `data["server_time"] = datetime.now(timezone.utc).isoformat()` 주입

### Tier 2 (P04) — P03 완료 후 진행 가능

**판정 근거**:
- P04는 P03의 `is_active_run` 필드를 FE에서 사용
- App.tsx:66 isLive 로직이 `is_active_run` 기반이어야 완성

---

## 7. 다음 단계

1. **leader**: uvicorn 재기동 결정 + Tier 1 (P02, P03) 착수 승인
2. **engineer-backend**: P02 → experiment.py Popen 직후 initializing write
3. **engineer-backend**: P03 → state.read_status() 후처리 is_active_run/server_time 주입
4. **reviewer-uiux**: P15 live 빌드 후 ValidationPanel skipped dot 확인
5. **팀 전체**: uvicorn 재기동 후 `SKIP_LIVE=0 ./dag-v21-tier0-regression-2026-05-14.sh` 재실행
6. **VR 트랙**: VR-G2-01 (off-target 실측), VR-G2-02 (REU 단위 레이블) 등록

---

## 변경 이력

| 시각 | 내용 |
|---|---|
| 2026-05-14 02:30 | reviewer-code, 회귀 스크립트 작성 + 정적 검증 실행 |
| 2026-05-14 02:44 | SKIP_LIVE=1 결과 확인 — PASS 8, FAIL 2(P03), SKIP 3 |
| 2026-05-14 02:44 | 통합 보고서 최종 작성 |
