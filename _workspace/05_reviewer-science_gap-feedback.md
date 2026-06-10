# Phase 4 — Gap Analysis & Integration Report

## 0. 메타

- 작성: 2026-05-11
- 작성자: reviewer-science (임시 라우터·통합 판정자)
- 라우팅 결정: **단일 도메인 한정 X — 4개 도메인 통합 검토** (reviewer-science 직접 판정)
- 입력: 01~04 (Phase 1+2), 06 (Phase 3 실험)
- 출력: 본 파일 + Phase 5 액션 목록

라우팅 근거: 본 modification_conflict 산출물은 (a) 코드 품질, (b) 합성 화학, (c) PK 정합성, (d) 실험·시스템 동작이라는 4축에서 동시에 평가되어야 하며, 각 전문 리뷰어(reviewer-code/-chemistry/-pharma)가 Phase 2에서 독립 산출한 결과를 본 라우터가 모순·갭 매트릭스로 통합한다.

---

## 1. 원래 목적 (의도)

| Goal | 출처 |
|------|------|
| G-1 modification 조합의 화학적·구조적 충돌을 **모두** 사전 차단 | 01 §의도 vs 구현 갭 |
| G-2 step08_stability.py(`_MODIFICATION_BONUS` + `predict_half_life`)와 정합성 유지 | 04 §step08 정합성 |
| G-3 C-01~C-06 6개 규칙 + 충분한 테스트 커버리지 | 01 §구현 규칙, §테스트 결과 |
| G-4 1차 문헌 출처를 모든 규칙에 부착 | 01 표 §구현 규칙 6개 |
| G-5 harness 사이클(Phase 1~7) 운영 검증 | 사이클 시방 (본 작업 자체) |

---

## 2. 실측 결과

| 항목 | 측정 |
|------|------|
| 구현 규칙 수 | 6 (C-01~C-06) |
| Phase 1 단위 테스트 | 20/20 PASS (0.09s) |
| Phase 3 conflict matrix | 12/12 PASS |
| Phase 3 pharmacology_guards 회귀 | 33/33 PASS (04 §사전 검증) |
| reviewer-code Critical | 2 (CR-1 silent except, CR-2 dead const) |
| reviewer-code 권장 리팩토링 | 4 (P1~P4) |
| reviewer-code 누락 테스트 | 6 건 |
| reviewer-chemistry 놓친 규칙 제안 | 4 핵심 (C-07~C-10) + 2 옵션 (C-11~C-12) |
| reviewer-chemistry severity 재검토 | 1 (C-04 WARNING vs ERROR) |
| reviewer-pharma step08 정합성 갭 | 3 (PEG 위치 가드 누락, substitution 가드 부재, 반감기 상한 캡 부재) |
| harness 라우팅 결함 | 1 (`modification` 키워드 매칭 우선순위 버그) |
| PyRosetta SS bond API | 미호환 (`ss_bond_score=null`, 외부 이슈) |
| PyRosetta minimization | 초기 3009.20 → 최소화 19.11 (정상 동작) |

---

## 3. 갭 매트릭스 (★ 핵심)

Impact (1–5) × Effort (1–5) — 수정 우선순위 = Impact / Effort (소수점 1자리, 높을수록 시급).

