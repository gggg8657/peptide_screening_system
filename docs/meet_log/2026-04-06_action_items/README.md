# AI-RI Scientist 프로젝트 — 제3차 월간회의 액션 아이템

**문서 번호**: KAERI-AIRL-MOM-2026-003  
**일시**: 2026년 4월 6일 (일) 13:57  
**참석자**: 서호성, 김유종, 김동주 외 팀원  
**원본 회의록**: `../AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`  
**관련 문서**: KAERI-AIRL-MOM-2026-002, AI-RI Scientist 개발 전략 보고서

---

## 1. 회의 요약 (Executive Summary)

본 제3차 월간회의에서는 지난 회의(2026-03-23, MOM-002) 이후 달성된 주요 진전 사항을 점검하고, 향후 파이프라인 고도화 방향을 논의하였다.

### 핵심 진전 사항

1. **SSTR1/3/4/5 도킹 시뮬레이션 구현 및 셀렉티비티 테스트 완료** — cryo-EM 기반 PDB 구조를 활용하여 서브타입별 결합 여부를 확인함.

2. **스크리닝 파이프라인 기능 통합** — 클러스터링, ADMET(Fab-ADMET), Radiolysis 위험 평가, 셀렉티비티, 킬레이터 기능을 통합 완료.

### 주요 이슈

- **ADMET/혈청 반감기 예측 모델의 정확도 한계** — D-아미노산/수식 펩타이드 처리 불가
- **Top-K 후보 선정 기준의 체계화 필요** — 현재 ΔG 과의존 문제
- **고성능 GPU 인프라 확보 필요성** — 디퓨전 모델 기반 도킹 가속화를 위해

### 확정 사항

서호성 박사의 제안으로 **7단계 다단계 선별 체계**가 확정되었다 (§2 참조).

---

## 2. 7단계 다단계 선별 체계 (서호성 박사 제안, 확정)

> 전략 보고서의 Gate 1-5 체계와 회의 논의를 종합하여 확정한 선별 프로세스

| 단계 | 내용 | 선별 목표 | 담당 AI | 관련 A-Item |
|------|------|---------|---------|-----------|
| **(1)** | **SSTR2 Specificity** — 현행 도킹 ΔG 기반 (Rosetta FlexPepDock) | ~200-500개 | engineer-backend | A-01, A-05, A-10 |
| **(2)** | **Serum Stability** — ProtParam 1차 + MD(RMSD) 2차 (도구 확정 중) | 추가 필터 | reviewer-pharma | A-02 |
| **(3)** | **Toxicity** — Fab-ADMET *(=pepADMET, 2026-05-20 확인)* 또는 대체 모델 | 독성 후보 제외 | reviewer-pharma | A-03 |
| **(4)** | **Lead Compound 확정** — 복합 스코어링 기반 최종 선정 | 3-4개 확정 | reviewer-science | A-04, A-09 |
| **(5)** | **Amino Acid Modification** — Radiolysis 민감 잔기 치환 등 | 안정성 강화 | reviewer-chemistry | A-04 (연동) |
| **(6)** | **RI 표지 후 MD Simulation** — MM-GBSA 랭킹 재산정 → FEP/TI 정밀 계산 | 20-50개 → 상위 | engineer-backend | A-06 (연동) |
| **(7)** | **기타 예측** — 제형 안정성, RCY/RCP 예측 등 | 최종 검증 | RI팀 협업 | A-09 |

### 서호성 박사 보충 의견 (단계 6 세부)

- **1차 스크리닝**: Rosetta 도킹 ΔG → 200-500개 선별
- **2차 스크리닝**: MM-GBSA 랭킹 재산정 → 20-50개 선별 (이 단계부터 킬레이터 부착)
- **3차 스크리닝**: FEP/TI 정밀 ΔΔG 계산
- 도구: OpenMM 알케미컬 프로토콜, OpenFE 프레임워크, gmx_MMPBSA

---

## 3. 전체 Action Item 인덱스 (A-01 ~ A-10)

