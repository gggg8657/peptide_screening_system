# SOD 2026-05-20 — Selectivity 검증 마무리

**세션**: 본 세션 (orchestrator) — UI BE/FE 가 selectivity 를 실제로 돌릴 수 있는지 종료 확인.
**전제**: 2026-05-19 EOD `eod-2026-05-19-selectivity-hotfix.md` 의 hot fix 적용 직후. 데이터 디렉토리는 복사본 상태.

## 0. 한 줄 목표

깨진 심링크 재발 막고, BE 가 `mode: "production"` 으로 한 번 실제 dock 결과를 뱉는지 종단 확인.

## 1. 어제로부터 이월된 미해결 (3건)

| # | 항목 | 우선도 | 비고 |
|---|------|--------|------|
| L-1 | `helloworld` 절대경로 깨진 심링크 자동 복원 watcher 추적 | **High** | hot fix 직후 1회 재발 관측. 누가 만드는지 모름 |
| L-2 | 실 production dock 1회 → 응답 `mode: "production"` 확인 | **High** | 후보당 ~120s × 4 receptor ≈ 8분. 1 candidate 만으로 충분 |
| L-3 | FE 가 보내는 `candidate_id` 포맷 매칭 (`001` / `var001` / `cand_001`) | Med | 다른 세션 UI 작업이 결정. 본 세션은 BE 응답 캡처만 |

## 2. 오늘 실행 순서

### Step 1 — 현재 상태 베이스라인 (5분)

- `ls -la --time-style=full-iso ai4sci-kaeri/data/somatostatin_receptor` mtime 확인
- 디렉토리인지 심링크인지 식별 — 만약 다시 심링크면 step 2 로 점프
- `curl /api/selectivity/receptors` 5/5 loaded 재확인

### Step 2 — 재발 watcher 추적 (L-1, ~30분)

심링크 자동 복원자 추적 후보:

- **a)** `inotifywait` 로 감시 + 깨질 때 trace
  ```
  inotifywait -m ai4sci-kaeri/data/ -e create -e delete -e moved_to
  ```
- **b)** `grep -rn "helloworld\|ln -s.*somatostatin" .` (모든 *.sh, *.py, Dockerfile, Makefile, conftest, fixtures) — 후보 스크립트 식별
- **c)** `ps -ef | grep -iE "setup|init|fixture"` 현재 도는 프로세스 후보
- **d)** 다른 세션 tmux pane 로그 (`tmux capture-pane -p -t <name>`) — UI 검증 중 setup 호출 흔적

→ 범인 식별 후 본 세션에서 패치는 **하지 않음** (다른 세션 작업 영역). 발견 위치만 SOD 본문에 기록 후 사용자 보고.

### Step 3 — 정공 조치 1개 선택·적용 (L-1, ~20분)

어제 EOD 에 적은 A~D 중 본 세션에서 안전하게 닫을 수 있는 안 1개 선택:

| 옵션 | 변경 | 다른 세션 충돌 위험 |
|------|------|---------------------|
| **A** | `selectivity.py:18` `_DATA_DIR` 후보 경로 fallback 추가 | 중간 — 다른 세션이 같은 파일 만지는 중일 가능성 |
| **B** | `state.py` 에 `OUTER_REPO_ROOT` 신설 + `SST_DATA_DIR` env 주입 | 낮음 — 신규 키만 추가, 기존 동작 무변경 |
| **C** | helloworld 심링크 생성 스크립트 root-cause 제거 | step 2 결과에 의존 |
| **D** | BE 기동 시 receptor 0/5 면 로그 + UI 토스트 (estimation silent fallback 차단) | 낮음 — selectivity.py 의 `list_receptors` 만 보강 |

**권고**: **D + B** 조합. D 가 가장 작고 즉시 효과, B 는 미래 깨짐 방어. C 는 범인 모르면 패스.

→ 본 세션 적용 전 사용자 confirm 1회 (`AskUserQuestion`) 받고 진행. 다른 세션과의 충돌 회피.

### Step 4 — 실 dock 1회 검증 (L-2, ~10분)

가장 작은 input 으로:

```
curl -X POST -H 'Content-Type: application/json' \
  -d '{"candidate_ids":["001"],"candidate_sequences":["AGCKNFFWKTFTSC"],"sstr2_ddgs":{"001":-30.0}}' \
  http://127.0.0.1:8787/api/selectivity/run
```

→ 백그라운드 job, ~8분 후 `/api/selectivity/results/<job_id>` 응답에 `mode: "production"` 확인. estimation 으로 떨어지면 Step 2 의 candidate_id 매칭 또는 dock 호출 실패 → 로그 확인.

### Step 5 — 결과 EOD 작성

`eod-2026-05-20-selectivity-validation.md` — production mode 확인 / 미확인 + 재발 방지 적용 항목 + 다른 세션 인계 사항.

## 3. 결정 대기 (사용자)

1. Step 3 정공 조치 안 (D / B / D+B / C / 패스) — Step 2 후 다시 물음
2. Step 4 dock 실행 시점 — 본 세션이 자체 트리거 vs 다른 세션 UI 클릭 대기

## 4. 다른 세션과의 경계 (중요)

- 본 세션은 BE 라우터 (`selectivity.py`) 가 **다른 세션 작업 영역**일 가능성 있어 **읽기 전용 + 부가 가드만**. 핵심 로직 수정은 다른 세션 PR 에서.
- 데이터 디렉토리 복사본 (`ai4sci-kaeri/data/somatostatin_receptor/`) 은 untracked 그대로 둠. `.gitignore` 등록은 별도 PR 에서.
- UI 자체 (FE) 는 본 세션이 안 만짐.

## 5. 컨디션 메모

전 세션 ~22시간 마라톤 직후. 본 SOD 는 의도적으로 좁은 범위 (Selectivity 단일 트랙) 만 다루며, Gate-2 후속·합성 의뢰서는 별도 SOD 로.
