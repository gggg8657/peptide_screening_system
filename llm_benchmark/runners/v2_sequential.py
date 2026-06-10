"""
v2_sequential.py — V2 LLM-direct mutation flow runner

V1 대비 변경:
  - Planner가 완전한 14-aa 서열을 직접 JSON으로 출력
  - SequenceValidator: 길이 / FWKT / Cys / BLOSUM62 / 중복 검증
  - n_guided ≤ 50% 상한 (나머지 균등 랜덤으로 exploration 보존)
  - Hamming diversity 모니터링 (mode collapse 감지)
  - LLMStructuralCritic: 구조적 분석 기반 다음 iteration 전략 세분화

재사용 (변경 없음):
  - FlexPepDock subprocess 실행
  - QCRankerAgent, ScientistCriticAgent, ReporterAgent
  - SES 계산, StatusEmitter, ConvergenceDetector

구현 패턴:
  collaborative.py와 동일하게 monkey-patch 방식 사용.
  PlannerAgent → _PatchedPlannerAgent (LLMDirectMutationPlanner 반환)
  generate_guided_mutant → proposed_sequences pop 우선 사용
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExperimentConfig, SequentialFlowRunner, REPO_ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

_SST14_SEQ = "AGCKNFFWKTFTSC"
# SST-14 구조:  A(1)G(2)C(3)K(4)N(5)F(6)F(7)W(8)K(9)T(10)F(11)T(12)S(13)C(14)
#   Cys3-Cys14: disulfide bond
#   FWKT: 포지션 7-10 (약물단)
_FWKT_REF: Dict[int, str] = {7: "F", 8: "W", 9: "K", 10: "T"}  # 1-indexed
_AA_VALID = set("ACDEFGHIKLMNPQRSTVWY")
_AA_NO_CYS = list("ADEFGHIKLMNPQRSTVWY")  # Cys 제외 18종 (V1 균등 랜덤과 동일)
_BLOSUM62_MIN_SCORE = -1
_HAMMING_COLLAPSE_THRESHOLD = 1.5
# V1 design_positions = [1,2,4,5,6,7,8,9,10,11,12,14]에서 FWKT(7-10) 제외
# → 실제 변이 가능: [1, 2, 4, 5, 6, 11, 12] (pos3=Cys3, pos14=Cys14 disulfide 고정)
# ※ pos14(C14)는 disulfide 구성원이므로 mutable에서 제외 — validator 일관성 확보
_MUTABLE_POSITIONS_DEFAULT = [1, 2, 4, 5, 6, 11, 12]


# ---------------------------------------------------------------------------
# BLOSUM62 — BioPython 있으면 사용, 없으면 필터 비적용
# ---------------------------------------------------------------------------

def _load_blosum62() -> Optional[Any]:
    try:
        import Bio.Align.substitution_matrices as sm  # type: ignore[import]
        return sm.load("BLOSUM62")
    except Exception:
        return None


_BLOSUM62_MATRIX = _load_blosum62()


def blosum62_score(aa_from: str, aa_to: str) -> Optional[int]:
    """BLOSUM62 점수 반환. 매트릭스 없으면 None."""
    if _BLOSUM62_MATRIX is None:
        return None
    try:
        return int(_BLOSUM62_MATRIX[aa_from][aa_to])
    except (KeyError, TypeError):
        return None


def blosum62_filter(original_aa: str, proposed_aa: str) -> bool:
    """치환이 BLOSUM62 min_score 이상이면 True. 매트릭스 없으면 항상 True."""
    if original_aa == proposed_aa:
        return True
    score = blosum62_score(original_aa, proposed_aa)
    if score is None:
        return True  # BioPython 없으면 필터 미적용
    return score >= _BLOSUM62_MIN_SCORE


# ---------------------------------------------------------------------------
# SequenceValidator
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    sequence: str
    valid: bool
    errors: List[str]
    blosum62_failures: List[str]


def validate_sequence(
    seq: str,
    original: str,
    seen: set,
    mutable_positions: List[int],
    apply_blosum62: bool = True,
) -> ValidationResult:
    """완전한 서열 검증 — 7가지 제약 조건.

    Args:
        seq: 검증할 서열
        original: 기준 서열 (SST-14)
        seen: 이미 시도된 서열 집합 (중복 방지)
        mutable_positions: 변이 허용 포지션 목록 (1-indexed)
        apply_blosum62: BLOSUM62 필터 적용 여부

    Returns:
        ValidationResult (valid=True면 FlexPepDock에 전달 가능)
    """
    errors: List[str] = []
    blosum62_failures: List[str] = []

    # 1. 길이 체크
    if len(seq) != len(original):
        errors.append(f"length {len(seq)} != {len(original)}")
        return ValidationResult(seq, False, errors, blosum62_failures)

    # 2. 유효 AA 체크 (20종 표준 AA)
    invalid = [c for c in seq if c not in _AA_VALID]
    if invalid:
        errors.append(f"invalid AA: {invalid}")

    # 3. FWKT 약물단 보존 (pos 7, 8, 9, 10)
    for pos, aa in _FWKT_REF.items():
        if seq[pos - 1] != aa:
            errors.append(f"pharmacophore pos{pos}: got '{seq[pos-1]}' expected '{aa}'")

    # 4. 신규 Cys 도입 금지 (원본에 없는 위치에 Cys 추가 금지)
    # V1의 AA_NO_CYS와 동일한 정책: 기존 Cys(pos3, pos14)는 유지, 새 Cys는 불허
    for i in range(len(seq)):
        if seq[i] == "C" and original[i] != "C":
            errors.append(f"new Cys introduced at pos{i + 1}")

    # 5. 원본 서열과 동일 체크
    if seq == original:
        errors.append("identical to original sequence")

    # 6. 중복 체크 (seen set과 비교)
    if seq in seen:
        errors.append("duplicate sequence")

    # 7. 고정 포지션 변이 금지
    fixed_positions = [
        p for p in range(1, len(original) + 1)
        if p not in mutable_positions and p not in _FWKT_REF
    ]
    for pos in fixed_positions:
        if seq[pos - 1] != original[pos - 1]:
            errors.append(
                f"non-mutable pos{pos}: '{original[pos-1]}'→'{seq[pos-1]}'"
            )

    # 8. BLOSUM62 필터 (선택적)
    if apply_blosum62:
        for pos in mutable_positions:
            if pos > len(seq) or pos > len(original):
                continue
            orig_aa = original[pos - 1]
            prop_aa = seq[pos - 1]
            if prop_aa != orig_aa and not blosum62_filter(orig_aa, prop_aa):
                blosum62_failures.append(
                    f"pos{pos}: {orig_aa}→{prop_aa} "
                    f"(BLOSUM62={blosum62_score(orig_aa, prop_aa)} < {_BLOSUM62_MIN_SCORE})"
                )

    # BLOSUM62 failures are logged but do NOT reject the sequence
    has_errors = bool(errors)
    return ValidationResult(seq, not has_errors, errors, blosum62_failures)


# ---------------------------------------------------------------------------
# Hamming diversity
# ---------------------------------------------------------------------------

def mean_pairwise_hamming(sequences: List[str]) -> float:
    """서열 집합의 평균 쌍별 Hamming distance.

    mode collapse 감지에 사용: 값이 threshold 미만이면 LLM이 편향된 서열만 반복.
    """
    if len(sequences) < 2:
        return 0.0
    total, count = 0, 0
    for i in range(len(sequences)):
        for j in range(i + 1, len(sequences)):
            s1, s2 = sequences[i], sequences[j]
            total += sum(a != b for a, b in zip(s1, s2))
            count += 1
    return total / count if count else 0.0


# ---------------------------------------------------------------------------
# LLM prompt templates
# ---------------------------------------------------------------------------

_V2_SYSTEM_PROMPT = """\
You are an expert SSTR2 peptide binder designer.
Design MUTANT variants of SST-14 to improve SSTR2 binding affinity (lower ddG = better).