| 영역 | 의도 | 실측 | 갭 (정량) | Impact | Effort | 우선순위 |
|------|------|------|---------|:------:|:------:|:--------:|
| 코드 품질 — silent except | broad except 없음 / 예외 누출 시 호출자에 전달 | `except Exception` 1건 (L434–435), C-02 TypeError가 삼켜져 규칙 우회 (CR-1) | 5 | 1 | **5.0** |
| 코드 품질 — dead code | 미사용 상수 없음 | `_SST14_CYS_SS_POSITIONS` (L36) 미참조 (CR-2) | 2 | 1 | 2.0 |
| 코드 품질 — Conflict frozen | 반환 dataclass 불변 | `frozen=False`, `mods_involved`가 가변 List (P2) | 2 | 1 | 2.0 |
| 코드 품질 — `isinstance(pos, int)` bool 트랩 | 정수만 허용 | `isinstance(True, int)==True` 통과 (03 C-06 평가) | 2 | 1 | 2.0 |
| 화학 규칙 커버리지 | 모든 충돌 차단 (G-1) | 6/10 (C-07 DOTA, C-08 D-Cys×2, C-09 lactam+Nterm, C-10 substitution+d_amino 누락) | 4 | 3 | 1.3 |
| 화학 severity — C-04 | 정책 결정 필요 | WARNING 유지 중 (정책 미확정) | 3 | 1 | 3.0 |
| 화학 — _find_cys_pairs `>=4` 휴리스틱 | 일반 SS 식별 | conotoxin 단거리 SS 미검출 (SST-14 한정에선 무영향) | 1 | 2 | 0.5 |
| 약리학 정합성 — PEG 위치 가드 | step08과 일치 (G-2) | conflict checker에 PEG 위치 제약 부재 (`_MODIFICATION_BONUS[pegylation]=96h` over-prediction 가능) | 4 | 2 | 2.0 |
| 약리학 정합성 — substitution 가드 | step08과 일치 | substitution mod에 대한 가드 0건 (step08는 R/K 권장만 함) | 3 | 2 | 1.5 |
| 약리학 정합성 — 반감기 상한 캡 | 임상 상한(168h 세마글루타이드) 존중 | `predict_half_life`에 cap 없음 — 다중 mod 합산 시 240h 초과 가능 | 3 | 2 | 1.5 |
| 실험 동작 — conflict matrix | 100% PASS | 12/12 PASS | **0** | – | – |
| 실험 동작 — Duplicate cyclization 케이스 (06 케이스 7) | C-05 단독 발화 기대 | C-05 WARNING + C-06 ERROR 동시 발화 (position=0 입력 때문). `expected: "warning"`이나 ERROR도 발생 → "PASS" 처리 기준이 모호 | 2 | 2 | 1.0 |
| auto_dispatch 라우팅 | 키워드 정확 라우팅 | `modification` 키워드가 외부 CLI 키워드보다 우선 매칭 → `internal:reviewer-chemistry`로 잘못 라우팅 1건 | 4 | 2 | 2.0 |
| harness — PyRosetta SS API | SS bond 점수 산출 | `ss_bond_score=null` (외부 API 미호환, 본 코드 책임 외) | 2 | 4 | 0.5 |
| 테스트 커버리지 | 충분 (G-3) | 누락 6건: 비-int pos, pos=None, mod_type 누락, 빈 서열, C-01+C-02 동시, _find_cys_pairs 단위테스트 | 3 | 2 | 1.5 |

### 핵심 신호 (3개 리뷰어 + codex 교차 검증)

1. **CR-1 silent except**는 reviewer-code의 HIGH Critical로 단독 지적되었고, Phase 3 실험 케이스(06 케이스 7 "Duplicate cyclization" mods=[{cyclization, position=0}])에서 C-05 WARNING + C-06 ERROR가 동시 발화되어 *모순적 출력*을 만들었다는 우회 증거가 있다 — 즉, 규칙 간 순서·예외 전파 결함이 실험에도 잠재적으로 영향. **수정 우선순위 1위.**
2. **화학 규칙 6/10 커버리지**는 reviewer-chemistry 단독 신호이나, reviewer-pharma의 "step08 substitution/PEG 가드 부재"(2건)와 일치된 방향으로 부분적으로 교차 검증된다(C-07 DOTA는 두 리뷰어 모두 §검증 필요로 명시).
3. **C-04 severity**는 reviewer-chemistry가 WARNING→ERROR 격상 검토를 제기했고, reviewer-pharma가 "+48h 보너스 vs -24h cyclization 손실 = net 음" 정량 추정으로 보강. 두 도메인이 같은 방향을 가리키며 정책 결정 필요.

### 누락 테스트 6건 시급도 분류

| # | 케이스 | 시급도 | 근거 |
|---|--------|--------|------|
| 1 | 비-int position 문자열 | HIGH | CR-1 silent except 직접 증거 |
| 2 | position=None 명시 | MED | 스키마 계약 불명확 |
| 3 | mod_type 키 누락 | MED | 같음 |
| 4 | 빈 서열 | LOW | 어색 메시지 정도 |
| 5 | C-01+C-02 동시 | MED | 다중 규칙 발화 미검증 |
| 6 | `_find_cys_pairs` 단위 | LOW | 간접 검증 존재 |

