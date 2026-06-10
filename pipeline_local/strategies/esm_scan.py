"""ESM-Scan zero-shot mutation generation strategy."""

from __future__ import annotations

import importlib.util
import itertools
import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry
from pipeline_local.strategies.blosum import (
    AMINO_ACIDS,
    DEFAULT_REFERENCE_PEPTIDE_SEQUENCE,
    get_blosum_score,
    hydrophobicity_check,
    validate_constraints,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ESMSubstitution:
    pos: int
    original_aa: str
    sub_aa: str
    esm_delta: float

    @property
    def mutation_label(self) -> str:
        return f"{self.original_aa}{self.pos}{self.sub_aa}"


def _quantile_threshold(values: List[float], quantile: float) -> float:
    if not values:
        return math.inf
    q = min(1.0, max(0.0, quantile))
    ordered = sorted(values)
    idx = math.ceil(q * (len(ordered) - 1))
    return ordered[idx]


class ESMScanStrategy:
    """Generate variants from ESM masked-marginal log-probability deltas."""

    name = "esm_scan"

    def validate_env(self) -> tuple[bool, str | None]:
        has_fair_esm = importlib.util.find_spec("esm") is not None
        has_torch = importlib.util.find_spec("torch") is not None
        has_transformers = importlib.util.find_spec("transformers") is not None

        if has_torch and (has_fair_esm or has_transformers):
            return True, None

        missing = []
        if not has_torch:
            missing.append("torch")
        if not has_fair_esm and not has_transformers:
            missing.append("fair-esm or transformers")
        return False, f"Missing ESM dependencies: {', '.join(missing)}"

    def generate(self, config: dict) -> Step03bOutput:
        ab_cfg = config.get("approach_b", config)
        ref_cfg = config.get("reference_peptide", {})
        opts = ab_cfg.get("esm_scan_opts", {})

        seed = ab_cfg.get(
            "seed_sequence",
            ref_cfg.get("sequence", DEFAULT_REFERENCE_PEPTIDE_SEQUENCE),
        )
        fixed_raw = ab_cfg.get(
            "fixed_positions",
            {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"},
        )
        fixed_positions = {int(k): str(v) for k, v in fixed_raw.items()}
        max_variants = int(ab_cfg.get("max_variants", 200))
        max_mutations = int(
            opts.get(
                "max_mutations_per_variant",
                ab_cfg.get("max_mutations_per_variant", 3),
            )
        )
        score_quantile = float(opts.get("score_quantile", 0.7))
        max_hydro_delta = float(ab_cfg.get("hydrophobicity_max_delta", 2.0))

        candidates = self._candidate_substitutions(
            seed=seed,
            fixed_positions=fixed_positions,
            opts=opts,
            score_quantile=score_quantile,
        )
        variants = self._build_variants(
            seed=seed,
            fixed_positions=fixed_positions,
            candidates=candidates,
            max_variants=max_variants,
            max_mutations=max_mutations,
            max_hydro_delta=max_hydro_delta,
        )

        logger.info(
            "[Step03b] ESM-Scan generated %d variants from seed %s",
            len(variants),
            seed,
        )
        return Step03bOutput(
            variants=variants,
            seed_sequence=seed,
            fixed_positions=fixed_positions,
            total_generated=len(variants),
            strategy="approach_b",
        )

    @staticmethod
    def _resolve_torch_device(torch_module: Any, requested_device: str) -> str:
        if requested_device.startswith("cuda") and not torch_module.cuda.is_available():
            logger.warning(
                "[Step03b] CUDA device %s requested for ESM-Scan but CUDA is unavailable; using CPU.",
                requested_device,
            )
            return "cpu"
        return requested_device

    def _candidate_substitutions(
        self,
        seed: str,
        fixed_positions: Dict[int, str],
        opts: Dict[str, Any],
        score_quantile: float,
    ) -> List[ESMSubstitution]:
        mutable_positions = [
            pos for pos in range(1, len(seed) + 1)
            if pos not in fixed_positions
        ]
        scored = self._score_substitution_deltas(seed, mutable_positions, opts)
        threshold = _quantile_threshold(
            [sub.esm_delta for sub in scored],
            score_quantile,
        )
        return sorted(
            [sub for sub in scored if sub.esm_delta >= threshold],
            key=lambda sub: (-sub.esm_delta, sub.pos, sub.sub_aa),
        )

    def _score_substitution_deltas(
        self,
        seed: str,
        mutable_positions: List[int],
        opts: Dict[str, Any],
    ) -> List[ESMSubstitution]:
        if importlib.util.find_spec("esm") is not None:
            return self._score_with_fair_esm(seed, mutable_positions, opts)
        if importlib.util.find_spec("transformers") is not None:
            return self._score_with_transformers(seed, mutable_positions, opts)
        raise RuntimeError(
            "ESM dependencies are unavailable. Install fair-esm or transformers."
        )

    def _score_with_fair_esm(
        self,
        seed: str,
        mutable_positions: List[int],
        opts: Dict[str, Any],
    ) -> List[ESMSubstitution]:
        import torch
        import esm

        model_name = str(opts.get("model", "esm2_t33_650M_UR50D"))
        device = self._resolve_torch_device(torch, str(opts.get("device", "cpu")))
        loader = getattr(esm.pretrained, model_name)
        model, alphabet = loader()
        model.eval().to(device)
        batch_converter = alphabet.get_batch_converter()

        _, _, base_tokens = batch_converter([("seed", seed)])
        base_tokens = base_tokens.to(device)
        aa_to_idx = {aa: alphabet.get_idx(aa) for aa in AMINO_ACIDS}
        substitutions: List[ESMSubstitution] = []

        with torch.no_grad():
            for pos in mutable_positions:
                masked_tokens = base_tokens.clone()
                masked_tokens[0, pos] = alphabet.mask_idx
                logits = model(masked_tokens)["logits"][0, pos]
                log_probs = torch.log_softmax(logits, dim=-1)
                original_aa = seed[pos - 1]
                original_log_prob = float(log_probs[aa_to_idx[original_aa]].item())
                for sub_aa in AMINO_ACIDS:
                    if sub_aa == original_aa:
                        continue
                    substitutions.append(ESMSubstitution(
                        pos=pos,
                        original_aa=original_aa,
                        sub_aa=sub_aa,
                        esm_delta=float(log_probs[aa_to_idx[sub_aa]].item()) - original_log_prob,
                    ))
        return substitutions

    def _score_with_transformers(
        self,
        seed: str,
        mutable_positions: List[int],
        opts: Dict[str, Any],
    ) -> List[ESMSubstitution]:
        import torch
        from transformers import AutoModelForMaskedLM, AutoTokenizer

        model_name = str(opts.get("model", "facebook/esm2_t33_650M_UR50D"))
        if not model_name.startswith("facebook/") and "/" not in model_name:
            model_name = f"facebook/{model_name}"
        device = self._resolve_torch_device(torch, str(opts.get("device", "cpu")))

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForMaskedLM.from_pretrained(model_name)
        model.eval().to(device)
        aa_to_idx = {
            aa: tokenizer.convert_tokens_to_ids(aa)
            for aa in AMINO_ACIDS
        }
        substitutions: List[ESMSubstitution] = []

        with torch.no_grad():
            for pos in mutable_positions:
                tokens = list(seed)
                tokens[pos - 1] = tokenizer.mask_token
                encoded = tokenizer(" ".join(tokens), return_tensors="pt").to(device)
                mask_positions = (encoded["input_ids"][0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0]
                if len(mask_positions) != 1:
                    raise RuntimeError("Unable to locate ESM mask token in encoded sequence.")
                mask_idx = int(mask_positions[0].item())
                logits = model(**encoded).logits[0, mask_idx]
                log_probs = torch.log_softmax(logits, dim=-1)
                original_aa = seed[pos - 1]
                original_log_prob = float(log_probs[aa_to_idx[original_aa]].item())
                for sub_aa in AMINO_ACIDS:
                    if sub_aa == original_aa:
                        continue
                    substitutions.append(ESMSubstitution(
                        pos=pos,
                        original_aa=original_aa,
                        sub_aa=sub_aa,
                        esm_delta=float(log_probs[aa_to_idx[sub_aa]].item()) - original_log_prob,
                    ))
        return substitutions

    def _build_variants(
        self,
        seed: str,
        fixed_positions: Dict[int, str],
        candidates: List[ESMSubstitution],
        max_variants: int,
        max_mutations: int,
        max_hydro_delta: float,
    ) -> List[VariantEntry]:
        by_pos: Dict[int, List[ESMSubstitution]] = {}
        for sub in candidates:
            by_pos.setdefault(sub.pos, []).append(sub)

        ranked_variants: List[tuple[float, VariantEntry]] = []
        seen_sequences: set[str] = set()
        max_mutations = max(1, max_mutations)

        for n_mut in range(1, max_mutations + 1):
            for pos_combo in itertools.combinations(sorted(by_pos), n_mut):
                for sub_combo in itertools.product(*(by_pos[pos] for pos in pos_combo)):
                    mutated = list(seed)
                    for sub in sub_combo:
                        mutated[sub.pos - 1] = sub.sub_aa
                    mutated_seq = "".join(mutated)

                    if mutated_seq in seen_sequences:
                        continue
                    seen_sequences.add(mutated_seq)
                    if not validate_constraints(mutated_seq, fixed_positions):
                        continue
                    if not hydrophobicity_check(mutated_seq, seed, max_hydro_delta):
                        continue

                    total_delta = sum(sub.esm_delta for sub in sub_combo)
                    total_blosum = sum(
                        get_blosum_score(sub.original_aa, sub.sub_aa)
                        for sub in sub_combo
                    )
                    ranked_variants.append((total_delta, VariantEntry(
                        variant_id="",
                        sequence=mutated_seq,
                        parent_sequence=seed,
                        mutations=[sub.mutation_label for sub in sub_combo],
                        n_mutations=n_mut,
                        blosum_total_score=total_blosum,
                        source="esm_scan",
                    )))

        ranked_variants.sort(
            key=lambda item: (
                -item[0],
                item[1].n_mutations,
                item[1].mutations,
            )
        )
        variants = [entry for _, entry in ranked_variants[:max_variants]]
        for idx, variant in enumerate(variants, start=1):
            variant.variant_id = f"var_{idx:03d}"
        return variants
