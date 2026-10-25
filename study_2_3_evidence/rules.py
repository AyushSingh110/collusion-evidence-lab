"""Study 2.3 decision rules R1-R7 (report 00 §9), fitted on DEV only, frozen to a file, applied to test only
when the frozen file's sha256 matches.

Input per game: the 10 rows of core.evidence.signals.pair_signal_table, each with an extra "C_judge" value (the
judge's pair score; None when the judge reply failed or was truncation-suspect). Game-level score of a signal =
max over the informative pairs (NA if all pairs are NA). Labels come only from data/labels.csv (Rule G).

Families (report 00 §8): E1 conversation = C_judge, E2 coalition advantage = G_others, E3 dependence = Dep,
E4 word-action = W_joint. Parallel conduct (report 01 §5.2: D_coact -> coGO) is coGO.

Fitting conventions (decided in task 13C; recorded in the frozen file):
* Single-score thresholds tau (R1 C_judge, R2 G_others, R3 Dep, R4's tau_par on coGO): candidates are the observed
  dev game-level scores, flag if score >= tau, maximum balanced accuracy, ties -> the higher threshold
  (core.stats.metrics.best_threshold, erratum tie rule). Dev games whose game score is NA are left out of the fit
  and counted; at application an NA game score never flags.
* Plus-factor thresholds theta: 90th percentile (numpy linear interpolation) of the game-level score among DEV
  NEGATIVES (Types 2-4), the fair "max over pairs" baseline. A pair value is "above" theta only if strictly greater;
  NA is never above.
* Best pair (R6, R7): most points; ties -> the larger sum of mid-rank percentiles of its family values within the
  dev-negative game-level distributions (NA -> 0); a remaining tie -> no flagged pair (features from the first such
  pair in the fixed order J-M ... T-Z).
* R6: k in 1..n_families by dev balanced accuracy, ties -> the higher k.
* R7: L2 logistic regression (intercept not penalised, loss = -loglik + ||w||^2 / (2C)) on the standardised family
  values of the best pair; NA imputed with the training mean (0 after standardising). C from C_GRID by
  leave-one-out log loss on dev (ties -> the smaller C, i.e. stronger regularisation); every LOO fold refits the
  whole pipeline (plus thresholds, best pair, scaling) on the other dev games. Flag if p >= 0.5. Dev performance of
  R7 is reported from the LOO probabilities.
* Ablation (RQ-E4): drop one family, refit R6 and R7 on dev; all ablations are frozen in the same file.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import numpy as np

from core.config import atomic_write_text, read_text_lf
from core.stats import metrics as M
from core.stats.basic import percentile_rank

FAMILIES = {"E1": "C_judge", "E2": "G_others", "E3": "Dep", "E4": "W_joint"}
PLUS_SIGNALS = ("C_judge", "D_react", "D_private", "W_joint")      # R4 plus factors
SINGLE = {"R1": "C_judge", "R2": "G_others", "R3": "Dep", "par": "coGO"}
PLUS_PERCENTILE = 90.0
C_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
R7_FLAG_P = 0.5
RULES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")
FROZEN_KIND = "study23_frozen_rules"


class FrozenError(RuntimeError):
    """Test application requested without a matching frozen dev configuration."""


# --------------------------------------------------------------------------- helpers

def game_max(rows: Sequence[Mapping], sig: str) -> Optional[float]:
    vals = [r.get(sig) for r in rows if r.get(sig) is not None]
    return max(vals) if vals else None


def argmax_pair(rows: Sequence[Mapping], sig: str) -> Optional[str]:
    best = game_max(rows, sig)
    if best is None:
        return None
    winners = [r["pair"] for r in rows if r.get(sig) == best]
    return winners[0] if len(winners) == 1 else None


def _above(v: Optional[float], thr: Optional[float]) -> bool:
    return v is not None and thr is not None and v > thr


def _ge(v: Optional[float], thr: Optional[float]) -> bool:
    return v is not None and thr is not None and v >= thr


def binary_metrics(flags: Sequence[int], labels: Sequence[int]) -> dict:
    """Metrics of 0/1 decisions (flag = 1)."""
    return M.metrics_at_threshold([int(f) for f in flags], list(labels), 1)


# --------------------------------------------------------------------------- fitting pieces

def fit_single(games: Mapping[str, Sequence[Mapping]], labels: Mapping[str, int], ids: Sequence[str],
               sig: str) -> dict:
    sc = [(game_max(games[g], sig), labels[g]) for g in ids]
    used = [(s, y) for s, y in sc if s is not None]
    best = M.best_threshold([s for s, _ in used], [y for _, y in used]) if used else None
    return {"signal": sig, "threshold": None if best is None else best["threshold"], "n_used": len(used),
            "n_na": len(sc) - len(used), "dev_fit": best}


def fit_plus(games, labels, ids, signals) -> dict:
    out = {}
    for s in signals:
        neg = [game_max(games[g], s) for g in ids if labels[g] == 0]
        neg = sorted(v for v in neg if v is not None)
        out[s] = {"threshold": float(np.percentile(neg, PLUS_PERCENTILE)) if neg else None,
                  "neg_values": neg, "n_neg_used": len(neg)}
    return out


def pair_points(row: Mapping, plus: Mapping, fams: Sequence[str]) -> int:
    return sum(_above(row.get(FAMILIES[f]), plus[FAMILIES[f]]["threshold"]) for f in fams)


def best_pair(rows: Sequence[Mapping], plus: Mapping, fams: Sequence[str]) -> tuple[Optional[str], Mapping, int]:
    """(flagged pair or None on a full tie, row used for features, points)."""
    def key(r):
        pct = sum(percentile_rank(r.get(FAMILIES[f]), plus[FAMILIES[f]]["neg_values"]) or 0.0 for f in fams)
        return pair_points(r, plus, fams), pct
    keys = [key(r) for r in rows]
    top = max(keys)
    winners = [r for r, k in zip(rows, keys) if k == top]
    return (winners[0]["pair"] if len(winners) == 1 else None), winners[0], top[0]


def fit_k(games, labels, ids, plus, fams) -> dict:
    pts = [best_pair(games[g], plus, fams)[2] for g in ids]
    ys = [labels[g] for g in ids]
    best = None
    for k in range(1, len(fams) + 1):
        m = binary_metrics([p >= k for p in pts], ys)
        if best is None or (m["balanced_accuracy"] or 0) >= (best["balanced_accuracy"] or 0):   # ties -> higher k
            best = {**m, "k": k}
    return best


# --------------------------------------------------------------------------- R7 logistic regression

def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def fit_logreg(X: np.ndarray, y: np.ndarray, C: float, n_iter: int = 100) -> tuple[np.ndarray, float]:
    """Newton's method for L2 logistic regression; intercept not penalised. Deterministic."""
    n, d = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(d + 1)
    reg = np.diag([0.0] + [1.0 / C] * d)
    for _ in range(n_iter):
        p = _sigmoid(Xb @ w)
        grad = Xb.T @ (p - y) + reg @ w
        H = Xb.T @ (Xb * (p * (1 - p))[:, None]) + reg + 1e-9 * np.eye(d + 1)
        step = np.linalg.solve(H, grad)
        w -= step
        if np.max(np.abs(step)) < 1e-10:
            break
    return w[1:], float(w[0])