---

## 4. Phase 5 수정 액션 목록 (우선순위 순)

| ID | 액션 | 책임 | 예상 효과 | Impact/Effort |
|----|------|------|---------|:-----:|
| **A-1** | `check_conflicts`의 broad `except Exception`을 좁은 타입(`(ValueError, TypeError)`)으로 제한 + `position` 비-int 시 C-06을 _RULES 첫 번째로 이동해 선행 차단 | engineer-backend (codex) | CR-1 해소, 규칙 우회 차단 | 5.0 |
| **A-2** | 누락 테스트 #1, #5 추가 (비-int pos, C-01+C-02 동시) | engineer-backend (codex) | A-1 회귀 차단 | 4.0 |
| **A-3** | C-04 severity 정책 결정 (WARNING 유지 + suggestion 강화 OR ERROR 격상) — reviewer-pharma의 "net 음 PK" 추정 근거로 PI 결정 요청 | reviewer-pharma + orchestrator | 약리 over-prediction/under-prediction 해소 | 3.0 |
| **A-4** | `auto_dispatch` 라우팅 우선순위 버그 수정 — 외부 CLI 키워드(codex/cursor-agent)를 도메인 키워드보다 먼저 매칭 | engineer-infra | 본 사이클 운영의 라우터 일관성 | 2.0 |
| **A-5** | `_MODIFICATION_BONUS[pegylation]`에 대응되는 conflict 규칙 C-07p (PEG 위치 제약) 추가 | engineer-backend | step08 정합성 갭 1건 해소 | 2.0 |
| **A-6** | dead const `_SST14_CYS_SS_POSITIONS` 제거 또는 C-04 fallback으로 사용 | engineer-backend | CR-2 해소, 가독성 | 2.0 |
| **A-7** | `Conflict` dataclass `frozen=True` + `mods_involved`를 `Tuple[int,...]`로 | engineer-backend | 외부 변이 차단 | 2.0 |
| **A-8** | `isinstance(pos, int) and not isinstance(pos, bool)` 가드 추가 | engineer-backend | bool 트랩 차단 | 2.0 |
| **A-9** | reviewer-chemistry 제안 C-07~C-10 4건 채택 (DOTA chelator 이중, D-Cys×2, lactam+Nterm, substitution+d_amino 동일 position) | engineer-backend | G-1 커버리지 6/10 → 10/10 | 1.3 |
| **A-10** | `predict_half_life` 상한 캡 `min(final_hl, 240h)` 도입 검토 (PI/reviewer-pharma 결정) | reviewer-pharma | 다중 mod over-prediction 차단 | 1.5 |
| **A-11** | substitution mod_type에 대한 가드(SS bond 위치 substitution 차단) 추가 | engineer-backend | step08 정합성 갭 1건 해소 | 1.5 |
| **A-12** | 누락 테스트 #2~#4, #6 추가 | engineer-backend | 테스트 커버리지 보강 | 1.0 |

Phase 5에서 **A-1~A-4 (HIGH/MED)** 를 차기 PR 1건에 묶고, **A-5~A-12** 는 후속 iteration으로 분리 권장. A-9의 화학 규칙 4건 추가는 step08 어휘 확장(`dota_conjugation`, `lactam_cyclization`)을 선행해야 하므로 별도 RFC 필요.

---

## 5. harness 어댑테이션 자체 발견 사항 (Phase 7 진화 입력)

다음 분기 회고용 §검증 필요 — 본 사이클을 운영하면서 발견한 harness 결함:

1. **auto_dispatch 키워드 매칭 우선순위 버그** (A-4와 동일 사항이지만 Phase 7 관점):
   - 증상: "modification" 키워드가 라우팅 테이블에서 `reviewer-chemistry`(도메인)에 매칭되어 외부 CLI 호출을 우회.
   - 원인 추정: 라우팅 규칙 평가 순서가 (도메인 키워드 → 외부 CLI 키워드)로 잡혀 있을 가능성. 외부 CLI(codex/cursor-agent)는 사용자가 명시적으로 호출하므로 우선되어야 함.
   - Phase 7 액션: `auto_dispatch` 매칭 규칙에 (a) 외부 CLI 명시 호출 검출 → 우선, (b) 도메인 키워드는 fallback으로 강등.

