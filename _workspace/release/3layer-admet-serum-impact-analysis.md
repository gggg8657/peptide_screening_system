# 3-Layer Ensemble과 Serum Stability / ADMET (A-02·A-03) — 코드·문서 기반 영향 분석

**작성일**: 2026-05-27  
**리포**: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`  
**청자 전제**: 생명공학·가속기 박사급 연구자, 펩타이드 스크리닝 파이프라인은 초회  
**메타**: 사용자 요청대로 과장 없이 코드·문헌 레지스트리(`pharmacology_guards`)에 근거한 사실 우선 서술.

---

## 1. 목적과 범위

4월 회의 A-02(혈청 반감기)·A-03(ADMET)에서 확인된 핵심 문제는 **D-AA·환형(SS bond)·DOTA 같은 전형적인 PRST 후보 구조에 대해 공개 도구 적용 가능성과 외삽(OOD) 위험**이다. 본 보고서는 5월 main에 반영된 **3-Layer Ensemble 관련 코드**가 그 문제를 “해결”하는지, 아니면 “한계와 모순을 구조적으로 드러내는 프레임”인지 분리해서 정리한다.

**분석 한계(정직 명시)**

- 사용자 워크스페이스의 현재 git `HEAD`는 `docs/schrodinger-proposal-d2-20260526` 브랜치 tip (`7e79169…`)이다. 검증 결과 **`e3a5413`(PR #117, ADMET divergence guard)** 는 **현재 브랜치 조상에 없다**. 따라서 **워킹 트리의 `composite_scorer.py`**에는 divergence 로직이 없고, 아래에서는 **히스토리에 존재하는 커밋 설명(#117)**과 **현재 체크아웃**을 구분했다.
- `recommended_for_decision` 문자열은 **레포 검색 결과** `predict_admet_ai_wrapper.py`, `ENDPOINT_CONFIDENCE["admet_ai_extrapolation"]`, 테스트에서만 확인되었으며 **`enrich_candidates_from_wrappers`나 Tier/Hard Cutoff와 자동 결합되어 있지 않다**.

---

## 2. A. 사실 조사 — 구현 상태 (파일·도구·라우팅)

### 2.1 Layer 정의 파일 (코드 매핑)

| Layer | 모듈 / 파일 | 실제 하는 일 |
|-------|-------------|-------------|
| **Layer 1** | `pipeline_local/scoring/layer1_ensemble.py` | 표준 **선형·대문자 L-AA** 에 대해 시간 단위 출력이 있는 wrapper만 가중 평균. 호출 대상은 코드상 **PlifePred(시간 가능 시)**, **HLE regression callable**, **pepADMET HBM 웹(파싱 미구현→사실상 unavailable 다수)** |
| **Layer 2** | `pipeline_local/scoring/layer2_ensemble.py` | 라우팅 경로 **`layer2_daa_cyclic_pepmsnd`**일 때 로컬 **PEPlife2 학습된 GAT+log1p(t½) 회귀** (`_workspace/pepmsnd_local/` + 격리 conda) subprocess 호출 |
| **Layer 3 (반감기 경로 스텁)** | `pipeline_local/scoring/ensemble_router.py` | **`run_routed_halflife`** 주석 및 구현 그대로: **Layer 2만 실구현**, **`layer3_dota_admet_ai_md_proxy_stub`는 시간 반감기 `None` + 경고 문자열만** |
| **Layer 3 (ADMET-AI 보조 모델)** | `pipeline_local/scripts/predict_admet_ai_wrapper.py` | ADMET-AI 추론 + **항상 `recommended_for_decision: False`** + extrapolation 경고 |

**라우터** (`ensemble_router.route_halflife_prediction`)

- DOTA 문자열 또는 `has_dota` → `layer3_dota_admet_ai_md_proxy_stub`
- **소문자 잔기(D-AA 표기) 또는 cyclic 휴리스틱(대문자 C가 2개 이상 등)** → `layer2_daa_cyclic_pepmsnd`
- 그 외 “선형 L-AA” 패턴 → `layer1_l_aa_ensemble_stub` 로 라벨 (단, 실행 함수는 아래 참고)

중요하게, **`run_routed_halflife`는 Layer 1을 호출하지 않고 스텁 메시지를 넣어 반환한다.** Layer 1의 실연산 엔드포인트는 **`compute_layer1_halflife`를 직접 호출하는 경로**(테스트·수동 실행)으로 분리되어 있다.

### 2.2 P1 복합 스코어 enrichment 경로와의 관계 (**불일치**)

표준 파이프라인에서 후보 리스트 보강에 쓰는 함수는 **`pipeline_local/scripts/composite_scorer.py`의 `enrich_candidates_from_wrappers`**이다.

- **D-AA 감지 시**: wrapper **전체 스킵**, `halflife_confidence_grade` / `admet_confidence_grade` = `UNAVAILABLE`, 노트만 남김.
- **그 외**: `predict_halflife` (**predict_halflife_pepmsnd.py**) 및 `predict_admet` (**predict_admet_pepadmet.py**)를 호출한다.
- **`run_routed_halflife`, `compute_layer1_halflife`, `predict_admet_layer3`는 이 함수에서 import·호출되지 않았다**(현재 브랜치 워킹 트리 기준, 전역 grep 결과 일치).

**정리**: “3-Layer가 main enrichment에 매달려 있다”는 서술은 **현 코드 기준 오류**. main에 존재하는 것은 **(a)** 모듈·테스트·가드 메타데이터 **(b)** 라우팅 가능한 subroutine **이며**, **복합 스코어 기본 enrichment는 구 경로**(단일 반감기 wrapper + 로컬 pepADMET 계열)다.

### 2.3 외부 도구 이름과 코드의 매핑

| 기능 | 코드·문서상 도구 |
|------|------------------|
| Half-life enrichment (비 D-AA) | PlifePred2 경로 (**확률/랭킹 스코어가 시간 아님** — 파일 상단 및 `HALFLIFE_PLIFEPRED2_CONFIDENCE`) |
| Layer 2 | 로컬 **PEPlife2 기반 간소 회귀** (공식 PepMSND 논문과 동일 스택이라고 단정 불가 — `layer2_ensemble.py` 주석 및 train 메모 인용) |
| ADMET (enrichment) | 로컬 **pepADMET GNN toxicity 재학습 가중치**(가능 시), modlamp surrogate, 웹 403 시 실패 |
| Layer 3 ADMET-AI | Chemprop 기반 **소분자** ADMET-AI — **펩타이드·DOTA는 외삽 취급** (`predict_admet_ai_wrapper.py` 경고 문자열 그대로) |

**ProtParam·HLP·Tan2024 transfer learning 등**은 `pharmacology_guards.ENDPOINT_CONFIDENCE` 및 `HEURISTIC_FUNCTION_DISCLAIMERS` 레지스트리에는 등록되어 있으나, **현 `layer1_ensemble.compute_layer1_halflife`의 직접 caller 목록에는 없다.**

### 2.4 출력 형식 (“schema” 요약)

- **Layer 1 dict**: `ensemble_halflife_hours`, `individual_predictions`, `recommended`, `warnings` 등 (`layer1_ensemble.py`).
- **Layer 2 dict**: `ensemble_halflife_hours`(성공 시), `applicability`, `confidence_grade`(via `attach_confidence`), 고정 문구 **`저신뢰(P4): … test R²<0`** 경고 추가 (`layer2_ensemble.py` L155–157).
- **ADMET Layer 3 wrapper dict**: `predictions`, **`recommended_for_decision: False`** (항상).

### 2.5 PR 머지 해시 및 이후 변경 (저장소 히스토리 기준)

| 항목 | 전체 커밋 해시 | 메시지에 나타난 PR |
|------|----------------|-------------------|
| 3-Layer framework | `5b57481983bd9682c9cf4247398f1f44d1bb938f` | **#85** |
| pepADMET 재훈련 + 동적 OOD | `f72c48ee657e8d56b1e93ae0c69f400df827cb51` | **#113** |
| ADMET 모델 간 불일치 경고 보강 | `e3a541342ac35fe0203583c7ac1bb10ca9042d17` | **#117** (본 분석 시점 사용자 브랜치 **미포함**) |

**PR #112 (사용자 질문에 명시된 번호)**  
- git subject에 `(#112)`가 박힌 머지 커밋은 **본 저장소 로그 검색으로는 확인되지 않았다**. 대신 레이어2 재학습 실험으로 보이는 커밋 **`299b100a282e14058035f2701975c8a2d8e1eb37`** (`experiment(layer2): pepMSND 재학습…`) 등이 존재한다 → **외부 PR 번호 매핑은 GitHub 웹/UI로 재확인 필요**.

### 2.6 Serum stability · D-AA 각 Layer 반응

| 입력 유형 | `route_halflife_prediction` 결과 | 코드상 의미 |
|----------|----------------------------------|-----------|
| D-AA 표기 (`[a-z]` 등) 또는 cyclic 휴리스틱 | Layer **2** | subprocess 로컬 회귀 시도 가능 — 단 `check_pepmsnd_local_applicability`는 **D-AA support False** 명시 (`pharmacology_guards.py`). 실제 SMILES 생성 실패 → `hours` 불가 패턴 가능. |
| DOTA | Layer **3 스텁** (`ensemble_halflife_hours` 없음) | 반감기 수치 제공 안 함. |
| 순수 선형 대문자 L-AA | 라우터 레이블 상 Layer **1** | **`run_routed_halflife`는 호출 안 하고 스텁 경고 반환.** |

별도 **`enrich_candidates_from_wrappers`**: **D-AA는 Layer 2로 라우팅하지 않고** 아예 호출 차단(UNAVAILABLE).

### 2.7 ENDPOINT_CONFIDENCE 혈청 7종 + 의사결정 반영 여부

`pharmacology_guards.ENDPOINT_CONFIDENCE`에는 혈청 계열 **`halflife_pepmsnd` 등 7키** 및 ADMET 계열 **`admet_ai_extrapolation` 등** 이 등록되어 있다 (`benchmark_test_r2_hours_2026_05_20: -0.028` 포함).

**중요 사실**: 이 테이블은 **`attach_confidence`로 응답 메타 삽입**할 때 참고되도록 설계되었으며, **`CompositeScorer._check_hard_cutoffs` 가 `ENDPOINT_CONFIDENCE` 테이블을 읽어 cut-off를 바꾸지는 않는다.** Hard cutoff의 `admet_tox_max` 등은 후보 필드 숫자(`admet_tox`)와만 비교 (`scripts/composite_scorer.py`).  
즉 “신뢰도 레이블로 자동 탈락”이라기보다 **문자열·등급을 붙여 H-06(휴리스틱 오용 차단)**에 기여한다.

### 2.8 ADMET·OOD·Disclaimer

**(1) OOD (#113)**

- 신경망 쪽 구현 파일: `pipeline_local/pepadmet_ood/ood_detection.py` (Mahalanobis + MC dropout 개요).
- **일상 경로** `predict_local_gnn_toxicity`(predict_admet_pepadmet 내)는 코드 주석대로 **`descriptor=0 외삽`이며 동적 OOD 계산 불가 → `ood_warning`이 항상 True일 수 있는 경로가 문서화**되어 있다. 별도 CLI `pepadmet_infer_ood.py` 언급은 동 파일 주석 참고.

**(2) `HEURISTIC_FUNCTION_DISCLAIMERS` “4개”와 합성 의뢰서**

- `STATUS_2026-05-20.md`는 **외부 도구 블록 `external_tool.*` 를 4개 추가**로 요약했다. 현재 코드의 `HEURISTIC_FUNCTION_DISCLAIMERS`에는 그 외 **`step08_stability.*`, `backend.pharmacophore.*` 등 다수 항목**이 공존한다.
- **합성 의뢰서 4종**은 개별 레지스트리 키를 붙여넣기보다 **`H-06 가드 disclaimer`**, **`pepADMET binary_toxicity=1.00 OOD 가능성`** 등의 **운영 서술**로 흡수되어 있다 (`runs_local/final_candidates/synthesis_orders/PRST-*.md`).
- 따라서 사용자 질문의 “4항목이 의뢰서에 어떻게 박히나?”에 대한 정직한 답: **합성 의뢰서는 코드 키 4개를 직렬화하지 않는다.** 다만 같은 정책을 **저신뢰·외삽·wet-lab 병행** 문장으로 반영했다.

### 2.9 PRST-001~004 합성 의뢰서에 보이는 3-Layer / 플래그

**관찰 결과 (파일 원문)**

- **“Layer 1/2/3”, “ensemble_halflife_hours”, “ADMET-AI Layer 3” 표기 없음**.
- Stability는 **`predict_half_life` / `step08_stability.py` 기반 HEURISTIC**으로 명시.
- ADMET은 **pepADMET local 재검증값 1.00 + OOD 해석 가능성**.
- **`recommended_for_decision` 문자열 부재.**

Tier·Hard Cutoff는 문서 표에 **`ADMET 실측 1.00, cutoff 미통과`**와 같이 적혀 있으나**, 이는 사람이 작성한 게이팅 표현이지 `recommended_for_decision=False` 코드 플래그가 아니다.**

---

## 3. B. 객관 평가

### 3.1 “해결책”인가 “한계 노출 프레임”인가

| 주장 레벨 | 판단 |
|----------|------|
| **혈청 t½ 또는 ADMET 독성의 절대값을 PRST 형태 후보에서 검증 가능하게 만들었는가?** | **아니다.** Layer 2는 메타데이터 상 **테스트 $R^2 \approx -0.028$** 로 등록되어 있고 (`ENDPOINT_CONFIDENCE["pepmsnd_local_halflife_hours"]`), 코드 자체도 **“평균보다 나쁜 예측력” 신호 수준**을 전제한다. Layer 3 ADMET-AI는 **항상 decision 비권고**. |
| **도구 부재 문제를 줄였는가?** | 부분적으로. **환형+L-AA가 라우팅 가능한 경로에서는 “수치 하나를 믿는 것”보다 라벨링·격리 학습이라는 현실 검증 과제를 드러낸다.** D-AA 후보는 라우팅보다 enrichment에서 차단이라 **별 문제(침묵 결측)**가 남는다. |

**언어 교정안**

- 부적절: “3-Layer가 serum/ADMET의 **결정적 해법**이다.”  
- 보다 정확: “**라우팅·저신뢰 회귀·외삽 가드·문서 레지스트리를 묶어, 단일 블랙박스 신뢰를 깨는 다중 레이어 견제 뼈대**이다.” (**정확도 향상 프레임**이라기보다 **거버넌스 프레임**)

### 3.2 사용자가 적은 레이어별 근거 (서술 정합성 확인)

| 사용자 메모 | 검증 결과 |
|-----------|----------|
| Layer 2 $R^2=-0.028$ | `ENDPOINT_CONFIDENCE` 문자열 및 수치 필드 존재. |
| Layer 3 ADMET=1.00이 “즉각 독성”이 아니라 외삽 아티팩트일 수 있다 | 저장소에서 PRST 재검증·OOD 논의와 정합 (`MEETING_PREP_2026-05-28.md` Q7 등). 코드상 pepADMET + ADMET-AI는 **물리적으로 다른 두 모델**이므로 같은 숫자로 해석하면 안 된다(#117 의도 자체가 이 분리 명시). |

### 3.3 도입 전후 (개념적 비교 — 코드 기준)

| 측면 | 이전 패턴(enrichment 초기 패턴 포함) | 3-Layer 모듈이 추가된 뒤 |
|------|--------------------------------------|---------------------------|
| 단일 수치 과신 | pepADMET / Plife Pred 스코어 하나로 순위 또는 gate 해석 가능한 위험 | **별 레이아웃 제공**: 회귀 `P4`, ADMET-AI `recommended_for_decision=False`, SS-bond OOD 가드(`check_pepadmet_applicability`의 `SS` 서브스트링 조건). |
| PRST 합성 의뢰서 | **여전히 pepADMET 1.00 + H-06 문장 중심** — 3-Layer 산출 필드는 문서에 없음 | 문서·코드 **불일치**: 발표용 narrative는 3-Layer를 말할 수 있으나 **의뢰서 산출 파이프라인은 구 경로**에 가깝다. |
| wet-lab | 문서상 이미 필수 | 가드가 **결측·저성능·외삽을 드러내**어 **실험 병행 논리가 강화**되는 방향(자동으로 실험을 대체하지는 못함). |

### 3.4 운영 비용 (정량은 환경 의존 — 질적만)

- **계산**: Layer 2는 subprocess + (옵션) GPU + conda env 마운트 → 후보마다 **수 초~2분 timeout** 설계(`layer2_ensemble.default timeout_sec=120`). ADMET-AI는 모델 로드 비용이 큼.
- **사람**: divergence·OOD·P4 경고는 **수동 triage 시간을 늘린다** — 대신 “조용한 잘못된 확신” 비용을 줄이는 트레이드오프.

### 3.5 한계·개선 경로 (사실과 연결)

1. **Layer 2 재학습 / 스택 정합**: 코드 주석이 말하듯 **DGL·2133d descriptor·공식 PepMSND와의 정합**이 미완. 실측 PK로 보정 전까지는 **순위도 신뢰하기 어려운 상태**라고 적시하는 것이 코드와 같다.
2. **OOD 가드 거짓 양성**: 학습 분포 안전 샘플이 Mahalanobis/MC 기준으로 OOD 처리될 수 있다 — 별도 **validation fold·임계 재보정** 없이는 차단 규칙으로 쓰기 위험.
3. **#117 미머지 브랜치**: divergence 경고 로직은 **있는 사람/브랜치와 없는 브랜치가 갈린다.** 운영 단일 진실 원하면 **main 통합 상태를 워크트리 HEAD와 동기화**해야 한다.

**6월 vs 이후**

- ~6월: **워크플로 불일치 정리**(enrichment가 3-layer를 부를 것인지, 아니면 문서만 조정할 것인지), **#117 포함 여부 합의**, 레이어2 학습 재현 스크립트·지표**(R² 회복 목표 명시 여부 포함)** 검토.
- 이후: D-AA 포함 PEPlife2 학습 재설계·실측 t½ 회귀·pepADMET 웹 차단 회피(법무·인프라) 등 **데이터 의존 과제**.

---

## 4. C. 결론 (한 단락)

3-Layer Ensemble은 **저장소에 존재하는 모듈·가드 레지스트리·회귀 실험의 집합**이며, A-02/A-03에서 식별된 **“D-AA·환형·DOTA에서 공개 예측기가 깨진다는 문제”를 수치적으로 ‘해결’하지는 않는다.** 대신 **`pepmsnd_local`의 저성능(음의 $R^2$)·ADMET-AI 외삽·pepADMET OOD 패턴 등을 이름 붙여 드러내고**(`recommended_for_decision=False`, `P4` 경고 문자열 포함), 사람이 왜 LC-MS/MS 혈청 측정·in vitro ADMET 패널이 필요한지를 **설명 가능한 형태로 남긴다.** 현재 브랜치 워킹 트리에서 **복합 스코어링 enrichment는 `run_routed_halflife`와 연결되지 않으며**,합성 의뢰서에도 **3-Layer 결과 필드가 직접 인쇄되지 않는다**는 점이 **발표 서사와 불일치 할 수 있는 코드 사실이다.** 따라서 타개책이라면 **운영 매뉴얼 및 데이터 파이프라인 정합**(어느 엔진이 canonical인지)·**후속 학습 과제**(Layer 2, pepADMET domain)까지 묶어, **예측 정확도를 대체하기보다 과학적 검증 책임을 회피하지 않도록 정렬했다**라고 적는 편이 낫다.

---

## 5. 코드 인용 (핵심 한 줄 근거)

**라우터가 Layer 1/3를 스텁으로 처리한다.**

```61:76:pipeline_local/scoring/ensemble_router.py
    """라우팅 후 Layer 2만 실구현; Layer 1/3은 스텁 메타만."""
    ...
    if route == "layer1_l_aa_ensemble_stub":
        base["ensemble_halflife_hours"] = None
        base["warnings"] = ["Layer 1 ensemble 미연결(스텁) — pipeline_local.scoring.layer1_ensemble 필요"]
        return base
```

(참고: 위 메시지 문자열과 달리, 동일 패키지에 `layer1_ensemble.py`는 실제 존재한다 → **네이밍/운영 상태가 구현보다 지연**되어 있다고 보는 편이 맞다.)

**Layer 3 ADMET-AI 결정 비권고 플래그**

```53:61:pipeline_local/scripts/predict_admet_ai_wrapper.py
    result: dict[str, Any] = {
        ...
        "recommended_for_decision": False,
        "warnings": [ADMET_AI_EXTRAPOLATION_WARNING],
```

**enrichment가 D-AA를 스킵한다**

```400:408:pipeline_local/scripts/composite_scorer.py
        if contains_d_amino_acid(seq):
            notes.append("D-AA detected; halflife/admet wrappers skipped")
            c.update({
                "halflife_confidence_grade": UNAVAILABLE_GRADE,
                "admet_confidence_grade": UNAVAILABLE_GRADE,
```

**Layer 2가 스스로 P4 저성능 경고를 붙인다**

```155:157:pipeline_local/scoring/layer2_ensemble.py
    out["warnings"].append(
        "저신뢰(P4): 실측 test R²<0 — screening 순위 전용, 절대 t½ 보고 금지"
    )
```

---

## 6. PRST 합성 의뢰서 vs 코드 파이프라인 — 정합성 매트릭스

| 항목 | PRST 의뢰서 (예: PRST-001) 표현 | 동일 명칭 코드 산출 | 일치 여부 |
|------|-------------------------------|-------------------|----------|
| 반감기 수치 근거 | `step08_stability.py`의 `predict_half_life`, HEURISTIC | `enrichment` 선택 시에는 `predict_halflife`; `run_routed_halflife`/Layer 블록 **비표기·비연결** | **부분 불일치** |
| 독성 1.00 | pepADMET local 재검증 결과 + OOD 문구 | 재훈련 GNN 출력과 문서 레지스트리와 정합 가능 | 의미상 일치 |
| 3-Layer 용어 | **용어 미사용** | 모듈·테스트 존재 | **문서 간 갭** |
| `recommended_for_decision` | 없음 | ADMET-AI wrapper에만 `False` 고정 | **서로 무관 레이어** |

이 표는 발표 준비 시 **한 슬라이드로 넣어도 될 분량의 “정직 표”**이다. 청자가 “그럼 5월에 뭐가 바뀌었나?”라고 묻거든, **합성 패키지 양식은 거의 고정되어 있고, 코드베이스에는 병렬로 더 엄격한 실험 모듈이 생긴 상태**라고 설명 가능하다.

---

## 7. narrative v1 대비 보완 후보 문장 (v2용 초안 아님, 사실 점검용)

`_workspace/release/meeting-2026-05-28-narrative.md`는 청자 친화 풀이에 무게가 실려 있다. 거기에서 **코드 검증 결과와 바로 연결 가능한 교정 포인트**만 나열한다.

1. **“main에 들어간 3-Layer가 enrichment를 모두 교체했다”**: 현재 브랜치 기준 **`enrich_candidates_from_wrappers`는 `run_routed_halflife`를 호출하지 않는다.**
2. **“통과해야 `recommended_for_decision=True`”**: 문자열 이름으로 보면 **ADMET-AI는 항상 False**이다. Gate-2는 **별도 사람 결정**(의뢰서 옵션 B) 영역이다.
3. **PR #112**: 깃 로그 상 `(#112)` 머지 식별자가 검색되지 않았으므로, 슬라이드에 번호만 박아 두었다면 **GitHub와 번호 교차확인**이 필요하다.

---

## 8. 참고 경로 요약표

| 구분 | 경로 |
|------|------|
| Layer 코드 | `pipeline_local/scoring/layer1_ensemble.py`, `layer2_ensemble.py`, `ensemble_router.py` |
| Enrichment 실경로 | `pipeline_local/scripts/composite_scorer.py` → `enrich_candidates_from_wrappers` |
| Layer 3 ADMET-AI wrapper | `pipeline_local/scripts/predict_admet_ai_wrapper.py` |
| 가드 레지스트리 | `pipeline_local/scripts/pharmacology_guards.py` (`ENDPOINT_CONFIDENCE`, `HEURISTIC_FUNCTION_DISCLAIMERS`, `check_pepadmet_applicability`) |
| 합성 의뢰서 | `runs_local/final_candidates/synthesis_orders/PRST-001.md` … `-004.md` |

---

## 부록 A. `ENDPOINT_CONFIDENCE`의 혈청·반감기 관련 키 목록 (실측)

동일 파일에 **동일 키 문자열이 두 번 정의된 항목**(예: `halflife_webmetabase_indirect`, `halflife_hle_regression_albumin` — 약 L954~ 이후 L1130~ 블록)이 있어, **파이썬 dict 해석상 후행 정의가 우선**한다. 분석·감사 목적의 키 스캔 시 이 점을 두고 읽어야 한다.

**혈청/반감기 인접 등록(발췌 순서, 약 L876~1028)**

1. `halflife_pepmsnd` — PepMSND 웹, 이진 출력, D-AA 미지원 표기  
2. `pepmsnd_local_halflife_hours` — 로컬 PEPlife2-GAT 회귀, **benchmark test R² 필드로 -0.028 기록**  
3. `halflife_plifepred` — PlifePred(1 계열) 논문 근거 문자열  
4. `halflife_plifepred2` — PlifePred2, **시간 아닌 랭킹 스코어** 경고  
5. `layer1_halflife_ensemble` — Layer 1 앙상블 메타데이터  
6. `halflife_webmetabase_indirect` — 간접 프로테아제 절단 지표  
7. `halflife_hle_regression_albumin` — Glassman 2024 회귀 서술, artefact 부재  
8. `halflife_ml_peptide` — ML_Peptide 불확실 표기  
9. `halflife_protparam` — N-end rule 혈청 불일치 강등(P4)  
10. `halflife_hlp` — 장(GI) 전용, 혈청 금지  
11. `halflife_peptiderranker` — 순위만, 반감기 아님  

(STATUS 문서가 말하는 “7개”와 정확히 일치하지 않으면 → **통계 시점 차이 또는 상위 카테고리 분류 차이**로 보면 된다.)

---

