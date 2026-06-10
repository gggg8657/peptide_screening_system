# ADMETlab 3.0 대체 전략 — pepADMET + PharmPapp 통합 계획

**작성일**: 2026-04-02
**배경**: A-02 액션 아이템 "ADMETlab 3.0 API로 상위 21개 후보 ADMET 프로파일 일괄 생성" 부적합 판정에 대한 대안 수립

---

## 1. ADMETlab 3.0 부적합 사유 (확정)

| 사유 | 상세 | 확인 방법 |
|------|------|---------|
| SSL 인증서 만료 | `notAfter=2026-01-13` — 3개월째 갱신 안 됨 | `openssl s_client` |
| API 엔드포인트 404 | 홈페이지(200)는 뜨지만 `/api/predict` 등 전부 404 | `curl -sk` 테스트 |
| 소분자 전용 학습 데이터 | 400K+ entries, drug-like 소분자. 논문에 "peptide" 언급 0회 | NAR 2024 논문 (PMID 38572755) |
| Applicability Domain | 학습 MW 150-500 Da. SST-14 MW ~1600 Da → 분포 밖 | 논문 + DMPNN 아키텍처 |
| 온프레미스 불가 | 소스/모델 비공개, 웹서비스 전용 | GitHub 없음 |

**판정**: 기술적으로 입력은 가능하나 (DMPNN 그래프 기반), 학습 분포 밖 외삽이므로 예측값 무의미. API도 비활성화 상태로 파이프라인 통합 불가.

---

## 2. 대체 도구 선정

### 선정 기준
1. **펩타이드 전용** 학습 데이터 (소분자 아님)
2. **실험 데이터** 기반 (합성 데이터 제외)
3. **Peer-reviewed 논문** 존재
4. **로컬 실행** 가능 (온프레미스)
5. SST-14 (14aa, MW~1600, 사이클릭, SS bond) **AD 안**

### 선정 결과

| 도구 | 역할 | 논문 | 데이터 | Endpoint | 로컬 | 선정 근거 |
|------|------|------|--------|----------|:----:|---------|
| **pepADMET** | 종합 ADMET | JCIM 2026, 66, 936-946 | 36,643 실험 | 19개 | ⚠️ 독성만 | 유일한 systematic 펩타이드 ADMET. 사이클릭/SS bond 명시 지원 |
| **PharmPapp** | 투과도 특화 | (투고 중, 같은 Dong 그룹) | 실험 | 5개 (Caco2×3, RRCK, PAMPA) | ✅ KNIME | pepADMET과 **동일 연구팀**, 투과도 심화 |

### 탈락 도구

| 도구 | 탈락 사유 |
|------|---------|
| openclaw-peptide-admet | 합성 데이터 15K, 0⭐, 2026-03-24 생성, peer review 없음 |
| Deep-PK | 소분자 전용, 서버 다운 (GitHub 404 + 웹 ECONNREFUSED) |
| ADMETlab 3.0 | 상기 사유 |
| pkCSM / admetSAR / ProTox / SwissADME | 전부 소분자 전용, 온프레미스 불가 |

---

## 3. 통합 아키텍처

```
SST-14 유사체 후보 서열
        │
        ▼
┌─────────────────────────────────────────────────┐
│  Layer 1: 자체 구현 (pharma_properties.py)        │
│  15 메서드 + 5 구조 규칙 + A~E 클러스터            │
│  → 즉시 실행, 외부 의존성 없음                      │
│  GRAVY, Boman, II, AI, pI(SS보정), MW,            │
│  ε280, N-end, μH, WW, charge, protease(4효소),    │
│  BLOSUM62, metal coord(Ga3+), radiolysis          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 2: pepADMET 독성 모델 (즉시)                │
│  입력: SMILES + 서열                               │
│  독성 binary (AUC 0.885)                           │
│  독성 6-class (AUC 0.949)                          │
│  독성 4-class 신경독성 (AUC 0.905)                  │
│  HC50 용혈 (R² 0.474)                              │
│  → GitHub .pth 공개, Python 3.7 + DGL 0.4.3        │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 3: pepADMET 재현 모델 (6주)                 │
│  Half-life 5종 (HBN/HBM/MBN/MBM/MIM)             │
│  BBB (AUC 0.889)                                   │
│  LogD7.4 (R² 0.818)                               │
│  Bioavailability F (AUC 0.900)                     │
│  → 학습 데이터 수집 + 재학습 필요                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Layer 4: PharmPapp 투과도 (중기)                   │
│  Caco-2 A/C/L (R² 0.435~0.527)                    │
│  RRCK (R² 0.623)                                   │
│  PAMPA (R² 0.657)                                  │
│  → KNIME 워크플로우, 로컬 실행                       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
           종합 ADMET 프로파일
     15 자체 + 4 독성 + 8 ADME + 5 투과도
              = 32 endpoint
```

