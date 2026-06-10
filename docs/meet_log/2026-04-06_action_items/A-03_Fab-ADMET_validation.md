# A-03: Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가

> **📌 명칭 정정 (2026-05-20 researcher 확인)**: 회의록 표기 **"Fab-ADMET"은 실재하지 않으며 실제 도구는 [pepADMET](https://github.com/ifyoungnet/pepADMET)** (Tan et al. 2026 JCIM, DOI: `10.1021/acs.jcim.5c02518`). 본 파일에서 이하 "Fab-ADMET"은 pepADMET을 지칭. 상세 조사 결과: [`A-03_research_fab_admet.md`](A-03_research_fab_admet.md). 파일명은 회의록 추적성을 위해 보존.

## 메타
- **회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06 제3차 월간회의)
- **담당**: AI팀 (모델 검증, 파이프라인 통합), RI팀 (도메인 검토)
- **기한**: 5월 회의 전
- **상태**: 신규
- **출처**: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`

---

## 배경

Fab-ADMET는 펩타이드/소분자 ADMET (흡수·분포·대사·배설·독성) 예측 ML 도구로, 본 프로젝트의 후보 펩타이드 독성 사전 스크리닝에 활용 가능성이 제기되었다.

그러나 SSTR2 타겟 펩타이드는 다음과 같은 특수성을 가진다:
- **환형 펩타이드** (Cys-Cys SS bond 고리화)
- **D-아미노산 포함** (D-Phe, D-Trp 등 — Octreotide 계열)
- **비천연 아미노산 포함** (D-Nal — Lanreotide)
- **DOTA 킬레이터 결합** (방사성 금속 킬레이션 — theranostic)

이런 특수성이 Fab-ADMET의 학습 데이터와 입력 처리 범위에 포함되는지 검증이 필요하다.

---

## 수행 방법 (단계별)

### Step 1. GitHub 리포지토리 클론 및 문서 분석
- Fab-ADMET GitHub 리포지토리 접근 (URL 확인 필요 — 회의록에 명시되지 않음)
- 공개된 독성 모델 코드 및 학습 코드 클론
- README, 논문, Supplementary material에서 지원 입력 형식 확인

### Step 2. 원 논문 성능 지표 정리

| 지표 | 보고값 (논문) | 데이터셋 | 모달리티 |
|------|-------------|---------|---------|
| AUC | 미확인 | 미확인 | 미확인 |
| Accuracy | 미확인 | 미확인 | 미확인 |
| F1-score | 미확인 | 미확인 | 미확인 |

> **주의**: 위 값은 GitHub/논문 접근 후 채워야 함. 현재는 미확인 상태.

### Step 3. SSTR2 타겟 펩타이드 적용 가능성 평가

**확인 항목**:
- [ ] 학습 데이터에 **환형 펩타이드** 포함 여부
- [ ] **D-아미노산** (D-Phe, D-Trp, D-Nal 등) 입력 처리 가능 여부
- [ ] **비천연 아미노산** SMILES/입력 표현 지원 여부
- [ ] **DOTA 킬레이터** 결합 펩타이드 처리 가능 여부
- [ ] SST14 (AGCKNFFWKTFTSC) 직접 입력 테스트 결과

**벤치마크 세트** (A-02와 공유):
- SST14: AGCKNFFWKTFTSC
- Octreotide: D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol)
- Lanreotide: D-Nal-Cys-Tyr-D-Trp-Lys-Val-Cys-Thr

### Step 4. 자체 학습 요구사항 산정

| 항목 | 기준 값 | 비고 |
|------|--------|------|
| 필요 학습 데이터 규모 | 미확인 | 논문 기준 산정 필요 |
| GPU 요구사양 | 미확인 | VRAM, 연산 요구량 |
| 예상 학습 시간 | 미확인 | H100 NVL 기준 환산 |
| Fine-tuning 가능 여부 | 미확인 | 전이학습으로 데이터 절약 가능 여부 |

> 프로젝트 GPU 자원: H100 NVL ×4 (CUDA_VISIBLE_DEVICES=2 기본 설정)

---

## 판단 기준 / KPI

| 기준 | 임계값 | 비고 |
|------|--------|------|
| 논문 AUC | ≥ 0.80 | 통합 후보 기준 (일반적 ML 기준) |
| D-아미노산 처리 | 지원 필수 | 미지원 시 자체 학습 로드맵 전환 |
| 환형 펩타이드 지원 | 지원 우선 | SMILES 기반이면 가능성 있음 |
| 로컬 실행 가능 | 필수 | 민감 데이터 외부 전송 불가 |
| 자체 fine-tuning | 가능 우선 | SSTR2 도메인 특화 |

---

## 도구 특성 분석 (잠정)

| 특성 | Fab-ADMET | 비고 |
|-----|---------|------|
| 입력 형식 | 미확인 (SMILES 추정) | 클론 후 확인 필요 |
| 지원 ADMET 항목 | 미확인 | 독성, Caco-2, hERG 등 추정 |
| 환형 펩타이드 | 미확인 | SMILES 입력 시 가능성 있음 |
| D-아미노산 | 미확인 | SMILES 기반이면 표현 가능, 학습 데이터 포함 여부 별도 확인 |
| DOTA 결합 | 미확인 | 특수 처리 필요 |
| 로컬 실행 | 미확인 | GitHub 코드 존재 시 가능 |
| 라이선스 | 미확인 | 상업적 활용 가능 여부 확인 |

---

## 서호성 박사 의견

> "보다 정밀한 Serum Stability 혹은 인체 반감기 측정 프로그램을 찾아 사용할 필요, 특히 D-Phe 등 변형된 아미노산 분석 가능하면 더 좋음."

**의미**:
- ADMET 도구뿐만 아니라 **D-아미노산/비천연 AA 분석 가능 여부**가 핵심 평가 기준
- Fab-ADMET이 미지원 시 자체 학습 모델 구축 또는 대안 도구 탐색 필요
- ADMET 독성 외에 혈청 안정성(serum stability) 예측 기능도 탐색

---

## 본 프로젝트 매핑

### Stage 5 약리학 가드 연동
- **파일**: `pipeline_local/scripts/pharmacology_guards.py`
- **관련 가드**:
  - `ENDPOINT_CONFIDENCE`: Fab-ADMET 도구의 신뢰도 등급(P1~P4) 등록 예정
  - `HEURISTIC_FUNCTION_DISCLAIMERS`: Fab-ADMET 예측 함수의 한계 명세 필수 (H-06 가드)
  - `modification_conflict_rules`: D-아미노산·DOTA 수식과 ADMET 예측의 충돌 방지
- **H-06 가드 적용**: Fab-ADMET 예측값을 "계산 불가능을 계산 가능한 척"하지 않도록 disclaimer 추가

### 연동 위치
```
pipeline_local/scripts/pharmacology_guards.py
  └── ENDPOINT_CONFIDENCE["fab_admet"] = {
          "tool": "Fab-ADMET",
          "grade": "P?",  # 검증 후 결정
          "d_amino_acid_support": False,  # 검증 후 갱신
          "cyclic_peptide_support": False,
          "disclaimer": "학습 데이터 외 구조는 예측 신뢰도 낮음"
      }
