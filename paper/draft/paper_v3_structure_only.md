# SSTR2 AI Scientist 논문 구조안 (수치 추후 입력 버전)

> 목적: 이번 주에는 **논문 구조와 메시지**를 확정하고, 수치/그래프는 다음 주에 채운다.
> 원칙: 결과 섹션은 "결함 발견"이 아니라 "AI Scientist의 연구 수행 성능(계획·비판·탐색)" 중심으로 작성.

---

## 0. 한 줄 메시지 (본문 전반 공통)

본 연구는 SSTR2 후보 탐색에서 멀티에이전트 AI Scientist가 **실험 계획 수립 → 실행 → 비판적 재평가 → 재탐색**의 연구 루프를 자동화하고, 재현 가능한 추적 로그를 제공함을 보인다.

---

## 1. Introduction (문제-필요성-기여)

### 1.1 문제 정의
- SSTR2 표적 후보 탐색은 탐색 공간이 넓고 계산 단계가 많아 수작업 조율 비용이 큼.
- 기존 접근은 단일 경로/단일 모델 중심으로 반복 실험 관리와 근거 추적이 어려움.

### 1.2 연구 질문
- AI Scientist가 실제로 연구 루프(계획/비판/탐색)를 안정적으로 수행하는가?
- 후보 탐색 결과를 추적 가능한 형태로 제시할 수 있는가?

### 1.3 기여
- Dual-Silo 기반 AI Scientist 워크플로우 제안
- Plan-Critique-Explore 성능 프레임 제시
- 계산 실험 traceability 중심의 보고 체계 제시

---

## 2. Related Work (짧고 명확하게)

### 2.1 AI 기반 후보 탐색
- RFdiffusion, ProteinMPNN, ESMFold, DiffDock 등 도구 파편화 문제

### 2.2 멀티에이전트 과학 자동화
- 단일 에이전트 대비 역할 분화 장점
- 본 연구의 차별점: 파이프라인 수행 성능을 연구 루프 관점으로 평가

### 2.3 MCP 기반 개발/운영
- 도구 통합과 재현성/운영성 측면의 의미

---

## 3. System Overview (코드 정합형 서술)

### 3.1 Dual-Silo 구성
- Silo A: 3-arm 가상 스크리닝
- Silo B: 제약 기반 변이 생성 + 게이팅
- 공통 스키마 변환 및 산출물(manifest/log) 관리

### 3.2 실행 루프
- Planning: 실험 파라미터/실행안 정의
- Execution: 후보 생성/필터/랭킹
- Critique: 실패 원인/개선 포인트 분석
- Re-plan: 다음 라운드 계획 갱신

### 3.3 산출물
- run manifest
- candidate ranking outputs
- iteration history (계획 변경/선정 근거)

---

## 4. Evaluation Protocol (수치 없이 프레임만)

### 4.1 평가 축
- Planning Performance
- Critical Reasoning Performance
- Exploration Performance
- Traceability/Reproducibility

### 4.2 평가 단위
- 라운드 단위(Iteration-level)
- 후보 단위(Candidate-level)
- 실행 단위(Run-level)

### 4.3 비교 관점(선택)
- 초기 계획 대비 개선
- 라운드별 수렴 경향
- 모달리티별 기여도

---

## 5. Results (핵심: 구조만 고정)

### 5.1 후보 생성 및 선별 결과
- [표 1 자리] Silo/Arm별 생성-필터-선정 흐름
- [그림 1 자리] 후보 흐름 다이어그램

### 5.2 Plan-Critique-Explore 수행 결과
- [표 2 자리] 계획 변경/비판 제안/탐색 결과 매핑
- [그림 2 자리] 라운드별 성능 추이

### 5.3 추적성 및 재현성
- [표 3 자리] run_id/config_hash/provenance 완결성
- [그림 3 자리] 실행 trace 예시(계획→행동→결과)

### 5.4 실무적 의미 (원자력학회 맥락)
- 후보 발굴 파이프라인의 표준화 가능성
- 실험팀(웨트랩) 전달 가능한 근거 형태 확보

---

## 6. Discussion

### 6.1 잘 된 점
- 연구 루프 자동화와 의사결정 추적 가능성

### 6.2 한계
- 생물학적 성능 확정 아님 (in-silico evidence)
- 일부 기능/지표는 다음 단계 확장 필요

### 6.3 다음 단계
- 다음 주 수치/그래프 반영
- 후보 검증 프로토콜(실험 연계) 강화

---

## 7. Conclusion

- 본 시스템은 단순 후보 생성기가 아니라, 계획-비판-탐색 루프를 수행하는 AI Scientist 프레임워크임.
- 본 논문은 성능 수치 이전에, 연구 수행 구조와 재현 가능한 증거 체계를 확립한 데 의의가 있음.

---

## 부록 A: 표/그림 작성 템플릿 (빈 폼)

### [Table 1] Candidate Funnel by Silo/Arm
| Group | Generated | Filtered | Shortlisted | Note |
|------|-----------|----------|-------------|------|
| Silo A Arm1 | TBD | TBD | TBD | |
| Silo A Arm2 | TBD | TBD | TBD | |
| Silo A Arm3 | TBD | TBD | TBD | |
| Silo B | TBD | TBD | TBD | |

### [Table 2] Plan-Critique-Explore Mapping
| Iteration | Plan Update | Critique Point | Applied Change | Outcome |
|-----------|-------------|----------------|----------------|---------|
| TBD | TBD | TBD | TBD | TBD |

### [Table 3] Traceability Checklist
| Item | Available | Evidence Path |
|------|-----------|---------------|
| Run Manifest | TBD | TBD |
| Candidate Provenance | TBD | TBD |
| Iteration History | TBD | TBD |

### [Figure placeholders]
- Fig.1: Dual-Silo + Loop Overview
- Fig.2: Iteration Trend
- Fig.3: Traceability Example