---

## 4. 구현 계획

### Phase 1: pepADMET 독성 모델 통합 (즉시, 1-2일)

| 단계 | 내용 | 의존성 |
|------|------|--------|
| 1.1 | `pepadmet` conda env 생성 (Python 3.7, DGL 0.4.3, PyTorch 1.13.1) | 네트워크 |
| 1.2 | pepADMET GitHub clone | 네트워크 |
| 1.3 | SST-14 SMILES 변환 파이프라인 (RDKit, Cys3-Cys14 SS bond 포함) | 1.1 |
| 1.4 | `toxicity_early_stop.pth` 로딩 + 추론 테스트 | 1.2 |
| 1.5 | 상위 21개 후보 일괄 독성 스크리닝 | 1.3 + 1.4 |
| 1.6 | `calculate_descriptors.py`로 2,133 feature 계산 | 1.2 |

**산출물**: 21개 후보 × 독성 4종 (binary, 6-class, 4-class, HC50) 결과 테이블

### Phase 2: pepADMET 전 모델 재현 (6주)

`docs/pepadmet_reproduction_plan.md` 참조.

| 주차 | 내용 |
|------|------|
| W1 | env + 독성 검증 + 데이터 수집 시작 |
| W2 | BBB/LogD/F 전통 ML 3모델 재학습 |
| W3 | Permeability GNN + RT DB 수집 |
| W4 | Permeability 완료 + Half-life TL pre-train |
| W5 | Half-life fine-tune 5종 + 전체 검증 |
| W6 | 22K 후보 일괄 ADMET 프로파일링 |

### Phase 3: PharmPapp 투과도 보완 (Phase 2와 병렬)

| 단계 | 내용 |
|------|------|
| 3.1 | KNIME 4.7.2 설치 |
| 3.2 | PharmPapp 워크플로우 다운로드 + 테스트 |
| 3.3 | SST-14 + 상위 21개 후보 투과도 예측 |
| 3.4 | pepADMET Permeability 결과와 교차 검증 |

---

## 5. SMILES 변환 전략 (선행 작업)

pepADMET은 **SMILES + 서열 이중 입력**이 필요. SST-14 유사체의 cyclic SMILES 생성:

```python
from rdkit import Chem
from rdkit.Chem import AllChem

def peptide_to_cyclic_smiles(sequence, ss_bond_positions=(3, 14)):
    """서열 → 사이클릭 펩타이드 SMILES (Cys-Cys SS bond 포함)"""
    # 1. 선형 펩타이드 빌드
    mol = Chem.MolFromSequence(sequence)
    # 2. Cys3-Cys14 SS bond 추가
    # ... RDKit EditableMol로 S-S 결합 형성
    # 3. Canonical SMILES 출력
    return Chem.MolToSmiles(mol)
```

**검증**: pepADMET 웹에서 동일 서열 입력 → 생성 SMILES 비교.
pepADMET GitHub의 `data/example.csv`에 SS bond 포함 SMILES 예시 있음 (`CSSC` 패턴).

---

## 6. 최종 커버리지 비교

| 카테고리 | ADMETlab 3.0 (부적합) | pepADMET + PharmPapp + 자체 |
|---------|:-------------------:|:-------------------------:|
| Physicochemical | 10 | **15** (자체 pharma) |
| Absorption | 5 | **6** (pepADMET F + PharmPapp 5) |
| Distribution | 2 | **2** (pepADMET BBB + LogD) |
| Metabolism | 0 | 0 |
| Excretion | 5 | **5** (pepADMET T½ 5종) |
| Toxicity | 12 | **4+** (pepADMET 4 + 자체 radiolysis) |
| **합계** | 34 (소분자 기반) | **32 (펩타이드 전용)** |
| **SST-14 AD** | ❌ 밖 | ✅ 안 |
| **신뢰도** | 외삽, 무의미 | 실험 데이터 기반 |

**수가 2개 적지만, 전부 펩타이드 AD 안이므로 실제 가치는 비교 불가하게 높음.**

---

## 7. 위험 요소

| 위험 | 확률 | 대안 |
|------|:----:|------|
| pepadmet env 구축 실패 (Python 3.7 EOL) | 중 | Docker 이미지 또는 Python 3.8+로 코드 마이그레이션 |
| SMILES 변환 오류 (SS bond) | 중 | pepADMET 웹에서 수동 비교 검증 |
| PharmPapp KNIME 호환 문제 | 낮 | Python 스크립트로 재구현 (모델 파일 공개) |
| Half-life RT DB 수집 어려움 | 중 | TL 없이 baseline RF로 시작, RT DB 확보 후 업그레이드 |
| pepADMET 독성 .pth 로딩 실패 | 낮 | DGL 0.4.3 정확 버전 맞추면 해결 |
