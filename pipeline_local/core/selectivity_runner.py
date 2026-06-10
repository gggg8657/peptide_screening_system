"""
selectivity_runner.py
=====================
SelectivityRunner — Boltz-2 + AlphaFoldDB MSA 기반 off-target 선택성 분석 클래스.

CIF/PDB 자동 감지, subprocess 격리 실행(conda boltz),
WSM/MSM/SR(selectivity ratio)/tier 계산을 통합 처리한다.

변경 이력:
    2026-05-12: PyRosetta FlexPepDock → Boltz-2 전환
                - conda 환경: bio-tools → boltz
                - timeout: 300 → 600 초
                - 근거: 50페어 검증에서 PyRosetta 전략 부적합 확인
                  (docs/selectivity_demo_20260511/report_final.html)
    2026-05-19: A-01 — 결합 포켓 좌표 인터페이스 추가
                - SelectivityRunner.__init__: binding_pocket_json 선택적 파라미터
                - load_binding_pocket(): JSON 파일 로드 헬퍼
                - get_pocket_center(): (x, y, z) 튜플 반환
                - get_gnina_config(): GNINA/AutoDock-GPU 설정 딕셔너리 반환

Public API:
    SelectivityRunner.dock_against_receptor(receptor_path, peptide_sequence, nstruct) -> float
    SelectivityRunner.run_selectivity_analysis(candidates, receptor_paths, sstr2_ddgs) -> list
    SelectivityRunner.load_binding_pocket(json_path) -> None
    SelectivityRunner.get_pocket_center() -> Optional[Tuple[float, float, float]]
    SelectivityRunner.get_gnina_config() -> Optional[Dict[str, float]]
    compute_full_selectivity(seq_id, sequence, sstr2_ddg, offtarget_ddgs) -> dict
    load_binding_pocket(json_path) -> dict  (모듈 수준 헬퍼)
"""
from __future__ import annotations

import json
import logging
import math
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 모듈 수준 헬퍼: 결합 포켓 JSON 로드
# ---------------------------------------------------------------------------

