"""
local_runner.py — 로컬 conda 환경에서 모델 스크립트를 서브프로세스로 실행

NIM API를 대체하는 로컬 실행 래퍼.
각 모델은 지정된 conda 환경에서 Python 스크립트로 실행되며,
stdout을 JSON으로 파싱해 결과를 반환한다.
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pipeline_local.core.config_loader import get_model_info, load_model_config

logger = logging.getLogger(__name__)


class RunnerError(Exception):
    """LocalModelRunner 실행 중 발생하는 기본 예외."""


class TimeoutError(RunnerError):
    """서브프로세스 타임아웃 초과."""


class NonZeroExitError(RunnerError):
    """서브프로세스가 비정상 종료코드로 종료됨."""

    def __init__(self, returncode: int, stderr: str) -> None:
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"프로세스가 exit code {returncode}로 종료되었습니다.\n"
            f"stderr:\n{stderr}"
        )


class JSONParseError(RunnerError):
    """stdout을 JSON으로 파싱하는 데 실패함."""

    def __init__(self, raw_output: str) -> None:
        self.raw_output = raw_output
        super().__init__(
            f"stdout을 JSON으로 파싱할 수 없습니다.\n"
            f"raw output (첫 500자):\n{raw_output[:500]}"
        )


class LocalModelRunner:
    """로컬 conda 환경에서 모델 스크립트를 실행하는 메인 러너.

    사용 예시::

        runner = LocalModelRunner()
        result = runner.run(
            model_name="esmfold",
            script_path="/path/to/predict.py",
            args=["--sequence", "ACDEFGHIKLMNPQRSTVWY"],
            input_files={"input.fasta": ">seq1\\nACDEFGHIKLMNPQRSTVWY\\n"},
        )
        print(result["plddt"])
    """

    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        """
        Parameters
        ----------
        config_path:
            model_paths.yaml 파일 경로. None이면 패키지 기본 경로를 사용.
        """
        self._config_path = config_path
        self._config = load_model_config(config_path)
        logger.debug("LocalModelRunner 초기화 완료. config: %s", config_path)

    # ------------------------------------------------------------------
    # wrapper_scripts 디렉토리 경로
    # ------------------------------------------------------------------
    _WRAPPER_DIR = Path(__file__).resolve().parent.parent / "wrapper_scripts"

    # 모델 이름 → wrapper 스크립트 매핑
    _WRAPPER_MAP = {
        "esmfold":        "run_esmfold.py",
        "rfdiffusion":    "run_rfdiffusion.py",
        "proteinmpnn":    "run_proteinmpnn.py",
        "boltz":          "run_boltz.py",
        "openfold3":      "run_openfold3.py",
        "diffpepbuilder": "run_diffpepbuilder.py",
        "genmol":         "run_genmol.py",
        "esm2":           "run_esm2.py",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        model_name: str,
        payload: dict | str | Path | list[str] | None = None,
        args: list[str] | None = None,
        script_path: str | Path | None = None,
        input_files: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """로컬 모델을 실행한다.

        두 가지 호출 패턴을 지원:

        **간편 호출** (step 파일용)::

            runner.run("esmfold", {"sequence": "ACDEF..."})

        payload dict를 JSON으로 직렬화해 wrapper script에 전달.

        **상세 호출** (직접 스크립트 지정)::

            runner.run("esmfold", script_path="...", args=["--seq", "ACDEF"])

        """
        # 간편 호출: payload가 dict면 자동으로 wrapper script + JSON 인자 구성
        if isinstance(payload, dict) and args is None:
            return self._run_with_payload(model_name, payload, timeout=timeout)

        # 상세 호출: 기존 시그니처 호환
        if script_path is None:
            raise ValueError("script_path 또는 payload(dict)를 지정해야 합니다.")
        if args is None:
            args = []
        return self._run_subprocess(
            model_name, script_path, args,
            input_files=input_files, timeout=timeout,
        )

    def _run_with_payload(
        self,
        model_name: str,
        payload: dict,
        timeout: Optional[int] = None,
    ) -> dict:
        """payload dict를 JSON 파일로 전달해 wrapper script를 실행한다."""
        wrapper_name = self._WRAPPER_MAP.get(model_name)
        if wrapper_name is None:
            raise ValueError(f"알 수 없는 모델: {model_name}. 지원: {list(self._WRAPPER_MAP)}")

        wrapper_path = self._WRAPPER_DIR / wrapper_name
        if not wrapper_path.exists():
            raise FileNotFoundError(f"Wrapper 스크립트 없음: {wrapper_path}")

        return self._run_subprocess(
            model_name=model_name,
            script_path=wrapper_path,
            args=["--input-json", "{tmpdir}/input_payload.json", "--output-dir", "{tmpdir}"],
            input_files={"input_payload.json": json.dumps(payload, ensure_ascii=False)},
            timeout=timeout,
        )

    def _run_subprocess(
        self,
        model_name: str,
        script_path: str | Path,
        args: list[str],
        input_files: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """conda 환경에서 Python 스크립트를 실행하고 JSON 결과를 반환한다.

        Returns
        -------
        dict
            스크립트 stdout을 JSON 파싱한 결과.

        Raises
        ------
        TimeoutError
            타임아웃 초과 시.
        NonZeroExitError
            비정상 종료코드 시.
        JSONParseError
            stdout JSON 파싱 실패 시.
        """
        model_info = get_model_info(model_name, self._config_path)
        effective_timeout = timeout if timeout is not None else model_info.get("timeout", 300)
        gpu_device = model_info.get("gpu_device", 0)

        tmpdir = Path(tempfile.mkdtemp(prefix=f"pipeline_local_{model_name}_"))
        logger.info(
            "[%s] 실행 시작. tmpdir=%s, timeout=%ds, GPU=%s",
            model_name, tmpdir, effective_timeout, gpu_device,
        )

        try:
            # 입력 파일을 임시 디렉토리에 저장
            if input_files:
                self._write_input_files(tmpdir, input_files)

            # args의 {tmpdir} 플레이스홀더를 실제 경로로 치환
            resolved_args = [
                a.replace("{tmpdir}", str(tmpdir)) for a in args
            ]

            cmd = self._build_command(
                conda_env=model_info["conda_env"],
                script_path=Path(script_path),
                args=resolved_args,
            )
            logger.debug("[%s] 실행 명령: %s", model_name, " ".join(cmd))

            env = self._build_env(gpu_device=gpu_device)
            result = self._execute(cmd, env=env, timeout=effective_timeout, model_name=model_name)

        finally:
            # 임시 디렉토리 정리 (오류 발생 시에도 반드시 삭제)
            shutil.rmtree(tmpdir, ignore_errors=True)
            logger.debug("[%s] tmpdir 정리 완료: %s", model_name, tmpdir)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_input_files(tmpdir: Path, input_files: dict[str, str]) -> None:
        """입력 파일 딕셔너리를 임시 디렉토리에 저장한다."""
        for filename, content in input_files.items():
            dest = tmpdir / filename
            # 중첩 디렉토리도 지원 (예: "subdir/input.fasta")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            logger.debug("입력 파일 작성: %s (%d bytes)", dest, len(content))

    @staticmethod
    def _build_command(
        conda_env: str,
        script_path: Path,
        args: list[str],
    ) -> list[str]:
        """conda run 명령 리스트를 생성한다.

        생성 형식::

            conda run -n {env} --no-capture-output python {script} {args...}
        """
        return [
            "conda", "run",
            "--no-capture-output",   # stdout/stderr를 그대로 전달
            "-n", conda_env,
            "python", str(script_path),
            *args,
        ]

    @staticmethod
    def _build_env(gpu_device: int | None = None) -> dict[str, str]:
        """서브프로세스에 전달할 환경 변수를 구성한다.

        gpu_device는 CUDA_VISIBLE_DEVICES 리매핑 인덱스:
        - 부모가 CUDA_VISIBLE_DEVICES=2,3이고 gpu_device=0이면 subprocess에 CUDA_VISIBLE_DEVICES=2
        - 부모가 CUDA_VISIBLE_DEVICES=2,3이고 gpu_device=1이면 subprocess에 CUDA_VISIBLE_DEVICES=3
        """
        env = os.environ.copy()
        if gpu_device is not None:
            # 부모 프로세스의 가시 GPU 목록을 기반으로 실제 물리 GPU ID 계산
            parent_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
            parent_devices = [d.strip() for d in parent_devices if d.strip()]
            if parent_devices and gpu_device < len(parent_devices):
                env["CUDA_VISIBLE_DEVICES"] = parent_devices[gpu_device]
            else:
                env["CUDA_VISIBLE_DEVICES"] = str(gpu_device)
        env["DGLBACKEND"] = "pytorch"
        env["TOKENIZERS_PARALLELISM"] = "false"
        env["OMP_NUM_THREADS"] = "4"
        env["HF_HUB_OFFLINE"] = "1"  # SSL 인증서 오류 방지: 캐시된 모델만 사용
        env["TRANSFORMERS_OFFLINE"] = "1"
        # conda 환경 변수 충돌 방지: CONDA_DEFAULT_ENV는 conda run이 관리
        return env

    def _execute(
        self,
        cmd: list[str],
        env: dict[str, str],
        timeout: int,
        model_name: str,
    ) -> dict:
        """서브프로세스를 실행하고 stdout을 JSON으로 파싱해 반환한다."""
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()  # zombie 방지
            raise TimeoutError(
                f"[{model_name}] {timeout}초 타임아웃 초과. "
                f"명령: {' '.join(cmd)}"
            )

        if proc.returncode != 0:
            logger.error(
                "[%s] 비정상 종료 (code=%d):\n%s",
                model_name, proc.returncode, stderr,
            )
            raise NonZeroExitError(
                returncode=proc.returncode,
                stderr=stderr,
            )

        stdout = stdout.strip()
        if stderr:
            logger.debug("[%s] stderr:\n%s", model_name, stderr)

        # stdout에서 JSON 블록 추출
        # 스크립트가 로그 메시지 + JSON을 섞어 출력하는 경우를 허용하기 위해
        # 마지막 JSON 오브젝트를 탐색한다.
        parsed = self._extract_json(stdout, model_name)
        logger.info("[%s] 실행 완료. 결과 키: %s", model_name, list(parsed.keys()))
        return parsed

    @staticmethod
    def _extract_json(stdout: str, model_name: str) -> dict:
        """stdout 텍스트에서 JSON 딕셔너리를 추출한다.

        전략:
        1. stdout 전체를 직접 파싱 시도.
        2. 실패 시 마지막 ``{`` ~ ``}`` 블록을 추출해 재시도.
        """
        # 1차 시도: 전체 stdout
        try:
            result = json.loads(stdout)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # 2차 시도: 마지막 JSON 오브젝트 블록 추출
        last_open = stdout.rfind("{")
        last_close = stdout.rfind("}")
        if last_open != -1 and last_close > last_open:
            candidate = stdout[last_open: last_close + 1]
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    logger.debug(
                        "[%s] stdout에서 JSON 블록 추출 성공 (offset %d~%d)",
                        model_name, last_open, last_close,
                    )
                    return result
            except json.JSONDecodeError:
                pass

        raise JSONParseError(raw_output=stdout)
