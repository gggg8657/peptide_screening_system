# 5월 28일 회의 발표 준비 (KAERI-AIRL-MOM-2026-004 예상)

> **회의 일자**: 2026-05-28 (목) | **작성**: 2026-05-20 (수, D-8) | **D-7 갱신**: 2026-05-21 (목) | **작성자**: team-lead (orchestrator)
> **목적**: 4/6 회의 Action Items 9건 audit + 5/19→5/20 추가 갭 정리 + 발표 시나리오
> **본 문서가 가리키는 자료**:
> - 어제 audit PPTX: [`_workspace/pptx/PRST_N_FM_ActionItems_Audit_2026-05-19.pptx`](../../../_workspace/pptx/PRST_N_FM_ActionItems_Audit_2026-05-19.pptx) (12 슬라이드)
> - 통합 STATUS: [`STATUS_2026-05-20.md`](STATUS_2026-05-20.md)
> - 일정 메모: [`meeting_schedule.md`](meeting_schedule.md)

---

## 1. D-마감 역산

| 마일스톤 | 일자 | 본 세션 할 일 (문서화) | 다른 세션 할 일 (코드) |
|---------|------|---------------------|---------------------|
| **D-8** (오늘) | 2026-05-20 (수) | ✅ 본 문서 + STATUS 작성 + 정리 파일 audit 반영 | feat/p1-sprint-integration PR 준비 |
| **D-7** (오늘) | 2026-05-21 (목) | 발표 시나리오 확정 + Q&A 예상 작성 | PR #85 3-Layer framework main 머지 완료, PR #90 binding_pocket fix 반영 |
| **D-6** | 2026-05-22 (금) | PPTX 갱신본 보강 (5/20 발견 사항) | A-02 D-AA 우회 또는 한계 명시 commit |
| **D-3** | 2026-05-25 (월) | 발표자료 확정 + 시연 리허설 | 핵심 PR 머지 완료 |
| **D-2** | 2026-05-26 (화) | 최종 슬라이드 검토 | 회귀 테스트 풀 패스 |
| **D-1** | 2026-05-27 (수) | 자료 배포 + 출력 | (코드 동결) |
| **D-Day** | 2026-05-28 (목) | 회의 진행 | — |

---

## 2. 발표 자료 구성 (3-tier)

### Tier 1: 완료 항목 (40% — 약 15분)
**메시지**: "4/6 회의 9건 중 6건 ✓ 달성, 1건 [삭제], 2건 △ 부분"

| ID | 핵심 산출물 | 발표 포인트 |
|----|-----------|----------|
| A-01 | PR #61, SSTR1/3/4/5 좌표 + 5종 정렬 | TM-align→cealign 대체 (RMSD 2.77~3.13Å 충족) |
| A-04 | PR #62, composite_scorer.py + Tier S/A/B/FAIL | 73 tests pass, Pareto+WSS+Tier 검증 |
| A-05 | main `8e7e1cc`, mean ΔG=553.857 REU (FlexPepDock) | σ=4.024 (KPI σ<5 충족, n≥10) |
| A-06 | DiffPepDock 평가 → **NOT_RECOMMENDED** | SS bond(Cys3-Cys14) 처리 불가, 선택 근거 |
| A-09 | PR #63, PRST-001~004 합성 의뢰서 | Gate-2 진입 후보 4건 + 의뢰서 |
| A-10 | PR #60, SSTR3_8XIR chain | 24 tests pass, smoke ddg=-92.09 |

### Tier 2: 부분 완료 + 블로커 (30% — 약 12분)
**메시지**: "도구 측면 식별 완료, 외부 의존 항목 남음"

| ID | 진행 | 블로커 | 회의 의사결정 요청 |
|----|------|-------|------------------|
| A-02 | 도구 7종 비교 완료 | **D-AA 지원 도구 0개** (HIGH) | 자체 학습 ML 모델 구축 승인 / 실험 측정 병행 |
| A-03 | "Fab-ADMET"→pepADMET 정정, wrapper 등록 | **HTTP 403** (REST 자동화 차단) + **D-AA 미지원** | 로컬 설치 GPL-3.0 + 법무 검토 (V-04) |
| A-07 | 점검 매트릭스 + 의사결정 양식 | 외부 벤더 응답 대기 | DGX H100 / B200 / 자체 빌드 선택 |