def load_binding_pocket(json_path: str) -> Dict[str, Any]:
    """결합 포켓 좌표 JSON 파일을 로드하여 딕셔너리를 반환한다.

    extract_binding_pocket.py 가 생성한 JSON 파일을 읽어
    center_x/center_y/center_z/radius/gnina_config 를 담은 딕셔너리를 반환한다.

    Args:
        json_path: binding_pocket_SSTR2.json 파일 경로

    Returns:
        포켓 정보 딕셔너리 (center_x, center_y, center_z, radius, gnina_config 등)

    Raises:
        FileNotFoundError: json_path 파일이 없는 경우
        ValueError: 필수 키(center_x, center_y, center_z)가 없는 경우
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"binding_pocket JSON 파일을 찾을 수 없습니다: {json_path}")

    with open(path, "r", encoding="utf-8") as fh:
        data: Dict[str, Any] = json.load(fh)

    for key in ("center_x", "center_y", "center_z"):
        if key not in data:
            raise ValueError(
                f"binding_pocket JSON에 필수 키 '{key}'가 없습니다: {json_path}"
            )

    return data

# ---------------------------------------------------------------------------
# 열역학 상수: RT at 310 K (체온, R = 1.987e-3 kcal/mol/K)
# ---------------------------------------------------------------------------
_RT_KCAL = 0.616  # kcal/mol

# Tier 임계값 (WSM 기준, 단위: kcal/mol)
# WSM = max(delta_ddg) — 가장 선택성이 낮은 off-target 기준
_TIER_THRESHOLDS = [
    (3, -3.0),  # wsm <= -3.0 → tier 3 (최고 선택성)
    (2, -2.0),  # wsm <= -2.0 → tier 2
    (1, -1.5),  # wsm <= -1.5 → tier 1
    (0, None),  # 나머지  → tier 0
]

# ---------------------------------------------------------------------------
# Selectivity 계산 헬퍼 (라우터와 공유)
# ---------------------------------------------------------------------------

def compute_full_selectivity(
    sstr2_ddg: float,
    offtarget_ddgs: Dict[str, Optional[float]],
    seq_id: str = "",
    sequence: str = "",
) -> Dict[str, Any]:
    """WSM/MSM/Selectivity Ratio/Tier를 포함한 완전한 selectivity 결과를 반환한다.

    Args:
        seq_id:         후보 식별자
        sequence:       펩타이드 아미노산 서열
        sstr2_ddg:      SSTR2 도킹 ddG (kcal/mol, 낮을수록 강한 결합)
        offtarget_ddgs: off-target 수용체별 ddG. None은 측정 불가.

    Returns:
        완전한 결과 딕셔너리 (JSON 직렬화 가능)

    Notes:
        - delta_ddg = sstr2_ddg - target_ddg
          음수(SSTR2가 더 강하게 결합) → 선택적
        - WSM = max(delta_ddg values)
          가장 선택성이 낮은(off-target과 가장 비슷한) 케이스
        - Selectivity Ratio = exp(-delta_ddg / RT)
          RT = 0.616 kcal/mol (310 K)
        - Tier: wsm <= -3.0 → 3, <= -2.0 → 2, <= -1.5 → 1, else 0
        - passed: wsm <= -2.0 (tier >= 2)
    """
    # delta_ddg 계산 (측정된 off-target만)
    delta_ddg: Dict[str, float] = {}
    for target, ddg in offtarget_ddgs.items():
        if ddg is not None:
            delta_ddg[target] = sstr2_ddg - ddg

    # WSM, MSM
    if delta_ddg:
        wsm = max(delta_ddg.values())  # 가장 선택성이 낮은(덜 음수) 케이스
        msm = sum(delta_ddg.values()) / len(delta_ddg)
    else:
        wsm = 0.0
        msm = 0.0

    # Tier 결정
    tier = 0
    for t, threshold in _TIER_THRESHOLDS:
        if threshold is None or wsm <= threshold:
            tier = t
            break

    passed = wsm <= -2.0

    # Selectivity Ratio = exp(-delta_ddg / RT)
    selectivity_ratios: Dict[str, int] = {}
    for target, ddg_delta in delta_ddg.items():
        ratio = math.exp(-ddg_delta / _RT_KCAL)
        selectivity_ratios[target] = round(ratio)

    return {
        "seq_id": seq_id,
        "sequence": sequence,
        "sstr2_ddg": sstr2_ddg,
        "offtarget_ddg": {k: v for k, v in offtarget_ddgs.items() if v is not None},
        "delta_ddg": delta_ddg,
        "wsm": round(wsm, 3),
        "msm": round(msm, 3),
        "selectivity_ratios": selectivity_ratios,
        "tier": tier,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# SelectivityRunner
# ---------------------------------------------------------------------------

class SelectivityRunner:
    """Boltz-2 + AlphaFoldDB MSA를 subprocess로 실행하여 off-target ddG를 계산한다.

    offtarget_dock.py 가 Boltz-2 기반으로 재작성되어
    conda 환경 기본값이 "boltz"로 변경되었다. (구: "bio-tools" / PyRosetta)

    A-01 추가: binding_pocket_json 파라미터로 SSTR2 결합 포켓 좌표를 전달할 수 있다.
    Boltz-2 자체는 binding box 불필요이지만 향후 GNINA/AutoDock-GPU 병용 시 사용된다.

    Args:
        conda_env:           Boltz-2가 설치된 conda 환경명 (기본 "boltz")
        nstruct:             생성 구조 수 (Boltz --diffusion_samples에 대응, 기본 1)
        timeout:             subprocess 타임아웃 (초, 기본 600)
        repo_root:           레포지토리 루트 경로. None이면 이 파일 기준으로 자동 감지.
        binding_pocket_json: SSTR2 결합 포켓 좌표 JSON 파일 경로 (선택).
                             extract_binding_pocket.py 출력 파일.
                             None이면 포켓 좌표 미사용 (Boltz-2 블라인드 도킹 모드).
    """

    def __init__(
        self,
        conda_env: str = "boltz",
        nstruct: int = 1,
        timeout: int = 600,
        repo_root: Optional[Path] = None,
        binding_pocket_json: Optional[str] = None,
    ) -> None:
        self.conda_env = conda_env
        self.nstruct = nstruct
        self.timeout = timeout
        # scripts/offtarget_dock.py 경로
        _root = repo_root or Path(__file__).parent.parent
        self.script_path = _root / "scripts" / "offtarget_dock.py"
        # conda 실행 파일 경로 자동 감지
        self.conda_bin = self._find_conda()
        # 결합 포켓 좌표 (선택적 로드)
        self._pocket_data: Optional[Dict[str, Any]] = None
        if binding_pocket_json is not None:
            self.load_binding_pocket(binding_pocket_json)

    @staticmethod
    def _find_conda() -> str:
        """PATH 또는 일반적인 설치 경로에서 conda 바이너리를 찾는다."""
        import shutil
        found = shutil.which("conda")
        if found:
            return found
        for base in (Path.home() / "miniforge3", Path.home() / "miniconda3", Path.home() / "anaconda3"):
            for p in (base / "condabin" / "conda", base / "bin" / "conda"):
                if p.exists():
                    return str(p)
        return "conda"  # fallback

    # ------------------------------------------------------------------
    # 결합 포켓 인터페이스 (A-01)
    # ------------------------------------------------------------------

    def load_binding_pocket(self, json_path: str) -> None:
        """SSTR2 결합 포켓 좌표 JSON 파일을 로드한다.

        extract_binding_pocket.py 가 생성한 binding_pocket_SSTR2.json 을
        읽어 self._pocket_data 에 저장한다.

        Args:
            json_path: binding_pocket_SSTR2.json 파일 경로

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: 필수 키(center_x, center_y, center_z)가 없는 경우
        """
        self._pocket_data = load_binding_pocket(json_path)
        logger.info(
            "[SelectivityRunner] 결합 포켓 로드: center=(%.3f, %.3f, %.3f), radius=%.3f Å",
            self._pocket_data["center_x"],
            self._pocket_data["center_y"],
            self._pocket_data["center_z"],
            self._pocket_data.get("radius", 0.0),
        )

    def get_pocket_center(self) -> Optional[Tuple[float, float, float]]:
        """SSTR2 결합 포켓 중심 좌표 (x, y, z)를 반환한다.

        결합 포켓 데이터가 로드되지 않은 경우 None을 반환한다.
        Boltz-2는 binding box 불필요이므로 현재는 GNINA/AutoDock-GPU 연동용.

        Returns:
            (center_x, center_y, center_z) 튜플 또는 None
        """
        if self._pocket_data is None:
            return None
        return (
            float(self._pocket_data["center_x"]),
            float(self._pocket_data["center_y"]),
            float(self._pocket_data["center_z"]),
        )

    def get_gnina_config(self) -> Optional[Dict[str, float]]:
        """GNINA/AutoDock-GPU 도킹 박스 설정 딕셔너리를 반환한다.

        결합 포켓 데이터가 로드되지 않은 경우 None을 반환한다.

        Returns:
            {"center_x": float, "center_y": float, "center_z": float,
             "size_x": float, "size_y": float, "size_z": float} 또는 None
        """
        if self._pocket_data is None:
            return None
        gnina_cfg = self._pocket_data.get("gnina_config")
        if gnina_cfg:
            return dict(gnina_cfg)
        # gnina_config 키가 없으면 center + box_size로 재구성
        box = float(self._pocket_data.get("box_size", 30.0))
        return {
            "center_x": float(self._pocket_data["center_x"]),
            "center_y": float(self._pocket_data["center_y"]),
            "center_z": float(self._pocket_data["center_z"]),
            "size_x": box,
            "size_y": box,
            "size_z": box,
        }

    # ------------------------------------------------------------------
    # 단일 도킹
    # ------------------------------------------------------------------

    def dock_against_receptor(
        self,
        receptor_path: str,
        peptide_sequence: str,
        nstruct: Optional[int] = None,
        output_dir: Optional[str] = None,
    ) -> float:
        """Boltz-2 + AlphaFoldDB MSA로 ddG 프록시를 계산한다.

        CIF/PDB 형식을 자동으로 감지하여 offtarget_dock.py subprocess에 전달한다.
        subprocess는 conda boltz 환경에서 실행된다.

        반환값 "ddg" = -100 * iPTM (하위 호환 유지):
            - iPTM 높음(강결합) → ddg 큰 음수 (예: iptm=0.95 → ddg=-95)
            - iPTM 낮음(약결합) → ddg 0에 가까움 (예: iptm=0.1 → ddg=-10)

        Args:
            receptor_path:    수용체 구조 경로 (CIF/PDB)
            peptide_sequence: 펩타이드 아미노산 서열 (1-letter code)
            nstruct:          생성 구조 수. None이면 self.nstruct 사용.
            output_dir:       최적 구조 PDB 저장 경로 (선택)

        Returns:
            float: ddG 프록시 (-100 * iPTM, kcal/mol)

        Raises:
            RuntimeError: subprocess 실패 또는 JSON 파싱 실패
        """
        n = nstruct if nstruct is not None else self.nstruct
        cmd = [
            self.conda_bin, "run", "--no-capture-output", "-n", self.conda_env,
            "python", str(self.script_path),
            "--receptor", receptor_path,
            "--sequence", peptide_sequence,
            "--nstruct", str(n),
        ]
        if output_dir:
            cmd.extend(["--output-dir", output_dir])

        logger.debug("[SelectivityRunner] 실행: %s", " ".join(cmd[-8:]))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"offtarget_dock.py 실패 (rc={proc.returncode}): "
                f"{proc.stderr[:300]}"
            )

        stdout = proc.stdout.strip()
        if not stdout:
            raise RuntimeError("offtarget_dock.py stdout이 비어 있습니다.")

        # PyRosetta 로그 이후 마지막 JSON 줄 파싱
        result: Optional[Dict[str, Any]] = None
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue

        if result is None:
            raise RuntimeError(
                f"offtarget_dock.py 출력에서 JSON을 찾지 못했습니다: "
                f"{stdout[:200]}"
            )

        if "error" in result:
            raise RuntimeError(f"offtarget_dock.py 오류: {result['error']}")

        return float(result["ddg"])

    # ------------------------------------------------------------------
    # 전체 selectivity 분석
    # ------------------------------------------------------------------

    def run_selectivity_analysis(
        self,
        candidates: List[Dict[str, Any]],
        receptor_paths: Dict[str, Optional[str]],
        sstr2_ddgs: Dict[str, float],
        job_dir: Optional[Path] = None,
        status_callback: Optional[Callable[[str, str, Optional[float]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """전체 selectivity 분석을 순차 실행하고 결과 리스트를 반환한다.

        Args:
            candidates:       후보 목록 [{"seq_id": str, "sequence": str}, ...]
            receptor_paths:   off-target 수용체 경로 {"sstr1": str|None, ...}
            sstr2_ddgs:       SSTR2 ddG {"seq_id": float, ...}
            job_dir:          도킹 결과 PDB 저장 루트 (선택)
            status_callback:  진행 상태 콜백 fn(seq_id, receptor_name, ddg)

        Returns:
            List of compute_full_selectivity() 결과 딕셔너리
        """
        results: List[Dict[str, Any]] = []

        for candidate in candidates:
            seq_id: str = candidate["seq_id"]
            sequence: str = candidate.get("sequence", "")
            sstr2_ddg: float = sstr2_ddgs.get(seq_id, -5.0)

            offtarget_ddgs: Dict[str, Optional[float]] = {}

            for receptor_name, receptor_path in receptor_paths.items():
                if not receptor_path or not Path(receptor_path).exists():
                    logger.debug(
                        "[SelectivityRunner] %s 경로 없음 — 건너뜀", receptor_name
                    )
                    offtarget_ddgs[receptor_name] = None
                    if status_callback:
                        status_callback(seq_id, receptor_name, None)
                    continue

                # 출력 디렉토리 준비
                dock_out_dir: Optional[str] = None
                if job_dir:
                    dock_out_dir = str(job_dir / seq_id / receptor_name)
                    Path(dock_out_dir).mkdir(parents=True, exist_ok=True)

                try:
                    ddg = self.dock_against_receptor(
                        receptor_path=receptor_path,
                        peptide_sequence=sequence,
                        output_dir=dock_out_dir,
                    )
                    offtarget_ddgs[receptor_name] = ddg
                    logger.info(
                        "[SelectivityRunner] %s vs %s → %.3f kcal/mol",
                        seq_id, receptor_name, ddg,
                    )
                except Exception as exc:
                    logger.warning(
                        "[SelectivityRunner] 도킹 실패 (%s vs %s): %s",
                        seq_id, receptor_name, exc,
                    )
                    offtarget_ddgs[receptor_name] = None

                if status_callback:
                    status_callback(seq_id, receptor_name, offtarget_ddgs[receptor_name])

            result = compute_full_selectivity(
                seq_id=seq_id,
                sequence=sequence,
                sstr2_ddg=sstr2_ddg,
                offtarget_ddgs=offtarget_ddgs,
            )
            results.append(result)

        return results
