---
description: 에이전트 팀 기동/관리 (네이티브 Agent Team API)
---

Claude Code 네이티브 Agent Team API를 사용하여 팀을 기동합니다.
사용자의 요청($ARGUMENTS)을 팀 태스크로 분해하여 병렬 실행합니다.

## 사전 요구사항

settings.json에 다음이 설정되어 있어야 합니다:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## 기동 절차

### 1단계: 기존 팀 확인
- TaskList로 기존 태스크 확인
- 기존 팀이 활성 상태면 사용자에게 알리고 계속할지 확인

### 2단계: 팀 생성
- TeamCreate로 팀 생성 (team_name은 작업 내용 기반으로 결정)
- 현재 세션이 팀 리드(orchestrator) 역할

### 3단계: 태스크 분해
- 사용자 요청($ARGUMENTS)을 5개 이하의 독립적 태스크로 분해
- TaskCreate로 각 태스크 생성

### 4단계: 팀원 기동 (병렬)
- Agent 도구로 팀원을 동시에 기동 (run_in_background: true)
- 각 팀원에게 team_name과 name을 지정
- 사용 가능한 agent 타입:
  - engineer-infra: 인프라, 환경 세팅, CI/CD
  - engineer-backend: 백엔드, 파이프라인, PyRosetta
  - reviewer-code: 코드 품질, 테스트, 리팩토링
  - reviewer-science: 과학 방법론, 약리학, 화공
  - reviewer-uiux: 프론트엔드, UI/UX, 접근성

### 5단계: 결과 수집
- 팀원들의 메시지가 자동 전달됨 (수동 확인 불필요)
- 모든 태스크 완료 시 결과 종합하여 사용자에게 보고
- TaskUpdate로 태스크 상태 업데이트

### 6단계: 정리
- 작업 완료 후 SendMessage로 팀원에게 shutdown_request
- TeamDelete로 팀 리소스 정리

## 팀 구성 예시

```
TeamCreate → team_name: "my-task"
TaskCreate × N → 태스크 분해
Agent(engineer-infra, name: "infra", team_name: "my-task", run_in_background: true)
Agent(engineer-backend, name: "backend", team_name: "my-task", run_in_background: true)
Agent(reviewer-code, name: "tester", team_name: "my-task", run_in_background: true)
Agent(reviewer-science, name: "science", team_name: "my-task", run_in_background: true)
Agent(reviewer-uiux, name: "frontend", team_name: "my-task", run_in_background: true)
```

## 주의사항
- 팀 리드(나)는 이 세션에서 사용자와 계속 대화 가능
- 팀원은 파일 수정 필요 시 명시적으로 지시해야 함
- 팀원 간 직접 메시지 가능 (SendMessage의 to에 이름 지정)
- 태스크당 1명의 owner 원칙
