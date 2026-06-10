# Claude Code 실행 프롬프트 — A-06

## 사용 방법
이 프롬프트를 복사하여 Claude Code 세션에 붙여넣어 실행.
CLAUDE.md의 위임 트리 1~4순위에 따라 자동 분배됨.

---

## 컨텍스트 (Claude Code가 먼저 읽어야 할 파일)
- @CLAUDE.md
- @docs/meet_log/2026-04-06_action_items/A-06_diffusion_docking_PoC.md
- @pipeline_local/steps/step05_docking.py
- @pipeline_local/scripts/flexpep_dock.py
- @AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/pipeline/orchestrator.py
- 회의록 원문: @docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf

---

## 작업 정의

**목표**: DiffDock(또는 유사 디퓨전 도킹 모델)을 SSTR2-SST14 복합체에 적용하여
cryo-EM 포즈 대비 RMSD와 FlexPepDock 대비 속도를 실측, PoC 보고서를 작성한다.

**세부 작업**:
1. GPU VRAM 가용성 확인 및 DiffDock 환경 구축
   - `nvidia-smi` 출력으로 현재 H100 NVL 가용 VRAM 확인
   - DiffDock conda 환경 생성 (engineer-infra 협력)
2. Ground truth 포즈 준비
   - RCSB에서 SSTR2-펩타이드 복합체 구조 다운로드 (7T10 또는 7T11의 펩타이드 체인)
   - 또는 `runs_local/sst14_ref_docking/` 의 FlexPepDock 최적 포즈 사용
3. DiffDock 실행 (40 포즈)
4. RMSD 계산 스크립트 작성 (`pipeline_local/scripts/compute_docking_rmsd.py`)
5. FlexPepDock 속도 vs DiffDock 속도 비교
6. PoC 결과 JSON + Markdown 보고서 생성
   - `runs_local/diffdock_poc/poc_report.json`
   - `runs_local/diffdock_poc/poc_report.md`

**파이프라인 통합 결정 기준**:
- RMSD ≤ 2.0 Å 성공률 ≥ 80% → Silo B 1차 필터 도입 검토
- 미달 → 기각 및 대안(NeuralPLexer, AlphaFold3) 후보 목록 작성

---

## 입력 (Input Spec)

| 항목 | 값/경로 |
|------|--------|
| 수용체 구조 | `data/somatostatin_receptor/SSTR2_7XNA.pdb` |
| Ground truth 포즈 | RCSB 7T10 펩타이드 체인 또는 FlexPepDock 최적 포즈 |
| SST14 서열 | `AGCKNFFWKTFTSC` |
| 비교 기준선 | `pipeline_local/scripts/flexpep_dock.py` (FlexPepDock wall-clock) |
| GPU | H100 NVL, `CUDA_VISIBLE_DEVICES=2` |

---

## 출력 (Output Spec)

| 산출물 | 위치 | 형식 |
|--------|------|------|
| DiffDock 포즈들 | `runs_local/diffdock_poc/poses/` | PDB (40개) |
| PoC 결과 JSON | `runs_local/diffdock_poc/poc_report.json` | JSON |
| PoC 보고서 | `runs_local/diffdock_poc/poc_report.md` | Markdown |
| RMSD 계산 스크립트 | `pipeline_local/scripts/compute_docking_rmsd.py` | Python |

---

## 검증 기준 (Acceptance Criteria)

- [ ] DiffDock 실행 완료 (40 포즈 생성)
- [ ] `poc_report.json`에 `rmsd_success_rate`, `diffdock_time_sec`, `speedup` 포함
- [ ] RMSD 계산 코드에 타입힌팅 + pytest 단위 테스트 추가
- [ ] `poc_report.md`에 파이프라인 통합 권고 또는 기각 사유 명시
- [ ] VRAM 사용량 로그 포함 (`nvidia-smi` 스냅샷)

---

## 추천 위임 경로

- **1순위 tmux team-mate** (A-06은 설계 결정 포함):
  ```bash
  ./scripts/launch_agent_team.sh
  # "DiffDock PoC 진행 여부 및 모델 선정" 토론
  ```
- **3순위 서브에이전트**:
  - `engineer-infra` — DiffDock conda 환경 구축, GPU VRAM 검증
  - `engineer-backend` — RMSD 계산 스크립트, PoC 보고서 생성
  - `researcher` — DiffDock 펩타이드 적용 선행 연구 조사 (DiffDock-PP 등)
- **2순위 codex** (RMSD 스크립트 단독 작성):
  ```bash
  codex exec "pipeline_local/scripts/compute_docking_rmsd.py 작성: BioPython Superimposer로 pred_pdb vs ref_pdb Cα RMSD 계산, CLI 인터페이스 포함, pytest 추가"
  ```

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| VRAM 부족 (< 24 GB) | Multi-GPU 모드 또는 A-07(DGX 검토) 에스컬레이션 |
| DiffDock 펩타이드 처리 미지원 | DiffDock-PP 또는 NeuralPLexer로 전환 |
| Ground truth 포즈 없음 | FlexPepDock 최적 포즈로 대체 (RMSD 0으로 기록 후 상대 비교) |
| RMSD 계산 오류 (잔기 수 불일치) | Cα만 선택 또는 sequence alignment 후 공통 원자만 사용 |
| DiffDock 설치 실패 | engineer-infra에 `conda env create -f diffdock_env.yml` 요청 |

---

## 참고 자료

- 회의록 A-06 원문: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`
- DiffDock 논문: arXiv:2210.01776 (Corso et al., 2022)
- DiffDock GitHub: https://github.com/gcorso/DiffDock
- DiffDock-PP (펩타이드 특화): https://github.com/YaourtB/DiffDock-PP
- NeuralPLexer: arXiv:2209.15171
- KAERI GPU 설정: `~/.zshrc` (CUDA_VISIBLE_DEVICES=2)
- 현행 FlexPepDock 래퍼: `pipeline_local/scripts/flexpep_dock.py`
