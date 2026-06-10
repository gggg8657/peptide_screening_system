# 2026-04-06 Action Items — 진행 계획

> **소스**: `docs/meet_log/2026-04-06_action_items/prompts/A-*.md` (9건, A-08 누락)
> **현 상태**: 오늘 (2026-05-19) 본 세션 + 다른 세션 작업으로 일부 인프라 갖춰진 상태.
> **작성**: orchestrator

## 1. 9건 요약 + 분류

| ID | 제목 | 분류 | 위임 후보 | 의존성 | 추정 |
|----|------|------|----------|--------|------|
| A-01 | SSTR site-directed docking (포켓 좌표 + 정렬) | BE | engineer-backend | A-10 선행 (SSTR3 부분) | 2-3h |
| A-02 | 혈청 반감기 예측 도구 5종 비교 | research | researcher | 독립 | 1-2h |
| A-03 | Fab-ADMET 정확도 검증 + 자체 학습 가능성 | research | researcher + reviewer-pharma | 독립 | 1-2h |
| A-04 | 복합 스코어링 체계 설계·구현 | BE 큰 | engineer-backend | 독립 | 4-8h |
| A-05 | SST14 reference dG (도킹 n=10) | BE 실험 | engineer-backend | 독립 | 2-4h |
| A-06 | Diffusion docking PoC (DiffDock) | BE 큰 | engineer-backend | 독립 | 4-8h |
| A-07 | GPU infra 견적 자동화 | infra | engineer-infra | 독립 | 1h |
| A-09 | 최종 후보 3-4개 도출 + 합성 의뢰서 | review + 문서 | reviewer-pharma + 본 세션 | **A-04 선행** | 1-2h |
| A-10 | SSTR3_8XIR 도킹 fix | BE bug | codex 또는 engineer-backend | 독립 | 1-2h |

**A-08 누락** — prompts/ 디렉토리 + 원본 markdown 모두 부재. 사용자 확인 필요 (의도적 skip? 또는 A-08 추가 작업?)

## 2. 현재 기반 (오늘 작업으로 갖춰진 자산)

A-04 (composite scoring) — *이미 일부 기반*:
- `pipeline_local/scripts/pharmacology_guards.py` (Anti-Hallucination Guards)
- `pipeline_local/strategies/{blosum,esm_scan,proteinmpnn,dual_b1_b2}.py` (변이 strategy)
- A/B 실험 결과 (PR #58) — strategy별 메트릭 정의

A-05 (SST14 ref dG) — *이미 일부 기반*:
- PR #49 `pipeline_local/scripts/flexpep_dock.py` wrapper (PyRosetta 실 inference 활성화)
- `data/somatostatin_receptor/SSTR2_7XNA.pdb` 변환 완료
- BE `/api/flexpepdock/jobs` 큐 활용 가능

A-10 (SSTR3_8XIR 도킹 fix) — *현재 코드*:
- `pipeline_local/scripts/offtarget_dock.py`
- `pipeline_local/tests/test_offtarget_dock_boltz.py`
- 5/15 작업: SSTR2.cif → SSTR2.pdb 변환 패턴 (PR #49) 응용 가능

A-01 (SSTR 결합 포켓) — *부분 기반*:
- SSTR2 7XNA 보유. 나머지 SSTR1/3/4/5 PDB 필요 (A-10 선행)

A-09 (최종 후보) — A-04 직접 의존, 현재 미진행

## 3. 의존성 그래프

```
A-10 (SSTR3 fix) → A-01 (SSTR site-directed)
                ↘
                  병렬: A-02, A-03, A-07
                ↗
A-04 (composite scoring) → A-09 (최종 후보)
A-05 (SST14 ref dG)    ↗   (A-04에 입력)
A-06 (DiffDock PoC)   ↗
```

## 4. 3-Phase 실행 계획

### Phase 1 — 즉시 병렬 가능 (~3-4h, 본 세션 + 외부 위임)

| ID | 위임 | 사유 |
|----|------|------|
| **A-10** SSTR3 fix | codex (~1h) | 단일 PDB 전처리 버그, 작고 명확 |
| **A-02** 반감기 도구 5종 비교 | researcher (~1-2h) | 외부 자료 수집, 본 세션 토큰 절약 |
| **A-03** Fab-ADMET 검증 | researcher + reviewer-pharma (~2h 병렬) | 도구 조사 + 약리학 검증 |
| **A-07** GPU 견적 자동화 | engineer-infra (~1h) | 시스템 점검 + 문서 자동화 |

**Phase 1 끝나면 4건 진행, 6 PR 누적 가능.**

### Phase 2 — BE 큰 작업 (~10-20h, 다음 SOD부터)

| ID | 위임 | 사유 |
|----|------|------|
| **A-04** 복합 스코어링 | engineer-backend (4-8h) | 핵심 인프라, 신중한 설계 |
| **A-05** SST14 ref dG | engineer-backend (2-4h) | flexpep_dock wrapper 활용 |
| **A-06** DiffDock PoC | engineer-backend (4-8h) | 환경 설치 + PoC |

### Phase 3 — 의존 작업 (Phase 1+2 후)

| ID | 위임 | 사유 |
|----|------|------|
| **A-01** SSTR site-directed | engineer-backend (2-3h) | A-10 후 SSTR3 합류, 5개 receptor 정렬 |
| **A-09** 최종 후보 도출 + 합성 의뢰서 | reviewer-pharma + 본 세션 (1-2h) | A-04 결과 기반 선정 + 문서화 |

## 5. 사용자 결정 필요

1. **A-08 누락 확인** — 의도적 skip? 또는 추가 작업?
2. **오늘 Phase 1 4건 시작 여부** — 또는 EOD 마감 후 다음 SOD부터?
3. **A-04 우선순위** — A-04는 4-8h 큰 작업이지만 A-09의 선행 조건. 다음 SOD 1순위로 적합?
4. **A-06 DiffDock 적용 가치** — Boltz와 무엇이 다른가? 둘 다 사용 시 어느 게 default?

## 6. 추정 총 시간

- Phase 1 (병렬): ~3-4h (외부 위임 토큰 사용)
- Phase 2 (순차): ~10-20h
- Phase 3 (병렬): ~3-5h
- **합산: ~16-29h** (3-5 영업일)

오늘 안에 Phase 1 4건 완료 가능.