```

### modification_conflict_rules 검토
- C-04 (D-Cys → SS bond 손상), C-07 (DOTA stoichiometry) 규칙과 Fab-ADMET 독성 예측의 정합성 확인
- Fab-ADMET가 D-아미노산 치환 펩타이드에 잘못된 독성 예측을 낼 경우 C-04 규칙에 주석 추가

---

## 의존성 / 연관 액션 아이템

| 액션 아이템 | 관계 | 설명 |
|------------|------|------|
| A-02 (혈청 반감기 도구) | 병렬 | 동일 벤치마크 세트 공유, 방법론 공유 |
| A-04 (복합 스코어링) | 하류 | ADMET 독성 점수를 복합 스코어에 반영 |
| A-09 (최종 후보 선정) | 하류 | Fab-ADMET 독성 스크리닝 결과를 최종 선정에 활용 |

---

## 미결 사항 (§검증 필요)

- [ ] Fab-ADMET GitHub URL 확인 및 리포지토리 클론 (회의록에 URL 미명시)
- [ ] 원 논문 AUC / Accuracy / F1 값 확인
- [ ] 학습 데이터에 환형 펩타이드 / D-아미노산 포함 여부 확인
- [ ] SST14 직접 입력 테스트 실행
- [ ] Octreotide / Lanreotide 입력 테스트 (D-아미노산 처리 확인)
- [ ] 자체 학습 시 GPU 요구사양 및 예상 소요 시간 산정 (H100 NVL 기준)
- [ ] 라이선스 확인 (상업적 활용 가능 여부)
- [ ] DOTA 킬레이터 결합 구조 처리 가능 여부 (SMILES 입력 형식 검토)