2. **`expected` 필드 모호성** (06 Phase 3 실험 스키마):
   - 06 케이스 7 "Duplicate cyclization" — `expected: "warning"`인데 C-05 WARNING + C-06 ERROR 동시 발화. 스키마가 단일 값("warning")이라 다중 발화 검증 어렵고, 그럼에도 `status: "PASS"`로 처리됨.
   - Phase 7 액션: `expected`를 `{errors: [...], warnings: [...]}` 구조로 확장, 또는 케이스 분리(고정 입력은 단일 규칙만 트리거하도록).

3. **PyRosetta SS bond API 비호환**:
   - `ss_bond_score=null` — 본 코드 외부 의존성이지만 사이클 실험 일부가 검증 불가 상태로 통과됨. Phase 7에서 실험 매트릭스에 "외부 의존 검증 차단" 마커 도입 권장.

4. **Phase 2 reviewer 3명 산출물의 §검증 필요 미해소**:
   - 04 §검증 필요 5건 (PEG-exenatide 수치, PEG 위치 가드, 반감기 cap, D-Cys net PK, substitution 가드)이 Phase 3 실험에서 별도 검증되지 않음. Phase 7 회고에서 "§검증 필요 → Phase 3 실험 매트릭스 자동 편입" 자동화 도입 권장.

5. **자기 인용·자료 신뢰도 미검증**:
   - reviewer-code §검증 필요 1번 — `_find_cys_pairs` L85 "Baker & Squire 2005 Chem Biol 12:103" 인용 미검증. Phase 7에서 reviewer-science 라우터가 인용 검증을 별도 단계로 분리 권장(researcher 호출).

---

## 6. 통합 판정

- **종합: CONDITIONAL PASS**

근거:
- (PASS 요소) 6개 규칙 모두 1차 문헌 출처 부착, Phase 1 20/20, Phase 3 12/12, pharmacology_guards 33/33 — 차단 회귀 없음. 의도된 동작은 검증됨 (G-3, G-4 충족).
- (CONDITIONAL 요소) reviewer-code CR-1 silent except는 *실측 우회 증거*를 가진 HIGH 결함이며, Phase 1 자기 진술의 G-1("모든 충돌 차단")과 직접 충돌한다 — Phase 5에서 해소 전 production 머지 권장 불가. 또한 화학 규칙 커버리지 6/10(G-1 부분 미달), step08 정합성 갭 3건(G-2 부분 미달)이 남아 있음.
- (도메인 일관성) 4개 도메인 간 모순은 없음. reviewer-chemistry의 C-04 ERROR 격상 제안과 reviewer-pharma의 "net 음 PK" 추정이 같은 방향이며, reviewer-code의 CR-1과 Phase 3 케이스 7의 비정상 동시 발화가 같은 결함을 가리킴 — 신호 일치.

- **Phase 5 진행 권고: YES** (조건부)

조건: A-1 (silent except + 규칙 순서) + A-2 (회귀 테스트) + A-4 (auto_dispatch 라우팅) 3건을 Phase 5 PR 단일 번들로 처리. A-3(C-04 정책)은 PI 결정 차단 가능성이 있어 Phase 5 진행과 병렬 진행. 나머지 A-5~A-12는 후속 iteration으로 분리.

---

## §검증 필요

1. **C-04 severity 정책** — PI/orchestrator 결정 (reviewer-pharma + reviewer-chemistry 양쪽이 격상 검토 권고했으나 의도적 SS 제거 케이스를 막지 않을 정책적 여지 존재).
2. **PEG-exenatide 96h 정확 수치** — step08 주석 인용 보강 필요 (04 §검증 필요 1).
3. **반감기 상한 cap (~240h)** — GLP-1 임상 사례 추가 검토 (04 §검증 필요 3).
4. **`Baker & Squire 2005 Chem Biol 12:103`** 실재성 — researcher 라우팅 권장 (02 §검증 필요 1).
5. **DOTA/chelator modification 어휘 확장** — step08 schema RFC 필요 (03 §검증 필요 2).
