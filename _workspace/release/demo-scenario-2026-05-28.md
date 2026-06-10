# 2026-05-28 회의 시연 시나리오 — 투명 시연

> **작성일**: 2026-05-27 (D-1)
> **결정 근거**: Phase 2 dual silo smoke 결과 (`phase2-dual-silo-smoke-2026-05-27.md`) + Phase 3 UI/UX 결과 (`phase3-ui-ux-2026-05-27.md`) + BE P0 fix (`be-p0-fix-2026-05-27.md`)
> **원칙**: 동작하는 것만 라이브, 한계는 화면 및 발화로 명시

---

## 사전 준비 (회의 30분 전)

### 1. BE 부팅
```bash
cd ~/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
source ~/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --log-level info
```
검증: 다른 터미널에서
```bash
curl -s http://127.0.0.1:8001/api/health | python3 -m json.tool
# 기대: {"status": "ok", "service": "ai4sci-kaeri-backend", "version": "2.0.0", ...}
```

### 2. FE 부팅
```bash
cd ~/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend
npm run dev
# 기대: http://localhost:5173 또는 vite가 배정한 포트
```

### 3. GPU 점유 확인
- GPU 0/1: 타인 점유 (손대지 말 것)
- GPU 2/3: 본인 가용 (시연 중 Silo B PyRosetta 단건 호출용)

### 4. 회의 자료
- 메인 PPTX: `_workspace/pptx/PRST_N_FM_Meeting_2026-05-28_v3.pptx` (26 슬라이드)
- narrative 백업: `_workspace/release/meeting-2026-05-28-narrative-v3.md`

---

## 시연 흐름 (예상 8~10분)

### Step 1 — BE/FE 라이브 부팅 확인 (1분)
**무엇을 보여줄지**: FE 메인 화면(`/console` 리다이렉트) + `/api/status` 응답
**대본**: "백엔드와 프론트엔드가 실제로 떠 있습니다. `/api/health` 응답에 우리 service 식별자가 박혀 있어, 다른 서비스가 8001을 점거하더라도 우리 BE 부팅 여부를 정확히 구분할 수 있습니다."

### Step 2 — 기존 PRST 산출물 화면 시연 (2~3분)
**무엇을 보여줄지**:
- `/run/new` → `runs_local/dual_final_03/local_20260402_1055_iter01/` 선택 (또는 ID로 직접 진입)
- Candidate Page: PRST-001 (Tier S), AGCKNIIWKTITSC, WSS=1.000, ΔG=-105.5 REU
- Mol* 3D 구조 (SSTR2 7XNA + SST-14 또는 PRST-001 docked)
- Selectivity Explorer: SSTR1/3/4/5 ΔG 비교

**대본**: "이것은 5월 19일에 도출한 PRST-001~004 후보 4개의 화면입니다. 합성 의뢰서까지 작성된 상태이며, ADMET=1.00은 OOD 외삽 위험으로 wet-lab 병행을 명시했습니다."

**한계 명시**: "Mol* 3D는 후보별 docked 구조가 있으면 그걸, 없으면 SSTR2 reference 7XNA를 폴백으로 보여줍니다. 화면에 'reference fallback' 표시를 추가하는 것이 후속 작업입니다." (Phase 3 P2 fix 후보)

### Step 3 — Silo B PyRosetta 단건 라이브 (~10초)
**명령** (별도 터미널, 사전 yaml 준비):
```bash
cd ~/Documents/workspace/repos/SST14-M_scr
source ~/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
export CUDA_VISIBLE_DEVICES=2  # 또는 3
python -c "
from pipelines.silo_b.src.docking import PyRosettaDockingRunner
from pipelines.silo_b.src.config import load_config
import time
config = load_config('pipelines/silo_b/configs/sst14_mutation_default.yaml')
runner = PyRosettaDockingRunner(config)
t = time.time()
result = runner.dock('AGCKNFFWKTFTSC', 'data/somatostatin_receptor/SSTR2_7XNA.pdb')
print(f'docking_dg={result.dg:.2f}, elapsed={time.time()-t:.1f}s, success={result.success}')
"
```
기대 결과: `docking_dg=0.0, elapsed=8~10s, success=True` (Phase 2에서 검증한 패턴)

**대본**: "이 한 줄로 PyRosetta `FlexPepDockingProtocol`이 실제 호출됩니다. SST-14 wildtype을 SSTR2에 docking 한 라이브 결과입니다."

