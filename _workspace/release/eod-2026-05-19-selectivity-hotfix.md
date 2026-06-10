# EOD 2026-05-19 — Selectivity Hot Fix

**세션**: 본 세션 (orchestrator) — 다른 세션이 UI BE/FE 에서 selectivity 검증 중인데 "안 돈다" 신고. 본 세션은 진단 + 데이터 경로 hot fix 만 수행, 소스코드는 미수정 (다른 세션 작업 충돌 회피).

## 증상

UI 에서 selectivity 가 의미 있는 결과를 못 냄. 후속 호출로 확인한 실태:

- `GET /api/selectivity/receptors` → 5개 전부 `loaded: false, path: null, size_bytes: 0`
- `POST /api/selectivity/run` 은 시작되지만, 응답 `mode: "estimation"`, 점수가 매번 다른 `random.gauss(-5, 3)` 난수
- 그럼에도 `gate_pass: true`, `tier: 3` 로 후보가 통과되는 UX 함정

## 근본 원인

1. `backend/state.py:22` → `REPO_ROOT = ai4sci-kaeri/` (uvicorn CWD)
2. `backend/routers/selectivity.py:18` → `_DATA_DIR = REPO_ROOT / "data" / "somatostatin_receptor"`
3. 실제 데이터: 외부 레포 루트 `<repo>/data/somatostatin_receptor/` 에만 존재
4. 내부 경로 `ai4sci-kaeri/data/somatostatin_receptor` 는 **타 사용자(`helloworld`) 절대경로**를 가리키는 **깨진 심볼릭 링크**로 들어와 있었음 (mtime 2026-04-02, 출처 미상)
5. → `filepath.exists()` 모두 False → `_get_receptor_pdb()` 가 None 반환 → off-target 점수 분기에서 `random.gauss(...)` fallback 으로 빠짐 (`selectivity.py:257`)

## 적용한 hot fix

깨진 심링크 제거 후 외부 데이터를 그대로 **복사**:

```
rm AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor
cp -r data/somatostatin_receptor AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor
```

→ 13M, 23개 파일 (SSTR1~5 cif/pdb/aligned + SSTR2_SST14_complex_boltz_{1,2,3} + 메타데이터). 소스 변경 0, BE 재시작 불필요.

## 사후 검증

| 항목 | 결과 |
|---|---|
| `GET /api/selectivity/receptors` | **5/5 `loaded: true`** (sstr1 1773.5 KB, sstr2 495.9, sstr3 916.9, sstr4 964.4, sstr5 859.1) |
| `AG_src.pipeline.step05b_selectivity` import | OK (`bio-tools` 환경) |
| `_build_pdb_index` 자동 선택 run | `test_full_pipeline_20260402` (sorted reverse=True 알파벳 역순 1순위) |
| 그 run 의 baseline_refined.pdb | 존재 ✓ → sstr2_complex 채워짐 → production mode 진입 조건 충족 |
| 그 run 의 cand_*.pdb | 32개 (`iter_02/03`, `cand_001~008` 패턴) → cid 키 `001/1/var001` 모두 등록됨 |

## 미검증 (다음 세션이 UI 에서 확인)

1. **실제 도킹 1회**: `POST /run` 후 응답에 `mode: "production"` 으로 찍히는지. 후보당 ~120s×4 receptor ≈ 8분 소요라 본 세션에서 미실행
2. **FE 가 보내는 candidate_id 형식**: UI 가 `001` / `var001` / `cand_001` 중 어느 형태로 송신하는지 확인 필요. 안 맞으면 후보 단위로 estimation fallback 으로 빠짐 (전체 실패 아님 — 매칭 안 되는 후보만)

## ⚠ 재발 위험 — 정공 조치 필요

본 hot fix 작업 중 **깨진 심링크가 한 번 다시 복원되는 현상** 관측됨 (12:32 시점, 본 세션 cp 직후). 누군가/어떤 스크립트가 `ai4sci-kaeri/data/somatostatin_receptor` 를 `/home/helloworld/...` 절대경로 심링크로 자동 재생성하고 있음. 다음 부팅·다음 setup 호출에서 다시 깨질 가능성.

후속 권고 (별도 PR 로):

- (A) `selectivity.py:18` `_DATA_DIR` 후보 경로 확장 — 외부 레포 루트도 fallback 으로 검사
- (B) 또는 `state.py` 에 `OUTER_REPO_ROOT` 신설 + `SST_DATA_DIR` 환경변수 주입
- (C) 또는 root-cause: `helloworld` 절대경로 심링크를 만드는 스크립트 추적해서 제거
- (D) 가드: BE 기동 시 receptor 로딩 0/5 면 명시적 에러 로그 + UI 토스트 (estimation fallback 으로 침묵 통과 막기)

## 변경 파일

- 추가: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor/` (디렉토리, 23 파일, 13M, untracked)
- 삭제: 동일 위치의 깨진 심볼릭 링크 (git status ` D `)
- 소스 코드 변경: **없음**

## PR

미생성 — 데이터 디렉토리만 추가, 다른 세션이 같은 영역 작업 중이라 본 세션에서 자체 PR 안 만듦. 정공 조치(A~D) 가 결정되면 그때 묶어서 PR.
