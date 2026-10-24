"""Statistics for RQ1-RQ9 and Study 2.3 (report 00 §10). Deterministic for a given seed.

Conventions:
* NA is None (never NaN, never a fake 0 or 1): AUROC with an empty class, a rate with a zero denominator,
  a correlation with a constant input.
* Scores must not be None here; callers drop failed monitor outputs first and report how many they dropped.
* A game is flagged positive when score >= threshold.
"""
from __future__ import annotations

import math
from typing import Callable, Hashable, Optional, Sequence

import numpy as np

DEFAULT_SEED = 20261023
DEFAULT_B = 2000


def _check(scores: Sequence[float], labels: Sequence[int]) -> None:
    if len(scores) != len(labels):
        raise ValueError("scores and labels differ in length")
    if any(s is None for s in scores):
        raise ValueError("scores contain None; drop failed outputs first (and report them)")
    if any(y not in (0, 1) for y in labels):
        raise ValueError("labels must be 0/1")


# --------------------------------------------------------------------------- AUROC

def auroc(scores: Sequence[float], labels: Sequence[int]) -> Optional[float]:
    """P(score_pos > score_neg) + 0.5 P(equal) (Mann-Whitney). None if a class is empty."""
    _check(scores, labels)
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    # rank-based, average ranks for ties: U = R_pos - n_pos (n_pos + 1) / 2
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    r_pos = sum(r for r, y in zip(ranks, labels) if y == 1)
    u = r_pos - len(pos) * (len(pos) + 1) / 2
    return u / (len(pos) * len(neg))


# --------------------------------------------------------------------------- thresholds

def metrics_at_threshold(scores: Sequence[float], labels: Sequence[int], threshold: float) -> dict:
    """Counts and rates when flagging score >= threshold. Rates are None when their denominator is 0."""
    _check(scores, labels)
    tp = sum(1 for s, y in zip(scores, labels) if y == 1 and s >= threshold)
    fn = sum(1 for s, y in zip(scores, labels) if y == 1 and s < threshold)
    fp = sum(1 for s, y in zip(scores, labels) if y == 0 and s >= threshold)
    tn = sum(1 for s, y in zip(scores, labels) if y == 0 and s < threshold)
    n_pos, n_neg, n = tp + fn, fp + tn, len(scores)
    tpr = tp / n_pos if n_pos else None
    fpr = fp / n_neg if n_neg else None
    return {"threshold": threshold, "tp": tp, "fp": fp, "tn": tn, "fn": fn, "n_pos": n_pos, "n_neg": n_neg,
            "accuracy": (tp + tn) / n if n else None, "tpr": tpr, "fpr": fpr,
            "balanced_accuracy": (tpr + 1 - fpr) / 2 if tpr is not None and fpr is not None else None}


def best_threshold(scores: Sequence[float], labels: Sequence[int]) -> Optional[dict]:
    """Threshold (among the observed scores) maximising balanced accuracy on dev; ties -> the higher threshold.

    Returns metrics_at_threshold of the chosen threshold, or None if a class is empty.
    """
    _check(scores, labels)
    if not any(labels) or all(labels):
        return None
    best = None
    for thr in sorted(set(scores)):
        m = metrics_at_threshold(scores, labels, thr)
        if best is None or m["balanced_accuracy"] >= best["balanced_accuracy"]:   # >= : ties go higher
            best = m
    return best


# --------------------------------------------------------------------------- bootstrap

def stratified_bootstrap_indices(strata: Sequence[Hashable], b: int = DEFAULT_B,
                                 seed: int = DEFAULT_SEED) -> list[np.ndarray]:
    """b resamples of whole units (games), with replacement WITHIN each stratum (episode type), fixed seed."""
    rng = np.random.default_rng(seed)
    groups: dict[Hashable, list[int]] = {}
    for i, s in enumerate(strata):
        groups.setdefault(s, []).append(i)
    keys = sorted(groups, key=str)
    out = []
    for _ in range(b):
        idx = [rng.choice(groups[k], size=len(groups[k]), replace=True) for k in keys]
        out.append(np.concatenate(idx))
    return out


