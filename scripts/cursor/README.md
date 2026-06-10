# Cursor 전용 보조 스크립트 (`scripts/cursor/`)

상위 디렉터리 `scripts/`의 도구 중 **Cursor IDE 터미널·Composer 컨텍스트**와 잘 맞는 것만 골라 래퍼로 모았습니다.

## 이 폴더의 스크립트

| 스크립트 | 역할 |
|---------|------|
| `repo-context-for-agent.sh` | 브랜치·status·최근 커밋·(있으면) ENVIRONMENT.md 일부를 마크다운으로 출력 → 채팅에 붙여넣기 |
| `external-agent-history.sh` | `logs/external_agents/history.jsonl` 최근 N건 요약 |
| `auto-dispatch-preview.sh` | `../auto_dispatch.sh --dry-run` 단축형 (라우팅만 확인) |
| `verify-dispatch-routing.sh` | `../test_auto_dispatch_routing.sh` 호출 |
| `pytest-pharmacology-guards.sh` | `pipeline_local/tests/test_pharmacology_guards.py` 빠른 pytest |
| **`harness_invoke.sh`** | **Cursor CLI harness**: `cursor-cli/stages/` 프롬프트를 묶어 `agent-wrapper.sh cursor-agent` 호출 (`--execute` 로만 실실행, 기본 dry-run). 상세는 [cursor-cli/README.md](../../tools/harness-adaptation/cursor-cli/README.md) 참고 |

### Cursor CLI harness (실행형) 빠른 예

상위 [`scripts/agent-wrapper.sh`](../agent-wrapper.sh) 내용은 그대로 두고, 다음만 확인한다.

```bash
./scripts/cursor/harness_invoke.sh list
./scripts/cursor/harness_invoke.sh run explore --topic feat-x --task "모듈 X 구조 분석"
./scripts/cursor/harness_invoke.sh chain explore,synthesize --topic epic-y --dry-run --task 통합 과제 브리프
```

- `_workspace/<NN>_cursor-<토픽>_<stage파일stem>.md` 로 산출 경로만 프롬프트 안에 채워 넣으며, NN은 단일 run은 현재 디스크 기준 `max(NN)+1`, `chain` 은 시작 시 할당된 연속 블록( dry-run 포함 시 순번 유지 ).
- 라우팅은 [`scripts/auto_dispatch.sh`](../auto_dispatch.sh) 와 무관; 스테이지 이름을 명시한다.

## 상위 `scripts/`와의 역할 분담

- **Cursor 안에서 주로 쓰는 것**: 이 폴더 + `agent-wrapper.sh` / `auto_dispatch.sh` / `git_status.sh` / `run_with_status.sh`(로컬 파이프라인) / `compile_mermaid.sh`(Node 있을 때)
- **Cursor 밖·전용 환경이 필요한 것**: `launch_agent_team.sh`(tmux+`claude` CLI), `run_arm*.sh`, GPU/원격 푸시류, `setup_ubuntu2204.sh` 등

## 보안 참고

`sync_linear_to_obsidian.py` 등에 API 키가 하드코딩되어 있으면 저장소에 노출됩니다. 환경 변수·ignore 처리로 이전하는 것을 권장합니다.
