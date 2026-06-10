---
description: 다른 세션·worktree 진행상황 + 보고자료(PPTX) 통합 보고
---

`scripts/session_report.sh`를 실행하여 worktree·미커밋 변경·OPEN PR·EOD/SOD·PPTX를 표로 집계합니다.

**사용법**:
- 인자 없음: 화면 출력만 (`bash scripts/session_report.sh`)
- `save`: `_workspace/release/session-overview-YYYY-MM-DD.md`로 저장 (`bash scripts/session_report.sh --save`)
- `pr|eod|pptx|worktree|dirty`: 특정 섹션만 (`bash scripts/session_report.sh --section <name>`)

**ARGUMENTS 처리 규칙**:
- 비어 있으면: `bash scripts/session_report.sh` 실행
- `save`이면: `bash scripts/session_report.sh --save` 실행 (저장 경로 안내)
- `pr` / `eod` / `pptx` / `worktree` / `dirty`이면: `--section <name>` 으로 실행
- 그 외 자유 텍스트면 전체 실행 후 텍스트가 가리키는 부분을 강조 요약

실행 후:
1. 결과를 그대로 표시
2. **점검 필요 항목** (dirty worktree, 5일 이상 OPEN PR, ⚠️ 표시)을 마지막에 별도로 한 번 더 강조
3. 사용자가 명시적으로 요청하지 않으면 위임이나 커밋 같은 추가 액션은 취하지 말 것
