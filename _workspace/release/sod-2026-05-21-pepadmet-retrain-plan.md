# SOD 2026-05-21 — pepADMET 재훈련 Plan (분기 P)

> **작성**: researcher (action-items-closure-20260521 팀)
> **일시**: 2026-05-21
> **전제**: A5-0 진단 완료 (분기 P 가능 확정, v3 프롬프트 기준)
> **범위**: 분기 P (pepADMET 재훈련) Plan. 분기 Q (자체 모델)는 sanity fail 또는 데이터 부족 시 fallback.

---

## 0. A5-0 진단 결과 요약

| 항목 | 현황 | 판정 |
|------|------|------|
| 학습 코드 (`Train.ipynb`) | `_workspace/pepadmet_local/pepADMET/Train.ipynb` 존재 (253KB, 2 cell) | ✅ 가용 |
| 데이터 (`Toxicity.csv`) | 135 row (train:45/test:45/valid:45), binary_toxicity=30건 | ✅ 가용 |
| 가중치 (`toxicity_early_stop.pth`) | model/ 디렉토리 존재 | ✅ 가용 |
| 의존성 | Python 3.7.16, dgl 0.4.3, torch 1.13.1, PyBioMed-1.0, rdkit 2020.09.1.0, openbabel 3.1.1, modlamp 4.3.0, scikit-learn 1.0.2 | ⚠️ 구버전 (충돌 위험) |
| 라이센스 | GPL v3 | ⚠️ derivative 작업 GPLv3 전파 |
| **분기 판정** | **분기 P (pepADMET 재훈련) 진행** | ✅ |

**Train.ipynb 아키텍처 요약**:
- 멀티태스크 GNN (MGA 클래스, `utils/MY_GNN.py`)
- Atom feature dim: 40, Descriptor dim: 2133 (PyBioMed 계산)
- RGCN hidden: [64, 64], Classifier hidden: 320
- Dropout: 0.2 (train), 0.2 (rgcn)
- 4 태스크: `toxicity_nontoxicity` (binary), `toxicity_type_class` (6-class), `neurotoxicity_type_class` (4-class), `HC50` (regression)
- 5-fold CV (`args['times'] = 5`), max 300 epoch, early stop patience=50

---

## 1. 데이터 큐레이션 전략 (H1 외부 DB 허용)

### 1.1 현 Toxicity.csv 도메인 분포

| 항목 | 값 |
|------|-----|
| 총 row | 135 |
| binary_toxicity 라벨 | 30건 (toxic=15, non-toxic=15) |
| SS-bond 포함 binary 라벨 | **1건** (50aa, toxic=1) |
| 14aa 환형 SS-bond binary 라벨 | **0건** ← PRST 구조적 OOD 핵심 |
| HC50 범위 (훈련) | 0.80~2.61 (양수, log₁₀ 추정) |

**결론**: cyclic 14aa SS-bond 구조가 binary_toxicity 도메인에 전혀 없어 Octreotide/SST-14/PRST 전부 OOD 외삽 중.

### 1.2 외부 DB 후보

| DB | URL | 수집 가능 데이터 | cyclic SS-bond 엔트리 수 | 접근성 | 권장 우선순위 |
|----|-----|----------------|------------------------|--------|-------------|
| **DBAASP v3** | https://dbaasp.org/ | 항균·세포독성·용혈성 활성, SMILES, 구조 분류 | **1,095건** (SS-bond ribosomal) | 웹 검색·CSV 다운로드 | **1위** |
| **HemoPI / Hemolytik2** | https://webs.iiitd.edu.in/hemolytik/ | 용혈성/비용혈성 분류 라벨, SMILES | 906건 cyclic (2025 업데이트) | 웹 다운로드 | **2위** |
| **APD3** | https://aps.unmc.edu/AP/ | 항균활성 + 세포독성(hemolysis) | ~2,619건 (부분 cyclic) | 웹 검색 필터 | **3위** |
| **ChEMBL** | https://www.ebi.ac.uk/chembl/ | 펩타이드 bioactivity, ATC code | 다수 | API 쿼리 (대용량) | **4위** |
| **FDA 승인 cyclic 의약품** | 아래 섹션 | 임상 안전 라벨 (non-toxic) | 9종 | 수동 구성 | **보조** |

