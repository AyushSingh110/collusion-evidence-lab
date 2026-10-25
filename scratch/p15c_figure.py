"""Task 15C Figure 8 (PNG, 150 dpi): RQ9 AUROC per view, llama (report 14) vs granite, with 95% CIs; and the
last-position-max share per view for both models. Reads runs/rq9_granite/results.json (run p15c_analysis.py first).

  conda run -n collusion-lab python -B scratch/p15c_figure.py
"""
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
VIEWS = ("V1", "V2", "V3", "V4")
R = json.loads((REPO_ROOT / "runs/rq9_granite/results.json").read_text(encoding="utf-8"))
LL = R["llama_reference"]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
C_LLAMA, C_GRANITE = "#34495e", "#c0392b"

fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [3, 2]})
x = np.arange(len(VIEWS))
w = 0.38
for off, name, col, vals in (
        (-w / 2, "llama3.1:8b (report 14)", C_LLAMA, [LL["auroc"][v] for v in VIEWS]),
        (w / 2, "granite3.3:8b (RQ9)", C_GRANITE,
         [(R["views"][v]["auroc"]["estimate"], R["views"][v]["auroc"]["ci_low"], R["views"][v]["auroc"]["ci_high"])
          for v in VIEWS])):
    est = [t[0] for t in vals]
    a1.bar(x + off, est, w, color=col, label=name)
    a1.errorbar(x + off, est, yerr=[[t[0] - t[1] for t in vals], [t[2] - t[0] for t in vals]], fmt="none",
                ecolor="black", capsize=3)
a1.axhline(0.5, ls="--", color="grey", lw=1)
a1.text(-0.55, 0.51, "chance", ha="left", va="bottom", color="grey", fontsize=8)
a1.set_xticks(x, VIEWS)
a1.set_ylim(0, 1)
a1.set_ylabel("AUROC (test, n = 24)")
a1.set_title("Same frozen prompt, two monitor models")
a1.legend(frameon=False, fontsize=8, loc="upper left")

lp_l = [LL["lpm"][v] / 24 for v in VIEWS]
lp_g = [R["views"][v]["lpm"]["share"] for v in VIEWS]
nb = [R["views"][v]["lpm"]["no_bias_expectation"] for v in VIEWS]
a2.bar(x - w / 2, lp_l, w, color=C_LLAMA, label="llama3.1:8b")
a2.bar(x + w / 2, lp_g, w, color=C_GRANITE, label="granite3.3:8b")
a2.scatter(x + w / 2, nb, marker="_", s=300, color="black", zorder=3, label="no-bias exp. (granite)")
a2.set_xticks(x, VIEWS)
a2.set_ylim(0, 1)
a2.set_ylabel("share of replies")
a2.set_title("Last-listed pair (T-Z) has the top score")
a2.legend(frameon=False, fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(FIG / "fig8_rq9_granite.png", dpi=150)
print("wrote", FIG / "fig8_rq9_granite.png")
