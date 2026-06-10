# Phase 4 통합 판정 및 5-1 리팩토링 플랜
**작성**: reviewer-science (라우터/통합 판정)  
**날짜**: 2026-05-27  
**입력**: reviewer-pharma (phase4-pharma-tech-limits-goals.md), reviewer-code (phase4-code-audit-refactor.md), reviewer-uiux (phase4-uiux-integration.md), narrative v3, 3layer-admet-serum-impact-analysis, phase2/3 smoke, be-p0-fix, demo-scenario  
**청자**: KAERI 생명공학 박사 + 가속기 박사 (5/28 회의 및 후속 팀)

---

## Section 1: 통합 판정 — 3 reviewer 결과의 일관성·충돌·누락

### 1.1 세 reviewer가 공통으로 식별한 항목 (일관성 확인)

아래 6개 항목은 세 reviewer가 독립적으로 동일 결론에 도달했으며, 이 점에서 신뢰도가 높다.

**① enrichment 경로와 3-Layer Ensemble의 분리**  
reviewer-pharma(§1-3), reviewer-code(§2 후속-1), reviewer-uiux(§7 결론 표)가 각자 다른 진입점에서 같은 사실을 확인했다. `enrich_candidates_from_wrappers`는 `run_routed_halflife`를 호출하지 않는다. 이 사실은 코드 직접 grep, narrative v3 §5.4, 3layer 분석 §2.2에서 교차 확인된다. 세 reviewer 사이 결론 차이: 없음.

**② PR #117 (ADMET divergence guard)의 main 미포함**  
reviewer-pharma(§5), reviewer-code(§2 후속-3), 3layer 분석(§2.5) 모두 e3a5413이 현재 브랜치 및 main 양쪽에 없다고 독립 확인했다. 이 PR의 머지 비용이 낮고(코드 변경 소규모) 효과가 명확하다는 점도 공통 평가다.

**③ D-AA 후보에 대한 혈청 반감기 예측 불가 (UNAVAILABLE)**  
reviewer-pharma(§1-1), reviewer-code(§2 A-02), 3layer 분석(§2.6)이 동일 코드 경로(composite_scorer.py:400-408)에서 D-AA 검출 시 halflife/admet wrapper 전체 스킵을 확인했다. pepmsnd_local R²=-0.028(초기), 재학습 후 0.022(seed 의존)로 의사결정 불가 상태도 공통 판정이다.

**④ ADMET binary_toxicity=1.00의 OOD 가능성**  
세 reviewer 모두 이 수치를 절대 독성 판정으로 해석하지 않는다는 점에서 일치한다. in vitro 실측(hemolysis, cytotoxicity)만이 OOD 아티팩트 여부를 확인할 수 있다는 결론도 공통이다.

**⑤ 5/28 시연 시 Report 버튼과 Benchmark 탭이 빈 화면 또는 에러를 반환**  
reviewer-uiux(§4 Step 2)와 reviewer-code(§3 후속-8)가 같은 사실을 확인했다. reviewer-pharma는 FE 상세를 다루지 않았으나 발표 위험으로 §4에서 간접 언급했다.

**⑥ 아티팩트 누적(worktree 77개, release 129개, 실험 런 61개)**  
reviewer-code가 직접 측정했고, reviewer-uiux는 Mol* 7XNA fallback과 contacts 하드코딩 등 FE 레벨 아티팩트를 별도 확인했다. 방향성: 즉시 정리 가능하고 위험이 없다.

### 1.2 reviewer 간 결론이 다른 항목 (충돌 + 판정)

**충돌 A: smoke test "more" button 실패의 원인 해석**  
- reviewer-code(§3 후속-7): "접근성 회귀 가능성"으로 분류  
- reviewer-uiux(§2.1, §3.1): "nav 설계 변경 후 테스트 미갱신"이며 접근성 회귀가 아님. 현재 NAV_ITEMS는 11개 탭 일렬 나열, "More" 드롭다운은 코드에 존재하지 않는다고 명시적 코드 확인.  

**판정**: reviewer-uiux의 분석이 더 구체적 근거(NAV_ITEMS 직접 확인, "More" 드롭다운 미존재 코드 확인)를 가진다. 접근성 회귀가 아니라 테스트 기대값 갱신 문제다. 수정 방향은 "테스트를 현재 nav 구조에 맞게 수정"이 우선이며, "More 드롭다운 구현"은 별도 P1 UX 작업이다.

**충돌 B: P0 우선순위 — orchestrator.py 리팩토링 시점**  
- reviewer-code(§3 C P0): pharmacology_guards.py 중복 키 2개, ensemble_router 주석, 문서 정리, FE smoke fix, BE stub 등록을 P0으로 분류. orchestrator.py 함수 분리는 P1.  
- reviewer-uiux: P0을 시연 직전 UX 수정(Report 버튼 비활성, Mol* fallback 레이블, Benchmark 에러 메시지 개선) 3건으로 정의.  

**판정**: 충돌이 아니라 기준 축이 다른 것이다. 코드 P0과 UX P0은 병렬로 진행 가능하다. 통합 P0 정의에서 양쪽 항목을 모두 포함한다. Section 3에서 통합 P0 작업 목록을 작성한다.

