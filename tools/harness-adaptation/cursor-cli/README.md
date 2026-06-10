# Cursor CLI harness 프롬프트 라이브러리

`cursor-agent`(및 레포 규약상 [`scripts/agent-wrapper.sh`](../../../scripts/agent-wrapper.sh))으로 **파일 기반 Pipeline** 을 구성할 때 쓰는 단계(stage)별 프롬프트 원본입니다.

- 인보케이션: [`scripts/cursor/harness_invoke.sh`](../../../scripts/cursor/harness_invoke.sh)
- 패턴 참고: [adapters/cursor-agent.md](../adapters/cursor-agent.md), [PROMPT_TEMPLATE.md](../PROMPT_TEMPLATE.md), [CLAUDE.md](../../../CLAUDE.md)

`_workspace/` 네이밍은 Stage 1 컨벤션과 맞춥니다. 이 CLI 하네스는 산출 경로를 프롬프트에만 넣어 주며, 패턴은 `_workspace/<NN>_cursor-<topic>_<stem>.md` (예: `10_cursor-myfeat_01_explore.md`). 단일 `run` 은 디스크 상 `max(NN)+1` 을 사용하고, `chain` 은 시작 시 한 번 잡은 블록 NN에 대해 각 스테이지마다 +0, +1, … 로 연속 번호를 할당합니다(dry-run 포함).

## 실행 예

```bash
./scripts/cursor/harness_invoke.sh list
./scripts/cursor/harness_invoke.sh run explore --topic myfeat --task "분석 목표"           # 기본 dry-run
./scripts/cursor/harness_invoke.sh run explore --topic myfeat --task "..." --execute        # 실호출
./scripts/cursor/harness_invoke.sh chain explore,synthesize,review_gate --topic epic --task "..." --dry-run
```

- `list`: `stages/*.md` stem 및 `stage_id` 별칭.
- `run STAGE`: 토큰은 `01_explore`(stem) 또는 `explore`(`stage_id`).
- `chain a,b,c`: 이전 단계 `OUTPUT_PATH` 가 다음 단계 `{{PREV_OUTPUT}}` 로 전달됩니다.

각 stage 파일 YAML 선행 블록에 `workspace_role`, `inputs`, `outputs`, `notes`; 본문 치환 플레이스홀더: `{{PROJECT_ROOT}}`, `{{TOPIC_SLUG}}`, `{{OUTPUT_PATH}}`, `{{PREV_OUTPUT}}`, `{{TASK}}`.

