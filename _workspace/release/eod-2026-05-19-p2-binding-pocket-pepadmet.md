# EOD 2026-05-19 — P2 sprint (binding-pocket-pepadmet)

**팀**: `binding-pocket-pepadmet` (lead session 80814a02)
**일자**: 2026-05-19, 활성 시각 12:14~12:38 KST (~24분)
**참여 팀원**: be-binding-api, fe-binding-ui, researcher, infra, reviewer

---

## 1. 최종 task 상태

| # | Task | 상태 | 산출물 |
|---|---|---|---|
| 1 | BE binding_pocket CRUD endpoint | ✅ completed | `402e526` + `49db836` (H-2 fix), 14 신규 + 126 회귀 PASS |
| 2 | FE BindingPocketEditor + `/binding-pocket` | ✅ completed | `4c868a6` (feat/p1-sprint-integration) → cherry-pick `eeae158` (main), 99/99 PASS |
| 3 | researcher pepADMET/PepMSND 재시도 | ✅ completed | `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md` |
| 4 | infra ENDPOINT_CONFIDENCE + wrapper + 벤치마크 | ✅ completed | 63/63 PASS, ENDPOINT_CONFIDENCE 11개, PlifePred2 SST14 벤치마크, `predict_halflife_pepmsnd.py` URL 정정 |
| 5 | reviewer E2E 통합 검증 + 회귀 | ✅ completed | 12:48 CONDITIONAL PASS — BE CRUD 5/5 200 OK, BE 152/152, FE 99/99, pipeline 592 PASS / 5 pre-existing fail, **신규 회귀 0건**. 보고서: `_workspace/release/p2-e2e-validation-2026-05-19.md` |

---

## 2. 주요 산출

### 코드 변경 (feat/p1-sprint-integration 브랜치, **main 미머지**)

```
402e526 feat(be): binding_pocket CRUD endpoint + tests
49db836 fix(be): box_size Pydantic validation (reviewer H-2)
4c868a6 feat(fe): BindingPocketEditor + /binding-pocket 라우트 + useBindingPocket 훅 (cherry-pick: eeae158 on main)
```

### 보고서 (5종)

- `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md` (researcher)
- `_workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md` (infra)
- `_workspace/release/p2-partial-review-2026-05-19.md` (reviewer 부분, **false positive 2건 포함**)
- `_workspace/release/p2-fe-review-2026-05-19.md` (reviewer FE PASS)
- `_workspace/44_reviewer-code_binding-pocket-router.md` (reviewer BE 리뷰)

### infra 핵심 결론

| 도구 | 등급 | 비고 |
|---|---|---|
| pepADMET | P1 | toxicity 가중치 로컬 사용 가능 (GitHub 45MB), 웹폼 IP 차단 추정 (HTTP 403) |
| PepMSND | P3 | 정식 URL `/static/service` HTTP 000, 로컬 학습 가능 (CUDA 12.1, DGL 2.4.0) |
| PlifePred2 | P4 | SST14 변이체 5종 완료, **출력 = ranking score (NOT hours)** |
| Octreotide pepADMET | HBN=84min | D-AA OOD 검증 (수동 A-02) |

### 벤치마크 파일

- `runs_local/pepmsnd_benchmark/sst14_bench_2026-05-19.json`
- `runs_local/pepadmet_benchmark/admet_bench_2026-05-19.json`

---

## 3. 🚨 SOD에서 처리 필요 (P2 마무리)

### 🔴 NEW CRITICAL — infra 코드 변경 4파일 손실

reviewer E2E 후 정합성 검증 결과, **infra task #4의 코드 변경이 git 어디에도 commit 안 됨 + working tree에서도 사라짐**:

