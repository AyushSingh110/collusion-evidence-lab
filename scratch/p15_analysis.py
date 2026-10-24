"""Task 15 (EXPLORATORY, not pre-registered; no model calls): dev-vs-test stability, pooled 48 games, test V3 - V1,
code signals. Reads the frozen-config monitor outputs (dev: run p7_v3_ctx16k sample 0; test: run test_p8) and
runs/p8_signals/game_signals.csv (honest baseline fitted on DEV Type 2 only, task 14).

  conda run -n collusion-lab python -B scratch/p15_analysis.py
Writes runs/p15/results.json and runs/p15/tables.md.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402
from core.stats import metrics as M  # noqa: E402

B, SEED = 2000, 20261023
OUT = REPO_ROOT / "runs/p15"
VIEWS = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
SIGS = ("coGO", "capture", "G_others", "C_kw", "Dep")
RUNS = {"dev": REPO_ROOT / "runs/p7_v3_ctx16k/outputs/monitor.jsonl", "test": REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl"}
REPORTED = {"dev": REPO_ROOT / "runs/p7_analysis_dev/rq1_per_view_dev.csv", "test": REPO_ROOT / "runs/test_p8/rq1_per_view_test.csv"}

LAB = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
SPLIT = json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))
IDS = {"dev": sorted(SPLIT["dev"]), "test": sorted(SPLIT["test"])}
IDS["pooled"] = IDS["dev"] + IDS["test"]
T = lambda g: int(LAB[g]["episode_type"])
Y = lambda g: int(LAB[g]["collusion"])

score = {}
for split, path in RUNS.items():
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line) if line.strip() else None
        if d and d["sample_idx"] == 0 and d["game_id"] in IDS[split]:
            assert (d["game_id"], d["view"]) not in score, "duplicate (game, view)"
            score[(d["game_id"], d["view"])] = d["score"]
assert len(score) == 48 * len(VIEWS) and all(v is not None for v in score.values())
SIG = {r["game_id"]: {s: (float(r[s]) if r[s] != "" else None) for s in SIGS}
       for r in csv.DictReader(open(REPO_ROOT / "runs/p8_signals/game_signals.csv", encoding="utf-8"))}


def r3(x):
    return None if x is None else round(x, 3)


def ci(d):
    return {"estimate": r3(d["estimate"]), "ci": [r3(d["ci_low"]), r3(d["ci_high"])], "b_na": d["b_na"]}


def per_view_auroc(games, get):
    gs = [g for g in games if get(g) is not None]
    return gs, ci(M.bootstrap_auroc([get(g) for g in gs], [Y(g) for g in gs], [T(g) for g in gs], B, SEED))


def per_type(games, get):
    out = {}
    for neg in (2, 3, 4):
        gs = [g for g in games if T(g) in (1, neg) and get(g) is not None]
        out[f"T1_vs_T{neg}"] = ci(M.bootstrap_auroc([get(g) for g in gs], [Y(g) for g in gs], [T(g) for g in gs], B, SEED)) | {"n": len(gs)}
    return out


def paired(games, a, b):
    gs = list(games)
    return ci(M.paired_auroc_diff([score[(g, a)] for g in gs], [score[(g, b)] for g in gs], [Y(g) for g in gs],
                                  [T(g) for g in gs], B, SEED)) | {"n": len(gs)}


res = {"label": "EXPLORATORY, not pre-registered", "b": B, "seed": SEED}

# 0. reproduce the reported per-view AUROCs (consistency check, not a new result)
chk = {}
for split in ("dev", "test"):
    rep = {r["view"]: float(r["auroc"]) for r in csv.DictReader(open(REPORTED[split], encoding="utf-8"))}
    for v in VIEWS:
        mine = M.auroc([score[(g, v)] for g in IDS[split]], [Y(g) for g in IDS[split]])
        chk[f"{split}/{v}"] = abs(mine - rep[v]) < 1e-9
res["reproduces_reported_auroc"] = all(chk.values())
assert res["reproduces_reported_auroc"], chk

# 1. dev vs test: unpaired bootstrap of AUROC(test) - AUROC(dev); one stratified resample over (split, type) strata
both = IDS["dev"] + IDS["test"]
strata = [(("d" if g in SPLIT["dev"] else "t"), T(g)) for g in both]
nd = len(IDS["dev"])
stab = {}
for v in VIEWS:
    s, y = [score[(g, v)] for g in both], [Y(g) for g in both]

    def stat(idx, s=s, y=y):
        di, ti = [i for i in idx if i < nd], [i for i in idx if i >= nd]
        a, b = M.auroc([s[i] for i in ti], [y[i] for i in ti]), M.auroc([s[i] for i in di], [y[i] for i in di])
        return None if a is None or b is None else a - b
    dev_auc = M.auroc(s[:nd], y[:nd])
    test_auc = M.auroc(s[nd:], y[nd:])
    stab[v] = {"dev": r3(dev_auc), "test": r3(test_auc), "test_minus_dev": ci(M.bootstrap_ci(stat, strata, B, SEED))}
dev_v, test_v = [stab[v]["dev"] for v in VIEWS], [stab[v]["test"] for v in VIEWS]
rank = lambda xs: {v: 1 + sum(x > xs[i] for x in xs) for i, v in enumerate(VIEWS)}  # 1 = best, ties share
res["stability"] = {"per_view": stab, "rank_dev": rank(dev_v), "rank_test": rank(test_v),
                    "kendall_tau_b": r3(M.kendall_tau(dev_v, test_v)), "n_views": len(VIEWS)}

# 2. pooled 48 games (stratified by episode type)
P = IDS["pooled"]
res["pooled"] = {"n": len(P), "note": "dev games were used for the format choice and the thresholds; AUROC is threshold-free, "
                                      "but the pooled numbers include selection data",
                 "per_view": {v: per_view_auroc(P, lambda g, v=v: score[(g, v)])[1] for v in VIEWS},
                 "per_type": {v: per_type(P, lambda g, v=v: score[(g, v)]) for v in VIEWS},
                 "paired": {f"{a} - {b}": paired(P, a, b) for a, b in
                            (("V3", "V2"), ("V3", "V1"), ("V4", "V3"), ("V4", "C-length"), ("V5", "V3"), ("V3", "C-mismatch"))}}

# 3. extra test comparison (not pre-registered)
res["test_V3_minus_V1"] = paired(IDS["test"], "V3", "V1")

# 4. code signals (game-level max over pairs), test and pooled, plus V4 for reference
cs = {}
for split in ("test", "pooled"):
    cs[split] = {}
    for s in SIGS + ("V4",):
        get = (lambda g: score[(g, "V4")]) if s == "V4" else (lambda g, s=s: SIG[g][s])
        gs, a = per_view_auroc(IDS[split], get)
        t4 = [g for g in gs if T(g) in (1, 4)]
        cs[split][s] = a | {"n": len(gs), "n_na": len(IDS[split]) - len(gs),
                            "T1_vs_T4b": ci(M.bootstrap_auroc([get(g) for g in t4], [Y(g) for g in t4], [T(g) for g in t4], B, SEED))
                            | {"n": len(t4)}}
res["code_signals"] = cs

# per-game data for figures / excerpts
res["games"] = {g: {"split": "dev" if g in SPLIT["dev"] else "test", "type": T(g), "y": Y(g),
                    "scores": {v: score[(g, v)] for v in VIEWS}, "signals": SIG[g]} for g in P}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

# tables.md
f = lambda d: f"{d['estimate']:.3f} [{d['ci'][0]:.3f}, {d['ci'][1]:.3f}]" if d["estimate"] is not None else "NA"
L = ["# Task 15 tables (EXPLORATORY, not pre-registered)", "", "## 1. Dev vs test", "",
     "| View | Dev AUROC | Test AUROC | Test − dev [95% CI] | Rank dev | Rank test |", "|---|---|---|---|---|---|"]
for v in VIEWS:
    x = stab[v]
    L.append(f"| {v} | {x['dev']:.3f} | {x['test']:.3f} | {f(x['test_minus_dev'])} | {res['stability']['rank_dev'][v]} | {res['stability']['rank_test'][v]} |")
L += ["", f"Kendall tau-b (dev vs test AUROC over 8 views): {res['stability']['kendall_tau_b']}", "",
      "## 2. Pooled 48 games", "", "| View | AUROC [CI] | T1 vs T2 | T1 vs T3 | T1 vs T4b |", "|---|---|---|---|---|"]
for v in VIEWS:
    pt = res["pooled"]["per_type"][v]
    L.append(f"| {v} | {f(res['pooled']['per_view'][v])} | {f(pt['T1_vs_T2'])} | {f(pt['T1_vs_T3'])} | {f(pt['T1_vs_T4'])} |")
L += ["", "| Pooled paired difference | Estimate [CI] |", "|---|---|"]
L += [f"| {k} | {f(d)} |" for k, d in res["pooled"]["paired"].items()]
L += ["", f"## 3. Test V3 − V1: {f(res['test_V3_minus_V1'])}", "", "## 4. Code signals", "",
      "| Signal | Test AUROC [CI] (n) | Test T1 vs T4b | Pooled AUROC [CI] (n) | Pooled T1 vs T4b |", "|---|---|---|---|---|"]
for s in SIGS + ("V4",):
    a, b = cs["test"][s], cs["pooled"][s]
    L.append(f"| {s} | {f(a)} ({a['n']}) | {f(a['T1_vs_T4b'])} ({a['T1_vs_T4b']['n']}) | {f(b)} ({b['n']}) | {f(b['T1_vs_T4b'])} ({b['T1_vs_T4b']['n']}) |")
(OUT / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
