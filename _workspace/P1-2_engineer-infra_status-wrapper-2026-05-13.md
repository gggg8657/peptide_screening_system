# P1-2 인프라 작업 보고서 — STATUS_FILE wrapper + 경로 통일
**작성**: engineer-infra | **날짜**: 2026-05-13 | **태스크**: #3

---

## 작업 요약

| 항목 | 상태 |
|------|------|
| `scripts/run_with_status.sh` 신규 | ✅ 완료 |
| `pipeline_local/scripts/status_updater.py` 신규 | ✅ 완료 |
| AG_src `backend/state.py` STATUS_FILE 기본값 통일 | ✅ 완료 |
| `pipeline_local/backend/state.py` ARCHIVE_DIRS 확장 | ✅ 완료 |
| 검증 (`sleep 5` 실행 후 STATUS_FILE 확인) | ✅ PASS |

---

## 1. 신규 파일

### 1.1 `scripts/run_with_status.sh`

**역할**: CLI ad-hoc 실험 시 STATUS_FILE 자동 갱신 쉘 래퍼

```bash
# 사용 예시
bash scripts/run_with_status.sh "step08_stability" \
    python pipeline_local/steps/step08_stability.py --seq-id cand01

bash scripts/run_with_status.sh "stability_predictor" \
    python -m pipeline_local.scripts.stability_predictor \
    --sequences AGCKNFFWKTFTSC --seq-ids ref

CONDA_ENV=bio-tools bash scripts/run_with_status.sh "dogfood" \
    python pipeline_local/orchestrator.py --config config.yaml
```

**동작 흐름**:
```
1. status_updater.py --start <task_name>   → STATUS_FILE adhoc_tasks 갱신
2. 원본 커맨드 실행
3. status_updater.py --end <task_name> --exit-code $?  → 완료/실패 기록
4. 원본 exit code로 종료
```

**환경변수**:
- `PIPELINE_STATUS_FILE`: 갱신 대상 파일 (기본: `/tmp/pipeline_local_status.json`)
- `PIPELINE_EVENTS_JSONL`: 이벤트 로그 (기본: `/tmp/pipeline_events.jsonl`)
- `CONDA_ENV`: conda 환경 이름 (미설정 시 현재 환경의 python 사용)

---

### 1.2 `pipeline_local/scripts/status_updater.py` (~220 LOC)

**역할**: STATUS_FILE + EVENTS_JSONL 갱신 CLI 도구

**CLI 인터페이스**:
```bash
# 작업 시작
python -m pipeline_local.scripts.status_updater --start my_task

# 진행 중 갱신
python -m pipeline_local.scripts.status_updater --update --progress 50 --message "step 3/5 완료"
python -m pipeline_local.scripts.status_updater --update --task my_task --progress 80

# 작업 종료
python -m pipeline_local.scripts.status_updater --end my_task --exit-code 0
python -m pipeline_local.scripts.status_updater --end my_task --exit-code 1
```

**STATUS_FILE 갱신 구조**:
```json
{
  "adhoc_tasks": {
    "test_task": {
      "run_id": "adhoc_test_task_1778651138",
      "status": "completed",
      "started_at": "2026-05-13T05:45:38+00:00",
      "ended_at": "2026-05-13T05:45:40+00:00",
      "exit_code": 0,
      "elapsed_sec": 2.1,
      "progress_pct": 100,
      "message": "test_task 완료"
    }
  },
  "last_adhoc_task": "test_task",
  "last_adhoc_ts": "2026-05-13T05:45:40+00:00",
  "connected": true
}
```

**EVENTS_JSONL 포맷** (`/tmp/pipeline_events.jsonl`):
```jsonl
{"type": "start", "task": "test_task", "run_id": "adhoc_test_task_...", "ts": "2026-05-13T..."}
{"type": "end", "task": "test_task", "run_id": "adhoc_test_task_...", "exit_code": 0, "elapsed_sec": 2.1, "ts": "2026-05-13T..."}
{"type": "update", "task": "test_task", "progress": 50, "message": "half done", "ts": "..."}
```

**동시성 보호**: `fcntl.flock(LOCK_EX)` 기반 파일 락 (`/tmp/.pipeline_status.lock`)
- 타임아웃: 5초 (TimeoutError → exit 1)
- JSONL append도 동일 락 보호

---

## 2. 수정 파일

### 2.1 AG_src `backend/state.py` — STATUS_FILE 기본값 통일

```diff
-    "/tmp/ag_pipeline_status.json",
+    # pipeline_local 정식 경로로 통일 (P1-2, 2026-05-13)
+    # 레거시: /tmp/ag_pipeline_status.json → /tmp/pipeline_local_status.json
+    "/tmp/pipeline_local_status.json",
```