REFERENCE SEQUENCE (1-indexed, 14 amino acids):
  pos:  1  2  3  4  5  6  7  8  9 10 11 12 13 14
  AA:   A  G  C  K  N  F  F  W  K  T  F  T  S  C
       [M][M][X][M][M][M][X][X][X][X][M][M][X][X]
        M = Mutable (you may substitute)
        X = Fixed   (MUST keep original AA — any change is REJECTED)

FIXED positions — DO NOT change these 7 positions:
  pos  3 = C  (Cys3-Cys14 disulfide bond)
  pos  7 = F  ]
  pos  8 = W  ] FWKT pharmacophore — critical for SSTR2 binding
  pos  9 = K  ]
  pos 10 = T  ]
  pos 13 = S  (structural anchor)
  pos 14 = C  (Cys3-Cys14 disulfide bond)

MUTABLE positions — change ONLY these 7 positions:
  pos 1(A)  pos 2(G)  pos 4(K)  pos 5(N)  pos 6(F)  pos 11(F)  pos 12(T)

HARD CONSTRAINTS (any violation → sequence is REJECTED):
1. Output ONLY the 14-character sequence string — no spaces, no dashes, no numbers
2. Length must be exactly 14 characters
3. Each sequence MUST differ from AGCKNFFWKTFTSC by ≥1 substitution at a mutable position
4. No Cysteine (C) at any mutable position (pos 1,2,4,5,6,11,12)
5. Only standard amino acids: A D E F G H I K L M N P Q R S T V W Y
6. All sequences in your response must be unique (no duplicates within the batch)

