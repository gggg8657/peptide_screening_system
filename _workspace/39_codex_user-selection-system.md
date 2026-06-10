# Task #39 — 사용자 취사선택 시스템 (Strategy mode/complex/variant 선택)

## 배경
PR #56 ProteinMPNNStrategy + #57 DualB1B2 완성. 사용자 결정 (5/19): "사용자가 시스템에서 mode/complex/variant 취사선택 가능하면 좋겠음".

## 의뢰
### 1. BE API (FastAPI)
신규 라우터 `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/strategies.py`:

```
GET  /api/strategies                       # 등록된 4 strategy 메타 (blosum, esm_scan, proteinmpnn, dual_b1_b2)
GET  /api/strategies/proteinmpnn/options   # mode 옵션 + 사용 가능 complex_pdb 리스트
POST /api/strategies/run                   # 사용자 명시 실행 (strategy, mode, config)
  body: { strategy: "proteinmpnn", mode: "peptide_only"|"receptor_context", complex_pdb?, max_variants, ... }
  resp: { job_id, eta_seconds }
GET  /api/strategies/runs/{job_id}         # 상태 + 진행률
GET  /api/strategies/runs/{job_id}/variants  # 생성된 variants list
POST /api/strategies/runs/{job_id}/select  # 사용자가 채택할 variants 선택
  body: { selected_variant_ids: [...], rejected_variant_ids: [...] }
GET  /api/strategies/runs/{job_id}/selected  # 채택된 variants only
```

### 2. FE 페이지
신규 `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/src/pages/StrategyRunnerPage.tsx`:
- Strategy 선택 (4종 라디오)
- ProteinMPNN 선택 시 mode toggle (peptide_only/receptor_context) + complex_pdb 드롭다운
- Config 입력 (max_variants, num_seq_per_target 등)
- Run 버튼 → 진행률
- 결과: variants list (각 row 채택/거부 체크박스)
- 채택된 variants → composite_scorer 입력 또는 wetlab order 생성

### 3. 라우팅
`App.tsx` NAV_ITEMS에 `/strategy-runner` 추가.

### 4. 검증
- TS 컴파일 0 에러
- BE smoke test (mock job)
- FE Vite HMR 정상

## 제약
- branch: `feat/user-selection-system`
- PR title: `feat: Strategy Runner — 사용자 mode/complex/variant 취사선택 시스템 (BE API + FE UI)`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 + smoke 결과 + 변경 파일 보고
