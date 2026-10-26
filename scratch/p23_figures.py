"""Task 23: fig9 (Study 2.2 AUROC per view, original test vs replication; llama and granite; plus capture) and fig10
(Study 2.3 rules, 17C vs replication). Re-plots stored results only; no new analysis on any game.

Sources (all local result files, except the 17C originals, copied from report 17C §4.1 = writeup/results_23.md §1-2):
  original llama test   runs/test_p8/rq1_per_view_test.csv (report 14 §4.2); capture test runs/p15/results.json (R15 §4.4)
  replication llama     runs/replication_granite/results.json descriptive.llama (R22C §4.4), checked against
                        runs/replication/analysis_22/replication_22.json R1 / R2 (report 21 §4.7); capture = R10a
  replication granite   runs/replication_granite/results.json descriptive.granite (R22C §4.4)
  Study 2.3 replication runs/replication_23/results.json auroc (R22C §4.2)

  conda run -n collusion-lab python -B scratch/p23_figures.py
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

FIG = REPO_ROOT / "writeup/figures"
J = lambda p: json.loads((REPO_ROOT / p).read_text(encoding="utf-8"))
orig = {r["view"]: (float(r["auroc"]), float(r["ci_low"]), float(r["ci_high"]))
        for r in csv.DictReader(open(REPO_ROOT / "runs/test_p8/rq1_per_view_test.csv", encoding="utf-8"))}
cap_t = J("runs/p15/results.json")["code_signals"]["test"]["capture"]
orig["capture"] = (cap_t["estimate"], *cap_t["ci"])
G = J("runs/replication_granite/results.json")["primary"]["descriptive"]
R22 = {h["id"]: h for h in J("runs/replication/analysis_22/replication_22.json")["primary"]["hypotheses"]}
trip = lambda a: (a["estimate"], a["ci_low"], a["ci_high"])
rep_l = {v: trip(G["llama"][v]["auroc"]) for v in ("V1", "V2", "V3", "V4")}
rep_g = {v: trip(G["granite"][v]["auroc"]) for v in ("V1", "V2", "V3", "V4")}
rep_l["capture"] = trip(R22["R10a"])
# consistency: C's llama numbers must equal B's own analysis (report 21)
for hid, v in (("R1", "V1"), ("R2", "V4")):
    assert abs(rep_l[v][0] - R22[hid]["estimate"]) < 1e-3, (hid, rep_l[v], R22[hid])
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# fig9
cats = ["V1", "V2", "V3", "V4", "capture"]
names = ["V1\nmessages", "V2\nactions", "V3\ncombined", "V4\nstructured", "capture\n(code, no LLM)"]
series = [("llama, original test (n = 24)", orig, "#95a5a6", -0.25),
          ("llama, replication (n = 48)", rep_l, "#34495e", 0.0),
          ("granite, replication (n = 48)", rep_g, "#c0392b", 0.25)]
fig, ax = plt.subplots(figsize=(9, 4.3))
x = np.arange(len(cats))
for lab, d, c, off in series:
    xs = [i + off for i, k in enumerate(cats) if k in d]
    e = np.array([d[k][0] for k in cats if k in d])
    lo, hi = np.array([d[k][1] for k in cats if k in d]), np.array([d[k][2] for k in cats if k in d])
    ax.errorbar(xs, e, yerr=[e - lo, hi - e], fmt="o", color=c, capsize=3, label=lab)
ax.axhline(0.5, ls="--", color="grey", lw=1)
ax.text(len(cats) - 0.45, 0.51, "chance", ha="right", va="bottom", color="grey", fontsize=8)
ax.axvline(3.5, color="lightgrey", lw=1)
ax.set_xticks(x, names)
ax.set_ylim(0, 1.05)
ax.set_ylabel("AUROC with 95% CI")
ax.set_title("Study 2.2: original test vs pre-registered replication (frozen prompts)")
ax.set_ylim(0, 1.15)
ax.set_yticks(np.arange(0, 1.01, 0.2))
ax.legend(fontsize=8, loc="upper center", ncol=3)
fig.tight_layout()
fig.savefig(FIG / "fig9_replication_22.png", dpi=150)
plt.close(fig)

# fig10: 17C values copied from report 17C (writeup/results_23.md sections 1-2)
o23 = {"R1": (0.396, 0.205, 0.597), "R2": (0.872, 0.736, 0.986), "R3": (0.736, 0.491, 0.942),
       "R6": (0.792, 0.667, 0.917), "R7": (0.812, 0.611, 0.972)}
A = J("runs/replication_23/results.json")["primary"]["auroc"]
r23 = {k: trip(A[k]) for k in o23}
rules = ["R1", "R2", "R3", "R6", "R7"]
rnames = ["R1\njudge (talk)", "R2\ncoalition gain", "R3\ndependence", "R6\npoints", "R7\nlearned"]
fig, ax = plt.subplots(figsize=(8, 4.2))
x = np.arange(len(rules))
for lab, d, c, off in (("original test, 17C (n = 24)", o23, "#95a5a6", -0.15),
                       ("replication (n = 48)", r23, "#34495e", 0.15)):
    e = np.array([d[k][0] for k in rules])
    ax.errorbar(x + off, e, yerr=[e - [d[k][1] for k in rules], [d[k][2] for k in rules] - e], fmt="o", color=c,
                capsize=3, label=lab)
ax.axhline(0.5, ls="--", color="grey", lw=1)
ax.set_xticks(x, rnames)
ax.set_ylim(0, 1.05)
ax.set_ylabel("AUROC with 95% CI")
ax.set_title("Study 2.3: frozen decision rules, original test vs replication")
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "fig10_replication_23.png", dpi=150)
plt.close(fig)
for k in cats:
    print(k, "orig", [round(v, 3) for v in orig[k]], "rep llama", [round(v, 3) for v in rep_l[k]],
          "rep granite", [round(v, 3) for v in rep_g[k]] if k in rep_g else "-")
for k in rules:
    print(k, "17C", o23[k], "rep", [round(v, 3) for v in r23[k]])
print("wrote fig9, fig10")
