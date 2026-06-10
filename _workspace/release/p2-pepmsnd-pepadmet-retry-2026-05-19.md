# PepMSND + pepADMET 재시도 결과 (2026-05-19)

> **수행**: researcher  
> **팀**: binding-pocket-pepadmet  
> **배경**: P1 sprint infra HTTP 403 확인 + 사용자 정정 (회의록 "Fab-ADMET" → pepADMET) 후 재접근  
> **검색 전략**: GitHub API (repos iyfoungnet/pepADMET, hmenghu/PepMSND) + 5채널 탐색 + 대안 도구 탐색  
> **검색일**: 2026-05-19

---

## § 정정 사항 요약

| # | 이전 기록 | 정정 내용 | 근거 |
|---|----------|---------|------|
| C-01 | P1 sprint: "PepMSND HTTP 403" | 올바른 웹 URL = `http://model.highslab.com/static/service` (README 확인). infra가 시도한 `/pepmsnd`는 비서비스 경로일 가능성 | PepMSND GitHub README |
| C-02 | P1 sprint: "pepADMET HTTP 403" | 웹 폼 POST는 작동 확인 (A-02 실 테스트 결과 존재). infra HTTP 403은 REST API 자동화 접근 시도였던 것으로 추정 | A-02 followup (7건 실 결과) |
| C-03 | pepADMET GitHub 라이선스 미기재 | **GPL-3.0** 확인 (상업적 사용 주의) | GitHub API metadata |
| C-04 | PepMSND GitHub 라이선스 "없음" | **MIT License** 확인 (README + LICENSE 파일) | PepMSND GitHub README |
| C-05 | pepADMET 교신저자 미확인 | **Prof. Jie Dong <jiedong@csu.edu.cn>** 확인 | pepADMET GitHub README |
| C-06 | 회의록 "Fab-ADMET" | pepADMET (JCIM 2025, DOI:10.1021/acs.jcim.5c02518) — 사용자 확인 완료 | A-03; 사용자 직접 정정 |

---

## 1. pepADMET 재접근 결과

### 1.1 정확한 출처

| 항목 | 내용 |
|------|------|
| 논문 | Tan X, Liu Q, Fang Y, Zhou M, Ouyang D, Zeng W*, Dong J*. "pepADMET: a novel computational platform for systematic ADMET evaluation of peptides." *J Chem Inf Model*, 2025. DOI: 10.1021/acs.jcim.5c02518 |
| 교신저자 | Prof. Jie Dong (공동) + Prof. Wenbin Zeng (공동) |
| **교신저자 이메일** | **jiedong@csu.edu.cn** (Central South University) |
| 소속 | DDAI Tech + Central South University (CSU) |
| 웹서버 | https://pepadmet.ddai.tech/ |
| 라이선스 | CC BY-NC-SA (웹서버); GPL-3.0 (GitHub) |

### 1.2 5채널 시도 결과

| 채널 | URL/명령 | 결과 | 비고 |
|------|---------|------|------|
| **GitHub** | https://github.com/ifyoungnet/pepADMET | ✅ **접근 가능** | GPL-3.0, Stars 22, Updated 2026-05-06 |
| **PyPI** | `pip install pepADMET` | ❌ **없음** | PyPI에 패키지 없음 |
| **HuggingFace** | huggingface.co/ifyoungnet 등 | ❌ **없음** | 검색 결과 없음 |
| **Docker Hub** | `docker pull pepADMET` | ❌ **없음** | 공식 이미지 없음 |
| **Zenodo/OSF** | 검색 시도 | ⚠️ **미확인** | WebFetch 제한으로 직접 확인 불가 |

### 1.3 GitHub 내용 상세 (핵심 발견)

```
pepADMET GitHub 파일 구조:
├── LICENSE (GPL-3.0)
├── README.md
├── Train.ipynb
├── build_graph_dataset.py
├── calculate_descriptors.py
├── data/
├── model/
│   └── toxicity_early_stop.pth  ← 45.8MB 사전훈련 가중치 (toxicity ONLY)
├── requirements/  (Python 3.7.16, torch 1.13.1, sklearn 1.0.2)
└── utils/
```

**중요**: GitHub에는 **독성(toxicity) 모델 가중치만** 공개됨.
- **반감기(half-life) 모델 가중치: 비공개** — 웹서버에서만 운영
- **BBB, 생체이용률 등 나머지 27개 endpoint: 비공개**
- 로컬 독성 예측은 가능하나, 29개 통합 ADMET는 웹서버 사용 필수

### 1.4 웹서버 접근 방법 (HTTP 403 정정)

**A-02 실 테스트 결과 (2026-05-19)**: Django 폼 POST 방식으로 7건 실 예측 성공.  
infra HTTP 403은 REST API 자동 접근 시도였을 가능성이 높음.

