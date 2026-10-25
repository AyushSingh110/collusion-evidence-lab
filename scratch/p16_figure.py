"""Task 16: writeup/figures/fig7_pair_order_followup.png from runs/followup1/analysis.json (run p16_analysis.py first).

  conda run -n collusion-lab python -B scratch/p16_figure.py
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

R = json.loads((REPO_ROOT / "runs/followup1/analysis.json").read_text(encoding="utf-8"))
VIEWS = ("V1", "V2", "V3", "V4")
ARMS = (("frozen", "fixed order, original test run", "#95a5a6"), ("fixed", "fixed order, same session", "#34495e"),
        ("rot", "random order, same session", "#c0392b"))
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
x = np.arange(len(VIEWS))
for ax, key, title, ylab in ((axes[0], "auroc", "AUROC per view", "AUROC with 95% CI"),
                             (axes[1], "lpm", "How often the LAST-listed pair gets the top score", "Share of replies (95% CI)")):
    for k, (arm, lab, c) in enumerate(ARMS):
        d = [R["views"][v][arm][key] for v in VIEWS]
        e = np.array([t["estimate"] for t in d])
        ax.errorbar(x + (k - 1) * 0.22, e, yerr=[e - [t["ci"][0] for t in d], [t["ci"][1] for t in d] - e], fmt="o",
                    color=c, capsize=3, label=lab)
        if key == "lpm":
            ax.scatter(x + (k - 1) * 0.22, [R["views"][v][arm]["lpm_nobias_expectation"] for v in VIEWS], marker="_",
                       s=200, color="black", zorder=3, label="no-bias expectation" if k == 0 else None)
    if key == "auroc":
        ax.axhline(0.5, ls="--", color="grey", lw=1)
    ax.set_xticks(x, VIEWS)
    ax.set_ylim(0, 1.05)
    ax.set_title(title)
    ax.set_ylabel(ylab)
axes[0].legend(fontsize=8, loc="lower right")
axes[1].set_ylim(0, 1.4)
axes[1].set_yticks(np.arange(0, 1.01, 0.2))
axes[1].legend(fontsize=8, loc="upper center", ncol=2)
fig.suptitle("Follow-up 1: randomising the order of the 10 pairs (24 test games)")
fig.tight_layout()
out = REPO_ROOT / "writeup/figures/fig7_pair_order_followup.png"
fig.savefig(out, dpi=150)
print("wrote", out)
