# Half-Life Tool Evaluation — 2026-05-14

## 목적

사용자 제안 문단의 사실성, RCSB PDB의 half-life 데이터 보유 여부, 그리고 `PlifePred / PlifePred2 / PepFun / PepFun2 / PepFuNN`의 본 프로젝트 적용 가능성을 재검토한다.

---

## 1. 결론 요약

1. **RCSB PDB는 반감기(half-life)를 구조화된 core metadata 필드로 제공하지 않는다.**
   - 반감기 관련 정보는 PDB 엔트리의 **제목(title)**, **primary citation 제목/초록**, 또는 외부 annotation 설명에 텍스트로 등장할 수는 있다.
   - 즉, **RCSB는 구조 저장소이지 PK/PD 데이터베이스가 아니다.**

2. **PlifePred는 실제 혈중 반감기 예측 도구로 인정 가능**하다.
   - 단, 정확도 서술은 조건부다.
   - `R=0.743`은 **natural peptide subset**에서의 최고 성능이며, natural+modified 전체 261 peptide에 대한 최고 성능은 `R=0.692`이다.

3. **PlifePred2는 존재하는 standalone toolkit이지만 현재 프로젝트에서는 미검증 상태**다.
   - 로컬 미설치.
   - PyPI/GitHub는 확인되지만, 현재 확보한 범위에서는 PlifePred2 자체 검증 논문 근거가 약하다.

4. **PepFun / PepFun2 / PepFuNN은 half-life predictor가 아니다.**
   - sequence/property/structure/library/similarity 분석용 peptide toolkit이다.
   - half-life 공백을 직접 메우지 못한다.

5. **본 프로젝트는 이미 PlifePred를 검토했지만 아직 실제 실행/통합은 하지 않았다.**
   - 현재 구현은 `step08_stability.predict_half_life()` 및 `stability_predictor.hl_score_heuristic` 중심이며, 둘 다 **HEURISTIC ranking**으로 명시되어 있다.

---

## 2. RCSB PDB 조사

### 2.1 RCSB의 데이터 모델 관점

- RCSB Data API 문서는 API가 분자명, 서열, 실험 구조 정보 등 **commonly used annotations**를 제공한다고 설명한다.
- 현재 확인된 공식 문서/스키마 설명에서는 **half-life, PK, serum stability** 같은 전용 필드는 확인되지 않았다.
- RCSB Annotations 문서도 GO, Pfam, domain, membrane, sequence/structure/function annotation 중심이다.

### 2.2 실제 관찰 결과

RCSB에서 `half-life`를 검색하면 다음과 같은 엔트리는 잡힌다.

| PDB | 관찰 방식 | 비고 |
|---|---|---|
| `3FJT` | 엔트리 제목/문헌 제목에 `extended serum half-life` | 구조화된 half-life 숫자 필드가 아니라 **설명 텍스트** |
| `5FUO`, `5FUZ` | primary citation에 `correlation between affinity and serum half-life` | 텍스트 기반 |
| `2N35` | snippet에 `terminal half-life of 60 h in mice and 182 h in cynomolgus monkeys` | 문헌 기반 설명이 snippet에 노출 |
| `6M58` | `extending the serum half-life of protein therapeutics` | 메커니즘 설명 수준 |
| `8C7V` | `serum albumin binding ... extend serum half-life` | 메커니즘 설명 수준 |

### 2.3 해석

- **있다/없다를 구분하면**:
  - `half-life 관련 텍스트`는 **있다**.
  - `정규화된 반감기 데이터 필드`는 **없다**.
- 따라서 RCSB를 직접 크롤링해서 반감기 데이터셋을 만드는 접근은 **가능은 하지만 텍스트 마이닝 과제**다.
- 이 방식의 한계:
  - 반감기 단위(`min`, `h`)가 문헌마다 다름
  - 종(`mouse`, `human`, `monkey`) 혼재
  - assay matrix(`serum`, `plasma`, `blood`) 혼재
  - 구조 엔트리 1개가 여러 변이체 PK 서술을 담을 수 있음
  - 숫자가 엔트리 core JSON에 정규화돼 있지 않음

### 2.4 프로젝트에 대한 실무 판단

