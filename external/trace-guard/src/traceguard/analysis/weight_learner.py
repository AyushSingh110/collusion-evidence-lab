"""Adaptive dimension weight learning from labeled evaluation data.

Offline tool that computes per-dimension AUC from labeled data and produces
normalized weights. Never called during active evaluation runs.
"""

import logging
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from traceguard.dimensions import DEFAULT_DIMENSIONS

logger = logging.getLogger(__name__)

DEFAULT_DIMENSION_NAMES = [d.name for d in DEFAULT_DIMENSIONS]

DEFAULT_WEIGHTS: dict[str, float] = {d.name: d.weight for d in DEFAULT_DIMENSIONS}


def learn_weights(
    df: pd.DataFrame,
    dimension_names: list[str] | None = None,
    min_samples: int = 50,
) -> dict[str, float]:
    """Compute AUC-based dimension weights from labeled evaluation data.

    Returns dict mapping dimension name -> weight (summing to 1.0).
    Falls back to default weights with warning if < min_samples.

    Parameters
    ----------
    df : pd.DataFrame
        Must have a ``label`` column (0 for honest, 1 for attack) and one
        column per dimension containing normalized scores in [0, 1].
    dimension_names : list[str] | None
        Dimension column names to use. Defaults to the 5 standard dimensions.
    min_samples : int
        Minimum number of rows required. Falls back to defaults if fewer.
    """
    if dimension_names is None:
        dimension_names = DEFAULT_DIMENSION_NAMES

    # --- Fallback: insufficient data ---
    if len(df) < min_samples:
        warnings.warn(
            f"Insufficient data ({len(df)} samples < {min_samples}). "
            "Falling back to default dimension weights.",
            stacklevel=2,
        )
        return dict(DEFAULT_WEIGHTS)

    labels = df["label"].values
    auc_values: dict[str, float] = {}

    for dim in dimension_names:
        try:
            auc = roc_auc_score(labels, df[dim].values)
        except ValueError:
            # All-same-class data: sklearn raises ValueError.
            # Assign AUC = 0.5 (random classifier) as fallback.
            auc = 0.5

        # Some sklearn versions return nan instead of raising for single-class data
        if np.isnan(auc):
            auc = 0.5

        auc_values[dim] = auc

    # --- Normalize AUC values to sum to 1.0 ---
    total_auc = sum(auc_values.values())

    if total_auc == 0.0:
        # Guard: all AUCs are 0 (shouldn't happen with 0.5 fallback, but be safe)
        n = len(dimension_names)
        return {dim: 1.0 / n for dim in dimension_names}

    weights = {dim: auc / total_auc for dim, auc in auc_values.items()}

    return weights
