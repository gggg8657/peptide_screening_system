# Silo A Readiness Report — 2026-05-12

**작성자**: engineer-infra (Task #4)
**팀**: sod-2026-05-12-f11-recovery
**목적**: F9 Silo A dogfood 환경 준비 및 명령 verification

---

## 1. GPU 자원 가용성

| GPU Index | 물리 장치 | Free | Total | Utilization |
|-----------|----------|------|-------|-------------|
| 0 (CUDA_VISIBLE_DEVICES=0) | NVIDIA H100 NVL | 92 GB | 93 GB | 0% |
| 1 (CUDA_VISIBLE_DEVICES=1) | NVIDIA H100 NVL | 92 GB | 93 GB | 0% |
| 2 (CUDA_VISIBLE_DEVICES=2) | NVIDIA H100 NVL | 92 GB | 93 GB | 0% |
| 3 (CUDA_VISIBLE_DEVICES=3) | NVIDIA H100 NVL | 92 GB | 93 GB | 0% |

어제 Silo B 데모 이후 GPU 메모리가 전부 회수됨. 모든 GPU 사용 가능.
메모리 기록(~/.zshrc)에 따른 기본 CUDA_VISIBLE_DEVICES=2 — Silo A 실행 시 CUDA_VISIBLE_DEVICES=2,3 권장 (config 기준: silo_a=cuda:0 → 물리 GPU 2).

---

## 2. conda 환경 가용성

| Step | conda env | 상태 | PyTorch | CUDA | 비고 |
|------|----------|------|---------|------|------|
| Step02 RFdiffusion | rfdiffusion | **OK** | 2.1.0+cu121 | True (2 GPUs) | rfdiffusion 모듈 import OK |
| Step03 ProteinMPNN | proteinmpnn | **OK** | 2.2.1+cu121 | True | ligandmpnn CLI 확인됨 |
| Step04 ESMFold | esmfold | **OK** | 2.6.0+cu124 | True | esm import OK |
| Step05 Boltz | boltz | **OK** | 2.5.1+cu121 | — | boltz predict CLI 확인됨 |

4개 env 모두 정상. 미검증 이슈(39일 전 EOD 기록된 proteinmpnn env "미검증") 해소됨 — ligandmpnn CLI (`ligandmpnn --help`) 정상 응답 확인.

---

## 3. 모델 가중치 경로 유효성

| 모델 | 경로 | 상태 | 상세 |
|------|------|------|------|
| RFdiffusion inference script | `local_models/RFdiffusion/scripts/run_inference.py` | **OK** | 파일 존재 확인 |
| RFdiffusion weights (8종) | `local_models/RFdiffusion/models/` | **OK** | 각 파일 ~461 MB (Base, Complex, InpaintSeq, ActiveSite 등) |
| ProteinMPNN / LigandMPNN | conda env 내 설치 (`ligandmpnn` CLI) | **OK** | 별도 model_dir 불필요 |
| ESMFold | HuggingFace 캐시 자동 로드 | **OK** | model_paths.yaml: model_dir=null |
| Boltz | conda env 내 설치 | **OK** | model_paths.yaml: model_dir=null |
| Receptor PDB | `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/fold_test1_model_0.pdb` | **OK** | 237 KB, 2026-03-26 |

`model_paths.yaml`에 정의된 모든 Silo A 관련 경로 유효.

---

## 4. Wrapper Script 점검

### run_rfdiffusion.py
- conda env: `rfdiffusion` (명시됨)
- inference script: `_RFDIFFUSION_REPO/scripts/run_inference.py` — 존재 확인
- 입력: `--receptor-pdb` / `--input-json` (PDB 텍스트), `--contigs`, `--hotspot-res`, `--output-dir`
- 출력: `{"output_pdbs": [<pdb_text>, ...]}`
- GPU: subprocess 내에서 hydra override (CUDA_VISIBLE_DEVICES 상속)
- 상태: **검토 이상 없음**

### run_proteinmpnn.py
- conda env: `proteinmpnn` (명시됨)
- 실행 경로: 1순위 ligandmpnn CLI → 2순위 ESM-IF fallback
- ligandmpnn CLI 정상 확인 → 1순위 경로 사용 예상
- 입력: `--backbone-pdb` / `--input-json`, `--num-seqs`, `--temperature`, `--output-dir`
- 출력: `{"sequences": [{"sequence": "...", "score": ...}, ...]}`
- 상태: **검토 이상 없음**

---

## 5. 파이프라인 명령 dry-run (--help)

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
conda run -n bio-tools python -m pipeline_local.run_pipeline_local \
    --no-approach-b --iterations 1 \
    --llm-model qwen3:8b --ollama-host localhost:11435 \
    --config pipeline_local/config/pipeline_config_local_dogfood.yaml \
    --output-dir runs_local/silo_a_demo_2026-05-12 \
    --help
```

`--help` 실행 결과 — 모든 옵션 정상 파싱됨:
- `--no-approach-b`: Approach A (RFdiffusion+ProteinMPNN) 강제 활성화
- `--dual`: 듀얼 사일로 모드 (Silo A + Silo B 동시 실행) 옵션도 존재

---

## 6. 알려진 장애물 및 우회안

| ID | 장애물 | 심각도 | 우회안 |
|----|-------|--------|--------|
| B1 | `local_models/rfdiffusion` 설정 — `model_paths.yaml`의 `model_dir`이 `local_models/RFdiffusion`을 가리키나, pipeline_config의 `local_models.rfdiffusion.enabled: false`로 되어 있음 | **낮음** | `--no-approach-b` 실행 시 `enabled: true`로 변경하거나 CLI override 필요. 실제 실행 전 config 수정 필수 |
| B2 | LLM 설정 — dogfood config가 `vllm / Qwen/Qwen3.5-27B / port 8002`를 기본값으로 지정. `--ollama-host localhost:11435` CLI 인자가 provider=ollama일 때만 적용됨 | **중간** | vLLM 서버(port 8002) 가동 여부 사전 확인 필요. 또는 `--llm-base-url http://localhost:11435 --llm-model qwen3:8b` 조합 사용 |
| B3 | proteinmpnn wrapper의 `_run_ligandmpnn_cli`가 `--out_folder` 내 `seqs/` 서브디렉토리를 기대하나, `output-dir`이 존재하지 않으면 `NamedTemporaryFile(dir=args.output_dir)` 에러 가능 | **낮음** | `--output-dir` 인자로 사전 생성된 경로 지정 (pipeline이 자동 생성) |
| B4 | rfdiffusion env의 CUDA device count = 2 (CUDA_VISIBLE_DEVICES 2,3 환경에서) — wrapper가 subprocess로 hydra 실행 시 환경 변수 상속됨. `gpu_device: 0` 설정이 실제 물리 GPU 2에 매핑됨 | **낮음** | 현행 config 그대로 사용 가능. 단, `~/.zshrc`의 CUDA_VISIBLE_DEVICES=2 단독 설정은 `CUDA_VISIBLE_DEVICES=2,3`으로 조정 필요 |

---

## 7. 실 실행 시 예상 자원 및 시간

| Step | env | GPU | 예상 시간(1 iter, n=10) | VRAM |
|------|-----|-----|----------------------|------|
| Step02 RFdiffusion | rfdiffusion | cuda:0 (H100 92GB free) | 3-8분 (backbone 10개) | ~4-8 GB |
| Step03 ProteinMPNN | proteinmpnn | CPU 중심 | 1-2분 (8 seq × 10 backbone) | <1 GB |
| Step04 ESMFold | esmfold | cuda:0 or cuda:1 | 5-10분 (80개 서열 예측) | ~8-16 GB |
| Step05 Boltz | boltz | cuda:0 or cuda:1 | 5-15분 (도킹) | ~4-8 GB |
| **합계** | | | **약 15-35분 / iter** | **H100 여유 충분** |

---

## 8. 실행 전 체크리스트 (Silo A 실행 담당팀 인계)

- [ ] `pipeline_config_local_dogfood.yaml`의 `local_models.rfdiffusion.enabled: true`로 변경
- [ ] LLM 서버 확인 — vLLM port 8002 또는 Ollama port 11435 중 하나 가동 확인
- [ ] `CUDA_VISIBLE_DEVICES=2,3` 설정 확인 (dual silo 시 GPU 2/3 분리 사용)
- [ ] `runs_local/silo_a_demo_2026-05-12/` 출력 디렉토리 확인 (자동 생성됨)
- [ ] Silo A 실행 명령:
  ```bash
  CUDA_VISIBLE_DEVICES=2,3 conda run -n bio-tools python -m pipeline_local.run_pipeline_local \
      --no-approach-b --iterations 1 \
      --config pipeline_local/config/pipeline_config_local_dogfood.yaml \
      --output-dir runs_local/silo_a_demo_2026-05-12 \
      --log-level INFO
  ```

---

## 결론

Silo A 실행을 위한 환경은 **준비 완료** 상태입니다.

- conda env 4개 (rfdiffusion / proteinmpnn / esmfold / boltz) 모두 정상
- GPU 4개 전부 유휴 (92 GB free each)
- 모델 가중치 8종 전부 존재 (RFdiffusion models/)
- wrapper script 구조 검토 이상 없음
- 중요 차단 이슈 없음 (B1/B2는 config 1줄 수정으로 해소)
