#!/usr/bin/env bash
# 무한 발굴 결과(텍스트+PDB+리포트+렌더)를 GitHub 에 push — 외부 모니터링용 (2026-06-10).
# .gitignore 는 건드리지 않고 결과 경로만 `git add -f` 로 강제 스테이징.
# 실패해도 죽지 않음(다음 주기 재시도). 로그: runs/pyrosetta_flow/autopush.log
set -uo pipefail

ROOT=/home/dongjukim/Documents/workspace/tmp/SST14-M_scr
RES=AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow
cd "$ROOT" || { echo "cd 실패"; exit 1; }

TS=$(date -u +%FT%H:%M:%SZ)

# 결과 경로만 강제 스테이징 (gitignore 무시). 존재하는 것만.
git add -f \
  "$RES"/experiment_log.jsonl \
  "$RES"/discovery_status.json \
  "$RES"/global_selectivity_leaderboard.json \
  "$RES"/baseline_cache.json \
  "$RES"/discovery_run.log \
  "$RES"/sst14_agentic_mutdock \
  "$RES"/archives 2>/dev/null
# run 산출물 JSON (inloop_/selectivity_/experiment_ 등) — 있으면
git add -f "$RES"/*.json 2>/dev/null

if git diff --cached --quiet 2>/dev/null; then
  echo "[$TS] 변경 없음 — skip push"
  exit 0
fi

git commit -q -m "autopush: 무한 발굴 결과 스냅샷 $TS" || { echo "[$TS] commit 실패"; exit 0; }

if git push origin main 2>&1; then
  echo "[$TS] push 완료 ($(git rev-parse --short HEAD))"
else
  echo "[$TS] push 실패 — 다음 주기 재시도 (네트워크/secret-scan 확인)"
fi
