---
description: Codex CLI 위임 — 코드 수정, 리뷰, 테스트 생성
---

사용자 인자를 Codex CLI에 전달하여 실행합니다.

인자가 "review"이면 `./scripts/agent-wrapper.sh codex review`를, 그 외에는 `./scripts/agent-wrapper.sh codex exec "$ARGUMENTS"`를 Bash로 실행하세요.
실행 후 결과를 요약 보고하고, diff가 생성됐으면 `codex apply` 적용 여부를 사용자에게 확인하세요.
