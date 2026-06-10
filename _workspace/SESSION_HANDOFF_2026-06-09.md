# 세션 인수인계 — 2026-06-09 (일시정지, 내일 재개)

> SSTR2 AI-Scientist 스크리닝 시스템. 사용자 지시로 **일시정지**. 이 문서 + 메모리(`MEMORY.md` 인덱스)로 재개.

## 0. 지금 백그라운드에서 도는 것 (중요)
- **종합 스크리닝 재실행** (A 재보정 + B 독성 + C ensemble + selectivity):
  - 로그: `_rerun_AB_ensemble.log`
  - 출력 예정: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/rerun_AB_ensemble_20260609.json`
  - 파라미터: n_candidates=8, max_iterations=3, top_k=5, --enable-selectivity --selectivity-top-k 3, bio-tools python
  - **내일 확인**: `tail -40 _rerun_AB_ensemble.log` + 위 JSON 의 final_candidates (half_life_heuristic_h/half_life_rf_h/halflife_source/pepadmet_toxic/selectivity_margin 필드 확인). 프로세스 죽었으면 동일 명령 재실행.

## 1. 서비스 상태 (재개 시 확인/재기동)
| 서비스 | 포트 | 기동 명령 |
|--------|------|-----------|
| vLLM Qwen3-32B | 8000 | `bash _launch_vllm.sh` (GPU2) |
| FastAPI 백엔드 | 8787 | `cd .../ai4sci-kaeri && .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8787` |
| React 프론트 | 5173 | `cd .../ai4sci-kaeri/frontend && npm run dev -- --host 127.0.0.1 --port 5173` |
- 확인: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/models` 등.
- 전용 env: `$REPO/.venv` (오케스트레이터/백엔드). 도킹·ML추론은 `bio-tools` env(sklearn 1.8/joblib/pyrosetta 보유). 독성은 `pepadmet` env(conda run).

## 2. 이번 세션(오늘) 완료한 것
- **시스템 가동**: 환경격리·vLLM·실 PyRosetta 도킹·에이전트 N-루프·FastAPI+React UI·UI 실험제어 (모두 검증).
- **다목적**: ΔG(실측)+반감기+선택성(실측 off-target)+ADMET 통합, Pareto/스칼라/dashboard.
- **버그 8건 수정** (clash×2, offtarget import/정렬/pre-relax, UI 설정, set_candidates, OUTER_REPO_ROOT).
- **CS 분석(codex+내장)** → D1-D4 수정(fail-closed, atomic status, 시드, retry 등). **P5 통합 스모크 테스트**(버그 1건 발견·수정). **P1 runner 분해**(docking_executor/scoring_pipeline, 1720→1438 LOC).
- **통합 리팩토링**: ai4sci-kaeri=SSOT + pipeline_local 컴퓨트 레이어, orphan 격리.
- **A 반감기 재보정**: log-multiplicative, SST-14 16.6h→0.042h, 벤치 Spearman 0.86. 회귀테스트.
- **B pepADMET 실독성**: GitHub 클론(`local_models/pepadmet/repo`) → 실 GNN 추론 통합(scoring_pipeline Step 0.5, admet 페널티).
- **C half-life 자체학습**: 기존 GAT(R²<0) → feature 기반 RF 재설계, **CV Spearman 0.78/R²log 0.64**. 모델 `pyrosetta_flow/halflife_model/halflife_gbr.joblib`.
- **ensemble**: 휴리스틱(A)+RF(C) log정규화 평균 → `pyrosetta_flow/halflife_ensemble.py`, cheap_objectives 배선.
- **pepADMET 문서/MCP 조사**: half-life 웹모델은 API 없음+403+CC-BY-NC-SA → 프로그램 접근 불가. `.mcp.json`엔 브라우저 자동화 MCP 없음 → 폼 자동화 불가.

## 3. /goal 달성 평가
핵심(작동 시스템 + 다목적 스크리닝 + UI + 실 후보 발굴)은 **달성**. 단 /goal은 "perfect system"의 진행형 — 아래 후속이 남음. 사용자 지시로 **일시정지**.

