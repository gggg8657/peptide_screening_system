# 멀티에이전트 AI Scientist 시스템 기반 SSTR2 후보 탐색: 계획·비판·탐색 수행 성능 중심 초안

**Draft Version**: v2 (Direction Shift)  
**목표 학회**: KNS 2026  
**핵심 방향**: "개발 결함 발견" 중심이 아니라, AI Scientist가 실제 연구 사이클(계획→실행→비판→재계획)을 얼마나 일관되게 수행했는지에 초점

---

## Abstract (KR, Draft)

본 연구는 SSTR2 표적 방사성의약품 후보 탐색을 위해 멀티에이전트 AI Scientist 시스템을 구축하고, 해당 시스템의 실험 수행 역량을 계획(Planning), 비판적 평가(Critical Reasoning), 탐색(Exploration)의 3개 축에서 평가하였다. 제안 시스템은 Dual-Silo 구조(Silo A: 3-arm virtual screening, Silo B: 제약 기반 돌연변이 생성)로 구성되며, 반복 루프에서 후보 생성, 품질 게이트, 랭킹, 재탐색을 수행한다. 평가 결과, 시스템은 단일 탐색 경로 대비 이종 모달리티 후보를 동시에 생성·선별할 수 있었고, 실행 trace를 기반으로 의사결정 경로를 재현 가능하게 기록하였다. 본 논문은 AI Scientist 자체의 방법론적 기여와 방사성의약품 탐색 적용 가능성을 함께 제시한다.

---

## 1. 논문 메시지 재정의

### 1.1 기존 메시지의 한계
- 기존 초안은 "에이전트가 결함을 찾아 수정했다"는 개발 방법론 비중이 큼
- KNS 제출 관점에서는 후보 탐색 성능/실험 파이프라인 관점 결과가 더 핵심

### 1.2 최종 메시지(권장)
> 본 시스템은 AI Scientist로서 실험 계획 수립, 후보 탐색, 비판적 재평가, 재탐색 루프를 수행하며,
> SSTR2 후보 탐색의 재현 가능한 계산 실험 프레임워크를 제공한다.

---

## 2. 평가 프레임 (Plan-Critique-Explore)

본 논문 결과를 3개 축으로 재구성한다.

### 2.1 Planning Performance
- 실험 계획 생성 횟수
- 계획 수정 횟수(라운드별)
- 수렴까지 소요 라운드
- 파라미터 변경 추적성(변경 사유 포함)

### 2.2 Critical Reasoning Performance
- 실패 유형 분류 개수(구조 품질/도킹/선택성/안정성 등)
- 비판 제안 채택률
- 비판 이후 지표 개선율

### 2.3 Exploration Performance
- 후보 생성 수(모달리티별)
- 게이트 통과율
- 최종 shortlist 크기
- 후보 다양성(중복 제거 후 고유 후보 수)

---

## 3. 시스템 개요 (코드 기준 요약)

- **Silo A**: Arm1(소분자), Arm2(펩타이드 변이), Arm3(De Novo) 실행 후 통합 점수화
- **Silo B**: 제약 기반 돌연변이 생성 + 필터 + 도킹/안정성 + 멀티오브젝트 랭킹
- 두 Silo는 `to_unified()`로 공통 후보 스키마로 변환 가능
- 결과는 manifest/run log 기반으로 추적 가능

> 주의: 논문 본문은 코드 실행 경로와 정합되게 기술 (미구현/가정 기능은 명시)

---

## 4. 결과 섹션 구조 제안 (교체용)

### 4.1 후보 생성 및 선별 결과
- 후보 생성 규모(arm/silo별)
- 게이트 통과 결과
- 최종 상위 후보 수

### 4.2 Plan-Critique-Explore 루프 성능
- 라운드별 계획 변경
- 비판 제안과 실제 개선의 연결성
- 탐색 폭(모달리티/다양성) 변화

### 4.3 재현성 및 추적성
- 동일 설정 재실행 시 결과 변동성
- run_id/config_hash 기반 추적
- 후보 선정 근거의 감사 가능성

---

## 5. 표/그림 초안

### Table 1. 후보 생성/선별 요약 (Silo/Arm별)
| 구분 | 생성 후보 수 | 필터 통과 수 | 최종 채택 수 | 비고 |
|------|-------------:|-------------:|-------------:|------|
| Silo A Arm1 | TBD | TBD | TBD | 소분자 |
| Silo A Arm2 | TBD | TBD | TBD | 펩타이드 변이 |
| Silo A Arm3 | TBD | TBD | TBD | De Novo |
| Silo B | TBD | TBD | TBD | 제약 기반 변이 |

### Table 2. Plan-Critique-Explore 루프 지표
| 지표 | 값 | 산출 근거 |
|------|---:|----------|
| 계획 생성 횟수 | TBD | run history |
| 평균 계획 수정/라운드 | TBD | plan diff |
| 실패 유형 분류 수 | TBD | critic logs |
| 비판 제안 채택률 | TBD% | proposal vs applied |
| 수렴 라운드 수 | TBD | convergence log |

### Table 3. 재현성/추적성 지표
| 지표 | 값 | 기준 |
|------|---:|------|
| 동일 설정 재실행 변동성 | TBD | score std |
| manifest 기록 완결성 | TBD% | required fields |
| 후보 선정 근거 링크율 | TBD% | provenance completeness |

### Figure 1. Dual-Silo + Iterative Loop
(기존 아키텍처 그림 재사용 가능)

### Figure 2. 라운드별 성능 추이
(예: 상위 후보 score, 게이트 통과율, 다양성)

---

## 6. `ai4sci-kaeri` 연동 데이터 추출 계획

다음 데이터는 상위 레포 `ai4sci-kaeri`에서 추출하여 본 초안의 TBD를 채운다.

1) run manifest / iteration logs  
2) candidate summary / ranking outputs  
3) gate pass/fail statistics  
4) parameter change history (plan/critic 루프)

추출 후 본 초안은 `paper_v2_ai_scientist_focus_draft.md` → `paper_v1.md`에 병합한다.

---

## 7. 한계 및 표현 가이드 (KNS 안전 표현)

- 임상/생물학적 효능 확정 표현 금지
- "computational evidence", "in-silico screening" 표현 사용
- 미구현 기능은 "향후 구현"으로 명시
- 방법론 강점은 결과 보조로 배치

---

## 8. 다음 액션

1. `ai4sci-kaeri`에서 수치 추출 (TBD 채우기)
2. Results 섹션 본문 교체
3. KR/EN Abstract 동시 정제
4. Word 양식 반영
