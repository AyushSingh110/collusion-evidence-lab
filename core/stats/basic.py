"""Small statistics helpers for RQ0.1 (report 01 §5.5, §7).

NA convention (project-wide for core.evidence / core.stats): a missing or undefined value is
Python ``None``, never NaN and never a fake 0 or 1.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence


def percentile_rank(value: Optional[float], sample: Iterable[Optional[float]]) -> Optional[float]:
    """Mid-rank percentile (0-100) of ``value`` within ``sample``.

    percentile = 100 * (#{s < value} + 0.5 * #{s == value}) / n, NA entries of ``sample`` dropped.
    Returns None if ``value`` is None or the sample has no non-NA entries.
    """
    if value is None:
        return None
    vals = [s for s in sample if s is not None]
    if not vals:
        return None
    below = sum(s < value for s in vals)
    ties = sum(s == value for s in vals)
    return 100.0 * (below + 0.5 * ties) / len(vals)


def count(items: Iterable, pred: Optional[Callable] = None) -> int:
    """Number of items that are truthy (or satisfy ``pred``). None counts as False."""
    if pred is None:
        return sum(1 for x in items if x)
    return sum(1 for x in items if pred(x))


def mean_or_none(values: Sequence[Optional[float]]) -> Optional[float]:
    """Mean of the non-None values; None if there are none."""
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None