| 번호 | 제목 | 담당 | 기한 | 상태 | 정리 파일 | 프롬프트 |
|------|------|------|------|------|---------|---------|
| **A-01** | SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 (SSTR3 에러 포함) | AI팀 | 5월 회의 전 | ✅ PR #61 머지 | [A-01](A-01_SSTR_site_directed_docking.md) | [prompt](prompts/A-01_prompt.md) |
| **A-02** | 혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가) | AI팀·RI팀 | 5월 회의 전 | 🟡 부분 (D-AA HIGH-BLOCKER) | [A-02](A-02_serum_halflife_tools.md) | [prompt](prompts/A-02_prompt.md) |
| **A-03** | Fab-ADMET *(=pepADMET)* 정확도 검증 및 자체 학습 가능성 평가 | AI팀 | 5월 회의 전 | 🟡 부분 (HTTP 403, D-AA 미지원) | [A-03](A-03_Fab-ADMET_validation.md) · [research](A-03_research_fab_admet.md) | [prompt](prompts/A-03_prompt.md) |
| **A-04** | Top-K 후보 선정 복합 스코어링 체계 설계 (ΔG + 반감기 + 셀렉티비티 + ADMET 통합) | AI팀·RI팀 | 5월 회의 전 | ✅ PR #62 머지 (Tier S/A/B/FAIL) | [A-04](A-04_composite_scoring.md) | [prompt](prompts/A-04_prompt.md) |
| **A-05** | SST14 레퍼런스 ΔG 기준선 확립 및 가변 임계값 적용 (n회 반복 Mean 값 기준) | AI팀 | 5월 회의 전 | ✅ main `8e7e1cc` direct push | [A-05](A-05_SST14_reference_dG.md) | [prompt](prompts/A-05_prompt.md) |
| **A-06** | 디퓨전 모델 기반 도킹 가속화 PoC 수행 (정확도 vs Rosetta 비교) | AI팀 | 5월 회의 전 | ✅ 완료 — NOT_RECOMMENDED | [A-06](A-06_diffusion_docking_PoC.md) | [prompt](prompts/A-06_prompt.md) |
| **A-07** | DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집 | 서호성·안기범 | 5월 회의 전 | 🟡 부분 (외부 견적 대기) | [A-07](A-07_GPU_infra_quote.md) | [prompt](prompts/A-07_prompt.md) |
| ~~**A-08**~~ | ~~라이브러리 서버 마이그레이션 완료 및 검증~~ | ~~AI팀~~ | — | **삭제** | — | — |
| **A-09** | 최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행) | 전체 | 연속 | ✅ PR #63 머지 (PRST-001~004) | [A-09](A-09_final_candidates_synthesis.md) | [prompt](prompts/A-09_prompt.md) |
| **A-10** | SSTR3 도킹 에러 원인 분석 및 해결 | AI팀 | 5월 회의 전 | ✅ PR #60 머지 + SSTR4 시그니처 BUG 후속 해결 확인 | [A-10](A-10_SSTR3_docking_fix.md) | [prompt](prompts/A-10_prompt.md) |

> **A-08 [삭제]**: 외부망 H100×8 서버 배포가 이미 완료(§2.3)되어 본 항목은 삭제 처리. A-08 파일은 의도적으로 생성하지 않음.

---

## 4. 도메인별 담당 파일 링크

### 도킹 / 스코어링
| 파일 | 담당 에이전트 | 선행 조건 |
|------|------------|---------|
| [A-10_SSTR3_docking_fix.md](A-10_SSTR3_docking_fix.md) | `engineer-backend`, `reviewer-biology` | — |
| [A-01_SSTR_site_directed_docking.md](A-01_SSTR_site_directed_docking.md) | `engineer-backend`, `reviewer-biology` | A-10 완료 후 |
| [A-05_SST14_reference_dG.md](A-05_SST14_reference_dG.md) | `engineer-backend` | A-01 병행 권장 |
| [A-06_diffusion_docking_PoC.md](A-06_diffusion_docking_PoC.md) | `engineer-backend`, `engineer-infra` | A-07 연동 |

### 약리학 / ADMET
| 파일 | 담당 에이전트 | 선행 조건 |
|------|------------|---------|
| [A-02_serum_halflife_tools.md](A-02_serum_halflife_tools.md) | `reviewer-pharma`, `reviewer-chemistry` | — |
| [A-03_Fab-ADMET_validation.md](A-03_Fab-ADMET_validation.md) | `reviewer-pharma`, `reviewer-chemistry` | — |

