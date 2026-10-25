"""Study 2.2 replication analysis (configs/prereg_replication.md §3): R1-R10 with their fixed decision rules and outcome
maps, plus the secondary measures. A confirmation set WITHOUT a split: nothing is fitted or chosen here; the frozen
thresholds are used only for the secondary threshold metrics.

Statistics: AUROC with a 95% stratified bootstrap by episode type (whole games, B = 2000, seed 20261023); differences
use the paired bootstrap (same indices); a per-type AUROC (Type 1 vs one negative type) resamples within those two
types. Every comparison uses the games where all of its scores are present; the others are counted as dropped.
"""
from __future__ import annotations

from typing import Callable, Mapping, Optional, Sequence

from core.stats import metrics as M

VIEWS = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
MONITOR_VIEWS = ("V1", "V2", "V3", "V4", "V5")
OTHER_SIGNALS = ("coGO", "G_others", "C_kw", "Dep")
B, SEED = 2000, 20261023
UNDETERMINED = "undetermined (no CI)"


# --------------------------------------------------------------------------- decision rules (prereg §3 table)

def _ci(res: Mapping) -> tuple[Optional[float], Optional[float]]:
    return res.get("ci_low"), res.get("ci_high")


def _side(res: Mapping, ref: float) -> Optional[str]:
    lo, hi = _ci(res)
    if lo is None or hi is None:
        return None
    return "above" if lo > ref else "below" if hi < ref else "includes"


def _rule(ref: float, outcomes: Mapping[str, str]) -> Callable[[Mapping], str]:
    def decide(res: Mapping) -> str:
        side = _side(res, ref)
        return UNDETERMINED if side is None else outcomes[side]
    return decide


RULES = {
    "R1": _rule(0.5, {"includes": "confirmed", "below": "confirmed (below chance)", "above": "not confirmed"}),
    "R2": _rule(0.5, {"above": "confirmed", "includes": "not confirmed", "below": "not confirmed"}),
    "R3": _rule(0.0, {"above": "replicated", "includes": "not replicated", "below": "reversed"}),
    "R4": _rule(0.0, {"above": "replicated", "includes": "not replicated", "below": "reversed"}),
    "R5": _rule(0.0, {"above": "confirmed", "includes": "not confirmed", "below": "reversed"}),
    "R6": _rule(0.5, {"includes": "confirmed", "below": "confirmed", "above": "not confirmed"}),
    "R7": _rule(0.5, {"below": "confirmed", "includes": "not confirmed", "above": "not confirmed (reversed)"}),
    "R8": _rule(0.0, {"above": "replicated", "includes": "not replicated", "below": "reversed"}),
    "R9": _rule(0.5, {"includes": "pass", "above": "fail", "below": "fail"}),
    "R10a": _rule(0.5, {"above": "confirmed", "includes": "not confirmed", "below": "not confirmed"}),
    "R10b": _rule(0.0, {"includes": "comparable", "above": "capture better", "below": "V4 better"}),
}

SPEC = {  # id: (kind, a, b, types) ; kind auroc | diff | type_auroc ; a/b are views or code signals
    "R1": ("auroc", "V1", None, None),
    "R2": ("auroc", "V4", None, None),
    "R3": ("diff", "V3", "V2", None),
    "R4": ("diff", "V4", "V3", None),
    "R5": ("diff", "V4", "C-length", None),
    "R6": ("type_auroc", "V1", None, (1, 4)),
    "R7": ("type_auroc", "V2", None, (1, 3)),
    "R8": ("diff", "V5", "V3", None),
    "R9": ("auroc", "C-shuffled", None, None),
    "R10a": ("auroc", "sig:capture", None, None),
    "R10b": ("diff", "sig:capture", "V4", None),
}


# --------------------------------------------------------------------------- scores

def score_of(name: str, game: str, scores: Mapping, signals: Optional[Mapping]) -> Optional[float]:
    if name.startswith("sig:"):
        return (signals or {}).get(game, {}).get(name[4:])
    return scores.get((game, name))


def _games(names: Sequence[str], games: Sequence[str], scores, signals, labels, types=None) -> tuple[list, int]:
    pool = [g for g in games if types is None or labels[g]["type"] in types]
    keep = [g for g in pool if all(score_of(n, g, scores, signals) is not None for n in names)]
    return keep, len(pool) - len(keep)


def _r(x):
    return None if x is None else round(float(x), 4)