```
# main HEAD + working tree 모두 클래스 부재
$ grep -c "class TestEndpointConfidenceExternalTools" pipeline_local/tests/test_pharmacology_guards.py
0
$ git show HEAD:pipeline_local/tests/test_pharmacology_guards.py | grep -c "class TestEndpointConfidenceExternalTools"
0
$ git log --all -S "TestEndpointConfidenceExternalTools" -- pipeline_local/tests/test_pharmacology_guards.py
# (어느 브랜치에도 없음)
```

**손실 추정 경로** (reflog 분석):
- 12:28 내가 본 working tree에 `class TestEndpointConfidenceExternalTools` 존재 + 63 collected = 실재
- 12:41 다른 세션이 EOD 커밋 `8e9ed23` (24 PR 머지 보고) 작성 과정에 working tree가 main HEAD로 reset/checkout 됨 → infra 변경 손실
- 12:48 reviewer E2E 시점에는 main HEAD = 39/39만 보임

**살아남은 산출물**:
- ✅ `_workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md` (infra 보고서)
- ✅ `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md` (researcher)
- ✅ `_workspace/release/p2-e2e-validation-2026-05-19.md` (reviewer E2E)
- ✅ `runs_local/pepmsnd_benchmark/sst14_bench_2026-05-19.json`
- ✅ `runs_local/pepadmet_benchmark/admet_bench_2026-05-19.json`

**손실된 코드 변경 (SOD에서 infra가 재실행 필요)**:
- `pipeline_local/scripts/pharmacology_guards.py` — ENDPOINT_CONFIDENCE 11개 + HEURISTIC 4개 + attach_confidence "warning" 패치
- `pipeline_local/tests/test_pharmacology_guards.py` — TestEndpointConfidenceExternalTools 24개 메서드
- `pipeline_local/scripts/predict_halflife_pepmsnd.py` — URL `/static/service` 정정 + V-01/V-02 반영
- `pipeline_local/scripts/predict_admet_pepadmet.py` — grade P2→P1 정정, D-AA=False 확정, 웹폼 엔드포인트 문서화

**SOD 복구 절차**: infra 보고서를 참고로 재실행 (보고서에 변경 내역 상세 기록) + 즉시 **commit + main 머지**. infra 본인 tmux pane 26에 working tree 잔존 가능성 확인.

---

### ✅ (해소) main 머지 누락

**12:39 be-binding-api가 cherry-pick으로 자체 해소** — `e83fda9` (49db836 → main).

```
$ git log --oneline main | head -2
e83fda9 fix(be): box_size Pydantic validation (reviewer H-2)
eeae158 feat(fe): BindingPocketEditor + /binding-pocket 라우트 + useBindingPocket 훅

$ grep "class BoxSize" backend/routers/binding_pocket.py
51:class BoxSize(BaseModel):  ✅

$ pytest backend/tests/test_binding_pocket_router.py -q
14 passed in 0.52s  ✅
```

선택 이유 (be-binding-api): `feat/p1-sprint-integration`에 타 팀 커밋 6개 섞여 있어 PR 전체 머지 시 충돌 위험. BE 전용 커밋만 cherry-pick.

**잔여 후속**: 원본 `402e526` (BE CRUD 원본)은 main에 없음 — 그러나 `e83fda9`가 동등 내용 포함 가능. SOD에서 `git show e83fda9 --stat` 확인 필요. 14/14 PASS이므로 기능적으로 문제 없음.

### reviewer E2E 미완료

- 12:32:58 idle 이후 6분 무응답
- 본인이 보낸 false positive 정정 메시지 3건 (worktree root cause + 8788 ready + E2E GO) 처리 결과 미보고
- SOD에서 reviewer 재기동 or 별도 dispatch 필요

### reviewer false positive 3건 (참조)

1. ~~"infra 62/62 PASS 허위"~~ — 실제 63 collected. reviewer가 worktree 잘못 본 것 (메인 vs `.worktrees/*`)
2. ~~"useExtractBindingPocket body 누락"~~ — 실제 `apiPostWithBody` 정상 사용
3. (FE 리뷰에서 자체 정정 완료)