### 복합 스코어링 / 최종 후보 선정
| 파일 | 담당 에이전트 | 선행 조건 |
|------|------------|---------|
| [A-04_composite_scoring.md](A-04_composite_scoring.md) | `reviewer-science`, `reviewer-pharma` | A-02·A-03·A-05 |
| [A-09_final_candidates_synthesis.md](A-09_final_candidates_synthesis.md) | 전체 팀 | A-04 완료 후 |

### 인프라
| 파일 | 담당 에이전트 | 선행 조건 |
|------|------------|---------|
| [A-07_GPU_infra_quote.md](A-07_GPU_infra_quote.md) | `engineer-infra` | — |

---

## 5. 다음 회의 일정

**예정일**: **2026-05-28 (목)** — D-8 (확정 2026-05-20)
**상세 일정**: [`meeting_schedule.md`](meeting_schedule.md) | **발표 준비**: [`MEETING_PREP_2026-05-28.md`](MEETING_PREP_2026-05-28.md)

**체크리스트** (회의 전 완료 목표 + 실제 상태):

- [x] A-10: SSTR3 도킹 에러 해결 — PR #60 머지, 별건 SSTR4 시그니처 BUG 후속 해결 확인
- [x] A-01: SSTR1/3/4/5 위치 지정 도킹 좌표 확정 — PR #61 머지
- [ ] A-02: 혈청 반감기 도구 비교 평가 — 🟡 부분 (D-AA HIGH-BLOCKER)
- [x] A-03: Fab-ADMET *(=pepADMET)* 정확도 검증 — 🟡 부분 (HTTP 403, D-AA 미지원)
- [x] A-05: SST14 레퍼런스 ΔG 기준선 확립 — main 직접 push
- [x] A-04: 복합 스코어링 체계 설계 — PR #62 머지
- [x] A-06: 디퓨전 모델 PoC — NOT_RECOMMENDED 결론
- [ ] A-07: GPU 서버 견적 수집 — 🟡 부분 (외부 견적 대기)
- [x] A-09: 최종 후보 3-4개 + 합성 의뢰서 — PR #63 머지 (PRST-001~004)

---

## 6. 이 디렉토리 사용 방법

### 파일 구조
```
docs/meet_log/2026-04-06_action_items/
├── README.md                   ← 본 파일 (회의 요약 + 전체 인덱스)
├── 00_MASTER_INDEX.md          ← 의존성 그래프 + pharmacology_guards 연동 현황
├── A-01_SSTR_site_directed_docking.md
├── A-02_serum_halflife_tools.md
├── A-03_Fab-ADMET_validation.md
├── A-04_composite_scoring.md
├── A-05_SST14_reference_dG.md
├── A-06_diffusion_docking_PoC.md
├── A-07_GPU_infra_quote.md
├── A-09_final_candidates_synthesis.md
├── A-10_SSTR3_docking_fix.md
└── prompts/
    ├── A-01_prompt.md  A-02_prompt.md  A-03_prompt.md
    ├── A-04_prompt.md  A-05_prompt.md  A-06_prompt.md
    ├── A-07_prompt.md  A-09_prompt.md  A-10_prompt.md
```

### Claude Code에서 액션 아이템 실행
```bash
# 특정 액션 아이템 프롬프트를 에이전트에 위임
/subagent-dev "@docs/meet_log/2026-04-06_action_items/prompts/A-02_prompt.md 참조하여 실행"
```

### 핵심 코드 연동
- `pipeline_local/scripts/pharmacology_guards.py` (Stage 5 약리학 가드)
  - A-02, A-03 결과 → `ENDPOINT_CONFIDENCE` 테이블 등록
  - H-06 가드: 미지원 항목은 "미지원" 명시 (추측 금지)
- 자세한 연동 현황 → [00_MASTER_INDEX.md](00_MASTER_INDEX.md) 참조

---

*최종 갱신: 2026-05-20 | 문서 번호: KAERI-AIRL-MOM-2026-003*