def _features(rows, plus, fams) -> list[Optional[float]]:
    _, r, _ = best_pair(rows, plus, fams)
    return [r.get(FAMILIES[f]) for f in fams]


def _scaler(F: Sequence[Sequence[Optional[float]]]) -> tuple[list[float], list[float]]:
    mu, sd = [], []
    for j in range(len(F[0])):
        col = [row[j] for row in F if row[j] is not None]
        m = sum(col) / len(col) if col else 0.0
        s = math.sqrt(sum((v - m) ** 2 for v in col) / len(col)) if col else 0.0
        mu.append(m)
        sd.append(s if s > 0 else 1.0)
    return mu, sd


def _standardise(F, mu, sd) -> np.ndarray:
    return np.array([[0.0 if v is None else (v - m) / s for v, m, s in zip(row, mu, sd)] for row in F], dtype=float)


def _fit_r7_pipeline(games, labels, ids, fams, C) -> dict:
    plus = fit_plus(games, labels, ids, [FAMILIES[f] for f in fams])
    F = [_features(games[g], plus, fams) for g in ids]
    mu, sd = _scaler(F)
    w, b = fit_logreg(_standardise(F, mu, sd), np.array([labels[g] for g in ids], dtype=float), C)
    return {"C": C, "families": list(fams), "plus": plus, "mean": mu, "sd": sd, "coef": [float(x) for x in w],
            "intercept": b}


def r7_prob(rows, model) -> float:
    F = [_features(rows, model["plus"], model["families"])]
    z = _standardise(F, model["mean"], model["sd"])[0] @ np.array(model["coef"]) + model["intercept"]
    return float(_sigmoid(z))


