"""predict_halflife_pepmsnd.py
==============================
혈청 반감기 예측 wrapper — PlifePred2 (로컬) + PepMSND (웹, 현재 불가).

## 도구 상태 (2026-05-19 기준)

| 도구 | 방법론 | 이진/연속 | 로컬 실행 | D-AA | 신뢰도 |
|------|--------|---------|---------|------|--------|
| PlifePred2 | ML (QSO features) | 확률 스코어 | ✅ (peptools env) | ❌ (L-AA only) | P4 |
| PepMSND    | KAN+Transformer+GAT | 이진 분류  | ❌ (웹 전용, 403) | ❌ | P3 |
| pepADMET   | GNN+RGCN            | 연속 R²=0.84-0.90 | ❌ (웹 전용) | 미확인 | P2 |

### 중요 한계 (H-06 가드)
- PlifePred2 출력: 확률 스코어 (0~1) — 시간(hour) 단위 아님
- PepMSND: http://model.highslab.com/static/service — 현재 403 오류로 접근 불가
- D-AA 함유 서열(Octreotide 등)은 어떤 로컬 도구도 지원 안 됨
- 출력값은 1차 triage 목적만 — wet-lab LC-MS/MS 실측 필수

## 사용법

### 로컬 (peptools env) — PlifePred2
```bash
conda run -n peptools python predict_halflife_pepmsnd.py \\
    --sequence AGCKNFFWKTFTSC \\
    --output runs_local/pepmsnd_benchmark/sst14.json
```

### 배치 (FASTA)
```bash
conda run -n peptools python predict_halflife_pepmsnd.py \\
    --fasta sequences.fasta \\
    --output output.json
```
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# peptools env에서만 실행 가능
PEPTOOLS_CONDA_ENV = "peptools"
VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")

HLE_REGRESSION_UNAVAILABLE_REASON = (
    "HLE regression coefficients/model artifact are not present in this checkout. "
    "The public abstract confirms the model family and R2, but not enough "
    "parameters to compute peptide half-life hours without hallucination."
)

# Exact benchmark controls only. These are not a fitted score->hour conversion.
# The PlifePred2 package writes predict_proba output into the "Halflife" CSV
# column, so unknown sequences must remain rank-only unless an explicit
# literature/calibration-table value exists here.
PLIFEPRED_HALFLIFE_CALIBRATION_TABLE = {
    "AGCKNFFWKTFTSC": {
        "name": "SST-14",
        "halflife_hours": 3.0 / 60.0,
        "halflife_label": "3 min",
        "source": "StatPearls/NCBI Bookshelf: somatostatin half-life 1-3 min; project benchmark uses 3 min.",
        "scope": "exact endogenous SST-14 benchmark lookup; not score calibration",
    },
}

PLIFEPRED2_RANK_ONLY_WARNING = (
    "PlifePred2 output column 'Halflife' is a predicted probability/ranking score, "
    "not an hour-valued half-life. No literature formula was found to convert this "
    "score to hours for arbitrary sequences."
)

# ENDPOINT_CONFIDENCE 등록값 (pharmacology_guards.py §5와 일치)
HALFLIFE_PLIFEPRED2_CONFIDENCE = {
    "tool": "PlifePred2",
    "version": "1.0 (PyPI)",
    "grade": "P4",   # peer-reviewed 성능 검증 미확보
    "d_amino_acid_support": False,
    "local_executable": True,
    "output_type": "probability_score",  # 0~1 스코어, 시간 단위 아님
    "output_unit": "probability (higher = longer half-life, estimated)",
    "benchmark_r2_natural": None,    # 미확인 (2026-05-19)
    "benchmark_spearman_rho": None,  # 미확인
    "assay_context": "mammalian_blood (natural L-AA only)",
    "disclaimer": (
        "PlifePred2 출력은 반감기 확률 스코어 (0~1)이며 시간(hour) 단위가 아닙니다. "
        "D-아미노산 서열은 입력 거부 (VALID_AA 체크). "
        "peer-reviewed 독립 성능 검증 미확보 — P4(heuristic) 등급. "
        "TPP KPI(≥24h, ≥72h) 직접 적용 불가. "
        "H-06: 스코어를 연속 반감기 값으로 해석 금지."
    ),
    "source": "PlifePred2 v1.0 PyPI. 원 논문: Mathur D et al. 2018 PLOS ONE 13(6):e0196829 (PlifePred 전신)",
}

PEPMSND_CONFIDENCE = {
    "tool": "PepMSND",
    "url": "http://model.highslab.com/static/service",
    "grade": "P3",
    "status": "web_only_403_unreachable",   # 2026-05-19 현재 403
    "d_amino_acid_support": False,          # 웹 인터페이스 미지원
    "local_executable": False,
    "output_type": "binary_classification",
    "benchmark_auc": 0.912,
    "benchmark_acc": 0.867,
    "disclaimer": (
        "PepMSND 웹서버(http://model.highslab.com/static/service)가 "
        "현재 서버에서 403 응답 — 사용 불가 (2026-05-19). "
        "웹 인터페이스는 natural amino acids only — D-AA 직접 입력 불가. "
        "이진 분류 출력(stable/unstable 등급) — 연속 t½ 아님. "
        "H-06: 분류 등급을 연속 반감기 값으로 해석 금지."
    ),
    "source": "Wang et al. 2025 Digital Discovery. DOI:10.1039/D5DD00118H",
}


def check_d_aa(sequence: str) -> list[str]:
    """D-AA 또는 비표준 AA가 있으면 경고 목록 반환."""
    invalid = [aa for aa in sequence if aa.upper() not in VALID_AA]
    return invalid


def _contains_d_aa_notation(sequence: str) -> bool:
    """Detect local D-AA notation used by repository tests and candidate files."""
    import re

    if any(ch.isalpha() and ch.islower() for ch in sequence):
        return True
    return bool(re.search(r"(^|[^A-Za-z])d[-_ ]?[A-Za-z]{1,3}", sequence, re.IGNORECASE))


def _write_fasta(seq_id: str, sequence: str, fasta_path: str) -> None:
    with open(fasta_path, "w") as f:
        f.write(f">{seq_id}\n{sequence}\n")


def predict_with_plifepred2(
    sequence: str,
    seq_id: str = "query",
    model: str = "1",
) -> dict:
    """PlifePred2 CLI를 호출하여 반감기 스코어 예측.

    Args:
        sequence: 표준 L-아미노산 1문자 서열
        seq_id:   출력에 표시될 ID
        model:    '1' (natural) 또는 '2' (modified)

    Returns:
        {
            "plifepred2_score": float or None,
            "confidence_grade": "P4",
            "input_sequence": str,
            "warnings": list[str],
            "disclaimer": str,
        }
    """
    warnings_list: list[str] = []
    invalid_aa = check_d_aa(sequence)

    if invalid_aa:
        return {
            "plifepred2_score": None,
            "confidence_grade": "P4",
            "input_sequence": sequence,
            "error": f"비표준 AA 포함 — PlifePred2 입력 불가: {invalid_aa}",
            "warnings": [
                f"비표준/D-아미노산 {invalid_aa} 포함. PlifePred2는 L-AA 20종만 지원."
            ],
            "disclaimer": HALFLIFE_PLIFEPRED2_CONFIDENCE["disclaimer"],
        }

    # 임시 FASTA + CSV 파일
    with tempfile.NamedTemporaryFile(suffix=".fasta", delete=False, mode="w") as fasta_f:
        fasta_f.write(f">{seq_id}\n{sequence}\n")
        fasta_path = fasta_f.name

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as csv_f:
        csv_path = csv_f.name

    try:
        # peptools env의 plifepred2 CLI 호출
        conda_prefix = os.environ.get(
            "CONDA_PREFIX_PEPTOOLS",
            f"{Path.home()}/miniforge3/envs/{PEPTOOLS_CONDA_ENV}"
        )
        plifepred2_bin = Path(conda_prefix) / "bin" / "plifepred2"

        if not plifepred2_bin.exists():
            # 현재 환경에서 직접 찾기
            result_which = subprocess.run(
                ["which", "plifepred2"], capture_output=True, text=True
            )
            if result_which.returncode == 0:
                plifepred2_bin = Path(result_which.stdout.strip())
            else:
                return {
                    "plifepred2_score": None,
                    "confidence_grade": "P4",
                    "input_sequence": sequence,
                    "error": f"plifepred2 바이너리를 찾을 수 없습니다. conda run -n {PEPTOOLS_CONDA_ENV} 환경에서 실행하세요.",
                    "warnings": ["peptools env 미활성화 또는 plifepred2 미설치"],
                    "disclaimer": HALFLIFE_PLIFEPRED2_CONFIDENCE["disclaimer"],
                }

        cmd = [
            str(plifepred2_bin),
            "-i", fasta_path,
            "-m", model,
            "-o", csv_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if proc.returncode != 0:
            return {
                "plifepred2_score": None,
                "confidence_grade": "P4",
                "input_sequence": sequence,
                "error": f"plifepred2 실행 오류: {proc.stderr}",
                "warnings": [proc.stderr.strip()],
                "disclaimer": HALFLIFE_PLIFEPRED2_CONFIDENCE["disclaimer"],
            }

        # CSV 결과 파싱
        import csv
        score = None
        with open(csv_path, newline="") as csvf:
            reader = csv.DictReader(csvf)
            for row in reader:
                if row.get("ID") == seq_id or row.get("Sequence", "").upper() == sequence.upper():
                    score_str = row.get("Halflife", "")
                    if score_str:
                        score = float(score_str)
                    break

        if score is None:
            # 첫 번째 행의 Halflife 값 사용
            with open(csv_path, newline="") as csvf:
                reader = csv.DictReader(csvf)
                for row in reader:
                    score_str = row.get("Halflife", "")
                    if score_str:
                        score = float(score_str)
                    break

        warnings_list.append(
            "PlifePred2 스코어는 확률값 (0~1)입니다. "
            "Higher score = 더 긴 반감기 추정 (검증 필요). "
            "시간(hour) 단위로 직접 변환 불가."
        )

        return {
            "plifepred2_score": score,
            "plifepred2_score_unit": "probability (0~1, NOT hours)",
            "plifepred2_model": f"model_{model}_{'natural' if model=='1' else 'modified'}",
            "confidence_grade": "P4",
            "input_sequence": sequence,
            "warnings": warnings_list,
            "disclaimer": HALFLIFE_PLIFEPRED2_CONFIDENCE["disclaimer"],
        }

    except subprocess.TimeoutExpired:
        return {
            "plifepred2_score": None,
            "confidence_grade": "P4",
            "input_sequence": sequence,
            "error": "plifepred2 실행 시간 초과 (60초)",
            "warnings": ["실행 시간 초과"],
            "disclaimer": HALFLIFE_PLIFEPRED2_CONFIDENCE["disclaimer"],
        }
    finally:
        for p in [fasta_path, csv_path]:
            if os.path.exists(p):
                os.remove(p)


def _standardize_sequence_key(sequence: str) -> str:
    return "".join(ch for ch in sequence.upper() if ch.isalpha())


def _plifepred_calibrated_hours(sequence: str) -> dict | None:
    """Return exact benchmark half-life hours when a documented lookup exists."""
    key = _standardize_sequence_key(sequence)
    entry = PLIFEPRED_HALFLIFE_CALIBRATION_TABLE.get(key)
    if not entry:
        return None
    return {
        "predicted_hours": float(entry["halflife_hours"]),
        "conversion_method": "calibration_table",
        "calibration_entry": entry,
        "warnings": [
            "Exact benchmark calibration-table lookup used; this is not a fitted PlifePred2 score-to-hour conversion.",
        ],
    }


def predict_halflife_plifepred(sequence: str, seq_id: str = "query", model: str = "1") -> dict:
    """PlifePred2 wrapper with explicit hour availability metadata.

    PlifePred2 v1.0 writes classifier probability/ranking output into a CSV
    column named "Halflife". The wrapper preserves that raw rank score and only
    returns hours for exact benchmark entries with documented measured values.
    """
    plife_result = predict_with_plifepred2(sequence, seq_id=seq_id, model=model)
    rank_score = plife_result.get("plifepred2_score")
    warnings_list = list(plife_result.get("warnings", []))

    calibrated = _plifepred_calibrated_hours(sequence)
    if calibrated is not None:
        warnings_list.extend(calibrated["warnings"])
        return {
            "rank_score": rank_score,
            "predicted_hours": calibrated["predicted_hours"],
            "conversion_method": "calibration_table",
            "absolute_confidence": "P3",
            "confidence_grade": "P3",
            "input_sequence": sequence,
            "warnings": warnings_list,
            "raw_plifepred2": plife_result,
            "calibration_entry": calibrated["calibration_entry"],
        }

    warnings_list.append(PLIFEPRED2_RANK_ONLY_WARNING)
    result = {
        "rank_score": rank_score,
        "predicted_hours": None,
        "conversion_method": "unavailable",
        "absolute_confidence": "P4",
        "confidence_grade": "P4",
        "input_sequence": sequence,
        "warnings": warnings_list,
        "raw_plifepred2": plife_result,
    }
    if plife_result.get("error"):
        result["error"] = plife_result["error"]
    return result


def predict_halflife_hle_regression(sequence: str) -> dict:
    """HLE regression 모델 호출.

    Returns:
        {
            'predicted_hours': float | None,
            'method': 'hle_regression_albumin' | 'unavailable',
            'absolute_confidence': 'P3' | 'P4',
            'warnings': list[str],
        }
    """
    warnings_list: list[str] = []
    invalid_aa = check_d_aa(sequence)
    if invalid_aa or _contains_d_aa_notation(sequence):
        warnings_list.append(
            "D-AA or non-standard amino acid notation detected; "
            "HLE regression wrapper is recommended=False for D-AA input."
        )
        return {
            "predicted_hours": None,
            "method": "unavailable",
            "absolute_confidence": "P4",
            "confidence": "P4",
            "input_sequence": sequence,
            "recommended": False,
            "unavailable": True,
            "reason": "D-AA/non-standard input rejected for HLE regression",
            "warnings": warnings_list,
        }

    warnings_list.extend(
        [
            HLE_REGRESSION_UNAVAILABLE_REASON,
            "No repo-local HLE regression weights, coefficients, or executable were found under pipeline_local/.",
            "Layer 1 will keep this tool callable but unavailable until a verifiable model artifact is added.",
        ]
    )
    return {
        "predicted_hours": None,
        "method": "unavailable",
        "absolute_confidence": "P4",
        "confidence": "P4",
        "input_sequence": sequence,
        "recommended": True,
        "unavailable": True,
        "reason": HLE_REGRESSION_UNAVAILABLE_REASON,
        "warnings": warnings_list,
    }


def predict_with_pepmsnd_web(sequence: str) -> dict:
    """PepMSND 웹서버 호출 (현재 403으로 불가능 — stub).

    Returns:
        {
            "pepmsnd_result": None,
            "status": "web_unreachable",
            ...
        }
    """
    try:
        import requests
        url = "http://model.highslab.com/static/service"
        resp = requests.get(url, timeout=10)
        status_code = resp.status_code
    except Exception as e:
        status_code = f"error: {e}"

    return {
        "pepmsnd_result": None,
        "status": f"web_unreachable (HTTP {status_code})",
        "url": "http://model.highslab.com/static/service",
        "confidence_grade": "P3",
        "input_sequence": sequence,
        "warnings": [
            f"PepMSND 웹서버 응답: HTTP {status_code}",
            "PepMSND는 웹 전용 도구 — 로컬 실행 불가.",
            "웹서버 접근 가능 시 https://model.highslab.com/pepmsnd 수동 입력 필요.",
            "D-AA 서열(Octreotide 등)은 웹 인터페이스에서도 입력 불가.",
        ],
        "disclaimer": PEPMSND_CONFIDENCE["disclaimer"],
        "manual_url": "http://model.highslab.com/static/service",
    }


def predict_halflife(
    sequence: str,
    seq_id: str = "query",
    use_plifepred2: bool = True,
    use_pepmsnd_web: bool = False,
    plifepred2_model: str = "1",
) -> dict:
    """통합 반감기 예측 wrapper.

    Args:
        sequence:         1문자 코드 펩타이드 서열
        seq_id:           출력 레이블
        use_plifepred2:   PlifePred2 로컬 예측 사용 여부
        use_pepmsnd_web:  PepMSND 웹 호출 시도 여부 (현재 403)
        plifepred2_model: '1' (natural) 또는 '2' (modified with flags)

    Returns:
        통합 결과 딕셔너리
    """
    result: dict = {
        "input_sequence": sequence,
        "seq_id": seq_id,
        "tool_status": {},
        "plifepred2": None,
        "pepmsnd_web": None,
        "warnings": [],
        "final_confidence_grade": "P4",
        "disclaimer": (
            "H-06 HEURISTIC: 이 함수의 출력은 1차 triage 목적입니다. "
            "PlifePred2는 확률 스코어(0~1)를 반환하며 시간 단위가 아닙니다. "
            "D-AA 서열에는 적용 불가. 반드시 wet-lab LC-MS/MS 실측이 필요합니다."
        ),
    }

    # D-AA 체크
    invalid_aa = check_d_aa(sequence)
    if invalid_aa:
        result["warnings"].append(
            f"⚠️ 비표준/D-아미노산 감지: {invalid_aa}. "
            "현재 로컬 도구 중 D-AA를 지원하는 반감기 예측 도구가 없습니다. "
            "(researcher 보고서 A-02 §4 참조)"
        )
        result["tool_status"]["d_aa_support"] = False

    # PlifePred2 로컬 예측
    if use_plifepred2:
        plife_result = predict_with_plifepred2(sequence, seq_id, plifepred2_model)
        result["plifepred2"] = plife_result
        result["warnings"].extend(plife_result.get("warnings", []))
        result["tool_status"]["plifepred2"] = (
            "success" if plife_result.get("plifepred2_score") is not None
            else f"failed: {plife_result.get('error', 'unknown')}"
        )

    # PepMSND 웹 (시도 시)
    if use_pepmsnd_web:
        pepmsnd_result = predict_with_pepmsnd_web(sequence)
        result["pepmsnd_web"] = pepmsnd_result
        result["warnings"].extend(pepmsnd_result.get("warnings", []))
        result["tool_status"]["pepmsnd_web"] = pepmsnd_result.get("status")

    return result


def predict_halflife_batch(
    sequences: list[dict],  # [{"id": str, "sequence": str}, ...]
    use_plifepred2: bool = True,
    plifepred2_model: str = "1",
) -> list[dict]:
    """배치 예측."""
    results = []
    for item in sequences:
        seq_id = item.get("id", "query")
        sequence = item.get("sequence", "")
        r = predict_halflife(
            sequence=sequence,
            seq_id=seq_id,
            use_plifepred2=use_plifepred2,
            use_pepmsnd_web=False,
            plifepred2_model=plifepred2_model,
        )
        results.append(r)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="반감기 예측 wrapper (PlifePred2 로컬 + PepMSND 웹 stub)"
    )
    parser.add_argument("--sequence", help="1문자 코드 펩타이드 서열")
    parser.add_argument("--fasta", help="Multi-FASTA 입력 파일")
    parser.add_argument("--seq-id", default="query", help="서열 ID")
    parser.add_argument(
        "--model", default="1", choices=["1", "2"],
        help="PlifePred2 모델: 1=natural, 2=modified"
    )
    parser.add_argument("--pepmsnd-web", action="store_true", help="PepMSND 웹 접속 시도")
    parser.add_argument("--output", help="출력 JSON 파일")

    args = parser.parse_args()

    if not args.sequence and not args.fasta:
        parser.error("--sequence 또는 --fasta 중 하나를 지정하세요.")

    if args.sequence:
        result = predict_halflife(
            sequence=args.sequence,
            seq_id=args.seq_id,
            use_plifepred2=True,
            use_pepmsnd_web=args.pepmsnd_web,
            plifepred2_model=args.model,
        )
        results = [result]

    elif args.fasta:
        # FASTA 파싱
        sequences = []
        with open(args.fasta) as f:
            current_id = None
            current_seq = []
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if current_id:
                        sequences.append({"id": current_id, "sequence": "".join(current_seq)})
                    current_id = line[1:].split()[0]
                    current_seq = []
                elif line:
                    current_seq.append(line)
            if current_id:
                sequences.append({"id": current_id, "sequence": "".join(current_seq)})

        results = predict_halflife_batch(sequences, plifepred2_model=args.model)

    output_str = json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"저장: {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
