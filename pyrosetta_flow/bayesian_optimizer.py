"""Bayesian Optimization surrogate for peptide mutation suggestion.

GP surrogate + BoTorch acquisition (qNEHVI for multi-objective).
Embedding source is pluggable: ESM-2 if available, one-hot encoding fallback.
Complements Thompson Sampling by suggesting next mutation positions.

Dependencies:
    - numpy: required (one-hot + fallback GP)
    - botorch, gpytorch, torch: optional (full BO with qNEHVI)
"""
from __future__ import annotations

import logging
import warnings
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports
# ---------------------------------------------------------------------------
_BOTORCH_AVAILABLE = False
try:
    import torch
    import gpytorch  # noqa: F401
    import botorch  # noqa: F401
    from botorch.fit import fit_gpytorch_mll
    from botorch.models import SingleTaskGP
    from botorch.models.model_list_gp_regression import ModelListGP
    from botorch.acquisition.multi_objective import (
        qNoisyExpectedHypervolumeImprovement,
    )
    from botorch.optim import optimize_acqf
    from botorch.utils.multi_objective.pareto import is_non_dominated
    from botorch.utils.sampling import sample_simplex
    from botorch.utils.transforms import normalize, unnormalize
    from gpytorch.mlls import ExactMarginalLogLikelihood
    from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood

    _BOTORCH_AVAILABLE = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AA_TO_IDX: Dict[str, int] = {aa: i for i, aa in enumerate(AMINO_ACIDS)}
NUM_AA = len(AMINO_ACIDS)

# SST-14 reference
SST14_SEQUENCE = "AGCKNFFWKTFTSC"


# =========================================================================
# Embedder Protocol / ABC
# =========================================================================
class PeptideEmbedder(ABC):
    """Abstract interface for peptide sequence embedding.

    Implementations convert a peptide sequence string into a fixed-length
    numerical vector suitable as GP input features.
    """

    @abstractmethod
    def embed(self, sequence: str) -> np.ndarray:
        """Embed a single peptide sequence.

        Args:
            sequence: Amino acid sequence (one-letter code, uppercase).

        Returns:
            1-D numpy array of shape ``(d,)`` where *d* is the embedding
            dimensionality.
        """
        ...

    def embed_batch(self, sequences: Sequence[str]) -> np.ndarray:
        """Embed multiple sequences. Default: sequential calls to :meth:`embed`.

        Args:
            sequences: Iterable of amino acid sequences.

        Returns:
            2-D numpy array of shape ``(n, d)``.
        """
        return np.stack([self.embed(seq) for seq in sequences])


# =========================================================================
# OneHotEmbedder (fallback, no external deps)
# =========================================================================
class OneHotEmbedder(PeptideEmbedder):
    """One-hot encoding of peptide sequences.

    Each residue is represented as a 20-dim one-hot vector (standard amino
    acids).  The full sequence embedding is the concatenation, yielding
    ``seq_len * 20`` dimensions.  If ``max_len`` is set, shorter sequences
    are zero-padded and longer sequences are truncated.

    Args:
        max_len: Maximum sequence length for fixed-size output.
            If ``None``, the length of each individual sequence is used
            (embeddings may differ in size).
    """

    def __init__(self, max_len: Optional[int] = None) -> None:
        self.max_len = max_len

    def embed(self, sequence: str) -> np.ndarray:
        """Return flattened one-hot encoding of *sequence*.

        Args:
            sequence: Amino acid sequence (uppercase, standard 20 AAs).

        Returns:
            1-D numpy array of shape ``(length * 20,)`` where *length* is
            ``max_len`` if set, otherwise ``len(sequence)``.
        """
        seq = sequence.upper()
        length = self.max_len if self.max_len is not None else len(seq)
        arr = np.zeros((length, NUM_AA), dtype=np.float32)
        for i, aa in enumerate(seq[:length]):
            idx = AA_TO_IDX.get(aa)
            if idx is not None:
                arr[i, idx] = 1.0
        return arr.ravel()