**충돌 C: 3-Layer Ensemble의 역할 서술 (narrative v3 §5 vs 코드 현실)**  
- reviewer-pharma: "3-Layer가 pipeline을 보호한다"는 서술이 코드와 다르다고 직접 지적  
- 3layer-admet-serum-impact-analysis §3.1: "해결책이 아니라 한계 노출 프레임"으로 명시  
- reviewer-code: 동일 결론  

**판정**: 세 소스가 모두 같은 방향이다. narrative v3 §5.4의 "3-Layer 모듈은 존재, 표준 enrichment 경로 미연결"이라는 서술이 코드 사실에 부합한다. 이 서술을 회의 발표에서 그대로 사용한다.

### 1.3 세 reviewer 누구도 다루지 않은 항목 (누락)

**누락 A: PR #11 (proposal/postmortem-r2r3-3path)의 구체적 내용과 머지 영향**  
reviewer-code는 "16일째 방치"로 분류했으나 R1~R7 통합 정정 진단의 내용이 무엇인지, 머지 시 어느 코드에 영향을 주는지는 다루지 않았다. 본 통합 판정에서 PR #11은 "머지 또는 명시적 폐기 결정"의 두 선택지만 있으므로 5/29 P0에 결정하도록 명시한다.

**누락 B: `.worktrees/` 로컬 31개의 브랜치 별 상태**  
어느 worktree가 활성 작업 중인지, 어느 것이 이미 main merge 완료인지에 대한 구체적 목록이 없다. 삭제 전 확인이 필요하다.

**누락 C: Silo A (NGC API 키 부재) 해소 일정**  
phase2 smoke §3.B에서 미실행 사실은 확인되었으나, NGC API 키 확보 방법·일정·비용에 대한 action item이 없다. 이번 회의 §7 의제에 포함되지 않았다.

**누락 D: UnifiedCandidate 스키마와 pipeline_local 산출물 스키마의 실제 필드 차이**  
reviewer-code는 "스키마가 다른 상태"라고 했지만 어느 필드가 어떻게 다른지 구체적으로 다루지 않았다. P2 integration/adapter.py 작업 전에 별도 감사가 필요하다.

---

## Section 2: 사용자 5가지 분석 항목별 종합 답변

### 2-1. 기술적 한계와 타개 방법

약리·생물 측면에서 핵심 한계는 두 개다. 첫째, D-AA·cyclic(SS bond)·DOTA 조합 후보에 대한 혈청 반감기와 ADMET 절대값이 현존 도구로 산출 불가능하다. 11종 ENDPOINT_CONFIDENCE 전수 조회에서 D-AA 지원 = True인 항목은 0개이고(halflife_webmetabase_indirect는 혈청 t½이 아님), Layer 2의 테스트 R²=-0.028로 순위 신호조차 불안정하다. ADMET binary_toxicity=1.00은 D-AA+cyclic+DOTA OOD 외삽 가능성이 높으며, in vitro 실측 없이는 아티팩트와 실제 독성을 구분할 수 없다. 둘째, DiffPepDock은 SS bond 처리 한계로 NOT_RECOMMENDED 판정이고, Boltz-2는 55개 후보 순차 처리에 1500초 초과로 파이프라인 완주가 불가능하다. 이 두 번째 한계는 A-07 GPU 견적과 Schrödinger 도입 여부에 직접 연결된다.

코드 측면의 한계는 enrichment 경로가 3-Layer를 호출하지 않는다는 사실이다. 이는 도구 정확도 문제가 아니라 파이프라인 연결 문제이며, 6월 회의 전까지 "어느 엔진이 canonical인가" 합의 후 1-2주 엔지니어링으로 해소 가능하다. UI/UX 측면에서는 Report 버튼, Benchmark 탭, ArchivesTopKSlider 세 곳이 BE endpoint 미구현 상태에서 에러 또는 빈 화면을 반환한다. 5/28 회의 발표에서 박사 청자에게 전달할 핵심 메시지는 narrative v3 §5.4와 정합하는 한 문장이다: "이 후보들의 ADMET과 혈청 반감기 수치는 절대값으로 읽을 수 없으며, PR #85의 3-Layer Ensemble 모듈은 이 한계를 해결하지 않고 수치와 경고 플래그로 드러내는 구조다."

타개 방법은 단기(1개월)와 중장기(3-6개월)로 나뉜다. 단기: wet-lab assay 의뢰서 작성(Ki assay + serum stability assay + hemolysis/cytotoxicity), PR #117 main 머지, canonical enrichment 경로 합의. 중장기: Schrödinger Desmond MD trajectory를 serum stability 대리지표로 활용(도입 승인 조건), Layer 2 재학습(실측 t½ 데이터 확보 후), pepADMET 저자 문의 및 법무 검토 결과 반영.

### 2-2. UI/UX 연동 문제

Phase 3 보고서 이후 P0-A(llm_benchmark import 실패로 인한 FastAPI 전체 차단) 및 P0-B(포트 false positive)는 be-p0-fix-2026-05-27로 해결되었다. 현재 미해소 연동 문제는 세 가지다. 첫째, `/api/archives/top-k` BE 라우터 없음 — `ArchivesTopKSlider.tsx:96`이 호출하며, ManualSelectivity와 SelectivityPage 양쪽에서 진입 즉시 에러 메시지를 표시한다. 둘째, `/api/candidate/{id}/report` BE 라우터 없음 — Report 버튼이 항상 활성화된 상태로 렌더링되고 클릭 시 브라우저 404를 받아 화면에 피드백이 없다. 셋째, Mol* 3D 구조 fallback — candidate.source 없으면 SSTR2 reference 7XNA만 표시되는데 화면에 이를 알리는 레이블이 없다.