접근 가능 경로:
```
# 웹 폼 POST (작동 확인)
POST https://pepadmet.ddai.tech/calcpep/half-life/
POST https://pepadmet.ddai.tech/calcpep/bbb/
POST https://pepadmet.ddai.tech/calcpep/tox/

# REST API (HTTP 403 — 미지원 또는 API 키 필요)
# infra가 시도한 방식으로 추정
```

### 1.5 API 키 / 학술 접근 신청 방법

공식 API 키 프로그램 없음. 학술 접근 신청:
1. **저자 직접 연락**: jiedong@csu.edu.cn (Prof. Jie Dong, CSU)
   - 요청 내용: 학술 라이선스, 반감기 모델 가중치, 로컬 배포 가능 여부
   - 기관 정보: KAERI (한국원자력연구원) + 방사성의약품 후보 스크리닝 연구
2. **CC BY-NC-SA 조건**: 비상업적 학술 사용은 귀속(attribution) 조건으로 허용
3. **GPL-3.0 (GitHub)**: 파생물 동일 라이선스 의무

### 1.6 테스트 결과 (A-02에서 이미 완료)

| 펩타이드 | HBN (min) | 실측 t½ | 신뢰도 |
|---------|----------|---------|--------|
| SST-14 (AGCKNFFWKTFTSC) | 14.484 | ~3분 | ❌ 4.83× 과대 |
| Octreotide (D-AA 근사) | 84.008 | ~90분 | △ 우연 근접 (D-AA 무시) |
| D-AA 직접 입력 | 불가 | — | ❌ 미지원 확정 |

**D-AA 지원 여부: 확정 NO** (modification 40종 중 D-AA 0개, A-02 실 테스트 확인)

---

## 2. PepMSND 재접근 결과

### 2.1 정확한 출처

| 항목 | 내용 |
|------|------|
| 논문 | Wang et al. "PepMSND: Integrating Multi-level Feature Engineering and Comprehensive Databases to Enhance in vitro/in vivo Peptide Blood Stability Prediction." *Digital Discovery* (RSC), 2025. DOI: 10.1039/D5DD00118H |
| bioRxiv 선행 | DOI: 10.1101/2024.12.12.628290 (2024-12-12) |
| 웹서버 | **http://model.highslab.com/static/service** (README 정확한 URL) |
| 데이터베이스 | http://model.highslab.com/static/Database.html |
| GitHub | https://github.com/hmenghu/PepMSND |
| 라이선스 | **MIT License** |

### 2.2 5채널 시도 결과

| 채널 | URL/명령 | 결과 | 비고 |
|------|---------|------|------|
| **GitHub** | https://github.com/hmenghu/PepMSND | ✅ **접근 가능** | MIT License, Stars 7, Updated 2026-05-05 |
| **PyPI** | `pip install pepmsnd` | ❌ **없음** | PyPI 패키지 없음 |
| **HuggingFace** | huggingface.co 검색 | ❌ **없음** | 검색 결과 없음 |
| **Zenodo** | 논문 supplementary | ⚠️ **미확인** | WebFetch 제한 |
| **Docker** | Docker Hub 검색 | ❌ **없음** | 공식 이미지 없음 |

### 2.3 GitHub 내용 상세 (핵심 발견)

```
PepMSND GitHub 파일 구조:
├── LICENSE (MIT)
├── README.md
├── requirements.txt  ← DGL CUDA 12.1, Flask, BioPython, torch
├── Vocab.txt
├── efficient_kan/
├── Baseline models/
├── Dataset/
│   └── Dataset.xlsx  ← 635개 데이터 (~960KB), 전체 공개
├── Models/           ← 모델 코드 (.py 파일만, 가중치 없음)
│   ├── GAT.py, KAN.py, SE3.py, Transformer.py
│   ├── model.py (메인 훈련 스크립트)
│   ├── modelsfusion.py, pretreatment.py
└── Peptide structure Dataset/
```

**중요**: **사전훈련 가중치(.pth) 미포함** — 로컬 사용 시 직접 훈련 필요.
- 635개 데이터 (`Dataset.xlsx`)로 `python ./Models/model.py` 실행 가능
- CUDA 12.1 + DGL 2.4.0 환경 필요 (requirements.txt 확인)

### 2.4 웹 URL 정정 (중요)

P1 sprint infra가 시도한 URL과 README의 정식 URL 불일치 발견:

| 구분 | URL |
|------|-----|
| infra 시도 (추정, HTTP 403) | http://model.highslab.com/pepmsnd |
| **README 정식 URL** | **http://model.highslab.com/static/service** |
| 데이터베이스 | http://model.highslab.com/static/Database.html |

**권고**: infra에 정식 URL로 재시도 요청.

### 2.5 모델 타입 분류