VALID EXAMPLES (accepted):
  SGCKNFFWKTFTSC  — pos1: A→S  ✓
  LGCRNFFWKTFTSC  — pos1: A→L, pos4: K→R  ✓
  AGCKNFFWKTFSSC  — pos12: T→S  ✓
  AGCQNFFWKTVTSC  — pos4: K→Q, pos11: F→V  ✓
  MGCENFFWKTLTSC  — pos1: A→M, pos5: N→E, pos11: F→L  ✓

INVALID EXAMPLES (rejected):
  AGCKNFFWKTFTSC  ✗  identical to reference (no mutation)
  AGCKNFFWATFTSC  ✗  pos9(K→A) — pos9 is FIXED (FWKT pharmacophore)
  AGCKNFFWKTFTTC  ✗  pos13(S→T) — pos13 is FIXED (structural anchor)
  AGCKCFFWKTFTSC  ✗  pos5(N→C) — no Cys at mutable positions
  AGCKNFFWKTFTS C ✗  space in sequence — output ONLY the 14-character string

DESIGN PRINCIPLES:
- Mutate 1–3 mutable positions per sequence for interpretability
- Balance exploitation (refine best hits) and exploration (new combinations)
- Prefer substitutions that preserve physicochemical character or improve binding (hydrophobic→aromatic at pos1, charged→polar at pos4/5, etc.)

OUTPUT: JSON only, no markdown, no code blocks, no extra text:
{
  "sequences": ["<14aa_1>", "<14aa_2>", ...],
  "rationale": "<2-3 sentences, Korean OK>",
  "focus_positions": [<pos1>, <pos2>],
  "strategy": "exploit|explore|diversify"
}"""

_V2_USER_TEMPLATE = """\
## Iteration {iteration}/{max_iterations}

Reference: {original_sequence}   baseline ddG = {baseline_ddg} REU
  pos:  1  2  3  4  5  6  7  8  9 10 11 12 13 14
  AA:   A  G  C  K  N  F  F  W  K  T  F  T  S  C
       [M][M][X][M][M][M][X][X][X][X][M][M][X][X]  M=Mutable X=Fixed

FIXED (never change): pos 3(C), 7(F), 8(W), 9(K), 10(T), 13(S), 14(C)
MUTABLE (change only these): pos 1(A), 2(G), 4(K), 5(N), 6(F), 11(F), 12(T) — no C

## REQUIREMENTS for all {n_llm_sequences} sequences:
- Each must be exactly 14 characters (the sequence string only, no spaces)
- Each must differ from {original_sequence} by ≥1 mutation at a mutable position
- Do NOT output {original_sequence} — it is the reference, not a valid proposal
- All sequences must be unique (no duplicates within this batch)
- Avoid repeating sequences from the "Already tried" list below

