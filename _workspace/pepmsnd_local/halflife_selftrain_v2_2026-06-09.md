# Half-life 자체학습 v2 (feature 기반 회귀) — 2026-06-09

## 배경
- 2026-05-20 GAT 시도 실패: hold-out R²=−0.028, Spearman=−0.119, SST-14 변이체 ~1.8h 상수 붕괴. (P4 등록)
- 실패 원인: ① PEPlife2 종/장기/assay 혼재 노이즈 ② 표준20aa SMILES만 → modification(D-AA/고리화/말단캡핑) 무시 ③ 노이즈 그래프 GAT.

## v2 재설계 (근본 수정)
- **데이터**: PEPlife2 REST API 재다운로드 (Linear 3777 + Cyclic 49 → 파싱 t½+서열 3669건).
- **일관조건 필터**: test_sample = serum/plasma/blood/human → **2418건** (타깃 노이즈 감소).
- **modification-aware 피처**: 서열물성(length/AA조성/GRAVY/charge/cleavage sites/말단) + 메타(`has_D`, `is_cyclic`, `chem_mod`, `nter_capped`, `cter_capped`, `lipid_or_peg`).
- **모델**: GradientBoosting / RandomForest, log1p(hours) 회귀, 5-fold CV.
- 스크립트: `scripts/train_halflife_features.py`, 추론 `scripts/predict_halflife_features.py`, 모델 `data/halflife_v2/halflife_gbr.joblib`.

## 결과
| 지표 | GAT(v1, 실패) | **RF(v2)** | GBR(v2) |
|------|--------------|-----------|---------|
| CV Spearman (hours, in-domain) | **−0.119** | **0.784** | 0.746 |
| CV R²(log) | ≤0 | **0.642** | 0.592 |
| CV R²(hours) | <0 | 0.249 | 0.189 |
| 8-drug 벤치 Spearman | — | 0.265 | — |
| SST-14 변이체 변별 | ❌ 상수붕괴 | ✅ spread 0.55h | ✅ |

→ **실패했던 self-train 을 CV Spearman 0.78 / R²log 0.64 로 되살림** (in-domain 실제 예측력).

## 정직한 한계
- **8-drug 벤치(0.265) < 휴리스틱(0.855)**: 벤치(승인약물)는 PEPlife2(serum AMP) 분포 밖(OOD). 휴리스틱은 그 8점에 튜닝됨.
- **SST-14 절대값 과대**(RF 1.8h vs 실제 0.05h): PEPlife2 serum AMP 가 소마토스타틴(신장청소 빠름)보다 t½ 김 → 모델이 그 평균으로 회귀.
- fatty-acid 극단(semaglutide 168h)도 과소(~10h): PEPlife2 에 극단 지질화 사례 적음.

## 채택 권고
- **라이브 스크리닝 기본 half-life = 휴리스틱(A) 유지** (SST-14 절대 스케일·벤치 우수, 로컬·즉시).
- **RF(C) 는 검증된 대안으로 제공** (in-domain 상대순위 CV 0.78). `predict_halflife_features.py` 로 사용 가능.
- **후속 옵션**: 휴리스틱+RF **rank-ensemble**(둘의 상보성: 휴리스틱=SST-14 스케일, RF=데이터 일반화) — 채택 전 추가 검증 권장. pharmacology_guards 의 pepmsnd 등급을 P4→(CV R²log 0.64 반영) 상향 갱신 가능.
