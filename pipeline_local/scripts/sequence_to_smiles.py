"""sequence_to_smiles.py
======================
펩타이드 서열 → SMILES 변환 유틸리티.

표준 L-아미노산 + D-아미노산 수식 표기 지원.
DOTA 킬레이터 부착 옵션 포함.

의존성:
    conda run -n peptools python sequence_to_smiles.py ...
    (rdkit, biopython 포함)

사용 예:
    python sequence_to_smiles.py --sequence AGCKNFFWKTFTSC
    python sequence_to_smiles.py --sequence AGCKNFFWKTFTSC --daa D-Phe:1
    python sequence_to_smiles.py --sequence AGCKNFFWKTFTSC --dota N-term

H-06 HEURISTIC 경고:
    SMILES 변환은 1차 화학 구조 표현이며 실제 3D 구조/SS bond 입체화학을
    완전히 재현하지 않는다. wet-lab 합성 전 전문 화학자 검토 필수.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

# RDKit 임포트 (peptools env 필요)
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

# 표준 L-아미노산 SMILES (RDKit canonical, N-Cα-C(=O) backbone 단일 잔기)
L_AA_SMILES: dict[str, str] = {
    "A": "N[C@@H](C)C(=O)O",
    "R": "N[C@@H](CCCNC(=N)N)C(=O)O",
    "N": "N[C@@H](CC(=O)N)C(=O)O",
    "D": "N[C@@H](CC(=O)O)C(=O)O",
    "C": "N[C@@H](CS)C(=O)O",
    "E": "N[C@@H](CCC(=O)O)C(=O)O",
    "Q": "N[C@@H](CCC(=O)N)C(=O)O",
    "G": "NCC(=O)O",
    "H": "N[C@@H](Cc1cnc[nH]1)C(=O)O",
    "I": "N[C@@H]([C@@H](CC)C)C(=O)O",
    "L": "N[C@@H](CC(C)C)C(=O)O",
    "K": "N[C@@H](CCCCN)C(=O)O",
    "M": "N[C@@H](CCSC)C(=O)O",
    "F": "N[C@@H](Cc1ccccc1)C(=O)O",
    "P": "N1CCC[C@H]1C(=O)O",
    "S": "N[C@@H](CO)C(=O)O",
    "T": "N[C@@H]([C@@H](O)C)C(=O)O",
    "W": "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)O",
    "Y": "N[C@@H](Cc1ccc(O)cc1)C(=O)O",
    "V": "N[C@@H](C(C)C)C(=O)O",
}

# D-아미노산 SMILES (키랄 태그 반전)
# L-AA에서 [C@@H] → [C@H] 로 반전 (또는 D-AA 전용 테이블)
D_AA_SMILES: dict[str, str] = {
    "D-Ala": "N[C@H](C)C(=O)O",
    "D-Arg": "N[C@H](CCCNC(=N)N)C(=O)O",
    "D-Asn": "N[C@H](CC(=O)N)C(=O)O",
    "D-Asp": "N[C@H](CC(=O)O)C(=O)O",
    "D-Cys": "N[C@H](CS)C(=O)O",
    "D-Glu": "N[C@H](CCC(=O)O)C(=O)O",
    "D-Gln": "N[C@H](CCC(=O)N)C(=O)O",
    "D-His": "N[C@H](Cc1cnc[nH]1)C(=O)O",
    "D-Ile": "N[C@H]([C@H](CC)C)C(=O)O",
    "D-Leu": "N[C@H](CC(C)C)C(=O)O",
    "D-Lys": "N[C@H](CCCCN)C(=O)O",
    "D-Met": "N[C@H](CCSC)C(=O)O",
    "D-Phe": "N[C@H](Cc1ccccc1)C(=O)O",
    "D-Pro": "N1CCC[C@@H]1C(=O)O",
    "D-Ser": "N[C@H](CO)C(=O)O",
    "D-Thr": "N[C@H]([C@H](O)C)C(=O)O",
    "D-Trp": "N[C@H](Cc1c[nH]c2ccccc12)C(=O)O",
    "D-Tyr": "N[C@H](Cc1ccc(O)cc1)C(=O)O",
    "D-Val": "N[C@H](C(C)C)C(=O)O",
    # 비천연 아미노산 (SST 유사체용)
    "D-Nal": "N[C@H](Cc1ccc2ccccc2c1)C(=O)O",    # D-2-Naphthylalanine (Lanreotide)
    "Cha":   "N[C@@H](CC1CCCCC1)C(=O)O",          # L-Cyclohexylalanine (SST 유사체)
    "Orn":   "N[C@@H](CCCN)C(=O)O",               # L-Ornithine
}

# DOTA 킬레이터 SMILES (간소화된 표현)
DOTA_SMILES = (
    "OC(=O)CN1CCN(CC(=O)O)CCN(CC(=O)O)CCN(CC(=O)O)CC1"
)
DOTA_LINKER_SMILES = (
    "OC(=O)CN1CCN(CC(=O)O)CCN(CC(=O)O)CCN(CC(=O)O)CC1"
    ".OC(=O)C"  # simplified linker: 아마이드 결합으로 N-term 또는 Lys ε-amine에 연결
)


def sequence_to_linear_smiles(
    sequence: str,
    daa_positions: Optional[dict[int, str]] = None,
) -> dict[str, object]:
    """표준 서열을 선형 펩타이드 SMILES로 변환.

    Args:
        sequence:      1문자 코드 펩타이드 서열 (표준 L-AA)
        daa_positions: {위치(1-indexed): 'D-Phe'} 형태의 D-아미노산 치환 딕셔너리

    Returns:
        {
            "smiles": str,          # 선형 펩타이드 SMILES (condensed, non-validated)
            "sequence": str,
            "d_aa_substitutions": dict,
            "warnings": list[str],
            "disclaimer": str,
        }

    참고:
        이 함수는 단순 SMILES 연결 방식으로, RDKit를 통한 전체 molecule 빌드를
        수행하지 않습니다 (SS bond, 환화 등 포함 시 별도 처리 필요).
        H-06: 출력 SMILES는 in-silico 1차 구조 표현 — wet-lab 합성 대체 불가.
    """
    if daa_positions is None:
        daa_positions = {}

    warnings: list[str] = []
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    residue_smiles: list[str] = []

    for i, aa in enumerate(sequence, 1):
        if aa not in valid_aa:
            warnings.append(f"위치 {i}: '{aa}' — 비표준 아미노산. 건너뜁니다.")
            continue

        if i in daa_positions:
            daa_name = daa_positions[i]
            if daa_name in D_AA_SMILES:
                residue_smiles.append(D_AA_SMILES[daa_name])
                warnings.append(f"위치 {i}: L-{aa} → {daa_name} (D-AA) 치환 적용")
            else:
                warnings.append(f"위치 {i}: '{daa_name}' D-AA SMILES 미등록. L-AA 유지.")
                residue_smiles.append(L_AA_SMILES[aa])
        else:
            residue_smiles.append(L_AA_SMILES[aa])

    # 단순 연결 SMILES (펩타이드 결합은 별도 처리 필요)
    # RDKit 사용 가능 시 실제 펩타이드 결합 건설
    if RDKIT_AVAILABLE and residue_smiles:
        combined_smiles = _build_peptide_smiles_rdkit(residue_smiles, warnings)
    else:
        # Fallback: 콤마 구분 (비정규 — 주의)
        combined_smiles = ".".join(residue_smiles)
        warnings.append("RDKit 미사용: 잔기 SMILES를 단순 연결. 실제 펩타이드 결합 미형성.")

    # SS bond 포함 여부 체크
    cys_count = sequence.count("C")
    if cys_count >= 2:
        warnings.append(
            f"Cys 잔기 {cys_count}개 감지 — SS bond (이황화결합) 미형성 상태."
            " 환화 SMILES가 필요하면 --cyclic 옵션 또는 전문가 검토 필요."
        )

    return {
        "smiles": combined_smiles,
        "sequence": sequence,
        "length": len(sequence),
        "d_aa_substitutions": daa_positions,
        "cys_count": cys_count,
        "warnings": warnings,
        "disclaimer": (
            "H-06 HEURISTIC: SMILES는 1차 화학 구조 표현입니다. "
            "이황화결합(SS bond), 환화, D-AA 키랄 정확성은 wet-lab 합성 전 "
            "전문 화학자 검토가 필수입니다. pepADMET 등 외부 도구 입력 시 "
            "해당 도구의 SMILES 수용 범위를 별도 확인하세요."
        ),
        "confidence_grade": "HEURISTIC",
    }


def _build_peptide_smiles_rdkit(
    residue_smiles_list: list[str],
    warnings: list[str],
) -> str:
    """RDKit를 사용한 실제 펩타이드 결합 SMILES 생성.

    Note:
        이 구현은 단순 아미드 결합 연결 방식으로 SS bond 미형성.
        N-terminus와 C-terminus는 유리 상태 (NH2-...-COOH).
    """
    if not RDKIT_AVAILABLE:
        warnings.append("RDKit 없음: 단순 연결 fallback 사용")
        return ".".join(residue_smiles_list)

    try:
        # 각 아미노산을 Mol로 변환
        mols = []
        for smi in residue_smiles_list:
            m = Chem.MolFromSmiles(smi)
            if m is None:
                warnings.append(f"SMILES 파싱 실패: {smi}")
                return ".".join(residue_smiles_list)
            mols.append(m)

        if len(mols) == 1:
            return Chem.MolToSmiles(mols[0])

        # 펩타이드 결합 형성: 간단한 SMILES 연결 패턴 사용
        # (실제로는 HELM notation 또는 전용 펩타이드 라이브러리 사용 권장)
        peptide_smi = _link_amino_acids_smiles(residue_smiles_list)
        mol = Chem.MolFromSmiles(peptide_smi)
        if mol is None:
            warnings.append("펩타이드 SMILES 빌드 실패 — 단순 연결 fallback")
            return ".".join(residue_smiles_list)
        return Chem.MolToSmiles(mol)

    except Exception as e:
        warnings.append(f"RDKit 오류: {e} — 단순 연결 fallback")
        return ".".join(residue_smiles_list)


def _link_amino_acids_smiles(residue_smiles_list: list[str]) -> str:
    """아미노산 SMILES를 펩타이드 결합(아마이드)으로 연결.

    단순화된 구현: Gly 기반 SMILES 패턴 연결.
    복잡한 서열에는 HELM 표준 또는 peptide SMILES 전문 라이브러리 사용 권장.
    """
    # 각 잔기에서 -OH (카르복실) 제거하고 N과 연결
    # 간소화: 첫 잔기 N-term, 마지막 잔기 C-term, 중간은 결합
    chain_parts = []
    for i, smi in enumerate(residue_smiles_list):
        # -C(=O)O 패턴에서 O 제거 → 아마이드 결합 형성
        # 이 단순화된 구현은 일부 복잡한 잔기에서 틀릴 수 있음
        if i < len(residue_smiles_list) - 1:
            part = smi.replace("C(=O)O", "C(=O)")
        else:
            part = smi
        chain_parts.append(part)

    return "".join(chain_parts)


def get_d_aa_smiles(name: str) -> Optional[str]:
    """D-아미노산 이름으로 SMILES 반환.

    Args:
        name: 'D-Phe', 'D-Trp', 'D-Nal' 등

    Returns:
        SMILES 문자열 또는 None (미등록 시)
    """
    return D_AA_SMILES.get(name)


def add_dota_to_smiles(
    peptide_smiles: str,
    attachment_site: str = "N-term",
) -> dict[str, object]:
    """펩타이드 SMILES에 DOTA 킬레이터 부착.

    Args:
        peptide_smiles: 기존 펩타이드 SMILES
        attachment_site: 'N-term' (기본) 또는 'Lys-epsilon'

    Returns:
        {
            "smiles": str,  # DOTA 결합 펩타이드 SMILES (단순 표현)
            "warnings": list[str],
            "disclaimer": str,
        }

    경고:
        이 함수는 DOTA를 단순 컴포넌트로 추가하는 1차 구조 표현입니다.
        실제 아마이드 결합 형성, 방사성 금속 킬레이션 기하학은 포함하지 않습니다.
        (H-06: wet-lab 합성/방사화학 수율 예측 불가)
    """
    warnings_list: list[str] = []

    if attachment_site == "N-term":
        combined = f"{DOTA_SMILES}.{peptide_smiles}"
        warnings_list.append(
            "N-term DOTA: 아마이드 결합 미형성 — 단순 컴포넌트 표현. "
            "실제 결합은 DOTA-NHS ester + N-terminus 아민 반응으로 형성됨."
        )
    elif attachment_site == "Lys-epsilon":
        combined = f"{DOTA_SMILES}.{peptide_smiles}"
        warnings_list.append(
            "Lys ε-amine DOTA: 아마이드 결합 미형성 — 단순 컴포넌트 표현. "
            "Lys 잔기 위치(1-indexed) 지정이 필요합니다."
        )
    else:
        combined = peptide_smiles
        warnings_list.append(f"알 수 없는 attachment_site: {attachment_site}. DOTA 추가 안 됨.")

    return {
        "smiles": combined,
        "dota_attached": attachment_site if attachment_site in ("N-term", "Lys-epsilon") else None,
        "warnings": warnings_list,
        "disclaimer": (
            "H-06 HEURISTIC: DOTA-펩타이드 결합 SMILES는 구조적 가이드 목적입니다. "
            "방사화학 수율, 금속 킬레이션 안정성, MALDI-TOF 확인은 wet-lab 필수. "
            "(reviewer-chemistry 검토 권장)"
        ),
        "confidence_grade": "HEURISTIC",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="펩타이드 서열 → SMILES 변환 유틸리티 (D-AA + DOTA 지원)"
    )
    parser.add_argument("--sequence", required=True, help="1문자 코드 펩타이드 서열 (예: AGCKNFFWKTFTSC)")
    parser.add_argument(
        "--daa",
        help="D-AA 치환: 'position:name' 쉼표 구분 (예: '1:D-Phe,3:D-Trp')",
        default=None,
    )
    parser.add_argument(
        "--dota",
        help="DOTA 부착 사이트: 'N-term' 또는 'Lys-epsilon'",
        default=None,
    )
    parser.add_argument("--output", help="출력 JSON 파일 경로", default=None)

    args = parser.parse_args()

    # D-AA 파싱
    daa_positions: dict[int, str] = {}
    if args.daa:
        for token in args.daa.split(","):
            token = token.strip()
            if ":" in token:
                pos_str, name = token.split(":", 1)
                daa_positions[int(pos_str)] = name.strip()

    # SMILES 변환
    result = sequence_to_linear_smiles(args.sequence, daa_positions)

    # DOTA 부착
    if args.dota:
        dota_result = add_dota_to_smiles(result["smiles"], args.dota)
        result["smiles_with_dota"] = dota_result["smiles"]
        result["dota_attachment"] = args.dota
        result["warnings"].extend(dota_result["warnings"])

    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"저장: {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