RCSB는 **구조/복합체 맥락 확인용**으로는 유용하지만, 본 프로젝트의 half-life surrogate 또는 predictor 데이터 소스로 쓰기에는 부적합하다.

권장 용도:
- albumin-binding half-life extension 메커니즘 사례 수집
- serum half-life extension 관련 구조적 motif 조사
- candidate와 유사 scaffold의 복합체 구조 확인

비권장 용도:
- 반감기 ground truth 데이터셋 구축의 주 데이터 소스
- 자동화된 정량 PK 테이블 생성의 1차 소스

---

## 3. 사용자 제안 문단 팩트체크

### 3.1 PlifePred

**판정**: 대체로 맞음, 단 정확도/범위 표현은 수정 필요

맞는 점:
- mammalian blood half-life 예측용 web server
- amino acid composition 및 chemical descriptor 사용
- PLOS ONE 2018 논문 존재

수정 필요한 점:
- `correlation up to 0.74`는 **natural peptides + selected PaDEL descriptors** 조건부 성능
- natural+modified 전체 데이터셋에서는 최고 성능이 `0.692`
- `cellular environments`는 PlifePred 핵심 범위 설명으로는 부정확
- modified 지원은 맞지만, 원 논문 데이터셋은 PEGylation/biotinylation/sarcosine/β-alanine 등 복잡 수정 일부를 제거하고 구축됨

### 3.2 PlifePred2

**판정**: 존재 확인, 하지만 현재는 “도구 설명 > 독립 검증” 상태

확인된 점:
- PyPI 존재
- standalone prediction + design mode 표방
- natural / modified model 구분
- property 계산 기능 포함

주의점:
- 로컬 미설치
- 현재 확보한 범위에서는 PlifePred2 자체 peer-reviewed 성능 검증 문헌을 확보하지 못함
- PyPI 설명상 `Only standard amino acids allowed`가 있어, 자유로운 NCAA 서열 입력보다는 **modification flags 기반** 처리일 가능성이 큼

### 3.3 PepFun / PepFun2 / PepFuNN

**판정**: half-life predictor로 소개하면 부정확

정확한 설명:
- **PepFun**: sequence/structure/property/interaction 분석 툴
- **PepFun2**: modified peptide 포함 sequence/structure/property/conformer/interaction toolkit
- **PepFuNN**: modified peptide 포함 library design, clustering, similarity analysis 중심 toolkit

부정확한 설명:
- `혈중 반감기 추정 도구`로 분류하는 것
- `degradation rate prediction`을 직접 수행한다고 보는 것

---

## 4. 프로젝트 내 기존 검토 여부

### 4.1 이미 검토된 항목

- `PlifePred`는 이미 인벤토리 문서에 정리됨.
- `docs/wetlab/stability_predictor_tools.md`에서 half-life/ADMET 예측 도구 표와 상세 설명을 제공.
- `docs/wetlab/META_stability_halflife_integrated.md`와 `_workspace/release/eod-2026-05-12-team-session.md`에서도 `D-Phe6` 안정성 보강 후보와 함께 PlifePred가 언급됨.

### 4.2 아직 안 된 항목

- 실제 handoff에는 `G-02: PlifePred D-Phe6 도입 후보 입력 테스트`가 **planned item**으로만 남아 있음.
- `PepFun / PepFun2 / PepFuNN`은 레포 내 실질 평가/통합 흔적이 거의 없음.

### 4.3 현재 구현 상태

현재 프로젝트 구현은 외부 half-life predictor 통합이 아니라:
- `pipeline_local/steps/step08_stability.py`
- `pipeline_local/scripts/stability_predictor/`

두 축 모두 **HEURISTIC ranking only**로 명시되어 있음.

---

## 5. 재현성 검증 (현 시점)

### 5.1 로컬 설치 상태

기본 Python에서 다음 모듈 import 가능 여부를 확인한 결과:

| 패키지 | import 가능 |
|---|---|
| `plifepred2` | False |
| `pepfun` | False |
| `pepfunn` | False |
| `peptides` | False |
| `Bio` | False |

주의:
- 이는 **현재 기본 Python** 기준이다.
- 프로젝트 문서상 `BioPython` 등은 별도 `bio-tools` 환경에서 사용될 수 있다.