Phase 3 보고서 대비 새로 확인된 사항은 네 가지다: Silo A 탭 비활성 미표시(A/B/A+B 모두 클릭 가능하지만 A는 데이터 없음), contacts 패널 하드코딩(K4/Asp137 등이 모든 후보에서 동일 표시), usePipelineStatus·useRunStatus 중복 폴링(/api/status 이중 호출), Nav 11개 탭이 1280px 이하에서 잘림 가능성. 이 네 항목은 Phase 3에서 식별되지 않았으나 시연 안정성에 영향을 줄 수 있다.

### 2-3. 향후 진행 가능한 목표

reviewer-pharma의 M+1~M+6 마일스톤과 reviewer-code의 P0~P3 일정을 정렬하면 다음과 같다.

| 시기 | 코드 목표 (reviewer-code) | 도메인 목표 (reviewer-pharma) |
|------|--------------------------|------------------------------|
| 5/29~6/4 (P0) | pharmacology_guards 중복 키 제거, FE smoke fix, BE endpoint stub, 문서 정리 | — |
| 6/4~7/1 (P1, M+1) | PR #117 merge, enrichment-3Layer 합의, orchestrator 1차 분리 | PRST-001 합성 발주 결정, pepADMET 법무, A-07 견적, Schrödinger 검토 승인 여부 |
| 7월~9월 (P2, M+2~M+3) | UnifiedCandidate 스키마 정합, Pydantic v2, Layer 2 재설계 착수 | enrichment 재실행으로 PRST-001~004 Tier 검증, PRST-001 합성 완료 예상, Ki assay 준비 |
| 9월~11월 (P3, M+4~M+6) | src/ 구조 재편(nice-to-have) | Ki assay·serum stability assay·hemolysis 결과 수령, 177Lu 표지 실험 준비(Gate-2 충족 시) |

M+3(2026-08)의 Ki assay 결과 수령 일정이 critical path이며, PRST-001 합성 발주 결정(M+1, 즉 5/28 회의 §7.1)이 지연될 경우 전체 wet-lab 일정이 연쇄 이동한다. 코드 P1의 enrichment-3Layer 연결 여부 합의(6월 회의 전)가 이 도메인 일정과 직접 연동된다.

### 2-4. 신규 목표 수립 + 액션리스트 충족 매트릭스

reviewer-code의 16건 충족 매트릭스를 그대로 채택한다.

| 항목 | 충족도 |
|------|--------|
| A-01 SSTR1/3/4/5 위치 지정 도킹 | 완전 |
| A-02 혈청 반감기 도구 비교 | 부분 (D-AA 지원 0개) |
| A-03 Fab-ADMET 검증 | 부분 (import 실패, REST 403) |
| A-04 복합 스코어링 체계 | 완전 (구조), 부분 (enrichment 경로 불일치) |
| A-05 SST14 ΔG 기준선 | 완전 |
| A-06 DiffPepDock PoC | 완전 (평가 완료, 도입 NOT_RECOMMENDED) |
| A-07 GPU 견적 | 부분 (외부 대기) |
| A-08 라이브러리 서버 마이그레이션 | N/A 삭제 |
| A-09 최종 후보 3~4개 도출 | 완전 |
| A-10 SSTR3 도킹 에러 해결 | 완전 |
| 후속-1: PR #85 3-Layer (enrichment 불연결) | 부분 |
| 후속-2: PR #90 binding pocket fix | 부분 |
| 후속-3: PR #117 ADMET divergence guard 미머지 | 미달 |
| 후속-4: PR #112 Layer 2 재학습 미머지 | 미달 |
| 후속-5: PR #11 16일째 방치 | 미달 |
| 후속-6: BE app import 실패 | 완전 (P0 해결됨) |
| 후속-7: FE smoke test 실패 1건 | 미달 |
| 후속-8: FE 미구현 endpoint 2건 | 미달 |

**신규 목표 (코드·도메인·UX 통합)**

신규 목표 1: **canonical enrichment 경로 확정** — "enrichment가 3-Layer를 호출하는가"를 6월 회의 전 팀 합의로 결정한다. Option A(연결)와 Option B(narrative 조정) 중 하나로 결정이 없으면 narrative와 코드 격차가 6월 회의 이후에도 지속된다. 의존: 회의 §7.5(6월 회의 기준 산출물 합의).

신규 목표 2: **wet-lab assay 패키지 담당 기관 확정** — Ki assay, serum stability assay, hemolysis/cytotoxicity, RCP 실험의 KAERI RI팀 내부 수행 vs CRO 외탁 결정. 이 결정이 없으면 M+3 일정 자체가 미정 상태다. 의존: 회의 §7.1(합성 발주 범위 결정) 직후.

신규 목표 3: **PR #117 main 머지 + 회귀 테스트 736 PASS 확인** — 발표 이후 5/29에 가능. PR 리뷰 비용이 낮다. 의존: 없음(회의 의사결정 불필요).