### Step 4 — 한계 화면 표시 (2분)
**무엇을 보여줄지**: narrative v3 §5.4 코드 격차 슬라이드 (Slide 17 ⚠)
**대본**: "여기 7가지 격차가 있습니다. 'PR #85 main 반영'과 'PRST 의뢰서가 그걸 호출한다'는 동치가 아닙니다. PR #117, PR #112도 본 브랜치에 머지되어 있지 않습니다. 6월까지 enrichment 경로를 3-Layer 모듈과 정합시키는 작업이 필요합니다."

### Step 5 — 슈뢰딩거 도입 검토 + 의사결정 요청 (3~4분)
**무엇을 보여줄지**: narrative v3 §6.3 모듈별 예상 효과 + §7 의사결정 항목
**대본**: "현재 도구 한계 5가지를 슈뢰딩거 모듈로 일부 줄일 수 있는지 검토를 6월 회의까지 진행하는 의사결정을 요청드립니다. 비용·라이센스·시스템 적용 결과는 6월에 정량화하겠습니다."

---

## 시연 중 라이브로 보여주지 않는 것 (Q&A 대비)

| 질문 가능 항목 | 답변 |
|---------------|------|
| pipeline_local 1 iter 라이브 실행? | "현재 한 사이클이 40~50분 정도 걸려 라이브는 어렵습니다. 5/27 스모크 결과 보고서를 슬라이드에 포함했습니다." |
| Silo A 3-Arm? | "NVIDIA NGC API key가 필요하고 회의 전 확보를 시도 중입니다. 오늘은 Silo B 기반으로 시연합니다." |
| Boltz 라이브? | "Boltz 단건 호출이 후보당 40~50초입니다. 시간이 충분하면 한 건 시연 가능합니다 (옵션)." |
| `--dual` flag? | "현재 코드의 `dual_silo.enabled`는 default false이고, 두 silo를 묶는 자동 통합은 차후 enrichment 정합 후 활성화 예정입니다." |
| 3-Layer Ensemble은 어디서 보나? | "코드의 `pipeline_local/scoring/layer1_ensemble.py`, `layer2_ensemble.py`, `ensemble_router.py`에 모듈이 있고, 화면에는 표시되지 않습니다. 발표 슬라이드 14~17이 이 격차를 다룹니다." |

---

## 백업 시나리오 (라이브 실패 시)

### Backup A — BE 부팅 실패 시
- 사전 캡처한 스크린샷으로 진행
- `_workspace/pptx/PRST_N_FM_Meeting_2026-05-28_v3.pptx` Slide 18 ADMET-AI 차트로 대체

### Backup B — FE 빌드 실패 시
- 빌드된 `frontend/dist`가 있다면 `npx serve frontend/dist`로 정적 시연
- 또는 PPTX Slide 13 (9건 매트릭스) 중심

### Backup C — PyRosetta 단건 실패 시 (예: 환경 conflict)
- `_workspace/release/3layer-admet-serum-impact-analysis.md` §2.3 인용 (이미 검증된 8.6초 실행 결과 인용)
- 라이브 시연 없이 결과만 보여줌

---

## 시연 후 즉시 후속 작업 (회의 종료 직후)

1. 회의 의사결정 결과를 SOD로 정리 (`_workspace/release/eod-2026-05-28-meeting.md`)
2. PR #112(pepMSND 재학습) 머지 여부 결정 — Layer 2 R² 0.022 결과 합의 시 머지
3. PR #117(ADMET divergence guard) main 동기화
4. NGC key 확보 진행 (Silo A 회귀용)
5. Schrödinger 검토 진행 승인 시 → Schrödinger Korea 영업 연락 일정

---

## 부록 — 시연 중 사용할 절대경로

| 항목 | 경로 |
|------|------|
| BE 부팅 | `~/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/main.py` |
| FE 부팅 | `~/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/` |
| PRST 산출물 | `~/Documents/workspace/repos/SST14-M_scr/runs_local/dual_final_03/local_20260402_1055_iter01/` |
| 합성 의뢰서 | `~/Documents/workspace/repos/SST14-M_scr/runs_local/final_candidates/synthesis_orders/PRST-001.md ~ PRST-004.md` |
| 발표 PPTX | `~/Documents/workspace/repos/SST14-M_scr/_workspace/pptx/PRST_N_FM_Meeting_2026-05-28_v3.pptx` |
| narrative 백업 | `~/Documents/workspace/repos/SST14-M_scr/_workspace/release/meeting-2026-05-28-narrative-v3.md` |
| SSTR2 PDB | `~/Documents/workspace/repos/SST14-M_scr/data/somatostatin_receptor/SSTR2_7XNA.pdb` |
| Silo B config | `~/Documents/workspace/repos/SST14-M_scr/pipelines/silo_b/configs/sst14_mutation_default.yaml` |
