# pepMSND 자체 학습 ROI 평가
**날짜**: 2026-05-20  
**담당**: engineer-infra  
**태스크**: #13 — Layer 2 D-AA/cyclic 펩타이드 혈중 안정성 예측 자체 학습 타당성 평가  
**시간 제한**: 60분 (NO training without user approval)

---

## 1. 평가 요약

| 항목 | 결과 |
|------|------|
| 모델 파라미터 | 21.55M (Transformer 87.7% 지배) |
| 원본 훈련 데이터 | 635 samples (23 cyclic / ~116 D-AA) |
| PEPlife2 추가 데이터 | 4,500 samples (617 cyclic / 26 pure D-AA) |
| Combined D-AA 충족도 | 546/5,135 (10.6%) — **매우 희소** |
| SE3 구조 데이터 (원본) | ✅ 635 PDB 파일 보유 |
| SE3 구조 데이터 (PEPlife2) | ❌ 4,500 PDB 미생성 (ESMFold 필요, ~2-4h) |
| 학습 시간 (H100×4 est.) | ~2-4h (구조 예측 포함), 훈련 자체 <30분 |
| GPU 비용 (로컬) | ~$0.003 (전기요금만) |
| **ROI 권고** | **옵션 B 우선, 옵션 A 백업** |

---

## 2. 모델 구조 분석

### 2.1 PepMSND 5-Component Ensemble

| 컴포넌트 | 파라미터 | 비율 | 입력 |
|----------|----------|------|------|
| Transformer | 18,906,112 | **87.7%** | 아미노산 시퀀스 |
| CModel (KAN fusion) | 1,974,283 | 9.2% | 4개 encoder 128-dim concat |
| KAN | 343,296 | 1.6% | 시퀀스 특성 |
| SE3Transformer | 242,304 | 1.1% | PDB 3D 좌표 |
| GAT | 85,888 | 0.4% | 분자 그래프 (DGL) |
| **TOTAL** | **21,551,883** | 100% | |

> **주의**: Transformer가 전체 파라미터의 87.7% 지배 → SE3 기하학적 정보 기여 제한적

### 2.2 SE3Transformer 특이점

SE3.py 분석 결과:
- 입력: PDB 파일에서 원자 3D 좌표 (x, y, z)
- 구조: EquivariantLayer × 3 layers (hidden=128, heads=4)
- **PDB 파일 필수**: 모든 학습 샘플에 대해 구조 예측 선행 필요
- 원본 635개 PDB: `/PepMSND/Peptide structure Dataset/*.pdb` — ✅ 보유

---

## 3. 데이터 가용성 평가

### 3.1 PepMSND 원본 데이터셋 (Dataset.xlsx)

```
총 샘플: 635
Cyclic: 23 (3.6%)
Linear: 612 (96.4%)
D-AA (추정): ~116 (18.3%)
화학 modification: 52 (8.2%)
SST14: Row 1 — 훈련 데이터에 포함!
```

### 3.2 PEPlife2 외부 데이터 (이미 다운로드 완료)

경로: `_workspace/pepmsnd_local/data/peplife2_raw/`

```
총 레코드: 4,500
Cyclic (all variants): 617 (13.7%)
  - 단순 Cyclic: 49
  - Disulfide bond cyclic: ~568 (다양한 형태)
D-AA only: 25 (0.6%)  ← 매우 희소!
D or Mix chiral: 430 (9.6%)
Cyclic + D/Mix: 84 (1.9%)
숫자 반감기 보유: 4,431 (98.5%, hours/minutes/seconds 포함)
혈중 안정성 분포: 불안정(<1h) 45.3% / 안정(≥1h) 54.7%
chem modification 보유: 1,939 (43.1%)
```

### 3.3 Combined Dataset 가능성 (pepMSND + PEPlife2)

```
합산 총계: 5,135 (8.1× 확장)
Cyclic: 640 (12.5%)
D-AA/Mix: 546 (10.6%)
```

