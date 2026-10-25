"""Task 17C: Study 2.3 test results (RQ-E1..E5), the exploratory plus-factor rule and judge diagnostics.

  conda run -n collusion-lab python -B scratch/p17c_analysis.py      -> runs/study23/results.json, runs/study23/tables.md

Reads the ONE frozen test application (runs/study23/test_decisions.csv, written by analyse_23.py --mode test) and
re-applies the frozen rules in memory only to assert that the CSV matches. Nothing is fitted on test: the plus-factor
thresholds come from runs/study23/preconditions.json (dev only, recorded in the DEVLOG before this script ran).
CIs: 95% stratified bootstrap by episode type, B = 2000, seed 20261023; paired comparisons share resample indices.
Games with an NA score are left out of that score's AUROC (n stated).
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT, load_json  # noqa: E402
from core.evidence.signals import HonestBaseline, game_signals, pair_signal_table  # noqa: E402
from core.labels import read_labels  # noqa: E402
from core.stats import metrics as M  # noqa: E402
from study_2_3_evidence import rules as R  # noqa: E402
from study_2_3_evidence.judge import load_judge  # noqa: E402

SHA = "ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5"
FROZEN = REPO_ROOT / "configs/frozen/rules_frozen.json"
OUT = REPO_ROOT / "runs/study23"
TYPE_NAME = {1: "T1", 2: "T2", 3: "T3", 4: "T4b"}
SCORE = {"R1": "R1_score", "R2": "R2_score", "R3": "R3_score", "R6": "R6_points", "R7": "R7_prob"}
SIGNAL_NAME = {"R1": "C_judge (E1)", "R2": "G_others (E2)", "R3": "Dep (E3)", "R6": "points", "R7": "probability"}
ABL = [f"no_{f}" for f in R.FAMILIES]


def num(v):
    return None if v in ("", None) else float(v)


fz = R.load_frozen(FROZEN, SHA)
labels = {lb.game_id: lb for lb in read_labels(REPO_ROOT / "data/labels.csv")}
test = sorted(load_json(REPO_ROOT / "data/split.json")["test"])
with open(OUT / "test_decisions.csv", encoding="utf-8") as f:
    dec = {r["game_id"]: r for r in csv.DictReader(f)}
assert sorted(dec) == test

# ---- re-derive the test signal table (frozen dev baseline) and check the CSV against an in-memory re-application
base = HonestBaseline(**fz["honest_baseline"])
j0 = load_judge(REPO_ROOT / fz["judge"]["judge_jsonl"], 0)
games = {}
for g in test:
    rows = pair_signal_table(load_json(REPO_ROOT / "data/clean" / f"{g}.json"), base)
    for r in rows:
        r["C_judge"] = j0[g]["pair_scores"][r["pair"]]
    games[g] = rows
again = R.apply_frozen(FROZEN, SHA, games, test, judge_prompt_version=fz["judge"]["prompt_version"])
for g in test:
    for k, v in again[g].items():
        assert int(dec[g][f"{k}_flag"]) == v["flag"], (g, k)
gsig = {g: game_signals(games[g]) for g in test}

y = [labels[g].collusion for g in test]
types = [labels[g].episode_type for g in test]
idx_all = list(range(len(test)))


def flags_of(name):
    return [int(dec[g][f"{name}_flag"]) for g in test]


def score_of(name):
    col = SCORE.get(name) or (f"{name}_{'points' if name.startswith('R6') else 'prob'}" if "_no_" in name else None)
    return None if col is None else [num(dec[g][col]) for g in test]


def ba(flags):
    return lambda idx: R.binary_metrics([flags[i] for i in idx], [y[i] for i in idx])["balanced_accuracy"]


def auroc_on(scores):
    def stat(idx):
        keep = [i for i in idx if scores[i] is not None]
        return M.auroc([scores[i] for i in keep], [y[i] for i in keep]) if keep else None
    return stat


def ci(d):
    return None if d is None else {k: d[k] for k in ("estimate", "ci_low", "ci_high", "b_na")}


def per_type(flags):
    out = {}
    for t in (1, 2, 3, 4):
        f = [fl for fl, tt in zip(flags, types) if tt == t]
        k = sum(f)
        out[TYPE_NAME[t]] = {"k": k, "n": len(f), "rate": k / len(f),
                             "upper95_rule_of_three": M.rule_of_three_upper(len(f)) if k == 0 else None}
    return out


def rule_block(name, flags, scores):
    m = R.binary_metrics(flags, y)
    out = {k: m[k] for k in ("tp", "fp", "tn", "fn", "accuracy", "tpr", "fpr", "balanced_accuracy")}
    out["per_type"] = per_type(flags)
    out["ba_ci"] = ci(M.bootstrap_ci(ba(flags), types))
    if scores is not None:
        out["n_auroc"] = sum(s is not None for s in scores)
        out["auroc"] = ci(M.bootstrap_ci(auroc_on(scores), types))
    return out


def paired(fa, fb):
    """(stat_a, stat_b) -> paired CI of a - b."""
    return ci(M.paired_bootstrap_diff(fa, fb, types))


def common(sa, sb):
    keep = [i for i in idx_all if sa[i] is not None and sb[i] is not None]
    return [sa[i] if i in keep else None for i in idx_all], [sb[i] if i in keep else None for i in idx_all], len(keep)


res = {"frozen_sha256": SHA, "n_test": len(test), "n_pos": sum(y),
       "ci": "95% stratified bootstrap by episode type, B=2000, seed 20261023"}

# ---- RQ-E1/E2: every rule
res["rules"] = {r: rule_block(r, flags_of(r), score_of(r)) for r in R.RULES}

# ---- RQ-E3 (primary): best combined (R6) vs best single (R2), dev choices from preconditions.json
pre = load_json(OUT / "preconditions.json")
assert pre["all_ok"]
bc, bs = pre["dev_choices"]["best_combined"], pre["dev_choices"]["best_single"]
sa, sb, n_c = common(score_of(bc), score_of(bs))
d_auc = paired(auroc_on(sa), auroc_on(sb))
lo, hi = d_auc["ci_low"], d_auc["ci_high"]
wording = ("combining evidence helps" if lo > 0 else "combining hurts" if hi < 0
           else "no clear difference at this sample size")
res["rq_e3"] = {"best_combined": bc, "best_single": bs, "n": n_c, "auroc_diff": d_auc, "verdict": wording,
                "ba_diff_descriptive": paired(ba(flags_of(bc)), ba(flags_of(bs)))}

# ---- RQ-E4: ablations; RQ-E5: the no-E4 ablations vs the full rules
res["ablations"] = {}
for a in ABL:
    for r in ("R6", "R7"):
        name = f"{r}_{a}"
        blk = rule_block(name, flags_of(name), score_of(name))
        fs, ab, n_p = common(score_of(r), score_of(name))
        blk["auroc_diff_full_minus_ablation"] = {**paired(auroc_on(fs), auroc_on(ab)), "n": n_p}
        blk["ba_diff_full_minus_ablation"] = paired(ba(flags_of(r)), ba(flags_of(name)))
        blk["frozen_param"] = ({"k": fz["ablations"][a]["R6"]["k"]} if r == "R6"
                               else {"C": fz["ablations"][a]["R7"]["C"], "coef": fz["ablations"][a]["R7"]["coef"]})
        blk["n_flagged"] = sum(flags_of(name))
        res["ablations"][name] = blk
res["rq_e5"] = {r: {k: res["ablations"][f"{r}_no_E4"][k] for k in ("auroc_diff_full_minus_ablation",
                                                                    "ba_diff_full_minus_ablation")}
                for r in ("R6", "R7")}
p_r7 = score_of("R7_no_E2")
res["r7_no_E2_artefact_check"] = {"coef": fz["ablations"]["no_E2"]["R7"]["coef"],
                                  "test_prob_min": min(p_r7), "test_prob_max": max(p_r7)}

# ---- exploratory plus-factor rule (dev thresholds from preconditions.json)
pf = pre["plus_factor_dev"]
pf_flags = [int(R._ge(gsig[g]["capture"], pf["capture_threshold"]) and R._ge(gsig[g]["C_kw"], pf["C_kw_threshold"]))
            for g in test]
cap_flags = [int(R._ge(gsig[g]["capture"], pf["capture_threshold"])) for g in test]
res["exploratory_plus_factor"] = {
    "label": "post hoc, motivated by report 15 §4.4; not pre-registered",
    "capture_threshold": pf["capture_threshold"], "C_kw_threshold": pf["C_kw_threshold"],
    "plus_factor_rule": rule_block("plus", pf_flags, None),
    "capture_alone": rule_block("capture", cap_flags, [gsig[g]["capture"] for g in test]),
    "C_kw_test_values": {g: gsig[g]["C_kw"] for g in test}, "capture_test_values": {g: gsig[g]["capture"] for g in test}}

# ---- judge diagnostics (descriptive)
jd = {"game_max_by_type": {TYPE_NAME[t]: sorted(j0[g]["score"] for g, tt in zip(test, types) if tt == t)
                           for t in (1, 2, 3, 4)}}
t1 = [g for g, t in zip(test, types) if t == 1]
def focal(g):
    return "-".join(sorted(labels[g].focal_pair))
top = {g: ("-".join(j0[g]["top_pair"]) if j0[g]["top_pair"] else None) for g in t1}
jd["type1_top_pair_is_focal"] = sum(top[g] == focal(g) for g in t1)
jd["type1_top_pair_tie"] = sum(top[g] is None for g in t1)
jd["type1_n"] = len(t1)
jd["type1_detail"] = {g: {"focal": focal(g), "judge_top": top[g], "judge_focal_score": j0[g]["pair_scores"][focal(g)],
                          "judge_max": j0[g]["score"]} for g in t1}
jd["share_games_max_ge_98"] = sum(j0[g]["score"] >= 98 for g in test) / len(test)
res["judge_diagnostics"] = jd
res["per_game"] = {g: {"type": TYPE_NAME[t], "y": yy, **{f"{r}_flag": int(dec[g][f"{r}_flag"]) for r in R.RULES},
                       **{SCORE[r]: num(dec[g][SCORE[r]]) for r in SCORE}, "plus_factor_flag": pf_flags[i],
                       "capture": gsig[g]["capture"], "C_kw": gsig[g]["C_kw"]}
                   for i, (g, t, yy) in enumerate(zip(test, types, y))}

(OUT / "results.json").write_text(json.dumps(R._jsonable(res), indent=1) + "\n", encoding="utf-8")


# ---- tables.md
def f3(v):
    return "—" if v is None else f"{v:.3f}"


def c3(d):
    return "—" if d is None else f"{f3(d['estimate'])} [{f3(d['ci_low'])}, {f3(d['ci_high'])}]"


def kn(pt, t):
    x = pt[t]
    s = f"{x['k']}/{x['n']}"
    return s + (f" (≤{x['upper95_rule_of_three']:.2f})" if x["upper95_rule_of_three"] is not None else "")


L = ["## RQ-E1/E2 rules on test (n = 24; 12 pos)", "",
     "| Rule | Score | AUROC [CI] (n) | Acc | TPR | FPR | BA | T1 | T2 | T3 | T4b |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for r, b in res["rules"].items():
    au = f"{c3(b['auroc'])} ({b['n_auroc']})" if "auroc" in b else "—"
    L.append(f"| {r} | {SIGNAL_NAME.get(r, 'binary')} | {au} | {f3(b['accuracy'])} | {f3(b['tpr'])} | {f3(b['fpr'])} | "
             f"{f3(b['balanced_accuracy'])} | " + " | ".join(kn(b["per_type"], t) for t in ("T1", "T2", "T3", "T4b")) + " |")
e3 = res["rq_e3"]
L += ["", f"## RQ-E3: {bc} − {bs}", "", f"AUROC diff {c3(e3['auroc_diff'])} (n {e3['n']}) → **{e3['verdict']}**; "
      f"BA diff (descriptive) {c3(e3['ba_diff_descriptive'])}", "",
      "## RQ-E4/E5 ablations", "", "| Ablation | Param | AUROC [CI] | BA | TPR | FPR | flagged | ΔAUROC full−abl | ΔBA full−abl |",
      "|---|---|---|---|---|---|---|---|---|"]
for n, b in res["ablations"].items():
    L.append(f"| {n} | {b['frozen_param'] if 'k' in b['frozen_param'] else 'C=' + str(b['frozen_param']['C'])} | "
             f"{c3(b['auroc'])} | {f3(b['balanced_accuracy'])} | {f3(b['tpr'])} | {f3(b['fpr'])} | {b['n_flagged']} | "
             f"{c3(b['auroc_diff_full_minus_ablation'])} | {c3(b['ba_diff_full_minus_ablation'])} |")
ep = res["exploratory_plus_factor"]
L += ["", "## Exploratory plus-factor rule (post hoc; not pre-registered)", "",
      "| Rule | TPR | FPR | BA | T1 | T2 | T3 | T4b |", "|---|---|---|---|---|---|---|---|"]
for n in ("plus_factor_rule", "capture_alone"):
    b = ep[n]
    L.append(f"| {n} | {f3(b['tpr'])} | {f3(b['fpr'])} | {f3(b['balanced_accuracy'])} | "
             + " | ".join(kn(b["per_type"], t) for t in ("T1", "T2", "T3", "T4b")) + " |")
L += ["", "## Judge diagnostics", "", json.dumps({k: v for k, v in jd.items() if k != "type1_detail"}), ""]
(OUT / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
