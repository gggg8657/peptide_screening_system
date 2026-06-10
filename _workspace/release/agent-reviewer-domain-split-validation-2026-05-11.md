# Agent Validation Report — reviewer-{pharma,biology,chemistry,math} (Domain Split)

> harness Stage 4 산출물. `reviewer-science` 도메인별 4분리.

## 0. 메타

| 항목 | 값 |
|------|---|
| Stage | 8b |
| 분리 대상 | `reviewer-science` |
| 신설 에이전트 | `reviewer-pharma`, `reviewer-biology`, `reviewer-chemistry`, `reviewer-math` |
| 재정의 에이전트 | `reviewer-science` → 라우터·통합 판정 |
| 패턴 | **Expert Pool** (`reviewer-science`가 라우터, 4명이 도메인 전문가) — `ANALYSIS.md §5.3` |
| 작성일 | 2026-05-11 |

## 1. 분리 이유

기존 `reviewer-science`가 4개 도메인을 모두 흡수하여:
- 도메인 경계 모호한 산출물에서 어느 기준으로 판정했는지 추적 불가
- 약리학 정밀 검증과 수학적 수렴 검정이 같은 에이전트에 강제 — 전문성 희석
- `pharmacology_guards.py` Stage 5와 결합도 ↑인 약리학 검증이 다른 도메인과 혼재

→ 분리 후:
- 약리학(`reviewer-pharma`) + 환각 가드 모듈 직결
- 구조생물학(`reviewer-biology`) — SST-14·SSTR2 특화
- 합성화학(`reviewer-chemistry`) — modification·DOTA 라벨링
- 수학(`reviewer-math`) — NSGA-II·BO·통계
- `reviewer-science` = 라우터·통합 (기존 호출 호환성 보장)

## 2. 라우팅 규칙 (Expert Pool)

| 입력 키워드 | 라우팅 대상 |
|-----------|---------|
| 약리학·ADMET·PK/PD·반감기·Boman·GRAVY·Instability | `reviewer-pharma` |
| 구조·SS bond·GPCR·수용체·binding pocket·생물활성 | `reviewer-biology` |
| 합성·modification·D-amino·PEG화·아실화·DOTA·라벨링 | `reviewer-chemistry` |
| NSGA·베이지안·BO·GP·통계·수렴·p-value | `reviewer-math` |
| 다도메인 통합 | `reviewer-science` (라우터) |

## 3. should-trigger 쿼리 (각 4명, 도메인별 2개씩)

### reviewer-pharma
- "GRAVY 값이 Kyte-Doolittle 척도와 일치하는지 검증"
- "step08_stability의 반감기 예측이 합리 범위인지 확인"

### reviewer-biology
- "SST-14 Cys3-Cys14 이황화결합이 도킹 구조에서 보존되었는지"
- "SSTR1/3/4/5와 SSTR2의 binding pocket 차이"

### reviewer-chemistry
- "C18 지방산 아실화를 Lys10에 적용 가능한가"
- "PEG20kDa + DOTA 동시 결합 화학적 충돌 검토"

### reviewer-math
- "NSGA-II 100 세대 수렴 진단"
- "베이지안 최적화 acquisition 함수 적합성"

### reviewer-science (라우터·통합)
- "이 modification의 PK·생물활성·합성 가능성 통합 판정"
- "약리학과 수학적 최적화 결과의 일관성"

## 4. should-NOT-trigger (라우팅 정확성)

| 쿼리 | 잘못된 라우팅 위험 |
|------|---------------|
| "코드 리팩토링" | reviewer-code (위 4명 X) |
| "EOD 보고" | cursor-agent |
| "이 PR 머지해도 되나" | orchestrator |
| "환경 설치" | engineer-infra |
| "UI 색상 대비" | reviewer-uiux |
| "선행 연구 논문 조사" | researcher (수집은 researcher, 검증은 reviewer-*) |
| "구조 파일 변환" | engineer-backend |
| "GPU 메모리 부족" | engineer-infra |

## 5. A/B 비교 (Phase 6)

### 비교 시드
- 시드: "C18 지방산 아실화 Lys10 적용 + 반감기 영향 검증 + 합성 가능성 확인"

### 기대 결과
- **with split (분리 후)**: 
  - `reviewer-chemistry` 산출물 — 화학적 가능성 PASS
  - `reviewer-pharma` 산출물 — 반감기 예측 정량 + 출처
  - `reviewer-science` (라우터) — 두 산출물 통합 + 일관성 검사
- **without split (분리 전)**: 단일 `reviewer-science` 산출물에 두 도메인 혼재, 출처 일관성 약함, 통합 판정 명시적 단계 부재

### 측정 (실 트래픽 후)
| 메트릭 | 목표 |
|--------|------|
| 도메인 경계 명확성 (사용자 평가) | ≥ HIGH |
| 출처 인용 비율 (도메인별) | ≥ 80% |
| 라우팅 정확도 (잘못된 라우팅 비율) | ≤ 10% |

## 6. 기존 호출 호환성

- 기존 `reviewer-science` 호출은 모두 작동 — 라우터로 자동 분배
- 단일 도메인 호출 시 라우터는 직접 전문 리뷰어에 위임 후 자기는 통과 (오버헤드 최소)

## 7. CLAUDE.md 갱신

- [x] 트리거 키워드 표 4명 분 추가
- [x] 팀원 목록 4명 분 추가 (총 13명)
- [x] reviewer-science 설명 "라우터·통합 판정"으로 변경

## 8. §검증 필요

| ID | 항목 |
|----|------|
| VR-domainsplit-01 | A/B 비교 정량 측정은 실 트래픽 발생 후 다음 분기 회고에서 |
| VR-domainsplit-02 | 도메인 경계 충돌 빈도 — 분기 회고에서 모니터링 |
| VR-domainsplit-03 | reviewer-science 라우터의 통합 판정 품질 — 단순 패스스루 비율 모니터링 |

---

**End of Validation Report.**