## Previous iteration top candidates
{top_candidates}

## Critic feedback
{critic_feedback}

## Historical top hits
{historical_hits}

## Already tried ({n_seen} sequences — do NOT repeat ANY, showing last 20):
{seen_sample}

Generate exactly {n_llm_sequences} distinct 14-aa MUTANT sequences.
WARNING: Outputting {original_sequence} (unchanged reference) will be rejected.
JSON only (no code blocks, no text outside JSON)."""


def _format_top_candidates(candidates: List[Dict[str, Any]]) -> str:
    if not candidates:
        return "(none yet)"
    rows = ["sequence | ddG | clash | result"]
    for c in candidates[:5]:
        ddg = c.get("ddg", c.get("ddG", 999))
        clash = c.get("clash_score", c.get("clashScore", "?"))
        result = "PASS" if float(ddg) <= -5 else "FAIL"
        rows.append(f"{c.get('sequence','?')} | {float(ddg):.2f} | {clash} | {result}")
    return "\n".join(rows)


def _format_seen_sample(seen: set, n: int = 20) -> str:
    sample = list(seen)[-n:]
    return "\n".join(sample) if sample else "(none)"


def _safe_parse_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """JSON 파싱. 실패 시 markdown 코드블록 추출 재시도 후 None."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# LLMDirectMutationPlanner
# ---------------------------------------------------------------------------

