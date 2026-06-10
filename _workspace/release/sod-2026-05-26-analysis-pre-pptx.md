# 분석 보고 — 회의 Action Items 대응 + RI 팀 요청 사항 (5/28 회의 PPTX 작성 전 정리)

> **목적**: 사용자 검토용 정리 보고. 자료 만들기 전 객관적 사실 + 갭 정직 노출 + 실험 계획 제시.
> **작성**: 2026-05-26 SOD, vram-pcap-dpep 세션
> **선행**: 4/6 회의록 (`AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`) + Action Items 마스터 인덱스 + 5/28 회의 준비 문서 + 5/21 EOD 5종
> **원칙**: 객관적 · 아첨 금지 · 갭/실패 정직 노출 · 증빙 없는 주장 금지

---

## §A. 회의 Action Items 대응 현황 — 9건 + A-08 삭제

### A-1. 완료 ✅ (5건)

| ID | 회의 요구 | 대응 PR/commit | 핵심 검증 | 한계 |
|---|---|---|---|---|
| **A-01** | SSTR1/3/4/5 위치 지정 도킹 좌표 + 재도킹 | PR #61 (10 files, +43K) | TM-align → cealign 대체, RMSD 2.77~3.13Å | 5종 정렬 데이터 있으나 실 결합 친화도 검증은 in silico만 |
| **A-04** | Top-K 후보 선정 복합 스코어링 체계 | PR #62 composite_scorer.py + Tier S/A/B/FAIL | 73 tests pass, Hard Cutoff + WSS + Pareto + Tier 분류 검증 | Hard Cutoff `admet_tox_max=0.3` vs PRST 재측 1.00 모순 (§E-3 참조) |
| **A-05** | SST14 레퍼런스 ΔG 기준선 | main `8e7e1cc` (직접 push), FlexPepDock n=10 | mean=553.857 REU, σ=4.024 (KPI σ<5 충족) | direct push (PR 우회) — 다른 세션 검증 회피 가능성 |
| **A-09** | 최종 후보 3-4개 + 합성 의뢰서 | PR #63 PRST-001~004 + `runs_local/final_candidates/synthesis_orders/` | Gate-2 진입 후보 4건 + 7개 필수 의뢰서 항목 | binary_toxicity=1.0 OOD artifact (§E-3) — Gate-2 진입 결정 보류 |
| **A-10** | SSTR3 도킹 에러 해결 | PR #60 SSTR3_8XIR chain | 24 tests pass, smoke ddg=-92.09 | 별건 SSTR4 VILRYAKMKTA BUG는 PR #72로 후속 해결 |

### A-2. 부분 완료 🟡 — 외부 의존/블로커 (4건)