신규 목표 4: **FE UX P0 3건 수정** — Report 버튼 비활성, Mol* reference fallback 레이블, Benchmark 에러 메시지 개선. 합산 약 1~2시간 작업. 의존: 없음.

신규 목표 5: **PRST-001~004 sequence identity 다양성 해소 방안** — 현재 86~93%로 권장 80% 미달. 6월까지 다양성 증진 전략(서열 mutant pool 확장, Pareto front 재계산) 방안 확인. 의존: enrichment 경로 합의(신규 목표 1).

신규 목표 6: **Silo A NGC API 키 확보 또는 명시적 보류 결정** — Dual Silo 통합 검증이 영구 미완인 현 상태를 해소하려면 키 확보 또는 Silo A 운영 보류를 팀 합의로 결정해야 한다. 의존: 회의 참석자 확인.

신규 목표 7: **`_workspace/release/` 아카이브 정책 시행** — 30일 이상 미참조 파일을 `_workspace/archived/`로 이관. 129개 → 50개 이하 목표. 즉시 시행 가능, 위험 없음. 의존: 없음.

### 2-5. 신규 폴더 리팩토링 필요성

reviewer-code(§3 A~C)의 분석을 그대로 채택하되, 두 항목에 대해 강도를 조정한다.

**강화하는 부분**: `enrich_candidates_from_wrappers`의 3-Layer 미연결 문제가 단순 코드 기술부채가 아니라 발표 서술의 신뢰도 문제이기도 하다. 이는 P1에서 반드시 결론을 내야 하는 사항이며, 코드 연결을 선택하지 않는다면 narrative를 코드에 맞게 명시적으로 낮춰야 한다. 어느 쪽도 선택하지 않는 현 상태가 가장 나쁘다.

**완화하는 부분**: orchestrator.py 2,479 LOC 함수 분리를 P1에 전체 착수하는 것은 6월 회의 전 시기에 과부하가 걸린다. P1에서 1차 분리를 착수하되 1,200 LOC 이하 목표는 P2까지로 분산한다.

**유지**: reviewer-code의 `src/` 통합 구조 제안(신설 `src/pipeline_local/`, `src/pipelines/`, `src/integration/adapter.py`, `apps/ai4sci-kaeri/`)은 P2~P3 수준 목표다. 3개월 이내 전체 재구조화는 conda env, CI 스크립트, pyproject.toml 동시 갱신이 필요하므로 비현실적이다.

---

## Section 3: 5-1 리팩토링 플랜 (상세)

### 3.1 리팩토링 진행 여부 판단

**판정: Y (진행)**

리팩토링을 하지 않는 선택지의 비용은 세 가지 방향으로 증가한다. 첫째, narrative-code 격차가 좁혀지지 않으면 6월 회의에서도 동일한 설명이 반복된다. 발표마다 "enrichment가 3-Layer를 호출하는지"를 추가 설명해야 하고, 박사 청자의 "그럼 계산값을 신뢰할 수 있는가"라는 질문에 매번 구두로 답해야 한다. 둘째, orchestrator.py 2,479 LOC와 runner.py 1,621 LOC는 단일 파일 전체를 이해해야 버그 재현·영향 분석·테스트 추가가 가능하므로, 후속 개발 비용이 선형이 아니라 제곱으로 증가한다. 셋째, 아티팩트 누적(worktree 77개, release 129개, 실험 런 61개)은 다음 세션 컨텍스트 로드 비용과 신규 개발자 온보딩 비용을 가시화되지 않는 방식으로 계속 높인다.

반면 리팩토링 진행의 위험은 다음 두 개다. 첫째, 5/28 회의 직전 또는 직후 대규모 구조 변경은 발표 안정성을 위협한다. 이 위험은 5/28 이전 코드 수정을 금지하고, P0을 5/29 이후로 착수함으로써 관리한다. 둘째, orchestrator.py 함수 분리는 736 pytest PASS 유지가 전제되어야 하며, 한 번에 1,000 LOC 이상 이동하면 회귀 탐지가 어렵다. 이 위험은 PR 단위를 기능 단위 3~5개로 분리하고 매 PR 후 전체 테스트를 통과 확인하는 방식으로 관리한다.

### 3.2 리팩토링 범위 정의

**포함할 것**

(a) 단순 정리: `.worktrees/` 30일 이상 비활성 13개 이상 삭제, `_workspace/release/` archived/ 이관, `runs_local/` 14일 이전 실험 런 archived/ 이관. 즉시 가능, 위험 없음.

(b) Pydantic v2 마이그레이션: `pipelines/silo_b/src/` 기준 `@validator` 패턴 50건. P2 수준. silo_b 실행 시 경고 발생 여부를 P1에서 먼저 확인하고, 경고가 실제로 발생하면 P2로 착수 시점을 당긴다.

