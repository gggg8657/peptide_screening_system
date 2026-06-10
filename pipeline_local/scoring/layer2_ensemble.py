"""Layer 2 혈중 반감기 — 로컬 PEPlife2 학습 GAT 회귀 (격리 conda 환경).

`ensemble_router.route_halflife_prediction` 이 Layer 2를 가리키면 이 모듈을 쓴다.

체크포인트·스크립트: `_workspace/pepmsnd_local/` (레포 루트 기준).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pipeline_local.scripts.pharmacology_guards import (
    attach_confidence,
    check_pepmsnd_local_applicability,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORK = _REPO_ROOT / "_workspace" / "pepmsnd_local"
_DEFAULT_CONDA = _WORK / ".conda_env"
_DEFAULT_CKPT = _WORK / "checkpoints" / "pepmsnd_peplife2_20260520_0723.pth"
_PRED = _WORK / "scripts" / "predict_halflife_checkpoint.py"

TPP_B_MIN_HOURS = 24.0
TPP_C_MIN_HOURS = 72.0


def infer_ss_bond_positions(sequence: str) -> Optional[Tuple[int, int]]:
    """Cys가 2개 이상이면 첫·마지막 Cys를 이황화로 가정 (1-indexed)."""
    s = sequence.upper().strip()
    cys = [i + 1 for i, a in enumerate(s) if a == "C"]
    if len(cys) >= 2:
        return (cys[0], cys[-1])
    return None


def compute_layer2_halflife(
    sequence: str,
    *,
    has_dota: bool = False,
    conda_env: Optional[Path] = None,
    checkpoint: Optional[Path] = None,
    cuda_visible_devices: Optional[str] = None,
    timeout_sec: int = 120,
) -> Dict[str, Any]:
    """로컬 체크포인트로 `half_life_hours` 추정. 실패 시 None + warnings."""
    applicability = check_pepmsnd_local_applicability(sequence, has_dota=has_dota)
    out: Dict[str, Any] = {
        "layer": 2,
        "ensemble_halflife_hours": None,
        "endpoint_path": "pepmsnd_local_halflife_hours",
        "applicability": applicability,
        "warnings": [],
        "tool_status": {"pepmsnd_local": "not_run"},
    }

    if has_dota:
        out["warnings"].append("DOTA 후보는 Layer 3 라우팅 — 로컬 PEPlife2-GAT OOD")
        out["tool_status"]["pepmsnd_local"] = "skipped_dota"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    env_dir = Path(conda_env or _DEFAULT_CONDA)
    ckpt = Path(checkpoint or _DEFAULT_CKPT)
    pred = Path(_PRED)

    if not env_dir.is_dir():
        out["warnings"].append(f"conda env 없음: {env_dir}")
        out["tool_status"]["pepmsnd_local"] = "missing_env"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out
    if not ckpt.is_file():
        out["warnings"].append(f"checkpoint 없음: {ckpt}")
        out["tool_status"]["pepmsnd_local"] = "missing_checkpoint"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out
    if not pred.is_file():
        out["warnings"].append(f"predict script 없음: {pred}")
        out["tool_status"]["pepmsnd_local"] = "missing_script"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    conda_exe = shutil.which("conda")
    if not conda_exe:
        out["warnings"].append("conda 실행 파일 없음 — PATH 확인")
        out["tool_status"]["pepmsnd_local"] = "missing_conda"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    cmd = [
        conda_exe,
        "run",
        "-p",
        str(env_dir),
        "python",
        str(pred),
        "--checkpoint",
        str(ckpt),
        "--sequence",
        sequence.strip(),
    ]
    ss = infer_ss_bond_positions(sequence)
    if ss:
        cmd += ["--ss-bond", f"{ss[0]},{ss[1]}"]

    sub_env = os.environ.copy()
    if cuda_visible_devices is not None:
        sub_env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=sub_env,
            cwd=str(_WORK),
        )
    except subprocess.TimeoutExpired:
        out["warnings"].append(f"predict 타임아웃 ({timeout_sec}s)")
        out["tool_status"]["pepmsnd_local"] = "timeout"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[:2000]
        out["warnings"].append(f"predict 실패 rc={proc.returncode}: {err}")
        out["tool_status"]["pepmsnd_local"] = "error"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    try:
        payload = json.loads(proc.stdout.strip())
    except json.JSONDecodeError as e:
        out["warnings"].append(f"JSON 파싱 실패: {e}; stdout={proc.stdout[:500]!r}")
        out["tool_status"]["pepmsnd_local"] = "bad_json"
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    if not payload.get("ok"):
        out["warnings"].append(f"SMILES/추론 실패: {payload.get('error', payload)}")
        out["tool_status"]["pepmsnd_local"] = str(payload.get("error", "failed"))
        out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
        return out

    hours = float(payload["half_life_hours"])
    out["ensemble_halflife_hours"] = hours
    out["raw_local_prediction"] = payload
    out["passes_tpp_b_ge_24h"] = hours >= TPP_B_MIN_HOURS
    out["passes_tpp_c_ge_72h"] = hours >= TPP_C_MIN_HOURS
    out["tool_status"]["pepmsnd_local"] = "ok"
    out["warnings"].append(
        "저신뢰(P4): 실측 test R²<0 — screening 순위 전용, 절대 t½ 보고 금지"
    )
    out.update(attach_confidence(out, "pepmsnd_local_halflife_hours"))
    return out
