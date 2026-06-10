#!/usr/bin/env python3
"""
Arm 3: SSTR2 De Novo 펩타이드 바인더 설계
============================================
1. RFdiffusion: SSTR2 바인딩 포켓에 대한 새 펩타이드 백본 설계
2. ProteinMPNN: 백본 → 최적 서열
3. ESMFold: 설계 서열의 폴딩 검증

사용법:
    python 07_sstr2_denovo_binder.py
"""

import json
from datetime import datetime
from pathlib import Path
try:
    from .rfdiffusion_client import get_client as get_rfdiffusion
    from .proteinmpnn_client import get_client as get_proteinmpnn
    from .esmfold_client import get_client as get_esmfold
except ImportError:
    from rfdiffusion_client import get_client as get_rfdiffusion
    from proteinmpnn_client import get_client as get_proteinmpnn
    from esmfold_client import get_client as get_esmfold

PROJECT_ROOT = Path(__file__).parent.parent
RECEPTOR_PDB = PROJECT_ROOT / "results" / "sstr2_docking" / "sstr2_receptor.pdb"
POCKET_JSON = PROJECT_ROOT / "results" / "sstr2_docking" / "binding_pocket.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "sstr2_docking" / "arm3_denovo"

NUM_DESIGNS = 5       # RFdiffusion 설계 수
SEQS_PER_BACKBONE = 4  # ProteinMPNN 서열 수 per 백본
PLDDT_THRESHOLD = 50   # ESMFold 통과 기준