(c) enrichment ↔ 3-Layer 연결 (가장 critical): Option A(코드 연결)를 선택 시 `enrich_candidates_from_wrappers`에 `run_routed_halflife` 호출 추가. Layer 2 R²=-0.028 출력이 enrichment에 진입하므로 D-AA 분기 처리 로직 및 HEURISTIC 경고 자동 삽입이 함께 필요하다. Option B(narrative 조정)를 선택 시 발표 서술을 "모듈 존재, enrichment 통합 진행 중"으로 명시하고 6월 회의에서 재확인한다. 이 결정은 회의 §7.5와 연동되므로 본 플랜에서는 결정을 가정하지 않고 "회의 직후 5/29~6/4 사이에 팀 합의 후 착수"로 일정을 잡는다.

(d) 신규 폴더 구조: `src/` 통합(pipeline_local 이동, pipelines 이동, integration/ adapter.py 신설)은 P2~P3 수준. 5/29~7월 사이에는 경계만 명시적으로 확립하고 물리적 이동은 P2 이후.

(e) FE-BE 미구현 endpoint: `/api/archives/top-k` stub(P0), `/api/candidate/{id}/report` 구현 또는 FE 제거(P1).

(f) PR #117 머지(P0 직후), PR #112 머지 여부 합의(6월 회의 §7.5), PR #11 처리 결정(P0).

**제외할 것 (의도적 경계)**

- conda env 17개 → 10개 이하 목표: P1 감사 후 비활성 환경 확인 단계를 거쳐야 하며, bio-tools 단일 env 통합은 P3 이후로 남긴다.
- Layer 2 반감기 모델 전면 재설계: wet-lab t½ 실측 데이터 없이는 의미 없는 재학습이다. M+4(2026-09) 실측 데이터 수령 후 착수.
- DiffPepDock 재시도: GPU VRAM 120 GB 요구로 A-07 해결 전까지 착수 불가.
- pyrosetta_flow/runner.py 1,621 LOC 함수 분리: P2 작업. 현재 smoke 기준 동작하므로 발표 전 손대지 않는다.

### 3.3 단계별 플랜 (P0 ~ P3)

---

**P0 (2026-05-29 ~ 2026-06-04, 1주)**

목표: 발표 직후 즉시 실행 가능한 저위험·고가시성 항목을 모두 처리. 회의 시연 안정성을 잃지 않으면서 코드 기준선을 복원한다.

작업 항목:
1. [코드] `pharmacology_guards.py` 중복 키 2개 제거(halflife_webmetabase_indirect, halflife_hle_regression_albumin, L954~L1130) — codex exec — `python3 -m pytest pipeline_local/tests/ --tb=no -q` 736 PASS 확인
2. [코드] `ensemble_router.py` Layer 1/3 스텁 경고 메시지 명확화 (코드 주석: "Layer 1/3 미연결 — 스텁 상태, run_routed_halflife 미호출") — 직접 수정 — import test
3. [UX] `CandidatePage.tsx` Report `<a download>` → `<button disabled title="준비 중">` 전환 — codex exec — FE build PASS
4. [UX] `SelectivityExplorerPage.tsx` + `CandidatePage.tsx` Mol* fallback 레이블 추가 (`candidate pose 없음 — reference 7XNA 표시 중`) — codex exec — 시각 확인
5. [UX] `BenchmarkPage.tsx` 503 에러 메시지 개선 ("Benchmark 데이터 비활성 — llm_benchmark 모듈 별도 설치 필요") — 직접 수정 — 15분
6. [BE] `/api/archives/top-k` BE stub 등록(503 반환) — codex exec — `python3 -m pytest pipeline_local/tests/ --tb=no -q` 유지
7. [FE] `App.smoke.test.tsx:95` "more" button 기대를 현재 NAV_ITEMS(11개 NavLink) 구조에 맞게 수정 — codex exec — `npm test` 119 PASS
8. [정리] `_workspace/release/` 2026-04-30 이전 파일 → `_workspace/archived/` 이관 + 목록 기록 — 직접 — `git status` 확인
9. [정리] `runs_local/` `final_candidates/` 및 최근 14일 런 외 → `runs_local/archived/` 이관 — 직접 — 삭제 전 목록 백업
10. [PR] PR #11 처리 결정: 팀 합의 후 머지 또는 "Close with comment(R1~R7 진단 흡수 완료 또는 별도 이슈로 분리)" — 직접 — git status

산출물: 736 PASS 유지, FE build PASS, 119 smoke PASS (0 FAIL), `_workspace/archived/` 신설, PR #11 처리 완료.

검증 게이트:
```bash
python3 -m pytest pipeline_local/tests/ --tb=no -q          # 736 PASS, 0 ERROR
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri && npm run build  # 0 error
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri && npm test       # 119 PASS, 0 FAIL
curl http://localhost:8001/api/health                        # {"service":"ai4sci-kaeri-backend"} 포함
```

위험: 낮음. pharmacology_guards 중복 키는 파이썬 dict 후행 우선이므로 제거 전후 동작 동일. FE 수정 3건은 독립적이고 소규모.

회의 §7과의 연동: 없음(회의 결정 불필요). 5/28 회의 종료 직후 착수.

---

**P1 (2026-06-04 ~ 2026-07-01, 4주, 6월 회의 전후)**

목표: narrative-code 격차의 핵심 항목을 닫거나 명시적으로 분류. 6월 회의까지 "어느 엔진이 canonical인가" 판단 가능 상태로 만든다.