### 3.4 D-AA 데이터 부족 경고 ⚠️

| 카테고리 | 샘플 수 | 비율 |
|----------|---------|------|
| PEPlife2 pure D-AA | 25 | 0.6% |
| PEPlife2 D or Mix | 430 | 9.6% |
| PepMSND 원본 D-AA 추정 | ~116 | 18.3% |
| Combined D-AA (conservative) | ~546 | 10.6% |

> **결론**: D-아미노산 전용 샘플이 극도로 희소. ML 모델이 D-AA 특이적 안정성 패턴을 학습하기에 불충분.

---

## 4. 학습 비용 분석

### 4.1 H100 NVL ×4 학습 시간 추정

| 단계 | 시간 추정 |
|------|----------|
| PEPlife2 구조 예측 (ESMFold, 4,500 seqs) | 2-4시간 |
| 데이터 전처리 (descriptor 계산) | 30-60분 |
| 실제 훈련 (100 epoch, 5,135 samples) | 15-30분 |
| 하이퍼파라미터 탐색 (×10 run) | 2.5-5시간 |
| **총 계 (최초 1회)** | **5-10시간** |

### 4.2 GPU 비용

```
로컬 H100 NVL ×4 (전기요금 ₩50/kWh 기준):
  GPU 소비: 4 × 700W = 2.8kW
  10시간 훈련: 28kWh ≈ ₩1,400 ($1.05)
  → 비용 문제 없음, 시간 문제

클라우드 H100 ($3/h × 10h):
  → $30 (소규모 실험에 불필요)
```

### 4.3 핵심 병목: SE3 구조 예측

- PEPlife2 4,500 레코드에는 PDB 구조 없음
- ESMFold 실행 필요: ~2-4h (H100 단일 GPU)
- 또는 SE3 컴포넌트 **비활성화** 시 구조 없어도 학습 가능 (GAT + Transformer + KAN + CModel만 사용)

---

## 5. ROI 결론: 4 옵션 평가

### 옵션 A — 자체학습 (PEPlife2 + 원본 635)

| 항목 | 평가 |
|------|------|
| 데이터 가용성 | ✅ PEPlife2 이미 다운로드 |
| D-AA 개선 | ⚠️ WEAK — 5,135 중 546 (10.6%), 여전히 희소 |
| Cyclic 개선 | ✅ 640/5,135 (12.5%), 원본 3.6%보다 개선 |
| SE3 구조 필요 | ❌ 4,500 PDB 추가 생성 필요 (2-4h) |
| 코드 수정 | 필요 (경로 하드코딩, data loader 재작성) |
| 소요 시간 | 2-3일 (엔지니어링 포함) |
| 예상 성능 향상 | 미지수, D-AA 특이적 개선 보장 없음 |
| **ROI** | ⚠️ MEDIUM-LOW |

> **Transformer 지배 문제**: 파라미터 87.7%가 시퀀스 기반 Transformer → D-AA L/D 입력 토큰화가 동일하면 학습 불가. 현재 코드에서 D-AA 특이적 토큰 구분 여부 확인 필요.

### 옵션 B — 저자 weights 요청

| 항목 | 평가 |
|------|------|
| 비용 | ✅ 무료 |
| D-AA 성능 | ✅ 원저자 공식 학습 → 기대 최고 |
| 소요 시간 | 불확실 (이메일 응답 대기) |
| 위험 | ⚠️ 응답 없을 가능성 |
| 한국 연구환경 | 학술 협력 메일 → 긍정적 응답 기대 |
| **ROI** | ✅ HIGH (성공 시), ZERO (무응답 시) |

> **Task #12 상태 확인 필요**: pepADMET 저자 메일 작성 완료 여부 → 동일 저자에게 PepMSND weights도 요청 가능.

### 옵션 C — CycPeptMP 대체

