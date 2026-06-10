---
description: 외부 에이전트(codex, cursor-agent) 실행 이력 조회
---

외부 에이전트 실행 이력을 보여줍니다.

1. `cat logs/external_agents/history.jsonl 2>/dev/null | tail -20`으로 최근 이력 조회
2. 인자가 있으면 해당 session_id의 상세 로그를 `cat logs/external_agents/${ARGUMENTS}.jsonl`로 조회
3. 결과를 표 형식으로 정리해서 보여주세요
