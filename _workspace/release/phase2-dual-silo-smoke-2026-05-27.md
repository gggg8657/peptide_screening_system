# Phase 2 — Dual Silo Smoke Test 보고서 (실제 도구 호출)

- **실행 일시**: 2026-05-27 (로컬) — 파이프라인 시작 UTC `2026-05-27T08:32:33Z`
- **리포 루트**: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- **Conda**: `bio-tools` (Python 3.11.15)
- **GPU 정책**: `CUDA_VISIBLE_DEVICES=2` 단일 노출 (`torch.cuda.device_count()==1`, 논리 `cuda:0` → 물리 GPU 인덱스 2)
- **로그 원본**: `/tmp/phase2_pipeline_local.log`
- **금지 준수**: 코드 수정 없음. 신규 산출은 `runs_local/phase2_smoke_20260527_083233/` 하위만 기록·보조 프로브.

---

## 1. 실행 환경 (부트스트랩)

| 항목 | 결과 |
|------|------|
| `LocalPipelineOrchestrator` import | 성공 (`pipeline_local.orchestrator`) |
| 기본 설정 로드 | `pipeline_local/config/pipeline_config_local.yaml` → 실행 시 `_effective_pipeline_config_local.yaml`로 덤프 후 오케스트레이터에 전달 (정상 패턴) |
| 누락 설정 (경고만) | `gate_thresholds_local.yaml`, `tool_registry.yaml` 없음 → 로그에 WARNING, 기본값 사용 |
| `torch` / CUDA | `torch 2.10.0+cu128`, `cuda_count` 1 (VISIBLE_DEVICES 적용 결과) |
| `nvidia-smi -i 2` | `index,memory.used [MiB],memory.total [MiB]` → `2, 14 MiB, 95830 MiB` (시작 시점) |

**추가 관측**

- 에이전트 LLM 구성은 YAML에 따라 **vLLM** (`http://localhost:8002`)로 초기화되었으나, Planner 단계에서 `Connection refused (errno 111)` → **규칙 기반 폴백** (파이프라인은 계속 진행).

---

## 2. 1차: `pipeline_local` 스모크 (사용자 지정 명령)

### 2.1 실행 커맨드 (재현)

```bash
source /home/dongjukim/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
export CUDA_VISIBLE_DEVICES=2
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
python -m pipeline_local.run_pipeline_local --iterations 1 \
  --output-dir runs_local/phase2_smoke_20260527_083233
# (실제 세션에서는 전체 월클럭 1500초 제한으로 timeout 래핑)
```

### 2.2 Dual 여부에 대한 명시적 판정

- CLI에 **`--dual` 플래그가 없었고**, 저장된 작업 디렉터리 설정에도 **`dual_silo.enabled: false`** 상태로 동작.
- 따라서 본 실행은 로그상 **`Approach B (BLOSUM62 mutation only)`가 아니라**, `approach_b.strategy: dual_b1_b2`에 따른 **`ProteinMPNN ∪ ESM-Scan` 결합 후 Step04 이하** 로컬 파이프라인이다.
- **중요**: `pipeline_local.orchestrator` 의미의 “Dual Silo (`_run_silo_a` + `_run_silo_b` + `_run_dual_silo` 병합)”는 **이번 1차 커맨드로는 트리거되지 않음**. (활성화하려면 `--dual` 필요. 단, GPU 단일 노출 시 `dual_silo.silo_b.gpu_device: 1` 같은 설정은 수정 없이는 **추가 위험** — 아래 §4 참고.)

### 2.3 타임라인 요약 (`local_20260527_0832_iter01`)

| 단계 | 결과 | 대략 소요 |
|------|------|-----------|
| step01 receptor | PDB 추출·기록 성공 (`01_receptor/`) | <1 s |
| step03b mutation (`dual_b1_b2`) | ProteinMPNN 100 시퀀스 → 변이체 71; ESM-Scan 200 생성; 로그합계 ~17 s | ~17 s |
| 안정성 사전 스크리닝 | 200/200 통과 메시지 | — |
| step04 ESMFold QC | 단일 호출로 200 시퀀스 플립 → `55 passed / 145 failed`; `qc_summary.json` 기록 | **~110 s** (로그상 `109.7s`) |
| QC Ranker 게이트 | Gate1→4 로그 상 55→11 후보 선택 | 즉시 |
| step05 Boltz docking | **`[boltz] 실행 완료` 로그 32회 확인** 후 **전역 1500 s timeout 으로 프로세스 강제 종료** | 총 **~1500 s** 에서 차단 |

**중단 지점**: Step05 진행 중(대략 33번째 Boltz 호출 직전/직후 타임아웃). `05_docking/` 에 **포즈 PDB 32개**만 존재, `docking_scores.json`·이후 스텝(06 Rosetta 등) **`runs_local` 산출 기준 미생성**.