| 항목 | 평가 |
|------|------|
| 태스크 적합성 | ❌ **부적합** |
| 이유 | CycPeptMP = 막 투과도 (PAMPA) 예측 — 혈중 안정성(반감기)과 다른 태스크 |
| 데이터 | CycPeptMPDB: PAMPA 6,698 / RRCK 181 / Caco-2 |
| 보완 가능성 | 막 투과도는 Layer 2의 별도 서브-태스크로는 유효 |
| **ROI for Layer 2 혈중안정성** | ❌ NONE |

> **단, 보완 활용**: CycPeptMP를 membrane permeability 서브-태스크로 Layer 2에 추가는 의미 있음.

### 옵션 D — 포기 (규칙 기반/웹 API 대체)

| 항목 | 평가 |
|------|------|
| 대안 1 | pepADMET 웹 API (https://pepadmet.ddai.tech) |
| 대안 2 | 규칙 기반: 반감기 히스토그램 + D-AA penalty |
| 대안 3 | pharmacology_guards.py에 stability rule 추가 |
| 개발 비용 | 낮음 (1-2일) |
| D-AA 처리 | pepADMET 웹에 D-AA 지원 여부 미확인 |
| **ROI** | ✅ MEDIUM — 빠르고 확실 |

---

## 6. 권고 결론

### 최종 권고: **B (저자 요청) 우선, A (자체학습 subset) 병행**

```
[즉시] 옵션 B: PepMSND 저자에게 weights 요청 이메일 발송
  → Task #12 pepADMET 문의에 PepMSND weights 추가 요청
  → 2주 무응답 시 옵션 A로 전환

[2주 내] 옵션 A (축소판): SE3 없이 GAT+Transformer+KAN+CModel만 사용
  → PEPlife2 구조 예측 불필요 (SE3 비활성화)
  → 5,135 샘플로 재학습, D-AA 토큰 구분 확인 필수
  → 예상 소요: 1-2일 엔지니어링

[선택적] CycPeptMP: Layer 2에 막 투과도 서브태스크로 추가
```

### D-AA 한계 인정

**현실적 판단**: 어떤 방식으로도 D-AA 특이적 혈중 안정성 예측은 데이터 한계로 정확도 보장 불가.
- 최선의 접근: D-AA 포함 여부를 binary feature로 추가하여 Transformer 입력에 명시적 신호 제공
- 또는: D-AA 변이체에 대해 안정성 +20-30% bonus를 rule-based로 적용 (문헌 기반 heuristic)

---

## 7. 학습 시작 조건 (사용자 승인 필요)

> ⚠️ **이 보고서는 평가 전용. 학습은 사용자 명시적 승인 없이 시작하지 않음.**

학습 시작 전 확인 사항:
1. [ ] 옵션 B 이메일 발송 완료 + 응답 대기 기간 설정
2. [ ] D-AA 토큰 구분 방식 결정 (소문자 구분, 별도 vocab 등)
3. [ ] SE3 비활성화 여부 결정 (구조 예측 시간 절약 vs 정확도)
4. [ ] pepADMET 웹 API D-AA 지원 여부 확인 (옵션 D 백업)
5. [ ] 학습 후 평가 지표: AUC-ROC (D-AA 서브셋 별도 평가 필수)

---

## 8. 환경 정보

```
conda env: pepadmet (Python 3.7.12), pepmsnd_local 클론
모델 경로: _workspace/pepmsnd_local/PepMSND/
체크포인트: _workspace/pepmsnd_local/checkpoints/ (현재 비어 있음 — weights 없음)
PDB 구조: 635개 보유 (원본 훈련 데이터)
PEPlife2: _workspace/pepmsnd_local/data/peplife2_raw/ (4,500 records)
학습 스크립트: PepMSND/Models/model.py (경로 하드코딩 수정 필요)
```

---

*Generated by engineer-infra | Task #13 | 2026-05-20*
