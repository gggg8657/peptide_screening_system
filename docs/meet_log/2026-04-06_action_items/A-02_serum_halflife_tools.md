# A-02: 혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가)

## 메타
- **회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06 제3차 월간회의)
- **담당**: AI팀 (파이프라인 통합), RI팀 (in vitro 실측 검증)
- **기한**: 5월 회의 전
- **상태**: 🟡 **부분 완료** (2026-05-19 audit, PR #65 PPTX 슬라이드 3)
- **audit 결과 요약**:
  - 도구 7종 비교 완료 (ProtParam, HLP, PlifePred, PeptideRanker, PeptideStability, pepMSND, CAMSOL)
  - wrapper 등록 완료: `pipeline_local/scripts/predict_halflife_pepmsnd.py`
  - ENDPOINT_CONFIDENCE 7개 등록 (혈청 반감기 항목, main commit `4d3583c`)
- 🔴 **HIGH-BLOCKER (2026-05-20 확인)**: **D-아미노산 지원 도구 0개**. Octreotide(D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr) 등 D-AA 후보 반감기 예측 시 L-AA 유사도 4.83× 과대 추정. 5월 28일 회의에서 자체 ML 모델 학습 vs 실험 측정 병행 결정 필요.
- **출처**: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`

---

## 배경

SST14 기반 펩타이드의 최대 약점은 극히 짧은 체내 혈청 반감기(t½ ~3분). 프로젝트 TPP 목표를 충족하는 후보를 계산 단계에서 선별하려면 신뢰할 수 있는 in silico 반감기 예측 도구가 필수다.

**TPP KPI** (전략 보고서 기준):
- TPP-B: 반감기 ≥ 24시간
- TPP-C: 반감기 ≥ 72시간

이를 달성하는 핵심 전략은 D-아미노산 치환, 고리화, 지방산 아실화(PEGylation) 등의 화학적 수식. 그러나 대부분의 기존 도구는 **표준 L-아미노산만 지원**하므로 수식 후 후보에는 적용 한계가 존재한다.

---

## 수행 방법 (단계별)

### Step 1. 후보 도구 목록 작성
- ProtParam (ExPASy): 물리화학 속성 계산, 반감기는 N-end rule 기반 추정
- HLP (Half-Life Prediction, Sharma et al.): ML 기반 혈청 반감기 예측
- PlifePred: 펩타이드 반감기 예측 웹서버
- PeptideRanker: 생물활성 펩타이드 순위화 (반감기 간접 지표)
- PeptideStability (ML): GitHub/웹서버 공개 AI 모델
- 추가 후보: 자체 개발 ML 모델 (D-아미노산 대응)

### Step 2. 벤치마크 세트 구성

| 펩타이드 | 서열 / 구조 | 알려진 t½ | 특징 |
|---------|-------------|---------|------|
| SST-14 | AGCKNFFWKTFTSC (Cys3-Cys14 SS bond) | ~3분 (혈청) | 내인성, 표준 L-아미노산 |
| Octreotide (Sandostatin) | D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol) | ~100분 | D-아미노산 포함 고리형 |
| Lanreotide | D-Nal-Cys-Tyr-D-Trp-Lys-Val-Cys-Thr | ~수 시간 | D-Nal 비천연 아미노산 |
| RC-160 (Vapreotide) | D-Phe-Cys-Phe-Trp-Lys-Val-Cys-Thr | 중간 | Val 소수성 측쇄로 serum stability ↑ |

### Step 3. 평가 지표 산출
- 각 도구에 벤치마크 세트 입력
- 예측값 vs 문헌 실측값의 상관계수 (R²) 및 순위 일치도 (Spearman ρ) 산출
- 정성 평가: 순위 일치 여부 (SST14 < RC-160 < Octreotide)

### Step 4. MCP 파이프라인 통합 가능성 평가
- API 유무, 로컬 실행 가능 여부, Python 인터페이스 여부 확인
- `pipeline_local/scripts/pharmacology_guards.py` Stage 5 가드 연동 가능성

---

## 판단 기준 / KPI

| 기준 | 임계값 | 비고 |
|------|--------|------|
| 예측 정확도 R² | ≥ 0.5 | 통합 후보 기준 |
| 순위 일치도 Spearman ρ | ≥ 0.7 | 통합 후보 기준 |
| D-아미노산 지원 | ≥ 1개 도구 확보 | 필수 요구사항 |
| 로컬 실행 가능 | 우선순위 높음 | API 의존성 최소화 |
| 비천연 아미노산(D-Nal 등) 지원 | 보너스 | 미지원 시 별도 로드맵 |

---

## 도구 평가 매트릭스

| 도구 | D-아미노산 | 비천연 AA | API | 로컬 실행 | 신뢰도 | 비고 |
|-----|-----------|---------|-----|---------|--------|-----|
| ProtParam (ExPASy) | ❌ | ❌ | ✅ (웹) | ❌ | SST14 예측 ~4.4h (문헌 ~3min) | N-end rule 기반, 수식 불가 |
| HLP | 미확인 | 미확인 | 미확인 | 미확인 | SST14 예측 ~1.6초 → 신뢰도 낮음 | 검증 필요 |
| PlifePred | 미확인 | ❌ | ✅ (웹) | ❌ | 미평가 | 표준 AA만 지원 추정 |
| PeptideStability (ML) | 미확인 | 미확인 | GitHub/웹 | 확인 필요 | 미평가 | AI 모델, 재학습 가능성 |
| 자체 ML 모델 | ✅ (구축 시) | ✅ (구축 시) | N/A | ✅ | 구축 비용 있음 | D-아미노산 데이터 필요 |

> **주의**: 지방산 수식(lipidation) 포함 펩타이드(GLP-1 유사체 등)는 대부분의 도구가 지원하지 않음. 지질화 펩타이드 지원 여부 별도 확인 필수.

---

## 기존 평가 결과 (회의 발표 자료 기준)

| 도구 | SST14 예측값 | 실측값 | 평가 |
|-----|-------------|--------|------|
| ProtParam (ExPASy) | ~4.4시간 | ~3분 | 과대 추정, 수식 처리 불가 |
| HLP | ~1.6초 | ~3분 | 과소 추정, 신뢰도 검증 필요 |
| PeptideStability (ML) | 미측정 | - | AI 모델 활용 가능성 검토 필요 |

---

## 서호성 박사 의견

> "1차 Serum Stability는 ProtParam, Modification 후에는 MD(RMSD)로 Stability 예측. 최종적으로는 직접 Serum Stability 실험 측정 병행."
>
> "보다 정밀한 Serum Stability 혹은 인체 반감기 측정 프로그램을 찾아 사용할 필요, 특히 D-Phe 등 변형된 아미노산 분석 가능하면 더 좋음."

**의미**:
- 계산 도구는 **선별 스크리닝** 용도 (wet-lab 전 단계)
- D-아미노산/비천연 AA 처리 가능한 도구 확보가 핵심
- MD 시뮬레이션을 중간 단계 bridge로 활용 가능
- 최종 판단은 wet-lab 실측

---

## 본 프로젝트 매핑

### Stage 5 약리학 가드 연동
- **파일**: `pipeline_local/scripts/pharmacology_guards.py`
- **관련 가드**:
  - `SCALE_RANGES["predicted_half_life_hours"]`: (0.0, 1e4) — 예측값 범위 검증
  - `SCALE_RANGES["n_end_half_life_hours"]`: (0.0, 100.0) — N-end rule 기반 값 범위
  - `LITERATURE_VALUES["nend_half_life_mammalian_hours"]`: Varshavsky 1996 기준 정답
  - `ENDPOINT_CONFIDENCE`: 도구별 신뢰도 등급 (P1~P4) 반영 예정
- **H-06 가드**: `HEURISTIC_FUNCTION_DISCLAIMERS` — 계산 도구의 정직한 한계 명세 필수
- **H-05 가드**: N-end rule 반감기 예측 시 mammalian vs yeast species 혼동 방지

### 파이프라인 통합 위치
- `pipeline_local/scripts/pharmacology_guards.py` → `ENDPOINT_CONFIDENCE` 테이블에 도구 신뢰도 등록
- `AG_src/pipeline/pharma_properties.py` → 반감기 예측 로직에 검증된 도구 연동
- `HEURISTIC_FUNCTION_DISCLAIMERS` 에 선택 도구의 한계 명세 추가 (H-06 closure 유지)

---

## 의존성 / 연관 액션 아이템

| 액션 아이템 | 관계 | 설명 |
|------------|------|------|
| A-03 (Fab-ADMET) | 병렬 | ADMET 도구 평가와 동일한 방법론적 프레임워크 |
| A-04 (복합 스코어링) | 하류 | 반감기 KPI(TPP-B ≥24h, TPP-C ≥72h)를 복합 스코어에 반영 |
| A-09 (최종 후보 선정) | 하류 | 선별된 도구로 최종 후보 반감기 예측 결과 제공 |

---

## 미결 사항 (§검증 필요)

- [ ] HLP 도구 1.6초 예측 재현 및 신뢰도 검증
- [ ] PeptideStability ML 모델 GitHub 리포지토리 확인 (학습 데이터셋 포함 여부)
- [ ] 지방산 수식(lipidation) 지원 도구 존재 여부 확인
- [ ] D-아미노산 지원 도구 ≥1개 확보 계획 (자체 학습 모델 로드맵)
- [ ] MD 기반 stability 예측과 in silico 도구 예측의 상관관계 정량화
