"""
step05c_boltz_cross.py
======================
Step 05c: Boltz-2 기반 Selectivity Cross-Validation (선택성 교차 검증)

SSTR2 도킹/QC 통과 후보를 Boltz-2로 SSTR1/2/3/4/5 전체에 대해 예측하여
iPTM 매트릭스를 산출하고 selectivity margin으로 Tier 분류한다.

우회 전략 (KAERI 내부망 ColabFold 차단 환경):
  1. 수용체 MSA: AlphaFoldDB (alphafold.ebi.ac.uk/files/msa/AF-{UP}-F1-msa_v6.a3m)
  2. 펩타이드: self-only a3m (>query\\n<seq>\\n)
  3. CLI 옵션: --no_kernels --num_workers 0

검증 근거:
  - SST-14 wild × SSTR2: iPTM 0.975 (geometry 신뢰성 입증)
  - 50쌍 batch 25분 완료 (페어당 ~30초)
  - docs/boltz2_offline_workaround.md 참조

⚠️ iPTM 해석 한계 (HEURISTIC-PARTIAL):
  iPTM은 *구조 geometry 신뢰도*이며 *결합 친화도(Ki/Kd) 또는 selectivity 순위의 비례 proxy 아님*.
  SST-14 vs SSTR1~5 실측 검증(2026-05-12):
    수용체    Ki(nM)   iPTM    Ki순위   iPTM순위
    SSTR1     0.4      0.975     3        1
    SSTR2     0.2      0.946     1        4   ← 목표지만 iPTM 4위
    SSTR3     0.8      0.958     4        2
    SSTR4     1.6      0.956     5        3
    SSTR5     0.3      0.913     2        5
    → 순위 일치 0/5 (Spearman ρ ≈ -0.3)
  본 모듈의 selectivity_margin 분류는 *geometry 신뢰도 기반 1차 스크리닝*이며
  정량 선택성 평가는 다음 중 하나로 *반드시* 확정해야 함:
    - FEP (Free Energy Perturbation)
    - MM-GBSA / MM-PBSA
    - 실측 Ki radioligand binding assay (cand03 wetlab path 참고)
  근거: _workspace/release/msa-routing-crosscheck-synthesis-2026-05-12.md §3 L3

Tier 분류 (Δ = selectivity_margin = iPTM(SSTR2) - max(iPTM(off-target))):
    T3: Δ ≥  0.03  (강한 SSTR2 선택성)
    T2: 0.00 ≤ Δ < 0.03  (유의미한 SSTR2 선택성)
    T1: -0.03 ≤ Δ < 0.00  (약한 off-target 우세, 주의)
    T0: Δ  < -0.03  (off-target 우세, 탈락)

Public API:
    run_boltz_cross_validation(candidates, offtarget_receptors, sstr2_receptor, config)
        -> Step05cOutput
    predict_pair(seq_id, sequence, receptor_name, receptor_seq, msa_dir, config)
        -> float  (iPTM)
    classify_tier(margin, thresholds) -> str
    download_alphafold_msa(uniprot_id, dest_dir, timeout) -> Path
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from pipeline_local.schemas.io_schemas import (
    BoltzSelectivityResult,
    DockingResult,
    Step05cOutput,
)

# ---------------------------------------------------------------------------
# UniProt 매핑 및 수용체 시퀀스 (isoform 1, reviewed)
# ---------------------------------------------------------------------------

UNIPROT_MAP: Dict[str, str] = {
    "SSTR1": "P30872",
    "SSTR2": "P30874",
    "SSTR3": "P32745",
    "SSTR4": "P31391",
    "SSTR5": "P35346",
}

# Uniprot reviewed canonical isoform 시퀀스 — run_boltz_batch.py 검증 완료
SSTR_SEQUENCES: Dict[str, str] = {
    "SSTR1": (
        "MFPNGTASSPSSSPSPSPGSCGEGGGSRGPGAGAADGMEEPGRNASQNGTLSEGQGSAILISFIYSVVCLVGLCGNSMVIYVILR"
        "YAKMKTATNIYILNLAIADELLMLSVPFLVTSTLLRHWPFGALLCRLVLSVDGINQFTSIFCLTVMSVDRYLAVVHPTRSARWRT"
        "APVARTVSAAVWVASAVVVLPVVVFSGVPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLIVVKVRSAGRRV"
        "WAPSCQRRRRSERRVTRMVVAVVALFVLCWMPFYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFR"
        "RVLLRPSRRVRSQEPTVGPPEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTSDPAK"
        "PSPHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR2": (
        "MDMADEPLNGSHTWLSIPFDLNGSVVSTNTSNQTEPYYDLTSNAVLTFIYFVVCIIGLCGNTLVIYVILRYAKMKTITNIYILNL"
        "AIADELFMLGLPFLAMQVALVHWPFGKAICRVVMTVDGINQFTSIFCLTVMSIDRYLAVVHPIKSAKWRRPRTAKMITMAVWGVS"
        "LLVILPIMIYAGLRSNQWGRSSCTINWPGESGAWYTGFIIYTFILGFLVPLTIICLCYLFIIIKVKSSGIRVGSSKRKKSEKKVT"
        "RMVSIVVAVFIFCWLPFYIFNVSSVSMAISPTPALKGMFDFVVVLTYANSCANPILYAFLSDNFKKSFQNVLCLVKVSGTDDGER"
        "SDSKQDKSRLNETTETQRTLLNGDLQTSI"
    ),
    "SSTR3": (
        "MDMLHPSSVSTTSEPENASSAWPPDATLGNVSAGPSPAGLAVSGVLIPLVYLVVCVVGLLGNSLVIYVVLRHTASPSVTNVYILNL"
        "ALADELFMLGLPFLAAQNALSYWPFGSLMCRLVMAVDGINQFTSIFCLTVMSVDRYLAVVHPTRSARWRTAPVARTVSAAVWVASA"
        "VVVLPVVVFSGVPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLIVVKVRSAGRRVWAPSCQRRRRSERRVTRM"
        "VVAVVALFVLCWMPFYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFRRVLLRPSRRVRSQEPTVGP"
        "PEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTSDPAKPSPHSGGGTPAHRGSAGSALA"
        "QTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR4": (
        "MSAPSTLPPGGEEGLGTAWPSAANASSAPAEAEEAVAGPGDARAAGMVAIQCIYALVCLVGLVGNALVIFVILRYAKMKTATNIYLLN"
        "LAVADELFMLSVPFVASSAALRHWPFGSVLCRAVLSVDGLNMFTSVFCLTVLSVDRYVAVVHPLRAATYRRPSVAKLINLGVWLASL"
        "LVTLPIAIFADTRPARGGEAVACNLQWPHPAWSAVFVVYTFLLGFLLPVGAICLCYVLIVVKMRMVALKAGWQQRKRSERKITLMVM"
        "MVVMVFVICWMPFYVVNLVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFRRVLLRPSRRVRSQEPTVGPPEK"
        "TEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTSDPAKPSPHSGGGTPAHRGSAGSALAQTQ"
        "VDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR5": (
        "MEPLFPASTPSWNASSPGAASGGGDNRTLVGPAPSAGARAVLVPVLYLLVCAAGLGGNTLVIYVVLRFATVTNIYILNLAVADVLYML"
        "GLPFLATQNAASFWPFGSLLCRTVIAVDGFNQFTSIFCLTVMSVDRYLAVVHPTRSARWRTAPVARTVSAAVWVASAVVVLPVVVFSG"
        "VPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLIVVKVRSAGRRVWAPSCQRRRRSERRVTRMVVAVVALFVLCWMP"
        "FYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFRRVLLRPSRRVRSQEPTVGPPEKTEEDDEEDEEGGG"
        "EEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTSDPAKPSPHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALA"
        "QTQVDTHTKCS"
    ),
}

# 기본 Tier 임계값 (Δ = iPTM(SSTR2) - max(iPTM(off-target)))
DEFAULT_TIER_THRESHOLDS: Dict[str, float] = {
    "T3": 0.03,
    "T2": 0.00,
    "T1": -0.03,
}

# AlphaFoldDB MSA 다운로드 URL 패턴
_AF_MSA_URL_TEMPLATE = (
    "https://alphafold.ebi.ac.uk/files/msa/AF-{uniprot}-F1-msa_v6.a3m"
)
_AF_API_URL_TEMPLATE = (
    "https://alphafold.ebi.ac.uk/api/prediction/{uniprot}"
)

# filename safety
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-\.]+$")


def _safe_id(value: str, field: str = "id") -> str:
    """path-unsafe 문자 검사."""
    if not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"Unsafe characters in {field!r}: {value!r}. "
            "Only alphanumerics, underscores, hyphens, and dots are allowed."
        )
    return value


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_boltz_cross_validation(
    candidates: List[DockingResult],
    offtarget_receptors: List[Dict[str, Any]],
    sstr2_receptor: Dict[str, Any],
    config: Dict[str, Any],
) -> Step05cOutput:
    """Boltz-2 기반 selectivity cross-validation.

    Args:
        candidates: step05/step05b의 docking 결과 (DockingResult list)
        offtarget_receptors: SSTR1/3/4/5 정보 (dict with keys: name, uniprot)
        sstr2_receptor: SSTR2 정보 (기준) (dict with keys: name, uniprot)
        config: {
            "alphafold_msa_dir": "runs_local/.../alphafold_receptors",
            "boltz_env": "boltz",
            "cuda_device": 3,
            "tier_thresholds": {"T3": 0.03, "T2": 0.0, "T1": -0.03},
            "pair_timeout": 600,        # 페어당 timeout 초
            "checkpoint_interval": 5,   # partial_results.json 저장 주기
            "work_dir": "runs_local/step05c",
        }

    Returns:
        Step05cOutput with iPTM matrix + selectivity tier
    """
    af_msa_dir = Path(config.get("alphafold_msa_dir", "runs_local/alphafold_receptors"))
    boltz_env = config.get("boltz_env", "boltz")
    cuda_device = int(config.get("cuda_device", 3))
    tier_thresholds = config.get("tier_thresholds", DEFAULT_TIER_THRESHOLDS)
    pair_timeout = int(config.get("pair_timeout", 600))
    checkpoint_interval = int(config.get("checkpoint_interval", 5))
    work_dir = Path(config.get("work_dir", "runs_local/step05c"))
    work_dir.mkdir(parents=True, exist_ok=True)

    af_msa_dir.mkdir(parents=True, exist_ok=True)

    # 수용체 목록 구성 (SSTR2 포함 전체)
    all_receptors: List[Dict[str, Any]] = [sstr2_receptor] + list(offtarget_receptors)
    sstr2_name = sstr2_receptor.get("name", "SSTR2")

    logger.info(
        "[Step05c] 후보 %d개 × 수용체 %d개 = 총 %d 페어",
        len(candidates),
        len(all_receptors),
        len(candidates) * len(all_receptors),
    )

    # 수용체 MSA 사전 준비
    receptor_msa_paths: Dict[str, Path] = {}
    for rec in all_receptors:
        rec_name = rec.get("name", "")
        uniprot_id = rec.get("uniprot", UNIPROT_MAP.get(rec_name, ""))
        if not uniprot_id:
            logger.warning("[Step05c] 수용체 %s UniProt ID 없음 — 스킵", rec_name)
            continue
        msa_path = _ensure_receptor_msa(
            uniprot_id=uniprot_id,
            receptor_name=rec_name,
            af_msa_dir=af_msa_dir,
        )
        if msa_path is not None:
            receptor_msa_paths[rec_name] = msa_path
        else:
            logger.warning("[Step05c] 수용체 %s MSA 준비 실패 — 해당 수용체 스킵", rec_name)

    # checkpoint 파일 — 이미 완료된 페어 로드
    checkpoint_file = work_dir / "partial_results.json"
    completed_pairs: Dict[str, Dict[str, Any]] = {}
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, encoding="utf-8") as f:
                completed_pairs = json.load(f)
            logger.info("[Step05c] checkpoint 로드: %d 페어 완료", len(completed_pairs))
        except Exception as e:
            logger.warning("[Step05c] checkpoint 로드 실패: %s", e)

    # 페어별 iPTM 매트릭스 수집
    # iptm_matrix[seq_id][receptor_name] = float
    iptm_matrix: Dict[str, Dict[str, Optional[float]]] = {}
    pair_count = 0
    total_pairs = len(candidates) * len(all_receptors)

    # F-06 fix: candidate에 sequence 필드가 없을 때 config.sequence_map fallback 지원
    # (DockingResult dataclass에는 sequence 필드가 없음 — step03b variants에서 매핑 필요)
    sequence_map = config.get("sequence_map", {}) if isinstance(config, dict) else {}

    for candidate in candidates:
        seq_id = getattr(candidate, "seq_id", getattr(candidate, "candidate_id", "unknown"))
        sequence = getattr(candidate, "sequence", "")
        if not sequence and seq_id in sequence_map:
            sequence = sequence_map[seq_id]
            logger.debug("[Step05c] %s sequence resolved via sequence_map", seq_id)
        if not sequence:
            logger.warning("[Step05c] 후보 %s sequence 없음 — 스킵 (sequence_map fallback도 부재)", seq_id)
            continue

        if seq_id not in iptm_matrix:
            iptm_matrix[seq_id] = {}

        for rec in all_receptors:
            rec_name = rec.get("name", "")
            pair_key = f"{seq_id}__{rec_name}"
            pair_count += 1

            if rec_name not in receptor_msa_paths:
                logger.debug("[Step05c] %s MSA 없음 — 스킵", rec_name)
                iptm_matrix[seq_id][rec_name] = None
                continue

            # checkpoint에 이미 완료된 페어는 스킵
            if pair_key in completed_pairs:
                cached = completed_pairs[pair_key]
                iptm_matrix[seq_id][rec_name] = cached.get("iptm")
                logger.debug(
                    "[Step05c] [%d/%d] SKIP (cached) %s × %s iPTM=%.3f",
                    pair_count, total_pairs, seq_id, rec_name,
                    cached.get("iptm", -1.0),
                )
                continue

            logger.info(
                "[Step05c] [%d/%d] RUN %s × %s",
                pair_count, total_pairs, seq_id, rec_name,
            )

            iptm_val = predict_pair(
                seq_id=seq_id,
                sequence=sequence,
                receptor_name=rec_name,
                receptor_seq=SSTR_SEQUENCES.get(rec_name, rec.get("sequence", "")),
                receptor_msa_path=receptor_msa_paths[rec_name],
                work_dir=work_dir,
                boltz_env=boltz_env,
                cuda_device=cuda_device,
                pair_timeout=pair_timeout,
            )
            iptm_matrix[seq_id][rec_name] = iptm_val

            # checkpoint 저장
            completed_pairs[pair_key] = {
                "seq_id": seq_id,
                "receptor": rec_name,
                "iptm": iptm_val,
            }
            if pair_count % checkpoint_interval == 0:
                _save_checkpoint(checkpoint_file, completed_pairs)

    # 마지막 checkpoint 저장
    _save_checkpoint(checkpoint_file, completed_pairs)

    # BoltzSelectivityResult 조합
    results: List[BoltzSelectivityResult] = []
    for candidate in candidates:
        seq_id = getattr(candidate, "seq_id", getattr(candidate, "candidate_id", "unknown"))
        sequence = getattr(candidate, "sequence", "")
        if seq_id not in iptm_matrix:
            continue

        receptor_iptm = iptm_matrix[seq_id]
        sstr2_iptm = receptor_iptm.get(sstr2_name)
        if sstr2_iptm is None:
            logger.warning("[Step05c] %s SSTR2 iPTM 없음 — 결과 스킵", seq_id)
            continue

        offtarget_iptm: Dict[str, float] = {
            name: val
            for name, val in receptor_iptm.items()
            if name != sstr2_name and val is not None
        }

        margin, best_receptor = compute_selectivity_margin(sstr2_iptm, offtarget_iptm)
        tier = classify_tier(margin, tier_thresholds)

        results.append(BoltzSelectivityResult(
            seq_id=seq_id,
            sequence=sequence,
            sstr2_iptm=sstr2_iptm,
            offtarget_iptm=offtarget_iptm,
            selectivity_margin=margin,
            best_receptor=best_receptor,
            tier=tier,
        ))

    # T2 이상 통과 후보 필터
    passed = [r for r in results if r.tier in ("T2", "T3")]

    logger.info(
        "[Step05c] 완료: %d/%d 후보 T2 이상 통과",
        len(passed), len(results),
    )

    return Step05cOutput(
        results=results,
        passed_candidates=passed,
        n_total=len(results),
        n_passed=len(passed),
    )


# ---------------------------------------------------------------------------
# Pair Prediction
# ---------------------------------------------------------------------------

def predict_pair(
    seq_id: str,
    sequence: str,
    receptor_name: str,
    receptor_seq: str,
    receptor_msa_path: Path,
    work_dir: Path,
    boltz_env: str = "boltz",
    cuda_device: int = 3,
    pair_timeout: int = 600,
) -> Optional[float]:
    """단일 후보 × 수용체 페어에 대해 Boltz-2 예측을 수행하고 iPTM 반환.

    Args:
        seq_id: 후보 시퀀스 ID
        sequence: 후보 아미노산 시퀀스
        receptor_name: 수용체 이름 (예: "SSTR2")
        receptor_seq: 수용체 아미노산 시퀀스
        receptor_msa_path: 수용체 AlphaFoldDB MSA .a3m 파일 경로
        work_dir: 작업 디렉토리 (YAML, 출력 저장)
        boltz_env: conda 환경 이름
        cuda_device: CUDA GPU 번호
        pair_timeout: subprocess timeout (초)

    Returns:
        float: iPTM 값 (0.0~1.0), 실패 시 None
    """
    _safe_id(seq_id, "seq_id")
    _safe_id(receptor_name, "receptor_name")

    pair_id = f"{seq_id}__{receptor_name}"
    pair_dir = work_dir / pair_id
    pair_dir.mkdir(parents=True, exist_ok=True)

    # 펩타이드 self-only a3m 생성
    pep_msa_path = pair_dir / f"{seq_id}_pepmsa.a3m"
    pep_msa_path.write_text(f">query\n{sequence}\n", encoding="utf-8")

    # Boltz YAML 생성
    yaml_path = pair_dir / f"{pair_id}.yaml"
    yaml_content = (
        f"version: 1\n"
        f"sequences:\n"
        f"  - protein:\n"
        f"      id: A\n"
        f"      sequence: {sequence}\n"
        f"      msa: {pep_msa_path.resolve()}\n"
        f"  - protein:\n"
        f"      id: B\n"
        f"      sequence: {receptor_seq}\n"
        f"      msa: {receptor_msa_path.resolve()}\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")

    out_dir = pair_dir / "boltz_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "conda", "run", "--no-capture-output", "-n", boltz_env,
        "boltz", "predict", str(yaml_path),
        "--out_dir", str(out_dir),
        "--recycling_steps", "1",
        "--sampling_steps", "50",
        "--diffusion_samples", "1",
        "--output_format", "pdb",
        "--override",
        "--num_workers", "0",
        "--no_kernels",
    ]

    env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(cuda_device)}

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=pair_timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        logger.error(
            "[Step05c] TIMEOUT (%ds) %s × %s", pair_timeout, seq_id, receptor_name
        )
        return None
    except Exception as e:
        logger.error("[Step05c] subprocess 오류 %s × %s: %s", seq_id, receptor_name, e)
        return None

    elapsed = time.time() - t0

    if proc.returncode != 0:
        logger.warning(
            "[Step05c] boltz predict 실패 (rc=%d) %s × %s: %s",
            proc.returncode, seq_id, receptor_name, proc.stderr[-500:],
        )
        return None

    # confidence JSON 파싱
    iptm = _parse_confidence(out_dir, pair_id)
    if iptm is not None:
        logger.info(
            "[Step05c] %s × %s → iPTM=%.3f (%.1fs)",
            seq_id, receptor_name, iptm, elapsed,
        )
    else:
        logger.warning(
            "[Step05c] %s × %s confidence 파일 없음 (%.1fs)",
            seq_id, receptor_name, elapsed,
        )

    return iptm


def _parse_confidence(out_dir: Path, pair_id: str) -> Optional[float]:
    """boltz predict 출력 디렉토리에서 confidence JSON을 찾아 iPTM 반환.

    Boltz 출력 구조:
        out_dir/boltz_results_{yaml_stem}/predictions/{yaml_stem}/confidence_{yaml_stem}_model_0.json

    Args:
        out_dir: boltz predict --out_dir 경로
        pair_id: YAML 파일 stem (= pair_id)

    Returns:
        float: iPTM, 없으면 None
    """
    # 패턴 1: 알려진 경로
    known = (
        out_dir
        / f"boltz_results_{pair_id}"
        / "predictions"
        / pair_id
        / f"confidence_{pair_id}_model_0.json"
    )
    if known.exists():
        return _read_iptm(known)

    # 패턴 2: rglob fallback
    conf_files = list(out_dir.rglob("confidence_*_model_0.json"))
    if conf_files:
        # 가장 최근 파일 선택
        conf_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return _read_iptm(conf_files[0])

    return None


def _read_iptm(path: Path) -> Optional[float]:
    """confidence JSON에서 iPTM 값을 읽어 반환."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        val = data.get("iptm")
        if val is not None:
            return float(val)
        # pair_chains_iptm fallback (체인 0-1)
        pci = data.get("pair_chains_iptm", {})
        val2 = pci.get("0", {}).get("1")
        if val2 is not None:
            return float(val2)
    except Exception as e:
        logger.debug("iPTM read failed %s: %s", path, e)
    return None


