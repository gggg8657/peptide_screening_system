---
stage_id: explore
workspace_role: cursor-harness-explore
inputs:
  - "TASK: 사용자 요청 또는 조사 목표 한 단락"
  - "(선택) PROJECT_ROOT 디렉터리 하위 참고 경로"
outputs:
  - "_workspace/{NN}_cursor-harness-explore_{TOPIC_SLUG}.md (script가 OUTPUT_PATH로 삽입)"
notes: |
  Pipeline 패턴 1단계. 구조·리스크·오픈 퀘스천 목록 산출.
  자세 패턴 이름은 PROMPT_TEMPLATE.md 참고.
---

다음 목표를 **분석하고 조사**하되, 새 코드 수정은 최소화하고 구조 요약 중심으로 보고한다.

### 컨텍스트
- **프로젝트 루트**: {{PROJECT_ROOT}}
- **토픽 슬러그**: {{TOPIC_SLUG}}

### 과제 (TASK)
{{TASK}}

### 산출 (필수)
최종 응답 본문 끝에 **단일 블록**으로 아래처럼 쓸 것 (경로 문자열 고정):

```
OUTPUT_ARTIFACT={{OUTPUT_PATH}}
```

동일 내용으로 **실제 파일** `{{OUTPUT_PATH}}` 에도 마크다운 보고서를 저장한다.

### 분석 포함 항목
1. 관련 디렉터리/모듈 트리 (요약만)
2. 데이터·설정 진입점
3. 검증해야 할 허약 지점 TOP 5
4. 다음 단계(구현/리뷰)에 필요한 명시 입력