| ID | 회의 요구 | 대응 | **HIGH 블로커 (회의 의사결정 요청)** |
|---|---|---|---|
| **A-02** | 혈청 반감기 예측 도구 비교 + 자체 학습 가능성 | wrapper 7종 비교 완료 (PR #103 D-AA SMILES utility 추가) | **D-AA 지원 도구 0개** (researcher 14종 탐색, WebMetabase는 간접 지원). 자체 ML 모델 (PEPlife2 + PepMSND) 진행 중 (PR #112 OPEN, ρ=0.571) |
| **A-03** | Fab-ADMET (=pepADMET) 정확도 + 자체 학습 | wrapper 등록, ENDPOINT_CONFIDENCE P1, OOD 가드 (PR #74/#108) | **HTTP 403** REST 자동화 차단, **로컬 GPL-3.0** 라이선스 — 법무 검토 필요. 로컬 GNN 재훈련 완료 (PR #113), **PRST max-min 0.217 간신히 분리** |
| **A-06** | 디퓨전 모델 기반 도킹 가속화 PoC | DiffPepDock 평가 → **NOT_RECOMMENDED** | SS bond (Cys3-Cys14) 처리 불가 — 본 시스템 적합성 부족. A-07과 묶임 |
| **A-07** | DGX/고성능 GPU 서버 견적 | 매트릭스 작성 (DGX H100 / B200 / 자체 빌드) | **외부 벤더 응답 대기** — 사용자 명시 외부 contact 금지로 본 세션 진행 불가 |

### A-3. 삭제 ❌ (1건)

- **A-08** 라이브러리 서버 마이그레이션 → 외부망 H100×8 서버 배포 완료 (PDF §2.3)

### 종합 진척률

- **9건 중 5건 ✅ 완료 (55.6%)**
- **9건 중 4건 🟡 부분 (44.4%)** — 외부 의존/블로커 잔존
- 5/28 회의에서 의사결정 요청 항목 4건 (A-02 D-AA, A-03 라이선스, A-06+A-07 GPU, A-07 견적)

---

## §B. PR 머지 매핑 — 본 sprint (4/6 회의 ~ 현재) 총 PR

### B-1. Action Items 직접 대응 PR (12건)
| Action | PR # | Commit |
|---|---|---|
| A-01 SSTR site-directed | #61 | (5/19) |
| A-04 composite_scorer | #62 | (5/19) |
| A-05 SST14 ref ΔG | direct main | `8e7e1cc` |
| A-09 PRST-001~004 합성 의뢰 | #63 | (5/19) |
| A-10 SSTR3 chain fix | #60 | (5/19) |
| A-02 D-AA SMILES utility | #103 | `ab4a011` |
| A-02/A-03 ENDPOINT_CONFIDENCE | #74 | `f2460e5` |
| A-03 pepADMET 가드 + 재훈련 | #108 #113 | (5/21) |
| A-03 HLE regression wrapper | #110 | (5/21) |
| A-02 pepMSND 재학습 | #112 | **OPEN** (ρ=0.571) |
| A-05 Rosetta gate align | #79 | (5/20) |
| A-09 Gate-2 의뢰서 옵션 B | #86 | (5/20) |

### B-2. Action Items 보조 PR — 시스템 안정화 (본 세션 vram-pcap-dpep) (12건)
| Category | PR | 효과 |
|---|---|---|
| LLM 인프라 | #89 #92 | vLLM Qwen3.5-35B-A3B + DeepSeek-R1 + per-agent + UX |
| Mol* 시각화 | #93 | 4 root cause fix |
| FlexPepDock | #94 #95 #96 #97 #98 | timeout/pool/orphan/경고/progress |
| Manual Selectivity | #99 #101 #107 | stub badge / status chips / 2-level 셀렉터 |
| BE | #102 #105 | Silo A 라우터 / PRST wetlab |
| FE | #106 | Candidate selector |
| Worker scale | #104 | Worker pool 2→4 |

### B-3. 다른 세션 PR (병행, 본 세션 외)
- #82 G-2 margin sign convention
- #109 selectivity silent fallback 제거 (mock 금지)
- #84 회의 D-7 prep Q&A

---

## §C. RI 팀 요청 사항 — 4건 (회의 의사결정 + 실험 협업)

### C-1. 회의에서 요청 (5/28 D-Day 안건)

| # | 요청 내용 | 근거 | 대안 |
|---|---|---|---|
| 1 | **A-02 D-AA 자체 학습 ML 모델 구축 승인** | 14종 도구 탐색 후 D-AA 지원 0개 (researcher 보고 `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md`) | PEPlife2 + PepMSND 결합 학습 (PR #112 OPEN, ρ=0.571 — ranking 신호 식별) |
| 2 | **A-03 pepADMET 로컬 GPL-3.0 라이선스 법무 검토** | GitHub 공개되어 있으나 GPL-3.0 → 우리 코드 영향 분석 필요 | 현재 로컬 재훈련 모델 사용 중 (PR #113), 법무 OK 시 OS 배포 가능 |
| 3 | **A-06 + A-07 GPU 인프라 의사결정** | DGX H100 / B200 / 자체 빌드 매트릭스 + 외부 벤더 응답 대기 | 사용자 명시 외부 contact 금지 → **RI 팀이 직접 견적 수집** |
| 4 | **A-09 PRST-001~004 합성 발주 결정** | binary_toxicity=1.0 OOD artifact (재훈련 후에도 PRST max-min 0.217 간신히 분리), Gate-2 진입 보류 | (a) 발주 진행 + 실험 측정 병행 / (b) OOD 추가 검증 후 결정 / (c) 신규 후보 탐색 |

### C-2. RI 팀 실험 협업 요구 사항 (in vitro 측정 필요)

| 항목 | 측정 대상 | 우선순위 | 본 세션 산출물 |
|---|---|---|---|
| **혈청 안정성 t½ 측정** | SST-14 (3 min baseline) + PRST-001~004 + cand03 | **HIGH** | PR #112 학습 결과 검증 위해 필수 |
| **Ki / IC50 결합 친화도** | SSTR2 + 5종 selectivity panel | **HIGH** | A-01 도킹 결과 검증, in silico-실측 상관 필요 |
| **세포독성 assay** | PRST-001~004 (pepADMET binary_toxicity=1.0 OOD) | **HIGH** | A-03 재훈련 모델 validation |
| **DOTA 킬레이션 + 방사 표지 yield** | PRST-001~004 + cand03 | MED | A-09 의뢰서에 명시된 항목 |
| **SS bond 안정성 + radiolysis** | Cys3-Cys14 보존 + Met/Phe/Tyr/Trp 산화 | MED | radiolysis_scorer 점수 검증 |

### C-3. RI 팀 의사결정 권한 사항 (본 세션이 처리 X)

| 항목 | 결정 사항 |
|---|---|
| 5월 회의 일자 확정 (`meeting_schedule.md` TBD) | RI 팀이 결정 |
| pepADMET 저자 contact (`pepadmet-author-inquiry-letter-2026-05-20-EN.md`) | 사용자 거부 → RI 팀이 직접 결정 |
| GPU 벤더 견적 수집 | 사용자 거부 → RI 팀이 직접 결정 |

---

## §D. 증빙/검증 자료 (객관적 사실, 디스크 + git)

### D-1. PR 머지 17건 (어제 5/21 EOD 기준 본 세션 누적)
- 머지 hash 확인: `git log origin/main 5b57481^..f72c48e` (5/21 09:00까지)
- 본 세션 머지: #89 #92 #93 #94 #95 #96 #97 #98 #99 #100 #101 #102 #103 #104 #105 #106 #107
- 회의 직접 대응 머지: #60 #61 #62 #63 + main `8e7e1cc` (A-01/A-04/A-05/A-09/A-10)

### D-2. 테스트 통과 (5/21 02:46 회귀 결과)
| Suite | PASS / Total |
|---|---|
| AG_src | 253/254 (1 fail + 8 errors 모두 pre-existing macOS 경로) |
| backend | **169/169 (100%)** |
| pipeline_local | **634/634 + 5 skip + 2 xfail (100%)** |
| FE vitest | 100/101 (1 fail은 어제부터) |

### D-3. 실 산출물 파일 (디스크에 존재)

| 항목 | 경로 | 크기/수 |
|---|---|---|
| PRST-001~004 의뢰서 | `runs_local/final_candidates/synthesis_orders/PRST-00{1-4}.md` | 4 파일 |
| Boltz 복합체 PDB | `data/somatostatin_receptor/SSTR2_SST14_complex_boltz_{1,2,3}.pdb` | 3 파일 (각 304KB) |
| FlexPepDock SSTR1 도킹 | `runs_local/flexpepdock_jobs/32e8cfe1-.../ensemble/SSTR1/docked_00{00-09}.pdb` | 10 파일 (각 1.6MB) |
| pepMSND 재훈련 weight | `_workspace/pepadmet_local/pepADMET/model/toxicity_retrained_2026-05-21.pth` | 60MB |
| pepMSND PEPlife2 학습 | `_workspace/pepmsnd_local/checkpoints/pepmsnd_peplife2_20260520_0723.pth` | 145KB |
| Layer 3 ADMET-AI | `_workspace/admet_ai_local/layer3_*_raw.json` | PRST 4 + Octreotide |
| EOD/SOD 보고서 | `_workspace/release/eod-2026-05-{19,20,21}*.md`, `sod-2026-05-{19,20,21,26}*.md` | 30+ 파일 |

### D-4. 검증 통과 (test 또는 sanity)
- PR #113 pepADMET 재훈련: Octreotide 0.132 / SST-14 0.402 / **PRST max-min 0.217** (A.A5Pd sanity PASS)
- PR #112 pepMSND 재학습: **Spearman ρ=0.571** (ranking 신호 식별)
- PR #93 Mol* fix: 4 root cause 진단 + 단위 테스트 신규
- PR #95 worker pool: 17 단위 테스트 + per-job fcntl.flock 검증

---

## §E. 갭/누락 (객관적, 부정적 사실 정직 노출)

### E-1. 사용된 자원의 한계
- **uvicorn 8787 6일+ 무중단**: PR #94/#95/#96/#97/#98/#104/#107 효과 미반영 (재시작 필요)
- **e36b362d FlexPepDock 잡**: 5/20 ~07:26 시작 → 5/26 현재 cancelling 40% (6일+ stuck)
- **Ollama GPU 0/1 좀비**: 179GB 점유 잔존 (5/20부터 미해결, NVIDIA reset 위험)

### E-2. 회의 Action Items 잔여 갭
- **A-02 D-AA**: 자체 학습 ρ=0.571 — ranking 신호만, 회귀 시간 예측 불가. **자료에 정직히 명시 필요**
- **A-03 OOD**: 재훈련 후에도 PRST max-min 0.217 — 4 후보 사실상 동일. **회의 Q&A 예상**
- **A-06+A-07**: DiffPepDock NOT_RECOMMENDED 결정 + GPU 견적 외부 의존
- **A-07 견적**: 외부 벤더 응답 없음 → 회의에서 RI 팀에 책임 이관 필요

### E-3. PRST-001~004 모순 (회의 Q&A 핵심)
- `composite_scorer.py admet_tox_max=0.3` Hard Cutoff
- `hard_cutoff_pass.csv` 모두 `True` 표시
- 동시에 `synthesis_orders/PRST-00x.md` + `pepadmet_local/PRST-candidates_revalidation_2026-05-20.md`에 **pepADMET 재측 `binary_toxicity=1.0`** 기록
- → CSV와 의뢰서가 **상반된 결과** 보유 — 어느 쪽 신뢰?

### E-4. action-items-closure 세션 발견 K-1/K-2 결함 (다른 세션 작업, 본 세션 미해결)
- **K-1**: `_build_pdb_index` 알파벳 정렬 버그 — `test_full_pipeline_20260402` ('t'>'p')가 본 sprint `prst_mutdock_20260521` 위 매칭 → cand_001 무시
- **K-2**: `_run_offtarget_pyrosetta(sstr2_complex_pdb, receptor_pdb, ...)` 시그니처에 candidate_pdb 없음 → off-target dock 가 baseline (SST-14) 만 사용 → **모든 후보 동일 결과 = selectivity 의미 무력화**
- PR #109 부분 fix (silent 0.0 제거) — K-1/K-2 본체 잔존
- **5/28 회의에서 이 부분 발견 시 답변 곤란** → 회의 전 closure 또는 회의에서 정직히 보고 결정

### E-5. 데이터 무결성 의문
- `prst_mutdock_20260521` SSTR2 위치 정확성: 5종 도킹 모두 SSTR2 baseline 사용했는지 검증 안 됨 (K-2 영향)
- HEURISTIC Ki nM 추정표 (`§ 5-SSTR`): in silico만, 실측 Ki 아님 → 자료에 명시 필요
- Layer 3 ADMET-AI 외삽: PRST max-min 0.217 보다 더 약한 분리 가능성

---

## §F. 자료 생성 전 필요 실험 (사용자 검토)

### F-1. 자료에 포함할 실험 (객관적 증빙 위해)

| # | 실험 | 시간 | 출력 |
|---|---|---|---|
| 1 | **모든 PR 머지 후 회귀 테스트 전체 재실행** | 5분 | 통과율 표 (D-2 시점) |
| 2 | **PRST-001~004 핵심 metric 표 생성** (Boltz ddG + selectivity + ADMET + pepADMET) | 10분 | 자료용 비교 표 |
| 3 | **Mol* 후보별 docked pose 시각화** (스크린샷 4 후보) | 15분 | 자료 슬라이드 |
| 4 | **A-02 pepMSND 재학습 결과 plot** (ρ=0.571 산점도, 실측 vs 예측) | 15분 | 자료 slide |
| 5 | **A-03 pepADMET 재훈련 결과 plot** (binary_toxicity, max-min 0.217 막대) | 15분 | 자료 slide |
| 6 | **5종 SSTR selectivity heatmap** (PRST 4 × SSTR 5 = 20 cells) | 10분 | 자료 slide |
| 7 | **K-1/K-2 결함 결과 정직 정리** (다른 세션 발견, 본 세션 명시) | 5분 | 자료 부록 |

### F-2. 실험에서 생성될 기록 (절대적 분석 위해)
- 각 실험별 `_workspace/release/experiment-2026-05-26-NN-<topic>.md` 파일
- 입력 파라미터 + 실행 명령 + 출력 결과 hash + 실측 데이터 + 분석 결론
- git commit 별도 (실험별 1 commit)

### F-3. 자료 생성 도구
- **/pptx 스킬**: PptxGenJS 기반 슬라이드 생성 (어제 PR #91 18 슬라이드 패턴 재사용)
- **matplotlib/Plotly**: 차트 (ρ=0.571 plot, max-min 0.217 plot, selectivity heatmap)
- **PyMOL render**: 분자 시각화 (Mol* 스크린샷 대안)
- **/codex** + **/cursor-agent**: 실험 코드 작성 + 분석 결과 정리 위임

---

## §G. 자료 구성 안 (사용자 검토)

### G-1. 슬라이드 구조 (~20~25 슬라이드 예상)

1. **표지**: SSTR2 펩타이드 디자인 — 4/6 회의 Action Items 진척 보고 (5/28 회의용)
2. **목차**: 9건 Action Items 진척률 (5✅/4🟡/1❌)
3. **A-01 완료**: 5종 도킹 + RMSD + 정렬 표 (§A-1)
4. **A-04 완료**: composite_scorer Tier 분류 + 73 tests pass
5. **A-05 완료**: SST14 ref ΔG mean=553.857 σ=4.024
6. **A-09 완료**: PRST-001~004 매트릭스 (§D-3 + §E-3 모순 정직 명시)
7. **A-10 완료**: SSTR3 chain fix + SSTR4 BUG 후속 fix
8. **A-02 부분**: 14종 도구 비교 + D-AA 0개 + 자체 ML (ρ=0.571 plot)
9. **A-03 부분**: pepADMET HTTP 403 + 로컬 재훈련 + max-min 0.217 plot
10. **A-06+A-07 부분**: DiffPepDock NOT_RECOMMENDED + GPU 매트릭스
11. **A-08 삭제**: 외부망 배포 완료
12. **RI 팀 요청 사항 4건** (§C-1)
13. **RI 팀 실험 협업 요구 5건** (§C-2)
14. **RI 팀 의사결정 권한 3건** (§C-3)
15. **시스템 안정화 12 PR** (본 세션 부속, §B-2)
16. **테스트 통과 표** (§D-2)
17. **갭/잔여 (정직 노출)** §E-1~E-5
18. **K-1/K-2 결함** (다른 세션 발견, 본 세션 명시) §E-4
19. **PRST 모순** (CSV vs 의뢰서) §E-3
20. **다음 sprint 계획**

### G-2. 실험으로 채울 슬라이드 (§F-1)
- 슬라이드 6 (PRST 매트릭스 — 실험 2 결과)
- 슬라이드 8 (ρ=0.571 plot — 실험 4)
- 슬라이드 9 (max-min 0.217 plot — 실험 5)
- 슬라이드 6 보조 (Mol* 시각화 — 실험 3)
- selectivity heatmap (실험 6)

---

## §H. 권장 진행 순서 (사용자 검토 후 결정)

1. **사용자 검토** (현 단계) — 본 보고서 + §F 실험 항목 + §G 슬라이드 구성 확인
2. **실험 수행** (§F-1 7개, ~75분) — 각 실험 기록 파일 작성
3. **자료 생성** (PptxGenJS — /codex + /cursor-agent 위임, ~60분)
4. **자료 검토** — 객관성 + 갭 명시 + 아첨 없음 확인
5. **회의 D-2 자료 final** — 5/26~5/27 사이 완료

총 ETA ~2-3시간 (실험 + 자료 생성).

---

## 한 줄 결론

**Action Items 9건 중 5건 완전 closure / 4건 부분 (외부 의존). RI 팀 요청 4건 + 실험 협업 5건 + 의사결정 3건 명확.** PRST-001~004 ADMET 1.00 모순 + K-1/K-2 selectivity 결함 + 외부 GPU 견적 부재가 회의에서 정직히 보고할 약점. 자체 학습 (pepMSND ρ=0.571, pepADMET max-min 0.217)은 ranking 신호만 — 회귀/절대값 보장 X (H-06 가드 명시 필수).

---

*최초 작성: 2026-05-26 SOD by team-lead (vram-pcap-dpep)*
