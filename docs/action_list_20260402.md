# 액션 리스트 대응 현황 — 2026-04-02

---

## 완료 ✅

| # | 항목 | 완료일 | 비고 |
|---|------|--------|------|
| 1 | NIM API → 로컬 GPU 마이그레이션 | 03-26 | pipeline_local/ 47파일, 원본 무변경 |
| 2 | 9개 conda 환경 구축 | 03-26 | bio-tools, rfdiffusion, esmfold, boltz, openfold3, diffpepbuilder, genmol, pepadmet, proteinmpnn |
| 3 | Ollama 8개 LLM 다운로드 | 03-26 | qwen3:8b~235b, deepseek-r1:70b, llama4:scout |
| 4 | SSTR1~5 실험 구조 CIF | 03-27 | cryo-EM/X-ray (9IK8, 7XNA, 8XIR, 7XMT, 8ZBJ) |
| 5 | Selectivity 모듈 | 03-27 | 5 API, Radar/Heatmap, WSM/MSM/SR |
| 6 | CIF/PDB 양방향 지원 | 03-27 | structure_io.py |
| 7 | ESMFold 배치 모드 | 03-27 | 128개 20분→70초 |
| 8 | 이황화결합 PyRosetta 형성 | 03-27 | _try_form_disulfide() |
| 9 | Boltz2 완전 로컬 | 03-30 | single-seq + no_kernels, ipTM=0.960 |
| 10 | 전수 검토 18건 이슈 | 03-31 | 3인 병렬 (backend/frontend/dual) |
| 11 | Round 1 CRITICAL 5건 | 03-31 | hotspot_res, 타입 통일, Boltz score, GPU 분배 |
| 12 | Round 2 HIGH 5건 | 03-31 | Silo B 통합, CIF→PDB, DiffPepBuilder 비활성화, UI 구조 |
| 13 | 듀얼 사일로 모드 | 03-31 | --dual CLI, A+B 순차 실행 + 병합 |
| 14 | Silo B PyRosetta flow 연동 | 04-01 | run_pyrosetta_agentic_mutdock_flow() 직접 호출 |
| 15 | FlexPepDock ddG 정상화 | 04-01 | 절대경로 resolve, baseline ddG=-52 |
| 16 | RFdiffusion backbone 생성 | 04-01 | 10/10 성공, GPU 2 |
| 17 | ProteinMPNN LigandMPNN CLI | 04-02 | 전용 env + 멀티체인 서열 분리 |
| 18 | step↔wrapper 키 매핑 전수 감사 | 04-02 | 5건 수정 |
| 19 | Diversity Manager 버그 수정 | 04-02 | seq_id int/str → candidate_id 통일 |
| 20 | UI Silo 필터링 | 04-02 | A/B/Combined 페이지별 데이터 분리 |
| 21 | vLLM Qwen3.5-27B GPU 3 | 04-02 | 88GB, FlashAttention v3 |
| 22 | Silo A Rosetta 스킵 | 04-02 | Boltz ipTM 기준 통과, Rosetta는 최종 검증용 |
| 23 | LLM 모델 4종 다운로드 | 04-02 | Qwen3.5-27B(52G), DeepSeek-R1-32B(62G), Qwen3.5-122B(234G), GLM-Z1-32B(61G) |
| 24 | vLLM/Ollama provider 분기 | 04-02 | CLI preflight, Settings 확장 (cursor agent) |
| 25 | 아카이브 경로 통합 | 04-02 | runs/ + runs_local/ 다중 탐색 |

---

## 진행 중 🔄

| # | 항목 | 상태 | 다음 단계 |
|---|------|------|----------|
| 26 | 듀얼 사일로 최종 검증 | 실행 중 | Silo A+B 통합 후보 확인 (Silo A Rosetta 스킵 적용) |
| 27 | Silo A 전체 흐름 E2E | 검증 중 | RFdiffusion→MPNN→ESMFold→Boltz→랭킹 끝까지 |

---

## 미착수 / TODO 📋

### 파이프라인 정상화