작업 항목:
1. [코드] PR #117 (ADMET divergence guard, e3a5413) main 머지 — git 직접 — 736 PASS + `composite_scorer.py` 통합 테스트 확인
2. [코드] enrichment-3Layer 연결 여부 팀 합의 (Option A 또는 B) — 회의 후 팀 결정 — 결정 문서화
3. [코드] (Option A 선택 시) `enrich_candidates_from_wrappers`에 `run_routed_halflife` 호출 추가 + D-AA HEURISTIC 경고 삽입 — engineer-backend — 736 PASS + enrichment 통합 테스트 신규 작성
4. [코드] (Option B 선택 시) narrative v3 §5.4 표 갱신: "enrichment-3Layer 연결: 진행 중, 6월 회의 결정 사항" 명시 — 직접 문서 수정
5. [코드] `pipeline_local/scripts/composite_scorer.py` vs `pipeline_local/scoring/composite_scorer.py` 동명 해소 (한쪽 명칭 변경 + import 갱신) — codex exec — 736 PASS
6. [코드] orchestrator.py 2,479 LOC → 1차 함수 분리 착수 (`_run_step_01_to_04` 블록 추출) — codex exec + reviewer-code — 매 PR 후 736 PASS
7. [FE/BE] `/api/candidate/{id}/report` 구현 또는 FE에서 버튼 조건부 비활성 유지(P0-1 연장)로 결정 — 팀 결정 후 codex exec
8. [정리] `.worktrees/` 30일 이상 비활성 목록 확인 + 비활성 13개 이상 삭제 — 직접 — `git worktree list` 확인
9. [정리] conda env 비활성 환경 감사 (17개 → 목표 10개 이하) — 직접 — `conda env list` 확인
10. [UX] Silo A/B/A+B 토글 비활성 Silo 시각적 표시 (A 탭 disabled + tooltip) — codex exec — FE build PASS
11. [PR] PR #112 (Layer 2 재학습) 머지 여부 합의 — 6월 회의 §7.5 연동 — 결정 문서화

산출물: PR #117 머지 완료, enrichment 경로 결정 문서, orchestrator.py 1차 분리 PR, 736 PASS 유지.

검증 게이트:
```bash
python3 -m pytest pipeline_local/tests/ --tb=no -q               # 736+ PASS
python3 -m pytest pipelines/silo_a/tests/ pipelines/silo_b/tests/ --tb=no -q  # 41 PASS
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri && npm run build
```

위험: 중간. enrichment-3Layer 연결(Option A)은 Layer 2 R²=-0.028 출력이 실제 enrichment에 진입하므로 D-AA 분기 처리와 HEURISTIC 경고 삽입을 함께 구현하지 않으면 결과 해석이 오도될 수 있다. 회귀 테스트를 먼저 확인하고 PR 단위를 작게 유지한다.

회의 §7과의 연동: §7.5(6월 회의 기준 산출물) 결정이 선행되어야 Option A/B 선택 가능. 6월 회의 날짜 전 2주 이내로 결정을 받아야 P1 완료 일정이 유지된다.

---

**P2 (2026-07-01 ~ 2026-09-01, 8주)**

목표: 파이프라인 구조적 분리를 명시적 경계로 전환. 도메인 모델 개선 착수 조건 확인.

작업 항목:
1. [코드] `pipelines/silo_b/src/` Pydantic v2 마이그레이션 (`@validator` → `@field_validator` 50건) — codex exec — silo_b 전체 테스트 PASS
2. [코드] `src/integration/adapter.py` 신설 — UnifiedCandidate ↔ pipeline_local 산출물 스키마 필드 차이 매핑 — engineer-backend — 스키마 변환 단위 테스트
3. [코드] orchestrator.py 2,479 LOC → 목표 1,200 LOC 이하 (P1 1차 분리 이후 계속) — codex exec — 736 PASS, 각 PR 단위 50~200 LOC 이동
4. [코드] `pyrosetta_flow/runner.py` 1,621 LOC 1차 함수 분리 착수 — engineer-backend
5. [도메인] Layer 2 반감기 모델 재학습 조건 확인 (M+4 실측 t½ 데이터 수령 여부) — reviewer-pharma — 데이터 있으면 착수, 없으면 보류 유지
6. [FE/BE] `/api/archives/top-k` 실 구현 (runs 데이터에서 top-k 파생) — engineer-backend — FE ArchivesTopKSlider 에러 해소
7. [UX] Candidate contacts 패널 하드코딩 제거 — BE에서 후보별 contact 데이터 반환 또는 "후보별 contact 계산 미지원" 표시 — codex exec
8. [정리] `src/` 디렉토리 신설 + `pipeline_local/`·`pipelines/` 물리적 이동 (CI 스크립트·pyproject.toml 동시 갱신) — engineer-infra — 전체 테스트 suite PASS

산출물: Pydantic v2 silo_b 완료, adapter.py 신설, orchestrator.py 1,200 LOC 이하, Layer 2 재학습 착수 여부 결정.

검증 게이트:
```bash
python3 -m pytest pipeline_local/tests/ --tb=no -q       # 736+ PASS
python3 -m pytest pipelines/silo_a/tests/ pipelines/silo_b/tests/ --tb=no -q  # 41+ PASS
python3 -m pytest src/integration/tests/ --tb=no -q       # 신규 스키마 테스트 PASS
```

