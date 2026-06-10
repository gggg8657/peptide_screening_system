# 2026-03-27 진행 보고서

## 1. 오늘 완료된 작업

### Phase 0: Off-target Selectivity 모듈 (최우선) ✅
- SSTR1~5 실험 구조 CIF 등록 (9IK8, 7XNA, 8XIR, 7XMT, 8ZBJ)
- CIF/PDB 양방향 지원 (전 파이프라인)
- Selectivity API 5개 엔드포인트 구현
- PyRosetta FlexPepDock 도킹 통합
- WSM/MSM/SR 스코어링 + Tier 분류
- SelectivityPage 프론트엔드 (Radar + Heatmap)
- 모듈 테스트 통과 (14/15 PASS, 1 PARTIAL=설계의도)

### Phase 1.0: Blocking Fixes ✅
- LocalModelRunner 환경변수 (DGLBACKEND, TOKENIZERS) 추가
- subprocess.run → Popen+communicate (GPU 메모리 누수 방지)
- 절대경로 → 환경변수 AG_SRC_REPO
- RFdiffusion 파이프라인 호출 성공 확인

### Phase 1.0.3: ESMFold 배치 모드 ✅
- 128서열 개별 호출(~20분) → 배치 1회(~2분)
- 모델 1회 로드 + N개 연속 예측

### Phase 1.0.6~7: 이황화결합 + pLDDT ✅
- PyRosetta _try_form_disulfide() 추가
- HF transformers pLDDT 0~1 → 0~100 스케일 변환
- gate_thresholds pLDDT 기준 60으로 통일

### Phase 1.1~1.5: 전수 검증 ✅
- Backend API 17/17 PASS
- Frontend proxy PASS
- ESMFold 배치 PASS
- RFdiffusion PASS
- ESM-2 PASS (conda env 수정 후)
- CIF 로드 5/5 PASS
- DL 모델 wrapper 8/8 구문 PASS

## 2. 미완료 항목 (다음 세션)

### Phase 1.6: 파이프라인 3 iteration 실행
- Silo B 3 iter: 대기 (실행 준비 완료)
- Silo A 3 iter: 대기 (RFdiffusion 검증 완료, 실행 가능)
- Dual Mode: 미구현 (A/B 개별 실행 후 수동 비교로 대체)

### Phase 1.7: LLM 피드백 루프 검증
- Ollama qwen3:8b 연동 확인됨
- 실제 피드백 루프 (Planner→Critic→Reporter) 미검증

### Phase 1.8: 시스템 정합성 분석
- 미착수

### Phase 1.9: 테스트 코드 작성
- 미착수 (mock/real 분리 필요)

### Phase 2: LLM 테스트벤치
- 2.0 orchestrator 리팩토링 미착수
- 2.1 LLM config 선택 미착수
- 2.2 Agent flow config 미착수
- 2.3 Per-agent LLM 미착수

### Phase 3: 문서화
- 미착수

## 3. Git 커밋 이력

| 커밋 | 내용 |
|------|------|
| cb3619f | chore: gitignore + Claude 설정 |
| 7a01ae7 | feat: pipeline_local 전체 (48 files) |
| 7807af1 | fix: Frontend UX/a11y |
| b6544d4 | feat: SSTR1~5 CIF + selectivity + plan |
| 14cdd4f | docs: plan v3 |
| 54d64e2 | feat: CIF 호환 + blocking fixes |
| 6350078 | feat: Selectivity 모듈 |
| 51bb441 | fix: Phase 0 검증 버그 수정 |
| b436fc8 | fix: Phase 1 검증 버그 수정 6건 |

## 4. 서버 상태

- Conda 환경 9개: bio-tools, rfdiffusion, diffpepbuilder, pepadmet, openfold3, boltz, esmfold, genmol + base
- Ollama LLM 8개 (포트 11435): qwen3:8b/30b/32b/235b, deepseek-r1:70b, llama4:scout, bge-m3, nomic-embed-text
- Backend: pipeline_local (port 8787)
- Frontend: Vite (port 5173)
- GPU: 4×H100 NVL 96GB, CUDA_VISIBLE_DEVICES=2

## 5. 다음 세션 시작 시 할 일

1. `source ~/.zshrc` (환경변수 로드)
2. Backend 시작: `conda activate bio-tools && python -m pipeline_local.backend.main &`
3. Frontend 시작: `cd .../frontend && npm run dev &`
4. 20260327_plan.md 확인 후 Phase 1.6부터 재개
