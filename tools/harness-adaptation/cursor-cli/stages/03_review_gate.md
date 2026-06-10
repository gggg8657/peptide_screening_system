---
stage_id: review_gate
workspace_role: cursor-harness-gate
inputs:
  - "통합 결과 또는 PATCH 요약 참조 파일 {{PREV_OUTPUT}}"
  - "검증할 규격 (테스트 이름, 가드 이름 등)"
outputs:
  - "_workspace/{NN}_cursor-harness-gate_{TOPIC_SLUG}.md"
notes: |
  Producer-Reviewer 루프의 문서 검토 단계. 코드 적용 여부 확인 전 체크리스트.
---

### 컨텍스트
- **프로젝트 루트**: {{PROJECT_ROOT}}
- **토픽 슬러그**: {{TOPIC_SLUG}}
- **근거 산출**: `{{PREV_OUTPUT}}`

### 과제 (TASK)
{{TASK}}

### 검토 기준 (Pass/Fail/NeedsInfo)
각 항목에 대해 상태 태그를 붙이고 근거 1줄만 기재.

| ID | 검사 내용 |
|----|-----------|
| G1 | 구현 또는 제안과 프로젝트 관례 일치 여부 |
| G2 | 재현 명령(conda env, 테스트 경로) 명시 여부 |
| G3 | 약리/도메인 수치 근거 vs 환각 위험 (해당 없으면 NA) |

### 산출 (필수)
파일 `{{OUTPUT_PATH}}` 에 저장 후 본문 끝에:

```
OUTPUT_ARTIFACT={{OUTPUT_PATH}}
```
