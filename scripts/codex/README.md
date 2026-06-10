# Codex 전용 보조 스크립트 (`scripts/codex/`)

상위 디렉터리 `scripts/`의 도구 중 **Codex CLI 터미널 세션**과 잘 맞는 것만 골라 래퍼로 모았습니다.

## 이 폴더의 스크립트

| 스크립트 | 역할 |
|---------|------|
| `repo-context-for-agent.sh` | 브랜치·status·최근 커밋·(있으면) ENVIRONMENT.md 일부를 마크다운으로 출력 → Codex 프롬프트/메모에 붙여넣기 |
| `external-agent-history.sh` | `logs/external_agents/history.jsonl` 최근 N건 요약 |
| `auto-dispatch-preview.sh` | `../auto_dispatch.sh --dry-run` 단축형 (라우팅만 확인) |
| `verify-dispatch-routing.sh` | `../test_auto_dispatch_routing.sh` 호출 |
| `pytest-pharmacology-guards.sh` | `pipeline_local/tests/test_pharmacology_guards.py` 빠른 pytest |

## 상위 `scripts/`와의 역할 분담

- **Codex 안에서 주로 쓰는 것**: 이 폴더 + `agent-wrapper.sh` / `auto_dispatch.sh` / `git_status.sh` / `run_with_status.sh` / `compile_mermaid.sh`
- **Codex 밖·전용 환경이 필요한 것**: `launch_agent_team.sh`(tmux+`claude` CLI), `run_arm*.sh`, GPU/원격 푸시류, `setup_ubuntu2204.sh` 등

## 참고

- 이 폴더는 `scripts/cursor/`와 같은 성격의 Codex용 복제본입니다.
- 원본 스크립트의 동작은 바꾸지 않고, Codex에서 찾기 쉬운 진입점만 추가합니다.