# ---------------------------------------------------------------------------
# Selectivity Margin & Tier Classification
# ---------------------------------------------------------------------------

def compute_selectivity_margin(
    sstr2_iptm: float,
    offtarget_iptm: Dict[str, float],
) -> Tuple[float, str]:
    """selectivity_margin 및 best off-target 수용체 반환.

    Args:
        sstr2_iptm: SSTR2 iPTM
        offtarget_iptm: {receptor_name: iPTM} (off-target)

    Returns:
        (margin, best_receptor)
        margin = sstr2_iptm - max(offtarget_iptm)  (양수 = SSTR2 선택적)

    HEURISTIC:
        margin은 Δ와 동치이며 iPTM(geometry 신뢰도) 차이이다. 바인딩 선택성 친화도
        proxy가 아니므로 tier 해석은 모듈 docstring 상단 disclaimer를 따른다.
    """
    if not offtarget_iptm:
        return 0.0, "none"

    best_receptor = max(offtarget_iptm, key=offtarget_iptm.__getitem__)
    best_iptm = offtarget_iptm[best_receptor]
    margin = sstr2_iptm - best_iptm
    return margin, best_receptor


def classify_tier(
    margin: float,
    thresholds: Optional[Dict[str, float]] = None,
) -> str:
    """selectivity margin을 Tier로 분류.

    Args:
        margin: selectivity_margin = iPTM(SSTR2) - max(iPTM(off-target))
        thresholds: {"T3": 0.03, "T2": 0.0, "T1": -0.03} (기본값)
            T3: margin >= 0.03
            T2: 0.00 <= margin < 0.03
            T1: -0.03 <= margin < 0.00
            T0: margin < -0.03

    Returns:
        "T3" | "T2" | "T1" | "T0"
    """
    t = thresholds or DEFAULT_TIER_THRESHOLDS
    t3 = t.get("T3", 0.03)
    t2 = t.get("T2", 0.00)
    t1 = t.get("T1", -0.03)

    if margin >= t3:
        return "T3"
    elif margin >= t2:
        return "T2"
    elif margin >= t1:
        return "T1"
    else:
        return "T0"