class LLMDirectMutationPlanner:
    """PlannerAgent 래퍼: LLM이 완전한 14-aa 서열을 직접 생성.

    n_guided ≤ 50% 원칙:
        LLM 제안 서열은 전체 n_candidates의 최대 50%.
        나머지는 generate_random_mutant() (V1 균등 랜덤)으로 채움.

    propose_sequences 주입 방식:
        plan.parameters["mutation_guidance"]["proposed_sequences"] 리스트에 저장.
        runner.py의 monkey-patched generate_guided_mutant이 iteration마다 pop해서 사용.
    """

    def __init__(
        self,
        inner_planner: Any,
        llm: Any,
        n_candidates: int,
        original_sequence: str = _SST14_SEQ,
        mutable_positions: Optional[List[int]] = None,
        max_llm_retries: int = 2,
        apply_blosum62: bool = True,
        log_dir: Optional[Path] = None,
        experiment_id: str = "exp",
    ) -> None:
        self._inner = inner_planner
        self._llm = llm
        self._n_candidates = n_candidates
        self._original = original_sequence
        self._mutable_positions = mutable_positions or _MUTABLE_POSITIONS_DEFAULT
        self._max_retries = max_llm_retries
        self._apply_blosum62 = apply_blosum62
        self._log_dir = log_dir
        self._experiment_id = experiment_id
        # 자체 seen set: original은 항상 제외.
        # runner.py seen_sequences와 완전 동기화는 불가하지만
        # 중복 후보는 runner.py의 dedup retry loop가 최종 차단함.
        self._seen: set = {original_sequence}
        self._baseline_ddg: float = 0.0

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """inner planner 실행 후 LLM 서열을 mutation_guidance["proposed_sequences"]에 주입."""
        result = self._inner.execute(context)
        plan = result.get("plan")
        iteration = context.get("iteration", 1)

        # n_guided ≤ 50% 상한
        n_llm_slots = max(1, self._n_candidates // 2)

        sequences, focus_positions = self._generate_sequences_via_llm(
            context, n_llm_slots
        )

        # Mode collapse 감지
        hamming = mean_pairwise_hamming(sequences)
        is_collapsed = hamming < _HAMMING_COLLAPSE_THRESHOLD and len(sequences) >= 2
        if is_collapsed:
            logger.warning(
                "[V2] iter=%d mode collapse (Hamming=%.2f < %.1f) "
                "→ n_guided 축소 + diversify 강제",
                iteration, hamming, _HAMMING_COLLAPSE_THRESHOLD,
            )
            n_llm_slots = max(1, self._n_candidates // 4)  # collapse 시 25%로
            sequences = sequences[:n_llm_slots]

        if plan is not None:
            guidance = plan.parameters.setdefault("mutation_guidance", {})
            guidance["proposed_sequences"] = list(sequences)
            guidance["n_guided"] = n_llm_slots
            # focus_positions가 있어야 runner.py의 guided 분기 활성화
            if focus_positions:
                guidance["focus_positions"] = focus_positions
            elif not guidance.get("focus_positions"):
                guidance["focus_positions"] = self._mutable_positions[:3]
            if is_collapsed:
                guidance["strategy"] = "diversify"

        result["v2_sequences_proposed"] = sequences
        result["v2_hamming_diversity"] = round(hamming, 3)
        result["v2_mode_collapsed"] = is_collapsed
        result["v2_n_llm_slots"] = n_llm_slots
        return result

    def _generate_sequences_via_llm(
        self,
        context: Dict[str, Any],
        n_llm_slots: int,
    ) -> tuple[List[str], List[int]]:
        """LLM 호출 → 검증 → 유효 서열 리스트 반환.

        Returns:
            (valid_sequences, focus_positions)
        """
        if not self._has_real_llm():
            logger.debug("[V2] LLM 없음 → proposed_sequences 빈 리스트")
            return [], []

        iteration = context.get("iteration", 1)
        prev_results = context.get("previous_results", {})
        top_cands = prev_results.get("top_candidates", [])
        critic_fb = context.get("critic_feedback", {})
        hist_hits = prev_results.get("historical_top_hits", [])
        constraints = context.get("constraints", {})

        user_prompt = _V2_USER_TEMPLATE.format(
            iteration=iteration,
            max_iterations=constraints.get("max_iterations", "?"),
            original_sequence=self._original,
            baseline_ddg=f"{self._baseline_ddg:.2f}",
            mutable_positions=self._mutable_positions,
            top_candidates=_format_top_candidates(top_cands),
            critic_feedback=(
                json.dumps(critic_fb, ensure_ascii=False) if critic_fb else "(none yet)"
            ),
            historical_hits=(
                json.dumps(hist_hits[:3], ensure_ascii=False) if hist_hits else "(none)"
            ),
            n_seen=len(self._seen),
            seen_sample=_format_seen_sample(self._seen),
            n_llm_sequences=n_llm_slots,
        )

        valid_sequences: List[str] = []
        focus_positions: List[int] = []

        for attempt in range(self._max_retries + 1):
            t0 = time.time()
            try:
                raw = self._llm.generate(
                    user_prompt,
                    system_prompt=_V2_SYSTEM_PROMPT,
                    json_mode=True,
                )
            except Exception as exc:
                logger.warning("[V2] LLM 호출 실패 (attempt %d): %s", attempt, exc)
                break

            latency_ms = (time.time() - t0) * 1000
            parsed = _safe_parse_json(raw)

            self._write_llm_log(iteration, attempt, user_prompt, raw, parsed, latency_ms)

            if parsed is None:
                logger.warning("[V2] JSON 파싱 실패 (attempt %d/%d)", attempt, self._max_retries)
                continue

            if not focus_positions:
                focus_positions = parsed.get("focus_positions", [])

            for seq in parsed.get("sequences", []):
                if not isinstance(seq, str):
                    continue
                seq = seq.strip().upper()
                vr = validate_sequence(
                    seq, self._original, self._seen,
                    self._mutable_positions, self._apply_blosum62,
                )
                if vr.valid:
                    valid_sequences.append(seq)
                    self._seen.add(seq)
                else:
                    logger.debug(
                        "[V2] 서열 거부: %s errors=%s blosum=%s",
                        seq, vr.errors, vr.blosum62_failures,
                    )

            # 충분한 유효 서열 확보 시 early stop
            if len(valid_sequences) >= n_llm_slots:
                break

            logger.info(
                "[V2] attempt %d: %d/%d valid — %s",
                attempt, len(valid_sequences), n_llm_slots,
                "retry" if attempt < self._max_retries else "done",
            )

        return valid_sequences[:n_llm_slots], focus_positions

    def _has_real_llm(self) -> bool:
        return getattr(self._llm, "provider_name", "NoneProvider") != "NoneProvider"

    def _write_llm_log(
        self,
        iteration: int,
        attempt: int,
        prompt: str,
        raw: Optional[str],
        parsed: Optional[Dict[str, Any]],
        latency_ms: float,
    ) -> None:
        if self._log_dir is None:
            return
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self._log_dir / f"iter_{iteration:02d}_v2_planner.jsonl"
            entry = {
                "experiment_id": self._experiment_id,
                "iteration": iteration,
                "attempt": attempt,
                "prompt_length": len(prompt),
                "raw_response": raw,
                "parse_success": parsed is not None,
                "n_sequences_parsed": len(parsed.get("sequences", [])) if parsed else 0,
                "latency_ms": round(latency_ms, 1),
            }
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception as exc:
            logger.warning("[V2] LLM 로그 기록 실패: %s", exc)

    def __getattr__(self, name: str) -> Any:
        """PlannerAgent의 나머지 메서드/속성을 투명하게 위임."""
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# Patched generate_guided_mutant
# ---------------------------------------------------------------------------

def _make_v2_generate_guided_mutant(original_func: Any) -> Any:
    """proposed_sequences가 있으면 pop, 없으면 원본 로직으로 fallback하는 래퍼 반환.

    runner.py에서 generate_guided_mutant(original, design_positions, guidance, rng) 형태로 호출됨.
    guidance["proposed_sequences"] 리스트에서 pop하여 LLM 제안 서열을 직접 반환.
    리스트가 비면 원본 guided mutant 로직으로 fallback.
    """
    def _v2_generate(
        original_seq: str,
        design_positions: List[int],
        guidance: Dict[str, Any],
        rng: Any,
    ) -> str:
        proposed = guidance.get("proposed_sequences")
        if proposed and isinstance(proposed, list) and len(proposed) > 0:
            seq = proposed.pop(0)
            logger.debug("[V2] LLM proposed sequence used: %s", seq)
            return seq
        # fallback: V1 generate_guided_mutant (focus_positions + rng.choice)
        return original_func(original_seq, design_positions, guidance, rng)

    return _v2_generate


# ---------------------------------------------------------------------------
# LLMStructuralCritic
# ---------------------------------------------------------------------------

_STRUCTURAL_CRITIC_SYSTEM = """\
You are a structural biologist specializing in SSTR2 peptide binding.
Analyze docking results and provide actionable mutation strategy for next iteration.
Respond ONLY with valid JSON."""

_STRUCTURAL_CRITIC_TEMPLATE = """\
## Iteration {iteration} docking results

Reference: {original_sequence} (baseline ddG={baseline_ddg:.2f})

Results (sequence | ddG | clash | pass?):
{results_table}

Pass rate (ddG ≤ -5): {pass_rate:.1%}

Provide:
1. Root cause of failures
2. Positions correlating with better ddG
3. Specific AA substitutions to try next

JSON:
{{
  "failure_analysis": "<1-2 sentences>",
  "key_positions": [<pos>, ...],
  "suggested_mutations": {{"<pos>": ["<AA>", ...], ...}},
  "strategy_next": "exploit|explore|diversify",
  "hypothesis": "<testable hypothesis>"
}}"""


class LLMStructuralCritic:
    """ScientistCriticAgent 보완 — 구조적 분석 기반 구체적 변이 제안.

    기존 ScientistCriticAgent는 파라미터 변경(mpnn_temperature 등)을 제안.
    이 클래스는 추가로 다음 iteration에서 시도할 구체적 위치+AA를 반환.
    결과는 critic_feedback["structural_suggestions"]으로 Planner 컨텍스트에 추가 가능.
    """

    def __init__(
        self,
        llm: Any,
        original_sequence: str = _SST14_SEQ,
        log_dir: Optional[Path] = None,
        experiment_id: str = "exp",
    ) -> None:
        self._llm = llm
        self._original = original_sequence
        self._log_dir = log_dir
        self._experiment_id = experiment_id

    def analyze(
        self,
        candidates: List[Dict[str, Any]],
        iteration: int,
        baseline_ddg: float = 0.0,
    ) -> Dict[str, Any]:
        """후보 목록 구조 분석 → 다음 iteration 전략 반환.

        Args:
            candidates: CandidateResult를 dict로 변환한 목록
            iteration: 현재 iteration 번호
            baseline_ddg: SST-14 native ddG

        Returns:
            parsed JSON dict or {} on failure
        """
        if not self._has_real_llm() or not candidates:
            return {}

        results_table = "\n".join(
            "{} | {:.2f} | {} | {}".format(
                c.get("sequence", "?"),
                float(c.get("ddg", c.get("ddG", 999))),
                c.get("clash_score", c.get("clashScore", "?")),
                "PASS" if float(c.get("ddg", c.get("ddG", 999))) <= -5.0 else "FAIL",
            )
            for c in candidates[:10]
        )
        n_pass = sum(
            1 for c in candidates
            if float(c.get("ddg", c.get("ddG", 999))) <= -5.0
        )
        pass_rate = n_pass / len(candidates) if candidates else 0.0

        prompt = _STRUCTURAL_CRITIC_TEMPLATE.format(
            iteration=iteration,
            original_sequence=self._original,
            baseline_ddg=baseline_ddg,
            results_table=results_table,
            pass_rate=pass_rate,
        )

        try:
            t0 = time.time()
            raw = self._llm.generate(
                prompt,
                system_prompt=_STRUCTURAL_CRITIC_SYSTEM,
                json_mode=True,
            )
            latency_ms = (time.time() - t0) * 1000
            parsed = _safe_parse_json(raw)
            if parsed:
                parsed["latency_ms"] = round(latency_ms, 1)
                self._write_log(iteration, prompt, raw, parsed)
                return parsed
        except Exception as exc:
            logger.warning("[V2Critic] 분석 실패 (non-fatal): %s", exc)
        return {}

    def _has_real_llm(self) -> bool:
        return getattr(self._llm, "provider_name", "NoneProvider") != "NoneProvider"

    def _write_log(
        self,
        iteration: int,
        prompt: str,
        raw: Optional[str],
        parsed: Dict[str, Any],
    ) -> None:
        if self._log_dir is None:
            return
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self._log_dir / f"iter_{iteration:02d}_v2_structural_critic.json"
            log_path.write_text(
                json.dumps(
                    {"prompt": prompt, "raw": raw, "parsed": parsed},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("[V2Critic] 로그 기록 실패: %s", exc)


# ---------------------------------------------------------------------------
# V2SequentialFlowRunner
# ---------------------------------------------------------------------------

class V2SequentialFlowRunner(SequentialFlowRunner):
    """V2 LLM-direct mutation flow runner.

    monkey-patch 전략 (collaborative.py와 동일):
        1. PlannerAgent → _PatchedPlannerAgent
           (LLMDirectMutationPlanner 인스턴스를 반환하는 팩토리)
        2. generate_guided_mutant → _v2_generate
           (proposed_sequences pop 우선, fallback은 원본 guided mutant)

    finally 블록에서 반드시 원복하여 다른 실험에 영향 없음.
    """

    def __init__(self, config: ExperimentConfig) -> None:
        super().__init__(config)
        self._apply_blosum62: bool = config.extra.get("v2_apply_blosum62", True)
        self._max_llm_retries: int = config.extra.get("v2_max_llm_retries", 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """V2 flow 실행. 실패 시 V1 sequential로 fallback."""
        try:
            return self._run_v2()
        except Exception as exc:
            logger.error(
                "[V2] 실행 실패 — sequential 폴백: %s", exc, exc_info=True
            )
            return super().run()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_v2(self) -> Dict[str, Any]:
        """LLM-direct mutation flow를 monkey-patch로 실행."""
        sys.path.insert(0, str(REPO_ROOT))

        from pyrosetta_flow.schema import FlowConfig
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow
        from AG_src.agents.planner import PlannerAgent
        from AG_src.agents.critic import ScientistCriticAgent
        from AG_src.llm import create_provider
        import pyrosetta_flow.runner as _runner_mod
        from pyrosetta_flow.adapter import (
            generate_guided_mutant as _orig_ggm,
        )

        flow_config = self._build_flow_config()
        self._write_config_snapshot(flow_config)

        llm = self._build_llm_provider(create_provider)

        orig_planner_cls = _runner_mod.__dict__.get("PlannerAgent", PlannerAgent)
        _v2_ggm = _make_v2_generate_guided_mutant(_orig_ggm)

        this = self

        class _PatchedPlannerAgent:
            """LLMDirectMutationPlanner를 반환하는 팩토리 클래스."""

            def __new__(cls, *args: Any, **kwargs: Any) -> "LLMDirectMutationPlanner":  # type: ignore[override]
                inner = orig_planner_cls(*args, **kwargs)
                return LLMDirectMutationPlanner(
                    inner_planner=inner,
                    llm=llm,
                    n_candidates=flow_config.n_candidates,
                    original_sequence=flow_config.original_sequence,
                    max_llm_retries=this._max_llm_retries,
                    apply_blosum62=this._apply_blosum62,
                    log_dir=this._agent_log_dir,
                    experiment_id=this.config.experiment_id,
                )

        start = time.time()
        try:
            # monkey-patch: PlannerAgent + generate_guided_mutant
            _runner_mod.PlannerAgent = _PatchedPlannerAgent  # type: ignore[attr-defined]
            _runner_mod.generate_guided_mutant = _v2_ggm  # type: ignore[attr-defined]
            logger.info(
                "[V2] monkey-patch 적용: PlannerAgent→LLMDirectMutationPlanner, "
                "generate_guided_mutant→proposed_sequences pop"
            )

            result = run_pyrosetta_agentic_mutdock_flow(flow_config)
            elapsed = time.time() - start
            self._write_status("done", elapsed)
            self._compute_ses()
            return {"success": True, "result": result, "elapsed_s": elapsed}

        except Exception as exc:
            elapsed = time.time() - start
            self._write_status("failed", elapsed, str(exc))
            logger.error(
                "[V2] experiment %s failed: %s",
                self.config.experiment_id, exc,
            )
            return {"success": False, "error": str(exc), "elapsed_s": elapsed}

        finally:
            # 반드시 원복
            _runner_mod.PlannerAgent = orig_planner_cls  # type: ignore[attr-defined]
            _runner_mod.generate_guided_mutant = _orig_ggm  # type: ignore[attr-defined]
            logger.info("[V2] monkey-patch 원복 완료")

    def _build_flow_config(self) -> Any:
        """V2용 FlowConfig 생성."""
        sys.path.insert(0, str(REPO_ROOT))
        from pyrosetta_flow.schema import FlowConfig

        return FlowConfig(
            template_pdb=str(REPO_ROOT / "data" / "fold_test1_model_0.pdb"),
            output_dir=str(self._output_dir / "pyrosetta_flow"),
            max_iterations=self.config.max_iterations,
            n_candidates=self.config.n_candidates,
            top_k=self.config.top_k,
            original_sequence="AGCKNFFWKTFTSC",
            peptide_chain=1,
            conda_env="bio-tools",
            seed_base=self.config.seed,
            llm_model_override=self.config.model_hf_id,
            llm_provider="vllm",
            llm_base_url=f"http://localhost:{self.config.extra.get('vllm_port', 8002)}",
            planner_mode="pyrosetta_only",
            validation_n_trials=1,
            gate_mode=self.config.extra.get("gate_mode", "static"),
        )

    def _build_llm_provider(self, create_provider: Any) -> Any:
        """vLLM LLM provider 생성."""
        llm_cfg = {
            "llm": {
                "provider": "vllm",
                "model": self.config.model_hf_id or "qwen3:8b",
                "base_url": f"http://localhost:{self.config.extra.get('vllm_port', 8002)}",
            }
        }
        return create_provider(llm_cfg, model_override=self.config.model_hf_id or None)