위험: 높음. `src/` 물리적 이동은 conda env, CI 스크립트, pyproject.toml 동시 갱신이 필요하다. 이 항목은 P2 마지막 단계에서 전체 테스트가 안정화된 후 시도하며, 실패 시 revert 후 P3로 이동.

---

**P3 (2026-09 이후, 시점 미정)**

목표: 단일 통합 테스트 suite, 도메인 데이터 기반 모델 개선, 운영 자동화.

작업 항목:
1. silo_a + silo_b + pipeline_local + backend 통합 단일 pytest suite
2. conda env 통합 (bio-tools 단일 env 목표)
3. `_workspace/` 자동 아카이브 스크립트
4. Layer 2 재학습 완료 (wet-lab t½ 데이터 기반)
5. Storybook 컴포넌트 카탈로그
6. WCAG 대비 자동화 측정 (axe-core 통합)

산출물: 미정 (P2 완료 후 일정 재산정).

---

### 3.4 작업 분담 매트릭스

| 작업 | 담당 | 위임 방식 | 예상 시간 |
|------|------|----------|---------|
| pharmacology_guards 중복 키 제거 | engineer-backend | codex exec | 30분 |
| ensemble_router 주석 명확화 | engineer-backend | 직접 | 15분 |
| CandidatePage Report 버튼 비활성 | engineer-backend | codex exec | 30분 |
| Mol* fallback 레이블 | engineer-backend | codex exec | 45분 |
| Benchmark 에러 메시지 | engineer-backend | 직접 | 15분 |
| /api/archives/top-k stub | engineer-backend | codex exec | 1시간 |
| FE smoke test 수정 | engineer-backend | codex exec | 30분 |
| _workspace 아카이브 | 직접 | — | 30분 |
| runs_local 아카이브 | 직접 | — | 30분 |
| PR #11 처리 결정 | 팀 합의 | — | — |
| PR #117 main 머지 | 직접 | — | 30분 |
| enrichment-3Layer 연결 Option A | engineer-backend | codex exec + reviewer-code | 2~5일 |
| enrichment 경로 합의 Option B | 팀 결정 + 직접 문서 | — | 1시간 |
| composite_scorer 동명 해소 | engineer-backend | codex exec | 1시간 |
| orchestrator.py 1차 분리 | engineer-backend | codex exec + reviewer-code | 1~2주 |
| /api/candidate report 구현 | engineer-backend | codex exec | 4~8시간 |
| worktree 정리 | 직접 | — | 1시간 |
| conda env 감사 | 직접 | — | 1시간 |
| Pydantic v2 마이그레이션 | engineer-backend | codex exec | 1주 |
| UnifiedCandidate adapter.py | engineer-backend | 서브에이전트 | 1~2주 |
| pyrosetta_flow 분리 | engineer-backend | codex exec | 1~2주 |
| src/ 물리적 이동 | engineer-infra | 서브에이전트 | 1~2주 |

### 3.5 검증 게이트

각 P 종료 시 다음 명령이 모두 통과해야 다음 P로 진행한다.

```bash
# P0 ~ P3 공통 필수 게이트
python3 -m pytest pipeline_local/tests/ --tb=no -q
# 기대: 736 PASS (추가 작업으로 수 증가 가능), 0 ERROR

python3 -m pytest pipelines/silo_a/tests/ pipelines/silo_b/tests/ --tb=no -q
# 기대: 41 PASS

cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
npm run build
# 기대: 0 error

npm test
# P0 이후 기대: 119 PASS, 0 FAIL

# BE 부팅 검증 (be-p0-fix-2026-05-27 §11 기준)
uvicorn backend.main:app --host 0.0.0.0 --port 8001 &
sleep 3
curl http://localhost:8001/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'ai4sci-kaeri-backend' in d['service']"
curl http://localhost:8001/api/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['paths']) >= 72"
# 기대: assertion PASS
```

P2 이후 추가:
```bash
python3 -m pytest src/integration/tests/ --tb=no -q  # 신규 adapter.py 테스트
```

### 3.6 안전 장치

**main 브랜치 보호 정책**: 모든 리팩토링 작업은 feature 브랜치에서 진행하고 PR 리뷰 후 머지. P0~P1의 소규모 수정은 단일 PR로, orchestrator.py 함수 분리는 기능 단위 3~5 PR로 분리.

**5/28 회의 시연과의 충돌 방지**: 5/28 이전에는 코드 수정 금지. P0은 5/29 이후 착수. 5/27 오늘은 발표 자료 최종 확인만.

**회귀 발견 시 롤백 절차**:
```bash
# 현재 상태 기록 (P0 착수 전)
python3 -m pytest pipeline_local/tests/ --tb=no -q > /tmp/baseline_736.txt 2>&1
git worktree list > /tmp/worktree_baseline.txt
git log --oneline -5 > /tmp/commit_baseline.txt

# 회귀 발견 시
git revert HEAD  # 해당 커밋 revert (amend 금지)
python3 -m pytest pipeline_local/tests/ --tb=no -q  # 736 PASS 복원 확인
```

P2의 `src/` 물리적 이동 작업은 전용 feature 브랜치에서 진행하고, 전체 테스트 실패 시 revert 후 P3로 이동. `src/` 이동은 역할 경계 명시가 목적이며 기능 손실 없이 완료되어야 한다.