def run_arm3():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 바인딩 포켓 정보 로드
    if not POCKET_JSON.exists():
        raise FileNotFoundError(f"binding_pocket.json을 찾을 수 없습니다: {POCKET_JSON}")

    pocket_info = json.loads(POCKET_JSON.read_text())
    hotspot_res = pocket_info.get("hotspot_res", [])
    rfdiff_contigs = pocket_info.get("rfdiffusion", {}).get("contigs", "B1-369/0 10-30")

    print("=" * 60)
    print("Arm 3: SSTR2 De Novo 펩타이드 바인더 설계")
    print("=" * 60)
    print(f"수용체: {RECEPTOR_PDB}")
    print(f"핫스팟 잔기: {len(hotspot_res)}개")
    print(f"Contigs: {rfdiff_contigs}")
    print(f"설계 수: {NUM_DESIGNS}개")

    rfdiff = get_rfdiffusion()
    mpnn = get_proteinmpnn()
    esmfold = get_esmfold()

    all_results = []

    # ── Step 1: RFdiffusion 백본 설계 ────────────────────
    print(f"\n[Step 1] RFdiffusion 바인더 백본 설계")

    backbones = []
    for i in range(NUM_DESIGNS):
        print(f"  [{i+1}/{NUM_DESIGNS}] 설계 중 (seed={i})...")
        try:
            result = rfdiff.design_binder(
                pdb_path=RECEPTOR_PDB,
                contigs=rfdiff_contigs,
                hotspot_res=hotspot_res[:10],  # 상위 10개 핫스팟
                diffusion_steps=50,
                random_seed=i,
            )
            backbone_pdb = result.get("output_pdb", "")
            elapsed = result.get("elapsed_ms", 0)

            if backbone_pdb:
                # 백본 PDB 저장
                bb_path = OUTPUT_DIR / f"backbone_{i:02d}.pdb"
                bb_path.write_text(backbone_pdb)
                backbones.append({
                    "idx": i,
                    "pdb_path": str(bb_path),
                    "pdb_content": backbone_pdb,
                    "elapsed_ms": elapsed,
                })
                print(f"    -> 성공 ({elapsed}ms)")
            else:
                print(f"    -> 빈 결과")
        except Exception as e:
            print(f"    -> 오류: {e}")
            backbones.append({"idx": i, "error": str(e)})

    print(f"  성공: {sum(1 for b in backbones if 'pdb_content' in b)}/{NUM_DESIGNS}")

    # ── Step 2: ProteinMPNN 서열 설계 ────────────────────
    print(f"\n[Step 2] ProteinMPNN 서열 설계")

    designed_sequences = []
    for bb in backbones:
        if "pdb_content" not in bb:
            continue

        idx = bb["idx"]
        print(f"  백본 {idx:02d}:")
        try:
            result = mpnn.predict(
                input_pdb=bb["pdb_content"],
                num_seq_per_target=SEQS_PER_BACKBONE,
                sampling_temp=0.2,
            )

            # 응답 파싱 (FASTA 또는 JSON)
            sequences = []
            if isinstance(result, dict):
                if "sequences" in result:
                    raw = result["sequences"]
                    if isinstance(raw, str):
                        entries = mpnn.parse_fasta(raw)
                        sequences = [e["sequence"] for e in entries]
                    elif isinstance(raw, list):
                        sequences = raw
                elif "output" in result:
                    raw = result["output"]
                    if isinstance(raw, str):
                        entries = mpnn.parse_fasta(raw)
                        sequences = [e["sequence"] for e in entries]

            for j, seq in enumerate(sequences):
                designed_sequences.append({
                    "backbone_idx": idx,
                    "seq_idx": j,
                    "sequence": seq,
                })
                print(f"    서열 {j}: {seq[:40]}{'...' if len(seq) > 40 else ''}")

        except Exception as e:
            print(f"    오류: {e}")

    print(f"  총 서열: {len(designed_sequences)}개")

    # ── Step 3: ESMFold 폴딩 검증 ────────────────────────
    print(f"\n[Step 3] ESMFold 폴딩 검증 (pLDDT > {PLDDT_THRESHOLD})")

    verified_designs = []
    for ds in designed_sequences:
        seq = ds["sequence"]
        label = f"bb{ds['backbone_idx']:02d}_seq{ds['seq_idx']}"
        print(f"  [{label}] {seq[:30]}...")

        try:
            result = esmfold.predict(seq)

            # pLDDT 추출
            plddt = None
            pdb_content = None
            if isinstance(result, dict):
                plddt = result.get("mean_plddt", result.get("plddt", None))
                pdb_content = result.get("pdbs", [None])[0] if "pdbs" in result else result.get("pdb", result.get("output", None))

            if plddt is None:
                print(f"    -> pLDDT 없음 (설계 제외)")
                continue
            if not pdb_content:
                print(f"    -> 구조 없음 (설계 제외)")
                continue

            if isinstance(plddt, (list, tuple)):
                plddt = sum(plddt) / len(plddt) if plddt else 0.0

            try:
                plddt = float(plddt)
            except (TypeError, ValueError):
                print(f"    -> pLDDT 형식 오류 ({plddt})")
                continue

            ds["plddt"] = plddt
            ds["pdb_content"] = pdb_content

            if pdb_content:
                pdb_path = OUTPUT_DIR / f"esmfold_{label}.pdb"
                pdb_path.write_text(pdb_content)
                ds["esmfold_pdb"] = str(pdb_path)

            if plddt >= PLDDT_THRESHOLD:
                verified_designs.append(ds)
                print(f"    -> PASS (pLDDT={plddt:.1f})")
            else:
                print(f"    -> FAIL (pLDDT={plddt:.1f} < {PLDDT_THRESHOLD})")

        except Exception as e:
            print(f"    -> 오류: {e}")

    # ── 결과 저장 ────────────────────────────────────────
    print(f"\n[Step 4] 결과 저장")

    output_file = OUTPUT_DIR / f"arm3_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    save_data = {
        "pipeline": "Arm 3: De Novo Peptide Binder Design",
        "receptor_pdb": str(RECEPTOR_PDB),
        "hotspot_res": hotspot_res,
        "contigs": rfdiff_contigs,
        "num_backbone_designs": NUM_DESIGNS,
        "num_sequences_per_backbone": SEQS_PER_BACKBONE,
        "plddt_threshold": PLDDT_THRESHOLD,
        "total_backbones": sum(1 for b in backbones if "pdb_content" in b),
        "total_sequences": len(designed_sequences),
        "verified_designs": len(verified_designs),
        "designs": [
            {
                "backbone_idx": d["backbone_idx"],
                "seq_idx": d["seq_idx"],
                "sequence": d["sequence"],
                "plddt": d.get("plddt"),
            }
            for d in verified_designs
        ],
        "timestamp": datetime.now().isoformat(),
    }
    output_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False))
    print(f"결과 저장: {output_file}")

    # ── 요약 ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("Arm 3 요약")
    print(f"{'=' * 60}")
    print(f"  RFdiffusion 백본:  {save_data['total_backbones']}/{NUM_DESIGNS}")
    print(f"  ProteinMPNN 서열: {save_data['total_sequences']}개")
    print(f"  ESMFold 검증 통과: {save_data['verified_designs']}개")
    if verified_designs:
        print(f"\n  검증된 펩타이드 서열:")
        for d in verified_designs:
            plddt_str = f"pLDDT={d['plddt']:.1f}" if d.get('plddt') else "pLDDT=N/A"
            print(f"    bb{d['backbone_idx']:02d}_seq{d['seq_idx']}: "
                  f"{d['sequence'][:40]}  ({plddt_str})")
        print(f"\n  다음 단계: AlphaFold3 Server에서 SSTR2 + 펩타이드 복합체 예측")

    return verified_designs


if __name__ == "__main__":
    run_arm3()