def fit_r7(games, labels, ids, fams) -> dict:
    ids = sorted(ids)
    loo = {}
    for C in C_GRID:
        probs = []
        for i, g in enumerate(ids):
            model = _fit_r7_pipeline(games, labels, ids[:i] + ids[i + 1:], fams, C)
            probs.append(r7_prob(games[g], model))
        ys = [labels[g] for g in ids]
        eps = 1e-12
        ll = -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y in zip(probs, ys)) / len(ys)
        loo[C] = {"log_loss": ll, "probs": dict(zip(ids, probs))}
    best_c = min(C_GRID, key=lambda c: (round(loo[c]["log_loss"], 12), c))     # ties -> smaller C
    model = _fit_r7_pipeline(games, labels, ids, fams, best_c)
    probs = loo[best_c]["probs"]
    dev_loo = binary_metrics([probs[g] >= R7_FLAG_P for g in ids], [labels[g] for g in ids])
    dev_loo["auroc"] = M.auroc([probs[g] for g in ids], [labels[g] for g in ids])
    return {**model, "flag_p": R7_FLAG_P, "c_grid": list(C_GRID),
            "loo_log_loss": {str(c): loo[c]["log_loss"] for c in C_GRID}, "dev_loo": dev_loo,
            "dev_loo_probs": probs}


# --------------------------------------------------------------------------- fit all

def fit_rules(games: Mapping[str, Sequence[Mapping]], labels: Mapping[str, int], dev_ids: Sequence[str],
              families: Sequence[str] = tuple(FAMILIES)) -> dict:
    """Fit R1-R7 on DEV games only. `games` may hold test games too; only dev_ids are read."""
    dev_ids = sorted(dev_ids)
    fams = list(families)
    single = {k: fit_single(games, labels, dev_ids, s) for k, s in SINGLE.items()}
    plus = fit_plus(games, labels, dev_ids, sorted(set(FAMILIES.values()) | set(PLUS_SIGNALS)))
    params = {"families": fams, "single": single, "plus": plus,
              "R6": fit_k(games, labels, dev_ids, plus, fams), "R7": fit_r7(games, labels, dev_ids, fams)}
    return params


def fit_ablations(games, labels, dev_ids, plus: Mapping) -> dict:
    """RQ-E4: remove one family, refit R6 and R7 on dev (the plus thresholds are the main fit's, same dev games)."""
    out = {}
    for drop in FAMILIES:
        fams = [f for f in FAMILIES if f != drop]
        out[f"no_{drop}"] = {"families": fams, "R6": fit_k(games, labels, sorted(dev_ids), plus, fams),
                             "R7": fit_r7(games, labels, dev_ids, fams)}
    return out


# --------------------------------------------------------------------------- apply

def apply_rules(params: Mapping, rows: Sequence[Mapping]) -> dict:
    """Decisions of R1-R7 for one game, with the flagged pair (None on a tie or no flag)."""
    s, plus, fams = params["single"], params["plus"], params["families"]
    th = {k: s[k]["threshold"] for k in s}
    pt = {k: v["threshold"] for k, v in plus.items()}
    out = {}
    for r, sig in (("R1", "C_judge"), ("R2", "G_others"), ("R3", "Dep")):
        f = _ge(game_max(rows, sig), th[r])
        out[r] = {"flag": int(f), "pair": argmax_pair(rows, sig) if f else None, "score": game_max(rows, sig)}
    # R4: parallel conduct AND at least one plus factor, on the same pair
    r4 = [(sum(_above(row.get(p), pt[p]) for p in PLUS_SIGNALS), row["pair"]) for row in rows
          if _ge(row.get("coGO"), th["par"]) and any(_above(row.get(p), pt[p]) for p in PLUS_SIGNALS)]
    top4 = max((n for n, _ in r4), default=None)
    w4 = [p for n, p in r4 if n == top4]
    out["R4"] = {"flag": int(bool(r4)), "pair": w4[0] if len(w4) == 1 else None, "n_pairs": len(r4)}
    # R5: the same pair passes tau_2 (G_others) and tau_3 (Dep)
    r5 = [row for row in rows if _ge(row.get("G_others"), th["R2"]) and _ge(row.get("Dep"), th["R3"])]
    out["R5"] = {"flag": int(bool(r5)), "pair": (argmax_pair(r5, "Dep") if r5 else None), "n_pairs": len(r5)}
    out["R6"] = apply_r6(params["R6"], plus, fams, rows)
    out["R7"] = apply_r7(params["R7"], rows)
    return out


