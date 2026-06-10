# pepADMET 저자 학술 협력 문의 — 초안 정리

**작성일**: 2026-05-20  
**작성자**: sync (gate2-closure-20260520)  
**수신**: Prof. Jie Dong (jiedong@csu.edu.cn), Central South University  
**영문 초안 파일**: `_workspace/release/pepadmet-author-inquiry-letter-2026-05-20-EN.md`  
**발송 권한**: 사용자 검토 후 직접 발송

---

## 1. 문의 배경

### 연구 컨텍스트
- **기관**: 한국원자력연구원 (KAERI, Korea Atomic Energy Research Institute) — 정부출연연구기관, 비영리
- **연구 과제**: SSTR2(소마토스타틴 수용체 2형) 타겟 방사성의약품 후보 스크리닝 AI 파이프라인 (PRST_N_FM)
- **대상 서열**: SST-14 유사 환형 펩타이드 (14aa, Cys3-Cys14 SS bond, FWKT pharmacophore)
- **목적**: 방사성핵종(¹⁷⁷Lu) 표지 테라노스틱스 후보 최종 4개 확정 → Gate-2 (실험 검증) 진입

### pepADMET 도입 경위
- 회의(KAERI-AIRL-MOM-2026-003, 2026-04-06)에서 펩타이드 ADMET 예측 도구 도입 결정
- Tan et al. 2026 JCIM (DOI: 10.1021/acs.jcim.5c02518)을 주 평가 대상으로 확정 (V-01 완료)
- GitHub GPL-3.0 코드 로컬 설치 성공, 4-task toxicity 모델로 PRST-001~004 재검증 실행 완료 (V-02/V-03 완료)

### V-03 결과 요약 (로컬 4-task 추론 결과)
| 후보 | binary_toxicity | toxicity_type | hc50 | 판정 |
|------|----------------|--------------|------|------|
| PRST-001 (AGCKNIIWKTITSC) | 1.0 | hemostasis | -38.61 | FAIL (Hard Cutoff) |
| PRST-002 (AGCKNFIWKTITSC) | 1.0 | hemostasis | -41.72 | FAIL |
| PRST-003 (AGCRNFIWKTITSC) | 1.0 | hemostasis | -43.62 | FAIL |
| PRST-004 (AICKNFIWKTITSC) | 1.0 | hemostasis | -45.38 | FAIL |

> 현재 GitHub 버전(4-task toxicity)만으로는 25개 전체 endpoint 평가 불가. 논문 전문 및 전체 모델 접근 필요.

---

## 2. 문의 항목 3건

### V-02 — 논문 전문 요청
- **이유**: ACS paywall (DOI: 10.1021/acs.jcim.5c02518) 전문 미열람
- **필요 정보**: 각 endpoint별 정확한 모델 아키텍처, 학습 데이터셋, AUC/성능 지표, D-AA 처리 방식 (공식 문서에서 미명시)
- **요청**: 논문 PDF 또는 저자 제출용 preprint 공유

### V-04 — 25 endpoint 추가 모델 코드 + weights 요청
- **이유**: GitHub 공개 버전은 4-task toxicity (binary_toxicity, toxicity_type, neurotoxicity_type, hc50)만 포함
- **필요 항목**: 논문 기재 29개 endpoint 중 특히:
  - 반감기 (half-life in human/mouse blood — A-02 연동)
  - 생체이용률 (bioavailability, F)
  - 막 투과성 (PAMPA, Caco-2 — 환형 펩타이드 전용 모델)
  - BBB 투과성
- **요청**: 나머지 25개 endpoint 모델 코드 + pretrained weights 공유 또는 접근 방법 안내

### V-05 — KAERI 기관 라이선스 적용 가능 여부 확인
- **현황**: GitHub = GPL-3.0 (로컬 실행 가능), 웹 플랫폼 = CC BY-NC-SA 4.0 (비상업 한정)
- **KAERI 상황**: 정부출연연구기관, 비영리 학술 연구 목적, 논문 발표 예정 (비상업)
- **불명확 사항**: KAERI 내부 파이프라인 통합 및 논문 결과 공개가 CC BY-NC-SA의 "비상업(NC)" 조건 충족 여부
- **요청**: KAERI 사용 허가 여부 확인 및 필요 시 별도 MOU/협약 가능 여부 타진

---

## 3. 발송 전 체크리스트 (사용자 검토용)

- [ ] 소속 부서명 / 담당자명 / 서명란 확인
- [ ] V-03 결과 (PRST 4건 toxic 판정) 언급 여부 결정 — 협력 타진용이므로 간략 언급 권장
- [ ] V-04 요청 시 "환형 펩타이드 막 투과성 모델" 우선순위 명시 여부
- [ ] CC — co-PI 또는 RI팀 담당자 수신 여부
- [ ] 영문 초안 최종 검토 후 발송

---

## 4. 참조 파일

| 파일 | 내용 |
|------|------|
| `docs/meet_log/2026-04-06_action_items/A-03_research_fab_admet.md` | researcher 2차 조사 — 공식 정보/논문/대안 도구 |
| `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` | V-03 검증 결과 — 4-task 로컬 추론 |
| `_workspace/pepadmet_local/V02-V03_validation_2026-05-20.md` | V-02/V-03 설치·실행 상세 |
| `docs/meet_log/2026-04-06_action_items/A-03_Fab-ADMET_validation.md` | 액션 아이템 원본 정의 |