| 항목 | 내용 |
|------|------|
| 출력 형식 | **이진/다중 분류** (unstable / stable / highly stable / non-degradable) |
| 연속 t½ 값 | **없음** — TPP KPI(≥24h, ≥72h) 직접 판정 불가 |
| 성능 | ACC=0.867±0.043, AUC=0.912±0.037 (평균); in vivo human blood: ACC=0.919, AUC=0.905 |
| D-AA 지원 | 웹 인터페이스: **NO** ("natural amino acids only") |
| D-AA (로컬) | 코드 레벨 지원 가능성: **미검증** (Dataset.xlsx에 D-AA 엔트리 포함 여부 확인 필요) |
| 훈련 데이터 | 635 펩타이드 혈중 안정성 데이터 (공개됨) |

### 2.6 로컬 설치 방법 (GitHub 기반)

```bash
# 1. Clone
git clone https://github.com/hmenghu/PepMSND
cd PepMSND

# 2. 환경 구축 (CUDA 12.1 필요 — H100 NVL 사용 가능)
pip install -r requirements.txt
./replace.sh

# 3. 학습
python ./Models/model.py

# ⚠️ 주의: 사전훈련 가중치 없음 — 635개 데이터로 직접 학습 필요
# ⚠️ 주의: DGL 2.4.0+cu121 설치 시 별도 DGL 공식 채널 필요
```

---

## 3. 대안 도구 매트릭스 (갱신판)

### 3.1 반감기 예측 도구

| 도구 | 등급 | 출력 | D-AA | 로컬 | R²/AUC | 비고 |
|-----|------|------|------|------|--------|------|
| PlifePred2 | **P4** | 연속 t½ | △ (flag) | ✅ pip | 미검증 | peptools env 설치됨 |
| pepADMET (half-life) | **P1** | 연속 t½ (min) | ❌ | ❌ 웹전용 | R²=0.84~0.90 | 웹폼 POST 작동 |
| PepMSND | **P3** | 분류 등급 | ❌ (웹), ? (로컬) | ⚠️ 학습 필요 | AUC=0.912 | 정식 URL 정정 |
| PlifePred | P2 | 연속 t½ | △ (modified) | ❌ 웹전용 | R²≈0.55 | 웹서버 |
| HLP | P4 | 장내 t½ | 미확인 | ❌ | — | GI 전용 |
| ProtParam | P4 | 세포내 t½ | ❌ | ✅ BioPython | — | 메커니즘 불일치 |

### 3.2 ADMET 도구

| 도구 | 등급 | D-AA | DOTA | 로컬 | 비고 |
|-----|------|------|------|------|------|
| pepADMET (full) | **P1** | ❌ | ❌ | ❌ 웹전용 | 29 endpoints, 웹폼 작동 |
| ADMET-AI | P2 | ❌ | ❌ | ✅ | 소분자 중심, 펩타이드 OOD |
| ADMETlab 3.0 | P2 | ❌ | ❌ | ❌ 상업 | 119 endpoints, API |
| ToxTeller | P2 | ❌ | ❌ | ✅ | 독성 이진 분류, CC-BY |
| CAPTP | P2 | ❌ | ❌ | ✅ | 독성 이진 분류, CC-BY |
| CycPeptMP | P2 | △ | ❌ | ✅ | 환형 막투과성 특화 |

### 3.3 P1 후보 갱신 — D-AA 특화 부재 확정

> **결론**: 현재 공개된 도구 중 D-AA 환형 펩타이드 ADMET/반감기 예측을 신뢰 가능 수준으로 지원하는 도구는 **0개**. pepADMET P1은 L-AA 선형 후보 triage 용도로만 유효.

---

## 4. 자체 모델 학습 가능성 — PEPlife2 핵심 발견

**PEPlife2** (bioRxiv 2025-05-16, DOI: 10.1101/2025.05.13.653654):
- 4,412개 엔트리 (PEPlife 2,229개 대비 2배)
- **D-AA 포함 213개 엔트리** — D-아미노산 포함 펩타이드 반감기 데이터셋
- 환형 펩타이드, N/C-말단 수식 포함
- D-AA 치환 효과 실증: VH434 t½=1.16h → VH445(D-AA) t½=3.03h

이 데이터셋은 D-AA 특화 모델 fine-tuning의 핵심 데이터 소스가 될 수 있음.
PepMSND Dataset.xlsx (635개)에 D-AA 엔트리가 포함되어 있는지 별도 확인 필요 (§검증 필요 V-01).

---

## 5. 권장 채택안

### A-02 (반감기 도구) 권장

