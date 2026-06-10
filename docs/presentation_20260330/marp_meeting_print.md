---
marp: true
theme: uncover
paginate: true
size: 16:9
backgroundColor: '#ffffff'
color: '#1f2328'
style: |
  section {
    font-family: 'Noto Sans KR', 'Helvetica Neue', 'Malgun Gothic', sans-serif;
    font-size: 0.86rem;
    padding: 26px 34px;
    background: #ffffff;
  }
  section.cover {
    background: #f6f8fa;
    border: 1px solid #d0d7de;
    display: flex; flex-direction: column; justify-content: center;
    text-align: center;
  }
  section.cover h1 { color: #0969da; font-size: 2.1rem; margin-bottom: 0.35rem; font-weight: 700; }
  section.cover h2 { color: #57606a; font-size: 1.05rem; font-weight: 400; letter-spacing: 0.02em; }
  section.cover p { color: #656d76; font-size: 0.82rem; }
  section.divider {
    background: #fff7f0;
    border: 1px solid #fd8c73;
    display: flex; flex-direction: column; justify-content: center;
    text-align: center;
  }
  section.divider h1 { color: #bc4c00; font-size: 1.85rem; border: none; font-weight: 700; }
  section.divider h3 { color: #57606a; font-weight: 400; font-size: 0.95rem; }
  h2 { color: #0969da; border-bottom: 2px solid #d0d7de; padding-bottom: 4px; margin-bottom: 10px; font-size: 1.1rem; }
  h3 { color: #bc4c00; font-size: 0.9rem; margin-bottom: 5px; }
  table { font-size: 0.66rem; width: 100%; border-collapse: collapse; border: 1px solid #d0d7de; }
  th { background: #f6f8fa; color: #0969da; padding: 4px 6px; border: 1px solid #d0d7de; font-weight: 600; }
  td { padding: 3px 6px; border: 1px solid #d0d7de; color: #24292f; }
  tr:nth-child(even) td { background: #f6f8fa; }
  ul { margin: 3px 0; } ul li { margin-bottom: 2px; line-height: 1.35; font-size: 0.76rem; color: #24292f; }
  strong { color: #1f2328; }
  code { background: #f6f8fa; color: #0550ae; border: 1px solid #d0d7de; border-radius: 3px; padding: 1px 4px; font-size: 0.68rem; }
  pre { background: #f6f8fa; border: 1px solid #d0d7de; font-size: 0.58rem; line-height: 1.25; padding: 8px; }
  blockquote { border-left: 4px solid #fd8c73; background: #fff8f3; padding: 0.3em 0.65em; font-size: 0.74rem; margin: 6px 0; color: #57606a; }
  .req { background: #ddf4ff; border-left: 4px solid #0969da; padding: 6px 10px; margin: 5px 0; font-size: 0.74rem; border-radius: 0 6px 6px 0; color: #0550ae; }
  .res { background: #dafbe1; border-left: 4px solid #1a7f37; padding: 6px 10px; margin: 5px 0; font-size: 0.74rem; border-radius: 0 6px 6px 0; color: #0d3d1a; }
  .blk { background: #fff8c5; border-left: 4px solid #9a6700; padding: 6px 10px; margin: 5px 0; font-size: 0.74rem; border-radius: 0 6px 6px 0; color: #3d2f00; }
  .fail { background: #ffebe9; border-left: 4px solid #cf222e; padding: 6px 10px; margin: 5px 0; font-size: 0.74rem; border-radius: 0 6px 6px 0; color: #82071e; }
  .tag { display: inline-block; background: #eaeef2; color: #24292f; padding: 2px 7px; border-radius: 10px; font-size: 0.62rem; margin: 1px 2px; border: 1px solid #d0d7de; }
  .tag-ok { background: #dafbe1; color: #1a7f37; border-color: #4ac26b; }
  .tag-warn { background: #fff8c5; color: #9a6700; border-color: #d4a72c; }
  .tag-fail { background: #ffebe9; color: #cf222e; border-color: #ff8182; }
  footer { color: #656d76; font-size: 0.62rem; }
  a { color: #0969da; }
---

<!-- _class: cover -->

# SSTR2 방사성의약품 후보 스크리닝

## AI Co-Scientist 파이프라인 — 내부 미팅 보고

**인쇄·배포용 v2** (밝은 배경 · Marp)

2026-03-30 &nbsp;·&nbsp; AI팀 (김동주)
`progress_report_20260323` · `meet_log` · `action_items_tracker`

---

## 회의 목적

- **진행 상황 공유**: 65건 통합 추적, A-01~A-10 대응, 약리·ADMET·선택성·스코어링 현황
- **의사결정·협의**: RI팀 연계(A-06/A-07), pepADMET 웹 접근, 블로커(네트워크·모델 다운로드) 정렬
- **기술 맥락 통합**: **서버 측** `pipeline_local` 마이그레이션(NIM→로컬)과 **에이전트/Critic·클러스터** 로드맵을 한 흐름으로 설명

---

## 회의 아젠다 (~60분)

| # | 주제 | 시간 | 요약 |
|:-:|------|:--:|------|
| 1 | 프로젝트·Silo·스캐폴드 | 5분 | 듀얼 Silo, SST-14, 5대 규칙, 스택 |
| 2 | **인프라** NIM→로컬 | 5분 | Before/After, conda, 서버 벤치마크 |
| 3 | **에이전트·Critic·게이트** | 8분 | 5-Agent, 피드백 루프, Gate, Critic 확장·긍정 루프, A~E 클러스터 |
| 4 | 전체 진행률·A-01~10 | 10분 | 65건, 액션 총괄 |
| 5 | A-01·A-02/A-09·A-03 | 15분 | 약리, pepADMET, 선택성 |
| 6 | A-04/A-05·A-08/A-10 | 8분 | 스코어링 체인, 방사화학 |
| 7 | 미완료·Wave·RI | 7분 | 다음 단계, 확인 사항 |
| 8 | Q&A | 2분 | |

---

## 협의 필요 · 핵심 숫자

| 구분 | 내용 |
|------|------|
| **A-06** DOTA 합성 견적 | RI팀 — Peptron / HLB PEP / Anygen |
| **A-07** C18 변형체 | RI팀 — Top-K 확정 후 |
| **pepADMET** | `pepadmet.ddai.tech` 기관망 접근 |

| 지표 | 수치 |
|------|:--:|
| 액션 65건 완료율 | **68%** (44/65) |
| A-01~10 AI팀 | **6/8** 완료 · 2 부분 |
| 테스트 함수 | ~510 (+57) |
| CI | **7/7** |

---

## 프로젝트 개요 — 듀얼 Silo 전략

SSTR2(Somatostatin Receptor Type 2)는 신경내분비종양(NET)에서 과발현되는 GPCR로, DOTATATE/DOTATOC 등 기존 방사성의약품의 타겟입니다. 본 프로젝트는 SST-14(14aa 사이클릭 펩타이드)를 출발 스캐폴드로, AI Co-Scientist 파이프라인을 통해 **SSTR2 선택적 결합 펩타이드 후보를 대규모로 스크리닝**하는 것을 목표로 합니다.

이를 위해 **두 가지 상호보완적 접근법(Silo)**을 병렬 운영합니다:

| | **Silo A** — De novo 설계 | **Silo B** — SST-14 변이 탐색 |
|:-:|--------------------------|------------------------------|
| **전략** | 백본부터 새로 설계 (3-Arm) | 기존 SST-14의 8잔기 변이 |
| **모델** | RFdiffusion → ProteinMPNN → ESMFold | Thompson Sampling + BLOSUM62 |
| **도킹** | DiffDock / Boltz2 / DiffPepBuilder | FlexPepDock (PyRosetta) |
| **QC** | pLDDT + dock confidence | ddG + clash + 5대 구조 규칙 |
| **최적화** | Grid search | Bayesian Bandit + BO |
| **처리량** | API 제한적 | ~240 candidates/hr |
| **현재 상태** | 설계 단계 (NIM→로컬 전환 중) | **운영 중** (10-iter 완료) |

> Silo A는 **새로운 접힘(fold)**을, Silo B는 **서열 변이(sequence variant)**를 탐색합니다. 공유 QC 게이트와 약리학 검증으로 일관성을 보장합니다.

---

## SST-14 스캐폴드 — 구조와 제약

모든 후보 설계의 출발점은 SST-14 native 서열입니다. 14개 아미노산 중 **6개 위치가 고정**(약효 유지 필수)이고, **8개 위치가 변이 가능**합니다.

| pos | 1 | 2 | **3** | 4 | 5 | 6 | **7** | **8** | **9** | **10** | 11 | 12 | 13 | **14** |
|:---:|:-:|:-:|:-----:|:-:|:-:|:-:|:-----:|:-----:|:-----:|:------:|:--:|:--:|:--:|:------:|
| **aa** | A | G | **C** | K | N | F | **F** | **W** | **K** | **T** | F | T | S | **C** |
| **역할** | mut | mut | SS↔ | mut | mut | mut | FWKT | FWKT | FWKT | FWKT | mut | mut | mut | ↔SS |

**5대 구조 규칙** (PASS/FAIL 이진 판정):
- **FWKT 보존** (pos 7-10): 약리단 핵심, SSTR2 결합 포켓에 직접 접촉
- **K9-D122 염다리**: Lys9 ↔ SSTR2 Asp122 정전기 상호작용
- **Cys3-Cys14 이황화결합**: 사이클릭 구조 유지 (SG-SG ≤ 2.5Å)
- **Phe6-Phe11 스태킹**: π-π 상호작용으로 구조 안정화
- **N-말단 킬레이터 접합**: DOTA/NOTA 등 킬레이터 부착 가능성

---

## 기술 스택 — 모델·라이브러리·목적 총괄

본 파이프라인에서 사용하는 모든 컴퓨팅 도구를 단계별로 정리합니다. 서버에서는 NIM Cloud API를 로컬 GPU로 전환 완료했으며, 연구실 PC에서는 전환 진행 중입니다.

| 단계 | 모델 / 라이브러리 | 목적 | 입력 → 출력 |
|:----:|------------------|------|-----------|
| Step01 | **OpenFold3** | 수용체 구조 예측 | 서열 → mmCIF 3D 구조 |
| Step02 | **RFdiffusion** | 바인더 백본 설계 | 수용체 PDB + hotspot → 펩타이드 백본 |
| Step03 | **ProteinMPNN** | 역폴딩 (서열 설계) | 백본 PDB → 아미노산 서열 |
| Step03b | **BLOSUM62** | 보존적 돌연변이 (Silo B) | 참조 서열 → 변이체 |
| Step04 | **ESMFold** | 구조 QC (pLDDT) | 서열 → 3D 구조 + 신뢰도 |
| Step05 | **Boltz2 / DiffPepBuilder** | 단백질-펩타이드 도킹 | 수용체 + 펩타이드 → 복합체 |
| Step05b | **PyRosetta FlexPepDock** | 선택성 스크리닝 | 펩타이드 × SSTR1~5 → ddG |
| Step06 | **PyRosetta** | 에너지 정제 + ddG | 복합체 PDB → 결합 에너지 |
| Step07 | **FoldMason / PyMOL** | 구조 비교 + 시각화 | PDB → lDDT + 렌더링 |
| 스코어링 | **GNINA v1.3.2** | CNN 재점수화 | PDB → CNN score + Vina |
| 스코어링 | **pymoo (NSGA-II)** | Pareto 다목적 최적화 | 4목적 → 프론트 + 거리 |
| 스코어링 | **BoTorch / GP** | Bayesian Optimization | 관측 → 다음 후보 제안 |
| 약리 | **pharma_properties.py** | 15개 물리화학 메서드 | 서열 → GRAVY, pI, MW, ... |
| ADMET | **pepADMET** (계획) | 펩타이드 독성/반감기 | 서열+SMILES → 19 endpoint |
| LLM | **Ollama (qwen3:8b)** | 에이전트 추론 | 맥락 → 가설/피드백 |
| 프론트 | **React 19 + TypeScript** | 실시간 대시보드 | API 폴링 → 시각화 |
| CI/CD | **GitHub Actions** | 7 job 자동화 | push → lint/test/build |

---

## 인프라 전환 — Before: NIM Cloud API

```
사용자 요청 → AG_src / pipeline_local → nim_client.py → NVIDIA NGC API
         → OpenFold3 / RFdiffusion / ProteinMPNN / ESMFold / DiffDock / Boltz2 / MolMIM
         → 인터넷·API Key·과금 필수
```

| 문제 | 영향 |
|------|------|
| 인터넷 의존 | 오프라인 불가 |
| 레이턴시 | 단계별 지연 |
| 과금·키 | 대규모·보안 부담 |

---

## 인프라 전환 — After: `pipeline_local` (서버)

```
pipeline_local/ — orchestrator (LocalModelRunner)
  ├── wrapper_scripts/ (8개 --input-json)
  └── envs/ (9개 conda)
로컬 GPU: H100 NVL ×4  ·  LLM: Ollama 다모델
```

| 모델·도구 | Before (NIM) | After (Local) | 비고 |
|-----------|-------------|---------------|------|
| ESMFold / RFdiffusion / ProteinMPNN / Boltz2 / OpenFold3 / GenMol | NGC API | 전용 `conda` env | 마이그레이션 완료 또는 검증 중 |
| PyRosetta | — | 로컬 | FlexPepDock |
| **ESMFold 배치** | (클라우드) | **128서열 ~70초** | 서버 벤치: **~17×** 개선(발표 기준) |

<div class="blk">

**연구실 PC**는 별도 맥락: PyTorch+가중치 **~23GB** 다운로드·USB 이식 등은 Part 9에서 정리 (테더링·오프라인 재현).
</div>

---

## 5-Agent 에이전트 시스템

Planner → QC&Ranker → DiversityMgr → **Critic** → Reporter 가 한 iteration을 구성합니다.

| 에이전트 | 유형 | 역할 | 호출 시점 |
|---------|:----:|------|---------|
| **Planner** | LLM | 가설·돌연변이·파라미터 | 반복 시작 |
| **QC & Ranker** | Code | 게이트(pLDDT, ddG, clash), 순위 | Step04~06 후 |
| **DiversityMgr** | Code | 중복 제거·다양성 | 순위 후 |
| **Critic** | LLM | 실패 분석·다음 반복 제안 | 반복 종료 전 |
| **Reporter** | LLM | 순위표·보고서 | 반복 종료 |

---

## 파이프라인 피드백 루프 (서버 실행 기준)

```
Iteration N: Planner → Step01~07 → QC & Ranker → Reporter
                              ↑                    │
                         Critic (실패 분석) ────────┘
Iteration N+1: 수정된 파라미터(최대 2개)로 재실행
```

---

## 평가 Gate (4단계) + Critic이 보는 것

```
Gate1: pLDDT ≥ 60  →  Gate2: 도킹 상위 20%  →  Gate3: ddG·clash  →  Gate4: selectivity margin
```

| Gate | 메트릭 | 의미 |
|:----:|--------|------|
| 1 | pLDDT | 구조 신뢰도 |
| 2 | dock | 결합 가능성 |
| 3 | ddG / clash | 결합·입체 |
| 4 | selectivity | SSTR2 vs off-target |

**Critic 현재**: **5/18 메트릭**만 참조 — 나머지 13개(interface pLDDT, 이황화, ADMET, MW/pI 등)는 확장 대상.

**확장 로드맵**: 실패 유형 **6 → 19** (ADMET·반감기·off-target 등 Gate 5와 연계) + **긍정 피드백 루프**: Reporter가 상위 서열 패턴을 추출 → Planner에 `bias_AA_per_residue` 반영.

---

## A-04: Cluster A~E — Critic과 연결

**원본 지시**: Critic에 ClusterReport(A~E) — `classify_cluster()` **57 tests** 통과.

| 클러스터 | 목적 | 한 줄 요약 |
|:--------:|------|------------|
| **A** | 결합 엘리트 | ddG·clash·pLDDT·FWKT |
| **B** | 선택성 | selectivity_margin |
| **C** | 안정성 | II·BLOSUM·protease |
| **D** | 방사화학 | GRAVY·charge·chelator |
| **E** | 탐색 | 폴백 |

**Critic 피드백 예**: `poor_selectivity` → hotspot 강화 · `instability_high` → 잔기 치환 · `radio_chem_unfavorable` → GRAVY/charge 조정.

---

<!-- _class: divider -->

# Part 1
### 전체 현황 — 65건 통합 추적

---

## 전체 진행률 — 65건 통합 추적

이번 보고 기준 7개 카테고리 65건의 작업을 추적하고 있으며, 그 중 44건(68%)이 완료 또는 대안 구현으로 처리되었습니다. 핵심 파이프라인에 해당하는 A(리팩토링)와 F(RCSB PDB 통합)는 100% 완료 상태입니다. **미완료 19건 중 대부분은 코드가 완성되어 있으나 네트워크(대용량 모델 다운로드) 또는 외부 API 접근에 의존하는 항목**으로, 알고리즘·로직 개발 측면의 블로커는 없습니다.

| 출처 | 총 | 완료 | 완료율 | 핵심 비고 |
|------|:--:|:----:|:------:|----------|
| A. 리팩토링 플랜 | 22 | 22 | <span class="tag tag-ok">100%</span> | Sprint 1~3 전체 완료 |
| B. pharma 검증 보고서 | 10 | 4 | <span class="tag tag-warn">40%</span> | P0 버그 16건 수정, 기능 개선 잔여 |
| C. ADMET 도구 Tier 계획 | 8 | 1 | <span class="tag tag-fail">13%</span> | pepADMET 전략 수립 완료 |
| D. 대안 스코어링 모듈 | 6 | 4 | <span class="tag tag-ok">67%</span> | 3모듈 구현, runner 통합 대기 |
| E. 로컬 모델 마이그레이션 | 8 | 3 | <span class="tag tag-warn">38%</span> | GNINA OK, PyTorch 23GB 블로커 |
| F. RCSB PDB 통합 | 6 | 6 | <span class="tag tag-ok">100%</span> | 26 tests, 전체 완료 |
| G. CI/CD | 5 | 4 | <span class="tag tag-ok">80%</span> | 7 jobs 중 NIM smoke만 보류 |
| **합계** | **65** | **44** | **68%** | 미완료 19건 중 대부분 네트워크 의존 |

> 회의 액션 A-01~A-10 — AI팀: ✅ **6**/8 완료 · ⚠️ **2**/8 부분 · RI팀 ⏸️ 2건

---

## 왜 전체 완료율이 68%인가

전체 68% 완료율의 구성 원인을 파악하는 것이 중요합니다. **코드가 완성된 항목(⚠️ 코드완료)과 네트워크 의존 항목은 "미완료"로 집계되지만, 실제 알고리즘 개발 작업은 대부분 완료**된 상태입니다. 반면 C(ADMET, 13%)가 낮은 이유는 원본 도구 6종 모두가 소분자 전용으로 판명되어 새 전략 수립에 시간이 소요된 때문이며, pepADMET로의 전환 방향은 확정되었습니다.

<div class="res">

**핵심 파이프라인 완료율**: A(리팩토링) + F(RCSB PDB) = **100%** — 파이프라인 뼈대는 완전히 동작합니다.
</div>

<div class="blk">

**주요 블로커 3가지**: ① PyTorch 모델 23GB 다운로드(테더링 환경) ② SSTR1/3/4/5 AlphaFold API 접근 ③ pepADMET DGL 환경 구축
</div>

- **A카테고리(100%)**: 22개 리팩토링 항목 모두 완료, Sprint 1~3 전부 처리
- **B카테고리(40%)**: 핵심 P0 버그 16건은 수정 완료, 기능 확장 6건 잔여
- **E카테고리(38%)**: GNINA 로컬 실행은 확보, PyTorch 기반 3개 모델 대기 중
- **G카테고리(80%)**: CI 7 job 중 NIM smoke test만 `continue-on-error=true`로 처리

---

<!-- _class: divider -->

# Part 1 — A-01 ~ A-10
### 원본 요청 → 판단 → 대응 총괄

---

## A-01~A-10 총괄 (1/2) — 원본 지시 & 판단

아래 표는 박사님이 2차 미팅(2026-02-12)에서 제시한 10개 액션 아이템 각각에 대해 AI팀이 내린 판단과 그 이유를 정리한 것입니다. "판단" 열의 표현이 원본 도구와 다를 경우, 이는 해당 도구가 SST-14에 직접 적용 불가하다는 근거가 있어 **동등 이상의 기능을 자체 구현하거나 대안 도구로 대체**했음을 의미합니다.

| ID | 박사님 원본 지시 | 기한 | 판단 요약 | 상태 |
|:--:|-----------------|:----:|------|:-:|
| **A-01** | PepCalc/PeptideCutter → Step 8 통합, 혈청 **t½ 예측** | 2주 | PepCalc **API 부재 + SS bond 미지원** → 자체 15메서드 구현 | ✅ |
| **A-02** | **ADMETlab 3.0** API로 21개 ADMET 프로파일 | 2주 | 소분자 6종 **AD 범위 초과** → pepADMET 대안 확보 | ⚠️ |
| **A-03** | SSTR1/3/4/5 **AlphaFold 구조** + 선택성 도킹 | 2주 | 코드 **전부 구현** 완료, 네트워크 차단으로 PDB 미다운로드 | ⚠️ |
| **A-04** | Critic Agent에 **ClusterReport A~E** 추가 | 1개월 | `classify_cluster()` **57 tests** 완전 구현 | ✅ |
| **A-05** | BLOSUM Tier 1/2/3 **병렬 후보** Step 3B 재설계 | 1개월 | BO+Pareto+GNINA **3모듈** 구현, runner 통합 1단계 잔여 | ✅ |

### 판단 기준 용어 정의

- <span class="tag tag-fail">부적합</span> = 도구 자체가 SST-14 적용 불가 (Applicability Domain 초과, 서버 다운 등)
- <span class="tag tag-ok">대체 구현</span> = 원본 도구 대신 자체/대안으로 동등 이상 기능 구현 완료
- <span class="tag tag-warn">코드완료</span> = 로직 구현됨, 실행 데이터 미생성 (네트워크 또는 외부 데이터 블로커)

---

## A-01~A-10 총괄 (2/2) — 원본 지시 & 판단

A-06과 A-07은 RI팀(방사성의약품 실험팀) 담당 항목으로, AI팀이 단독으로 결정할 수 없는 사항입니다. A-06의 합성 견적은 외부 업체 컨택이 필요하고, A-07의 C18 변형체 설계는 파이프라인 Top-K 후보가 확정된 이후에야 진행 가능합니다. A-08/A-09/A-10은 **모두 완료**로, 13개 메트릭에 신규 3개가 추가되었고 pepADMET 전문 분석이 수행되었습니다.

| ID | 박사님 원본 지시 | 기한 | 판단 요약 | 상태 |
|:--:|-----------------|:----:|------|:-:|
| **A-06** | Peptron/HLB PEP/Anygen **DOTA 합성 견적** | 2주 | RI팀 담당 — 진행 여부 이번 회의에서 확인 필요 | ⏸️ |
| **A-07** | 상위 3개 **Lys/N-말단 C18 변형체** 설계 | 1개월 | RI팀 담당 — Top-K 후보 확정 이후 진행 가능 | ⏸️ |
| **A-08** | 13-메트릭에 **Selectivity/Radiolysis/Chelator** | 2주 | **3/3 전부 신규 구현**, 메트릭 총 15개로 확장 | ✅ |
| **A-09** | 김민규 교수팀 **JCIM 논문** 검토 → 적용 정리 | 2주 | pepADMET 19 endpoint 전문 분석 + 로드맵 PA-01~06 | ✅ |
| **A-10** | **RCP 안정성** (radiolysis risk) 구현 확인 | 1개월 | `calculate_radiolysis_susceptibility()` 구현 + 검증 | ✅ |

| 상태 | 건수 | 해당 액션 |
|:----:|:----:|----------|
| <span class="tag tag-ok">✅ 완료 / 대체</span> | **6** | A-01, A-04, A-05, A-08, A-09, A-10 |
| <span class="tag tag-warn">⚠️ 코드완료 / 미실행</span> | **2** | A-02 (대안 확보), A-03 (네트워크) |
| <span class="tag">⏸️ RI팀</span> | **2** | A-06, A-07 |

---

<!-- _class: divider -->

# Part 2 — A-01 상세
### PepCalc 부적합 → `pharma_properties.py` 15메서드

---

## A-01: PepCalc이 왜 부적합한가

<div class="req">

**원본 지시**: "PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고, SST-14 변형체의 혈청 반감기(t½) 예측값을 일괄 산출할 것"
</div>

PepCalc을 채택하지 않은 이유는 단순히 대안이 더 좋아서가 아니라, **PepCalc이 구조적으로 이번 파이프라인에 통합 자체가 불가능하기 때문**입니다. PepCalc은 웹 인터페이스만 제공하며 프로그래밍 방식의 REST API가 전혀 존재하지 않아, 22,000개 후보를 자동 처리하려면 브라우저 자동화(Selenium)를 써야 하는데 이는 서버 정책 위반이자 비효율입니다. 또한 SST-14의 Cys3-Cys14 이황화 결합(disulfide bond)을 고려하는 파라미터가 없어, 순환 펩타이드의 물리화학적 특성을 정확히 계산할 수 없습니다.

| 평가 항목 | PepCalc | 자체 구현 `pharma_properties.py` |
|----------|:-------:|:------:|
| **API 지원** | <span class="tag tag-fail">❌ 웹 인터페이스만 제공</span> | <span class="tag tag-ok">✅ Python 클래스, batch 지원</span> |
| **소스 공개** | <span class="tag tag-fail">❌ 비공개 (블랙박스)</span> | <span class="tag tag-ok">✅ 전체 공개, 재현 가능</span> |
| **SS bond (Cys-Cys)** | <span class="tag tag-fail">❌ 미지원 (pI 오계산)</span> | <span class="tag tag-ok">✅ `ss_bond_cysteines` 파라미터</span> |
| **사이클릭 펩타이드** | <span class="tag tag-fail">❌ 선형만 가정</span> | <span class="tag tag-ok">✅ 구조 규칙 #2, #5 연동</span> |
| **메서드 수** | ~5개 | **15개** (13 문헌 + MW + radiolysis) |
| **문헌 투명성** | <span class="tag tag-fail">❌ 미명시</span> | <span class="tag tag-ok">✅ 각 메서드마다 원본 논문 명시</span> |
| **배치 처리** | <span class="tag tag-fail">❌ 1건씩 수동 입력</span> | <span class="tag tag-ok">✅ `batch_analyze()` 22,000건</span> |
| **파이프라인 통합** | <span class="tag tag-fail">❌ 자동화 불가</span> | <span class="tag tag-ok">✅ `calculate_all()` Step 8 직결</span> |

<div class="res">

**결론**: `PharmaProperties` 클래스로 PepCalc 완전 대체 + `peptides` v0.5.0 Ground Truth와 8/8 항목 완벽 일치 검증 완료
</div>

---

## A-01: 15개 메서드 — 문헌 근거 전수

아래 표는 `pharma_properties.py`에 구현된 15개 메서드 각각의 원본 논문 근거입니다. 이 방식의 핵심 강점은 **모든 계산이 특정 연구자의 주관적 설정 없이 1982년~1998년 사이에 발표된 검증된 문헌에 정확히 기반**한다는 점입니다. 특히 ★ 표시된 MW(분자량)와 Radiolysis(방사선분해 감수성)는 원본 지시에 없었으나 방사성의약품 QC에 필수적이라 판단하여 이번에 신규 추가했습니다.

| # | 메서드 | 함수명 | 원본 논문 | 반환값 |
|:-:|--------|-------|---------|------|
| 1 | GRAVY | `calculate_gravy()` | Kyte & Doolittle **1982** | 소수성 평균 지수 |
| 2 | Boman Index | `calculate_boman_index()` | Radzicka-Wolfenden 1988 / Boman **2003** | kcal/mol (단백질 결합 예측) |
| 3 | Instability Index | `calculate_instability_index()` | Guruprasad et al. **1990** | II (< 40 = 안정) |
| 4 | Aliphatic Index | `calculate_aliphatic_index()` | Ikai **1980** | 소수성 지방족 잔기 상대 부피 |
| 5 | **pI** | `calculate_pi(ss_bond_cysteines=)` | Bjellqvist **1993** / Lehninger | 등전점 pH |
| 6 | Extinction Coeff. | `calculate_extinction_coefficient()` | Pace et al. **1995** | M⁻¹cm⁻¹ (농도 측정용) |
| 7 | N-end Rule T½ | `calculate_nend_rule_halflife()` | Varshavsky **1996** | hours (세포내 단백질분해) |
| 8 | Hydrophobic Moment | `calculate_hydrophobic_moment()` | Eisenberg et al. **1982** | μH (양친매성 지표) |
| 9 | Wimley-White | `calculate_wimley_white()` | Wimley & White **1996** | ΔG kcal/mol (막 삽입 에너지) |
| 10 | Net Charge | `calculate_net_charge(ph=)` | Henderson-Hasselbalch 공식 | 특정 pH에서의 순전하 |
| 11 | **MW** ★ | `calculate_mw(n_disulfide=)` | PubChem / NIST 원소 질량 | Da (DOTA+⁶⁸Ga QC 기준) |
| 12 | Protease Sites | `count_protease_sites()` | MEROPS Database | 4~5종 효소별 절단 사이트 수 |
| 13 | BLOSUM62 | `calculate_blosum62_score()` | Henikoff & Henikoff **1992** | 진화적 보존도 점수 |
| 14 | Metal Coord. | `analyze_metal_coordination()` | Rulisek & Vondrasek **1998** | 잔기별 금속 배위 선호도 |
| 15 | **Radiolysis** ★ | `calculate_radiolysis_susceptibility()` | 방사화학 문헌 종합 | score + risk 등급 |

---

## A-01: DIWV 버그 발견 과정 — 전수 대조 검증

`pharma_properties.py`의 신뢰성을 확보하기 위해 `peptides` v0.5.0 라이브러리를 Ground Truth로 채택하여 400개 다이펩타이드(DIWV 테이블 전체)를 일대일 대조하는 방식으로 검증을 수행했습니다. 이 과정에서 **단순한 copy-paste 전사 오류로 인한 16건의 수치 버그**가 발견되었습니다. 특히 RR 다이펩타이드의 경우 오류 전 값이 -6.54였으나 실제 값은 +58.28로, **부호와 크기 모두 완전히 틀린** 상태였습니다. SST-14 서열에 RR/MM/YT가 포함되지 않아 기존 35개 테스트로는 이 오류가 탐지되지 않았다는 점이 더욱 중요합니다.

| 파일 | 다이펩타이드 | 수정 전 | 수정 후 | 최대 오차 | 근본 원인 |
|------|:-----------:|:-------:|:-------:|:---------:|------|
| pharma_properties | **RR** | -6.54 | **58.28** | **64.82** | DIWV 테이블 copy-paste 전사 오류 |
| pharma_properties | **MM** | -14.03 | **-1.88** | 12.15 | 행 간 복사 오류 |
| pharma_properties | 기타 10개 | — | — | — | 동일 원인 (행 오프셋) |
| pharmacology | **YT** | 33.60 | **-7.49** | **41.09** | copy-paste 전사 오류 |
| pharmacology | EW, KP, VK | — | — | — | 동일 원인 |
| pharmacology | **Boman** | `-sum/n` | `+sum/n` | **부호 반전** | Boman 2003 공식 부호 오해 |

> SST-14에 RR/MM/YT 미포함 → 기존 35개 테스트로 미탐지 · 수정 후 **62개 테스트 (8/8 GT 완벽 일치)** · `commit eb213c9` + `commit e5bcb51`

---

## A-01: SS bond pI 보정 — 신장 클리어런스 직결

Cys3-Cys14 이황화 결합이 형성되면 두 Cys 잔기의 thiol기(pKa 8.18)가 이온화에 참여하지 못합니다. 기존 계산 방식은 이를 고려하지 않아 pI를 과소 평가했으며, 이를 Henderson-Hasselbalch 공식에서 해당 잔기를 제외하는 방식으로 보정했습니다. **pI 보정은 신장 클리어런스 예측에 직결**됩니다. 일반적으로 방사성의약품은 pI가 낮을수록 신장에서 재흡수가 억제되어 신독성이 낮아지므로, 보정된 pI 10.62는 Octreo 계열과 비교 시 신장 흡수가 더 높을 수 있음을 시사합니다.

### `_charge_at_ph(sequence, ph, ss_bond_cysteines=)` 보정 로직

SS bond 형성 Cys의 **thiol기(pKa 8.18) 비이온화** → Henderson-Hasselbalch 계산에서 제외
`ss_bond_cysteines={2, 13}` (0-indexed) → Cys3(pos 2), Cys14(pos 13) 이온화 차단

| 항목 | 보정 전 | 보정 후 | 변화 | 임상 의의 |
|------|:-------:|:-------:|:----:|----------|
| **pI** | 9.04 | **10.62** | **+1.58 pH** | 신장 여과 vs 재흡수 판단 기준 |
| **Charge** (pH 7.4) | +1.709 | **+1.993** | +0.284 | 종양 미세환경 pH 6.5에서 더 양전하 |
| **MW** | 미구현 | **1639.91 Da** | 신규 추가 | [peptide]+[DOTA]+[⁶⁸Ga] QC 기준 |

### SST-14 서열 포지션 맵 — FWKT 약리단과 SS bond 위치

| pos | 1 | 2 | **3** | 4 | 5 | 6 | **7** | **8** | **9** | **10** | 11 | 12 | 13 | **14** |
|:---:|:-:|:-:|:-----:|:-:|:-:|:-:|:-----:|:-----:|:-----:|:------:|:--:|:--:|:--:|:------:|
| **aa** | A | G | **C** | K | N | F | **F** | **W** | **K** | **T** | F | T | S | **C** |
| 역할 | | | SS↔ | | | | FWKT | FWKT | FWKT | FWKT | | | | ↔SS |
| 방사선 취약 | | | ★ | | | ◎ | ◎ | **★★★** | | | ◎ | | | ★ |

> 포지션 맵에서 W8(Trp)이 FWKT 약리단의 핵심이면서 동시에 방사선 분해 최취약 잔기임을 확인할 수 있습니다.

---

<!-- _class: divider -->

# Part 3 — A-02 / A-09 상세
### ADMET 재정의 — pepADMET 유일 대안

---

## A-02: 소분자 ADMET 6종 — 개별 부적합 사유

<div class="req">

**원본 지시**: "ADMETlab 3.0 API를 활용하여 상위 21개 후보에 대한 ADMET 프로파일 21건을 일괄 생성할 것"
</div>

6종 ADMET 도구가 모두 부적합 판정을 받은 것은 우연이 아닙니다. **이 도구들의 공통된 근본 문제는 MW < 500 Da인 소분자를 대상으로 훈련되었다는 점**입니다. SST-14는 MW ~ 1,600 Da로 이 범위의 3배 이상이며, 간 CYP450 대사를 기준으로 설계된 소분자 ADMET 모델은 프로테아제 분해를 통해 대사되는 펩타이드에 메커니즘적으로 적용될 수 없습니다. 또한 ADMETlab 3.0은 2026년 3월 기준 TLS 인증서가 만료되어 서버 접속 자체가 불가능한 상태입니다.

| 도구 | 판정 | 부적합 사유 | 상세 |
|------|:----:|-----------|------|
| **ADMETlab 3.0** | <span class="tag tag-fail">❌</span> | TLS 인증서 만료 + 소분자 전용 | 서버 다운 (2026-03), 119 endpoint 모두 MW<500 기반 |
| **Deep-PK** | <span class="tag tag-fail">❌</span> | 서버 404 + 소분자 전용 | GitHub 404, 웹 ECONNREFUSED, D-MPNN 73 endpoint |
| **pkCSM** | <span class="tag tag-fail">❌</span> | 2015년 obsolete + API 없음 | Graph signature QSAR 기반, Deep-PK에 의해 사실상 대체됨 |
| **admetSAR 2.0** | <span class="tag tag-fail">❌</span> | 배치 20개 제한 + API 없음 | 22,000 후보 처리 불가, 웹 수동 입력만 지원 |
| **ProTox-3.0** | <span class="tag tag-fail">❌</span> | 독성 편중 + API 없음 | ADME 커버리지 부재 (독성 61 endpoint만), 서버 불안정 |
| **SwissADME** | <span class="tag tag-fail">❌</span> | MW 150-500 명시 + Lipinski 전용 | SST-14 1600 Da → 전 항목 violation, 펩타이드 해석 불가 |

<div class="fail">

**공통 근본 원인**: 소분자(MW<500) 훈련 데이터 → SST-14(MW~1600) **적용 가능성 도메인(AD) 3배 초과** · 간 CYP 대사 ≠ 펩타이드 프로테아제 분해 → **메커니즘 불일치**
</div>

---

## A-09: pepADMET — 펩타이드 전용 ADMET의 유일 대안

<div class="res">

**원본 지시**: "김민규 교수팀 JCIM 논문을 검토하여 파이프라인에 적용할 항목을 정리할 것"
**결과**: pepADMET (JCIM 2026, 66, 936-946) 분석 완료 — **36,643개 펩타이드** 학습, 19 ADMET endpoint 지원
</div>

pepADMET이 유일한 대안인 이유는, 현재까지 알려진 ADMET 예측 도구 중 **펩타이드(2-50aa)를 훈련 데이터로 사용한 것이 pepADMET 뿐이기 때문**입니다. 특히 Desmopressin(9aa, Cys1-Cys6 이황화 결합 보유)을 검증 케이스로 사용하여 SS bond가 있는 환형 펩타이드도 처리 가능함을 확인했습니다. SST-14는 구조적으로 Desmopressin과 유사(14aa, Cys3-Cys14)하므로 pepADMET 적용 가능성이 가장 높습니다.

| 차원 | 소분자 ADMET 6종 | **pepADMET** |
|------|:----------------:|:------------:|
| 훈련 데이터 | MW < 500 소분자 | **36,643 펩타이드** (2-50aa) |
| 반감기 메커니즘 | 간 CYP 대사 | **프로테아제 분해** (혈액/조직 5종) |
| SS bond | 훈련 예시 전무 | **Desmopressin 검증** ✅ |
| 환형 펩타이드 | 선형 가정 | **명시 지원** (Cyclosporine 검증) |
| 온프레미스 | 전멸 | 독성 모델 `.pth` **GitHub 공개** |
| Endpoints | MW<500 전용 | **19 ADMET** (독성·투과·반감기) |

---

## A-09: pepADMET — Case Study 3건 검증 결과

pepADMET의 예측 신뢰성을 판단하기 위해 SS bond 보유 펩타이드(Desmopressin), 환형 펩타이드(Cyclosporine), 선형 펩타이드(Leuprolide) 총 3가지 구조 유형에 대해 실험값과 비교 검증을 수행했습니다. **Leuprolide(선형)는 오차 2%로 거의 완벽**하며, Desmopressin(SS bond)도 18% 오차로 실용 범위 내에 있습니다. Cyclosporine의 35% 오차는 환형 특성 특유의 입체 구조를 완전히 반영하지 못한 것으로 해석되며, SST-14에는 Desmopressin 케이스가 더 적합한 참조입니다.

| 펩타이드 | 특성 | T½ 실험값 | T½ 예측값 | 오차 | Toxicity |
|---------|------|:------:|:------:|:----:|:--------:|
| **Desmopressin** (9aa) | Cys1-Cys6 이황화 결합 | 3.00 h | 2.46 h | 18% | Toxic ✅ |
| Cyclosporine (11aa) | 완전 환형 펩타이드 | 19.00 h | 12.28 h | 35% | Non-toxic ✅ |
| Leuprolide (9aa) | 선형 합성 펩타이드 | 3.00 h | 2.95 h | **2%** | Non-toxic ✅ |

> SST-14 (14aa, Cys3-Cys14 SS bond) → Desmopressin과 구조 유사 → pepADMET 적용 가능성 높음, 예측 오차 18% 내외 예상

<div class="res">

**결론**: 소분자 ADMET 6종이 전부 부적합 판정을 받은 상황에서, pepADMET은 현재 시점에서 구조적으로 적합한 **유일한 검증된 대안**입니다.
</div>

---

## A-09: pepADMET 17개 모델 아키텍처 + 실행 로드맵

pepADMET의 19개 endpoint 중 일부는 GitHub에 `.pth` 가중치가 공개되어 오프라인 실행이 가능하고, 나머지는 웹 API 호출이 필요합니다. **독성 모델 12개는 즉시 실행 가능**하며, 투과도·반감기 모델은 웹 API 자동화를 통해 확보할 수 있습니다. 아래 로드맵(PA-01~PA-06)은 의존성 순서를 고려하여 최단 경로로 설계되었습니다.

| 카테고리 | 모델 수 | 아키텍처 | 성능 지표 | 가중치 공개 | 즉시 실행 |
|---------|:------:|---------|------|:----:|:----:|
| **독성** | 12 | MLR-GAT (Graph Attention) | AUC 0.885~0.949 | <span class="tag tag-ok">✅ .pth</span> | **즉시** |
| **투과도** | 5 | GNN + LightGBM | R² 0.43~0.66 | <span class="tag tag-fail">❌</span> | 웹 API |
| **반감기** | 5 | Transfer Learning (RT DB 350K) | R² 0.84~0.98 | <span class="tag tag-fail">❌</span> | 웹 API |
| **Distribution** | 3 | RF / SVM / XGBoost | AUC 0.90 | <span class="tag tag-fail">❌</span> | 재현 가능 |

| 단계 | 작업 | 의존성 | 예상 소요 | 우선순위 |
|:----:|------|--------|:----:|:----:|
| PA-01 | DGL 0.4.3 + PyTorch `pepadmet` env 구축 | 네트워크 | 1일 | P1 |
| PA-02 | SST-14 + 21개 후보 **SMILES 변환** (RDKit) | 없음 | 0.5일 | P1 |
| PA-03 | **독성 모델** 로컬 추론 (binary + 6-class) | PA-01+02 | 0.5일 | P1 |
| PA-04 | **웹 API** 자동화 (permeability/half-life/BBB) | 네트워크 | 1일 | P2 |
| PA-06 | **2,133 feature** → BayesOpt 입력 확장 | PA-02 | 1일 | P2 |

> 전 모델 독립 재현 계획: `pepadmet_reproduction_plan.md` — 5-Phase **6주** 타임라인

---

<!-- _class: divider -->

# Part 4 — A-03 상세
### SSTR 선택성 — AlphaFold CIF→PDB + selectivity_margin

---

## A-03: CIF→PDB 변환 흐름 + 구현 항목 전체

<div class="req">

**원본 지시**: "SSTR1/3/4/5 AlphaFold 구조를 다운로드하고, 선택성 도킹 프로토콜을 구성하며, SSTR2 선택성 스크리닝 파이프라인에 연결할 것"
</div>

AlphaFold EBI API에서 최신 모델 버전을 자동 감지하고, CIF(Crystallographic Information File) 형식으로 다운로드한 뒤 BioPython의 `MMCIFParser`로 파싱하여 PDB 형식으로 변환합니다. CIF 형식을 그대로 PyRosetta에 공급하면 원자 순서 및 chain 인식 오류가 발생하기 때문에 **반드시 PDB 변환이 필요**합니다. 변환 후 PyRosetta의 `FlexPepDockingProtocol`로 오프-타겟 도킹을 수행하여 SSTR2 대비 결합 선호도를 정량 비교합니다.

| 구현 항목 | 상세 설명 | 코드 위치 |
|----------|------|------|
| 오프-타겟 4종 | SSTR1(**P30872**), SSTR3(**P32745**), SSTR4(**P31391**), SSTR5(**P35346**) UniProt ID | `pipeline_config.yaml` |
| AlphaFold 다운로드 | `download_alphafold_structure()` — 최신 버전 자동 감지, 3회 재시도, 실패 시 Estimation 모드 폴백 | `download_alphafold.py` |
| **CIF → PDB 변환** | BioPython `MMCIFParser` → `PDBIO` 저장, chain ID 정규화 포함 | `cif_to_pdb.py` |
| Production 도킹 | PyRosetta FlexPepDock — CA superposition → 키메릭 PDB 조립 → ddG 계산 | `offtarget_dock.py` |
| Estimation 모드 | PDB 없을 때 가우시안 노이즈 폴백 `N(μ=2.0, σ=1.0)` — 파이프라인 중단 방지 | `dock_against_offtarget()` |
| 선택성 마진 계산 | `margin = SSTR2_ddG - worst_offtarget_ddG` | `compute_selectivity_margin()` |
| 선택성 게이트 | `margin ≤ -10.0` **AND** `worst ≥ -15.0` (AND 로직) | `apply_selectivity_gate()` |

<div class="blk">

**블로커**: SSTR1/3/4/5 AlphaFold PDB 미다운로드 (연구실 네트워크 필요) → 도킹 미실행 → selectivity margin 결과 미생성. 코드 로직 자체는 완전 구현 상태이며, PDB 파일만 확보되면 즉시 실행 가능합니다.
</div>

---

## A-03: Production vs Estimation 모드 + 6단계 도킹 흐름

Production 모드와 Estimation 모드의 구분은 **파이프라인의 견고성(robustness)을 위한 설계 결정**입니다. AlphaFold API 접근이 불가한 환경(연구실 테더링, API 일시 다운)에서도 파이프라인이 중단 없이 진행될 수 있도록, PDB가 없을 때는 통계적 분포(정규 분포)에서 샘플링한 추정값으로 대체합니다. 이 추정값은 "근사 결과"임을 로그에 명시하고, Production 실행 후 반드시 교체됩니다.

### Production 모드 — 6단계 도킹 흐름

| 순서 | 단계 | 상세 설명 |
|:----:|------|------|
| ① | SSTR2 복합체 로드 | 펩타이드(≤20aa)와 수용체(~370aa)를 chain 기준으로 자동 분리 |
| ② | 오프-타겟 로드 | AlphaFold PDB 파일 로드 (`AF-P30872-F1-model_v4.pdb` 등) |
| ③ | **CA 구조 정렬** | `superimpose_pose_on_subset_CA()` — SSTR2 수용체 기준으로 오프-타겟 정렬 |
| ④ | **키메릭 PDB 조립** | offtarget receptor(chain B) + 원래 peptide(chain A)를 합성하여 새 PDB 생성 |
| ⑤ | FlexPepDock 정제 | `FlexPepDockingProtocol` 실행, backbone+sidechain 유연성 허용 |
| ⑥ | **ddG 계산** | `InterfaceAnalyzerMover` → kcal/mol + clash_score 반환 |

---

## A-03: selectivity_margin 알고리즘 — 공식 + 예시

`selectivity_margin`은 **"SSTR2에 얼마나 선택적으로 결합하는가"를 수치화한 지표**입니다. 값이 음수일수록 SSTR2 결합력이 오프-타겟보다 강함을 의미합니다. AND 로직을 사용하는 이유는 SSTR2 결합이 강하더라도 오프-타겟 결합 자체가 너무 강하면 부작용 위험이 있기 때문입니다. 예를 들어 bb00_03 후보는 SSTR2 결합이 가장 강하지만(-22.0), SSTR1이 -10.0으로 오프-타겟 결합도 강해 게이트에서 탈락합니다.

### 게이트 조건 수식 (AND 로직)

| 조건 | 수식 | 임계값 | 해석 |
|:----:|------|:------:|------|
| ① 선택성 마진 | `SSTR2_ddG - worst_OT_ddG ≤ thresh` | **-10.0 kcal/mol** | SSTR2가 오프-타겟보다 최소 10 kcal/mol 더 강하게 결합해야 |
| ② 오프-타겟 한계 | `worst_OT_ddG ≥ thresh` | **-15.0 kcal/mol** | 가장 강한 오프-타겟 결합도 -15.0보다 약해야 (부작용 방지) |

### 예시 케이스 3건 — 게이트 통과 여부

| 후보 | SSTR2 | SSTR1 | SSTR3 | worst OT | margin | 조건① | 조건② | **결과** |
|------|:-----:|:-----:|:-----:|:-----:|:------:|:-:|:-:|:------:|
| bb00_01 | -20.0 | -4.0 | -3.5 | -4.0 | **-16.0** | ✅ | ✅ | <span class="tag tag-ok">PASS</span> |
| bb00_02 | -15.0 | -8.0 | -6.0 | -8.0 | **-7.0** | ❌ | ✅ | <span class="tag tag-fail">FAIL (margin 부족)</span> |
| bb00_03 | -22.0 | -10.0 | -8.0 | -10.0 | **-12.0** | ✅ | ❌ | <span class="tag tag-fail">FAIL (OT 결합 강함)</span> |

---

<!-- _class: divider -->

# Part 5 — A-05
### 가중합 탈피 — 4단계 대안 스코어링 체인

> **A-04** 전체 표·`classify_cluster()` 검증: 앞부 **「A-04: Cluster A~E」** 및 동일 묶음의 `marp_meeting_dark.md`(다크 원본).

---

## A-05: 기존 가중합의 문제점

<div class="req">

**원본 지시**: "BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성 Step 3B 재설계"
</div>

기존 가중합 방식(0.45/0.20/0.15/0.10)의 근본적 문제는 **가중치가 연구자의 주관적 판단에 의존**한다는 점입니다. ddG가 단위 차이로 10배 차이나더라도 고정 가중치 하에서는 그 차이가 선형으로만 반영됩니다. 또한 한 지표가 극단값을 가질 경우 다른 지표들이 희석되는 아웃라이어 민감성 문제가 있습니다. **신규 4단계 체인은 이 두 문제를 모두 해결**합니다. ECR(Exponential Cumulative Rank)은 순위 기반 합의로 아웃라이어를 억제하고, Pareto 프론트는 어떤 목적도 가중치 없이 공정하게 처리합니다.

| 차원 | 기존 (0.45/0.20/0.15/0.10 가중합) | 신규 4단계 체인 |
|------|--------------------------|----------|
| 방식 | 선형 스칼라 합산 | **GNINA→ECR→Pareto→BO** 4단계 |
| 가중치 | 고정 (연구자 주관) | 동적 (순위 기반 ECR + 비지배 프론트) |
| 아웃라이어 민감성 | 높음 (절대값 직접 사용) | 낮음 (지수 합의, Pareto 프론트) |
| 탐색-활용 균형 | 없음 (greedy) | **GP surrogate + UCB** 베이즈 최적화 |
| 다목적 최적화 | 단일 스칼라로 압축 | **4개 목적 동시 최적화** |

---

## A-05: 4단계 체인 — 각 모듈의 역할

4단계 체인은 순차적으로 실행되며, 각 단계의 출력이 다음 단계의 입력이 됩니다. GNINA가 물리 기반 도킹 재점수를 제공하고, ECR이 3종 스코어를 합의 점수로 집약하며, NSGA-II Pareto가 다목적 비지배 프론트를 구성하고, 마지막으로 BO가 GP 서로게이트를 학습하여 다음 iteration에서 탐색할 mutation을 능동적으로 제안합니다.

| 단계 | 모듈 | 알고리즘 | 입력 → 출력 | 테스트 |
|:----:|------|---------|-----------|:-----:|
| ① | `gnina_rescoring.py` | GNINA v1.3.2 CNN + Vina 이중 스코어 | PDB 파일 → CNN score, Vina score, CNNaffinity | 24 |
| ② | ECR consensus | `Σ exp(-rank_i/N)` 순위 기반 합산 | 3종 score → 단일 ecr_score | — |
| ③ | `pareto_ranking.py` | NSGA-II (pymoo) + crowding distance | 4목적 벡터 → Pareto front + crowding 거리 | 9 |
| ④ | `bayesian_optimizer.py` | OneHot/ESM-2 인코딩 → GP → UCB 획득 함수 | 후보 서열 → 다음 mutation 제안 | 27 |

### Pareto 4목적 + 2제약 조건

| 목적 함수 (최소화) | 의미 |
|-------------|------|
| ddG | SSTR2 결합 자유에너지 (kcal/mol) |
| -stability | 안정성 (Instability Index 역수) |
| -druggability | 드럭어빌리티 점수 역수 |
| -diversity | 후보군 다양성 역수 |

| 제약 조건 | 임계값 | 의미 |
|---------|:------:|------|
| `hard_violations` | ≤ 0 | FWKT/SS bond/pI 등 구조 규칙 위반 없어야 |
| `clash_score` | ≤ 10.0 | 도킹 복합체 입체 충돌 없어야 |

<div class="blk">

**잔여 작업 D5**: `runner.py`에 4단계 체인 통합 연결 — 예상 2-3시간, 외부 의존성 없음
</div>

---

<!-- _class: divider -->

# Part 7 — A-08 / A-10 상세
### 방사화학 메트릭 — Radiolysis + Metal Coordination

---

## A-08/A-10: W8이 왜 Critical인가 — 화학적 근거

<div class="req">

**A-08**: "13-메트릭에 Selectivity Margin, Radiolysis Susceptibility, Chelator Binding Compatibility를 추가할 것"
**A-10**: "RCP(방사화학 순도) 안정성 예측 위한 radiolysis risk 구현 확인"
</div>

방사성의약품에서 방사선분해(radiolysis)는 방사성 동위원소가 붕괴할 때 발생하는 에너지(β 입자, γ선 등)가 인접 분자의 화학 결합을 파괴하는 현상입니다. **Trp(W)의 indole ring은 방사선에 의해 kynurenine으로 산화되는 반응이 타 아미노산 대비 6배 이상 빠릅니다.** W8은 FWKT 약리단의 핵심 잔기이므로 이것이 산화되면 SSTR2 결합 능력이 직접 손실됩니다. 이것이 W8을 "이중으로 critical한 잔기"로 분류하는 이유입니다.

### `calculate_radiolysis_susceptibility()` — SST-14 잔기별 위험도

| pos | aa | 산화 메커니즘 | 기본 점수 | SS bond 보정 | 최종 | FWKT |
|:---:|:--:|-------------|:----:|:-------:|:----:|:----:|
| 3 | **C** | SS bond 파괴 (단, SS 형성 시 thiol 산화 저항) | 2.0 | → **1.0** | 1.0 | — |
| 6 | F | aromatic ring hydroxylation | 0.5 | — | 0.5 | — |
| 7 | **F** | aromatic ring hydroxylation | 0.5 | — | 0.5 | ✓ |
| **8** | **W** | **indole ring → kynurenine (자유 라디칼 공격)** | **3.0** | — | **3.0** | **★** |
| 11 | F | aromatic ring hydroxylation | 0.5 | — | 0.5 | — |
| 14 | **C** | SS bond 파괴 (단, SS 형성 시 thiol 산화 저항) | 2.0 | → **1.0** | 1.0 | — |
| | | **합계** | | | **6.5** | <span class="tag tag-fail">HIGH</span> |

> **W8(Trp)**: FWKT 약리단 핵심 + 방사선 최취약 → 대응 전략: **5-fluoro-Trp 치환** (방사선 저항성 증가) 또는 **Met 스캐빈저 첨가** (제형 최적화)

---

## A-08: Metal Coordination + Chelator Binding 분석

`analyze_metal_coordination()` 함수는 펩타이드 서열을 스캔하여 금속 이온 배위에 참여할 수 있는 잔기를 식별하고, ⁶⁸Ga/¹⁷⁷Lu/²²⁵Ac 각각에 대한 직접 배위 가능성을 판단합니다. Ga³⁺와 Lu³⁺/Ac³⁺는 carboxylate 산소(Asp/Glu)를 통한 배위를 선호하는 반면, Zn²⁺/Cu²⁺는 imidazole(His) 및 thiolate(Cys)를 선호합니다. SST-14 native 서열에는 His, Asp, Glu가 없으므로 Ga³⁺/Lu³⁺ 직접 배위가 불가합니다.

### 금속별 배위 잔기 선호도 — Rulisek & Vondrasek 1998 기반

| 아미노산 | 배위 자리 | 배위 강도 | Zn²⁺ | Cu²⁺ | **Ga³⁺** | **Lu³⁺** | **Ac³⁺** |
|---------|---------|:----:|:----:|:----:|:-------:|:-------:|:-------:|
| **H** (His) | imidazole N | 강 | ✅ | ✅ | **✅** | — | — |
| **C** (Cys) | thiolate S | 강 | ✅ | ✅ | — | — | — |
| **D** (Asp) | carboxylate O | 중 | — | — | **✅** | **✅** | **✅** |
| **E** (Glu) | carboxylate O | 중 | — | — | **✅** | **✅** | **✅** |
| M (Met) | thioether S | 약 | — | ✅ | — | — | — |

### SST-14 native 분석 결과 + 설계 함의

| 잔기 유형 | SST-14 위치 | Ga³⁺/Lu³⁺ 직접 배위 |
|------|------|----------|
| Cys (thiolate) | C3, C14 | SS bond 형성 시 **불가** |
| **D/E (carboxylate)** | **없음** | **Ga³⁺/Lu³⁺ 직접 배위 불가** |

> SST-14에 D/E 없음 → **N-말단 DOTA 킬레이터 필수** (구조 규칙 #5)
> 변이체 설계 시 D/E 도입하면 Ga³⁺ 직접 배위 가능성이 생기며, 킬레이터 부담을 경감할 수 있습니다

---

<!-- _class: divider -->

# Part 8 — 회의록 전체
### 1차·2차 미팅 31건 대응 현황

---

## 1차·2차 미팅 31건 대응 현황

2026년 1월(1차)과 2월(2차)에 걸쳐 제기된 총 31건의 요청 사항에 대한 현재 대응 상황입니다. 1차 미팅(MD Agent 아키텍처)의 요청들은 대부분 파이프라인 뼈대로 구현되어 완료 또는 부분 완료 상태입니다. 2차 미팅(25건)은 카테고리별로 완성도 차이가 크며, **추천 도구 5종 중 4종이 미완료**인 것이 눈에 띕니다. 이는 해당 도구들이 외부 서버 의존적이거나 별도 GPU 연산이 필요하기 때문입니다.

### 1차 미팅 (2026-01-26) — MD Agent 아키텍처 6건

| ID | 원본 요청 | 대응 상태 | 비고 |
|:--:|----------|:----:|------|
| M1-1 | SSTR2 DOTATATE 유도체 AI 설계 시스템 | <span class="tag tag-ok">✅</span> | Silo A + Silo B 듀얼 파이프라인 구현 완료 |
| M1-2 | BioNeMo API 연결 | <span class="tag tag-ok">✅</span> | 8개 NIM 래퍼 구현 완료 |
| M1-3 | BioNeMo 불가 시 수동 접근 | <span class="tag tag-ok">✅</span> | 로컬 전환 3 conda env 스크립트 완비 |
| M1-4 | Rosetta FlexPepDock 도킹 | <span class="tag tag-ok">✅</span> | 2단계 전략 (screening + validation) |
| M1-5 | SSTR 특이성 스크리닝 | <span class="tag tag-warn">⚠️</span> | SSTR5만 완료, SSTR1/3/4 PDB 미다운로드 |
| M1-6 | 혈액 6-10일 Stability | <span class="tag tag-warn">⚠️</span> | II + protease surrogate 구현, pepADMET 대기 |

### 2차 미팅 (2026-02-12) — 25건 카테고리별 요약

| 카테고리 | 총 | ✅ | ⚠️ | ❌ | 핵심 미완 |
|---------|:--:|:--:|:--:|:--:|---------|
| 구조 예측 | 2 | 2 | 0 | 0 | 전 완료 |
| 후보 설계 | 3 | 3 | 0 | 0 | 전 완료 |
| **Stability Agent** | 4 | 1 | 1 | **2** | rigidity(OpenMM), PEG(Phase 4) |
| Docking Agent | 2 | 1 | 1 | 0 | SSTR1/3/4 |
| ADME 도구 | 3 | 2 | 1 | 0 | GPU |
| 파이프라인 1~7 | 7 | 6 | 0 | **1** | Step 7 Phase 4 |
| 추가 검토 | 5 | 4 | 1 | 0 | — |
| **추천 도구** | 5 | 0 | 1 | **4** | CycPeptPPB, CleaveNet, AGGRESCAN3D, OpenMM |

> **31건 합계**: ✅ 16 (52%) · ⚠️ 7 (23%) · ❌ 8 (26%)

---

<!-- _class: divider -->

# Part 9 — 로컬 모델 전환
### 서버 `pipeline_local`와 연구실 PC — 맥락 공유

앞부 **인프라 Before/After**·`marp_migration.md`는 **서버 측** 마이그레이션·벤치마크 중심입니다. 아래는 **연구실·워크스테이션** 기준 NIM 탈피·conda 매핑·USB 이식까지 포함합니다.

---

## 로컬 모델 전환: 왜 NIM에서 벗어나야 하는가

NIM(NVIDIA Inference Microservice) Cloud API를 사용하던 방식에서 로컬 온프레미스 모델로 전환하는 결정은 **연구실 환경의 실용적 제약에서 비롯된 것**입니다. 첫째, NIM API는 NGC(NVIDIA GPU Cloud) API 키와 안정적인 인터넷 연결이 필수적인데, 연구실의 테더링 환경에서는 대용량 추론 요청 시 타임아웃이 빈번히 발생합니다. 둘째, 22,000개 후보를 처리하는 배치 작업에서 클라우드 API는 rate limit과 비용 문제가 발생합니다. 셋째, **데이터 보안** 측면에서 미발표 연구 데이터를 외부 서버로 전송하는 것은 바람직하지 않습니다.

### 8개 NIM API Tool → 로컬 대체 매핑

| NIM Tool | Step | 로컬 모델 | conda env | 상태 |
|----------|:----:|---------|-----|:-:|
| `esmfold_tool.py` | 04 | ESMFold (HuggingFace, fp16 ~4GB VRAM) | bio-tools | <span class="tag tag-fail">❌ 대기중</span> |
| `proteinmpnn_tool.py` | 03 | LigandMPNN (pip install, <1GB) | bio-tools | <span class="tag tag-fail">❌ 대기중</span> |
| `rfdiffusion_tool.py` | 02 | RFdiffusion (8 ckpt, ~10GB) | rfdiffusion | <span class="tag tag-fail">❌ 대기중</span> |
| `diffdock_tool.py` | 05 | **DiffPepDock** (8-30aa 펩타이드 전용) | diffpepdock | <span class="tag tag-fail">❌ 대기중</span> |
| `boltz2_tool.py` | 05 | FlexPepDock 대체 검토 중 | — | ⏸️ |
| (PyRosetta) | 06 | FlexPepDock local (PyRosetta 라이센스) | bio-tools | <span class="tag tag-ok">✅ 완료</span> |
| **GNINA** | rescore | v1.3.2 (~1.4GB, CUDA 12+cuDNN9) | — | <span class="tag tag-ok">✅ 완료</span> |

<div class="blk">

**핵심 블로커**: bio-tools, rfdiffusion, diffpepdock 3개 env의 PyTorch + 모델 가중치 합계 **~23GB** 미다운로드 — 테더링 환경 한계. 집 WSL에서 사전 다운로드 후 USB 이식 예정.
</div>

---

## 로컬 전환 후 On-Premise 성능 비교

로컬 RTX 4090 (24GB VRAM) 기준으로 NIM 클라우드 대비 ESMFold와 ProteinMPNN은 **3-5배 속도 향상**이 예상됩니다. RFdiffusion은 네트워크 지연이 없어도 연산 자체가 무거워 클라우드와 비슷하거나 로컬이 약간 느릴 수 있습니다. 그러나 **오프라인 가용성과 배치 처리 무제한**이 핵심 이점입니다. FlexPepDock은 NIM API가 아예 없어 로컬만 가능합니다.

| 모델 | NIM (클라우드, 네트워크 포함) | 로컬 (RTX 4090) | 개선 비율 |
|------|:-------------:|:----:|:----:|
| ESMFold (14aa 펩타이드) | 2-3초 | **0.5-1초** | **3~5×** |
| ProteinMPNN (8 시퀀스) | 3-5초 | **1-2초** | **2~3×** |
| RFdiffusion (1 backbone) | 10-20초 | 15-30초 | ~동등 (네트워크 없어도 연산 무거움) |
| FlexPepDock (1 정제) | — | 30-60초 | **로컬 전용** |

### BaseTool 인터페이스 호환성 유지 전략

로컬 전환 시 **호출 코드를 변경하지 않도록** `BaseTool` 인터페이스를 동일하게 유지합니다. NIM API 방식의 `_post_timed()` HTTP 호출을 로컬 Python `model(**tokens)` 직접 호출로 교체하되, 반환 타입(`ToolResult`)은 동일하게 유지합니다.

| 차원 | NIM API (현재) | 로컬 전환 후 |
|------|:------------:|:-------------:|
| 호출 방식 | `_post_timed()` HTTPS REST | Python `model(**tokens)` 직접 호출 |
| API 키 필요 | NGC_CLI_API_KEY 필수 | **불필요** |
| Rate Limit | 429 오류, exp backoff | **없음** |
| 오프라인 가용 | ❌ | **✅** |
| 반환 인터페이스 | `ToolResult` | **동일** `ToolResult` |

> 1 iteration 예상 처리 시간: NIM 5-10분 → 로컬 **2-5분** · CI Job 5(NIM smoke test): `continue-on-error: true` 유지

---

## 오프라인 이식 전략 — 3단계 스크립트

테더링 환경에서 ~23GB 모델 가중치를 직접 다운로드하는 것은 현실적으로 불가합니다. 이를 해결하기 위해 **집 WSL 환경에서 사전 다운로드 → USB 이식 → 연구실 오프라인 설치**의 3단계 전략을 수립했습니다. 이 방식은 한 번 USB를 만들어두면 이후 환경 재구축 시에도 네트워크 없이 설치할 수 있어 재현성 측면에서도 유리합니다.

| 스크립트 | 실행 장소 | 주요 역할 |
|---------|------|------|
| `scripts/setup_local_models.sh` | 네트워크 OK 환경 | conda env 생성 + pip 설치 + 모델 가중치 온라인 직접 다운로드 |
| `scripts/download_models_offline.sh` | **집 WSL** (고속 인터넷) | PyTorch wheel + conda 패키지 + 모델 가중치 사전 다운로드 (~23GB → USB) |
| `scripts/install_from_offline.sh` | **연구실** (오프라인) | USB 마운트 → conda/pip 오프라인 설치 → 모델 가중치 복사 |

### 모델별 예상 다운로드 용량

| 모델 | 용량 | 비고 |
|------|:----:|------|
| ESMFold (HuggingFace fp16) | ~4 GB | `esm2_t48_15B_UR50D` 가중치 |
| ProteinMPNN (LigandMPNN) | < 1 GB | pip 패키지 + 가중치 |
| RFdiffusion (8 checkpoints) | ~10 GB | `rfdiffusion` GitHub 공식 |
| DiffPepDock | ~2 GB | 펩타이드 전용 도킹 모델 |
| PyTorch + CUDA wheel | ~6 GB | cu118/cu117 버전별 상이 |
| **합계** | **~23 GB** | USB 32GB 이상 권장 |

---

<!-- _class: divider -->

# Part 10 — 미완료 + 다음 단계
### Wave 1~4 의존성 체인 + RI팀 협의

---

## 미완료 19건 — Wave별 의존성 분류

미완료 19건을 4개 Wave로 분류한 기준은 **외부 의존성 유무와 실행 순서**입니다. Wave 1은 현재 즉시 실행 가능한 항목으로, 네트워크나 외부 데이터 없이 코드 작업만으로 완료됩니다. Wave 2는 모델 다운로드(USB 이식) 또는 API 접근이 확보된 이후 진행 가능합니다. Wave 3~4는 앞 단계의 결과물이 입력으로 필요한 순차 의존 항목입니다.

### Wave 1: 즉시 실행 가능 (코드만, 외부 의존성 없음)

| 항목 ID | 설명 | 예상 소요 | 담당 |
|------|------|:----:|:----:|
| **D5** | `runner.py`에 GNINA→ECR→Pareto→BO 4단계 체인 통합 연결 | 2-3h | AI팀 |
| **B8** | `pharmacology.py` → `pharma_properties.py` 래핑 (중복 제거 리팩토링) | 2-3h | AI팀 |
| **B9** | DPP-IV protease 추가 (혈청 안정성 커버리지 확장) | 1h | AI팀 |
| **B10** | Ga³⁺ D/E carboxylate 배위 추가 (⁶⁸Ga 킬레이션 정확도 개선) | 30m | AI팀 |
| **UI** | PharmacologyPanel에 MW/radiolysis/SS-pI 결과 표시 | 1-2h | AI팀 |

### Wave 2: 네트워크/데이터 확보 후

| 항목 | 의존성 | 비고 |
|------|--------|------|
| **E7** 모델 23GB 다운로드 | 집 WSL → USB 이식 | 가장 큰 단일 블로커 |
| **E4** bio-tools → **D6** ESM-2 → **E8** adapter | E7 순차 완료 후 | 3단계 순차 chain |
| **E5** rfdiffusion / **E6** diffpepdock | E7 완료 후 | 병렬 진행 가능 |
| **A-03** SSTR1/3/4/5 PDB + selectivity margin 실행 | AlphaFold API 접근 | 도킹 결과 최초 생성 |

---

## Wave 3~4 + 코드 품질 지표 + RI팀 확인 사항

Wave 3는 pepADMET 환경이 구축된 후 독성 모델부터 순차 실행하고, Wave 4는 Silo B 전체 22,000 후보 대상 FlexPepDock 대규모 도킹을 실행하는 단계입니다. Wave 4는 trial당 ~70초, 평균 5-6 trial 수렴 기준으로 **1후보당 약 6-7분**이 소요되며, 22,000 후보 전체는 약 2,200시간(분산 처리 필요)입니다.

| Wave | 항목 | 의존성 |
|:----:|------|--------|
| **3** | C6 pepADMET 독성 (DGL 0.4.3 env) · C7 descriptor 생성 · C8 웹 API 자동화 | Wave 2 완료 |
| **4** | Silo B 22,000 후보 FlexPepDock → C4 PRODIGY ΔG 검증 | Wave 3 완료 + 분산 처리 인프라 |

### 코드 품질 지표 (이번 스프린트 변화)

| 메트릭 | 스프린트 시작 | 현재 | 변화 |
|--------|:----:|:----:|:----:|
| 테스트 파일 수 | 34 | **40+** | +6 |
| 테스트 함수 수 | ~453 | **~510** | **+57** |
| pharma 메서드 수 | 13 | **15** | +2 (MW, radiolysis 신규) |
| DIWV lookup 오류 | 16 | **0** | **-16 (전체 수정)** |
| CI 통과 Jobs | 6/7 | **7/7** | 전 job 통과 |
| 테스트 커버리지 | ~90% | **~93%** | +3%p |

### RI팀 확인 필요 항목

| 액션 | 원본 요청 | 이번 회의 확인 내용 |
|:----:|----------|------|
| **A-06** | Peptron / HLB PEP / Anygen DOTA 합성 견적 | 진행 여부 + 예상 일정 |
| **A-07** | 상위 3개 Lys/N-말단 C18 변형체 설계 | Top-K 후보 확정 이후 착수 가능 |
| — | pepADMET 웹 API (`pepadmet.ddai.tech`) | 기관 네트워크에서 접근 가능 여부 |

> 다음 보고: **2026-04-06** · Linear `CHA-xx` · `bio_linear_ssot.md`

---

<!-- _class: cover -->

# Q & A

<br>

`meet_log.md` — A-01~A-10 대응 상세 + pepADMET 19 endpoint
`progress_report_20260323.md` — 이슈 1~9 상세 보고
`action_items_tracker.md` — 65건 통합 추적 (7출처, M1/M2 31건)
`pepadmet_reproduction_plan.md` — 전 모델 재현 5-Phase 6주
`serum_stability_admet_tools_report.md` — 16개 ADMET 도구 평가
