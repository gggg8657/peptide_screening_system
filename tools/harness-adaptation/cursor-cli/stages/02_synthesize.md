---
stage_id: synthesize
workspace_role: cursor-harness-synth
inputs:
  - "이전 산출 PREV_ARTIFACT 파일 경로 (chain 시 자동 치환)"
  - "TASK 또는 통합 명령"
outputs:
  - "_workspace/{NN}_cursor-harness-synth_{TOPIC_SLUG}.md"
notes: |
  Pipeline 2단계. 이전 분석 결과를 근거로 결론·권장 작업 순서 작성.
---

### 컨텍스트
- **프로젝트 루트**: {{PROJECT_ROOT}}
- **토픽 슬러그**: {{TOPIC_SLUG}}
- **직전 단계 산출 파일**: 이 파일을 근거로 삼음 → `{{PREV_OUTPUT}}`

### 과제 (TASK)
{{TASK}}

### 지시
1. `{{PREV_OUTPUT}}` 내용 요약 근거에 기반하여 **통합 결론**과 **실행 순서**(우선순위 있는 체크리스트) 작성.
2. 추가 조사 필요 시 무엇이 부족한지 명시.
3. 과장된 확신 피하기. 불확실 시 "불확실 + 확인 방법" 명시.

### 산출 (필수)
실제 파일 `{{OUTPUT_PATH}}` 에 결과를 저장하고, 본문 끝에:

```
OUTPUT_ARTIFACT={{OUTPUT_PATH}}
```