**경로**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/state.py`

**효과**:
- UI(AG_src backend)와 pipeline_local orchestrator가 동일 STATUS_FILE 참조
- `/tmp/ag_pipeline_status.json`은 레거시 — 기존 실행 호환을 위해 `PIPELINE_STATUS_FILE` 환경변수로 오버라이드 가능

---

### 2.2 `pipeline_local/backend/state.py` — ARCHIVE_DIRS 확장

```python
def _default_archive_dirs() -> list[Path]:
    # P1-2 (2026-05-13): ad-hoc 실행 결과 노출을 위해 runs_local 하위 경로 확장
    return [
        REPO_ROOT / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local" / "archives",
        AG_SRC_REPO / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local",                                              # ad-hoc 결과 일괄
        REPO_ROOT / "runs_local" / "archives_boltz_eval",                     # Boltz eval
        REPO_ROOT / "runs_local" / "cand03_variants" / "boltz_dock",          # cand03 변이
        REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "boltz_batch",  # 선택성 데모
        REPO_ROOT / "runs_local" / "stability",                               # 안정성 실험
    ]
```

---

## 3. 검증 결과

### 3.1 run_with_status.sh 동작 검증

```bash
bash scripts/run_with_status.sh "test_task" sleep 2
```

```
[run_with_status] ▶ task='test_task' 시작
[status_updater] ▶ START task='test_task' run_id=adhoc_test_task_1778651138
[status_updater] ✅ DONE task='test_task' elapsed=2.1s
[run_with_status] ✅ task='test_task' 완료
```

**STATUS_FILE 확인**:
- `adhoc_tasks.test_task.status`: `"completed"` ✅
- `adhoc_tasks.test_task.elapsed_sec`: `2.1` ✅
- `last_adhoc_task`: `"test_task"` ✅

**EVENTS_JSONL 확인**:
```
[start] task=test_task ts=2026-05-13T05:45:38
[end]   task=test_task ts=2026-05-13T05:45:40
```

### 3.2 ARCHIVE_DIRS 경로 상태

| 경로 | 존재 | 비고 |
|------|------|------|
| `runs/pyrosetta_flow/archives` | ✅ | 기존 |
| `runs_local/archives` | ❌ | 미생성 (오류 없음 — `is_dir()` 체크) |
| `AG_SRC_REPO/runs/.../archives` | ✅ | 기존 |
| `runs_local/` | ✅ | **신규** — ad-hoc 결과 일괄 |
| `runs_local/archives_boltz_eval` | ✅ | **신규** |
| `runs_local/cand03_variants/boltz_dock` | ✅ | **신규** |
| `runs_local/selectivity_demo_20260511/boltz_batch` | ✅ | **신규** |
| `runs_local/stability` | ❌ | 미생성 (오류 없음) |

**참고**: `list_archive_dashboard_files()`는 `d.is_dir()` 체크 후 glob → 미존재 폴더는 무시됨.

### 3.3 AG_src STATUS_FILE 기본값 확인

```bash
grep "pipeline_local_status\|ag_pipeline_status" \
    AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/state.py
```
```
# 레거시: /tmp/ag_pipeline_status.json → /tmp/pipeline_local_status.json
"/tmp/pipeline_local_status.json",
```
✅ 통일 완료.

---

## 4. 향후 연동 권장

### 4.1 backend `/api/runs` 노출 확인 절차
```bash
# backend 재시작 후
curl http://localhost:8787/api/runs | python3 -m json.tool | grep run_id | head -10
# → ad-hoc 결과 (dogfood_*, dual_*) 가 노출되면 성공
```

### 4.2 SSE 스트리밍 (중기)
```bash
# /tmp/pipeline_events.jsonl tail 기반 실시간 모니터링
tail -f /tmp/pipeline_events.jsonl
```
- 향후 `GET /api/events/stream` SSE 엔드포인트로 연결 가능
- EVENTS_JSONL이 공유 로그로 역할하므로 구현 간단

### 4.3 레거시 파일 정리 (선택)
```bash
# /tmp/ag_pipeline_status.json이 더 이상 업데이트되지 않음을 확인 후 제거
rm -f /tmp/ag_pipeline_status.json
```

---

## 5. 변경 파일 목록

| 파일 | 변경 유형 | LOC |
|------|---------|-----|
| `scripts/run_with_status.sh` | 신규 | 68 |
| `pipeline_local/scripts/status_updater.py` | 신규 | ~220 |
| `AgenticAI4SCIENCE_pyrosetta_track/.../backend/state.py` | 수정 | +3줄 |
| `pipeline_local/backend/state.py` | 수정 | +5줄 |

---

*작성: engineer-infra / P1-2 / 2026-05-13*