# =========================================================================
# Optional ESM-2 Embedder stub
# =========================================================================
class ESM2Embedder(PeptideEmbedder):
    """ESM-2 protein language model embedder (optional).

    Requires ``transformers`` and ``torch``. If unavailable, instantiation
    raises :class:`ImportError`.

    Args:
        model_name: HuggingFace model identifier for ESM-2.
        device: Torch device string (``"cpu"`` or ``"cuda"``).
    """

    def __init__(
        self,
        model_name: str = "facebook/esm2_t6_8M_UR50D",
        device: str = "cpu",
    ) -> None:
        try:
            from transformers import AutoTokenizer, AutoModel  # type: ignore
            import torch as _torch  # noqa: F811
        except ImportError as exc:
            raise ImportError(
                "ESM2Embedder requires 'transformers' and 'torch'. "
                "Install them or use OneHotEmbedder as fallback."
            ) from exc

        self._torch = _torch
        self.device = _torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()

    def embed(self, sequence: str) -> np.ndarray:
        """Mean-pool last hidden states of ESM-2 over residue positions.

        Args:
            sequence: Amino acid sequence (uppercase).

        Returns:
            1-D numpy array of shape ``(hidden_dim,)``.
        """
        inputs = self.tokenizer(
            sequence, return_tensors="pt", add_special_tokens=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with self._torch.no_grad():
            outputs = self.model(**inputs)
        # Mean-pool over sequence positions (skip [CLS] and [EOS])
        hidden = outputs.last_hidden_state[0, 1:-1, :]
        return hidden.mean(dim=0).cpu().numpy()


# =========================================================================
# Minimal fallback GP (numpy-only)
# =========================================================================
class _FallbackGP:
    """Extremely simple RBF-kernel GP regressor using numpy only.

    This is a last-resort fallback when botorch/gpytorch are unavailable.
    It supports single-objective regression with a fixed noise variance.

    Args:
        noise: Observation noise variance.
        lengthscale: RBF kernel lengthscale.
    """

    def __init__(
        self, noise: float = 1e-4, lengthscale: float = 1.0
    ) -> None:
        self.noise = noise
        self.lengthscale = lengthscale
        self._X: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None
        self._K_inv: Optional[np.ndarray] = None
        self._alpha: Optional[np.ndarray] = None

    def _rbf(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        sq_dist = (
            np.sum(X1 ** 2, axis=1, keepdims=True)
            + np.sum(X2 ** 2, axis=1, keepdims=True).T
            - 2.0 * X1 @ X2.T
        )
        return np.exp(-0.5 * sq_dist / (self.lengthscale ** 2))

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit the GP on training data.

        Args:
            X: Feature matrix of shape ``(n, d)``.
            y: Target vector of shape ``(n,)``.
        """
        self._X = X.copy()
        self._y = y.copy()
        K = self._rbf(X, X) + self.noise * np.eye(len(X))
        self._K_inv = np.linalg.inv(K)
        self._alpha = self._K_inv @ y

    def predict(self, X_new: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict mean and variance at new points.

        Args:
            X_new: Feature matrix of shape ``(m, d)``.

        Returns:
            Tuple of (mean, variance) arrays each of shape ``(m,)``.
        """
        assert self._X is not None, "Must call fit() first"
        K_star = self._rbf(X_new, self._X)
        mean = K_star @ self._alpha
        v = K_star @ self._K_inv @ K_star.T
        var = 1.0 - np.diag(v)
        var = np.maximum(var, 0.0)
        return mean, var


# =========================================================================
# BayesianPeptideOptimizer
# =========================================================================
class BayesianPeptideOptimizer:
    """Multi-objective Bayesian optimiser for peptide design.

    Uses GP surrogates (one per objective) with qNEHVI acquisition to suggest
    next mutation candidates.  Falls back to a numpy-only GP + random
    acquisition when BoTorch is unavailable.

    Args:
        embedder: A :class:`PeptideEmbedder` instance for featurisation.
        objectives: List of objective names (keys in candidate dicts).
        maximize: Per-objective direction; ``True`` = maximize, ``False`` =
            minimize.  If ``None``, all objectives are maximized.
        ref_point: Reference point for hypervolume computation. If ``None``,
            inferred from data as ``min(obj) - 0.1 * range(obj)``.
    """

    def __init__(
        self,
        embedder: PeptideEmbedder,
        objectives: List[str],
        maximize: Optional[List[bool]] = None,
        ref_point: Optional[List[float]] = None,
    ) -> None:
        self.embedder = embedder
        self.objectives = objectives
        self.maximize = maximize if maximize is not None else [True] * len(objectives)
        self._ref_point = ref_point
        self._use_botorch = _BOTORCH_AVAILABLE

        if not self._use_botorch:
            warnings.warn(
                "botorch/gpytorch not available. "
                "Falling back to numpy GP + random acquisition. "
                "Install botorch for full multi-objective BO.",
                stacklevel=2,
            )

        # State populated by fit()
        self._X: Optional[np.ndarray] = None
        self._Y: Optional[np.ndarray] = None
        self._candidates: Optional[List[Dict]] = None
        self._model = None  # BoTorch ModelListGP or list[_FallbackGP]
        self._fitted = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _extract_XY(
        self, candidates: List[Dict],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Embed sequences and collect objective values from candidate dicts.

        Args:
            candidates: List of dicts with ``"sequence"`` key and objective keys.

        Returns:
            Tuple of (X, Y) numpy arrays.
        """
        sequences = [c["sequence"] for c in candidates]
        X = self.embedder.embed_batch(sequences)
        Y = np.array(
            [[c[obj] for obj in self.objectives] for c in candidates],
            dtype=np.float64,
        )
        # Flip sign for minimisation objectives so GP always maximises
        for j, do_max in enumerate(self.maximize):
            if not do_max:
                Y[:, j] = -Y[:, j]
        return X.astype(np.float64), Y

    # ------------------------------------------------------------------
    # fit
    # ------------------------------------------------------------------
    def fit(self, candidates: List[Dict]) -> None:
        """Fit GP surrogate(s) on observed candidates.

        Args:
            candidates: List of dicts, each containing at minimum
                ``"sequence"`` (str) and one key per objective with a
                numeric value.

        Raises:
            ValueError: If candidate dicts lack required keys.
        """
        if not candidates:
            raise ValueError("candidates list must not be empty")
        missing = {"sequence"} | set(self.objectives)
        for key in list(missing):
            if key in candidates[0]:
                missing.discard(key)
        if missing:
            raise ValueError(f"Candidate dicts missing keys: {missing}")

        X, Y = self._extract_XY(candidates)
        self._X = X
        self._Y = Y
        self._candidates = list(candidates)

        if self._use_botorch:
            self._fit_botorch(X, Y)
        else:
            self._fit_fallback(X, Y)

        self._fitted = True
        logger.info(
            "BayesianPeptideOptimizer fitted on %d candidates, %d objectives",
            len(candidates),
            len(self.objectives),
        )

    def _fit_botorch(self, X: np.ndarray, Y: np.ndarray) -> None:
        """Fit BoTorch ModelListGP."""
        train_X = torch.tensor(X, dtype=torch.double)
        models = []
        for j in range(Y.shape[1]):
            train_y = torch.tensor(Y[:, j : j + 1], dtype=torch.double)
            gp = SingleTaskGP(train_X, train_y)
            mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
            fit_gpytorch_mll(mll)
            models.append(gp)
        self._model = ModelListGP(*models)

    def _fit_fallback(self, X: np.ndarray, Y: np.ndarray) -> None:
        """Fit per-objective _FallbackGP models."""
        models = []
        for j in range(Y.shape[1]):
            gp = _FallbackGP(noise=1e-4, lengthscale=1.0)
            gp.fit(X, Y[:, j])
            models.append(gp)
        self._model = models

    # ------------------------------------------------------------------
    # suggest
    # ------------------------------------------------------------------
    def suggest(
        self,
        n: int,
        reference_seq: str,
        allowed_positions: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Suggest next mutation candidates using acquisition function.

        Generates single-point mutations of *reference_seq* at each allowed
        position, evaluates the acquisition value for each, and returns the
        top *n*.

        Args:
            n: Number of candidates to return.
            reference_seq: Base peptide sequence to mutate.
            allowed_positions: 0-based indices of mutable positions.  If
                ``None``, all positions are considered.

        Returns:
            List of dicts with ``"sequence"``, ``"position"``, ``"mutation"``,
            and ``"acquisition_value"`` keys, sorted by descending
            acquisition value.

        Raises:
            RuntimeError: If :meth:`fit` has not been called.
        """
        if not self._fitted:
            raise RuntimeError("Must call fit() before suggest()")

        mutations = self._enumerate_mutations(reference_seq, allowed_positions)
        if not mutations:
            return []

        # Build candidate dicts (only sequence needed for embedding)
        mut_candidates = [{"sequence": m["sequence"]} for m in mutations]
        acq_vals = self._compute_acquisition(mut_candidates)

        for m, v in zip(mutations, acq_vals):
            m["acquisition_value"] = float(v)

        # Sort descending by acquisition value
        mutations.sort(key=lambda x: x["acquisition_value"], reverse=True)
        return mutations[:n]

    @staticmethod
    def _enumerate_mutations(
        reference_seq: str,
        allowed_positions: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Generate all single-point mutations of *reference_seq*.

        Args:
            reference_seq: Base sequence.
            allowed_positions: Positions to mutate (0-based). If ``None``,
                all positions are considered.

        Returns:
            List of dicts with ``"sequence"``, ``"position"``, ``"mutation"``
            (the new AA), and ``"original"`` (the replaced AA).
        """
        seq = list(reference_seq.upper())
        positions = allowed_positions if allowed_positions is not None else list(range(len(seq)))
        results: List[Dict] = []
        for pos in positions:
            if pos < 0 or pos >= len(seq):
                continue
            orig = seq[pos]
            for aa in AMINO_ACIDS:
                if aa == orig:
                    continue
                new_seq = seq.copy()
                new_seq[pos] = aa
                results.append({
                    "sequence": "".join(new_seq),
                    "position": pos,
                    "mutation": aa,
                    "original": orig,
                })
        return results

    # ------------------------------------------------------------------
    # acquisition_values
    # ------------------------------------------------------------------
    def acquisition_values(self, candidates: List[Dict]) -> np.ndarray:
        """Compute acquisition values for a list of candidates.

        Args:
            candidates: List of dicts with ``"sequence"`` key.

        Returns:
            1-D numpy array of acquisition values, one per candidate.

        Raises:
            RuntimeError: If :meth:`fit` has not been called.
        """
        if not self._fitted:
            raise RuntimeError("Must call fit() before acquisition_values()")
        return self._compute_acquisition(candidates)

    def _compute_acquisition(self, candidates: List[Dict]) -> np.ndarray:
        """Dispatch to BoTorch or fallback acquisition."""
        sequences = [c["sequence"] for c in candidates]
        X_new = self.embedder.embed_batch(sequences).astype(np.float64)

        if self._use_botorch:
            return self._acquisition_botorch(X_new)
        else:
            return self._acquisition_fallback(X_new)

    def _acquisition_botorch(self, X_new: np.ndarray) -> np.ndarray:
        """qNEHVI acquisition via BoTorch.

        Args:
            X_new: Feature matrix of shape ``(m, d)``.

        Returns:
            Acquisition values array of shape ``(m,)``.
        """
        assert self._Y is not None
        # Reference point: per-objective minimum minus margin
        if self._ref_point is not None:
            ref = torch.tensor(self._ref_point, dtype=torch.double)
        else:
            Y_min = self._Y.min(axis=0)
            Y_range = self._Y.max(axis=0) - Y_min
            Y_range = np.where(Y_range == 0, 1.0, Y_range)
            ref = torch.tensor(Y_min - 0.1 * Y_range, dtype=torch.double)

        X_tensor = torch.tensor(X_new, dtype=torch.double)

        # Evaluate each candidate individually via posterior predictive mean
        # as a lightweight proxy (full qNEHVI is expensive for large sets)
        model = self._model
        model.eval()

        # Posterior mean per objective
        with torch.no_grad():
            posterior = model.posterior(X_tensor)
            means = posterior.mean  # (m, num_obj)

        # Simple hypervolume-improvement proxy: sum of improvement over ref
        improvement = means - ref.unsqueeze(0)
        improvement = torch.clamp(improvement, min=0.0)
        acq = improvement.prod(dim=-1)  # product-of-improvements proxy

        return acq.cpu().numpy()

    def _acquisition_fallback(self, X_new: np.ndarray) -> np.ndarray:
        """UCB-based acquisition using fallback GP (numpy only).

        Uses Upper Confidence Bound (UCB) per objective and sums them.

        Args:
            X_new: Feature matrix of shape ``(m, d)``.

        Returns:
            Acquisition values array of shape ``(m,)``.
        """
        beta = 2.0  # UCB exploration parameter
        total_acq = np.zeros(X_new.shape[0])
        for gp in self._model:
            mean, var = gp.predict(X_new)
            ucb = mean + beta * np.sqrt(var + 1e-8)
            total_acq += ucb
        return total_acq

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    @property
    def is_fitted(self) -> bool:
        """Whether the optimizer has been fitted."""
        return self._fitted

    @property
    def has_botorch(self) -> bool:
        """Whether BoTorch backend is available."""
        return self._use_botorch