향후 reviewer 검증 워크플로에 `pwd` 명시 + 다른 worktree 가능성 사전 체크 필수.

---

## 4. 사용자 결정 대기 사항

### V-05 (PepMSND 로컬 학습 착수 여부)

- 환경: CUDA 12.1, DGL 2.4.0, H100 NVL 사용 가능
- 데이터: PepMSND 635개 + D-AA 116개 (18.3%) — 로컬 학습 시 D-AA 분류기 재현 가능
- 결정 사항: GPU 할당 + 일정

### V-07 (pepADMET 저자 학술 문의)

- 연락: `jiedong@csu.edu.cn` (Prof. Jie Dong, CSU)
- 목적: 반감기 가중치 학술 취득 + 웹폼 IP 차단 협의
- 결정 사항: 연구책임자 승인 + 문의문 작성 주체

---

## 5. 인프라 상태 (EOD 시점)

### uvicorn 인스턴스

| PID | 포트 | cwd | 용도 |
|---|---|---|---|
| 62459 | 8787 | ai4sci-kaeri | **운영, 3시간+ 도킹 잡 자식 보호 중 (PID 810467, 813489)** |
| 2920956 | 8788 | ai4sci-kaeri | E2E 검증용 (본 세션에서 신규 띄움, PYTHONPATH 적용) |

- 8787 유지 (도킹 잡 진행 중)
- 8788 그대로 유지 (다음 세션에서 사용) 또는 사용 끝났으면 kill 2920956
- 로그: `/tmp/uvicorn_8788.log`

### FlexPepDock 도킹 잡 (진행 중)

- PID 813489 — SSTR1 9IK8 receptor, peptide `PQCKNFFWKTFTSC`, 10 cycles × 50 nstruct
- 3시간 20분+ 경과 (12:30 기준 03:20:22)
- 출력: `runs_local/flexpepdock_jobs/a707e6b6-2c48-4ae2-81f2-4ad2ff090102/ensemble/SSTR1/`

### vite dev

- PID 1360651 (5월 14일 가동, 보존)

---

## 6. 다음 세션 (SOD 2026-05-20) 권장 순서

0. **[CRITICAL] infra 코드 변경 4파일 복구** (보고서 §3 NEW CRITICAL 참조) — pharmacology_guards.py 외 3파일. infra 보고서 기반 재실행 + 즉시 commit. **다른 항목보다 우선**.
1. ~~be-binding-api 머지~~ → ✅ EOD 직후 12:39 해소 (`e83fda9`)
2. **uvicorn 8788 재기동** — 이미 부팅된 PID 2920956은 cherry-pick 전 코드 import. 새 BoxSize validation 적용 위해:
   ```bash
   kill 2920956
   cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
   PYTHONPATH=.:/home/dongjukim/Documents/workspace/repos/SST14-M_scr \
     nohup conda run --no-capture-output -n bio-tools \
     uvicorn backend.main:app --host 127.0.0.1 --port 8788 \
     > /tmp/uvicorn_8788.log 2>&1 &
   ```
3. ~~reviewer E2E~~ → ✅ 12:48 CONDITIONAL PASS 완료 (Action Items 4건은 후속 sprint)
4. **reviewer Action Items 처리** (후속 sprint):
   - [High] BE — `test_step05b_selectivity.py::TestBindingPocketInterface` 3개 테스트를 신 BE 스키마(`residue_ids`/`radius_angstrom`)에 맞게 업데이트
   - [Medium] BE — SSTR4 `VILRYAKMKTA` 공유 서명 제거 (4 pre-existing failures)
   - [Low] FE — `parseInt` 사전 검증 + `isError=true` fallback 테스트 추가
5. **V-05/V-07 사용자 결정 반영** (선택)
6. **PR 작성 + 머지** (P2 sprint closure)

---

*최초 작성: 2026-05-19 EOD by team-lead (binding-pocket-pepadmet)*
