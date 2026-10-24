"""Tests for core.stats.metrics: hand-computed values, brute-force AUROC, deterministic bootstrap."""
import itertools
import random

import numpy as np
import pytest

from core.stats import metrics as M


def brute_auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p, n in itertools.product(pos, neg))
    return wins / (len(pos) * len(neg))


def test_auroc_hand_example():
    # pos {0.9, 0.4}, neg {0.8, 0.4, 0.1}: 0.9 beats 3; 0.4 loses to 0.8, ties 0.4, beats 0.1 -> 4.5 / 6
    assert M.auroc([0.9, 0.8, 0.4, 0.4, 0.1], [1, 0, 1, 0, 0]) == 0.75
    assert M.auroc([1, 2], [0, 1]) == 1.0 and M.auroc([1, 2], [1, 0]) == 0.0 and M.auroc([5, 5], [0, 1]) == 0.5


def test_auroc_matches_brute_force_with_ties():
    rng = random.Random(7)
    for _ in range(200):
        n = rng.randint(2, 30)
        labels = [rng.randint(0, 1) for _ in range(n)]
        if 0 < sum(labels) < n:
            scores = [rng.choice([0, 10, 20, 50, 80, 100]) for _ in range(n)]   # many ties
            assert M.auroc(scores, labels) == pytest.approx(brute_auroc(scores, labels))


def test_auroc_na_and_input_checks():
    assert M.auroc([1, 2, 3], [1, 1, 1]) is None and M.auroc([1, 2], [0, 0]) is None
    with pytest.raises(ValueError):
        M.auroc([1, None], [0, 1])
    with pytest.raises(ValueError):
        M.auroc([1, 2], [0, 2])


def test_metrics_at_threshold_counts():
    m = M.metrics_at_threshold([10, 20, 30, 40, 50], [0, 1, 0, 1, 1], 30)
    assert (m["tp"], m["fp"], m["tn"], m["fn"]) == (2, 1, 1, 1)
    assert m["tpr"] == pytest.approx(2 / 3) and m["fpr"] == 0.5 and m["accuracy"] == 0.6
    assert m["balanced_accuracy"] == pytest.approx((2 / 3 + 0.5) / 2)
    assert M.metrics_at_threshold([1, 2], [0, 0], 1)["tpr"] is None


def test_best_threshold_max_balanced_accuracy_ties_to_higher():
    assert M.best_threshold([10, 20, 30, 40], [0, 0, 1, 1])["threshold"] == 30
    # thr 2: tpr 1, fpr .5 -> .75 ; thr 4: tpr .5, fpr 0 -> .75 ; tie -> the higher threshold (4)
    b = M.best_threshold([1, 2, 3, 4], [0, 1, 0, 1])
    assert b["threshold"] == 4 and b["balanced_accuracy"] == 0.75
    assert M.best_threshold([1, 2], [1, 1]) is None


def test_bootstrap_indices_stratified_and_deterministic():
    strata = [1, 1, 1, 2, 2, 3]
    a = M.stratified_bootstrap_indices(strata, b=50, seed=11)
    b = M.stratified_bootstrap_indices(strata, b=50, seed=11)
    assert all(np.array_equal(x, y) for x, y in zip(a, b)) and len(a) == 50
    for idx in a:
        assert sorted(strata[i] for i in idx) == sorted(strata)          # stratum sizes kept
    c = M.stratified_bootstrap_indices(strata, b=50, seed=12)
    assert not all(np.array_equal(x, y) for x, y in zip(a, c))


def test_bootstrap_auroc_ci_contains_estimate_and_is_reproducible():
    scores = [90, 80, 70, 60, 40, 30, 20, 10, 85, 15]
    labels = [1, 1, 1, 0, 1, 0, 0, 0, 1, 0]
    strata = [1, 1, 1, 2, 1, 3, 4, 2, 1, 3]
    r1 = M.bootstrap_auroc(scores, labels, strata, b=300, seed=5)
    r2 = M.bootstrap_auroc(scores, labels, strata, b=300, seed=5)
    assert r1 == r2 and r1["estimate"] == M.auroc(scores, labels)
    assert r1["ci_low"] <= r1["estimate"] <= r1["ci_high"] and r1["b_na"] == 0


def test_paired_diff_uses_same_indices():
    labels = [1, 1, 0, 0, 1, 0]
    strata = [1, 1, 2, 2, 1, 3]
    a = [0.9, 0.7, 0.2, 0.4, 0.6, 0.1]
    same = M.paired_auroc_diff(a, a, labels, strata, b=200, seed=3)
    assert (same["estimate"], same["ci_low"], same["ci_high"]) == (0.0, 0.0, 0.0)   # identical arms -> exactly 0
    b = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    d = M.paired_auroc_diff(a, b, labels, strata, b=200, seed=3)
    assert d["estimate"] == pytest.approx(M.auroc(a, labels) - 0.5)
    # recompute by hand with the same indices
    idx = M.stratified_bootstrap_indices(strata, b=200, seed=3)
    manual = [M.auroc([a[i] for i in ix], [labels[i] for i in ix]) - M.auroc([b[i] for i in ix], [labels[i] for i in ix])
              for ix in idx]
    assert d["ci_low"] == pytest.approx(float(np.percentile(manual, 2.5)))


def test_fpr_by_type_and_rule_of_three():
    rows = M.fpr_by_type([1, 0, 0, 0, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0, 0], [1, 2, 2, 3, 3, 4, 4, 4, 4])
    assert rows == [{"type": 2, "n": 2, "fp": 0, "fpr": 0.0, "upper95_rule_of_three": 1.0},
                    {"type": 3, "n": 2, "fp": 1, "fpr": 0.5, "upper95_rule_of_three": None},
                    {"type": 4, "n": 4, "fp": 0, "fpr": 0.0, "upper95_rule_of_three": 0.75}]
    assert M.rule_of_three_upper(12) == 0.25 and M.rule_of_three_upper(0) is None


def test_spearman_mean_abs_diff_kendall():
    assert M.spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)          # 1 - 6*2/(4*15)
    assert M.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert M.spearman([1, 1, 1], [1, 2, 3]) is None
    assert M.mean_abs_diff([10, 20, 30], [12, 20, 25]) == pytest.approx(7 / 3)
    assert M.kendall_tau([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(4 / 6)      # 5 concordant, 1 discordant
    assert M.kendall_tau([1, 1, 2], [1, 2, 3]) == pytest.approx(2 / (3 * 2) ** 0.5)  # tau-b with a tie
    assert M.kendall_tau([1, 2], [5, 5]) is None


def test_top1_pair_accuracy():
    r = M.top1_pair_accuracy([["M", "T"], ["T", "M"], [], ["J", "Q"]], [["M", "T"]] * 4)
    assert r == {"n": 4, "correct": 2, "no_pair": 1, "accuracy": 0.5}
