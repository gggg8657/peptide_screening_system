"""pharmacology_guards.py
========================
Anti-Hallucination Guards for Pharmacological Lookup Tables and Calculations.

harness Stage 5 적용 (tools/harness-adaptation/INTEGRATION_PLAN.md).
기존 약리학 코드를 수정하지 않고, **알려진 정답 회귀 + 범위 가드**를
선언적으로 제공하여 환각/실수에 의한 lookup table 손상을 차단한다.

도메인 환각 시나리오 (tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md §3):
  H-01 파라미터 테이블 오기재   ← LITERATURE_VALUES + assert_literature_value()
  H-02 부호 규약 역전           ← SIGN_CONVENTIONS + check_sign_convention()
  H-03 척도 혼용                ← SCALE_RANGES + assert_in_range()
  H-04 PyRosetta 채점 환각      ← (별도 모듈, 본 모듈은 펩타이드 약리학만)
  H-05 반감기 참조 종 혼동      ← LITERATURE_VALUES["nend_half_life"]에 species 명시
  H-06 계산 불가능을 계산 가능한 척 ← HEURISTIC_FUNCTION_DISCLAIMERS + check_heuristic_function()
       (VR-cycle-09 closure 2026-05-11) — pre-wet-lab screening 함수의 정직한 명세화

이 모듈은 stand-alone — 외부 패키지(AG_src.pipeline.pharma_properties 등) import 없이
선언적 비교만 수행. 따라서 import 실패에 무관하게 회귀 검증 가능.

Public API:
    LITERATURE_VALUES                  : Dict — 알려진 정답 lookup table
    SCALE_RANGES                       : Dict — 각 척도의 생물학적 합리 범위
    SIGN_CONVENTIONS                   : Dict — 각 척도의 부호 의미
    HEURISTIC_FUNCTION_DISCLAIMERS     : Dict — 휴리스틱 함수의 정직한 명세 (H-06 가드)
    ENDPOINT_CONFIDENCE                : Dict — API 엔드포인트별 신뢰도 메타데이터 (P1-4)
    assert_literature_value(...)       : 단일 값이 문헌 정답과 일치 검증
    assert_in_range(...)               : GATE-C 범위 검사
    check_sign_convention(...)         : 부호 규약 위반 탐지
    audit_table(...)                   : 전체 테이블을 LITERATURE_VALUES와 대조
    is_heuristic_function(qualname)    : 휴리스틱 함수 여부 확인 (H-06 가드)
    check_pepadmet_applicability(...)  : pepADMET 적용 가능성 가드 (A-03)
    check_pepmsnd_local_applicability() : Layer2 로컬 PEPlife2-GAT 회귀 적용 가능성 (2026-05-20)
    attach_confidence(response, path)  : API 응답에 confidence_grade 자동 주입 (P1-4)

회귀 테스트: pipeline_local/tests/test_pharmacology_guards.py (39개, 2026-05-13 기준)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. 알려진 정답 lookup table (Literature Ground Truth)
# ---------------------------------------------------------------------------
#
# 각 항목은 다음 구조:
#   {
#       "key": (expected_value, "Author Year Journal Vol:Page", "comment")
#   }
#
# 본 정답은 코드베이스의 현재 값이 아닌 **문헌 직접 인용**이다.
# 코드의 lookup table을 이 정답과 대조하여 무단 변경/오기재를 탐지한다.

LITERATURE_VALUES: Dict[str, Dict[str, Tuple[Any, str, str]]] = {
    # Kyte & Doolittle 1982, J Mol Biol 157:105-132, Table I
    "kyte_doolittle": {
        "I": (4.5,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "isoleucine — most hydrophobic"),
        "V": (4.2,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "valine"),
        "L": (3.8,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "leucine"),
        "F": (2.8,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "phenylalanine"),
        "C": (2.5,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "cysteine"),
        "M": (1.9,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "methionine"),
        "A": (1.8,  "Kyte & Doolittle 1982 J Mol Biol 157:105", "alanine"),
        "G": (-0.4, "Kyte & Doolittle 1982 J Mol Biol 157:105", "glycine"),
        "P": (-1.6, "Kyte & Doolittle 1982 J Mol Biol 157:105", "proline"),
        "K": (-3.9, "Kyte & Doolittle 1982 J Mol Biol 157:105", "lysine"),
        "R": (-4.5, "Kyte & Doolittle 1982 J Mol Biol 157:105", "arginine — most hydrophilic"),
    },
    # Radzicka & Wolfenden 1988, Biochemistry 27:1664 (vapor→cyclohexane→water transfer)
    # NOTE: 본 코드베이스(AG_src/.../pharma_properties.py L41-46)는
    #       Boman convention(positive = hydrophilic, protein-binding potential 높음)으로
    #       부호를 변환하여 저장. 즉 RW_TRANSFER[aa] = -Radzicka1988_value[aa].
    "radzicka_wolfenden_boman_convention": {
        "R": (14.92, "Boman 2003 J Intern Med 254:197 (sign-flipped from Radzicka 1988)", "most hydrophilic / strongest protein binder"),
        "D": (8.72,  "Boman 2003 J Intern Med 254:197",                                   "aspartate"),
        "E": (6.81,  "Boman 2003 J Intern Med 254:197",                                   "glutamate"),
        "N": (6.64,  "Boman 2003 J Intern Med 254:197",                                   "asparagine"),
        "K": (5.55,  "Boman 2003 J Intern Med 254:197",                                   "lysine"),
        "P": (-2.54, "Boman 2003 J Intern Med 254:197",                                   "proline — note: literature defect was P=0.0 in earlier code"),
        "S": (3.40,  "Boman 2003 J Intern Med 254:197",                                   "serine — note: literature defect was S=1.15 in earlier code"),
        "A": (-1.81, "Boman 2003 J Intern Med 254:197",                                   "alanine"),
        "I": (-4.92, "Boman 2003 J Intern Med 254:197",                                   "isoleucine — most hydrophobic"),
        "L": (-4.92, "Boman 2003 J Intern Med 254:197",                                   "leucine"),
    },
    # Varshavsky 1996, PNAS 93:12142-12149 (mammalian reticulocyte half-life, hours)
    # NOTE: half-life는 종(species)·조건(cell type)별로 다르다.
    #       본 정답은 mammalian reticulocyte 기준. 효모 등 다른 종은 다른 값.
    "nend_half_life_mammalian_hours": {
        "M": (30.0, "Varshavsky 1996 PNAS 93:12142", "methionine — stable, mammalian reticulocyte"),
        "S": (30.0, "Varshavsky 1996 PNAS 93:12142", "serine — stable"),
        "A": (30.0, "Varshavsky 1996 PNAS 93:12142", "alanine — stable"),
        "V": (30.0, "Varshavsky 1996 PNAS 93:12142", "valine — stable"),
        "G": (30.0, "Varshavsky 1996 PNAS 93:12142", "glycine — stable"),
        "P": (30.0, "Varshavsky 1996 PNAS 93:12142", "proline — stable, NOT 20 (common literature mistake)"),
        "T": (30.0, "Varshavsky 1996 PNAS 93:12142", "threonine — stable"),
        "R": (1.0,  "Varshavsky 1996 PNAS 93:12142", "arginine — very unstable"),
        "K": (1.3,  "Varshavsky 1996 PNAS 93:12142", "lysine — very unstable"),
        "F": (1.1,  "Varshavsky 1996 PNAS 93:12142", "phenylalanine — very unstable"),
    },
    # Lehninger pKa set
    "lehninger_pka_sidechain": {
        "D": (3.65,  "Lehninger Biochemistry",        "aspartate"),
        "E": (4.25,  "Lehninger Biochemistry",        "glutamate"),
        "H": (6.00,  "Lehninger Biochemistry",        "histidine"),
        "C": (8.18,  "Lehninger Biochemistry",        "cysteine"),
        "Y": (10.07, "Lehninger Biochemistry",        "tyrosine"),
        "K": (10.53, "Lehninger Biochemistry",        "lysine"),
        "R": (12.48, "Lehninger Biochemistry",        "arginine"),
    },
    # ---------------------------------------------------------------------------
    # modification_conflict_rules — 도메인 출처 추적용 (A-8, Phase 5)
    # 각 규칙의 화학적 근거 문헌을 추적하기 위한 레지스트리.
    # 향후 이 테이블을 변경할 경우 인용 의무화를 보장한다.
    # 회귀 테스트는 별도로 추가하지 않음 — 출처 추적 전용.
    # ---------------------------------------------------------------------------
    "modification_conflict_rules": {
        "C-01": (
            "ERROR",
            "Knudsen LB & Lau J (2019) Front Endocrinol 10:155 doi:10.3389/fendo.2019.00155",
            "Lys ε-NH2 단일 acylation 부위 — fatty_acid + pegylation 동시 불가",
        ),
        "C-02": (
            "ERROR",
            "Knudsen & Lau 2019 Front Endocrinol 10:155; Hermanson GT (2013) Bioconjugate Techniques 3rd ed. Ch.2",
            "fatty_acid NHS-ester 아실화 부위 선택성 — Lys/N-terminal 외 ERROR",
        ),
        "C-03": (
            "WARNING",
            "Merrifield RB (1963) J Am Chem Soc 85:2149; IUPAC-IUB JCBN (1984) Eur J Biochem 138:9",
            "Gly 비키랄성 — D-Gly = L-Gly, no-op",
        ),
        "C-04": (
            "ERROR",
            "Reubi JC et al. (2000) Eur J Nucl Med 28:836; Veber DF et al. (1978) PNAS 75:2636; Pellegrini & Mierke (1999) Biopolymers 51:208",
            "SS bond Cys D-치환 → β-turn 손상, 활성 ~10× 감소 (Phase 5 ERROR 격상)",
        ),
        "C-05": (
            "WARNING",
            "Reubi 2000 Eur J Nucl Med 28:836; Andreu D et al. (1994) Methods Mol Biol 35:91",
            "자연 Cys-Cys SS bond 존재 시 cyclization 중복 지정",
        ),
        "C-06": (
            "ERROR",
            "(language-agnostic array bounds validation)",
            "position 범위/타입 유효성 — 1-indexed 정수, [1, len(seq)] 범위",
        ),
        "C-07": (
            "ERROR",
            "Reubi JC et al. (2000) Eur J Nucl Med 28:836; Wadas TJ et al. (2010) Chem Rev 110:2858",
            "DOTA chelator stoichiometry — 펩타이드당 1개 (radioisotope binding 단일성, theranostic 라벨링 필수)",
        ),
        "C-08": (
            "ERROR",
            "Mosberg HI et al. (1983) PNAS 80:5871; Veber DF et al. (1978) PNAS 75:2636",
            "SS bond 양쪽 Cys 동시 D-치환 → D,D-cystine geometry 비호환",
        ),
        "C-09": (
            "ERROR",
            "Davies JS (2003) J Pept Sci 9:471; Knudsen & Lau 2019 Front Endocrinol 10:155",
            "head-to-tail cyclization + N-term acylation — α-NH2 소진 충돌",
        ),
        "C-10": (
            "ERROR",
            "(pipeline schema integrity — Fmoc building block ambiguity)",
            "동일 position substitution + d_amino_acid 동시 지정 — 의미 충돌",
        ),
        "C-99": (
            "ERROR",
            "(internal — reserved rule_id for unexpected exceptions in check_conflicts)",
            "규칙 실행 중 내부 예외 발생 시 호출자에 전달하기 위한 예약 rule_id",
        ),
    },
    # Ikai 1980 — aliphatic index 계산 계수
    # Reference: Ikai AJ (1980) Thermostability and aliphatic index of globular proteins.
    #            J Biochem 88:1895-1898. doi:10.1093/oxfordjournals.jbchem.a133168
    # Formula: AI = X_Ala * 100 + coeff_V * X_Val * 100 + coeff_I * (X_Ile + X_Leu) * 100
    # 100 곱은 mole fraction → per 100 residue 단위
    "ikai_aliphatic_index": {
        "Val_coefficient":  (2.9, "Ikai 1980 J Biochem 88:1895-1898", "Valine coefficient in aliphatic index formula"),
        "Ile_coefficient":  (3.9, "Ikai 1980 J Biochem 88:1895-1898", "Isoleucine coefficient in aliphatic index formula"),
        "Leu_coefficient":  (3.9, "Ikai 1980 J Biochem 88:1895-1898", "Leucine coefficient in aliphatic index formula (same as Ile)"),
    },
    # SST14 SSTR2 도킹 ΔG 레퍼런스 (A-04/A-05 — Hard Cutoff 기준선)
    # ΔG 단위: REU proxy (-100 * iPTM). Boltz-2 도킹 산출값.
    # 음수 값: 더 음수일수록 더 강한 결합. Hard Cutoff: candidate_ddg ≤ ref_ddg.
    # 출처: KAERI-AIRL P0 commit ed86fa0 — SST14(AGCKNFFWKTFTSC) vs SSTR2 Boltz2 dock.
    "SST14_SSTR2_ref_ddg_boltz2": {
        "ref_ddg_reu": (
            -95.024,
            "KAERI A-05 2026-05-19 SSTR2_7XNA Boltz-2",
            "SST14 AGCKNFFWKTFTSC vs SSTR2 Boltz2 dock ΔG 레퍼런스. "
            "A-04 Hard Cutoff 기준선: candidate.ddg ≤ -95.024 REU 통과.",
        ),
    },
    # A-05: SST14 SSTR2 FlexPepDock 레퍼런스 (PyRosetta InterfaceAnalyzerMover ddG)
    # ΔG 단위: REU. PyRosetta FlexPepDock 실측 (2026-05-19).
    # 알려진 한계: reference complex 부재 → Fallback 모드(확장 conformation) → 양수 값.
    # 상대 비교: candidate < 553.857 REU → SST14보다 유리한 결합 에너지.
    # A-05 rosetta_ddg_max = 553.857 × 0.9 = 498.4713 REU.
    # A-04 composite_scorer.ddg_score 정규화 기준. n=10, nstruct=5/run, σ=4.024 < 5.
    "SST14_SSTR2_ref_ddg_flexpep": {
        "ref_ddg_reu_mean": (
            553.857,
            "KAERI A-05 2026-05-19 feat/a05-sst14-reference-dg "
            "PyRosetta FlexPepDock SSTR2_7XNA n=10 nstruct=5/run cycles=5",
            "SST14 AGCKNFFWKTFTSC vs SSTR2_7XNA FlexPepDock ddG mean (REU). "
            "Fallback 모드 양수. candidate < 553.857 → SST14 대비 유리. "
            "data/somatostatin_receptor/SST14_SSTR2_reference_dG.json 참조.",
        ),
        "ref_ddg_reu_std": (
            4.024,
            "KAERI A-05 2026-05-19 feat/a05-sst14-reference-dg "
            "PyRosetta FlexPepDock SSTR2_7XNA n=10 nstruct=5/run cycles=5",
            "SST14 FlexPepDock ddG 표준편차 σ (REU). "
            "σ=4.024 < 5.0 → A-05 KPI 재현성 기준 충족. "
            "candidate < (553.857 - 4.024 = 549.833) → 통계적 유의미 우위.",
        ),
        "n": (
            10,
            "KAERI A-05 2026-05-19 feat/a05-sst14-reference-dg "
            "PyRosetta FlexPepDock SSTR2_7XNA n=10 nstruct=5/run cycles=5",
            "SST14 FlexPepDock 반복 도킹 횟수. A-05 KPI n ≥ 10 충족.",
        ),
    },
}


# ---------------------------------------------------------------------------
# 2. 생물학적 합리 범위 (GATE-C — PROMPT_TEMPLATE.md §3)
# ---------------------------------------------------------------------------

SCALE_RANGES: Dict[str, Tuple[float, float]] = {
    # name: (min, max)
    "kyte_doolittle_per_residue":     (-4.5, 4.5),
    "kyte_doolittle_mean":            (-2.0, 3.0),   # 펩타이드 평균 GRAVY
    "boman_index_kcal_per_mol":       (-5.0, 15.0),  # 이론 max ~14.92 (all-R), min ~-4.92 (all-I/L). 표시 단위 = mean RW_transfer (Boman convention).
    "instability_index":              (0.0, 100.0),
    "n_end_half_life_hours":          (0.0, 100.0),  # mammalian, in vivo
    "predicted_half_life_hours":      (0.0, 1e4),    # 합리적 상한 (현실적으로 1년 = 8760h)
    "isoelectric_point":              (0.0, 14.0),
    "molecular_weight_peptide_da":    (200.0, 10000.0),  # 1-100 residue peptide
    "rosetta_total_score":            (-1000.0, 500.0),  # 펩타이드-수용체 도킹
    "hydrophobic_moment":             (0.0, 2.0),
}


# ---------------------------------------------------------------------------
# 3. 부호 규약 (H-02 가드)
# ---------------------------------------------------------------------------

HEURISTIC_FUNCTION_DISCLAIMERS: Dict[str, Dict[str, str]] = {
    # H-06 가드 (VR-cycle-09 closure):
    # 휴리스틱 ranking score 함수들. 표면적 단위(hours, 등)는 임상 의미 아님.
    # 호출자는 reviewer-pharma.md §"휴리스틱 함수 해석 가이드" 의무 준수.
    "pipeline_local.steps.step08_stability.predict_half_life": {
        "surface_unit": "hours",
        "actual_meaning": "heuristic ranking score (NOT clinical half-life)",
        "limitations": (
            "in-vitro serum stability assay 미수행; 알부민 결합 affinity 측정 X; "
            "신장 청소율/Vd/F 모델 부재; modification 보너스 단순 가산; "
            "_PROTEASE_VULNERABILITY 점수 출처 부재 (VR-S5-01)"
        ),
        "valid_use": "후보 펩타이드 *상대 순위* 부여 (예: NSGA-II 입력)",
        "invalid_use": "임상 반감기 절대값 보고 / wet-lab 결과 대체",
        "confidence_grade": "HEURISTIC",  # HIGH/MED/LOW 와 별도 카테고리
        "fix_status": "VR-cycle-09 R1 closure 2026-05-11 — docstring 명세화",
    },
    "pipeline_local.steps.step08_stability.suggest_modifications": {
        "surface_unit": "list[ModificationSuggestion]",
        "actual_meaning": "heuristic priority list",
        "limitations": "합성 효율·임상 결과 보장 X; GLP-1 사례 기반 휴리스틱 가산",
        "valid_use": "modification 후보의 *우선순위* 부여",
        "invalid_use": "임상 modification 처방 결정",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-09 R1 closure 2026-05-11",
    },
    "pipeline_local.steps.step08_stability._compute_stability_score": {
        "surface_unit": "0-1 score",
        "actual_meaning": "sigmoid-normalized heuristic score",
        "limitations": "임상 관련성 미검증; midpoint=target_hl로 임의 calibration",
        "valid_use": "정렬·필터링 임계값",
        "invalid_use": "임상 안정성 확률로 해석",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-09 R1 closure 2026-05-11",
    },
    # VR-S5-01 closure: _PROTEASE_VULNERABILITY 점수 정량 출처 부재 명시 등록
    "pipeline_local.steps.step08_stability._PROTEASE_VULNERABILITY": {
        "surface_unit": "0-3 score per residue",
        "actual_meaning": "휴리스틱 protease cleavage preference proxy",
        "limitations": (
            "트립신/키모트립신/엘라스타제 정성적 선호도 기반 — 정량 문헌 출처 부재 "
            "(VR-S5-01). 실제 kcat/Km 값과 무관. 절대값 의미 X, 상대 순위만 유효."
        ),
        "valid_use": "잔기별 상대 vulnerability 순위 (predict_half_life 내부)",
        "invalid_use": "protease cleavage rate 추정; 절대값 임상 보고",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-S5-01 closure 2026-05-11 — 출처 부재 명시 등록 (full 출처 조사는 후속)",
    },
    # stability_predictor — U1 구현 (2026-05-12)
    "pipeline_local.scripts.stability_predictor.compute_stability": {
        "surface_unit": "StabilityResult (mw, gravy, instability_index, pi, boman, aliphatic_index, hl_score_heuristic)",
        "actual_meaning": "시퀀스 기반 physicochemical 속성 + heuristic HL ranking score",
        "limitations": (
            "hl_score_heuristic: step08_stability.predict_half_life 와 동일 한계 (in-vitro assay X, "
            "PK 모델 X). instability_index: Biopython Guruprasad 1990 — 일반 단백질 훈련, cyclic "
            "peptide 검증 부재. boman: peptides.py 설치 시만 산출 (없으면 fallback 경고). "
            "protease_cleavage_sites: 정성적 취약 부위 예측, kcat/Km 정량 아님."
        ),
        "valid_use": "후보 비교 ranking, modification 우선순위 결정",
        "invalid_use": "임상 반감기 절대값 보고, wet-lab 결과 대체",
        "confidence_grade": "HEURISTIC",
        "fix_status": "U1 신규 구현 2026-05-12",
    },
    "pipeline_local.scripts.stability_predictor.batch_evaluate": {
        "surface_unit": "List[StabilityResult]",
        "actual_meaning": "compute_stability 일괄 적용",
        "limitations": "compute_stability와 동일",
        "valid_use": "후보 배치 비교 ranking",
        "invalid_use": "임상 의사결정 근거",
        "confidence_grade": "HEURISTIC",
        "fix_status": "U1 신규 구현 2026-05-12",
    },
    # tier1-cluster-data 신규 구현 (2026-05-14) — BE candidate 6-field 머지 sprint
    "backend.pharmacophore.compute_fwkt_contact": {
        "surface_unit": "bool",
        "actual_meaning": "FWKT 모티프 sequence-only 존재 여부 (pharmacophore 접촉 proxy)",
        "limitations": (
            "Phase 1 구현: 'FWKT' substring 존재 여부만 판정. "
            "PDB 도킹 pose 기반 거리 계산 미수행 (< 5 Å, SSTR2 pocket residues Phe208/Tyr213 등). "
            "동일 motif라도 서열 context에 따라 결합 geometry 다를 수 있음. "
            "reviewer-pharma 응답 후 Phase 2에서 PDB 기반 계산으로 교체 예정."
        ),
        "valid_use": "1차 pharmacophore 보존 여부 필터 (후보 비교 ranking)",
        "invalid_use": "실제 SSTR2 접촉 확인, Ki 예측, 임상 결합 친화도 보고",
        "confidence_grade": "HEURISTIC",
        "fix_status": "tier1-cluster-data Phase 1 구현 2026-05-14 — reviewer-pharma 응답 대기",
    },
    "backend.pharmacophore.compute_chelator_site": {
        "surface_unit": "bool",
        "actual_meaning": "DOTA chelator 부착 가능 site 존재 여부 (sequence-only heuristic)",
        "limitations": (
            "Phase 1 구현: N-terminus(non-Pro) 또는 Lys ε-amine 존재 여부로 판정. "
            "실제 합성 yield/반응성 미측정. Pro N-terminus DOTA coupling 가능 여부 "
            "reviewer-pharma 확인 필요. Cys thiol 경쟁 chelation 시나리오 미평가. "
            "MALDI-TOF, HPLC, 방사화학 yield 측정으로 검증 필요."
        ),
        "valid_use": "1차 chelation site 존재 여부 필터",
        "invalid_use": "방사화학 yield 예측, 합성 성공 보장, 임상 방사성의약품 결정",
        "confidence_grade": "HEURISTIC",
        "fix_status": "tier1-cluster-data Phase 1 구현 2026-05-14 — reviewer-pharma 응답 대기",
    },
    # ─────────────────────────────────────────────────────────────────────
    # P1/P2 sprint 손실 복구 (2026-05-20 SOD) — 외부 도구 wrapper HEURISTIC 등록
    # 출처: _workspace/release/p1-action-items-execution-2026-05-19.md §2,
    #       _workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md §2
    # ─────────────────────────────────────────────────────────────────────
    "external_tool.halflife_pepmsnd": {
        "surface_unit": "binary label (stable / unstable)",
        "actual_meaning": "PepMSND 이진 분류 score (Wang 2025, DOI:10.1039/D5DD00118H)",
        "limitations": (
            "이진 분류기 — 연속 t½(시간) 출력 아님. D-AA 미지원 (학습셋 100% L-AA). "
            "PepMSND 학습셋 PEPlife 635개에 D-AA 116개(18.3%) 포함됨에도 모델 출력은 L-AA 한정. "
            "절대 임상 t½ 수치로 해석 금지 — 후보 *상대 순위* 부여만 유효 (NSGA-II 입력)."
        ),
        "valid_use": "후보 펩타이드 *상대* 안정성 ranking (binary 출력 기반)",
        "invalid_use": "임상 t½ 수치 보고; D-AA 펩타이드 직접 평가; wet-lab assay 대체",
        "confidence_grade": "HEURISTIC",
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD — 외부 도구 등록",
    },
    "external_tool.halflife_hlp": {
        "surface_unit": "time (intestinal/GI environment only)",
        "actual_meaning": "HLP (Sharma 2014) GI 환경 한정 안정성",
        "limitations": (
            "GI 전용 모델 — 혈청 적용 절대 금지. 1.6초 같은 비현실적 출력 traceback "
            "(reviewer-pharma A-02 §3.5). GI 효소 vs 혈청 단백분해효소 메커니즘 완전 분리. "
            "D-AA 미지원."
        ),
        "valid_use": "장내 안정성 추정만 (경구 투여 후보 GI 통과 평가)",
        "invalid_use": "혈청 t½ 추정 절대 금지; 정맥/근육 투여 약물 평가",
        "confidence_grade": "HEURISTIC",
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "external_tool.admet_pepadmet": {
        "surface_unit": "29 ADMET endpoints (R²=0.84-0.90 in original)",
        "actual_meaning": "pepADMET 펩타이드 ADMET 예측 (Wang 2026 JCIM)",
        "limitations": (
            "DOTA chelator OOD (학습셋 미포함). D-AA 미확인 — 학습셋 D-AA 비율 비공개. "
            "Web-only 접근 (HTTP 403 차단 가능, IP 의존). 환형 펩타이드 일부만 지원. "
            "원격 서비스 응답 변동 가능 (재현성 제약)."
        ),
        "valid_use": "표준 L-AA 선형 펩타이드 ADMET 1차 스크리닝 ranking",
        "invalid_use": "DOTA-conjugated 후보 평가; D-AA 직접 평가; 임상 ADMET 절대값 보고",
        "confidence_grade": "HEURISTIC",
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "external_tool.pepadmet": {
        "surface_unit": "toxicity prediction",
        "actual_meaning": "pepADMET toxicity 예측 (Tan et al. 2026 JCIM)",
        "limitations": (
            "pepADMET (Tan et al. 2026 JCIM)는 L-AA 펩타이드에 대해 P1 신뢰 (AUC=0.949). "
            "그러나 (1) D-아미노산 포함 펩타이드 예측은 환경 안정화 미완(2026-05-20 V-02/V-03 부분 성공), "
            "(2) DOTA 킬레이터 결합 펩타이드 처리 불가, (3) 웹 REST API 자동화 차단(HTTP 403)됨. "
            "본 가드는 위 한계를 자동 감지하여 결과 신뢰도를 LOW로 강제하거나 UNAVAILABLE 처리한다."
        ),
        "valid_use": "L-AA 펩타이드 toxicity 1차 스크리닝",
        "invalid_use": "D-AA 포함 펩타이드 예측; DOTA 킬레이터 결합 펩타이드 처리; 웹 REST API 자동화",
        "confidence_grade": "HEURISTIC",
        "fix_status": "A-03 pepADMET UNAVAILABLE/HEURISTIC 가드 등록 2026-05-20",
        "disclaimer": (
            "pepADMET (Tan et al. 2026 JCIM)는 L-AA 펩타이드에 대해 P1 신뢰 (AUC=0.949). "
            "그러나 (1) D-아미노산 포함 펩타이드 예측은 환경 안정화 미완(2026-05-20 V-02/V-03 부분 성공), "
            "(2) DOTA 킬레이터 결합 펩타이드 처리 불가, (3) 웹 REST API 자동화 차단(HTTP 403)됨. "
            "본 가드는 위 한계를 자동 감지하여 결과 신뢰도를 LOW로 강제하거나 UNAVAILABLE 처리한다."
        ),
    },
    "external_tool.admet_ai": {
        "surface_unit": "104 ADMET-AI small-molecule endpoints",
        "actual_meaning": "ADMET-AI learned model output for raw SMILES triage",
        "limitations": (
            "소분자 중심 Chemprop/ADMET-AI 모델 출력. PRST cyclic peptides, large peptides, "
            "DOTA/radiometal-chelator conjugates are OOD/extrapolative. 학습된 모델만 사용하며 "
            "로컬 재학습·보정 없음. endpoint 수치는 wet-lab ADMET 또는 임상 의사결정 대체 불가."
        ),
        "valid_use": "Layer 3 후보 triage에서 endpoint별 원시 출력 확인 및 OOD flag와 함께 보조 비교",
        "invalid_use": "DOTA 후보 최종 의사결정; 임상 ADMET 절대값 보고; wet-lab assay 대체",
        "confidence_grade": "HEURISTIC",
        "fix_status": "Layer 3 ADMET-AI wrapper 2026-05-20 — H-06 extrapolation guard",
    },
    "external_tool.halflife_plifepred2": {
        "surface_unit": "probability/ranking score (단위 미명시)",
        "actual_meaning": "PlifePred2 score — 출력 단위 문헌 미명시 (§V-infra-01)",
        "limitations": (
            "§V-infra-01 검증 결과 — 출력 'Halflife' label은 ranking score (시간 단위 NOT). "
            "SST14 score=3.38은 ranking 비교용 (시간 아님). 절대값 임상 t½ 추정 금지. "
            "D-AA 미지원."
        ),
        "valid_use": "동일 입력군 내 *상대* 순위 비교",
        "invalid_use": "절대 t½ 시간 수치 보고; D-AA 펩타이드 평가",
        "confidence_grade": "HEURISTIC",
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD — §V-infra-01 단위 미명시 반영",
    },
    "pipeline_local.scoring.layer1_ensemble.compute_layer1_halflife": {
        "surface_unit": "hours when explicit hour-valued wrappers are available",
        "actual_meaning": "Layer 1 weighted ensemble over L-AA serum-stability wrappers",
        "limitations": (
            "PlifePred2 ranking/probability scores are not converted to hours. "
            "HLE regression callable returns unavailable unless verified coefficients/model artifacts exist. "
            "pepADMET HBM is web-only and may be blocked by HTTP 403. "
            "D-AA, cyclic, and DOTA candidates must route to Layer 2/3 and are not recommended for Layer 1."
        ),
        "valid_use": "L-AA linear peptide first-pass serum stability ranking when explicit wrapper outputs exist",
        "invalid_use": "wet-lab serum stability replacement; clinical t½ reporting; D-AA/cyclic/DOTA evaluation",
        "confidence_grade": "HEURISTIC",
        "fix_status": "Layer 1 ensemble H-06 guard registered 2026-05-20",
    },
    # VR-cycle-08 closure: PDB 좌표 부재 시 PyRosetta sequence-only pose의 한계
    "pyrosetta.pose_from_sequence_ideal_coord": {
        "surface_unit": "ref2015 score (energy unit)",
        "actual_meaning": "sequence-only ideal coord pose의 ref2015 score",
        "limitations": (
            "실 NMR/X-ray PDB 좌표 부재. ideal backbone + ideal side chain rotamer로 "
            "시작 — 실제 conformation과 다름. minimize/relax 후에도 native energy "
            "minimum 도달 보장 X. ref2015는 큰 단백질용 calibrated, 작은 cyclic "
            "peptide에 부적합 가능 (VR-cycle-08)."
        ),
        "valid_use": "modification 적용 전후 *상대* score 변화 비교",
        "invalid_use": "절대 binding energy 추정; 실 wet-lab dock energy 대체",
        "confidence_grade": "HEURISTIC",
        "fix_status": (
            "VR-cycle-08 partial closure 2026-05-11 — 한계 명시. full closure는 "
            "실 PDB 좌표 인프라 도입 후 (NMR/X-ray 또는 NMR predictor)."
        ),
    },
}


def is_heuristic_function(qualname: str) -> bool:
    """주어진 함수가 HEURISTIC_FUNCTION_DISCLAIMERS에 등록된 휴리스틱인지 확인.

    Args:
        qualname: 함수의 full qualified name (예: "pipeline_local.steps.step08_stability.predict_half_life")

    Returns:
        등록된 휴리스틱이면 True (호출자는 HEURISTIC 신뢰 등급 의무).
    """
    return qualname in HEURISTIC_FUNCTION_DISCLAIMERS


_STANDARD_AA_1LETTER = set("ACDEFGHIKLMNPQRSTVWY")
_STANDARD_AA_3LETTER = {
    "ala", "arg", "asn", "asp", "cys", "gln", "glu", "gly", "his", "ile",
    "leu", "lys", "met", "phe", "pro", "ser", "thr", "trp", "tyr", "val",
}


def check_pepadmet_applicability(
    sequence: str,
    has_dota: bool = False,
    smiles: Optional[str] = None,
) -> dict:
    """pepADMET 적용 가능성을 보수적으로 판정한다.

    A-03 / V-02/V-03 (2026-05-20): D-AA 구조 인식은 확인됐으나 toxicity
    예측 출력이 실패했으므로 D-AA 또는 비표준 아미노산 입력은 권장하지 않는다.

    2026-05-21 SS-bond OOD 가드 추가 (reviewer-pharma §7-C):
    SMILES 내 'SS' 서브구조(이황화결합)가 감지되면 OOD 판정.
    근거: pepADMET binary_toxicity 학습 도메인에서 14aa SS-bond 펩타이드 0건
    (_workspace/55_reviewer-pharma_prst-admet-ood-analysis.md §2.2).
    Octreotide (FDA-승인) 동일 OOD 패턴으로 입증 (§3.1).

    Args:
        sequence: 펩타이드 서열 (1-letter 또는 3-letter 표기 혼용 허용)
        has_dota: DOTA 킬레이터 결합 여부
        smiles:   SMILES 문자열 (옵션). 제공 시 'SS' 서브구조로 이황화결합 감지.

    Returns:
        dict:
            recommended (bool): True = pepADMET 적용 권장, False = OOD 우려
            reason (str): 비권장 사유 또는 적용 가능 메시지
            d_amino_acid_present (bool): D-AA 감지 여부
            dota_chelator_present (bool): DOTA 킬레이터 감지 여부
            cyclic_ss_bond_present (bool): SMILES 기반 이황화결합 감지 여부
            absolute_confidence (str): 항상 "LOW" — pepADMET cyclic SS-bond OOD 위험
    """
    normalized = sequence.strip()
    lowered = normalized.lower()
    d_amino_acid_present = any(
        marker in lowered
        for marker in (
            "d-ala", "d-arg", "d-asn", "d-asp", "d-cys", "d-gln", "d-glu",
            "d-gly", "d-his", "d-ile", "d-leu", "d-lys", "d-met", "d-phe",
            "d-pro", "d-ser", "d-thr", "d-trp", "d-tyr", "d-val",
        )
    )

    if not d_amino_acid_present:
        if normalized.isalpha():
            d_amino_acid_present = any(aa not in _STANDARD_AA_1LETTER for aa in normalized.upper())
        else:
            tokens = [tok for tok in lowered.replace("-", " ").replace("_", " ").split() if tok]
            d_amino_acid_present = any(
                tok not in _STANDARD_AA_3LETTER and tok.upper() not in _STANDARD_AA_1LETTER
                for tok in tokens
            )

    dota_chelator_present = bool(has_dota)

    # SS-bond OOD 가드 (2026-05-21 — reviewer-pharma §7-C)
    # SMILES의 'SS' 서브구조 = 이황화결합 (예: Cys3-Cys14: ...CSSC...)
    # 감지 조건: smiles 인자 제공 AND 'SS' 포함
    # 주의: 대소문자 구분 서브스트링 검색 (SMARTS 아님). RDKit 표준 SMILES 전제.
    # - trisulfide(CSSSCC) → true (보수적 false positive, 안전 방향)
    # - 하전 표기 [S+][S-] → false negative (표준 SMILES에서 극히 드묾)
    # - Met (CSCC...), 단량체 Cys (N[C@@H](CS)...) → false (S 단독, SS 없음)
    cyclic_ss_bond_present = bool(smiles and "SS" in smiles)

    reasons: List[str] = []
    if d_amino_acid_present:
        reasons.append("D-AA 표기 또는 비표준 아미노산 포함: V-02/V-03 부분 성공으로 예측 출력 재검증 필요")
    if dota_chelator_present:
        reasons.append("DOTA 킬레이터 결합 펩타이드 처리 불가")
    if cyclic_ss_bond_present:
        reasons.append(
            "cyclic SS-bond peptide OOD: pepADMET binary_toxicity 학습 도메인 미포함 "
            "(14aa SS-bond binary label 0건 — reviewer-pharma 2026-05-20 §2.2; "
            "Octreotide binary_toxicity=1.0 교차검증 실패 §3.1)"
        )

    return {
        "recommended": not reasons,
        "reason": "; ".join(reasons) if reasons else "L-AA 입력: pepADMET 적용 가능하나 absolute_confidence는 LOW 유지",
        "d_amino_acid_present": d_amino_acid_present,
        "dota_chelator_present": dota_chelator_present,
        "cyclic_ss_bond_present": cyclic_ss_bond_present,
        "absolute_confidence": "LOW",
    }


def check_pepmsnd_local_applicability(
    sequence: str,
    *,
    has_dota: bool = False,
) -> Dict[str, Any]:
    """Layer 2 로컬 모델(`_workspace/pepmsnd_local`) 혈중 t½ 회귀 호출 전 적용성.

    학습 데이터는 PEPlife2 REST 병합본 중 **표준 20aa 대문자 서열 → RDKit SMILES** 만 포함.
    공식 PepMSND(paper)와 달리 본 빌드는 GAT+log1p(t½) 간소화 회귀(격리 env, PyG)이다.

    Returns:
        recommended: bool — SMILES 생성·체크포인트 존재 시 True 가능
        d_amino_acid_support: D-AA 서열은 학습 분포 밖 + RDKit 단순 시퀀스 변환 한계
        cyclic_support: Cys–Cys 이황화 등은 `pyrosetta_flow.smiles_converter` 경로로 시도 가능(레포 내)
    """
    seq = (sequence or "").strip()
    ok_chars = set("ACDEFGHIKLMNPQRSTVWY")
    standard_upper = bool(seq) and all(c in ok_chars for c in seq.upper())
    cyclic_hint = seq.upper().count("C") >= 2
    return {
        "recommended": bool(standard_upper and not has_dota),
        "d_amino_acid_support": False,
        "cyclic_support": cyclic_hint,
        "dota_chelator": bool(has_dota),
        "notes": (
            "로컬 학습 체크포인트는 L-AA 위주; D-AA·Thr(ol) 등 비표준 SMILES 실패 시 None 반환. "
            "DOTA는 본 endpoint OOD — Layer 3 라우팅."
        ),
    }


SIGN_CONVENTIONS: Dict[str, str] = {
    "kyte_doolittle":    "POSITIVE = hydrophobic, NEGATIVE = hydrophilic (Kyte & Doolittle 1982 Table I)",
    "boman_index":       "POSITIVE = hydrophilic / high protein-binding potential, NEGATIVE = hydrophobic (Boman 2003 §3; opposite sign from raw Radzicka-Wolfenden transfer free energy)",
    "instability_index": "POSITIVE only — higher means LESS stable. II < 40 = stable, II >= 40 = unstable (Guruprasad 1990)",
    "wimley_white":      "POSITIVE = unfavourable transfer (stays in water), NEGATIVE = favourable transfer to membrane interface (Wimley & White 1996)",
    "eisenberg":         "POSITIVE = hydrophobic (consensus scale, Eisenberg 1982)",
    "n_end_half_life":   "POSITIVE hours only; smaller = less stable. Mammalian reticulocyte (Varshavsky 1996)",
    "rosetta_total_score": "NEGATIVE = favorable binding, POSITIVE = unfavorable / clashes (ref2015, Alford 2017)",
}


# ---------------------------------------------------------------------------
# 4. 가드 함수 (Public API)
# ---------------------------------------------------------------------------


@dataclass
class GuardViolation:
    """가드 위반 사례."""
    table_name: str
    key: str
    actual_value: Any
    expected_value: Any
    source: str
    message: str


def assert_literature_value(
    table: Mapping[str, Any],
    table_name: str,
    key: str,
    tolerance: float = 1e-6,
) -> None:
    """단일 lookup 값이 문헌 정답과 일치하는지 검증.

    Raises:
        AssertionError: 정답과 다를 때 (어디서 가져온 정답인지 출처와 함께)
        KeyError:       LITERATURE_VALUES에 등록되지 않은 table_name 또는 key
    """
    if table_name not in LITERATURE_VALUES:
        raise KeyError(f"Unknown literature table: {table_name!r}. Available: {sorted(LITERATURE_VALUES)}")
    truth = LITERATURE_VALUES[table_name]
    if key not in truth:
        raise KeyError(f"Key {key!r} not registered in literature for {table_name!r}")
    expected, source, comment = truth[key]
    actual = table.get(key)
    if actual is None:
        raise AssertionError(
            f"[{table_name}] missing key {key!r} (expected {expected} per {source}; {comment})"
        )
    # 수치 비교
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if abs(actual - expected) > tolerance:
            raise AssertionError(
                f"[{table_name}][{key!r}] = {actual} but literature says {expected} "
                f"(tolerance {tolerance}; source: {source}; note: {comment})"
            )
    # 튜플 비교 (e.g. NEND_HALFLIFE: (hours, category))
    elif isinstance(expected, tuple) and isinstance(actual, tuple):
        if actual[0] != expected:
            raise AssertionError(
                f"[{table_name}][{key!r}] = {actual} but literature says {expected} "
                f"(source: {source}; note: {comment})"
            )


def audit_table(
    table: Mapping[str, Any],
    table_name: str,
    tolerance: float = 1e-6,
) -> List[GuardViolation]:
    """LITERATURE_VALUES에 등록된 모든 key를 일괄 검증.

    Returns:
        위반 사례 목록. 비어 있으면 모두 통과.
    """
    if table_name not in LITERATURE_VALUES:
        return [GuardViolation(
            table_name=table_name, key="*", actual_value=None, expected_value=None,
            source="-", message=f"Unknown literature table: {table_name!r}",
        )]
    violations: List[GuardViolation] = []
    truth = LITERATURE_VALUES[table_name]
    for key, (expected, source, comment) in truth.items():
        actual = table.get(key)
        if actual is None:
            violations.append(GuardViolation(
                table_name=table_name, key=key, actual_value=None,
                expected_value=expected, source=source,
                message=f"missing key (note: {comment})",
            ))
            continue
        # NEND_HALFLIFE처럼 (hours, category) 튜플 처리
        actual_value = actual[0] if isinstance(actual, tuple) and not isinstance(expected, tuple) else actual
        try:
            if isinstance(expected, (int, float)) and abs(actual_value - expected) > tolerance:
                violations.append(GuardViolation(
                    table_name=table_name, key=key, actual_value=actual_value,
                    expected_value=expected, source=source,
                    message=f"value mismatch (note: {comment})",
                ))
        except TypeError:
            violations.append(GuardViolation(
                table_name=table_name, key=key, actual_value=actual,
                expected_value=expected, source=source,
                message=f"type mismatch (note: {comment})",
            ))
    return violations


def assert_in_range(
    value: float,
    scale_name: str,
    context: str = "",
) -> None:
    """GATE-C 범위 검사. 도메인 합리 범위를 벗어나면 AssertionError.

    Args:
        value:      검증할 수치
        scale_name: SCALE_RANGES의 키 (예: "boman_index_kcal_per_mol")
        context:    오류 메시지에 포함할 추가 컨텍스트 (서열, 후보ID 등)
    """
    if scale_name not in SCALE_RANGES:
        raise KeyError(f"Unknown scale: {scale_name!r}. Available: {sorted(SCALE_RANGES)}")
    lo, hi = SCALE_RANGES[scale_name]
    if not (lo <= value <= hi):
        ctx = f" ({context})" if context else ""
        raise AssertionError(
            f"RANGE-CHECK FAIL: [{scale_name}] = {value}{ctx} outside biological/physical range [{lo}, {hi}]"
        )


def check_sign_convention(
    scale_name: str,
    aa_high: str,
    aa_low: str,
    table: Mapping[str, float],
) -> None:
    """부호 규약 invariant 검증.

    Args:
        scale_name: SIGN_CONVENTIONS의 키
        aa_high:    이 척도에서 양수(또는 큰 값)이어야 하는 representative AA
        aa_low:     이 척도에서 음수(또는 작은 값)이어야 하는 representative AA
        table:      검증할 lookup table

    예: Kyte-Doolittle에서 I(소수성, +) > R(친수성, -)이어야 함.
        호출: check_sign_convention("kyte_doolittle", "I", "R", KD_HYDROPATHY)
    """
    if scale_name not in SIGN_CONVENTIONS:
        raise KeyError(f"Unknown scale: {scale_name!r}")
    v_high = table.get(aa_high)
    v_low = table.get(aa_low)
    if v_high is None or v_low is None:
        raise KeyError(f"[{scale_name}] missing key {aa_high!r} or {aa_low!r}")
    if not (v_high > v_low):
        raise AssertionError(
            f"SIGN-CONVENTION VIOLATION: [{scale_name}] {aa_high}={v_high} should be > {aa_low}={v_low}. "
            f"Convention: {SIGN_CONVENTIONS[scale_name]}"
        )


# ---------------------------------------------------------------------------
# 5. API 신뢰도 메타데이터 (P1-4 — HEURISTIC API 자동 주입, 2026-05-13)
# ---------------------------------------------------------------------------
#
# M5 신뢰도 매트릭스 (_workspace/M5_reviewer-pharma_module-spec-2026-05-13.md §1) 기반.
# 각 API 엔드포인트가 반환하는 주요 값의 신뢰 등급을 정의한다.
#
# 등급 정의:
#   "A"         : 실측 기반 또는 물리 법칙 기반 계산 — 절대값 인용 가능
#   "B"         : in-silico 추정 — 순위/비교에 유효, ⚠️ 표기 권장
#   "C"         : 검증 부족 — 절대값 해석 주의, ⚠️⚠️ 표기 강제
#   "HEURISTIC" : HEURISTIC_FUNCTION_DISCLAIMERS 등록 함수 출력 — ranking 전용
#
# attach_confidence() helper가 이 테이블을 참조하여 API 응답에 자동 주입한다.

ENDPOINT_CONFIDENCE: Dict[str, Dict[str, Any]] = {
    # ── /admet — ADMET + 신독성 (C등급: DLscore 포화 문제) ─────────────────
    "/admet/{sequence}": {
        "grade": "C",
        "metrics": ["dlscore", "nephrotox_risk", "bbb_risk", "herg_risk", "cyp450"],
        "warnings": [
            "⚠️⚠️ compute_admet DLscore 100/100 포화 — 변별력 부족 (§검증 필요 G-05/M5-P3)",
            "⚠️ 소분자 기반 ADMET 모델 — 펩타이드 적합성 미검증",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.11",
    },
    "/admet/batch": {
        "grade": "C",
        "metrics": ["dlscore", "nephrotox_risk", "bbb_risk", "herg_risk", "cyp450"],
        "warnings": [
            "⚠️⚠️ compute_admet DLscore 100/100 포화 — 변별력 부족 (§검증 필요 G-05/M5-P3)",
            "⚠️ 소분자 기반 ADMET 모델 — 펩타이드 적합성 미검증",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.11",
    },
    # ── /pharmacology — 물리화학적 특성 (B등급: Biopython ProtParam) ────────
    "/pharmacology/batch": {
        "grade": "B",
        "metrics": [
            "gravy", "instability_index", "boman_index",
            "molecular_weight", "pi", "aliphatic_index",
        ],
        "warnings": [
            "⚠️ in-silico 추정값 (Biopython ProtParam). 임상 결과 대체 불가.",
            "⚠️ D-아미노산 도입 후보는 Instability Index가 L-AA 기준으로 계산됨 — pepADMET 사용 권장 (M5-P1)",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.11",
    },
    # ── /selectivity — 선택성 스크리닝 (C등급: Ki 상관 미검증) ───────────────
    "/selectivity/results/{job_id}": {
        "grade": "C",
        "metrics": [
            "selectivity_margin", "wsm", "msm", "tier",
            "passed", "sstr2_ddg", "delta_ddg",
        ],
        "warnings": [
            "⚠️⚠️ selectivity_margin은 dock_score 차이 기반 — 실측 Ki selectivity 상관 미검증 (M5-P4)",
            "⚠️⚠️ Boltz iPTM ≠ Ki proxy (Spearman ρ≈-0.3, 순위 일치 0/5 실증) — 정량 선택성은 FEP/Ki assay 필요",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.7, §3.3; step05c.py docstring",
    },
    "/selectivity/status/{job_id}": {
        "grade": "C",
        "metrics": ["selectivity_margin", "tier"],
        "warnings": [
            "⚠️⚠️ selectivity_margin은 dock_score 차이 기반 — 실측 Ki selectivity 상관 미검증 (M5-P4)",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.7",
    },
    # ── /validation — PyRosetta 결과 검증 (B등급: ideal coord 한계) ─────────
    "/validate/selected": {
        "grade": "B",
        "metrics": ["ddG", "clashScore", "totalScore"],
        "warnings": [
            "⚠️ ddG: PyRosetta ref2015 (ideal coord 출발점) — 상대 비교만 유효 (VR-cycle-08)",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.8",
    },
    "/validation/run": {
        "grade": "B",
        "metrics": ["ddG", "statistical_scores"],
        "warnings": [
            "⚠️ in-silico 추정값. 임상 결과 대체 불가.",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.8",
    },
    "/validate/unified": {
        "grade": "B",
        "metrics": ["ddG", "gravy", "instability_index", "boman_index"],
        "warnings": [
            "⚠️ in-silico 추정값 (복합 검증). 임상 결과 대체 불가.",
        ],
        "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.8, §1.11",
    },
    # ──────────────────────────────────────────────────────────────────────
    # P1/P2 sprint 손실 복구 (2026-05-20 SOD) — 외부 도구 신뢰 등급 11개
    # 출처: _workspace/release/p1-action-items-execution-2026-05-19.md §2,
    #       _workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md §1.1, §1.2
    # 등급은 논문 R²/AUC 기준 — 인프라 접근성과 분리 (예: pepADMET P1 ↔ HTTP 403 인프라 문제)
    # ──────────────────────────────────────────────────────────────────────
    # 혈청 반감기 도구 7개
    "halflife_pepmsnd": {
        "grade": "P3",
        "tool": "PepMSND",
        "source_doi": "10.1039/D5DD00118H",
        "d_amino_acid_support": False,
        "url": "http://model.highslab.com/static/service",
        "metrics": ["halflife_binary_label"],
        "warnings": [
            "⚠️ P1→P3 강등: 이진 분류, 연속 t½(시간) 출력 아님",
            "⚠️ D-아미노산 직접 미지원 (학습셋 100% L-AA)",
            "⚠️ HEURISTIC — external_tool.halflife_pepmsnd 참조",
        ],
        "dataset_note": (
            "PEPlife 학습셋 635개 entries (T1/2 hour 연속값 225 unique). "
            "D-AA 포함 entries 116개(18.3%). 로컬 학습 시 D-AA 분류기 재현 가능 (V-05)."
        ),
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    # ── Layer 2 로컬 PEPlife2 → GAT 회귀 (2026-05-20 실측, 품질 낮음 → P4) ──
    "pepmsnd_local_halflife_hours": {
        "grade": "P4",
        "tool": "local_PEPlife2_GAT_regression",
        "source": "_workspace/pepmsnd_local/training_2026-05-20.md",
        "d_amino_acid_support": False,
        "cyclic_support": True,
        "dota_support": False,
        "metrics": ["half_life_hours", "pred_log1p"],
        "benchmark_test_r2_hours_2026_05_20": -0.028,
        "benchmark_test_spearman_2026_05_20": -0.119,
        "warnings": [
            "⚠️ 공식 PepMSND fusion(SE3+PDB)·이진분류 아님 — PyG GAT+log1p(시간) 간소화 재학습",
            "⚠️ 실측 test R²≈-0.03 / Spearman ρ≈-0.12 (2026-05-20) — 순위·절대값 신뢰 불가",
            "⚠️ 전처리: 표준 20aa 대문자만; PEPlife2 merged unique id=4500 (researcher 4412와 소차이)",
            "⚠️ PyBioMed 2133d 미사용(DGL import 실패·시간); pepmsnd_local 환경에 패키지 없음",
            "⚠️ HEURISTIC — check_pepmsnd_local_applicability() 선행 권장",
        ],
        "fix_status": "Layer2 dogfood 2026-05-20 — 정직한 저성능 보고",
    },
    "halflife_plifepred": {
        "grade": "P2",
        "tool": "PlifePred",
        "source_doi": "Mathur 2018 PLOS ONE",
        "d_amino_acid_support": False,
        "metrics": ["halflife_hours"],
        "warnings": [
            "⚠️ R²≈0.552 (Mathur 2018), 혈중 t½ 직접 예측",
            "⚠️ HEURISTIC ranking 권장 — 절대값 보고는 §V-infra 검증 후",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "halflife_plifepred2": {
        "grade": "P4",
        "tool": "PlifePred2",
        "d_amino_acid_support": False,
        "metrics": ["halflife_score"],
        "warnings": [
            "⚠️ §V-infra-01: 출력 단위 미명시 — ranking score (시간 아님)",
            "⚠️ 절대값 사용 금지 (예: SST14=3.38은 ranking 비교용)",
            "⚠️ HEURISTIC — external_tool.halflife_plifepred2 참조",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD — §V-infra-01 반영",
    },
    "layer1_halflife_ensemble": {
        "grade": "P2",
        "tool": "Layer 1 Ensemble (PlifePred/HLE regression/pepADMET HBM)",
        "d_amino_acid_support": False,
        "cyclic_support": False,
        "dota_support": False,
        "recommended": True,
        "metrics": ["ensemble_halflife_hours", "individual_predictions", "tools_unavailable"],
        "warnings": [
            "⚠️ Uses only explicit hour-valued wrapper outputs; PlifePred2 ranking scores are excluded from hour averaging",
            "⚠️ D-AA/cyclic/DOTA candidates set recommended=False and require Layer 2/3 routing",
            "⚠️ pepADMET HBM web access may be unavailable via HTTP 403",
            "⚠️ HEURISTIC — pipeline_local.scoring.layer1_ensemble.compute_layer1_halflife 참조",
        ],
        "fix_status": "3-Layer Ensemble Layer 1 등록 2026-05-20",
    },
    "halflife_webmetabase_indirect": {
        "tool": "WebMetabase",
        "url": "https://mass-analytica.com/protease-specific-cleavage-sites/",
        "grade": "P3",
        "d_amino_acid_support": True,
        "local_executable": False,
        "output_type": "cleavage_site_probability",
        "half_life_direct": False,
        "benchmark_r2": None,
        "assay_context": "protease_cleavage_prediction_indirect",
        "disclaimer": (
            "WebMetabase는 프로테아제 절단 사이트를 D-AA 포함 비표준 AA에 대해 예측. "
            "혈청 반감기를 직접 출력하지 않으며 간접 stability 지표로만 활용 가능. "
            "D-AA 치환 효과 분석(어떤 사이트가 차단되는지)에 유효. "
            "(H-06: 절단 사이트 예측 결과를 혈청 t½ 수치로 해석하지 말 것)"
        ),
        "source": "Radchenko MV et al. 2019 PLOS ONE DOI:10.1371/journal.pone.0215484",
    },
    "halflife_hle_regression_albumin": {
        "tool": "HLE Regression (Glassman 2024) — albumin-binding subset",
        "url": "DOI:10.1016/j.ijpharm.2024.124382",
        "grade": "P3",
        "d_amino_acid_support": False,
        "local_executable": True,
        "callable": "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife_hle_regression",
        "output_type": "t_half_fold_change",
        "half_life_direct": True,
        "benchmark_r2_albumin_binding": 0.879,
        "n_training": 26,
        "assay_context": "albumin_binding_half_life_extension",
        "disclaimer": (
            "HLE Regression은 분자량 변화 기반 단순 선형 모델. "
            "albumin-binding HLE 전략에서 R²=0.879이지만 학습셋 n=26으로 작음. "
            "C18 지방산 acylation SST-14 유사체의 t½ rough estimate에만 활용. "
            "현재 repo에는 회귀 계수/모델 artifact가 없어 callable은 unavailable을 반환. "
            "(H-06: 이 공식을 임상 t½ 예측값으로 오용 금지)"
        ),
        "source": "Glassman PM. 2024 Int J Pharm 660:124382 DOI:10.1016/j.ijpharm.2024.124382",
    },
    "halflife_ml_peptide": {
        "grade": "P3",
        "tool": "ML_Peptide",
        "d_amino_acid_support": False,
        "metrics": ["halflife_hours"],
        "warnings": [
            "⚠️ peer-review 미확보 — 검증 제한",
            "⚠️ HEURISTIC ranking 권장",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "halflife_protparam": {
        "grade": "P4",
        "tool": "ProtParam",
        "source_doi": "Varshavsky 1996 (N-end rule)",
        "d_amino_acid_support": False,
        "metrics": ["instability_index", "halflife_n_end_rule"],
        "warning": (  # 단수 키 — attach_confidence warning 패치 검증용
            "⚠️ P3→P4 강등: N-end rule = 세포내 메커니즘 — 혈청 t½ 완전 불일치"
        ),
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "halflife_hlp": {
        "grade": "P4",
        "tool": "HLP",
        "source_doi": "Sharma 2014",
        "d_amino_acid_support": False,
        "metrics": ["halflife_gi"],
        "warnings": [
            "⚠️ GI 전용 (장내 환경 한정) — 혈청 적용 절대 금지",
            "⚠️ 1.6초 비현실적 출력 traceback (reviewer-pharma A-02 §3.5)",
            "⚠️ HEURISTIC — external_tool.halflife_hlp 참조",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "halflife_peptiderranker": {
        "grade": "P4",
        "tool": "PeptideRanker",
        "d_amino_acid_support": False,
        "metrics": ["bioactivity_ranking_score"],
        "warning": (  # 단수 키 — 단수키 호환 검증
            "⚠️ 생물활성 ranking 전용 — t½ 예측 아님 (혼동 금지)"
        ),
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    # ADMET 도구 4개
    "admet_pepadmet": {
        "grade": "P1",
        "tool": "pepADMET",
        "source_doi": "Wang 2026 JCIM",
        "d_amino_acid_support": False,
        "url": "https://pepadmet.ddai.tech/calcpep/half-life/",
        "metrics": ["29_admet_endpoints"],
        "warnings": [
            "⚠️ R²=0.84-0.90 (원 논문 기준) — 등급은 정확도 기준, 인프라(HTTP 403)와 분리",
            "⚠️ DOTA chelator OOD (학습셋 미포함)",
            "⚠️ D-AA 미확인 (학습셋 D-AA 비율 비공개)",
            "⚠️ Web-only 접근 — 재현성 제약",
            "⚠️ HEURISTIC — external_tool.admet_pepadmet 참조",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD — grade P2→P1 정정",
    },
    "pepadmet_toxicity": {
        "grade": "P1",
        "tool": "pepADMET",
        "source_doi": "Wang/Tan 2026 JCIM AUC=0.949",
        "d_amino_acid_support": "partial",
        "local_install_status": "partial",
        "api_status": "blocked",
        "reference": "github.com/ifyoungnet/pepADMET",
        "metrics": ["toxicity"],
        "warnings": [
            "⚠️ L-AA 입력 시만 신뢰. D-AA는 환경 안정화 (V-02b) 후 재검증 필요. 환형 펩타이드 7,765개 학습 데이터 포함.",
            "⚠️ local_install_status=partial — clone OK, calculate_descriptors.py 실패",
            "⚠️ api_status=blocked — HTTP 403, 2026-05-19 확인",
            "⚠️ HEURISTIC — external_tool.pepadmet 참조",
        ],
        "notes": (
            "L-AA 입력 시만 신뢰. D-AA는 환경 안정화 (V-02b) 후 재검증 필요. "
            "환형 펩타이드 7,765개 학습 데이터 포함."
        ),
        "fix_status": "A-03 pepADMET UNAVAILABLE/HEURISTIC 가드 등록 2026-05-20",
    },
    "admet_modlamp": {
        "grade": "P3",
        "tool": "modlamp",
        "d_amino_acid_support": False,
        "metrics": ["physicochemical_descriptors"],
        "warning": (  # 단수 키 — 단수키 호환 검증
            "⚠️ 물리화학 디스크립터만 — ADMET 예측 아님 (variable이지만 ADMET surrogate 아님)"
        ),
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "admet_ai": {
        "grade": "P2",
        "tool": "ADMET-AI",
        "d_amino_acid_support": False,
        "metrics": ["admet_endpoints"],
        "warnings": [
            "⚠️ 소분자 중심 학습 — 펩타이드는 OOD 감점",
            "⚠️ 펩타이드 ADMET 예측 정확도 미보장",
        ],
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD",
    },
    "admet_ai_extrapolation": {
        "grade": "P4",
        "tool": "ADMET-AI",
        "source": "https://github.com/swansonk14/admet_ai; _workspace/admet_ai_local/",
        "d_amino_acid_support": False,
        "dota_support": False,
        "cyclic_peptide_support": "extrapolation_only",
        "metrics": ["104_admet_ai_endpoints"],
        "recommended_for_decision": False,
        "warnings": [
            "⚠️ H-06: ADMET-AI 출력은 PRST cyclic peptide/DOTA 후보에 대한 외삽 결과",
            "⚠️ 학습된 ADMET-AI 모델만 사용; 로컬 재학습·보정 없음",
            "⚠️ DOTA/radiometal-chelator conjugate는 OOD — decision용 사용 금지",
            "⚠️ HEURISTIC — external_tool.admet_ai 참조",
        ],
        "fix_status": "Layer 3 ADMET-AI wrapper 2026-05-20 — recommended_for_decision=False",
    },
    "admet_fab": {
        "grade": "UNKNOWN",
        "tool": "Fab-ADMET",
        "url": None,  # 원출처 미식별
        "d_amino_acid_support": None,
        "metrics": [],
        "warning": (  # 단수 키 — 단수키 호환 검증
            "⚠️ 원출처 미식별 — 5월 회의 'Fab-ADMET = pepADMET' 정정 가능성 (researcher §검증)"
        ),
        "fix_status": "P1/P2 sprint 손실 복구 2026-05-20 SOD — 원출처 조사 미완",
    },
    # ──────────────────────────────────────────────────────────────────────
    # A-02 D-AA 도구 확장 탐색 신규 2개 (2026-05-20)
    # 출처: _workspace/release/sod-2026-05-20-A02-daa-tools-extended.md §4.3
    # researcher-daa 보고서 권고 → engineer-backend 적용
    # ──────────────────────────────────────────────────────────────────────
    "halflife_webmetabase_indirect": {
        "tool": "WebMetabase",
        "url": "https://mass-analytica.com/protease-specific-cleavage-sites/",
        "grade": "P3",   # indirect — 절단 사이트 예측으로 안정성 간접 추론
        "d_amino_acid_support": True,   # 명시적 지원 (Radchenko 2019 논문)
        "local_executable": False,  # 학술 협력 필요
        "output_type": "cleavage_site_probability",  # NOT t½
        "half_life_direct": False,
        "benchmark_r2": None,
        "assay_context": "protease_cleavage_prediction_indirect",
        "disclaimer": (
            "WebMetabase는 프로테아제 절단 사이트를 D-AA 포함 비표준 AA에 대해 예측. "
            "혈청 반감기를 직접 출력하지 않으며 간접 stability 지표로만 활용 가능. "
            "D-AA 치환 효과 분석(어떤 사이트가 차단되는지)에 유효. "
            "(H-06: 절단 사이트 예측 결과를 혈청 t½ 수치로 해석하지 말 것)"
        ),
        "source": "Radchenko MV et al. 2019 PLOS ONE DOI:10.1371/journal.pone.0215484",
    },
    "halflife_hle_regression_albumin": {
        "tool": "HLE Regression (Glassman 2024) — albumin-binding subset",
        "url": "DOI:10.1016/j.ijpharm.2024.124382",
        "grade": "P3",   # rough estimate only — R²=0.879 but MWT-based, not AA-level
        "d_amino_acid_support": False,  # wrapper policy: D-AA input rejected
        "local_executable": True,  # 수식 직접 구현 가능
        "callable": "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife_hle_regression",
        "output_type": "t_half_fold_change",
        "half_life_direct": True,  # fold-change 기반 indirect prediction
        "benchmark_r2_albumin_binding": 0.879,
        "n_training": 26,  # albumin-binding HLE subset only
        "assay_context": "albumin_binding_half_life_extension",
        "disclaimer": (
            "HLE Regression은 분자량 변화 기반 단순 선형 모델. "
            "albumin-binding HLE 전략에서 R²=0.879이지만 학습셋 n=26으로 작음. "
            "C18 지방산 acylation SST-14 유사체의 t½ rough estimate에만 활용. "
            "현재 repo에는 회귀 계수/모델 artifact가 없어 callable은 unavailable을 반환. "
            "(H-06: 이 공식을 임상 t½ 예측값으로 오용 금지)"
        ),
        "source": "Glassman PM. 2024 Int J Pharm 660:124382 DOI:10.1016/j.ijpharm.2024.124382",
    },
}

# 기본 신뢰도 (매핑 없는 엔드포인트에 적용)
_DEFAULT_CONFIDENCE: Dict[str, Any] = {
    "grade": "B",
    "metrics": [],
    "warnings": ["⚠️ in-silico 추정값. 임상 결과 대체 불가."],
    "source": "pharmacology_guards.py (default)",
}


def attach_confidence(
    response: Dict[str, Any],
    endpoint_path: str,
    *,
    heuristic_functions_used: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """API 응답 dict에 confidence_grade와 confidence_warnings를 자동 주입한다.

    P1-4 구현 (2026-05-13): 모든 라우터 응답에 일관된 신뢰도 메타데이터를 주입.
    ENDPOINT_CONFIDENCE 테이블에서 등급·경고를 조회하고, HEURISTIC 함수 사용 시
    HEURISTIC_FUNCTION_DISCLAIMERS에서 추가 경고를 자동 생성한다.

    Args:
        response:                  원본 응답 dict.
        endpoint_path:             ENDPOINT_CONFIDENCE 의 key (예: "/admet/{sequence}").
                                   미등록 경로는 기본값(B등급) 적용.
        heuristic_functions_used:  이 응답 생성에 사용된 HEURISTIC 함수 qualname 목록.
                                   HEURISTIC_FUNCTION_DISCLAIMERS 에 등록된 경우 경고 자동 추가.

    Returns:
        다음 필드가 추가된 새 dict (원본 변경 없음):
            confidence_grade      : "A" | "B" | "C" | "HEURISTIC"
            confidence_warnings   : List[str] — 경고 메시지 목록
            confidence_metadata   : Dict — 상세 메타데이터 (affected_metrics, source 등)

    Example::
        result = compute_admet_full(seq)
        return attach_confidence(result, "/admet/{sequence}")
        # → result["confidence_grade"] == "C"
        # → result["confidence_warnings"] == ["⚠️⚠️ DLscore 포화...", ...]

    Reviewer note (reviewer-pharma):
        이 함수는 *메타데이터 주입*이며 값 자체를 변경하지 않는다.
        등급은 pharmacology_guards.ENDPOINT_CONFIDENCE에서 관리하므로
        등급 변경이 필요하면 해당 테이블을 수정한다 (PR 시 Stage 5 절차 강제).
    """
    info = ENDPOINT_CONFIDENCE.get(endpoint_path, _DEFAULT_CONFIDENCE)

    warnings: List[str] = list(info.get("warnings", []))
    # 단수 "warning" 키 호환 (P1/P2 sprint 손실 복구 2026-05-20 SOD)
    # halflife_protparam, halflife_peptiderranker, admet_modlamp, admet_fab 등
    # 단일 경고 entry는 "warning" 단수 키 사용 — 누락 방지
    if "warning" in info and info["warning"] not in warnings:
        warnings.append(info["warning"])

    # HEURISTIC 함수 사용 시 추가 경고 자동 생성
    if heuristic_functions_used:
        for qn in heuristic_functions_used:
            disc = HEURISTIC_FUNCTION_DISCLAIMERS.get(qn)
            if disc:
                warnings.append(
                    f"⚠️ HEURISTIC — {qn}: {disc['actual_meaning']} "
                    f"(표면 단위: {disc['surface_unit']}). "
                    f"유효 사용: {disc['valid_use']}"
                )

    # 원본 dict 복사 후 필드 주입 (원본 불변)
    result = dict(response)
    result["confidence_grade"] = info.get("grade", "B")
    result["confidence_warnings"] = warnings
    result["confidence_metadata"] = {
        "grade": info.get("grade", "B"),
        "affected_metrics": info.get("metrics", []),
        "source": info.get("source", ""),
        "heuristic_functions": heuristic_functions_used or [],
        "guard_version": "pharmacology_guards.py P1-4 (2026-05-13)",
    }
    return result