---

## Section 4: 5/28 회의 직후 본 세션의 즉시 후속 작업

### 4.1 회의 의사결정 결과 정리

회의 종료 후 30분 이내에 다음 의사결정 결과를 기록한다. 결정되지 않은 항목은 "미결정 — 담당자 X, 기한 Y"로 명시한다.

| 의사결정 항목 | 회의 §번호 | 결과 기록 필요 내용 |
|-------------|----------|------------------|
| PRST-001~004 합성 진행 범위 | §7.1 | 전체/PRST-001 우선/보류 + 실험 패키지 포함 여부 |
| pepADMET 법무 검토 및 저자 문의 | §7.2 | 착수 승인 여부 + 담당자 |
| A-07 GPU 견적 결과 | §7.3 | DGX H100/B200 결정 또는 보류 |
| Schrödinger 도입 검토 승인 | §7.4 | 6월까지 검토 진행 여부 Y/N |
| 6월 회의 기준 산출물 범위 | §7.5 | 합의된 6가지 산출물 목록 확정 |
| 실측 assay 패키지 담당 기관 | 신규 §7.6 | KAERI RI팀 내부 / CRO 외탁 / 미결정 |
| Silo A NGC API 키 확보 | 신규 §7.7 | 진행 여부 / 담당자 / 예산 |

### 4.2 P0 작업 착수 시점

회의 의사결정 결과 기록 완료 후, 5/29(목) 오전 P0 착수. Section 3.3 P0 10개 항목을 순서대로 진행하되 pharmacology_guards 중복 키 제거(작업 1)를 첫 번째로 처리하고 736 PASS 확인 후 다음 항목으로 이동.

PR #117 머지는 P0 검증 게이트 전부 통과 후 진행(5/29 오후 또는 5/30).

### 4.3 다음 회의(6월) 준비 마일스톤

P1 완료 조건(6월 회의 기준):
- PR #117 머지 완료 (736 PASS 유지)
- enrichment-3Layer 경로 합의 결과 문서화 + 코드 또는 narrative 반영
- orchestrator.py 1차 분리 PR 1개 이상 머지 완료
- PRST-001 합성 진행 상태 확인 (발주 후 리드타임 진행 중)
- pepADMET 법무 검토 진행 상태 보고
- Schrödinger 검토 결과 (라이센스 조건, 대상 모듈, GPU 연동 여부)
- A-07 GPU 견적 비교표 완성

6월 회의에서 "예측값과 실측값 불일치 보고"는 PRST-001 합성이 완료되고 Ki assay가 의뢰된 경우에만 가능하다. 합성 발주가 5/28에 결정되지 않으면 이 항목은 6월 회의 의제에서 제거해야 한다.

---

## 마지막 stdout 7줄

**3 reviewer 결과 일관성**: Partial — 핵심 사실(enrichment-3Layer 분리, PR #117 미머지, D-AA UNAVAILABLE)에서 High 일관성. "more" button 원인 해석에서 충돌 1건(reviewer-uiux 판단이 코드 직접 확인으로 더 신뢰도 높음). 누락 4건(PR #11 영향 범위, worktree 브랜치별 상태, Silo A NGC 키 일정, UnifiedCandidate 필드 차이).

**가장 결정적 종합 결론**: `enrich_candidates_from_wrappers`가 `run_routed_halflife`를 호출하지 않는 상태에서 "3-Layer가 pipeline을 보호한다"는 발표 서술은 코드 사실과 다르다. 6월 회의 전까지 Option A(코드 연결) 또는 Option B(narrative 명시적 조정) 중 하나를 선택하지 않으면 이 격차가 계속 누적되고 발표마다 구두 보완이 필요하다.

**5-1 리팩토링 진행 권고**: Y — narrative-code 격차가 방치되면 합성 의뢰서 해석 오류 리스크가 증가하고, orchestrator.py 2,479 LOC는 현재도 유지보수 병목이다. 단, 5/28 이전 코드 수정 금지, P0을 5/29 이후로 착수.

**P0~P3 총 일정**: P0 1주(5/29~6/4) + P1 4주(6/4~7/1) + P2 8주(7/1~9/1) + P3 시점 미정 = P0~P2 합산 약 13주.

**6월 회의 전까지 closure 가능한 작업 1개**: PR #117 (ADMET divergence guard, e3a5413) main 머지 — PR 리뷰 + 머지만 하면 되는 최저 비용 개선. 5/29 P0 게이트 통과 후 즉시 가능.

**narrative v3에 추가 반영 권장 항목 1개**: §5.4 "코드 실태" 표에 "FE Report 버튼 — BE /api/candidate/{id}/report 라우터 미존재, 클릭 시 화면 피드백 없음" 행 추가. 발표 시 박사 청자가 버튼을 누를 경우를 대비한 사전 발화 준비와 연동.

**사용자가 회의 후 첫 결정해야 할 작업 1개**: 실측 assay 패키지(Ki assay + serum stability assay + hemolysis/cytotoxicity)의 담당 기관 확정(KAERI RI팀 내부 vs CRO 외탁). 이 결정이 없으면 PRST-001 합성 발주가 결정되더라도 wet-lab 일정 전체가 미정 상태로 남는다.
