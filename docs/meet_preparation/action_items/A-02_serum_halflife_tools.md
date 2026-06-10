# A-02: 혈청 반감기 예측 도구 비교 조사

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀·RI팀 | **기한**: 5월 회의 전 | **상태**: 🟡 wrapper 완료, D-AA HIGH-BLOCKER

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가)"

### 회의록 §2.2 배경 (p.3)
> "혈청 반감기 예측에 대해서는 N-end rule 기반 방법(약 30시간 예측), GPT 기반 모델(서비스 중단), 추가 웹/코드 기반 예측 도구 등 여러 접근법이 논의되었다. **GLP-1처럼 지질 수식(lipidation)이 포함되거나, Modification이 된 경우 기존 방법론으로는 분석이 어렵다**는 한계가 지적되었다."

### 회의록 §4 A-02 수행 가이드 (p.6)
> "후보 도구 목록 작성: ProtParam(ExPASy), HLP, PlifePred, PeptideRanker, PeptideStability(ML), 기타 웹/코드 기반 도구. 벤치마크 세트 구성: SST14(~3분), Octreotide(~100분), Lanreotide, RC-160 등 알려진 반감기가 있는 소마토스타틴 유사체 5-10종. 각 도구에 벤치마크 세트를 입력하고, 예측값 vs 문헌 실측값의 상관계수(R²), 순위 일치도(Spearman ρ)를 산출한다."

### 서호성 박사 보강 의견 (p.3, p.7)
> "1차 Serum Stability는 ProtParam으로 수행하고, Modification 진행 후에는 MD(RMSD)로 Stability를 예측한다. 최종적으로는 직접 Serum Stability를 실험 측정하는 것을 병행한다."

### 의도·범위·성공 기준
- **의도**: ⊿G 단일 의존 탈피 + 반감기 KPI(TPP-B ≥24h, TPP-C ≥72h) 계산 단계 통과 후보 선별
- **성공 기준**: 벤치마크 세트에서 R² ≥0.6 또는 Spearman ρ ≥0.7
- **요청 분류**: 연구·실험 + 기능

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근 (Layer 1 + Layer 2 분리)
- **Layer 1 (L-AA)**: PlifePred + HLE 회귀 + pepADMET → wrapper로 통합
- **Layer 2 (D-AA / cyclic)**: 로컬 PEPlife2-GAT 체크포인트 (재학습 진행 중)
- **Layer 0 (1차)**: ProtParam 휴리스틱 (Boman, instability index) — 서호성 의견의 ProtParam 1차

### 알고리즘·파이프라인
1. `predict_halflife_pepmsnd.py` 가 입력 시퀀스를 받아
2. ensemble_router가 도메인 판정 (L-AA / D-AA / cyclic / lipidation)
3. 도메인별 Layer 호출 → `routed_halflife` 출력
4. composite_scorer가 Tier 산정에 통합

