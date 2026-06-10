"""학습된 feature 기반 half-life 모델 추론 (2026-06-09 C).

train_halflife_features.py 가 저장한 halflife_gbr.joblib 를 로드해 서열(+선택적 메타)로
혈중 t½(hours)를 예측한다. CV Spearman 0.78 (PEPlife2 human, in-domain).

honest: PEPlife2(serum/plasma AMP·연구펩타이드) 도메인에서 검증. 승인약물·소마토스타틴
유사체 등 OOD 에선 절대값 신뢰도 낮음(SST-14 과대예측). 상대 순위(in-domain) 용도 권장.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import joblib

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from train_halflife_features import featurize  # noqa: E402

_MODEL_PATH = _HERE.parent / "data" / "halflife_v2" / "halflife_gbr.joblib"
_BUNDLE = None


def _load():
    global _BUNDLE
    if _BUNDLE is None:
        _BUNDLE = joblib.load(_MODEL_PATH)
    return _BUNDLE


def predict_halflife_hours(sequence: str, rec: Optional[Dict] = None) -> Optional[float]:
    """서열(+메타 dict: chiral/lin_cyc/chem_mod/nter/cter)로 t½(hours) 예측. 실패 시 None."""
    try:
        b = _load()
        f = featurize(sequence, rec or {})
        if f is None:
            return None
        x = np.array([[f[c] for c in b["feat_cols"]]], float)
        return float(np.expm1(b["model"].predict(x)[0]))
    except Exception:
        return None


def predict_batch(sequences: List[str]) -> Dict[str, Optional[float]]:
    return {s: predict_halflife_hours(s) for s in sequences}


if __name__ == "__main__":
    seqs = sys.argv[1:] or ["AGCKNFFWKTFTSC", "AGCKWFFWKTFTSC", "YGCKNFFWKTFTST"]
    for s, v in predict_batch(seqs).items():
        print(f"{s}: {v:.3f}h" if v is not None else f"{s}: None")
