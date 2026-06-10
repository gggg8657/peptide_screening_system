"""vLLM model hot-swap utility — multi-GPU support.

Manages up to 2 vLLM servers on separate GPUs for parallel model serving.
  Slot 0: GPU 2, port 8003
  Slot 1: GPU 3, port 8002 (default, backward-compatible)
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

CONDA_ENV = "vllm-server"
MAX_WAIT = 180  # seconds


@dataclass
class VLLMSlot:
    """A single vLLM server slot on a specific GPU."""
    gpu_id: int
    port: int
    model: Optional[str] = None
    pid: Optional[int] = None


# Two available slots
SLOTS: Dict[int, VLLMSlot] = {
    0: VLLMSlot(gpu_id=2, port=8003),
    1: VLLMSlot(gpu_id=3, port=8002),
}


def get_current_model(port: int) -> Optional[str]:
    """Check what model is currently loaded on a given port."""
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=3)
        data = json.loads(resp.read())
        models = data.get("data", [])
        return models[0].get("id") if models else None
    except Exception:
        return None


def _kill_slot(slot_id: int) -> None:
    """Kill vLLM on a specific slot using stored PID and GPU-targeted cleanup."""
    slot = SLOTS[slot_id]
    port = slot.port
    gpu_id = slot.gpu_id

    # 1. Find and kill API server process by port
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"], capture_output=True, text=True,
    )
    server_pids = set()
    if result.returncode == 0 and result.stdout.strip():
        for pid_str in result.stdout.strip().split("\n"):
            try:
                server_pids.add(int(pid_str))
            except ValueError:
                pass

    # 2. Find EngineCore/resource_tracker children via nvidia-smi for THIS GPU only
    gpu_pids = set()
    result = subprocess.run(
        ["nvidia-smi", f"--id={gpu_id}", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        for pid_str in result.stdout.strip().split("\n"):
            try:
                gpu_pids.add(int(pid_str.strip()))
            except ValueError:
                pass

    # 3. Kill entire process group if PID was started with setsid
    if slot.pid:
        try:
            os.killpg(os.getpgid(slot.pid), 9)
            logger.debug("Slot %d: killed process group of PID %d", slot_id, slot.pid)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    # 4. Kill individual PIDs (server + GPU-holding)
    all_pids = server_pids | gpu_pids
    for pid in all_pids:
        try:
            os.kill(pid, 9)
        except (ProcessLookupError, PermissionError):
            pass

    time.sleep(3)

    # 5. Retry: check GPU and kill any remaining processes (up to 3 attempts)
    for attempt in range(3):
        result = subprocess.run(
            ["nvidia-smi", f"--id={gpu_id}", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
            capture_output=True, text=True,
        )
        if not result.stdout.strip():
            break  # GPU is free
        for pid_str in result.stdout.strip().split("\n"):
            try:
                os.kill(int(pid_str.strip()), 9)
            except (ProcessLookupError, PermissionError, ValueError):
                pass
        time.sleep(2)

    slot.model = None
    slot.pid = None


def start_model(
    slot_id: int,
    model_hf_id: str,
    gpu_util: float = 0.9,
    max_model_len: int = 4096,
) -> bool:
    """Start a vLLM server on the specified slot.

    Args:
        slot_id: 0 (GPU 2, port 8003) or 1 (GPU 3, port 8002)
        model_hf_id: HuggingFace model ID
        gpu_util: GPU memory utilization (0.0-1.0)
        max_model_len: Maximum sequence length

    Returns:
        True if server started and healthy.
    """
    slot = SLOTS[slot_id]

    # Already loaded?
    current = get_current_model(slot.port)
    if current == model_hf_id:
        logger.info("Slot %d: model already loaded (%s)", slot_id, model_hf_id)
        slot.model = model_hf_id
        return True

    # Kill existing on this slot (GPU-targeted, won't affect other slot)
    logger.info("Slot %d: stopping current server (GPU %d, port %d)...", slot_id, slot.gpu_id, slot.port)
    _kill_slot(slot_id)

    # Wait for GPU memory to actually free (up to 15s)
    import subprocess as _sp
    for _wait in range(15):
        try:
            out = _sp.run(
                ["nvidia-smi", f"--id={slot.gpu_id}", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            mem_mb = int(out.stdout.strip())
            if mem_mb < 500:  # less than 500MB = free
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        logger.warning("Slot %d: GPU %d still has %dMB after kill — proceeding anyway", slot_id, slot.gpu_id, mem_mb)

    # Launch
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(slot.gpu_id)

    cmd = [
        "conda", "run", "--no-capture-output", "-n", CONDA_ENV,
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_hf_id,
        "--port", str(slot.port),
        "--trust-remote-code",
        "--max-model-len", "8192",
        "--gpu-memory-utilization", str(gpu_util),
    ]

    logger.info("Slot %d: starting vLLM %s (GPU %d, port %d)",
                slot_id, model_hf_id, slot.gpu_id, slot.port)
    proc = subprocess.Popen(
        cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        preexec_fn=os.setsid,  # new session → killpg kills entire tree
    )

    # Health check
    for i in range(MAX_WAIT // 2):
        time.sleep(2)
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode(errors="replace")[-500:]
            logger.error("Slot %d: vLLM died (code=%d): %s", slot_id, proc.returncode, stderr)
            return False
        try:
            resp = urllib.request.urlopen(f"http://localhost:{slot.port}/v1/models", timeout=3)
            data = json.loads(resp.read())
            loaded = data.get("data", [{}])[0].get("id", "")
            if loaded:
                slot.model = model_hf_id
                slot.pid = proc.pid
                logger.info("Slot %d: ready — %s (pid=%d, %ds)", slot_id, loaded, proc.pid, (i+1)*2)
                return True
        except Exception:
            if i % 15 == 14:
                logger.info("  slot %d still loading... (%ds)", slot_id, (i+1)*2)

    logger.error("Slot %d: timeout %ds — %s", slot_id, MAX_WAIT, model_hf_id)
    proc.kill()
    return False


def stop_slot(slot_id: int) -> None:
    """Stop the vLLM server on a specific slot."""
    _kill_slot(slot_id)
    logger.info("Slot %d: stopped", slot_id)


def stop_all() -> None:
    """Stop all vLLM servers."""
    for sid in SLOTS:
        stop_slot(sid)


# Backward-compatible single-GPU API
def swap_model(model_hf_id: str, port: int = 8002, **kwargs) -> bool:
    """Single-GPU swap (slot 1 = GPU 3). Backward compatible."""
    slot_id = 1 if port == 8002 else 0
    return start_model(slot_id, model_hf_id, **kwargs)
