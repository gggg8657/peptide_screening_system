# Action Plan — 5/27 회의 (D-1) PPTX 자료 생성 + 결함 fix 시도

> **컨텍스트**: 5/27 회의 = **중간 점검**. 청자에게 진행 완료 사안의 캡쳐 + 그래프 + 도식 중심 자료.
> **선행**: `sod-2026-05-26-analysis-pre-pptx.md` (분석 보고서) + 사용자 5건 결정
> **사용자 결정**:
>   1. ✅ 추가 검토 + 디테일 + 객관적 타개 방법 제안 → 본 문서 §B
>   2. ✅ 진행 (실험 수행) → §C
>   3. ✅ 추가 사안 직접 검토 후 제안 → §D
>   4. ✅ 결함 자료 정직 포함 + fix 시도 예정 → §E
>   5. ✅ 5/27 회의 진행 (D-1 = **오늘 5/26**)
> **원칙**: 객관적 · 아첨 금지 · 캡쳐로 증빙 · 그래프/도식 우선 · fix 시도 기록 보존

---

## §A. 자료 캡쳐 + 그래프 우선 — 중간 점검 청자 기준

### A-1. 캡쳐 우선 영역 (실 진행 증빙)

| # | 캡쳐 대상 | 페이지/URL | 캡쳐 도구 |
|---|---|---|---|
| C1 | `/console` 실 잡 진행 상태 (bb6625b8 done / e36b362d cancelling) | http://localhost:5173/console | Chrome screenshot |
| C2 | `/selectivity-explorer` 후보 PDB 시각화 (PR #93 효과) | /selectivity-explorer | 후보 1→2→3 클릭 캡쳐 |
| C3 | `/candidate` 2-level 셀렉터 (PR #107) | /candidate?run_id=X&candidate=Y | header + Mol* 근처 |
| C4 | `/run/new` LLM dropdown 8 모델 optgroup (PR #92) | /run/new | dropdown 펼친 상태 |
| C5 | `/manual-selectivity` jobs list (PR #99 stub badge + PR #101 status chips + PR #97 amber 경고) | /manual-selectivity | nstruct>20 큰 잡 + done/failed 잡 혼합 |
| C6 | `/binding-pocket` BindingPocketEditor (PR #74 ENDPOINT_CONFIDENCE + Mol* fix) | /binding-pocket | SSTR2 좌표/잔기 |
| C7 | `/wetlab/orders` PRST-001~004 (PR #105 통합) | /wetlab/orders | 4 PRST 행 |
| C8 | `/benchmark` phase별 결과 | /benchmark | 빌드 + 기존 결과 |
| C9 | `/strategy-runner` ProteinMPNN 전략 | /strategy-runner | 전략 선택 UI |
| C10 | `/about` 시스템 description + architecture | /about | 갱신된 LLM 설명 |

→ 총 **10개 캡쳐**. 시스템 재시작 후 진행 (PR #98/#99/#101/#107 등 새 코드 반영).

### A-2. 그래프/도식 우선 영역

| # | 그래프 | 데이터 source | 생성 도구 |
|---|---|---|---|
| G1 | **Action Items 9건 진척 도넛 차트** (5✅/4🟡/1❌) | §B-1 본 문서 | matplotlib/Plotly |
| G2 | **PR 머지 timeline** (4/6 회의 ~ 5/26, 30+ PR) | git log | matplotlib timeline |
| G3 | **PRST-001~004 종합 매트릭스** (Boltz ddG / WSS / Tier / ADMET / 안정성) | `runs_local/final_candidates/*.csv` + 의뢰서 | pandas heatmap |
| G4 | **pepMSND 재학습 산점도** (실측 vs 예측, ρ=0.571) | PR #112 데이터 | matplotlib scatter |
| G5 | **pepADMET binary_toxicity 막대** (PRST-001~004 + Octreotide + SST-14) | PR #113 sanity 데이터 | matplotlib bar |
| G6 | **5종 SSTR selectivity heatmap** (PRST 4 × SSTR 5) | HEURISTIC Ki 추정표 | matplotlib heatmap |
| G7 | **Pipeline 시스템 아키텍처 도식** (Silo A/B + 3-Layer Ensemble) | 코드 + PR #85 | Mermaid 또는 draw.io |
| G8 | **테스트 통과율 막대** (AG_src/backend/pipeline/FE) | 5/21 02:46 회귀 | matplotlib bar |
| G9 | **K-1/K-2 결함 도식** (selectivity production 실패 흐름) | action-items EOD §2.3 | Mermaid sequence diagram |
| G10 | **RI 팀 요청 사항 분류 도식** (의사결정 4 / 실험 5 / 권한 3) | §C 본 문서 | Mermaid mindmap |
| G11 | **A-02 14종 도구 비교 매트릭스** (D-AA 지원, 신뢰도) | researcher 보고서 | pandas table heatmap |
| G12 | **A-03 pepADMET 라이선스 + HTTP 403 한계 도식** | A-03 정리 파일 | Mermaid flowchart |

→ 총 **12개 그래프/도식**. matplotlib/Plotly/Mermaid 사용. /codex로 코드 생성 위임.

---

## §B. 추가 검토 + 디테일 분석 + 객관적 타개 방법

### B-1. Action Items 9건 디테일 (회의 진척 표 강화)

| ID | 상태 | 검증 통과 항목 | 미해결/약점 | **타개 방법** |
|---|---|---|---|---|
| A-01 | ✅ | PR #61 5종 정렬, RMSD 2.77~3.13Å | 실 결합 친화도 측정 없음 | RI 팀 in vitro Ki 측정 협업 |
| A-02 | 🟡 | wrapper 14종 비교, PR #112 ρ=0.571 | D-AA 직접 지원 도구 0개 | (a) 자체 학습 acceptance (ranking only) + (b) RI 팀 실험 측정 병행 |
| A-03 | 🟡 | PR #113 재훈련, OOD 검출 | HTTP 403 + PRST max-min 0.217 | (a) GPL 법무 검토 후 로컬 OS / (b) RI 팀 in vitro 독성 assay 병행 |
| A-04 | ✅ | PR #62 Tier S/A/B/FAIL, 73 tests | admet_tox_max=0.3 vs PRST 1.00 모순 | composite_scorer 가드 강화 (`§E-3 fix 시도`) |
| A-05 | ✅ | mean=553.857 σ=4.024 (n=10) | direct main push (PR 우회) | 회의 후 PR로 재커밋 (감사 추적) |
| A-06 | 🟡 | DiffPepDock NOT_RECOMMENDED 결정 | SS bond 처리 불가 | RFdiffusion + Boltz 조합 유지 (이미 작동) |
| A-07 | 🟡 | DGX/B200/자체 빌드 매트릭스 작성 | 외부 견적 무응답 | **RI 팀 직접 견적 수집** (사용자 명시 contact 금지) |
| A-08 | ❌ | 외부망 H100×8 배포 완료 | — | 삭제 |
| A-09 | ✅ | PR #63 PRST-001~004 의뢰서 | binary_toxicity=1.0 OOD | (a) 발주 진행 + 실험 병행 / (b) OOD 추가 검증 / (c) 신규 후보 |
| A-10 | ✅ | PR #60 chain fix + SSTR4 BUG 후속 | — | — |

### B-2. 객관적 타개 방법 — 회의에서 사용자 결정 요청

| 결정 항목 | Option A | Option B | 권장 |
|---|---|---|---|
| **A-02 D-AA 자체 ML 수용** | ρ=0.571 ranking만 사용 + 실험 병행 | 시간 더 투자 (절대값 학습 시도) | **A** — ranking 으로도 1차 triage 가능 |
| **A-03 pepADMET 로컬 GPL** | 법무 OK → 로컬 OS 사용 | OS 못 함 → 외부 도구 의존 | 법무 OK 시 **A** (재훈련 모델 활용) |
| **A-09 PRST 합성 발주** | 발주 진행 + 실험 측정 병행 | OOD 추가 검증 후 결정 | **A** — 실측 없이 OOD 추가 검증 한계 (악순환) |
| **A-07 GPU 인프라** | DGX H100 (안정성) | B200 (최신, 가격↑) | RI 팀 + 사용자 결정 |

### B-3. 시스템 검증 객관적 사실

| 항목 | 통과 | 미해결 |
|---|---|---|
| 단위 테스트 | backend 169/169, pipeline 634/634 | AG_src test_config macOS 경로 8 errors (pre-existing) |
| FE vitest | 100/101 | 1 fail (어제부터) |
| 본 세션 PR | 17건 머지 (#89~#107) | PR #114 EOD 미머지 |
| 회의 직접 PR | 10건 머지 (#60~#86) | — |
| 다른 세션 PR | 5건 (#82/#85/#108/#109/#110/#113) | — |
| 시스템 uvicorn | 6일+ 무중단 | 새 코드 (PR #98/#101/#107) 미반영 |

---

## §C. 진행 — 실험 수행 (자료 만들기 위한)

### C-1. 즉시 실행 실험 (60~90분 예상)

**E1. 시스템 재가동** (5분) — PR 17개 효과 활성화
- uvicorn kill + 재가동 (PYTHONPATH + V5-R4 lifespan)
- Worker pool 4 가동 (start_flexpepdock_workers.sh)
- 검증: ss + curl /api/health

**E2. PRST-001~004 데이터 추출** (15분) — G3/G5 그래프
- `runs_local/final_candidates/*.csv` 읽기
- `pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` 파싱
- pandas DataFrame + matplotlib heatmap

**E3. pepMSND 산점도 데이터** (15분) — G4 그래프
- PR #112 branch checkout → 학습 결과 데이터 위치
- 실측 vs 예측 산점도 + ρ=0.571 표시

**E4. pepADMET binary_toxicity 막대** (10분) — G5 그래프
- PR #113 sanity 데이터 (Octreotide 0.132 / SST-14 0.402 / PRST max-min 0.217)
- 막대 그래프 + max-min 차이 강조

**E5. UI 캡쳐 10건** (20분) — C1~C10
- vite + chrome headless 또는 사용자 직접 캡쳐
- 본 세션이 가이드만 제공 (브라우저 자동화 불안정)

**E6. K-1/K-2 결함 분석 자료** (10분) — G9 도식
- `action-items-closure EOD §2.3` 본문 인용
- Mermaid sequence diagram (selectivity production 흐름)
- 정직 명시 (회의 약점 노출)

**E7. 회귀 테스트 재실행** (5분) — G8 막대 데이터 (어제 5/21 결과는 stale)
- pytest 3 suites + npm test
- 통과율 막대 그래프

### C-2. 각 실험 기록 형식 (절대적 분석)
```
_workspace/release/experiment-2026-05-26-NN-<topic>.md
- 입력: 명령어 + 파일 경로 + 파라미터
- 실행 시각: ISO 8601
- 출력: stdout/stderr hash + 결과 파일 경로
- 검증: 회귀 0건 확인 또는 변경 식별
- 결론: 객관적 (성공/부분/실패), 아첨 없음
- git commit: experiment-NN-<topic>
```

---

## §D. 추가 사안 직접 검토 — 새 발견 가능성

### D-1. 본 세션 직접 검토할 추가 영역

| 영역 | 검토 방법 | 우선 |
|---|---|---|
| **시스템 16개 worktree 정리** | `git worktree list` + stale 정리 | LOW (기능 무관) |
| **e36b362d 잡 강제 종료** | kill -9 + status 갱신 | MED (UI 정리) |
| **5/21 EOD 5개 보고서 정합성** | 다른 세션 EOD와 중복 검증 | LOW (어제 §6에서 정리) |
| **PR #112 (pepMSND 재학습) 결과 검증** | branch checkout + 학습 plot 데이터 | HIGH (자료 핵심) |
| **PR #111 (PRST 매트릭스) 머지 가능성** | conflict 검증 | MED |
| **PR #114 (본 세션 EOD) 머지** | gh pr merge 114 | HIGH (감사 추적) |

### D-2. 회의 Q&A 예상 — 추가 검토 필요 사항

| 예상 Q | 답변 준비 |
|---|---|
| "PRST ADMET 1.00 이유?" | OOD artifact — Cys3-Cys14 SS bond 학습셋 부재. PR #108 가드 + PR #113 재훈련으로 max-min 0.217 분리 (간신히) |
| "Selectivity 5종 어떻게 측정?" | Boltz ddG 기반 HEURISTIC Ki nM 추정표 — 실측 아님. K-2 결함으로 실 SSTR2 baseline만 사용 가능성 (정직 명시) |
| "D-AA 도구 없는데 어떻게?" | 14종 탐색 후 0개 확인 → 자체 학습 PR #112 (ρ=0.571 ranking) + WebMetabase 간접 |
| "DiffPepDock 왜 안 함?" | SS bond 처리 불가 → SST-14 핵심 Cys3-Cys14 깨질 위험. RFdiffusion + Boltz 조합 유지 |
| "GPU 견적 안 받았나?" | 외부 contact 사용자 거부 → RI 팀 직접 견적 협업 권장 |

---

## §E. 결함 자료 정직 포함 + fix 시도 예정

### E-1. 자료에 정직 포함 (회의에서 노출할 약점)

| # | 결함 | 회의 슬라이드 위치 | 정직성 |
|---|---|---|---|
| F1 | **K-1/K-2 selectivity production 결함** | 별도 슬라이드 (G9 도식) | "다른 세션 발견, 본 세션 미해결" 명시 |
| F2 | **PRST CSV vs 의뢰서 ADMET 모순** | PRST 매트릭스 슬라이드 (G3) | 양쪽 데이터 보존, 회의 결정 요청 |
| F3 | **자체 학습 ranking only** (ρ=0.571, max-min 0.217) | pepMSND/pepADMET 슬라이드 (G4/G5) | 절대값 회귀 불가 명시 |
| F4 | **HEURISTIC Ki nM 추정표** | selectivity 슬라이드 (G6) | "in silico, 실측 아님" 워터마크 |
| F5 | **A-07 GPU 견적 부재** | A-07 슬라이드 | "외부 contact 거부 → RI 팀 책임" 명시 |
| F6 | **uvicorn 6일+ 무중단, 새 코드 미반영** | 시스템 슬라이드 | "회의 직전 재시작 권고" 명시 |

### E-2. 회의 전 fix 시도할 결함 (시간 허용 시)

| # | Fix 대상 | 시도 방법 | 시간 | 위험 |
|---|---|---|---|---|
| **K-1** | `_build_pdb_index` 알파벳 정렬 버그 | reverse=True 제거 또는 timestamp 우선 정렬 | 30분 | LOW (단위 테스트 가능) |
| **K-2** | `_run_offtarget_pyrosetta` candidate_pdb 인자 누락 | 함수 시그니처 + 호출부 갱신 | 60분 | MED (다른 세션 영역 — 충돌 위험) |
| **PRST 모순** | `hard_cutoff_pass` 재평가 (binary_toxicity=1.0 반영) | composite_scorer 가드 강화 | 30분 | LOW (테스트 가능) |
| **uvicorn 재시작** | kill + start_workers.sh | 5분 | MED (e36b362d 잡 손실) |

→ K-2는 다른 세션 영역. K-1 + PRST 모순 + uvicorn 재시작은 시도 가능. /codex 위임.

### E-3. fix 실패 시 폴백
- 자료에 fix 시도 자체를 정직 명시 ("시도했으나 시간 부족 / 결함 확정")
- 회의에서 RI 팀에 인계 (다음 sprint)

---

## §F. 5/27 회의 진행 (D-Day = 내일)

### F-1. 발표 구성 — 중간 점검 청자 기준 (~30-40분)

| 시간 | 슬라이드 | 내용 | 캡쳐/그래프 |
|---|---|---|---|
| 0~3분 | 1. 표지 + 목차 | 4/6 회의 9건 진척 (5✅/4🟡/1❌) | G1 도넛 |
| 3~10분 | 2-7. 완료 5건 (A-01/04/05/09/10) | 각 PR + 검증 + 캡쳐 | C2/C3/C4 + G2 |
| 10~20분 | 8-11. 부분 4건 (A-02/03/06+07) | 블로커 + 타개 방법 + 그래프 | G4 G5 G11 G12 |
| 20~25분 | 12-14. RI 팀 요청 사항 | 의사결정 4 / 실험 5 / 권한 3 | G10 mindmap |
| 25~28분 | 15. 시스템 PR 17건 | 본 세션 부속 + timeline | G2 timeline |
| 28~32분 | 16-19. 결함 정직 노출 | F1-F6 + fix 시도 결과 | G9 도식 |
| 32~38분 | 20-23. 캡쳐 자료 | C1-C10 UI 실 화면 | 캡쳐 |
| 38~40분 | 24. 다음 sprint + Q&A | — | — |

### F-2. 발표 자료 산출
- `_workspace/pptx/PRST_N_FM_MidCheckup_2026-05-27.pptx` 또는 `.js` (PptxGenJS)
- 슬라이드 ~25개
- PDF export 함께

### F-3. 작업 순서 (5/26 SOD ~ 5/27 회의 전)

1. **본 보고서 사용자 검토** (현 단계) — 5분
2. **시스템 재가동 + worker pool 4** (E1) — 5분
3. **PR #114 머지 + #111/#112 검토** (D-1) — 10분
4. **fix 시도 (K-1 + PRST 모순)** (E-2) — 60분 (codex 위임)
5. **그래프 12개 생성** (G1-G12) — 60분 (codex matplotlib + Mermaid)
6. **UI 캡쳐 10건** (C1-C10) — 30분 (사용자 + 본 세션 가이드)
7. **PPTX 생성** (PptxGenJS) — 60분 (codex 위임)
8. **자료 검토 + final** — 30분
9. **5/27 발표**

총 ETA ~4시간.

---

## §G. 실험 기록 + 자료 생성 워크플로

### G-1. 모든 실험 기록 보존
- 실험별 `_workspace/release/experiment-2026-05-26-NN-<topic>.md` 파일
- git commit 별도 (블록 단위)
- 본 PR로 머지 (감사 추적)

### G-2. 자료 생성 도구
- **PptxGenJS**: 슬라이드 (PR #91 패턴 재사용)
- **matplotlib**: G1/G2/G4/G5/G8 (단순 차트)
- **Plotly**: G3/G6/G11 (인터랙티브, PNG export)
- **Mermaid**: G7/G9/G10/G12 (도식, SVG → PNG)
- **PyMOL**: 분자 시각화 (필요 시, Mol* 스크린샷 대안)

### G-3. /codex + /cursor-agent 활용
- codex: matplotlib/Plotly 코드 생성 (G1-G8 각각 30~60s)
- cursor-agent: 분석 보고서 정리 + 자료 검토
- /pptx 스킬: 슬라이드 합성

---

## 한 줄 결론

**자료 = 중간 점검 청자용 캡쳐 10건 + 그래프 12건 + 슬라이드 ~25개**. 진행 완료 5건 정직 + 부분 4건 타개 방법 + RI 팀 요청 12건 + 결함 6건 정직 (fix 3건 시도 — K-1/PRST 모순/uvicorn 재시작). 모든 실험 기록 보존 + 객관적 분석.

---

*최초 작성: 2026-05-26 SOD by team-lead (vram-pcap-dpep)*
*검토 대기: 사용자 확인 후 §C 실험 + §E fix 시도 + 자료 생성 진행*