def _percentile_ci(values: list[float], level: float = 0.95) -> tuple[Optional[float], Optional[float]]:
    if not values:
        return None, None
    lo, hi = np.percentile(values, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    return float(lo), float(hi)


def bootstrap_ci(stat: Callable[[np.ndarray], Optional[float]], strata: Sequence[Hashable], b: int = DEFAULT_B,
                 seed: int = DEFAULT_SEED, level: float = 0.95) -> dict:
    """Percentile CI of stat(indices) over stratified resamples; resamples where stat is None are counted, not used."""
    idx_all = np.arange(len(strata))
    est = stat(idx_all)
    vals, n_na = [], 0
    for idx in stratified_bootstrap_indices(strata, b, seed):
        v = stat(idx)
        if v is None:
            n_na += 1
        else:
            vals.append(v)
    lo, hi = _percentile_ci(vals, level)
    return {"estimate": est, "ci_low": lo, "ci_high": hi, "b": b, "b_na": n_na, "seed": seed, "level": level}


def bootstrap_auroc(scores: Sequence[float], labels: Sequence[int], strata: Sequence[Hashable],
                    b: int = DEFAULT_B, seed: int = DEFAULT_SEED) -> dict:
    s, y = list(scores), list(labels)
    return bootstrap_ci(lambda idx: auroc([s[i] for i in idx], [y[i] for i in idx]), strata, b, seed)


def paired_bootstrap_diff(stat_a: Callable[[np.ndarray], Optional[float]],
                          stat_b: Callable[[np.ndarray], Optional[float]], strata: Sequence[Hashable],
                          b: int = DEFAULT_B, seed: int = DEFAULT_SEED, level: float = 0.95) -> dict:
    """CI of stat_a - stat_b using the SAME resample indices for both arms."""
    def diff(idx):
        va, vb = stat_a(idx), stat_b(idx)
        return None if va is None or vb is None else va - vb
    return bootstrap_ci(diff, strata, b, seed, level)


def paired_auroc_diff(scores_a: Sequence[float], scores_b: Sequence[float], labels: Sequence[int],
                      strata: Sequence[Hashable], b: int = DEFAULT_B, seed: int = DEFAULT_SEED) -> dict:
    """AUROC(a) - AUROC(b) on the same games, paired bootstrap CI."""
    sa, sb, y = list(scores_a), list(scores_b), list(labels)
    return paired_bootstrap_diff(lambda idx: auroc([sa[i] for i in idx], [y[i] for i in idx]),
                                 lambda idx: auroc([sb[i] for i in idx], [y[i] for i in idx]), strata, b, seed)


# --------------------------------------------------------------------------- FPR per type (RQ3)

def rule_of_three_upper(n: int) -> Optional[float]:
    """Approximate 95% upper bound for a rate when 0 events were seen in n trials (3/n, capped at 1)."""
    return min(1.0, 3 / n) if n > 0 else None


def fpr_by_type(flags: Sequence[int], labels: Sequence[int], types: Sequence[Hashable]) -> list[dict]:
    """One row per NEGATIVE episode type: n, false positives, FPR, and the rule-of-three bound when fp = 0."""
    rows = []
    for t in sorted({t for t, y in zip(types, labels) if y == 0}, key=str):
        f = [fl for fl, y, tt in zip(flags, labels, types) if y == 0 and tt == t]
        fp = sum(f)
        rows.append({"type": t, "n": len(f), "fp": fp, "fpr": fp / len(f) if f else None,
                     "upper95_rule_of_three": rule_of_three_upper(len(f)) if fp == 0 else None})
    return rows


# --------------------------------------------------------------------------- agreement / ranking

def _ranks(x: Sequence[float]) -> list[float]:
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def _pearson(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if sa == 0 or sb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def spearman(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Spearman rank correlation (Pearson on average ranks). None if n < 2 or an input is constant."""
    if len(x) != len(y):
        raise ValueError("length mismatch")
    return _pearson(_ranks(x), _ranks(y))


def mean_abs_diff(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    if len(x) != len(y):
        raise ValueError("length mismatch")
    return sum(abs(a - b) for a, b in zip(x, y)) / len(x) if x else None


def kendall_tau(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Kendall tau-b (tie-corrected). None if n < 2 or an input is constant."""
    if len(x) != len(y):
        raise ValueError("length mismatch")
    n = len(x)
    if n < 2:
        return None
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif dx * dy > 0:
                conc += 1
            else:
                disc += 1
    denom = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return (conc - disc) / denom if denom else None


# --------------------------------------------------------------------------- RQ8

def top1_pair_accuracy(predicted: Sequence[Sequence[str]], true: Sequence[Sequence[str]]) -> dict:
    """Share of games whose predicted pair equals the true focal pair (order-free). An empty prediction is wrong."""
    if len(predicted) != len(true):
        raise ValueError("length mismatch")
    correct = sum(1 for p, t in zip(predicted, true) if p and len(p) == 2 and set(p) == set(t))
    n = len(true)
    return {"n": n, "correct": correct, "no_pair": sum(1 for p in predicted if not p),
            "accuracy": correct / n if n else None}