# ---------------------------------------------------------------------------
# AlphaFoldDB MSA 자동 다운로드
# ---------------------------------------------------------------------------

def download_alphafold_msa(
    uniprot_id: str,
    dest_dir: Path,
    timeout: int = 120,
) -> Optional[Path]:
    """AlphaFoldDB에서 UniProt 수용체 MSA a3m 다운로드.

    시도 순서:
      1. 직접 URL 패턴 (AF-{UP}-F1-msa_v6.a3m)
      2. API endpoint 동적 조회 (msaUrl 필드)

    Args:
        uniprot_id: UniProt accession (예: "P30874")
        dest_dir: 저장 디렉토리
        timeout: HTTP 요청 timeout (초)

    Returns:
        Path: 다운로드된 .a3m 파일 경로, 실패 시 None
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"AF-{uniprot_id}-F1-msa.a3m"

    # 이미 존재하면 재사용
    if dest.exists() and dest.stat().st_size > 1000:
        logger.debug("[Step05c] MSA 캐시 사용: %s", dest)
        return dest

    # 시도 1: 직접 URL
    direct_url = _AF_MSA_URL_TEMPLATE.format(uniprot=uniprot_id)
    if _download_url(direct_url, dest, timeout):
        logger.info("[Step05c] MSA 다운로드 완료 (direct): %s", dest)
        return dest

    # 시도 2: API endpoint 동적 조회
    api_url = _AF_API_URL_TEMPLATE.format(uniprot=uniprot_id)
    try:
        with urllib.request.urlopen(api_url, timeout=timeout) as resp:
            api_data = json.loads(resp.read())
        if isinstance(api_data, list) and api_data:
            msa_url = api_data[0].get("msaUrl", "")
        else:
            msa_url = ""
        if msa_url and _download_url(msa_url, dest, timeout):
            logger.info("[Step05c] MSA 다운로드 완료 (API): %s", dest)
            return dest
    except Exception as e:
        logger.warning("[Step05c] API 조회 실패 %s: %s", uniprot_id, e)

    logger.error("[Step05c] MSA 다운로드 실패: %s", uniprot_id)
    return None


def _download_url(url: str, dest: Path, timeout: int) -> bool:
    """URL에서 파일을 다운로드. 성공 시 True 반환."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content = resp.read()
        if len(content) < 100:
            return False
        dest.write_bytes(content)
        return True
    except Exception as e:
        logger.debug("[Step05c] download failed %s: %s", url, e)
        return False