### Tier 3: 5/19 audit 이후 추가 발견 (20% — 약 8분)
**메시지**: "audit 이후 발견된 갭, 회의 전 처리 또는 5월 회의 이후 처리"

| 항목 | 영향 | 조치 |
|------|------|------|
| **SSTR4 시그니처 BUG** (`VILRYAKMKTA` SSTR1/SSTR4 중복) | 오프타겟 선택성 결과 오염 | D-7 fix 권고 |
| **3-Layer Ensemble framework main 반영** (PR #85) | Layer 1/2/3 라우팅·검증 코드가 main에 들어감 | 발표에서는 "구현 완료 + 한계 명시"로 정리 |
| **binding pocket 좌표 정합성 개선** (PR #90) | PDB/CIF 중심 좌표 4.076Å 차이 제거, A-01 docking 입력 신뢰도 개선 | A-01 후속 재산정 권고 |
| **PR #92~#100 후속 11 PR 진행** | LLM UX, Mol* mapping, FlexPepDock timeout/worker/sub-progress, orphan cleanup, FE badge, EOD 문서 main 반영 | 회의 자료에는 운영 안정화 진척으로 요약 |
| **biopython 미설치** | step06/07 stub 고착 가능성 | engineer-infra 위임 |
| **A-09 다양성 WARN** | 후보 4개 identity 86~93% (기준 80% 미달) | 14aa SS bond 제약으로 불가피 — 회의 양해 사전 공유 |
| **pepADMET HTTP 403** | 자동화 차단 | 로컬 설치 vs 우회 결정 |

### Tier 4: 요청 사항 (10% — 약 5분)
**메시지**: "다음 회의(2026-06)까지 결정·진행 필요한 외부 의존 항목"

1. **DGX 견적 결정** — A-07 (인프라 부서 협력)
2. **KAERI 법무 검토** — pepADMET GPL-3.0 vs CC BY-NC-SA 상업적 활용 가능성
3. **합성 발주 결정** — PRST-001~004 중 우선 후보 + 예산 + 일정
4. **다음 회의 일자** — 2026년 6월 일자 사전 합의

---

## 3. 핵심 메시지 (1-paragraph)

> **"4/6 회의 9건 중 6건 ✓ 달성. PRST-001~004 후보 4개 도출 + Gate-2 진입 의뢰서 작성 완료. 다만 D-AA 펩타이드의 in silico ADMET/반감기 예측 도구가 부재함을 확인 (A-02/A-03), 따라서 실험 측정 병행이 불가피. A-06 DiffPepDock은 SS bond 처리 불가로 NOT_RECOMMENDED 결정. 다음 단계는 PRST-001~004 합성·실측 + 자체 D-AA 모델 학습 + DGX 인프라 결정."**

---

## 4. Q&A 예상 (회의 사전 준비)

### Q1. "왜 도구 결과를 100% 신뢰하지 못하는가?"
A. 회의 KPI 기준 (혈청 반감기 ≥24h, ADMET 독성 ≤0.3 등)은 학습 데이터 도메인 안에서만 유효함. SST-14 유사체 + cyclic Cys3-Cys14 + D-AA + DOTA 킬레이터 조합은 대부분의 ML 도구 학습 데이터 밖에 위치한다. PR #85에서 Layer 1/2/3 framework는 main에 들어갔지만, Layer 2는 P4(R²=-0.028)로 의사결정용이 아니며 Layer 3 ADMET-AI도 H-06 외삽 가드로 `recommended_for_decision=False`를 강제한다. 따라서 계산 결과는 우선순위화 보조이고, Ki/혈청 안정성/ADMET wet-lab 실측이 필수.

### Q2. "PRST-001~004의 다양성이 부족한 이유?"
A. 14aa + Cys3-Cys14 SS bond + FWKT 핵심 잔기 보존 + Hard Cutoff 5개를 모두 통과하면 자연스럽게 수렴한다. 후보 4개 identity 86~93%는 본질적 제약으로 보고한다. PR #86 이후 합성 의뢰서는 OOD/ADMET 경고를 명시한 옵션 B로 정리됐고, 다양성 확보는 향후 BLOSUM 외 substitution 매트릭스, 환형화 전략 변경, 또는 후보 생성 목적함수 재가중으로 다룬다.

### Q3. "DiffPepDock NOT_RECOMMENDED 근거?"
A. (1) SS bond를 입력에서 풀어 도킹하므로 SST-14 단량체 형태 정확도 손실 가능성이 있다. (2) Rosetta 대비 약 10× 가속이지만 정확도 검증에서 RMSD 2.0Å 기준 미달로 판정했다. (3) GPU VRAM 120GB 이상 필요로 인프라 의존성이 크다. 다만 PR #90에서 PDB/CIF binding pocket 좌표 불일치(4.076Å)가 해소되어 A-01 계열 docking 입력의 정합성은 개선됐고, 회의에서는 "DiffPepDock은 보류, Rosetta/Boltz 입력 좌표는 개선"으로 구분해 설명한다.

### Q4. "5월 회의 자료에서 audit 이후 발견 사항을 왜 별도 tier로 분리?"
A. 5/19 audit은 4/6 회의 시점 요구의 충족도 측정이 목적이다. 5/20~5/21 발견과 머지는 audit 자체의 한계가 아니라 audit 이후 진행된 코드/통합 작업의 결과다. PR #85(3-Layer framework), PR #90(binding pocket fix), PR #92~#100(LLM UX, Mol* mapping, FlexPepDock 운영 안정화, FE badge, EOD 문서)을 별도 tier로 분리하면 audit 신뢰도를 유지하면서 후속 진척도 투명하게 보여줄 수 있다.

### Q5. "A-08은 정말 삭제해도 되는가?"
A. 회의 §2.3 "외부망 H100×8 배포 완료" 명시 → §3 A-08 [삭제] 처리. 5/20 sync 정찰에서 본 처리가 정합임을 재확인.

### Q6. "Layer 2 R²가 음수인데 발표에서 어떻게 설명할 것인가?"
A. 숨기지 않고 한계로 발표한다. PR #85 기준 Layer 2는 PEPlife2-GAT 로컬 재학습까지 구현했지만 R²=-0.028, Spearman ρ=-0.119, MAE=33.12h로 예측력이 없다. 따라서 현재 Layer 2는 "D-AA/cyclic 후보를 라우팅하고 실패를 계량적으로 보여준 framework"이지 의사결정 모델이 아니다. 6월 전까지는 DGL/공식 스택 재현, PEPlife2 데이터 정합성 재확인, HBM/실측 데이터 추가, 회귀 목적함수 재학습을 로드맵으로 제시한다.

### Q7. "PRST 후보 ADMET=1.00이면 합성 진행해도 되는가?"
A. 단독 근거로는 진행하면 안 된다. PRST-001~004 합성 의뢰서는 pepADMET binary_toxicity=1.00 정정과 OOD 외삽 가능성을 함께 명시했고, 사용자 결정은 그 경고를 붙인 옵션 B 진행이다. 1.00은 "즉시 폐기"가 아니라 "wet-lab ADMET/용혈/세포독성 assay를 합성 패키지에 반드시 포함"하라는 신호로 다룬다. 합성 우선순위는 Ki(SSTR2), 5-SSTR selectivity, 혈청 안정성, radiochemical purity와 함께 재판정한다.

### Q8. "5월 28일 회의 이후 6월 회의까지 어떤 작업을 할 것인가?"
A. 세 갈래로 정리한다. 첫째, DGL/pepADMET/PEPlife2 환경을 정비해 Layer 2 재학습 가능 상태를 만든다. 둘째, HBM 또는 wet-lab 측정 데이터를 받아 ADMET/반감기 보정셋을 축적한다. 셋째, PR #90 이후 좌표 정합성이 개선된 binding pocket 기준으로 A-01 docking 후속 재산정과 PRST-001~004 합성·assay 결과 반영을 진행한다. 목표는 6월 회의에서 "예측 framework"가 아니라 "실측으로 보정되는 의사결정 루프"를 보여주는 것이다.

### Q9. "현 도구 한계를 슈뢰딩거 도입으로 해결 가능한가? 비용·일정은?"
A. 현 도구 한계는 5가지 축으로 정리된다. PRST 후보의 ADMET=1.00은 Layer 3 OOD 외삽 가능성이 크고, Layer 2 half-life 회귀는 PR #112 이후에도 R²=0.022 수준이라 절대값 의사결정에 부족하다. Layer 1은 HLE 회귀 계수 부재로 시간 단위 합의 출력이 제한되고, A-06 DiffPepDock은 SS bond를 안정적으로 다루지 못해 NOT_RECOMMENDED로 판정했다. 또한 OpenMM/OpenFE/FlexPepDock/Boltz-2 조합은 학습 곡선과 단위 충돌을 계속 관리해야 한다.

슈뢰딩거 도입 검토 시 매핑은 명확하다. BioLuminate는 Bio/peptide 물리 기반 모델링 검토 축으로 Layer 3 OOD ML의 보완책이 될 수 있고, Desmond는 MD 기반 안정성 및 t½ 관련 검토, Glide는 cyclic peptide 도킹과 SP/XP 표준 스코어링, FEP+는 변이·표지 전후 상대 자유에너지 평가, Prime MM-GBSA는 lead compound 재평가, WaterMap은 제형 안정성/물 네트워크 검토에 연결된다. 이는 회의 §2.5의 (1) Specificity, (4) Lead Compound, (5) AA Modification, (6) RI 표지 후 MD, (7) 제형 안정성 단계와 직접 정합한다.

단, KAERI는 현재 Schrödinger 라이센스를 보유하지 않는 것으로 사용자 확인되었으므로 비용·일정은 이 문서에서 확정하지 않는다. 라이센스 모델(학술 vs 상업), 노드 수, 모듈별 cost-benefit, Desmond/FEP+ GPU 가속을 A-07 GPU 견적과 함께 검토해야 하며, Schrödinger Korea 영업 연락은 사용자 책임으로 진행해야 한다. KAERI 외부 SW 도입 승인 절차와 구매/계약 리드타임도 별도 확인이 필요하다.

권고는 5월 28일 회의에서 "6월 회의까지 도입 검토 진행"을 의사결정 요청으로 올리는 것이다. 책임은 KAERI 행정, 사용자, AI팀으로 나누고, 6월 회의 산출물은 견적, 모듈 범위, 도입 일정, GPU 연계 필요성, 1~3개월 학습 곡선 평가로 제한한다. 즉시 구매 결정이 아니라 현재 도구 한계를 해결할 수 있는 상용 워크플로우를 검토하는 단계로 제안한다.

---

## 5. 발표 자료 작성 체크리스트 (본 세션이 D-7~D-1 진행)

- [ ] **D-7 (내일)**: 본 문서 §2 Tier별 슬라이드 매핑 표 작성 (어제 PPTX 12장 + 신규 보강 슬라이드 식별)
- [ ] **D-7~D-6**: 신규 PPTX 슬라이드 5장 작성 (Tier 3 audit 이후 발견 + Tier 4 요청 사항)
- [ ] **D-3 (월)**: PPTX 통합본 빌드 (`_workspace/pptx/build_meeting_2026-05-28.js`)
- [ ] **D-3**: 시연 시나리오 작성 (PRST-001 합성 의뢰서 + composite_scorer 결과)
- [ ] **D-1 (수)**: PDF export + 인쇄본 준비

---

## 6. 다른 세션 위임 항목 (본 세션은 손대지 않음)

본 세션은 **문서화 주 담당**. 아래 코드 작업은 별도 세션 (codex / engineer-backend / engineer-infra)에 위임 권고.

| 항목 | 위임 대상 | 마감 |
|------|---------|------|
| Layer 2 DGL/PEPlife2 재학습 로드맵 실행 | codex / engineer-backend | 6월 회의 전 |
| PR #90 이후 A-01 docking 후속 재산정 | engineer-backend | 6월 회의 전 |
| biopython 설치 (step06/07 stub 해제) | engineer-infra | D-6 |
| AG_src/tests/agents/test_critic_normalization.py commit | reviewer-code | D-3 |
| worktree 3개 (feat-fe-*) main 머지 | reviewer-uiux | D-3 |

---

## 7. 변경 이력

| 날짜 | 변경 | 작성자 |
|------|------|--------|
| 2026-05-20 | 초안 — 회의 일자 5/28 확정 후 작성 | team-lead |
| 2026-05-21 | D-7 갱신 — PR #85/#90/#92~#100 main 반영, Q6~Q8 추가 | codex |
