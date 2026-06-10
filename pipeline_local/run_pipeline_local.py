#!/usr/bin/env python3
"""
run_pipeline_local.py
=====================
LOCAL MODE 메인 진입점 — NVIDIA NIM API 없이 로컬 GPU 모델만 사용

원본: run_pipeline_live.py (NIM API 버전)
변경 사항:
  - NVIDIA_NIM_API_KEY 불필요
  - pipeline_config_local.yaml 로드
  - LocalPipelineOrchestrator 사용
  - LOCAL MODE 배너 출력 (사용 중인 GPU 장치 표시)
  - 추가 CLI 인수: --iterations, --output-dir, --llm-model

사용법:
    python -m pipeline_local.run_pipeline_local
    python -m pipeline_local.run_pipeline_local --iterations 3 --llm-model qwen3:8b
    python -m pipeline_local.run_pipeline_local --resume --run-id local_20260326_1200_iter01
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

# ---------------------------------------------------------------------------
# sys.path 설정: pipeline_local 루트 + 원본 AG_src 저장소
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent  # genmol-repo/
_AG_SRC_REPO = Path(
    "/home/dongjukim/Documents/workspace/repos/SST14-M_scr"
    "/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri"
)

for _p in (_REPO_ROOT, _AG_SRC_REPO):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pipeline_local.orchestrator import LocalPipelineOrchestrator, FinalResult

# ---------------------------------------------------------------------------
# 컬러 출력 헬퍼
# ---------------------------------------------------------------------------
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[90m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
RED     = "\033[31m"
WHITE   = "\033[97m"
BG_BLUE  = "\033[44m"
BG_GREEN = "\033[42m"


def _ts() -> str:
    return f"{DIM}{time.strftime('%H:%M:%S')}{RESET}"


def p(msg: str, color: str = CYAN) -> None:
    print(f"{_ts()} {color}{msg}{RESET}")


def ok(msg: str) -> None:
    print(f"    {GREEN}[OK]{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"    {YELLOW}[WARN]{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"    {RED}[FAIL]{RESET} {msg}")


def info(msg: str) -> None:
    print(f"    {DIM}[INFO]{RESET} {msg}")


def banner(text: str, char: str = "=", width: int = 72) -> None:
    print(f"\n{BOLD}{MAGENTA}{char * width}\n  {text}\n{char * width}{RESET}\n")


def step_h(name: str, desc: str) -> None:
    print(f"\n  {BG_BLUE}{WHITE}{BOLD} {name} {RESET}  {desc}\n  {'-' * 60}")


# ---------------------------------------------------------------------------
# GPU 장치 정보 확인
# ---------------------------------------------------------------------------

def _detect_device() -> str:
    """사용 가능한 CUDA 장치를 감지한다.

    CUDA_VISIBLE_DEVICES 환경변수를 우선 참조하고,
    없으면 torch.cuda로 확인한다.
    """
    cuda_devs = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_devs:
        first = cuda_devs.split(",")[0].strip()
        return f"cuda:{first}" if first.isdigit() else "cuda:0"
    try:
        import torch
        if torch.cuda.is_available():
            dev_idx = torch.cuda.current_device()
            dev_name = torch.cuda.get_device_name(dev_idx)
            return f"cuda:{dev_idx} ({dev_name})"
    except ImportError:
        pass
    return "cpu (GPU 없음)"


def _check_ollama(host: str, model: str) -> bool:
    """Ollama 서버 상태와 지정 모델 존재 여부를 확인한다.

    Args:
        host:  Ollama 서버 주소 (예: "127.0.0.1:11435")
        model: 확인할 모델 이름 (예: "qwen3:8b")

    Returns:
        True: Ollama 정상 작동 및 모델 존재
        False: 서버 미응답 또는 모델 없음
    """
    import urllib.request
    import urllib.error

    # /api/tags 로 모델 목록 조회
    url = f"http://{host}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            model_base = model.split(":")[0]
            found = any(model_base in m for m in models)
            return found
    except (urllib.error.URLError, json.JSONDecodeError, Exception):
        return False


def _check_vllm(base_url: str, model: str) -> Tuple[bool, str]:
    """vLLM OpenAI 호환 API ``GET /v1/models`` 로 서버 가동 및 모델 id 일치 여부를 확인한다.

    Returns:
        (True, msg)  서버 응답 및 모델 매칭 성공
        (False, msg) 실패 사유 (표시용 짧은 문자열)
    """
    import urllib.error
    import urllib.request

    base = base_url.rstrip("/")
    url = f"{base}/v1/models"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ids = [item.get("id", "") for item in (data.get("data") or []) if item.get("id")]
            if not ids:
                return False, "/v1/models 응답에 data/id 없음"
            short = model.split("/")[-1]
            for mid in ids:
                if mid == model or model in mid or mid.endswith(short):
                    return True, f"모델 일치 ({mid})"
            return False, f"서버 모델 목록에 '{model}' 없음 — {ids[:8]}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except (urllib.error.URLError, json.JSONDecodeError, OSError, Exception) as e:
        return False, str(e)[:200]


def _ollama_host_from_base_url(llm_cfg: Dict[str, Any]) -> str:
    """llm.base_url 에서 host:port 형태로 변환."""
    bu = llm_cfg.get("base_url", "http://127.0.0.1:11435")
    return bu.replace("http://", "").replace("https://", "").split("/")[0]


# ---------------------------------------------------------------------------
# CLI 인수 파싱
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LOCAL MODE — SSTR2 Peptide Binder Pipeline (no NIM API)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--iterations",
        "--max-iterations",
        dest="iterations",
        type=int,
        default=None,
        help="최대 반복 횟수 (설정 파일의 max_iterations 덮어쓰기)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="결과 저장 루트 디렉토리 (기본: runs_local/)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="LLM 모델 id (Ollama 태그 또는 vLLM served-model-name)",
    )
    parser.add_argument(
        "--llm-base-url",
        type=str,
        default=None,
        help="LLM API 베이스 URL 전체 (예: http://127.0.0.1:8001). vLLM/Ollama 모두 설정 가능.",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default=None,
        help="Ollama 전용: host:port (provider=ollama 일 때만 base_url 로 적용)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="설정 파일 경로 (기본: pipeline_local/config/pipeline_config_local.yaml)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="마지막 체크포인트에서 재개",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="재개할 run_id (--resume 사용 시 필요)",
    )
    parser.add_argument(
        "--approach-b",
        action="store_true",
        default=None,
        help="Approach B (BLOSUM62 텍스트 수준 돌연변이) 강제 활성화",
    )
    parser.add_argument(
        "--no-approach-b",
        action="store_true",
        default=False,
        help="Approach A (RFdiffusion + ProteinMPNN) 강제 사용",
    )
    parser.add_argument(
        "--dual",
        action="store_true",
        default=False,
        help=(
            "듀얼 사일로 모드 활성화: Silo A (RFdiffusion+ProteinMPNN) + "
            "Silo B (BLOSUM62+FlexPepDock) 동시 실행 후 후보 병합"
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="로그 레벨",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    # 로그 레벨 설정
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="[%(asctime)s][%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # ------------------------------------------------------------------
    # 설정 파일 로드
    # ------------------------------------------------------------------
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = _THIS_DIR / "config" / "pipeline_config_local.yaml"

    if not config_path.exists():
        fail(f"설정 파일 없음: {config_path}")
        fail("pipeline_local/config/pipeline_config_local.yaml 파일을 확인하세요.")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        pipeline_cfg: Dict[str, Any] = yaml.safe_load(f) or {}

    # ------------------------------------------------------------------
    # CLI 인수로 설정 덮어쓰기
    # ------------------------------------------------------------------
    llm_cfg = pipeline_cfg.setdefault("llm", {})
    if args.llm_model:
        llm_cfg["model"] = args.llm_model
    if args.llm_base_url:
        llm_cfg["base_url"] = args.llm_base_url.rstrip("/")
    if args.ollama_host:
        prov = str(llm_cfg.get("provider", "ollama")).lower()
        if prov == "ollama":
            llm_cfg["base_url"] = f"http://{args.ollama_host}"

    iter_cfg = pipeline_cfg.setdefault("iteration", {})
    if args.iterations is not None:
        iter_cfg["max_iterations"] = max(1, int(args.iterations))

    if args.output_dir:
        pipeline_cfg["output_base_dir"] = args.output_dir

    # 듀얼 사일로 모드 설정 (--dual 플래그)
    if args.dual:
        pipeline_cfg.setdefault("dual_silo", {})["enabled"] = True
        # 듀얼 모드에서는 approach_b.enabled 상태와 무관하게 양쪽 사일로 실행
        # (approach_b는 단일 Silo B 전용 플래그이므로 dual 모드와 독립)

    # Approach 분기 설정 (--dual 미사용 시에만 유효)
    if not args.dual:
        if args.no_approach_b:
            pipeline_cfg.setdefault("approach_b", {})["enabled"] = False
        elif args.approach_b:
            pipeline_cfg.setdefault("approach_b", {})["enabled"] = True

    # 수정된 설정을 임시 파일로 저장 (orchestrator가 YAML 경로를 받으므로)
    effective_config_path = (
        config_path.parent / f"_effective_{config_path.name}"
    )
    with open(effective_config_path, "w", encoding="utf-8") as f:
        yaml.dump(pipeline_cfg, f, allow_unicode=True, default_flow_style=False)

    # ------------------------------------------------------------------
    # 실행 환경 정보 수집
    # ------------------------------------------------------------------
    device = _detect_device()
    llm_provider = str(llm_cfg.get("provider", "ollama")).lower()
    llm_base = str(llm_cfg.get("base_url", "http://127.0.0.1:11435")).rstrip("/")
    ollama_host = _ollama_host_from_base_url(llm_cfg)
    llm_model = llm_cfg.get("model", "qwen3:8b")
    max_iterations = int(iter_cfg.get("max_iterations", 5))
    dual_silo_enabled = pipeline_cfg.get("dual_silo", {}).get("enabled", False)
    approach_b_enabled = pipeline_cfg.get("approach_b", {}).get("enabled", False)

    # ------------------------------------------------------------------
    # 시작 배너 출력
    # ------------------------------------------------------------------
    banner("SSTR2 Peptide Binder Design — LOCAL MODE")
    print(f"  {GREEN}Mode:{RESET}     LOCAL — all models running on GPU {device}")
    print(f"  {GREEN}Target:{RESET}   SSTR2 (Somatostatin Receptor Type 2)")
    print(f"  {GREEN}Ref:{RESET}      DOTATATE (AGCKNFFWKTFTSC, 14-aa)")
    if llm_provider == "vllm":
        print(f"  {GREEN}LLM:{RESET}      vLLM [{llm_base}] model={llm_model}")
    elif llm_provider == "none":
        print(f"  {GREEN}LLM:{RESET}      none (rule-based)")
    else:
        print(f"  {GREEN}LLM:{RESET}      Ollama [{ollama_host}] model={llm_model}")
    print(f"  {GREEN}Config:{RESET}   {config_path}")
    print(f"  {GREEN}Iters:{RESET}    {max_iterations}")
    if dual_silo_enabled:
        _approach_label = "DUAL (Silo A: RFdiffusion+MPNN | Silo B: BLOSUM62+FlexPepDock)"
    elif approach_b_enabled:
        _approach_label = "B (BLOSUM62 mutation only)"
    else:
        _approach_label = "A (RFdiffusion + ProteinMPNN only)"
    print(f"  {GREEN}Approach:{RESET} {_approach_label}")
    print()

    # ------------------------------------------------------------------
    # 사전 점검
    # ------------------------------------------------------------------
    step_h("CHECK", "실행 환경 사전 점검")

    # CUDA 가용성 확인
    try:
        import torch
        if torch.cuda.is_available():
            n_gpu = torch.cuda.device_count()
            ok(f"CUDA 사용 가능 — {n_gpu}개 GPU 감지됨")
            for i in range(n_gpu):
                mem_total = torch.cuda.get_device_properties(i).total_memory // (1024 ** 3)
                info(f"  GPU {i}: {torch.cuda.get_device_name(i)} ({mem_total} GB)")
        else:
            warn("CUDA 사용 불가 — CPU 모드로 실행 (속도 매우 느림)")
    except ImportError:
        warn("PyTorch 미설치 — GPU 상태 확인 불가")

    # LLM 사전 점검 (provider별)
    if llm_provider == "none":
        info("LLM provider=none — 에이전트는 규칙 기반 스텁으로 동작할 수 있습니다.")
    elif llm_provider == "vllm":
        v_ok, v_msg = _check_vllm(llm_base, llm_model)
        if v_ok:
            ok(f"vLLM [{llm_base}] — {v_msg}")
        else:
            warn(
                f"vLLM 점검 실패 [{llm_base}]: {v_msg}. "
                "에이전트가 LLM 없이 동작하거나 스텁으로 떨어질 수 있습니다."
            )
            info("  vLLM OpenAI API 서버가 떠 있는지, --served-model-name 이 설정 모델과 맞는지 확인하세요.")
    else:
        ollama_ok = _check_ollama(ollama_host, llm_model)
        if ollama_ok:
            ok(f"Ollama 연결됨 [{ollama_host}] — 모델 '{llm_model}' 확인")
        else:
            warn(
                f"Ollama 미응답 [{ollama_host}] 또는 모델 '{llm_model}' 없음. "
                "에이전트가 rule-based stub으로 동작합니다."
            )
            info(
                f"  Ollama 시작: OLLAMA_HOST={ollama_host.split(':')[0]} "
                f"OLLAMA_PORT={ollama_host.split(':')[-1]} ollama serve"
            )
            info(f"  모델 풀: ollama pull {llm_model}")

    # PyRosetta 확인
    try:
        import pyrosetta  # noqa: F401
        ok("PyRosetta import 성공")
    except ImportError:
        warn("PyRosetta 미설치 — Step06 (Rosetta 정제)가 mock으로 실행됩니다.")
        info("  conda activate bio-tools 후 실행하세요.")

    print()

    # ------------------------------------------------------------------
    # resume 검증
    # ------------------------------------------------------------------
    if args.resume and not args.run_id:
        fail("--resume 사용 시 --run-id가 필요합니다.")
        sys.exit(2)

    # ------------------------------------------------------------------
    # 오케스트레이터 초기화 및 실행
    # ------------------------------------------------------------------
    step_h("PIPELINE", "파이프라인 오케스트레이터 초기화")

    try:
        orchestrator = LocalPipelineOrchestrator(config_path=str(effective_config_path))
        ok(f"오케스트레이터 초기화 완료 (device={orchestrator.device})")
    except Exception as exc:
        fail(f"오케스트레이터 초기화 실패: {exc}")
        raise

    p(f"파이프라인 시작 — {max_iterations}회 반복 예정", color=BOLD + GREEN)
    t_start = time.monotonic()

    try:
        result: FinalResult = orchestrator.run(
            max_iterations=args.iterations,
            resume=args.resume,
            resume_run_id=args.run_id,
        )
    except KeyboardInterrupt:
        warn("\n사용자 중단 (Ctrl+C). 체크포인트가 저장되어 있으면 --resume으로 재개 가능합니다.")
        sys.exit(130)
    except Exception as exc:
        fail(f"파이프라인 실행 중 오류: {exc}")
        raise

    elapsed = time.monotonic() - t_start

    # ------------------------------------------------------------------
    # 결과 요약 출력
    # ------------------------------------------------------------------
    banner("PIPELINE COMPLETE", char="-", width=72)
    print(f"  {GREEN}Run ID:{RESET}        {result.run_id}")
    print(f"  {GREEN}Total iterations:{RESET} {result.total_iterations}")
    print(f"  {GREEN}Converged:{RESET}     {result.converged}")
    print(f"  {GREEN}Elapsed:{RESET}       {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  {GREEN}Final report:{RESET}  {result.final_report_path}")
    print()

    if result.best_candidates:
        print(f"  {BOLD}{CYAN}Top Candidates (by ddG):{RESET}")
        print(f"  {'Rank':>4}  {'seq_id':<20}  {'ddG':>10}  {'Iteration':>10}")
        print(f"  {'-'*50}")
        for rank, c in enumerate(result.best_candidates[:5], 1):
            print(
                f"  {rank:>4}  {str(c.get('seq_id', 'N/A')):<20}"
                f"  {c.get('ddg', 0.0):>10.2f}"
                f"  {str(c.get('iteration', '-')):>10}"
            )
    else:
        warn("최종 통과 후보 없음. QC 게이트 임계값을 확인하세요.")

    print()

    # 결과 JSON 저장
    output_dir = Path(pipeline_cfg.get("output_base_dir", "runs_local"))
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{result.run_id}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    ok(f"결과 요약 저장: {summary_path}")

    # 임시 effective config 정리
    try:
        effective_config_path.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