### 2.4 결론 (1차)

- **실제 도구**: ProteinMPNN(로컬 래퍼), ESM-Scan 전략, **ESMFold**(배치), **Boltz**(순차 다회) 호출까지 **실제 프로세스로 확인**.
- **End-to-end 1 iteration 완료**: **아니오** — 외부 스모크 시간 상한에 의해 Step05 미완 + 이후 미실행.

---

## 3. Silo A (요청 관점별로 분리해 기술)

### 3.A `pipeline_local` 의미의 Silo A (RFdiffusion + ProteinMPNN 백본 경로)

- 이번 1차 실행에서는 Approach 분기상 **Step02/03 미실행** (로그: `Approach B 활성화: Step02/03 스킵`).
- **RFdiffusion / Rosetta 단독 워커 conda env** 존재 여부는 §6 매트릭스에 기록 (`rfdiffusion`, `proteinmpnn` env `python -c` 성공).

### 3.B `pipelines/silo_a` 패키지 (3-arm NIM 오케스트레이션)

| Arm | 사용자 질문 항목 | 본 세션 결과 |
|-----|------------------|--------------|
| Arm1 MolMIM + DiffDock | 실행 시도 | **미실행** — `pipelines/silo_a/src/clients.create_nim_bundle()` 호출 시 `ValueError: NVIDIA API 키를 찾을 수 없습니다` (`NGC_CLI_API_KEY` / `.env` / `molmim.key` 요구 메시지) |
| Arm2 FlexPepDock (11 SST-14 변이 후보 YAML) | 1개 이상 실행 | **미실행** — NIM 번들 미구축으로 `SiloAOrchestrator.execute()` 전체가 시작되지 않음 |
| Arm3 RFdiffusion → ProteinMPNN → ESMFold | 외부 conda 호출 | **미실행** (동일 API 키 블로커) |
| UnifiedScorer / manifest | 교차-arm 정규화 | **미생성** (오케스트레이터 미실행) |

**판정**: 패키지 `SiloAOrchestrator` **import 성공**, **실 실행은 차단**(NVIDIA NGC/BioNeMo NIM 자격증명 부재).

---

## 4. Silo B (요청 관점별)

### 4.A `pipeline_local` 의미의 Silo B (PyRosetta mutdock 브랜치)

- `--dual` 비활성이므로 `_run_silo_b` / `run_pyrosetta_agentic_mutdock_flow` 호출 로그는 **존재하지 않음** (본 스모크에 미포함).

### 4.B `pipelines/silo_b` 모듈형 오케스트레이터 (제약 컴파일 → 생성 → 필터 → 도킹 → 안정성 → 스코어링 → 게이트)

아래 프로브는 **동일 Phase2 디렉터리** 내 `modular_probe/` 에만 추가 파일 생성.

#### 4.B.1 제약 검증 SST-14

- `configs/sst14_mutation_default.yaml` 기준: Cys3·C14 frozen, FWKT 고정 motif, 디설파이드 — `ConstraintCompiler` 경로 상 **정합** (기본값 로드).

#### 4.B.2 Generator / 필터 / 게이트 (Mock docking)

- `generator.budget.total_candidates: 3` 으로 임시 최소 실행 (설정 파일: `runs_local/phase2_smoke_20260527_083233/modular_probe/silo_b_minimal.yaml`).
- 결과: **`total_generated=3`, `filtered=3`, `scored=3`**, 상위 후보에 `sequence`, `dg`, `stability`, `druggability`, `score`, `gate` 관련 필드 포함.
- `DrugabilityFilter` 및 Gate1→3: **통과**(DefaultHILGate 시뮬레이션 경로).

#### 4.B.3 PyRosetta `PyRosettaDockingRunner` (실제 호출)

- 템플릿 PDB: `.../ai4sci-kaeri/data/fold_test1_model_0.pdb`
- SST-14 wildtype 서열에 대해 `FlexPepDockingProtocol()` 적용: **`success=True`, `dg=0.0`**, 벽시계 **~8.6 s**.

#### 4.B.4 `UnifiedCandidate` 변환

- `SiloBOrchestrator.to_unified(...)` 실행: **3건** 후보, `silo=Silo.SILO_B`, `modality=SST14_MUTANT`.

#### 4.B.5 레퍼런스 패키지 vs 로컬 mutdock 결과 스키마 (읽기 전용 검증)

