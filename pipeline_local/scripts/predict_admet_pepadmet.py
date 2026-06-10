"""predict_admet_pepadmet.py
============================
ADMET 예측 wrapper — pepADMET 로컬 GNN (재훈련) + modlamp 디스크립터 fallback.

## 도구 상태 (2026-05-21 기준, A.A5 chain 완료)

| 도구 | 엔드포인트 | 로컬 | D-AA | 신뢰도 |
|------|-----------|------|------|--------|
| pepADMET GNN (로컬) | binary_toxicity (SMILES) | ✅ pepadmet-upgrade env | ❌ | P2 |
| pepADMET | 29 ADMET (R²=0.84-0.90) | ❌ 웹 전용, 403 | 미확인 | P2 |
| modlamp  | 물리화학 디스크립터 (Boman, GRAVY 등) | ✅ (pepadmet env) | ❌ | P3 |
| BioPython ProtParam | 불안정성 지수, MW 등 | ✅ (bio-tools env) | ❌ | P3 |

### 중요 한계 (H-06 가드)
- **pepADMET 로컬 GNN**: descriptor=0 기반 추론 → 구조적 특징만 반영 (상대 비교 용도)
- pepADMET 웹서버(https://pepadmet.ddai.tech/) 현재 이 서버에서 403 응답
- D-AA/DOTA 결합 후보: 신뢰 가능한 ADMET 예측 도구 없음 (researcher A-03 결론)
- modlamp 출력은 물리화학적 디스크립터 (실제 ADMET 예측 아님)
- 출력은 1차 triage 목적만 — wet-lab ADMET assay 병행 필수

## 29 pepADMET 엔드포인트 (웹 접근 가능 시)
- Half-life: human/mouse blood + intestine
- Toxicity: DILI, cardiotoxicity, cytotoxicity
- ADME: BBB, Caco-2, solubility, PPB, CYP inhibition 등

## 사용법

### 로컬 물리화학 디스크립터 (pepadmet env)
```bash
conda run -n pepadmet python predict_admet_pepadmet.py \\
    --sequence AGCKNFFWKTFTSC \\
    --output runs_local/pepadmet_benchmark/sst14.json
```

### pepADMET 웹 시도 (현재 403)
```bash
conda run -n pepadmet python predict_admet_pepadmet.py \\
    --sequence AGCKNFFWKTFTSC \\
    --pepADMET-web \\
    --output runs_local/pepadmet_benchmark/sst14.json
```
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# modlamp (pepadmet env) — 임포트 실패 시 graceful degradation
try:
    from modlamp.descriptors import GlobalDescriptor
    MODLAMP_AVAILABLE = True
except ImportError:
    MODLAMP_AVAILABLE = False

# ---------------------------------------------------------------------------
# 로컬 pepADMET GNN 모델 설정 (A.A5 chain, 2026-05-21)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PEPADMET_LOCAL = _REPO_ROOT / "_workspace" / "pepadmet_local"
_PEPADMET_MODEL_PATH = (
    _PEPADMET_LOCAL / "pepADMET" / "model" / "toxicity_retrained_2026-05-21.pth"
)
_PEPADMET_SRC = _PEPADMET_LOCAL / "pepADMET"

LOCAL_GNN_AVAILABLE: bool = False
_LOCAL_GNN_MODEL = None

def _try_load_local_gnn() -> bool:
    """로컬 GNN 모델 로드 시도. 성공 시 True 반환."""
    global LOCAL_GNN_AVAILABLE, _LOCAL_GNN_MODEL
    if not _PEPADMET_MODEL_PATH.exists():
        return False
    try:
        import torch
        sys.path.insert(0, str(_PEPADMET_SRC))
        from utils.MY_GNN import MGA  # type: ignore[import]
        _GNN_ARGS = {
            "device": "cpu",  # pipeline에서는 CPU 사용 (안정성 우선)
            "atom_data_field": "atom",
            "bond_data_field": "etype",
            "descriptor_dim": 2133,
            "descriptor": 2133,
            "fpn_out": 2133,
            "fp_2_dim": 512,
            "hidden_size": 256,
            "in_feats": 40,
            "rgcn_hidden_feats": [64, 64],
            "classifier_hidden_feats": 320,
            "rgcn_drop_out": 0.2,
            "drop_out": 0.2,
            "loop": True,
            "select_task_list": [
                "toxicity_nontoxicity",
                "toxicity_type_class",
                "neurotoxicity_type_class",
                "HC50",
            ],
        }
        task_number = len(_GNN_ARGS["select_task_list"])
        model = MGA(
            in_feats=_GNN_ARGS["in_feats"],
            descriptor=_GNN_ARGS["descriptor"],
            descriptor_dim=_GNN_ARGS["descriptor_dim"],
            rgcn_hidden_feats=_GNN_ARGS["rgcn_hidden_feats"],
            n_tasks=task_number,
            rgcn_drop_out=_GNN_ARGS["rgcn_drop_out"],
            fpn_out=_GNN_ARGS["fpn_out"],
            fp_2_dim=_GNN_ARGS["fp_2_dim"],
            hidden_size=_GNN_ARGS["hidden_size"],
            select_task_list=_GNN_ARGS["select_task_list"],
            device=_GNN_ARGS["device"],
            classifier_hidden_feats=_GNN_ARGS["classifier_hidden_feats"],
            dropout=_GNN_ARGS["drop_out"],
            loop=_GNN_ARGS["loop"],
        )
        state = torch.load(str(_PEPADMET_MODEL_PATH), map_location="cpu", weights_only=False)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        model.load_state_dict(state)
        model.eval()
        _LOCAL_GNN_MODEL = (model, _GNN_ARGS)
        LOCAL_GNN_AVAILABLE = True
        return True
    except Exception as e:
        _LOCAL_GNN_MODEL = None
        LOCAL_GNN_AVAILABLE = False
        return False


def predict_local_gnn_toxicity(smiles: str) -> dict:
    """로컬 GNN으로 binary_toxicity_pred 반환 (descriptor=0 기반).

    Args:
        smiles: 입력 SMILES 문자열

    Returns:
        {
          "binary_toxicity_pred": float,   # sigmoid 확률 (0~1)
          "ood_warning": bool,             # descriptor=0 외삽 주의
          "confidence_grade": "P2",
          "source": "pepADMET-GNN-local-2026-05-21",
          "disclaimer": str,
        }
    """
    if not LOCAL_GNN_AVAILABLE or _LOCAL_GNN_MODEL is None:
        return {
            "error": "로컬 GNN 모델 미로드 — _try_load_local_gnn() 호출 필요",
            "binary_toxicity_pred": None,
        }

    model, args = _LOCAL_GNN_MODEL
    try:
        import torch
        sys.path.insert(0, str(_PEPADMET_SRC))
        from utils.build_dataset import construct_RGCN_bigraph_from_smiles  # type: ignore
        import dgl

        g = construct_RGCN_bigraph_from_smiles(smiles)
        bg = dgl.batch([g])
        descriptor = torch.zeros(1, args["descriptor_dim"])
        atom_feats = bg.ndata.pop(args["atom_data_field"]).float()
        bond_feats = bg.edata.pop(args["bond_data_field"]).long()

        with torch.no_grad():
            logits = model(bg, atom_feats, bond_feats, descriptor)
        pred = float(torch.sigmoid(logits["task_0"]).squeeze().cpu())

        return {
            "binary_toxicity_pred": pred,
            # 항상 True: descriptor=0 외삽이므로 동적 OOD 계산 불가.
            # 동적 OOD (Mahalanobis + MC Dropout) 가 필요하면
            # pipeline_local/scripts/pepadmet_infer_ood.py CLI 경로를 사용하세요.
            "ood_warning": True,
            "confidence_grade": "P2",
            "source": "pepADMET-GNN-local-2026-05-21",
            "model_path": str(_PEPADMET_MODEL_PATH),
            "disclaimer": (
                "H-06: 로컬 GNN은 descriptor=0 기반 구조 추론. "
                "1차 triage 전용 — wet-lab 독성 assay 병행 필수. "
                "Sanity check: Octreotide=0.1322, SST-14=0.4022 (A.A5Pd 통과)."
            ),
        }
    except Exception as e:
        return {
            "error": f"GNN 추론 실패: {e}",
            "binary_toxicity_pred": None,
        }

# ENDPOINT_CONFIDENCE 등록값
PEPADMET_CONFIDENCE = {  # P1/P2 sprint 손실 복구 (2026-05-20 SOD) — grade P2→P1, D-AA=False, 웹폼 엔드포인트
    "tool": "pepADMET",
    "url": "https://pepadmet.ddai.tech/",
    "form_endpoint": "https://pepadmet.ddai.tech/calcpep/half-life/",  # 웹폼 POST (researcher P2)
    "grade": "P1",  # P2 → P1 정정: Wang 2026 JCIM 원 논문 R²=0.84-0.90 기준 (인프라 HTTP 403과 분리)
    "status": "web_only_403_unreachable",
    "d_amino_acid_support": False,  # researcher V-03 확정 — 학습셋 L-AA 한정
    "local_executable": False,
    "n_endpoints": 29,
    "benchmark_r2_human_blood_natural": 0.84,
    "benchmark_r2_human_blood_modified": 0.90,
    "license": "CC BY-NC-SA",
    "disclaimer": (
        "pepADMET 웹서버(https://pepadmet.ddai.tech/)가 현재 서버에서 403 응답 — "
        "자동화 통합 불가 (2026-05-19). "
        "D-아미노산 직접 지원 여부 미확인. "
        "R²=0.84~0.90 (human blood)이나 web-only 제약으로 파이프라인 자동화 불가. "
        "H-06: 웹 예측 결과는 in vitro 실측 대체 불가."
    ),
    "source": "pepADMET JCIM 2025. DOI:10.1021/acs.jcim.5c02518",
    "manual_access": "https://pepadmet.ddai.tech/ — 수동 입력 필요",
}

MODLAMP_CONFIDENCE = {
    "tool": "modlamp GlobalDescriptor",
    "grade": "P3",
    "d_amino_acid_support": False,
    "local_executable": True,
    "conda_env": "pepadmet",
    "disclaimer": (
        "modlamp 출력은 물리화학적 글로벌 디스크립터이며 "
        "실제 ADMET 파라미터(반감기, 독성, BBB 등)와 직접 동일하지 않습니다. "
        "GRAVY, Boman index, 순전하 등은 ADMET의 proxy descriptor입니다. "
        "H-06: 디스크립터 값을 임상 ADMET 수치로 해석 금지."
    ),
}


def predict_with_modlamp(sequence: str) -> dict:
    """modlamp GlobalDescriptor로 물리화학 디스크립터 계산.

    modlamp v0.4.3 API 기준 (pepadmet env):
      - calculate_all(): Length, MW, Charge, ChargeDensity, pI,
                         InstabilityInd, Aromaticity, AliphaticInd,
                         BomanInd, HydrophRatio
    반환:
        {
            "molecular_weight_da": float,
            "charge_ph7": float,
            "isoelectric_point": float,
            "instability_index": float,
            "boman_index": float,
            "aliphatic_index": float,
            "hydrophobic_ratio": float,
            "aromaticity": float,
            "confidence_grade": "P3",
            "warnings": list[str],
        }
    """
    if not MODLAMP_AVAILABLE:
        return {
            "error": "modlamp 미설치. conda run -n pepadmet 환경에서 실행하세요.",
            "confidence_grade": "P3",
            "warnings": ["modlamp import 실패"],
        }

    try:
        desc = GlobalDescriptor([sequence])
        desc.calculate_all()

        feature_names = desc.featurenames  # list
        values = desc.descriptor[0]       # numpy array

        data = dict(zip(feature_names, [float(v) for v in values]))
        # feature_names: ['Length','MW','Charge','ChargeDensity','pI',
        #                  'InstabilityInd','Aromaticity','AliphaticInd',
        #                  'BomanInd','HydrophRatio']

        mw              = data.get("MW", None)
        charge          = data.get("Charge", None)
        pi              = data.get("pI", None)
        instability     = data.get("InstabilityInd", None)
        boman           = data.get("BomanInd", None)
        aliphatic       = data.get("AliphaticInd", None)
        hydrophobic_r   = data.get("HydrophRatio", None)
        aromaticity     = data.get("Aromaticity", None)

        warnings_list: list[str] = [
            "modlamp 출력은 물리화학 디스크립터이며 ADMET 예측 결과가 아닙니다.",
            "D-AA 함유 서열에 L-AA 기준 디스크립터가 적용됩니다 — 부정확할 수 있음.",
        ]

        interpretation_notes: list[str] = []
        if instability is not None:
            if instability < 40:
                interpretation_notes.append(
                    f"InstabilityIndex={instability:.1f} < 40: 안정 (ProtParam 기준)"
                )
            else:
                interpretation_notes.append(
                    f"InstabilityIndex={instability:.1f} ≥ 40: 불안정 (ProtParam 기준)"
                )
        if boman is not None and boman > 1.0:
            interpretation_notes.append(
                f"BomanIndex={boman:.3f} > 1: 단백질 결합 가능성 높음"
            )
        if hydrophobic_r is not None:
            interpretation_notes.append(
                f"HydrophRatio={hydrophobic_r:.3f}: "
                + ("소수성 잔기 비율 높음" if hydrophobic_r > 0.5 else "소수성 잔기 비율 낮음")
            )

        return {
            "molecular_weight_da": mw,
            "charge_ph7": charge,
            "isoelectric_point": pi,
            "instability_index": instability,
            "boman_index": boman,
            "aliphatic_index": aliphatic,
            "hydrophobic_ratio": hydrophobic_r,
            "aromaticity": aromaticity,
            "raw_features": data,
            "confidence_grade": "P3",
            "tool": "modlamp v0.4.3 GlobalDescriptor.calculate_all()",
            "interpretation_notes": interpretation_notes,
            "warnings": warnings_list,
            "disclaimer": MODLAMP_CONFIDENCE["disclaimer"],
        }

    except Exception as e:
        return {
            "error": f"modlamp 계산 오류: {e}",
            "confidence_grade": "P3",
            "warnings": [str(e)],
        }


def check_pepadmet_web_access() -> dict:
    """pepADMET 웹서버 접근 가능성 확인."""
    try:
        import requests
        url = "https://pepadmet.ddai.tech/"
        resp = requests.get(url, timeout=10)
        status_code = resp.status_code
        reachable = 200 <= status_code < 400
    except Exception as e:
        status_code = f"error: {e}"
        reachable = False

    return {
        "url": "https://pepadmet.ddai.tech/",
        "http_status": status_code,
        "reachable": reachable,
        "message": (
            "✅ 접근 가능 — 수동 입력 또는 API 엔드포인트 확인 필요" if reachable
            else f"❌ 접근 불가 (HTTP {status_code}) — 수동 브라우저 접속 시도 필요"
        ),
    }


def predict_admet(
    sequence: str,
    seq_id: str = "query",
    use_modlamp_fallback: bool = True,
    check_pepadmet_web: bool = True,
    smiles: Optional[str] = None,
    use_local_gnn: bool = True,
) -> dict:
    """통합 ADMET 예측 wrapper.

    Args:
        sequence:               1문자 코드 펩타이드 서열
        seq_id:                 출력 레이블
        use_modlamp_fallback:   modlamp 디스크립터 계산 여부
        check_pepadmet_web:     pepADMET 웹 접근 확인 여부
        smiles:                 SMILES 문자열 (제공 시 로컬 GNN 독성 예측 활성화)
        use_local_gnn:          로컬 GNN 독성 예측 활성화 (smiles 필요, default True)

    Returns:
        통합 결과 딕셔너리
    """
    result: dict = {
        "input_sequence": sequence,
        "seq_id": seq_id,
        "tool_status": {},
        "pepadmet_web": None,
        "local_gnn_toxicity": None,
        "modlamp_descriptors": None,
        "warnings": [],
        "recommendations": [],
        "final_confidence_grade": "P3",
        "disclaimer": (
            "H-06 HEURISTIC: ADMET 예측 결과는 1차 triage 목적입니다. "
            "D-AA/DOTA 함유 서열에 대한 신뢰 가능한 ADMET 도구가 현재 존재하지 않습니다. "
            "wet-lab ADMET assay (독성, 혈청 안정성, PK/PD) 병행이 필수입니다."
        ),
    }

    # D-AA/비표준 AA 체크
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    invalid_aa = [aa for aa in sequence if aa.upper() not in valid_aa]
    if invalid_aa:
        result["warnings"].append(
            f"⚠️ 비표준/D-아미노산 감지: {invalid_aa}. "
            "현재 어떤 로컬 ADMET 도구도 D-AA를 지원하지 않습니다. "
            "(researcher 보고서 A-03 결론)"
        )

    # 로컬 GNN 독성 예측 (A.A5 chain — SMILES 제공 시)
    if use_local_gnn and smiles:
        loaded = _try_load_local_gnn()
        if loaded:
            gnn_result = predict_local_gnn_toxicity(smiles)
            result["local_gnn_toxicity"] = gnn_result
            if gnn_result.get("binary_toxicity_pred") is not None:
                pred_val = gnn_result["binary_toxicity_pred"]
                grade = "toxic_risk" if pred_val >= 0.5 else "low_risk"
                result["tool_status"]["local_gnn"] = (
                    f"success (binary_toxicity_pred={pred_val:.4f}, {grade})"
                )
                # P2 → 최종 신뢰도 P2로 상향
                result["final_confidence_grade"] = "P2"
            else:
                result["tool_status"]["local_gnn"] = (
                    f"failed: {gnn_result.get('error', 'unknown')}"
                )
                result["warnings"].append(
                    f"⚠️ 로컬 GNN 추론 실패: {gnn_result.get('error', 'unknown')}"
                )
        else:
            result["tool_status"]["local_gnn"] = (
                f"model_not_found: {_PEPADMET_MODEL_PATH}"
            )
            result["warnings"].append(
                f"⚠️ 로컬 GNN 모델 파일 없음: {_PEPADMET_MODEL_PATH}. "
                "A.A5Pc 재훈련 완료 후 사용 가능."
            )
    elif use_local_gnn and not smiles:
        result["tool_status"]["local_gnn"] = "skipped: smiles not provided"

    # pepADMET 웹 접근 확인
    if check_pepadmet_web:
        web_status = check_pepadmet_web_access()
        result["pepadmet_web"] = {
            **web_status,
            "confidence_grade": "P1",  # P2→P1 정정 (Wang 2026 JCIM R²=0.84-0.90; 인프라 HTTP 403과 분리)
            "n_endpoints": 29,
            "disclaimer": PEPADMET_CONFIDENCE["disclaimer"],
            "manual_instruction": (
                "pepADMET 웹서버 수동 사용: https://pepadmet.ddai.tech/ 접속 → "
                "서열 입력 → 29 ADMET endpoint 결과 다운로드 (JSON/CSV)"
            ),
        }
        result["tool_status"]["pepadmet_web"] = web_status["message"]

    # modlamp 디스크립터 fallback
    if use_modlamp_fallback:
        modlamp_result = predict_with_modlamp(sequence)
        result["modlamp_descriptors"] = modlamp_result
        result["tool_status"]["modlamp"] = (
            "success" if "error" not in modlamp_result else f"failed: {modlamp_result.get('error')}"
        )
        result["warnings"].extend(modlamp_result.get("warnings", []))

    # 권고사항
    result["recommendations"] = [
        "pepADMET 웹서버 수동 접속: https://pepadmet.ddai.tech/ (L-AA 서열 우선)",
        "D-AA/DOTA 후보: wet-lab ADMET assay 발주 필요 (신뢰 가능한 in-silico 도구 없음)",
        "CAPTP/ToxTeller: 독성 스크리닝용 (L-AA 선형 한정, CC-BY 라이선스)",
        "CycPeptMP: 환형 펩타이드 막 투과성 예측 전용 (별도 확인 필요)",
    ]

    return result


def predict_admet_batch(
    sequences: list[dict],  # [{"id": str, "sequence": str, "smiles": str (optional)}, ...]
    use_modlamp_fallback: bool = True,
    use_local_gnn: bool = True,
) -> list[dict]:
    """배치 ADMET 예측.

    Args:
        sequences:          [{"id": str, "sequence": str, "smiles": str (optional)}, ...]
        use_modlamp_fallback: modlamp 디스크립터 계산 여부
        use_local_gnn:      로컬 GNN 독성 예측 여부 (smiles 제공 시 활성화)

    Returns:
        각 서열에 대한 predict_admet() 결과 리스트
    """
    # 배치 실행 전 GNN 모델 1회 로드 (반복 로드 방지)
    if use_local_gnn:
        _try_load_local_gnn()

    results = []
    for item in sequences:
        seq_id = item.get("id", "query")
        sequence = item.get("sequence", "")
        smiles = item.get("smiles", None)
        r = predict_admet(
            sequence=sequence,
            seq_id=seq_id,
            use_modlamp_fallback=use_modlamp_fallback,
            check_pepadmet_web=False,  # 배치에서는 웹 체크 1회만
            smiles=smiles,
            use_local_gnn=use_local_gnn,
        )
        results.append(r)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ADMET 예측 wrapper (pepADMET 웹 stub + modlamp fallback)"
    )
    parser.add_argument("--sequence", help="1문자 코드 펩타이드 서열")
    parser.add_argument("--smiles", help="SMILES 문자열 (로컬 GNN 독성 예측 활성화)")
    parser.add_argument("--fasta", help="Multi-FASTA 입력 파일")
    parser.add_argument("--seq-id", default="query", help="서열 ID")
    parser.add_argument("--no-modlamp", action="store_true", help="modlamp fallback 비활성화")
    parser.add_argument("--no-local-gnn", action="store_true", help="로컬 GNN 독성 예측 비활성화")
    parser.add_argument("--check-web", action="store_true", help="pepADMET 웹 접근 확인")
    parser.add_argument("--output", help="출력 JSON 파일")

    args = parser.parse_args()

    if not args.sequence and not args.fasta:
        parser.error("--sequence 또는 --fasta 중 하나를 지정하세요.")

    if args.sequence:
        result = predict_admet(
            sequence=args.sequence,
            seq_id=args.seq_id,
            use_modlamp_fallback=not args.no_modlamp,
            check_pepadmet_web=args.check_web,
            smiles=args.smiles,
            use_local_gnn=not args.no_local_gnn,
        )
        results = [result]

    elif args.fasta:
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

        results = predict_admet_batch(sequences, use_modlamp_fallback=not args.no_modlamp)

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