### 5.2 도구별 재현성 판정

| 도구 | 재현성 판정 | 근거 |
|---|---|---|
| RCSB PDB | 부분 가능 | 공개 API/페이지는 있음. 하지만 half-life는 정규 필드가 아니라 텍스트 마이닝 필요 |
| PlifePred | 낮음 | 웹 전용, 스탠드얼론 미공개 |
| PlifePred2 | 중간 | standalone이나 미설치, 추가 바이너리/conda/버전 의존성 있음 |
| PepFun | 중간 | GitHub 공개, conda 의존성 있음 |
| PepFun2 | 중간 | GitHub 공개, RDKit/BioPython/Modeller 필요 |
| PepFuNN | 중간 | GitHub 공개, local pip 설치 가능 |

### 5.3 실무 해석

- **즉시 재현 가능한 것은 없다.**
- 가장 현실적인 첫 검증 후보는 **PlifePred2**다.
- PlifePred(web)는 빠르게 결과를 볼 수 있지만 **운영 재현성은 떨어진다**.

---

## 6. 유사체 입력 가능성 확인

### 6.1 cand03 / SST-14 계열

대상 예시:
- `AGCKNFFWKTFTSC`
- `AICKNFFWKTFTSC`
- `ILCKKFFWKTFTSC`

이들은 길이 14 aa의 표준 서열이므로:
- **PlifePred natural model**: 입력 가능성 높음
- **PlifePred2 natural model**: 입력 가능성 높음 (`12–100 aa`, standard amino acids)
- **PepFun/PepFun2/PepFuNN**: sequence/property 분석 입력 가능

### 6.2 D-Phe6 / K→Orn / DOTA / PEG3 같은 수정체

| 변형 | PlifePred | PlifePred2 | PepFun2 | PepFuNN |
|---|---|---|---|---|
| D-Phe6 | web modified 모듈에서 가능성 있음 | 자유 서열 입력은 불명확, modification flag 수준일 가능성 | modified peptide 분석 쪽은 상대적으로 적합 | modified peptide 분석 가능성 있음 |
| K→Orn | web modified 모듈에서 가능성 있음 | direct residue-level encoding 불명확 | NCAA 분석 보조 가능 | sequence-space 분석 보조 가능 |
| N-term DOTA | sequence-only predictor와 충돌 가능 | 직접 처리 불명확 | 구조/cheminformatics 보조 가능 | 직접 PK 예측 아님 |
| PEGylation | web modified 모듈 문맥상 일부 가능 | modification flag 기반만 확인 | property/structure 보조 가능 | 직접 반감기 모델 아님 |

핵심:
- **표준 14aa 유사체는 PlifePred2로 바로 넣어볼 가치가 있음**
- **정교한 modified analog는 PlifePred(web) 쪽이 오히려 더 직접적일 수 있음**
- PepFun 계열은 수정체의 **표현/분석 보조**이지 half-life 답변기는 아님

---

## 7. 기존 계획과 충돌 여부

### 7.1 충돌하지 않는 부분

- 외부 predictor를 **보조 ranking/triage**로 붙이는 것은 현재 계획과 충돌하지 않는다.
- 현재 시스템이 이미 `HEURISTIC` 경고를 강하게 유지하고 있어, PlifePred/PlifePred2 결과도 같은 원칙으로 래핑하면 일관성이 유지된다.
- `pepADMET`와 역할도 다르다.
  - `pepADMET`: 더 넓은 ADMET endpoint
  - `PlifePred`: blood half-life 특화

### 7.2 충돌 가능한 부분

1. **용어 충돌**
   - 현재 `predict_half_life()`는 이름은 half-life지만 실제로는 heuristic ranking이다.
   - 여기에 PlifePred 결과를 같이 붙이면 사용자가 둘을 혼동할 수 있다.

2. **신뢰도 체계 충돌**
   - 현재는 `HEURISTIC` 카테고리로 엄격히 가드한다.
   - PlifePred는 heuristic보다는 한 단계 높지만, 그렇다고 실험 대체 수준은 아니다.
   - 따라서 새 confidence label 필요 가능: `MODEL_BASED / MED` 같은 별도 구분.