- `runs_local/dual_final_03/local_20260402_1055_iter01/silo_b/.../iteration_manifest.json` 은 후보 블록에 `candidate_id`, `sequence`, `ddg`, `pdb_path`, 확장 메트릭 `pharma`(GRAVY, Boman, …) 포함.
- 모듈형 `OrchestratorResult.top_candidates[]` 필드 이름·중첩은 **서로 다른 JSON 계약**(통합 레이어 `UnifiedCandidate`에 맞추려면 명시 매핑 필요).
- **중요**: 동일 디렉터리의 `pipeline_config_local.yaml` 스냅샷에도 **`dual_silo.enabled: false`** — 보관물 자체가 “패키지 `CrossSiloManifest`” 형식이 아니며 **`pipelines/shared/models.py` 의 직렬화 산출은 확인되지 않음**.

---

## 5. Dual 통합 (`UnifiedCandidate` / 오케스트레이션)

| 질문 | 답변 |
|------|------|
| `pipelines/shared/models.UnifiedCandidate` 로 `pipeline_local` 이 통합하는가? | **아니오** — `pipeline_local/` 내 코드 검색 결과 **직접 import/사용 없음**. 통합 표현은 `AG_src.agents`/rank 테이블/로제타 결과 객체 쪽. |
| `pipeline_local.LocalPipelineOrchestrator` 가 두 silo를 호출하는가? | **`dual_silo.enabled` 참일 때만** `_run_silo_a` 및 `_run_silo_b(mutdock runner)` 실행. 이번 1차 CLI는 해당 플래그 없음 → **단일 브랜치**. |
| `pipelines/silo_a`/`silo_b` 패키지와의 관계 | **별도 패키지**. 옵션 패스로 교차 비교 가능(`to_unified` 제공)하나 금번 `pipeline_local` 실행과 자동 연동되진 않음. |

---

## 6. 실제 도구 가용성 매트릭스 (본 호스트 스냅샷)

| 도구 | bio-tools 에서 확인 | 비고 |
|------|---------------------|------|
| PyRosetta | import 성공 (배너 출력) | `PyRosettaDockingRunner` 1건 성공 |
| ProteinMPNN | Step03b 실호출 성공 | `ligandmpnn` 호출 로그 존재 |
| ESMFold | Step04 단일 실행으로 200 시퀀스 처리 성공 | `local_runner` GPU=0(가시 단일 디바이스) |
| Boltz-2 | Step05 에서 반복 실행 성공(32회 완료) | 후보당 ~40–52 s 수준(로그 인접 시간차 추정), **전체 후보 처리는 미완** |
| RFdiffusion / ProteinMPNN / ESMFold 전용 conda env | `conda run -n … python -c` 성공 (`rfdiffusion`, `proteinmpnn`, `esmfold`, `boltz`) | 이번 `pipeline_local` 경로에서는 Step02 미호출로 **직접 기동 검증 미수행** |
| MolMIM / DiffDock (NIM 클라이언트) | `bionemo` 번들 초기화 **실패** | `NGC_CLI_API_KEY` 등 자격증명 부재 메시지 |
| pepADMET | `conda run -n pepadmet python -c "import pepadmet"` **실패** | 패키지명·엔트리포인트 추가 확인 필요 (환경 존재 O, import 불가) |
| pepMSND | `_workspace/pepmsnd_local/.conda_env` 에서 단순 실행 OK | 파이프라인 본 실행 경로에서는 미통합 검증 |

---

## 7. 실패·부분 결과 상세 원인 분류

| 항목 | 분류 태그 | 요약 |
|------|-----------|------|
| Phase2 전역 1500 s 종료 | `timeout` | Step05 진행 도중 차단 (`ELAPSED_SEC=1500`) |
| vLLM planner | `errno 111` / `connection refused` | 에이전트는 폴백으로 계속 |
| NIM Silo A | `ValueError` (API 키) | NGC/BioNeMo 자격증명 |
| Modular Silo B `receptor PDB path` 설정 | 구성 미비 경고 로그 (`SSTR2` 문자열 폴백) | 목업 도킹엔 무해했으나 **실패진단용으로 기록** |
| pepADMET import | 모듈 경로 또는 설치 상태 미일치 가능 | `conda list`/엔트리 재확인 권장 (코드 수정은 이번 Phase 범위 밖) |

**스택 트레이스**: 극단 네트워크 또는 PyRosetta 측 **치명 장애 traceback 은 발생하지 않음**(주로 timeout 및 구성 단계 ValueError).

---

## 8. 한 줄 결론

**Y / Partial / N** → **`Partial`**  
근거: `pipeline_local` 단일 반복도 **Boltz 과다 순차 실행으로 SLA 내 완료 실패**. 반면 단일 GPU2에서 **ESMFold·Boltz 부분 호출**, **패키지 Silo B + PyRosetta 실제 docking 1건**은 확인됨. **설계 의미의 orchestrator 듀얼 사일오(`--dual`) + NIM Silo A** 는 **미검증 또는 키에 의해 차단**.

