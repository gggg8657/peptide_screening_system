# 발표 스크립트 — SSTR2 AI Co-Scientist 내부 보고

**예상 시간**: 15~20분 (발표 12분 + Q&A 8분)
**자료**: `04_presentation_slides.html` (Marp 12장)
**백업**: `03_SILO_B_MASTER_PRESENTATION_REPORT.pdf` (인쇄용)
**데모**: `http://localhost:5173` (Backend 8787 + Frontend 5173)

---

## 발표 흐름

### [0:00] 오프닝 — 슬라이드 1

> "SSTR2 타겟 방사성의약품 후보 스크리닝 AI 파이프라인 진행 현황 보고드리겠습니다."

- 프로젝트명, 날짜, 보고자

---

### [0:30] 전체 현황 — 슬라이드 2

> "먼저 전체 현황입니다."

**왼쪽**: 액션 아이템 상태
- "회의에서 나온 10개 액션 중 **7개 완료**, 1개 진행중, 2개 RI팀 담당입니다."

**오른쪽**: 핵심 수치
- "테스트 265개 통과, pharma 15개 메서드 검증, selectivity 5종 수용체 연결, pepADMET 독성 추론까지 성공했습니다."

---

### [1:30] 파이프라인 아키텍처 — 슬라이드 3

> "파이프라인 구조입니다."

- Mermaid 다이어그램 설명
- "SST-14 서열에서 시작해서 변이 생성 → FlexPepDock 도킹 → QC → 대안 스코어링을 거칩니다."
- "평가 단계에서 A~E 클러스터 분류, 약리 15종, 선택성 검증, pepADMET 독성까지 종합합니다."

---

### [3:00] 액션 대응 요약 — 슬라이드 4

> "각 액션별 대응 현황입니다."

- 7행 표 빠르게 훑기
- **A-01**: "PepCalc 대신 자체 구현, peptides 패키지로 78케이스 검증"
- **A-02**: "ADMETlab 서버 다운 + 소분자 전용 → pepADMET으로 전환, 독성 추론 성공"
- **A-03**: "SSTR1~5 실험 구조 CIF 등록, FlexPepDock 실제 도킹 연결"
- **A-04**: "A~E 5등급 분류 구현, 57개 테스트"
- "나머지 A-06, A-07은 RI팀 담당입니다."

---

### [4:30] pharma 검증 — 슬라이드 5

> "약리학적 계산기 검증 결과입니다."

- "lookup table에서 **16건 버그**를 발견해서 전수 수정했습니다."
- "수정 후 peptides 패키지 대비 **8/8 완벽 일치** 확인."
- "SS bond Cys 보정으로 pI가 9.04에서 **10.62**로 수정됐습니다. 방사성의약품의 신장 클리어런스 판단에 직접 영향."
- "MW 계산도 추가 — 1639.91 Da."

---

### [5:30] A~E 클러스터 — 슬라이드 6

> "후보 분류 체계입니다."

- 의사결정 트리 설명
- **A**: "결합 엘리트 — ddG ≤ -8, clash ≤ 5, FWKT 유지. 최우선 합성 대상."
- **B**: "선택성 특화 — SSTR2 vs off-target 차이 3 이상."
- **C**: "안정성 강화 — Instability Index 30 미만."
- **D**: "방사화학 최적 — GRAVY 중간, 전하 최소, 킬레이터 적합."
- **E**: "탐색 후보 — 나머지."
- "*pLDDT는 ESMFold 미실행 시 skip 처리됩니다."

---

### [7:00] pepADMET — 슬라이드 7

> "ADMETlab 대안으로 pepADMET을 도입했습니다."

**왼쪽**: 왜 ADMETlab이 안 되는지
- "SSL 만료, API 404, 소분자 전용."

**오른쪽**: pepADMET 현황
- "conda 환경 구축, MGA 모델 로딩, forward pass까지 성공."
- "descriptor 2133차원 실제 계산 통합 완료."
- "SST-14 독성 예측: toxic, hemostasis type."
- "†현재 ADMET 값은 in-house surrogate이며, pepADMET descriptor 통합으로 대체 예정."

---

### [8:30] Selectivity — 슬라이드 8

> "선택성 검증입니다."

- "SSTR1~5 실험 구조 CIF 5종 전부 등록."
- "FlexPepDock production mode로 실제 도킹 연결."
- "비동기 전환 완료 — UI에서 바로 실행 가능."

---

### [9:30] UI 데모 — 슬라이드 9-10

> "실제 대시보드 화면입니다."

- **슬라이드 9**: Silo B 전체 대시보드
  - "Candidate Table에 19개 후보, best ddG -47.66."
  - "각 패널 — Cluster, ADMET, Pharmacology, RCSB Match."

- **슬라이드 10**: Selectivity 페이지
  - "5/5 receptor loaded."

**[라이브 데모 전환 — 선택사항]**
- 브라우저 `http://localhost:5173` 열기
- 아카이브 4002 선택 → 후보 테이블 → 3D 구조 클릭
- Selectivity 페이지 → receptor 상태 확인

---

### [11:00] 시스템 감사 + 향후 계획 — 슬라이드 11-12

> "시스템 감사에서 발견한 이슈와 수정 현황입니다."

- "clash_max 버그, validation 시행 횟수, pLDDT 처리 — 3건 수정 완료."
- "ADMET 정확도와 ddG threshold는 진행 중."

> "향후 계획입니다."

- **즉시**: pepADMET descriptor 완전 통합, selectivity 비동기 완료
- **중기**: 전 모델 재현 6주, 대규모 실행
- **논의**: RI팀 A-06/A-07, pepADMET 우선순위, 실행 일정

---

### [12:00] Q&A

**예상 질문 + 답변 준비**:

| 질문 | 답변 | 근거 자료 |
|------|------|---------|
| "22,000개 돌린 거야?" | "이론적 처리 용량. 현재 검증 단계, 4,002건 아카이브." | presentation §향후 |
| "pepADMET 정확도는?" | "논문 AUC 0.885(binary), HC50 R²=0.474. 독성 예측은 보조 신호." | admet_alternative_plan |
| "selectivity 실제 결과는?" | "인프라 완성, 대규모 배치 실행 대기. estimation→production 전환 완료." | action_response A-03 |
| "druglikeness가 논문 없다?" | "in-house surrogate 명시. pharma 15메서드가 논문 기반 주요 지표." | system_architecture §4.2 |
| "Cluster A에 왜 아무것도 없어?" | "ddG ≤ -8 기준. 현재 실험은 소규모 검증용. 대규모 실행 시 A등급 출현 예상." | cluster_report.py |
| "LLM이 뭘 하는 거야?" | "Planner가 변이 전략, Critic이 실패 분석, Reporter가 보고서. ddG/clash 기반." | system_architecture §5 |

---

## 데모 체크리스트 (발표 10분 전)

- [ ] Backend 기동: `python3 -m uvicorn backend.main:app --port 8787`
- [ ] Frontend 기동: `npm run dev -- --port 5173`
- [ ] 4002 아카이브 데이터 로드 확인
- [ ] Selectivity 페이지 5/5 loaded 확인
- [ ] Ollama 불필요 모델 언로드 (랙 방지)
- [ ] 브라우저 탭 미리 열어두기
- [ ] PDF 백업 인쇄

## Fallback

- 데모 안 되면 → 슬라이드 스크린샷으로 대체 (이미 포함)
- selectivity 도킹 느리면 → "production mode, 실제 계산 중" 설명
- LLM 응답 느리면 → 아카이브 데이터로 전환