| 순위 | 도구 | 용도 | 조건 |
|------|------|------|------|
| **P1** | **PlifePred2** (로컬) | L-AA 자연 펩타이드 반감기 순위 | pip 설치됨, 성능 검증 필요 (자체 벤치마크) |
| **P2** | **pepADMET** (웹) | L-AA 통합 ADMET triage | 웹폼 POST, 절대값 사용 금지 (4.83× 오차) |
| 보조 | PepMSND (로컬 학습) | 1차 triage 분류기 | 학습 후 infra 평가 필요 |
| 중장기 | **PEPlife2 fine-tuning** | D-AA 반감기 특화 | 213개 D-AA 데이터 + wet-lab 실측 확보 후 |

### A-03 (ADMET 도구) 권장

| 순위 | 도구 | 용도 | 조건 |
|------|------|------|------|
| **P1** | **pepADMET** (웹) | L-AA 선형 후보 ADMET triage | 웹폼 POST, D-AA 입력 금지 |
| **P2** | **ToxTeller 또는 CAPTP** | 독성 이진 분류 | 로컬 실행, L-AA 한정 |
| 중장기 | CycPeptMP | 환형 막투과성 | 구조 기반, 별도 학습 필요 |

---

## 6. infra 인계 사항

### 즉시 시도 가능

1. **PepMSND 웹서버 재시도**: URL 변경
   ```
   기존: http://model.highslab.com/pepmsnd
   정정: http://model.highslab.com/static/service
   ```

2. **PepMSND 로컬 학습** (H100 NVL, CUDA 12.1):
   ```bash
   git clone https://github.com/hmenghu/PepMSND
   cd PepMSND
   # peptools 또는 신규 conda env
   pip install -r requirements.txt  # DGL CUDA 12.1 별도 설치 필요
   ./replace.sh
   python ./Models/model.py
   ```

3. **pepADMET 웹폼 자동화 (Python requests)**:
   ```python
   # 웹폼 POST 방식 (REST API 아님)
   import requests
   resp = requests.post(
       "https://pepadmet.ddai.tech/calcpep/half-life/",
       data={"sequence": "AGCKNFFWKTFTSC"},
       headers={"Referer": "https://pepadmet.ddai.tech/"}
   )
   ```

4. **pepADMET 독성 로컬 실행** (GitHub, GPL-3.0):
   ```bash
   git clone https://github.com/ifyoungnet/pepADMET
   cd pepADMET
   # Python 3.7.16 + torch 1.13.1 환경 필요
   # model/toxicity_early_stop.pth 가중치 포함
   ```

### pepADMET 반감기 가중치 취득 방법

공식 API 없음. 저자 직접 연락:
```
To: jiedong@csu.edu.cn (Prof. Jie Dong, CSU)
Subject: Academic request for pepADMET half-life model weights

Dear Prof. Dong,
We are researchers at KAERI (Korea Atomic Energy Research Institute) conducting 
pre-clinical screening of SSTR2-targeting radioligand therapy candidates.
We would like to request access to the local model weights for the half-life 
prediction module of pepADMET for non-commercial academic research purposes.
Could you please provide guidance on obtaining the model weights or local 
deployment options?
Thank you for your contributions to the field.
```

---

## 7. §검증 필요

| # | 항목 | 우선 | 담당 |
|---|------|------|------|
| V-01 | PepMSND Dataset.xlsx D-AA 엔트리 수 확인 | HIGH | infra |
| V-02 | PepMSND 정식 URL (`/static/service`) HTTP 200 재확인 | HIGH | infra |
| V-03 | pepADMET 웹폼 POST Python requests 자동화 | HIGH | infra |
| V-04 | PEPlife2 데이터셋 D-AA 213개 엔트리 상세 분포 (혈청/혈중) | MED | researcher |
| V-05 | PepMSND 로컬 학습 후 SST14/Octreotide 분류 결과 | MED | infra |
| V-06 | pepADMET Zenodo/OSF 데이터셋 공개 여부 | LOW | researcher |
| V-07 | jiedong@csu.edu.cn 연락 및 반감기 가중치 취득 | MED | 사용자/연구책임자 |
| V-08 | PepMSND Dataset.xlsx에서 D-AA chirality 인코딩 방식 | MED | engineer-backend |

---

## 8. 참고 문헌

1. Tan X et al. 2025 J Chem Inf Model. DOI: 10.1021/acs.jcim.5c02518 — pepADMET
2. Wang et al. 2025 Digital Discovery (RSC). DOI: 10.1039/D5DD00118H — PepMSND
3. Wang et al. 2024 bioRxiv. DOI: 10.1101/2024.12.12.628290 — PepMSND preprint
4. PEPlife2 2025 bioRxiv. DOI: 10.1101/2025.05.13.653654 — D-AA 213개 반감기 데이터
5. Brazeau P et al. 1973 Science 179:77 — SST-14 t½≈3분 (ground truth)
6. github.com/ifyoungnet/pepADMET — GPL-3.0, toxicity weights 45MB
7. github.com/hmenghu/PepMSND — MIT License, 635 data points, model code only