> **출처**: DBAASP v3 (Pirtskhalava et al. 2021 Nucleic Acids Res 49:D288, https://academic.oup.com/nar/article/49/D1/D288/5957160); Hemolytik2 (2025 biorxiv); APD3 (Wang et al. 2016 Nucleic Acids Res 44:D1087, https://pmc.ncbi.nlm.nih.gov/articles/PMC4702905/)

### 1.3 FDA 승인 cyclic peptide 의약품 안전 라벨 (non-toxic 기준 입력)

| 약물명 | 구조 | SSTR 관련성 | binary_toxicity 라벨 | 출처 |
|--------|------|------------|---------------------|------|
| **Octreotide** (Sandostatin®) | 8aa cyclic SS×1 | SSTR2/5 agonist | **0 (non-toxic)** | FDA 승인, 임상 안전 입증 |
| **Lanreotide** (Somatuline®) | 8aa cyclic SS×1 | SSTR2/5 agonist | 0 (non-toxic) | FDA/EMA 승인 |
| **Pasireotide** (Signifor®) | cyclic hexapeptide SS×1 | pan-SSTR | 0 (non-toxic) | FDA 승인 2012 |
| **Vasopressin** (ADH) | 9aa cyclic SS×1 | - | 0 (non-toxic 임상 용량) | FDA 승인 |
| **Oxytocin** | 9aa cyclic SS×1 | - | 0 (non-toxic) | FDA 승인 |
| **Atosiban** | 9aa cyclic SS×1 | - | 0 (non-toxic) | EMA 승인 |
| **Desmopressin** | 9aa cyclic SS×1 | - | 0 (non-toxic) | FDA 승인 |
| **Calcitonin** | 32aa cyclic SS×1 (N-term) | - | 0 (non-toxic) | FDA 승인 |
| **Eptifibatide** (Integrilin®) | cyclic heptapeptide | GPIIb/IIIa | 0 (non-toxic 치료 용량) | FDA 승인 |

→ 9종 × 1 항목 = **9 non-toxic 샘플** 직접 구성 가능 (SMILES: UniChem/PubChem에서 수집)

### 1.4 목표 데이터셋 구성

| 라벨 | 수집 출처 | 목표 수 | abort 기준 |
|------|---------|---------|----------|
| **non-toxic (0)** | FDA 승인 9종 + DBAASP 안전 cyclic SS-bond 항목 | 30+ | - |
| **toxic (1)** | DBAASP hemolytic cyclic SS-bond + HemoPI cyclic | 30+ | - |
| **합계** | | **60+ 신규 행** | 추가 < 50 row → **abort, 사용자 보고** |

**이전 학습 데이터와 병합 방식**: 기존 30 binary_toxicity 행 유지 + 신규 60+ 행 추가 = 총 90+ 행  
→ 불균형이 심하면 `pos_weight` / `multi_weight_six` 재계산 필요 (`MY_GNN.py` 이미 지원)

---

## 2. OOD Detection 메커니즘 비교

### 2.1 후보 비교표

| 방법 | 원리 | pepADMET dgl 0.4.3 통합 난이도 | 구현 우선순위 |
|------|------|-------------------------------|-------------|
| **Mahalanobis distance** | 마지막 hidden layer 임베딩의 훈련 분포까지 거리 측정 | **낮음** — forward hook으로 last hidden 추출 후 `numpy` 계산; dgl 버전 무관 | **1위** |
| **MC Dropout** | inference 시 dropout 켜고 N회 순전파, 분산 = uncertainty | **낮음** — `model.train()` 상태에서 inference loop; 기존 dropout=0.2 활용 | **2위** |
| **Label Smoothing** | 학습 시 소프트 타겟(0.9/0.1) → sigmoid saturation 완화 | **낮음** — BCEWithLogitsLoss에 smooth 라벨 입력 | 보조 (calibration) |
| **Focal Loss** | hard example에 집중, 쉬운 예측 gradient 억제 | **낮음** — loss 함수 교체만 필요 | 보조 (class imbalance) |
| **Deep Ensemble** | 독립 5 모델 평균 | **중간** — 5배 훈련 시간 | (A5Pb 실패 시 fallback) |

### 2.2 권장 구현 전략

**1단계 (A5Pb)**: Mahalanobis distance + MC Dropout 병행
- Mahalanobis: `utils/MY_GNN.py`의 MGA 마지막 레이어에 forward hook 삽입 → 훈련 후 class-conditional mean/covariance 저장 → inference 시 거리 계산
- MC Dropout: `EarlyStopping` 이후 `run_an_eval_epoch_heterogeneous(model, loader, train=True)` 으로 N=30 순전파 → std 계산
- 임계값: `mahal_dist > 3σ` (훈련 내 분포 95th percentile) → OOD 경고 플래그

**2단계 (선택)**: Label smoothing (binary task 0에 smooth=0.1 적용)
- 이유: 현재 binary_toxicity sigmoid saturation (confidence=1.0) 근본 원인은 hard label로 인한 boundary sharpness
- 구현: `pos_weight` 설정 유지 + 라벨 `0→0.1`, `1→0.9` 치환

### 2.3 dgl 0.4.3 통합 위험

| 위험 | 영향 | 완화 |
|------|------|------|
| dgl 0.4.3 는 PyTorch 1.13.1 에 의존 | CUDA 11.7 이하 필요 → H100 (CUDA 12.x)과 충돌 가능 | conda env 격리, `CUDA_VISIBLE_DEVICES=2` 지정, `cudatoolkit=11.7` 명시 |
| PyBioMed-1.0 Python 3.7 only | Python 3.8+ 에서 불안정 | conda env Python 3.7.16 고정 |
| openbabel 3.1.1 C 라이브러리 빌드 | conda-forge 채널 필요 | `conda install -c conda-forge openbabel=3.1.1` |

---

## 3. Sanity Check 메트릭 (v3 의무)

| 체크 항목 | 기준 | 실패 처리 |
|----------|------|---------|
| **Octreotide** → binary_toxicity | **< 0.5** | 즉시 abort + 이전 모델 유지 + 사용자 보고 |
| **SST-14 native** (AGCKNFFWKTFTSC) → binary_toxicity | **< 0.5** | 즉시 abort |
| **PRST-001~004** 4 score max-min 구별력 | **≥ 0.2** (변이 구별력 보장) | 즉시 abort |

**sanity 스크립트 위치 (예정)**: `pipeline_local/scripts/sanity_check_pepadmet.py`

```python
# sanity_check_pepadmet.py — 구현 스펙
SANITY_SEQUENCES = {
    "Octreotide":  "c1c[nH]cc1CC(NC(=O)C(CC(C)C)NC...)...",  # SMILES from PubChem CID 448601
    "SST14":       "AGCKNFFWKTFTSC",   # 원형 서열 → SMILES 변환 필요
    "PRST-001":    "AGCKNIIWKTIТSC",
    "PRST-002":    "AGCKNFIWKTITSC",
    "PRST-003":    "AGCRNFIWKTITSC",
    "PRST-004":    "AICKNFIWKTITSC",
}
PASS_CONDITIONS = {
    "Octreotide_binary_toxicity": lambda x: x < 0.5,
    "SST14_binary_toxicity": lambda x: x < 0.5,
    "PRST_spread": lambda scores: max(scores) - min(scores) >= 0.2,
}
```

---

## 4. 일정·자원 견적

| 단계 | 내용 | 예상 시간 | GPU 사용 |
|------|------|---------|---------|
| **A5Pa-1** 데이터 큐레이션 | DBAASP 필터링·SMILES 수집, HemoPI CSV 다운로드, FDA 9종 수동 SMILES 구성, 라벨 정합 | **4~8시간** (웹 수집 포함) | CPU only |
| **A5Pa-2** 데이터 전처리 | PyBioMed descriptor 재계산 (2133 차원), dgl graph 빌드 (`build_graph_dataset.py`) | **2~4시간** | CPU (PyBioMed 병목) |
| **A5Pb** conda env 셋업 | Python 3.7.16 + dgl 0.4.3 + torch 1.13.1 + cudatoolkit=11.7 환경 구성 | **2~4시간** | N/A |
| **A5Pb** OOD hook 구현 | Mahalanobis hook + MC Dropout 코드 (50~100 LOC) | **2~3시간** | N/A |
| **A5Pc** 재훈련 5-fold CV | max 300 epoch × 5 fold, batch=128, 데이터 90+ row | **0.5~2 GPU-hour** | H100 (CUDA_VISIBLE_DEVICES=2) |
| **A5Pd** Sanity check | Octreotide/SST-14/PRST 4종 추론 + 기준 검사 | **0.5~1시간** | GPU (추론) |
| **A5Pe** PR 작성 | 재훈련 weights + OOD hook + sanity 스크립트 통합 PR | **1~2시간** | N/A |
| **합계** | | **12~24시간** | 0.5~2 GPU-hour |

**병목**: conda env 셋업 (dgl 0.4.3 + H100 CUDA 버전 충돌). dgl 0.4.3이 CUDA 11.7 전용이어서 H100 (CUDA 12.3)과 충돌 시:
- **대안 A**: CPU 모드 학습 (`args['device'] = "cpu"`) — 소규모 데이터(90행)이므로 5-fold CV 총 ~1~2시간 CPU 예상
- **대안 B**: `dgl>=0.9` + `torch>=2.0` 으로 업데이트 (MY_GNN.py API 수정 필요 ~2시간)

---

## 5. GPL v3 영향 분석

| 항목 | 내용 | 판단 |
|------|------|------|
| pepADMET 원본 라이센스 | **GPL v3** (GitHub repo) | pepADMET 자체·수정·재배포 모두 GPLv3 의무 |
| 본 레포 LICENSE | **미명시** (루트에 LICENSE 파일 없음) | 현재 비공개·내부 사용 → GPL copyleft 의무 없음 |
| 재훈련 weights 라이센스 | pepADMET derivative → **GPLv3 적용** | 재훈련 weights 도 GPLv3. 외부 배포 시 소스 공개 의무 |
| Dynamic call 형식 (현재) | `pipeline_local/scripts/` 에서 subprocess 호출 → pepADMET 디렉토리 독립 | **현 형태 유지 권고** — GPL 전파 범위 명확히 격리 |
| 외부 공개 시 의무 | 본 레포 전체가 GPL 또는 GPL 호환 라이센스 필요 | 사용자 결정 필요 (실 법무 검토: D2 항목) |

**권고**: 현재 dynamic call (별도 디렉토리 `_workspace/pepadmet_local/pepADMET/`) 형태는 GPL 전파를 격리하는 안전한 구조. 재훈련 weights도 같은 디렉토리에 저장하면 라이센스 경계 명확.

---

## 6. Abort 조건 및 fallback

| 단계 | Abort 조건 | Fallback |
|------|-----------|---------|
| A5Pa 데이터 큐레이션 | 추가 < 50 row | 사용자 보고 + 분기 Q 검토 |
| A5Pb OOD 구현 | dgl 0.4.3 API 완전 막힘 | Label smoothing 만 적용 (OOD 가드 없이) |
| A5Pc 재훈련 | 학습 발산 / NaN | 이전 weights 유지, abort 보고서 |
| A5Pd Sanity check | Octreotide > 0.5 OR SST-14 > 0.5 OR PRST spread < 0.2 | **즉시 abort** + `a5-retrain-abort-2026-05-21.md` 생성 + 이전 모델 유지 |

**abort 보고서 형식** (`_workspace/release/a5-retrain-abort-2026-05-21.md`):
- 분기/단계/메트릭 수치
- 추정 원인 (데이터 부족/학습 발산/OOD 구현 실패)
- 권고 next step (분기 Q 전환 여부 사용자 결정)

---

## 7. 외부 DB 수집 쿼리 전략 (재현 가능성)

### DBAASP 쿼리 (dbaasp.org/search)
```
- Structural class: Cyclic
- Disulfide bonds: Yes (≥1)
- Experimental activity: Hemolysis (HC50 또는 MHC 기록)
- Length: 8~16aa
- Export: CSV (smiles, sequence, hemolysis_activity, hemolysis_mhc)
```

### HemoPI/Hemolytik2 다운로드
```
URL: https://webs.iiitd.edu.in/hemolytik/download.php
파일: hemolytic_peptides.csv, non_hemolytic_peptides.csv
필터: cyclic=True, disulfide=True
```

### APD3 쿼리
```
URL: https://aps.unmc.edu/AP/APD3/search/
Search: Hemolysis (active), Cyclic, S-S bond
Export: FASTA + activity table
```

---

## 8. §검증 필요

| 항목 | 이유 | 우선순위 |
|------|------|---------|
| dgl 0.4.3 + CUDA 12.3 (H100) 실호환성 | H100 드라이버와 cudatoolkit 11.7 혼용 가능 여부 불확실 | **HIGH** — conda env 셋업 첫 번째 확인 필요 |
| DBAASP 헤모라이시스 cyclic SS-bond 라벨 품질 | binary toxic/non-toxic 라벨이 HC50 기반인지, 임상 안전성 기반인지 불분명 | HIGH |
| Octreotide SMILES 내 SS-bond pepADMET descriptor 처리 | PyBioMed 2133 descriptor 중 SS-bond 특이적 descriptor 존재 여부 | MED |
| FDA 승인 9종 외 추가 cyclic SS-bond 의약품 존재 여부 | Eptifibatide 외 추가 안전 샘플 확보 가능성 | MED |
| pepADMET 원 논문 HC50 단위 정의 | log₁₀ vs 선형 확인 필요 (리뷰어-pharma §검증 필요 HIGH) | HIGH |

---

## 9. 권고 요약

1. **분기 P 진행** — Train.ipynb/Toxicity.csv/weights 모두 가용
2. **선행 작업**: conda env 셋업 + CUDA 호환성 검사가 병목 → **가장 먼저 테스트**
3. **DBAASP 우선 수집** — 1,095건 SS-bond 항목 중 cyclic 8~16aa + hemolysis 라벨 필터링 → 가장 풍부한 소스
4. **OOD 구현**: Mahalanobis distance (forward hook, 가장 적은 코드 변경) + MC Dropout (inference `train=True`, 기존 dropout 활용)
5. **Sanity check 절대 의무** — Octreotide < 0.5 실패 시 즉시 abort (무한 재시도 없음)
6. **GPL 분리** — dynamic call 형태 유지 (pepADMET 디렉토리 분리)

---

**다음 수신자**: team-lead (orchestrator) → backend 위임 결정
**관련 문서**: `_workspace/55_reviewer-pharma_prst-admet-ood-analysis.md`, `_workspace/release/goal-prompt-2026-05-21.md §A5`
