# SOD 2026-05-21 — FlexPepDock Worker Pool 4

## 목표

FlexPepDock local worker pool 기본 기동 수를 2개에서 4개로 확장한다.

## 배경

- 기존 `start_flexpepdock_workers.sh` 기본값은 worker 2개였다.
- 큐 대기 ETA가 약 38분까지 증가해, worker 2개로는 local FlexPepDock 잡 처리 대기 시간이 병목이 된다.
- `flexpepdock_worker.py`의 V5-R4 `_MAX_WORKER_SLOTS=4`는 이미 worker-1~worker-4 PID slot을 지원하므로 worker 구현 변경 없이 기동 스크립트만 4개 worker를 시작하면 된다.

## 변경

- `pipeline_local/scripts/start_flexpepdock_workers.sh`
  - 기본 `N_WORKERS`를 4로 변경.
  - 도움말과 헤더 문서를 worker-1~worker-4 기준으로 갱신.
  - `--workers` 입력은 1~4 범위로 검증.
- `pipeline_local/tests/test_flexpepdock_worker_pool.py`
  - 4개 프로세스가 서로 다른 4개 job에 대해 `fcntl.flock` 기반 per-job lock을 동시에 획득할 수 있는 회귀 테스트 추가.
  - start script 기본 pool 크기가 4임을 확인하는 정적 회귀 테스트 추가.

## 기대 효과

- 기존 worker 2개 제한에서 worker 4개 동시 처리로 확장된다.
- 동일한 job 처리 시간이 균등하다는 가정에서 큐 대기 38분 ETA는 약 절반 수준으로 단축될 것으로 예상된다.
- per-job lock이 유지되므로 동일 job 중복 처리 위험은 기존 방어선을 그대로 사용한다.

## 자원 영향

- CPU/메모리 사용량은 FlexPepDock worker 2개 추가분만큼 증가한다.
- worker별 PyRosetta 초기화와 실행 메모리를 감안해 host 여유 메모리 모니터링이 필요하다.
- H100 NVL GPU 자원은 FlexPepDock local worker와 분리되어 있으므로, 다른 세션의 GPU 작업에는 직접 영향이 없다.

## 범위 외

- `flexpepdock_worker.py`의 V4-A timeout, V4-B `acquire_lock` 영역은 변경하지 않았다.
- V5-R4 `cleanup_stale_worker_pid_files` 영역은 변경하지 않았다.
- npm test 대상이 없는 BE-only 변경이다.