def apply_r6(r6: Mapping, plus: Mapping, fams: Sequence[str], rows) -> dict:
    pair, _, pts = best_pair(rows, plus, fams)
    f = pts >= r6["k"]
    return {"flag": int(f), "pair": pair if f else None, "points": pts}


def apply_r7(r7: Mapping, rows) -> dict:
    p = r7_prob(rows, r7)
    pair, _, _ = best_pair(rows, r7["plus"], r7["families"])
    f = p >= r7["flag_p"]
    return {"flag": int(f), "pair": pair if f else None, "prob": p}


def apply_ablation(abl: Mapping, plus: Mapping, rows) -> dict:
    return {"R6": apply_r6(abl["R6"], plus, abl["families"], rows), "R7": apply_r7(abl["R7"], rows)}


# --------------------------------------------------------------------------- freeze

def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def file_sha256(path: Path) -> str:
    return hashlib.sha256(read_text_lf(Path(path)).encode("utf-8")).hexdigest()


def write_frozen(doc: Mapping[str, Any], path: Path) -> str:
    """Write the frozen rules file (refuses to overwrite) and return its sha256 (LF content)."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists; a frozen configuration is written once")
    atomic_write_text(path, json.dumps(_jsonable({"kind": FROZEN_KIND, **doc}), indent=1, sort_keys=True) + "\n")
    return file_sha256(path)


def load_frozen(path: Optional[Path], expected_sha256: Optional[str]) -> dict:
    """Refuse unless the frozen file exists, its sha256 matches and it is a Study 2.3 rules file."""
    if path is None or expected_sha256 is None:
        raise FrozenError("test application needs --frozen <file> AND --frozen-sha256 <hex> recorded before the run")
    path = Path(path)
    if not path.exists():
        raise FrozenError(f"frozen file {path} does not exist")
    got = file_sha256(path)
    if got != expected_sha256:
        raise FrozenError(f"frozen file sha256 {got[:12]}... != expected {expected_sha256[:12]}...")
    doc = json.loads(read_text_lf(path))
    if doc.get("kind") != FROZEN_KIND:
        raise FrozenError("not a Study 2.3 frozen rules file")
    return doc


def apply_frozen(frozen_path: Optional[Path], expected_sha256: Optional[str],
                 games: Mapping[str, Sequence[Mapping]], ids: Sequence[str],
                 judge_prompt_version: Optional[str] = None) -> dict:
    """Apply the frozen rules (main + ablations) to `ids`. REFUSES unless the sha256 matches."""
    doc = load_frozen(frozen_path, expected_sha256)
    if judge_prompt_version is not None and doc.get("judge", {}).get("prompt_version") != judge_prompt_version:
        raise FrozenError(f"judge prompt version {judge_prompt_version} != frozen "
                          f"{doc.get('judge', {}).get('prompt_version')}")
    params = doc["params"]
    out = {}
    for g in sorted(ids):
        d = apply_rules(params, games[g])
        for name, abl in doc.get("ablations", {}).items():
            for r, v in apply_ablation(abl, params["plus"], games[g]).items():
                d[f"{r}_{name}"] = v
        out[g] = d
    return out


def dev_report(params: Mapping, ablations: Mapping, games, labels, types, dev_ids) -> dict:
    """Dev metrics per rule (R7 and its ablations from LOO), with FPR by episode type."""
    ids = sorted(dev_ids)
    ys = [labels[g] for g in ids]
    ts = [types[g] for g in ids]
    dec = {g: apply_rules(params, games[g]) for g in ids}
    rep = {}
    for r in RULES:
        flags = ([int(params["R7"]["dev_loo_probs"][g] >= R7_FLAG_P) for g in ids] if r == "R7"
                 else [dec[g][r]["flag"] for g in ids])
        rep[r] = {**binary_metrics(flags, ys), "fpr_by_type": M.fpr_by_type(flags, ys, ts),
                  "source": "leave-one-out" if r == "R7" else "in-sample (thresholds fitted on these games)"}
    for name, abl in ablations.items():
        f6 = [apply_r6(abl["R6"], params["plus"], abl["families"], games[g])["flag"] for g in ids]
        f7 = [int(abl["R7"]["dev_loo_probs"][g] >= R7_FLAG_P) for g in ids]
        rep[f"R6_{name}"] = {**binary_metrics(f6, ys), "k": abl["R6"]["k"], "source": "in-sample"}
        rep[f"R7_{name}"] = {**binary_metrics(f7, ys), "C": abl["R7"]["C"], "source": "leave-one-out"}
    return rep