---

## 9. 다음 단계 권고 (수정 우선순위 — 코드 수정 제안 없이 운영 관점만)

1. **스모크 재현 명령에 `--dual` 여부 명시 검토** 및, GPU 단일 노출 스모크에서는 `dual_silo.silo_* .gpu_device` 를 **논리 0 하나로 정렬**(설정 수정은 다음 Phase에서 합의).
2. Boltz 평가 규모: Step05 진입 후보 수(예: 현재 로그 상 **55개 전체 순차 docking**) 또는 `docking_top_pct` 를 **스모크 전용 프로파일**로 축소(정책 합의).
3. **`NGC_CLI_API_KEY`** 제공 후 `pipelines/silo_a` Arm1–3 **최소 1 회** 실호출 회귀.
4. `pepadmet` 환경의 **실제 import 경로**(배포된 wheel 구조) 점검.
5. vLLM이 필요하면 **서비스 헬스체크** 포함한 Phase3 사전 게이트, 불필요하면 `pipeline_config_local.yaml`에서 `provider: none` 테스트로 변동성 제거.

---

## 부록 A. 증거 경로 모음

- Phase2 신규 런 디렉터리:  
  `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/runs_local/phase2_smoke_20260527_083233/local_20260527_0832_iter01/`
- QC 요약 JSON: 위 경로 `/04_qc/qc_summary.json`
- Modular Silo B 보조 결과:  
  `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/runs_local/phase2_smoke_20260527_083233/modular_probe/modular_silo_b_probe.json`

---

## 부록 B. `pipeline_shared.UnifiedCandidate` 스키마 (참조)

다음 타입 정의 위치만 확인하였으며 코드 변경 없음:

- `pipelines/shared/models.py` — `UnifiedCandidate`, `CrossSiloManifest`.

---

## 부록 C. Step03b 출력 규모 (로그 근거)

| 구분 | 수치 |
|------|------|
| ProteinMPNN raw 수집 | 100 시퀀스 |
| 약품포어 통과 변이체 | 71 (`pharmacophore 통과` 로그) |
| ESM-Scan 생성 | 200 변이체 |
| Step03b wall time | ~17 s (오케스트레이터 로그) |

## 부록 D. Step04 게이트 임계 (동작 확인용)

로그 라인 패턴 예: `[Step04] var_xxx: pLDDT=…, iface_pLDDT=… -> PASS/FAIL`  
종합 라인: `QC gate: 55 passed / 145 failed.`  
→ **ESMFold** 경로 실호출 후 **통과 세트 크기 확정**(이후 게이트는 이 세트 상에서 동작).

## 부록 E. Boltz 호출 카운팅 방법

`/tmp/phase2_pipeline_local.log` 에서 문자열 **`[boltz] 실행 완료`** 카운트 = **32** (grep count). 남은 QC 통과 후보 수는 **대략 55 − 32 = 23** 추정 상태에서 종료 신호 발생.

## 부록 F. 타임아웃 종료 시그널 (재현 검증용)

외부 명령 `timeout -k … 1500 …` 패턴 표준 종료 코드 **124**(GNU coreutils 관례). 본 실행에서도 글로벌 1500 s 경계에서 프로세스가 끊겼으며, 사용자 제약(25 분) 준수.

## 부록 G. GPU 가시 인덱스와 오케스트레이터 `device=` 문자열

`CUDA_VISIBLE_DEVICES=2` 인 경우 일반 규약상 PyTorch 장치 문자열 **`cuda:0`** 이 물리 GPU 2에 매핑됨 (`LocalPipelineOrchestrator device=cuda:0`).  
로그의 `GPU=0` 은 논리 인덱스이며 사용자 요구 “GPU 0/1/3 미사용”과 충돌하지 않도록 **VISIBLE 세트로만 장치 선택**하였음을 기록한다.

---

## 부록 H. 과거 저장물 `dual_final_03` 해석 한계

저장 디렉터리 `runs_local/dual_final_03/local_20260402_1055_iter01/` 에는 다음이 존재:

- 저장된 설정 스냅샷 내 `dual_silo.enabled: false`
- 무거운 `silo_b/sst14_agentic_mutdock/…` PDB·JSON 산출
- 패키지 `pipelines/shared` 차원의 `CrossSiloManifest`/후보 목록 형식 분명한 단일 파일은 **탐색되지 않음** (패키지 Silo 병합 결과와의 **자동 교차 검증 불가**).

이 때문에 “dual_final_03 과 Phase2 산출의 schema 정합”은 **`UnifiedCandidate` 기준에는 Partial / Not applicable** 에 가깝다.