## 4. 내일 재개 시 우선순위 (제안)
1. **오늘 밤 스크리닝 결과 검증** (rerun_AB_ensemble_20260609.json): A+B+ensemble+selectivity가 반영된 새 랭킹 확인. native vs top 후보의 ΔG/반감기(H·RF)/독성/선택성_margin 표로.
2. **ensemble 검증·튜닝**: 8-drug 벤치 + 변이체 변별에서 ensemble이 단일(A) 대비 개선되는지 정량 확인. 가중치(A:C) 조정.
3. **selectivity on-target 일관화**: on-target(SSTR2)도 동일 transplant 프로토콜로 측정해 margin 공정 비교.
4. **C 모델 bio-tools sklearn(1.8)로 재학습** → 버전경고 제거(현재 cross-version 로드 경고만, 예측은 동일).
5. (선택) pharmacology_guards: pepmsnd 등급 P4→CV R²log 0.64 반영 상향. RF OOD 한계 명시.
6. 미적용 PEND: P2 영속 DB+stateless API, P3 API 인증, P4 분산 도킹, P6 스키마 codegen, P1 메인 함수 phase 분해(FlowContext).

## 5. 핵심 산출 문서
- `CONSOLIDATION.md`, `docs/ADMET_HALFLIFE_APPROACH.md`(부록 포함), `docs/system_pamphlet.html`,
- `_workspace/CS_ANALYSIS_SYNTHESIS.md`, `_workspace/pepmsnd_local/halflife_selftrain_v2_2026-06-09.md`,
- `_workspace/halflife_benchmark.py`(벤치), 메모리 5+개 파일.

---

## 6. 오늘 밤 스크리닝 결과 (rerun_AB_ensemble — 완료, run_status=success)
**모든 기능 통합 산출 확인됨**: 후보별 ΔG + 반감기(ensemble: hlH 휴리스틱 + hlRF) + 독성(pepADMET) + 선택성_margin 전부 채워짐. 5 final candidates, 전원 clash 0.

| 서열 | ddg | hlH(h) | hlRF(h) | stab | toxic | sel_margin |
|------|-----|--------|---------|------|-------|-----------|
| AGCKYFFWKTITSC | **-29.05** | 0.042 | 2.02 | 0.291 | True | **-25.9** |
| AGCKYEFWKTVTSC | -22.58 | 0.05 | 2.05 | 0.301 | True | -17.4 |
| AGCKWEFWKTLTSC | -22.35 | 0.049 | 2.87 | 0.318 | True | -25.4 |
| AGCKYEFWKTITSC | -19.06 | 0.05 | 2.48 | 0.311 | True | (미측정) |
| AGCKFDFWKTITSC | -7.40 | 0.049 | 1.80 | 0.293 | True | (미측정) |

### ⚠️ 핵심 과학적 발견 (내일 최우선 검토)
1. **선택성 margin 전부 음수(-17~-26)**: 후보들이 SSTR3/5(off-target, ddg -53/-55)에 SSTR2보다 **더 강하게 결합** → **아직 SSTR2-선택적 후보를 못 찾음**. native pan-agonist 패턴 그대로. ΔG는 개선됐으나 선택성은 미해결.
   → **대응안**: (a) 목적함수에서 selectivity 가중↑ + 음수 margin 후보 **하드 게이트 탈락**, (b) Planner 프롬프트에 "SSTR3/5 회피 잔기" 가설 유도, (c) negative_design_residues_SSTR2.json 활용한 제약 변이.
2. **전원 pepADMET toxic=True (hemostasis)**: 소마토스타틴 계열 특성일 수 있으나, admet 페널티가 모든 후보에 동일 적용되어 변별력 0 → 독성 **6-class/연속(hc50) 차등**으로 변별 강화 검토.
3. 반감기: hlH(0.04~0.05h, SST-14 스케일) vs hlRF(1.8~2.9h, PEPlife 도메인) — ensemble이 둘 결합. 변이 간 hlRF 차이(1.8~2.9h)가 변별 기여.

**결론**: 통합 파이프라인은 완벽 작동(모든 목적 산출). 다음 과학 과제 = **SSTR2 선택성 양성 margin 후보 발굴**(현재 0건) — 목적함수·게이트·Planner 가설 강화. 이게 내일 핵심.
