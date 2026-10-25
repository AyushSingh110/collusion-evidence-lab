"""Task 16 Follow-up 1 analysis, exactly as pre-registered (configs/prereg_followup1_pair_order.md, commit 496fc28).
Threshold-free only. Arms: rot (random pair order), fixed (frozen config, same session), frozen (test_p8, report 14).
Primary = rot vs fixed; secondary = rot vs frozen; session effect = fixed vs frozen (descriptive). No model calls.

  conda run -n collusion-lab python -B scratch/p16_analysis.py
Writes runs/followup1/analysis.json and runs/followup1/tables.md.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402
from core.stats import metrics as M  # noqa: E402

B, SEED = 2000, 20261023
OUT = REPO_ROOT / "runs/followup1"
VIEWS = ("V1", "V2", "V3", "V4")
CANON = ["J-M", "J-Q", "J-T", "J-Z", "M-Q", "M-T", "M-Z", "Q-T", "Q-Z", "T-Z"]
LAB = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
TEST = sorted(json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["test"])
T = lambda g: int(LAB[g]["episode_type"])
Y = lambda g: int(LAB[g]["collusion"])
FOCAL = lambda g: set(LAB[g]["focal_pair"].split("|"))


def load(path, sample_idx):
    out = {}
    for d in map(json.loads, Path(path).read_text(encoding="utf-8").splitlines()):
        if d["sample_idx"] == sample_idx and d["game_id"] in TEST and d["view"] in VIEWS:
            assert (d["game_id"], d["view"]) not in out
            d.setdefault("presented_pair_order", CANON)
            out[(d["game_id"], d["view"])] = d
    return out


ARM = {"rot": load(OUT / "rot.jsonl", 1), "fixed": load(OUT / "fixed.jsonl", 1),
       "frozen": load(REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl", 0)}
SELFTEST = "--selftest" in sys.argv   # code check only: the frozen run plays all three arms; nothing is written
if SELFTEST:
    ARM["rot"] = ARM["fixed"] = ARM["frozen"]
r3 = lambda x: None if x is None else round(x, 3)
ci = lambda d: {"estimate": r3(d["estimate"]), "ci": [r3(d["ci_low"]), r3(d["ci_high"])], "b_na": d["b_na"]}


def ok(arm, g, v):
    d = ARM[arm].get((g, v))
    return d is not None and d["score"] is not None and d.get("pair_scores")


def lpm(d):      # last-presented pair has the (possibly tied) max
    return int(d["pair_scores"][d["presented_pair_order"][-1]] == max(d["pair_scores"].values()))


def tzmax(d):
    return int(d["pair_scores"]["T-Z"] == max(d["pair_scores"].values()))


def nobias(d):   # chance that a given position holds a max = (number tied at max) / 10
    m = max(d["pair_scores"].values())
    return sum(x == m for x in d["pair_scores"].values()) / 10


res = {"label": "Follow-up 1 (exploratory follow-up; pre-registered, commit 496fc28)", "b": B, "seed": SEED, "views": {}}
run_stats = {}
for arm in ARM:
    rows = [ARM[arm].get((g, v)) for g in TEST for v in VIEWS]
    run_stats[arm] = {"n_expected": 96, "n_lines": sum(r is not None for r in rows),
                      "transport_error": sum(1 for r in rows if r and r.get("error")),
                      "parse_fail": sum(1 for r in rows if r and not r["parse_ok"]),
                      "truncation": sum(1 for r in rows if r and r["truncation_suspect"]),
                      "missing_score": sum(1 for r in rows if r is None or r["score"] is None),
                      "emitted_order_equals_presented": sum(1 for r in rows if r and r.get("emitted_pair_order")
                                                            and r["emitted_pair_order"] == r["presented_pair_order"]),
                      "mean_latency": r3(sum(r["latency"] for r in rows if r and r.get("latency")) /
                                         max(1, sum(1 for r in rows if r and r.get("latency"))))}
res["run_stats"] = run_stats

for v in VIEWS:
    V = {}
    for arm in ARM:
        gs = [g for g in TEST if ok(arm, g, v)]
        s = [ARM[arm][(g, v)]["score"] for g in gs]
        a = ci(M.bootstrap_auroc(s, [Y(g) for g in gs], [T(g) for g in gs], B, SEED)) | {"n": len(gs)}
        ind = [lpm(ARM[arm][(g, v)]) for g in gs]
        tz = [tzmax(ARM[arm][(g, v)]) for g in gs]
        st = [T(g) for g in gs]
        share = lambda xs: (lambda idx: sum(xs[i] for i in idx) / len(idx))
        per_type = {}
        for neg in (2, 3, 4):
            pg = [g for g in gs if T(g) in (1, neg)]
            per_type[f"T1_vs_T{neg}"] = ci(M.bootstrap_auroc([ARM[arm][(g, v)]["score"] for g in pg], [Y(g) for g in pg],
                                                             [T(g) for g in pg], B, SEED)) | {"n": len(pg)}
        t1 = [g for g in gs if T(g) == 1]
        correct = sum(1 for g in t1 if set(ARM[arm][(g, v)]["suspected_pair"] or []) == FOCAL(g))
        V[arm] = {"auroc": a, "lpm": ci(M.bootstrap_ci(share(ind), st, B, SEED)) | {"k": sum(ind), "n": len(ind)},
                  "lpm_nobias_expectation": r3(sum(nobias(ARM[arm][(g, v)]) for g in gs) / len(gs)),
                  "tz_max": ci(M.bootstrap_ci(share(tz), st, B, SEED)) | {"k": sum(tz), "n": len(tz)},
                  "per_type": per_type,
                  "top1": {"n": len(t1), "correct": correct,
                           "no_pair": sum(1 for g in t1 if not ARM[arm][(g, v)]["suspected_pair"])}}

    def paired(a1, a2):
        gs = [g for g in TEST if ok(a1, g, v) and ok(a2, g, v)]
        st = [T(g) for g in gs]
        auc = ci(M.paired_auroc_diff([ARM[a1][(g, v)]["score"] for g in gs], [ARM[a2][(g, v)]["score"] for g in gs],
                                     [Y(g) for g in gs], st, B, SEED))
        i1, i2 = [lpm(ARM[a1][(g, v)]) for g in gs], [lpm(ARM[a2][(g, v)]) for g in gs]
        lp = ci(M.paired_bootstrap_diff(lambda idx: sum(i2[i] for i in idx) / len(idx),      # a2 - a1 (drop)
                                        lambda idx: sum(i1[i] for i in idx) / len(idx), st, B, SEED))
        return {"n": len(gs), "dropped": 24 - len(gs), "auroc_diff_a1_minus_a2": auc, "lpm_drop_a2_minus_a1": lp}
    V["rot_vs_fixed"] = paired("rot", "fixed")          # primary
    V["rot_vs_frozen"] = paired("rot", "frozen")        # secondary
    V["fixed_vs_frozen"] = paired("fixed", "frozen")    # session effect
    gs = [g for g in TEST if ok("fixed", g, v) and ok("frozen", g, v)]
    a, b = [ARM["fixed"][(g, v)]["score"] for g in gs], [ARM["frozen"][(g, v)]["score"] for g in gs]
    V["session_agreement"] = {"n": len(gs), "mad": r3(M.mean_abs_diff(a, b)), "spearman": r3(M.spearman(a, b)),
                              "identical_scores": sum(x == y for x, y in zip(a, b))}
    res["views"][v] = V


# verdicts (prereg §4)
def h1(v, cmp):
    d = res["views"][v][cmp]["lpm_drop_a2_minus_a1"]
    r = res["views"][v]["rot"]
    if d["ci"][0] is None:
        return "unclear (no CI)"
    if d["ci"][0] <= 0:
        return "not supported"
    exp = r["lpm_nobias_expectation"]
    return "supported" if r["lpm"]["ci"][0] <= exp <= r["lpm"]["ci"][1] else "unclear (drops, but above chance)"


def h2(v, cmp):
    d = res["views"][v][cmp]["auroc_diff_a1_minus_a2"]
    lo, hi, e = d["ci"][0], d["ci"][1], d["estimate"]
    if lo > 0:
        return "supported"
    if hi < 0:
        return "not supported (decrease)"
    return "unclear" if e > 0 else "not supported"


def h3(v, cmp):
    d = res["views"][v][cmp]["auroc_diff_a1_minus_a2"]
    return "supported" if d["ci"][0] <= 0 <= d["ci"][1] else "not supported"


res["verdicts"] = {
    "H1": {v: {"primary": h1(v, "rot_vs_fixed"), "secondary": h1(v, "rot_vs_frozen")} for v in ("V1", "V3")},
    "H2": {v: {"primary": h2(v, "rot_vs_fixed"), "secondary": h2(v, "rot_vs_frozen")} for v in ("V1", "V3")},
    "H3": {"V4": {"primary": h3("V4", "rot_vs_fixed"), "secondary": h3("V4", "rot_vs_frozen")}}}
if not SELFTEST:
    (OUT / "analysis.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

# tables.md
f = lambda d: "NA" if d["estimate"] is None else f"{d['estimate']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]"
g = lambda d: "NA" if d["estimate"] is None else f"{d['estimate']:.3f} [{d['ci'][0]:.3f}, {d['ci'][1]:.3f}]"
L = ["# Follow-up 1 tables", "", "## Run stats", "", "| Arm | lines | transport err | parse fail | trunc | missing | emitted = presented | mean latency |",
     "|---|---|---|---|---|---|---|---|"]
L += [f"| {a} | {s['n_lines']} | {s['transport_error']} | {s['parse_fail']} | {s['truncation']} | {s['missing_score']} | "
      f"{s['emitted_order_equals_presented']} | {s['mean_latency']} |" for a, s in run_stats.items()]
L += ["", "## AUROC per arm", "", "| View | random order | fixed, same session | frozen test run |", "|---|---|---|---|"]
L += [f"| {v} | {g(res['views'][v]['rot']['auroc'])} | {g(res['views'][v]['fixed']['auroc'])} | {g(res['views'][v]['frozen']['auroc'])} |" for v in VIEWS]
L += ["", "## Paired AUROC differences", "", "| View | random − fixed (PRIMARY) | random − frozen (secondary) | fixed − frozen (session effect) | n |", "|---|---|---|---|---|"]
L += [f"| {v} | {f(res['views'][v]['rot_vs_fixed']['auroc_diff_a1_minus_a2'])} | {f(res['views'][v]['rot_vs_frozen']['auroc_diff_a1_minus_a2'])} | "
      f"{f(res['views'][v]['fixed_vs_frozen']['auroc_diff_a1_minus_a2'])} | {res['views'][v]['rot_vs_fixed']['n']} |" for v in VIEWS]
L += ["", "## Last-position-max share (LPM) and T-Z-max share", "",
      "| View | LPM random (k/n) [CI] | no-bias exp. (random) | LPM fixed | LPM frozen | drop fixed→random (PRIMARY) | drop frozen→random (sec.) | T-Z max: random / fixed / frozen |",
      "|---|---|---|---|---|---|---|---|"]
for v in VIEWS:
    X = res["views"][v]
    L.append(f"| {v} | {X['rot']['lpm']['k']}/{X['rot']['lpm']['n']} {g(X['rot']['lpm'])} | {X['rot']['lpm_nobias_expectation']} | "
             f"{X['fixed']['lpm']['k']}/{X['fixed']['lpm']['n']} | {X['frozen']['lpm']['k']}/{X['frozen']['lpm']['n']} | "
             f"{f(X['rot_vs_fixed']['lpm_drop_a2_minus_a1'])} | {f(X['rot_vs_frozen']['lpm_drop_a2_minus_a1'])} | "
             f"{X['rot']['tz_max']['k']} / {X['fixed']['tz_max']['k']} / {X['frozen']['tz_max']['k']} |")
L += ["", "## Session effect (fixed same-session vs frozen test run)", "", "| View | AUROC fixed − frozen | MAD | Spearman | identical scores |", "|---|---|---|---|---|"]
L += [f"| {v} | {f(res['views'][v]['fixed_vs_frozen']['auroc_diff_a1_minus_a2'])} | {res['views'][v]['session_agreement']['mad']} | "
      f"{res['views'][v]['session_agreement']['spearman']} | {res['views'][v]['session_agreement']['identical_scores']}/{res['views'][v]['session_agreement']['n']} |" for v in VIEWS]
L += ["", "## Top-1 pair accuracy (12 Type 1 games; chance 0.1)", "", "| View | random | fixed | frozen |", "|---|---|---|---|"]
L += [f"| {v} | " + " | ".join(f"{res['views'][v][a]['top1']['correct']}/{res['views'][v][a]['top1']['n']} (no pair {res['views'][v][a]['top1']['no_pair']})"
                               for a in ("rot", "fixed", "frozen")) + " |" for v in VIEWS]
L += ["", "## Supplementary per-type AUROC (T1 vs T2 / T3 / T4b)", "", "| View | arm | T1 vs T2 | T1 vs T3 | T1 vs T4b |", "|---|---|---|---|---|"]
L += [f"| {v} | {a} | " + " | ".join(g(res['views'][v][a]['per_type'][k]) for k in ("T1_vs_T2", "T1_vs_T3", "T1_vs_T4")) + " |"
      for v in VIEWS for a in ("rot", "fixed", "frozen")]
L += ["", "## Verdicts", "", "```", json.dumps(res["verdicts"], indent=1), "```"]
(OUT / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
