"""
prompts.py
==========
Agent-specific prompt templates for Qwen 2.5 7B / Qwen 3.5-35B-A3B.

각 LLM-backed 에이전트(Planner, Critic, Reporter)의 시스템/사용자 프롬프트를
구조화된 템플릿으로 관리한다. JSON 출력 스키마를 명시하여 파싱 안정성을 높인다.

Usage:
    from AG_src.llm.prompts import get_system_prompt, format_planner_prompt
    system = get_system_prompt("planner")
    user = format_planner_prompt(iteration=1, constraints={...})

    # M4 버그 픽스 — 직접 변이 생성 (few-shot 강화):
    from AG_src.llm.prompts import build_variant_generation_prompt
    prompt = build_variant_generation_prompt(
        reference_sequence="AGCKNFFWKTFTSC",
        mutable_positions=[1,2,4,5,6,11,12,13],
        n_mutations=3,
    )
    result = provider.generate_json(prompt)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# System Prompts (역할 설정)
# ---------------------------------------------------------------------------

_PLANNER_SYSTEM_DEFAULT = (
    "You are PlannerAgent, a computational biologist specializing in "
    "SSTR2-selective peptide binder design using RFdiffusion, ProteinMPNN, "
    "and ESMFold.\n\n"
    "Your task: Given the current iteration state and constraints, produce "
    "an ExperimentPlan with specific parameter choices and a testable "
    "scientific hypothesis.\n\n"
    "Rules:\n"
    "- Always output valid JSON matching the schema below.\n"
    "- Propose concrete numeric parameters (n_backbone, k_seq, etc.).\n"
    "- State a falsifiable hypothesis for this iteration.\n"
    "- Reference previous results when available.\n"
)

_PLANNER_SYSTEM_PYROSETTA_ONLY = (
    "You are PlannerAgent for a PyRosetta-only mutate->dock loop.\n\n"
    "Your task: Given the current iteration state, previous results, and critic feedback,\n"
    "produce an ExperimentPlan that includes **specific mutation guidance** for the next iteration.\n\n"
    "CRITICAL RULES (MUST follow — plan is invalid if violated):\n"
    "- Always output valid JSON matching the schema below.\n"
    "- mutation_guidance MUST be populated with focus_positions (non-empty list) and\n"
    "  suggested_mutations (non-empty dict). Returning an empty focus_positions or\n"
    "  empty suggested_mutations is a FAILURE.\n"
    "- MUST suggest mutations for AT LEAST 2 distinct positions from the mutable set.\n"
    "- Base mutation suggestions on previous ddG results and SSTR2 binding pocket chemistry.\n"
    "- Reference previous iteration outcomes when available.\n"
    "- Hypothesis must be testable within mutate->dock / ddG / clash terms.\n"
    "- Allowed action terms: mutate->dock, QC, critic, reporter.\n"
    "- Do NOT mention RFdiffusion, ProteinMPNN, ESMFold, or related aliases.\n\n"
    "PRIMARY CAMPAIGN OBJECTIVE — SSTR2 SELECTIVITY (radiopharmaceutical):\n"
    "- Goal is NOT just strong SSTR2 binding (ddG) but SSTR2 SELECTIVITY: bind SSTR2 strongly\n"
    "  while binding off-targets SSTR1/SSTR3/SSTR4/SSTR5 WEAKLY. Native SST-14 is a pan-agonist\n"
    "  (binds all subtypes ~equally) — your job is to BREAK off-target affinity, especially SSTR3/SSTR5,\n"
    "  while preserving SSTR2 binding. Target: selectivity_margin = min(offtarget ddG) - SSTR2 ddG > 0.\n"
    "- Selectivity arises from peptide contacts with SSTR2-UNIQUE receptor regions: ECL2 (res 192/193/195/197),\n"
    "  ECL3 (284/286), TM5 (205/208/209/212), TM6 (272/273/276/279). Off-target subtypes differ there.\n"
    "- STRATEGY: mutate non-pharmacophore peptide positions (1,2,4,5,6,11,12) to (a) enhance complementarity\n"
    "  with SSTR2-unique ECL2/ECL3/TM5/TM6 contacts, and/or (b) introduce charge/steric features that clash\n"
    "  with off-target-conserved pocket while tolerated by SSTR2. PRESERVE FWKT pharmacophore (pos 7-10)\n"
    "  and Cys3/Cys14 disulfide — never mutate these.\n"
    "- If previous results show NEGATIVE selectivity_margin (off-target binds stronger), propose mutations\n"
    "  that DIFFERENTIATE: e.g., charge changes at 1/2/5/6/11/12 to disrupt off-target electrostatics,\n"
    "  or bulky/aromatic substitutions exploiting SSTR2-specific subpockets.\n"
)

SYSTEM_PROMPTS: Dict[str, str] = {
    "planner": _PLANNER_SYSTEM_DEFAULT,
    "planner_pyrosetta_only": _PLANNER_SYSTEM_PYROSETTA_ONLY,
    "critic": (
        "You are ScientistCriticAgent, an expert reviewer of computational "
        "protein design experiments targeting SSTR2.\n\n"
        "Your task: Analyze the QC results and rank table from the current "
        "iteration, identify failure patterns, and propose up to 2 parameter "
        "changes for the next iteration.\n\n"
        "PRIMARY CAMPAIGN OBJECTIVE — SSTR2 SELECTIVITY (radiopharmaceutical):\n"
        "- Success is NOT strong SSTR2 binding alone. It is SSTR2 SELECTIVITY: bind SSTR2 strongly\n"
        "  while binding off-targets SSTR1/3/4/5 weakly. The metric is Δmargin = candidate_margin −\n"
        "  native_margin (home-advantage corrected). Δmargin > 0 means MORE selective than native SST-14.\n"
        "- If a SELECTIVITY section is present, treat it as the top-priority signal. When Δmargin ≤ 0,\n"
        "  the campaign has NOT succeeded — diagnose why off-targets still bind (usually SSTR3/SSTR5\n"
        "  conserved-pocket contacts) and propose mutations that push Δmargin positive: disrupt\n"
        "  off-target contacts at non-pharmacophore positions 1/2/5/6/11/12 while preserving FWKT(7-10)\n"
        "  and Cys3/Cys14. Selectivity is a failure dimension distinct from structural/sequence/docking/\n"
        "  stability — do not let strong ddG mask poor selectivity.\n\n"
        "Rules:\n"
        "- Always output valid JSON matching the schema below.\n"
        "- Classify failures as: structural, sequence, docking, stability, or selectivity.\n"
        "- Each parameter change must include rationale and expected effect.\n"
        "- Be conservative on protocol params, but be decisive about selectivity-driving mutations\n"
        "  when Δmargin is non-positive.\n"
    ),
    "reporter": (
        "You are ReporterAgent, a scientific writer producing iteration "
        "summaries for an SSTR2 peptide binder design campaign.\n\n"
        "Your task: Generate a concise lab notebook entry summarizing the "
        "iteration results, key findings, and recommendations.\n\n"
        "Rules:\n"
        "- Write in scientific style (clear, precise, data-driven).\n"
        "- Include key metrics: pLDDT, docking scores, ddG, selectivity.\n"
        "- Highlight top candidates with their IDs and scores.\n"
        "- Note any QC gate failures and their implications.\n"
    ),
}


# ---------------------------------------------------------------------------
# JSON Output Schemas (에이전트별 출력 형식 명세)
# ---------------------------------------------------------------------------

OUTPUT_SCHEMAS: Dict[str, str] = {
    "planner_pyrosetta_only": """{
  "run_id": "string (e.g., 20260218_1430_iter01)",
  "iteration": "integer",
  "hypothesis": "string (falsifiable scientific hypothesis)",
  "mutation_guidance": {
    "focus_positions": [5, 6, 11],
    "suggested_mutations": {
      "5": ["W", "F", "Y"],
      "6": ["E", "D"],
      "11": ["L", "I", "V"]
    },
    "n_guided": "integer (how many of n_candidates to use guidance, rest random)",
    "strategy": "string (e.g., aromatic_enrichment, charge_optimization)"
  },
  "parameters": {
    "rosetta_relax_cycles": "integer",
    "rosetta_ddg_max": "float"
  },
  "changes_from_prev": [
    {"parameter": "string", "old_value": "any", "new_value": "any", "reason": "string"}
  ]
}""",
    "planner": """{
  "run_id": "string (e.g., 20260218_1430_iter01)",
  "iteration": "integer",
  "hypothesis": "string (falsifiable scientific hypothesis)",
  "parameters": {
    "n_backbone": "integer (5-50)",
    "k_seq_per_backbone": "integer (4-16)",
    "top_m_rosetta": "integer (5-30)",
    "contigs": "string (RFdiffusion contig spec)",
    "hotspot_res": ["string (e.g., B122)"]
  },
  "steps_config": {
    "step01_receptor": {"enabled": true},
    "step02_rfdiffusion": {"noise_scale": "float"},
    "step03_proteinmpnn": {"sampling_temp": "float"},
    "step04_esmfold": {"min_plddt": "float"},
    "step05_docking": {"engine": "diffdock|boltz2"},
    "step06_rosetta": {"relax_cycles": "integer"},
    "step07_analysis": {"enabled": true}
  },
  "changes_from_prev": [
    {"parameter": "string", "old_value": "any", "new_value": "any", "reason": "string"}
  ]
}""",
    "critic": """{
  "overall_assessment": "string (1-2 sentence summary)",
  "failure_analysis": {
    "structural_failures": "integer",
    "sequence_failures": "integer",
    "docking_failures": "integer",
    "stability_failures": "integer",
    "primary_failure_type": "string"
  },
  "parameter_changes": [
    {
      "parameter_name": "string",
      "old_value": "any",
      "new_value": "any",
      "rationale": "string",
      "expected_effect": "string"
    }
  ],
  "hypothesis_update": "string (revised hypothesis if needed)",
  "convergence_signal": "boolean"
}""",
    "reporter": """{
  "title": "string (iteration summary title)",
  "summary": "string (2-3 paragraph summary)",
  "key_metrics": {
    "n_candidates_total": "integer",
    "n_passed_qc": "integer",
    "best_plddt": "float",
    "best_dock_score": "float",
    "best_ddg": "float",
    "selectivity_pass_rate": "float"
  },
  "top_candidates": [
    {"id": "string", "plddt": "float", "dock_score": "float", "ddg": "float"}
  ],
  "recommendations": ["string"]
}""",
}


# ---------------------------------------------------------------------------
# Prompt Formatters
# ---------------------------------------------------------------------------

def get_system_prompt(agent_name: str, planner_mode: str = "default") -> str:
    """에이전트 이름에 해당하는 시스템 프롬프트를 반환한다."""
    if agent_name == "planner":
        if planner_mode in {"pyrosetta_only", "pyrosetta-only"}:
            return SYSTEM_PROMPTS["planner_pyrosetta_only"]
        return SYSTEM_PROMPTS["planner"]
    return SYSTEM_PROMPTS.get(agent_name, "You are a helpful assistant.")


def get_output_schema(agent_name: str, planner_mode: str = "default") -> str:
    """에이전트 이름에 해당하는 JSON 출력 스키마를 반환한다."""
    if agent_name == "planner" and planner_mode in {"pyrosetta_only", "pyrosetta-only"}:
        return OUTPUT_SCHEMAS.get("planner_pyrosetta_only", OUTPUT_SCHEMAS.get(agent_name, "{}"))
    return OUTPUT_SCHEMAS.get(agent_name, "{}")


def format_planner_prompt(
    iteration: int,
    receptor_config: Dict[str, Any],
    constraints: Dict[str, Any],
    previous_results: Optional[Dict[str, Any]] = None,
    critic_feedback: Optional[Dict[str, Any]] = None,
    planner_mode: str = "default",
) -> str:
    """PlannerAgent용 사용자 프롬프트를 생성한다."""
    lines = [
        f"## Iteration {iteration} - Experiment Planning",
        "",
        f"**Receptor**: {receptor_config.get('name', 'SSTR2')}",
        f"**Reference peptide**: {constraints.get('reference_sequence', 'AGCKNFFWKTFTSC')}",
        f"**Planner mode**: {'pyrosetta-only' if planner_mode in {'pyrosetta_only', 'pyrosetta-only'} else 'default'}",
        "",
        "### Constraints",
    ]

    for key, val in constraints.items():
        lines.append(f"- {key}: {val}")

    if planner_mode in {"pyrosetta_only", "pyrosetta-only"}:
        lines.extend([
            "",
            "### Peptide Design Space",
            f"- Original sequence: {constraints.get('reference_sequence', 'AGCKNFFWKTFTSC')}",
            f"- Mutable positions (1-indexed): {constraints.get('design_positions', [1,2,4,5,6,7,8,9,10,11,12,14])}",
            "- Fixed: position 3 (Cys, disulfide), position 13 (Ser)",
            "- Cysteine is excluded from mutation candidates",
        ])

    if previous_results:
        lines.extend([
            "",
            "### Previous Iteration Results",
            f"- Best ddG: {previous_results.get('best_ddg', 'N/A')}",
            f"- Best pLDDT: {previous_results.get('best_plddt', 'N/A')}",
            f"- Candidates passed QC: {previous_results.get('n_passed', 'N/A')}",
            f"- Hypothesis: {previous_results.get('hypothesis', 'N/A')}",
        ])
        top_candidates = previous_results.get("top_candidates", [])
        if top_candidates:
            lines.append("")
            lines.append("### Top Candidates from Previous Iteration")
            for tc in top_candidates[:5]:
                lines.append(
                    f"- {tc.get('id', '?')}: sequence={tc.get('sequence', '?')}, "
                    f"ddG={tc.get('ddg', 'N/A')}"
                )
        # 2026-06-10: in-loop 선택성 피드백 — Δmargin>0 = native SST-14 보다 SSTR2-선택적(목표!).
        sel_lb = previous_results.get("selectivity_leaderboard")
        if sel_lb:
            lines.append("")
            lines.append("### SELECTIVITY Leaderboard (측정된 후보 — Δmargin>0 이 목표: native SST-14 초과 선택성)")
            lines.append(f"- Best Δmargin so far: {previous_results.get('best_delta_margin', 'N/A')} "
                         f"(>0 이면 native 보다 SSTR2-선택적)")
            for e in sel_lb[:5]:
                lines.append(
                    f"- {e.get('sequence', '?')}: Δmargin={e.get('delta_margin', 'N/A')} "
                    f"(margin={e.get('margin', 'N/A')}, ddG={e.get('ddg', 'N/A')})"
                )
            lines.append("→ Δmargin 이 음수/0 이면 아직 native 만큼도 선택적이지 않음. "
                         "Δmargin 양수를 키우는 변이(SSTR3/5 회피, SSTR2-고유 ECL2/ECL3·TM5/TM6 상보)에 집중하라.")

    if critic_feedback:
        lines.extend([
            "",
            "### Critic Feedback",
            f"- Assessment: {critic_feedback.get('overall_assessment', 'N/A')}",
            f"- Primary failure: {critic_feedback.get('primary_failure_type', 'N/A')}",
        ])
        for change in critic_feedback.get("parameter_changes", []):
            lines.append(
                f"- Change {change.get('parameter_name')}: "
                f"{change.get('old_value')} -> {change.get('new_value')} "
                f"({change.get('rationale', '')})"
            )

    if planner_mode in {"pyrosetta_only", "pyrosetta-only"}:
        lines.extend(
            [
                "",
                "### PyRosetta-only Rules (ENFORCE STRICTLY)",
                "- Allowed action terms: mutate->dock, QC, critic, reporter",
                "- Forbidden terms: RFdiffusion, ProteinMPNN, ESMFold (and aliases)",
                "- MUST populate mutation_guidance.focus_positions with ≥2 positions (empty list = INVALID)",
                "- MUST populate mutation_guidance.suggested_mutations with ≥2 entries (empty dict = INVALID)",
                "- Returning the reference sequence unchanged or providing zero mutations is a FAILURE",
            ]
        )

    lines.extend([
        "",
        "### Output Format",
        "Respond with a JSON object matching this schema:",
        f"```json\n{get_output_schema('planner', planner_mode=planner_mode)}\n```",
    ])

    return "\n".join(lines)


def format_critic_prompt(
    iteration: int,
    rank_table_summary: Dict[str, Any],
    qc_report_summary: Dict[str, Any],
    current_params: Dict[str, Any],
    selectivity_info: Optional[Dict[str, Any]] = None,
) -> str:
    """ScientistCriticAgent용 사용자 프롬프트를 생성한다."""
    lines = [
        f"## Iteration {iteration} - Critical Analysis",
        "",
        "### QC Report Summary",
        f"- Total candidates: {qc_report_summary.get('total', 0)}",
        f"- Passed QC gate: {qc_report_summary.get('passed', 0)}",
        f"- Failed QC gate: {qc_report_summary.get('failed', 0)}",
        f"- Pass rate: {qc_report_summary.get('pass_rate', 0):.1%}",
    ]

    gate_results = qc_report_summary.get("gate_results", {})
    if gate_results:
        lines.append("")
        lines.append("### Gate-by-Gate Results")
        for gate, stats in gate_results.items():
            lines.append(f"- {gate}: {stats}")

    lines.extend([
        "",
        "### Rank Table (Top 5)",
    ])
    for cand in rank_table_summary.get("top_candidates", [])[:5]:
        lines.append(
            f"- {cand.get('id', '?')}: pLDDT={cand.get('plddt', 0):.1f}, "
            f"dock={cand.get('dock_score', 0):.2f}, ddG={cand.get('ddg', 0):.1f}"
        )

    lines.extend([
        "",
        "### Current Parameters",
    ])
    for key, val in current_params.items():
        lines.append(f"- {key}: {val}")

    # 2026-06-10: in-loop 선택성 리더보드 (Δmargin>0 = native SST-14 초과 선택성 = 캠페인 목표).
    if selectivity_info:
        lb = selectivity_info.get("leaderboard") or []
        best = selectivity_info.get("best_delta_margin")
        lines.extend([
            "",
            "### SELECTIVITY (PRIMARY OBJECTIVE — SSTR2 vs SSTR1/3/4/5)",
            f"- Best Δmargin so far: {best if best is not None else 'N/A'} "
            "(Δmargin = candidate_margin − native_margin; >0 = MORE selective than native SST-14)",
        ])
        if lb:
            lines.append("- Screened candidates:")
            for e in lb[:5]:
                lines.append(
                    f"  - {e.get('sequence', '?')}: Δmargin={e.get('delta_margin', 'N/A')}, "
                    f"margin={e.get('margin', 'N/A')}, ddG={e.get('ddg', 'N/A')}"
                )
        else:
            lines.append("- No candidate screened for selectivity yet this run.")
        lines.append(
            "- INTERPRET: Δmargin ≤ 0 means NOT yet selective beyond native — the campaign has not "
            "succeeded. Diagnose WHY off-targets still bind (likely SSTR3/SSTR5 conserved-pocket "
            "contacts) and propose parameter changes (focus_positions, suggested_mutations) that push "
            "Δmargin positive: disrupt off-target contacts at non-pharmacophore positions 1/2/5/6/11/12 "
            "while preserving FWKT(7-10) + Cys3/Cys14. Treat selectivity as a failure dimension distinct "
            "from structural/sequence/docking/stability."
        )

    lines.extend([
        "",
        "### Output Format",
        "Respond with a JSON object matching this schema:",
        f"```json\n{get_output_schema('critic')}\n```",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Variant Generation Prompt (M4 버그 픽스 — 직접 변이 생성용 few-shot 강화 프롬프트)
# ---------------------------------------------------------------------------

# SST-14 참조 시퀀스에 대한 검증된 few-shot 예시 (1-indexed)
# 불변 위치: 3(Cys, 이황화), 7(Phe), 8(Trp), 9(Lys), 10(Thr), 14(Cys, 이황화)
# 가변 위치: [1,2,4,5,6,11,12,13]
_SST14_FEW_SHOT_EXAMPLES: List[Dict[str, str]] = [
    {
        "input_seq": "AGCKNFFWKTFTSC",
        "mutable": "[1,2,4,5,6,11,12,13]",
        "n": "3",
        "vid": "v01",
        "output_seq": "PGCKHFFWKTFISC",
        "mutations_json": (
            '[{"pos":1,"from":"A","to":"P"},'
            '{"pos":5,"from":"N","to":"H"},'
            '{"pos":12,"from":"T","to":"I"}]'
        ),
    },
    {
        "input_seq": "AGCKNFFWKTFTSC",
        "mutable": "[1,2,4,5,6,11,12,13]",
        "n": "3",
        "vid": "v02",
        "output_seq": "AECKNLFWKTYTSC",
        "mutations_json": (
            '[{"pos":2,"from":"G","to":"E"},'
            '{"pos":6,"from":"F","to":"L"},'
            '{"pos":11,"from":"F","to":"Y"}]'
        ),
    },
]

# 변이 생성 시스템 프롬프트 (direct variant generation용)
VARIANT_DESIGN_SYSTEM_PROMPT = (
    "You are a peptide variant designer specializing in SSTR2-targeting SST-14 analogs.\n\n"
    "CRITICAL RULES (MUST follow without exception):\n"
    "1. Preserve C3 and C14 (disulfide bond) — positions 3 and 14 are FIXED\n"
    "2. Preserve FWKT pharmacophore — positions 7, 8, 9, 10 are FIXED\n"
    "3. You MUST mutate EXACTLY the requested number of positions (n_mutations)\n"
    "4. Each mutation MUST change the amino acid (from_aa ≠ to_aa)\n"
    "5. Output ONLY valid JSON — no text, no markdown, no explanation\n\n"
    "FAILURE CONDITIONS (output rejected if any apply):\n"
    "- mutations array length ≠ n_mutations\n"
    "- Any mutation modifies positions 3, 7, 8, 9, 10, or 14\n"
    "- from_aa equals to_aa (no-op mutation)\n"
    "- sequence does not reflect all listed mutations\n"
)


def build_variant_generation_prompt(
    reference_sequence: str,
    mutable_positions: List[int],
    n_mutations: int,
    variant_id: str = "v03",
) -> str:
    """직접 변이 생성을 위한 few-shot 강화 프롬프트를 생성한다.

    M4 발견 버그 픽스: Qwen3.5-35B-A3B가 mutation 명시 prompt에도 원본 시퀀스를
    그대로 반환하는 보수적 응답 현상 방지.

    3가지 강화 기법:
    1. 명시적 강제 — "MUST mutate EXACTLY N positions" (대문자 + MUST)
    2. Few-shot examples — 올바른 변이가 적용된 시퀀스 2개 포함
    3. 검증 가능 instruction — mutations 배열 길이 명시

    Args:
        reference_sequence: 원본 펩타이드 시퀀스 (예: "AGCKNFFWKTFTSC")
        mutable_positions: 변이 가능 위치 목록, 1-indexed (예: [1,2,4,5,6,11,12,13])
        n_mutations: 정확히 변이해야 할 위치 수 (예: 3)
        variant_id: 생성할 변이체 ID (예: "v03")

    Returns:
        LLM에 직접 전달 가능한 self-contained few-shot 프롬프트 문자열.
        generate_json(prompt) 또는 generate_json(prompt, system_prompt=VARIANT_DESIGN_SYSTEM_PROMPT)
        형태로 사용 가능.
    """
    mutable_str = str(mutable_positions)
    n = n_mutations

    # few-shot 예시 구성
    example_lines: List[str] = [
        "You are a peptide variant designer for SST-14 (SSTR2 targeting).",
        "",
        "RULES (MUST follow):",
        "1. Preserve C3, C14 (disulfide bond) — positions 3 and 14 are FIXED",
        "2. Preserve FWKT pharmacophore — positions 7, 8, 9, 10 are FIXED",
        f"3. You MUST mutate EXACTLY {n} positions — NOT 0, NOT 1, EXACTLY {n}",
        "4. Each mutation must change the amino acid (from_aa ≠ to_aa)",
        "5. Output ONLY valid JSON with keys: variant_id, sequence, mutations",
        f"6. mutations array MUST have exactly {n} entries",
        "",
        "EXAMPLES (follow this exact JSON format):",
        "",
    ]

    # SST-14 참조 시퀀스 예시 포함 (검증된 few-shot)
    for ex in _SST14_FEW_SHOT_EXAMPLES:
        example_lines.append(
            f"Input: sequence={ex['input_seq']} "
            f"mutable={ex['mutable']} "
            f"n_mutations={ex['n']} "
            f"variant_id={ex['vid']}"
        )
        example_lines.append(
            f'Output: {{"variant_id":"{ex["vid"]}",'
            f'"sequence":"{ex["output_seq"]}",'
            f'"mutations":{ex["mutations_json"]}}}'
        )
        example_lines.append("")

    # 실제 쿼리
    example_lines.extend([
        f"NOW GENERATE (MUST have EXACTLY {n} entries in mutations array — returning original sequence is a FAILURE):",
        f"Input: sequence={reference_sequence} "
        f"mutable={mutable_str} "
        f"n_mutations={n} "
        f"variant_id={variant_id}",
        "Output:",
    ])

    return "\n".join(example_lines)


def format_reporter_prompt(
    iteration: int,
    run_id: str,
    rank_table_summary: Dict[str, Any],
    critic_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """ReporterAgent용 사용자 프롬프트를 생성한다."""
    lines = [
        f"## Iteration {iteration} Report - {run_id}",
        "",
        "### Results Summary",
        f"- Total candidates evaluated: {rank_table_summary.get('total', 0)}",
        f"- Passed all QC gates: {rank_table_summary.get('passed', 0)}",
    ]

    top = rank_table_summary.get("top_candidates", [])
    if top:
        lines.extend(["", "### Top Candidates"])
        for cand in top[:10]:
            lines.append(
                f"- {cand.get('id')}: pLDDT={cand.get('plddt', 0):.1f}, "
                f"dock={cand.get('dock_score', 0):.2f}, "
                f"ddG={cand.get('ddg', 0):.1f}"
            )

    if critic_analysis:
        lines.extend([
            "",
            "### Critic Analysis",
            f"- Assessment: {critic_analysis.get('overall_assessment', 'N/A')}",
            f"- Primary failure type: {critic_analysis.get('primary_failure_type', 'N/A')}",
        ])

    lines.extend([
        "",
        "### Task",
        "Write a scientific lab notebook entry summarizing this iteration.",
        "Include key metrics, notable candidates, and recommendations for the next iteration.",
        "",
        "### Output Format",
        "Respond with a JSON object matching this schema:",
        f"```json\n{get_output_schema('reporter')}\n```",
    ])

    return "\n".join(lines)