def _ensure_receptor_msa(
    uniprot_id: str,
    receptor_name: str,
    af_msa_dir: Path,
) -> Optional[Path]:
    """수용체 MSA가 없으면 자동 다운로드."""
    expected = af_msa_dir / f"AF-{uniprot_id}-F1-msa.a3m"
    if expected.exists() and expected.stat().st_size > 1000:
        logger.debug("[Step05c] MSA 기존 사용: %s", expected)
        return expected

    logger.info(
        "[Step05c] %s (%s) MSA 없음 → 다운로드 시도",
        receptor_name, uniprot_id,
    )
    return download_alphafold_msa(uniprot_id, af_msa_dir)


# ---------------------------------------------------------------------------
# Checkpoint helper
# ---------------------------------------------------------------------------

def _save_checkpoint(
    checkpoint_file: Path,
    completed_pairs: Dict[str, Any],
) -> None:
    """partial_results.json 저장 (원자적 쓰기)."""
    try:
        tmp = checkpoint_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(completed_pairs, f, indent=2, ensure_ascii=False)
        shutil.move(str(tmp), str(checkpoint_file))
        logger.debug("[Step05c] checkpoint 저장: %d 페어", len(completed_pairs))
    except Exception as e:
        logger.warning("[Step05c] checkpoint 저장 실패: %s", e)


# ---------------------------------------------------------------------------
# Result I/O
# ---------------------------------------------------------------------------

def save_step05c_results(
    output: Step05cOutput,
    output_dir: Path,
) -> Dict[str, str]:
    """Step05c 결과를 파일로 저장.

    Args:
        output: Step05cOutput 인스턴스
        output_dir: 저장 디렉토리

    Returns:
        저장된 파일 경로 dict
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "boltz_cross_validation.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)

    saved = {"summary": str(summary_path)}

    for result in output.results:
        safe_id = _safe_id(result.seq_id, "seq_id")
        detail_path = output_dir / f"{safe_id}_boltz_cross.json"
        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        saved[result.seq_id] = str(detail_path)

    logger.info("[Step05c] 결과 저장 완료: %s", output_dir)
    return saved