3. **NCAA 처리 정책 충돌**
   - 프로젝트는 `[dF]`, `[Orn]`, `[Aib]` 등을 내부 canonicalization으로 다룬다.
   - PlifePred2는 직접적인 residue-level modified sequence 표현을 그대로 받지 못할 수 있다.

### 7.3 통합 시 권장 원칙

- 기존 `step08`과 `stability_predictor`는 유지
- 외부 predictor는 **sidecar plugin**으로 추가
- UI/API에서는 아래처럼 분리 표기
  - `hl_score_heuristic` = 내부 ranking
  - `plifepred_score` or `plifepred_predicted_log2_seconds` = 외부 모델 출력
- 절대 단위 표시는 원문 모델 정의를 따르되, **실험 미검증 경고** 유지

---

## 8. 권장 비교표

| 도구 | 실제 역할 | half-life 직접 예측 | modified peptide | 오프라인성 | 프로젝트 적합도 |
|---|---|---:|---:|---:|---|
| RCSB PDB | 구조/문헌 메타데이터 저장소 | △ 텍스트만 | △ | ○ | 구조 근거 조사 용도 |
| PlifePred | blood half-life web predictor | ○ | △~○ | × | 빠른 외부 참조용 |
| PlifePred2 | standalone half-life toolkit | ○ | △ | △ | **우선 검증 후보** |
| PepFun | sequence/structure/property toolkit | × | △ | △ | 보조 분석용 |
| PepFun2 | modified peptide analysis toolkit | × | ○ | △ | modified 표현/분석 보조 |
| PepFuNN | library/similarity/clustering toolkit | × | ○ | △ | SAR/chemical space 보조 |
| pepADMET | peptide ADMET platform | ○ (플랫폼 내 일부) | ○ | △ | 기존 프로젝트 핵심 축 |
| step08 / stability_predictor | 내부 heuristic ranker | × (정량 아님) | 부분 | ○ | 현재 운영 축 |

---

## 9. 다음 단계 제안

### 우선순위 1 — PlifePred2 재현성 검증
- 별도 env에서 설치
- example FASTA로 smoke test
- cand03 / SST-14 / ILCKKFFWKTFTSC 입력 가능 여부 확인
- 출력 단위와 score 정의 확인

### 우선순위 2 — 표준 유사체 입력 테스트
- `AGCKNFFWKTFTSC`
- `AICKNFFWKTFTSC`
- `ILCKKFFWKTFTSC`
- 단일 치환 mutant batch scan

### 우선순위 3 — modified analog 처리 전략 결정
- D-Phe6, Orn, DOTA, PEG3를 어떤 계층에서 다룰지 결정
- 후보:
  - PlifePred(web) modified 모듈 수동/반자동
  - 내부 canonicalization + 별도 modification flag 매핑
  - PepFun2/PepFuNN를 descriptor/representation 보조로 사용

### 우선순위 4 — 프로젝트 충돌 방지 설계
- API schema에 `source`, `confidence_grade`, `assay_context`, `unit` 분리
- `HEURISTIC`와 `MODEL_BASED`를 구분
- UI에서 절대시간과 ranking score 혼동 방지

---

## 10. 참고 소스

### 프로젝트 내부
- `docs/wetlab/stability_predictor_tools.md`
- `docs/wetlab/halflife_methodology.md`
- `docs/wetlab/META_stability_halflife_integrated.md`
- `_workspace/release/eod-2026-05-12-team-session.md`
- `pipeline_local/steps/step08_stability.py`
- `pipeline_local/scripts/stability_predictor/`

### 외부
- RCSB Data API: https://data.rcsb.org/
- RCSB Annotations: https://www1.rcsb.org/docs/exploring-a-3d-structure/annotations
- PlifePred PLOS ONE 2018: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0196829
- PlifePred2 PyPI: https://pypi.org/project/plifepred2/
- PepFun GitHub: https://github.com/rochoa85/PepFun
- PepFun2 GitHub: https://github.com/rochoa85/PepFun2
- PepFuNN GitHub: https://github.com/novonordisk-research/pepfunn
- PepFuNN preprint/publication trace: https://chemrxiv.org/engage/chemrxiv/article-details/66c5ba0020ac769e5f50bbfa