| # | 항목 | 우선순위 | 예상 시간 |
|---|------|---------|----------|
| 28 | 듀얼 사일로 병렬화 | 높음 | 2시간 |
|   | - Silo A(GPU 2) + Silo B(CPU) 동시 실행 | | |
|   | - 독립 상태 추적 → 완료 후 병합 | | |
|   | - ThreadPoolExecutor + status lock | | |
| 29 | PyRosetta flow LLM → vLLM 연결 | 중간 | 30분 |
|   | - Silo B 내부 Planner/Critic이 Ollama 호출 → 404 | | |
|   | - FlowConfig에 llm_base_url 전달 필요 | | |
| 30 | GLM-4-32B HF 인증 + 다운로드 | 낮음 | 30분 |

### UI / 프론트엔드

| # | 항목 | 우선순위 | 예상 시간 |
|---|------|---------|----------|
| 31 | Silo B status 갱신 | 높음 | 1시간 |
|   | - PyRosetta flow 자체 루프 중 status.json 미갱신 | | |
|   | - orchestrator에서 silo_b 진행률 주기적 업데이트 | | |
| 32 | UI 실시간 후보 테이블 | 중간 | 1시간 |
|   | - /api/status candidates[] → CandidateTable 자동 반영 | | |
|   | - 현재 parseStatusData 호환 확인 | | |
| 33 | Settings 페이지 LLM provider/model 선택 | 중간 | 1시간 |
|   | - vLLM 모델 목록 표시 | | |
|   | - provider 전환 (vllm/ollama) | | |

### 과학 / 에이전트

| # | 항목 | 우선순위 | 예상 시간 |
|---|------|---------|----------|
| 34 | Critic 확장 (5→19 메트릭) | 높음 | 3시간 |
|   | - interface_pLDDT, disulfide, ADMET, half_life 등 13개 추가 | | |
|   | - FAILURE_ACTION_MAP 확장 | | |
| 35 | 긍정 피드백 루프 (Reporter→Planner) | 중간 | 2시간 |
|   | - 성공 서열 위치별 AA 패턴 추출 | | |
|   | - ProteinMPNN bias로 반영 | | |
| 36 | Multi-iteration 수렴 검증 | 중간 | 2시간 |
|   | - 3 iter × Critic 피드백 → Planner 재계획 | | |
|   | - ddG 수렴 판단 | | |
| 37 | Off-target selectivity 실행 | 중간 | 2시간 |
|   | - 최종 후보 → SSTR1/3/4/5 도킹 | | |
|   | - WSM Tier 분류 | | |

### 인프라 / 모델

| # | 항목 | 우선순위 | 예상 시간 |
|---|------|---------|----------|
| 38 | LLM 벤치마크 (per-agent 모델 선택) | 중간 | 4시간 |
|   | - Qwen3.5-27B vs DeepSeek-R1-32B vs GLM-Z1-32B | | |
|   | - Planner/Critic/Reporter 역할별 비교 | | |
| 39 | Round 3 MEDIUM 이슈 7건 | 낮음 | 2시간 |
|   | - config, 다양성 필터, LLM 타임아웃, UI scatter chart | | |
| 40 | 테스트 코드 작성 | 낮음 | 2시간 |
|   | - pipeline_local pytest 스위트 | | |
|   | - mock/real 분리 | | |

---

## 시스템 현황

### GPU
| GPU | 용도 | VRAM |
|-----|------|------|
| 0 | 사용 안 함 | - |
| 1 | 다른 사용자 | 86GB |
| 2 | 파이프라인 (RFdiffusion/ESMFold/Boltz) | ~5GB 사용 시 |
| 3 | vLLM Qwen3.5-27B | 88GB |

### 서비스
| 서비스 | 포트 | 상태 |
|--------|------|------|
| Backend (FastAPI) | 8787 | ✅ |
| Frontend (Vite) | 5173 | ✅ |
| vLLM (Qwen3.5-27B) | 8002 | ✅ |
| Ollama | 11435 | CPU (백업용) |

### 파이프라인 성과
| 메트릭 | Silo A | Silo B |
|--------|--------|--------|
| 후보 생성 | 80 (MPNN) | 128 (BLOSUM+FlexPepDock) |
| QC 통과 | 54/80 (67%) | N/A (자체 ddG) |
| 도킹 통과 | 8/54 (Boltz ipTM) | 5/128 (FlexPepDock ddG) |
| Diversity | 8→8 | N/A |
| 최종 후보 | 검증 중 | 5개 (ddG -62 최고) |