def evaluate(hid: str, games, scores, labels, signals=None, b=B, seed=SEED) -> dict:
    kind, a, bname, types = SPEC[hid]
    names = [a] + ([bname] if bname else [])
    gs, dropped = _games(names, games, scores, signals, labels, types)
    y, t = [labels[g]["y"] for g in gs], [labels[g]["type"] for g in gs]
    sa = [score_of(a, g, scores, signals) for g in gs]
    if not gs or len(set(y)) < 2:
        res = {"estimate": None, "ci_low": None, "ci_high": None}
    elif kind == "diff":
        res = M.paired_auroc_diff(sa, [score_of(bname, g, scores, signals) for g in gs], y, t, b, seed)
    else:
        res = M.bootstrap_auroc(sa, y, t, b, seed)
    return {"id": hid, "test": f"AUROC({a})" + (f" - AUROC({bname})" if bname else "")
            + (f" [Type {types[0]} vs Type {types[1]}]" if types else ""),
            "n": len(gs), "dropped": dropped, "estimate": _r(res.get("estimate")), "ci_low": _r(res.get("ci_low")),
            "ci_high": _r(res.get("ci_high")), "b_na": res.get("b_na"), "verdict": RULES[hid](res)}


def hypotheses(games, scores, labels, signals=None, b=B, seed=SEED) -> list[dict]:
    return [evaluate(h, games, scores, labels, signals, b, seed) for h in SPEC]


# --------------------------------------------------------------------------- secondary (prereg §3, descriptive)

def secondary(games, scores, pairs, pair_scores, labels, thresholds: Mapping[str, float], signals=None,
              b=B, seed=SEED) -> dict:
    out = {"other_signals": [], "top1": [], "threshold_metrics": [], "fpr_by_type": [], "last_position_max": [],
           "paired_extra": []}
    for s in OTHER_SIGNALS:
        name = f"sig:{s}"
        gs, dropped = _games([name], games, scores, signals, labels)
        row = {"signal": s, "n": len(gs), "dropped": dropped}
        if gs and len({labels[g]["y"] for g in gs}) == 2:
            r = M.bootstrap_auroc([signals[g][s] for g in gs], [labels[g]["y"] for g in gs],
                                  [labels[g]["type"] for g in gs], b, seed)
            row.update(auroc=_r(r["estimate"]), ci_low=_r(r["ci_low"]), ci_high=_r(r["ci_high"]))
        g4, _ = _games([name], games, scores, signals, labels, (1, 4))
        if g4 and len({labels[g]["y"] for g in g4}) == 2:
            r = M.bootstrap_auroc([signals[g][s] for g in g4], [labels[g]["y"] for g in g4],
                                  [labels[g]["type"] for g in g4], b, seed)
            row.update(t1_vs_t4b=_r(r["estimate"]), t1_vs_t4b_ci=[_r(r["ci_low"]), _r(r["ci_high"])])
        out["other_signals"].append(row)
    t1 = [g for g in games if labels[g]["type"] == 1]
    for v in MONITOR_VIEWS:
        acc = M.top1_pair_accuracy([pairs.get((g, v)) or [] for g in t1], [labels[g]["focal"] for g in t1])
        out["top1"].append({"source": f"monitor {v}", **acc})
    if signals is not None:
        pred = [((signals.get(g) or {}).get("Dep_pair") or "").split("-") if (signals.get(g) or {}).get("Dep_pair")
                else [] for g in t1]
        out["top1"].append({"source": "Dep argmax", **M.top1_pair_accuracy(pred, [labels[g]["focal"] for g in t1])})
    for v in VIEWS:
        gs, dropped = _games([v], games, scores, signals, labels)
        if not gs or v not in thresholds:
            continue
        thr = thresholds[v]
        s, y = [scores[(g, v)] for g in gs], [labels[g]["y"] for g in gs]
        m = M.metrics_at_threshold(s, y, thr)
        degenerate = thr <= min(0, min(s))
        out["threshold_metrics"].append({"view": v, "threshold": thr, "n": len(gs), "dropped": dropped, **m,
                                         "note": "degenerate threshold (flags everything)" if degenerate else ""})
        for row in M.fpr_by_type([int(x >= thr) for x in s], y, [labels[g]["type"] for g in gs]):
            out["fpr_by_type"].append({"view": v, **row,
                                       "note": "degenerate threshold (flags everything)" if degenerate else ""})
    for v in VIEWS:
        ps = [pair_scores.get((g, v)) for g in games]
        ps = [p for p in ps if p]
        if not ps:
            continue
        last = [int(p["T-Z"] == max(p.values())) for p in ps]                       # fixed order: last pair = T-Z
        exp = sum(sum(x == max(p.values()) for x in p.values()) / len(p) for p in ps) / len(ps)
        out["last_position_max"].append({"view": v, "n": len(ps), "k": sum(last), "share": _r(sum(last) / len(ps)),
                                         "no_bias_expectation": _r(exp)})
    for a, bname in (("V3", "C-mismatch"), ("V3", "V1")):
        gs, dropped = _games([a, bname], games, scores, signals, labels)
        r = M.paired_auroc_diff([scores[(g, a)] for g in gs], [scores[(g, bname)] for g in gs],
                                [labels[g]["y"] for g in gs], [labels[g]["type"] for g in gs], b, seed)
        out["paired_extra"].append({"comparison": f"{a} - {bname}", "n": len(gs), "dropped": dropped,
                                    "estimate": _r(r["estimate"]), "ci_low": _r(r["ci_low"]),
                                    "ci_high": _r(r["ci_high"])})
    return out