### 대안 / Trade-off
- **N-end rule (Bachmair 1986)**: 단순·해석 가능, 단 ~30h 단일 예측 (분해능 부족)
- **PeptideRanker (UCD)**: 항균 펩타이드 활성 점수 — 반감기 X, 직접 적용 불가
- **GPT 기반**: 서비스 중단, 재현성 X
- **MD(RMSD) 2차** (서호성 의견): 신뢰도 높음, 단 GPU 시간 ↑
- §5 references/libraries/ 에서 도구 비교표 작성

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/scripts/predict_halflife_pepmsnd.py` ([확인] 본 점검 §4.6 검증)
- `pipeline_local/scoring/layer1_ensemble.py` (PlifePred 호출)
- `pipeline_local/scoring/layer2_ensemble.py` (PEPlife2-GAT)
- `pipeline_local/pepadmet_ood/ood_detection.py` (OOD 가드)

### 라이브 검증
- BE `/api/admet/batch` → 3-Layer Ensemble 호출 응답 ([확인])
- Layer 2 단위 테스트 PASS (`pipeline_local/tests/test_layer1_ensemble.py`, `test_composite_scorer.py`)

### 한계 (정직 명시)
- 🔴 **D-AA HIGH-BLOCKER**: D-Phe·Thr(ol) 등 변형 아미노산 함유 펩타이드의 신뢰 가능한 반감기 예측 도구가 **현재 부재**
- 🟡 **PEPlife2-GAT 재학습 R²=0.022** (seed 의존, audit 5/27) — 사실상 의사결정 불가
- 🔴 **enrichment 경로가 `run_routed_halflife`를 호출하지 않음** (PR #117 미머지, audit §1.1 ①)
- ProtParam (서호성 1차 도구)는 wrapper에 통합되어 있으나 라이브 호출 흔적 미확인 (`확인 필요`)

### 데모 가능 여부
- 🟢 wrapper 단위 호출 + Tier 산정까지 가능
- 🔴 **End-to-end "벤치마크 세트 R²/Spearman 측정"은 미완** → 발표 시 화면 시연 불가

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- 펩타이드 SST-14(t½ ~3분)는 임상 사용 불가 — TPP-B/C 충족 후보 도출이 본 프로젝트의 **약리학적 핵심**
- D-AA Modification 후 반감기 예측은 방사성의약품 워크플로의 **breakthrough 필요 영역**

### 향후 방향 (§5 웹 검증 필요)
- **PlifePred** — `[추정]` GitHub repo 실재 확인 + 라이선스 검토 (§5 references/libraries/PlifePred.md)
- **PeptideStability(ML)** — `[추정]` GitHub 공개 모델 검증 필요
- **MD(RMSD) 2차** — gmx_MMPBSA / OpenMM (§5 references 검증 완료 시 신뢰도 높음)
- **실험 병행** — `[확인 — 서호성 의견]` 직접 in-vitro Serum Stability 측정 필수

### 단기 목표 (다음 회의까지)
1. PR #117 머지 결정 (R² 재학습 합의 시)
2. 벤치마크 세트 5-10종 (SST14, Octreotide, Lanreotide, RC-160 + 3-6종) 정확도 측정
3. D-AA 블로커 해소 전략 (MD 2차 vs 외부 도구 도입) 6월 회의 결정 요청

### `[확인]` vs `[추정]` 분리
- `[확인]` Layer 1/2 wrapper 동작, 단위 테스트 PASS
- `[확인]` 회의록 N-end rule 30시간 예측, GPT 모델 서비스 중단
- `[추정]` PlifePred·PeptideStability 성능 — §5 검증 필요
- `[추정]` MD(RMSD) 2차의 실제 정확도 — `확인 필요`

---

## ⑤ 한 줄 보고 요약
> Layer 1/2 wrapper는 완성되었으나 **PR #117 미머지로 enrichment 경로가 3-Layer를 호출하지 않고**, **D-AA HIGH-BLOCKER**(PEPlife2 R²=0.022)와 **벤치마크 세트 정확도 측정 미완**으로 6월 회의 의사결정 안건이다.

---

## ⑥ L-AA Serum Stability — 알려진 성능과 한계 (Landscape)

### 6-1. 도구별 알려진 성능 (검증된 출처)

| 도구 | 학습 데이터 | 보고된 정확도 | 출처 (검증됨) |
|------|------------|--------------|--------------|
| **N-end rule** (Bachmair 1986) | E. coli, yeast — N-terminal 잔기 → in vivo t½ | 단일 N-term 잔기로 분류 (~30h 점 추정), short peptide에는 부적합 | DOI: 10.1126/science.3018930 ([R 검증]) |
| **ProtParam** (ExPASy) | 자연 L-AA 단백질 | Instability index <40 → 안정, Boman index 휴리스틱 (분해능 낮음) | https://web.expasy.org/protparam/ ([R 검증]) |
| **PlifePred** (Mathur 2018) | 펩타이드 t½ 데이터셋 (자연 L-AA 위주) | 보고 R²/MAE는 자연 펩타이드 한정 — 외삽 시 신뢰 저하 | DOI: 10.1371/journal.pone.0196829 (PLOS One, [R 검증]) |
| **HLP (Half-Life Prediction)** | IIITD Raghava 그룹, L-AA 펩타이드 | 자연 펩타이드 분류기, 정확도 보고 한정 | https://webs.iiitd.edu.in/raghava/ ([R 검증]) |
| **PeptideRanker** (UCD) | bioactive 펩타이드 활성 | **반감기 X — bioactivity 점수**. A-02 직접 적용 부적합 | (논문 확인, 서버 timeout) |

### 6-2. L-AA 펩타이드 분해 메커니즘 (생화학적 사실)

자연 L-AA 펩타이드는 혈청 내 다수 단백질분해효소(protease)에 의해 빠르게 분해된다:

| 효소 (대표 클래스) | 인지 부위 | SST14 분해 영향 |
|------------------|----------|----------------|
| Trypsin | Lys, Arg C-말단 측 | SST14의 K4, K9 절단 → 매우 빠른 분해 |
| Chymotrypsin | Phe, Trp, Tyr C-말단 측 | SST14의 F6, F7, W8 절단 |
| Elastase | 소형 잔기 (Ala, Gly, Ser) C-말단 측 | SST14 G2 절단 |
| Carboxypeptidase | C-말단 잔기 (한 잔기씩 분해) | C-말단 Cys-Cys 보호 효과 |
| Aminopeptidase | N-말단 잔기 (한 잔기씩 분해) | N-말단 Ala 노출 |

**SST-14 (AGCKNFFWKTFTSC) 의 t½ ~3분 (회의록 §2.2 p.3)** 은 위 효소 다중 인지 부위가 함께 작용한 결과이다.

### 6-3. L-AA 도구의 한계 (명시)

- **자연 L-AA에 학습됨** — D-AA / N-methyl / 환형화 / 비천연 아미노산이 도입되면 모든 도구가 **외삽 영역**으로 들어간다 (회의록 §2.2 명시: "GLP-1처럼 지질 수식이 포함되거나, Modification이 된 경우 기존 방법론으로는 분석이 어렵다").
- **점 추정만 제공** (uncertainty quantification 없음).
- **벤치마크 부족** — SST14/Octreotide/Lanreotide/RC-160 같은 약물 라이브러리에서 일관 R² 보고가 드물다 → 회의록 §4 A-02 가이드가 본 프로젝트 벤치마크 세트 구축을 요구한 이유.
- **혈청 vs 다른 매트릭스** — 대부분의 도구는 혈청 / 위장관 / 세포 내 분해를 구분하지 않는다.

---

## ⑦ D-AA Serum Stability — 알려진 사실과 도구 격차

### 7-1. D-AA Modification의 약동학적 효과 (확인된 사실)

D-아미노산은 자연계 단백질분해효소(trypsin, chymotrypsin 등)의 인지 부위와 입체화학(stereochemistry)이 반대이므로, **단백질 분해에 대한 저항성이 크게 증가한다**. 본 프로젝트의 벤치마크 세트 (회의록 §2.2 p.3) 가 그 정량적 증거이다:

| 펩타이드 | 시퀀스 | t½ (혈청) | 핵심 modification | t½ 증가 배수 (vs SST14) |
|---------|--------|----------|-----------------|----------------------|
| **SST14** (자연형) | AGCKNFFWKTFTSC (전 L-AA) | ~3분 (회의록) | 없음 | 1× (기준) |
| **Octreotide** (Sandostatin) | D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol) | ~100분 (회의록) | D-Phe(N-말단) + Thr(ol)(C-말단 CH₂OH 환원) | ~**33×** |
| **Lanreotide** | D-Nal-Cys-Tyr-D-Trp-Lys-Val-Cys-Thr | (수명 더 김, 정확치 회의록 미기재) | D-Nal + D-Trp + L-Val | 회의록 미기재 — `확인 필요` |
| **RC-160 (Vapreotide)** | D-Phe-Cys-Phe-Trp-Lys-Val-Cys-Thr | 보고된 t½는 회의록 미기재 | D-Phe + L-Val (소수성 측쇄로 stability ↑, 단 specificity ↓) | 회의록 §2.2 비고 |

> **출처 (검증됨)**: 회의록 §2.2 p.3 (벤치마크 세트) + **Lutathera (Lutetium Lu-177 DOTATATE)** FDA DailyMed (NDA 208700) — D-Phe-modified octapeptide 라벨링 사례 ([R 검증]).

### 7-2. D-AA 펩타이드 stability 예측 도구 격차 (현재 시점, 본 프로젝트 실증)

본 프로젝트의 **A-02 D-AA HIGH-BLOCKER** 는 다음 사실에서 유래한다:

| 도구 | D-AA 처리 가능성 | 보고 정확도 (D-AA) | 본 프로젝트 실증 |
|------|----------------|------------------|----------------|
| PlifePred | ❌ 학습 데이터에 D-AA 부재 | 외삽 — 보고 없음 | wrapper 통합 가능하나 출력 신뢰 X |
| HLP | ❌ | 외삽 — 보고 없음 | 동 |
| ProtParam | ❌ (L-AA 코드만 처리) | 미지원 — D-AA 입력 시 무시 또는 에러 | 서호성 의견 (p.3): "Modification(예: D-Phe)은 예측 불가" |
| **PEPlife2-GAT** (Layer 2 자체 학습) | △ D-AA 데이터로 재학습 시도 | **R² = 0.022** (재학습 후, seed 의존) — audit 5/27 | 본 프로젝트 직접 측정 — **사실상 의사결정 불가** |
| **pepADMET** | `[추정]` — 환형 펩타이드 포함, D-AA 지원 가능 (`확인 필요`) | 19개 ADMET 엔드포인트 보고, t½는 명시 미확인 | [R 검증] DOI: 10.1021/acs.jcim.5c02518, GPL-3.0. 자세한 D-AA 처리는 향후 검증 |
| **MD(RMSD) 2차** | ✅ 입체화학 직접 모델링 | 정량적 예측치 산출은 도구·력장 의존 | 서호성 의견 (p.3): "Modification 진행 후에는 MD(RMSD)로 Stability 예측" — 본 프로젝트 미구현 |
| **in vitro 실험** | ✅ 표준 | 결정적 (gold standard) | 서호성 의견: "직접 Serum Stability 측정을 병행" — wet-lab Ki/안정성 assay 시점에 진행 |

> **핵심 결론**: **현재 시점에서 D-AA 펩타이드의 혈청 반감기를 신뢰 가능한 정확도로 예측하는 in silico 도구는 부재**. 본 프로젝트의 7단계 §2 (Serum Stability) 통과 판정은 **MD 2차 검증 + 실험 실측의 병행 없이는 의사결정 불가**하다는 것이 4/6 회의의 명시적 결론이다.

### 7-3. D-AA stability에 영향을 미치는 추가 변형 (정성적 정리)

| Modification | 효과 | 본 프로젝트 도구 상태 |
|-------------|------|---------------------|
| **D-AA 단일 치환** (예: D-Phe at N-term) | t½ 10-50× ↑ (Octreotide 사례) | 정량 도구 부재 |
| **N-methyl** (Nα-methyl) | protease 저항성 ↑, 막투과성 일부 ↑ | 정량 도구 부재 |
| **환형화** (Cys-Cys → thioether / lactam / dicarba) | 형태 안정성 ↑ + 분해 저항성 ↑ | 회의록 p.8 변형 후보 표 (서호성 의견), 본 프로젝트 도구 부재 |
| **PEG 화** | renal clearance ↓ → blood t½ ↑ (다른 메커니즘) | 본 프로젝트 미고려 |
| **지질 수식** (GLP-1 style lipidation) | 알부민 결합 → t½ 매우 ↑ | 회의록 §2.2 명시 한계 |
| **불소화** (5-F-Trp, 3-F-Tyr) | 일부 protease 저항성 ↑ + radiolysis 저항 ↑ | 회의록 p.8 (서호성 의견 — Radiolysis 변형 전략) |

### 7-4. 본 프로젝트의 D-AA Serum Stability 대응 권고

1. **단기 (R-12 / 6월 회의 D-7)**:
   - 벤치마크 세트 (SST14, Octreotide, Lanreotide, RC-160 + 3-6종)에서 PEPlife2-GAT의 D-AA 정확도 측정 → 회의 자료
   - pepADMET의 D-AA 처리 가능성 정밀 확인 (`[추정]` 검증 → `확인` 또는 `근거 부족` 확정)

2. **중기 (R-11 + Q3)**:
   - **MD(RMSD) 2차 스크리닝 구현** (서호성 의견) — gmx_MMPBSA / OpenMM 활용 ([R 검증] §11)
   - D-AA·환형 펩타이드를 위한 자체 학습 데이터 수집 (pepADMET fine-tuning 또는 신규 모델)

3. **장기**:
   - **wet-lab serum stability assay 표준화** — RP-HPLC + LC-MS로 시간별 잔존율 측정 (회의록 §4 A-04 Radiolysis assay와 결합 가능)
   - in silico 출력 ↔ 실측 정정 사이클 (active learning)

> **약리학적 의미 (생명공학 청중)**: D-AA 도입은 단순한 "stability 향상" 이상이다 — 입체화학이 바뀌면 receptor 결합 모드도 미세하게 달라질 수 있고 (selectivity ↑↓), modification은 합성 비용 및 wet-lab assay 설계에도 영향을 미친다. 따라서 **A-02(stability) + A-04(scoring) + A-09(synthesis) 결정은 함께 묶여서 다뤄져야 한다**.

---

## 추적성 매핑
- 머지 PR: (wrapper) — PR #117 (ADMET divergence guard) 미머지
- 핵심 파일: `pipeline_local/scripts/predict_halflife_pepmsnd.py`, `scoring/layer{1,2}_ensemble.py`
- 점검 증거: `inspect_evidence/silo_b_docking.md` §3-Layer 매핑, audit `phase4-integration-and-refactor-plan.md` §1.1
- 회의록 출처: PDF p.3 §2.2, p.6 §4 A-02
- 관련 Action Item: A-03 (Fab-ADMET — Toxicity 단계 인접), A-04 (Top-K 통합), A-05 (레퍼런스)
- 추가 References (§6-7 보강): `references/references.md` 의 N-end Rule (DOI: 10.1126/science.3018930), PlifePred (DOI: 10.1371/journal.pone.0196829), pepADMET (DOI: 10.1021/acs.jcim.5c02518), Lutathera FDA DailyMed (NDA 208700) — 모두 [R 검증]
