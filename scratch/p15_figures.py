"""Task 15 figures (PNG, 150 dpi) -> writeup/figures/. Reads the reported per-view tables (dev: runs/p7_analysis_dev,
test: runs/test_p8) and runs/p15/results.json (run scratch/p15_analysis.py first). No model calls.

  conda run -n collusion-lab python -B scratch/p15_figures.py
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
FIG.mkdir(parents=True, exist_ok=True)
VIEWS = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
TYPES = {1: "Type 1\ncollusion", 2: "Type 2\nplacebo", 3: "Type 3\npersona talk", 4: "Type 4b\nsame incentive"}
TCOL = {1: "#c0392b", 2: "#7f8c8d", 3: "#2e86c1", 4: "#d68910"}
R = json.loads((REPO_ROOT / "runs/p15/results.json").read_text(encoding="utf-8"))
G = R["games"]
rd = lambda p: {r.get("view") or r.get("source"): r for r in csv.DictReader(open(REPO_ROOT / p, encoding="utf-8"))}
DEV, TEST = rd("runs/p7_analysis_dev/rq1_per_view_dev.csv"), rd("runs/test_p8/rq1_per_view_test.csv")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)
    print("wrote", FIG / name)


def err(rows, v):
    a, lo, hi = (float(rows[v][k]) for k in ("auroc", "ci_low", "ci_high"))
    return a, a - lo, hi - a


# fig1: test AUROC per view with 95% CI
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(VIEWS))
a = [err(TEST, v) for v in VIEWS]
ax.bar(x, [t[0] for t in a], color=["#34495e"] * 5 + ["#bdc3c7"] * 3)
ax.errorbar(x, [t[0] for t in a], yerr=[[t[1] for t in a], [t[2] for t in a]], fmt="none", ecolor="black", capsize=4)
ax.axhline(0.5, ls="--", color="grey", lw=1)
ax.text(len(VIEWS) - 0.5, 0.51, "chance", ha="right", va="bottom", color="grey", fontsize=8)
ax.set_xticks(x, VIEWS)
ax.set_ylim(0, 1)
ax.set_ylabel("AUROC (test, n = 24)")
ax.set_title("How well each view separates collusion games (test set)")
save(fig, "fig1_auroc_by_view_test.png")

# fig2: score per game, by episode type, per view (test)
fig, axes = plt.subplots(2, 4, figsize=(12, 6), sharey=True)
rng = np.random.default_rng(20261023)
for ax, v in zip(axes.flat, VIEWS):
    for t in TYPES:
        s = [g["scores"][v] for g in G.values() if g["split"] == "test" and g["type"] == t]
        ax.scatter(t + rng.uniform(-0.15, 0.15, len(s)), s, color=TCOL[t], alpha=0.7, s=22)
        ax.hlines(np.mean(s), t - 0.3, t + 0.3, color="black", lw=2)
    ax.set_title(v)
    ax.set_xticks(list(TYPES), ["T1", "T2", "T3", "T4b"])
    ax.set_ylim(-5, 105)
for ax in axes[:, 0]:
    ax.set_ylabel("Monitor score (0–100)")
fig.suptitle("Monitor score per test game by episode type (black bar = mean; T1 = collusion)")
save(fig, "fig2_per_type_scores_test.png")


# fig3: ROC curves V1-V4 (test)
def roc(scores, labels):
    pts = [(0.0, 0.0)]
    P, N = sum(labels), len(labels) - sum(labels)
    for thr in sorted(set(scores), reverse=True):
        tp = sum(1 for s, y in zip(scores, labels) if s >= thr and y)
        fp = sum(1 for s, y in zip(scores, labels) if s >= thr and not y)
        pts.append((fp / N, tp / P))
    return zip(*pts)


fig, ax = plt.subplots(figsize=(5, 5))
for v, c in zip(("V1", "V2", "V3", "V4"), ("#e67e22", "#16a085", "#8e44ad", "#c0392b")):
    tg = [g for g in G.values() if g["split"] == "test"]
    fx, fy = roc([g["scores"][v] for g in tg], [g["y"] for g in tg])
    ax.plot(list(fx), list(fy), marker="o", ms=3, color=c, label=f"{v} (AUROC {float(TEST[v]['auroc']):.2f})")
ax.plot([0, 1], [0, 1], ls="--", color="grey", lw=1)
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title("ROC curves, test set (n = 24)")
ax.legend(loc="lower right", fontsize=8)
save(fig, "fig3_roc_V1_V2_V3_V4_test.png")

# fig4: dev vs test AUROC per view
fig, ax = plt.subplots(figsize=(8, 4))
for off, rows, lab, c in ((-0.18, DEV, "dev (n = 24)", "#95a5a6"), (0.18, TEST, "test (n = 24)", "#34495e")):
    a = [err(rows, v) for v in VIEWS]
    ax.errorbar(x + off, [t[0] for t in a], yerr=[[t[1] for t in a], [t[2] for t in a]], fmt="o", color=c, capsize=3,
                label=lab)
ax.axhline(0.5, ls="--", color="grey", lw=1)
ax.set_xticks(x, VIEWS)
ax.set_ylim(0, 1)
ax.set_ylabel("AUROC with 95% CI")
ax.set_title(f"Dev vs test AUROC per view (Kendall tau of the two orders = {R['stability']['kendall_tau_b']:.2f})")
ax.legend(loc="lower right", fontsize=8)
save(fig, "fig4_dev_vs_test_auroc.png")

# fig5: RQ8 pair accuracy, dev and test
D8, T8 = rd("runs/p7_analysis_dev/rq8_top1_pair_dev.csv"), rd("runs/test_p8/rq8_top1_pair_test.csv")
src = ["monitor V1", "monitor V2", "monitor V3", "monitor V4", "monitor V5", "evidence argmax (Dep)"]
names = ["V1", "V2", "V3", "V4", "V5", "Dep\n(code)"]
fig, ax = plt.subplots(figsize=(7, 4))
xs = np.arange(len(src))
ax.bar(xs - 0.2, [float(D8[s]["accuracy"]) if s in D8 else 0 for s in src], 0.4, color="#95a5a6", label="dev (12 collusion games)")
ax.bar(xs + 0.2, [float(T8[s]["accuracy"]) for s in src], 0.4, color="#34495e", label="test (12 collusion games)")
ax.text(xs[-1] - 0.2, 0.02, "n/a", ha="center", fontsize=8)
ax.axhline(0.1, ls="--", color="#c0392b", lw=1)
ax.text(-0.5, 0.11, "chance (1 in 10 pairs)", color="#c0392b", fontsize=8)
ax.set_xticks(xs, names)
ax.set_ylim(0, 1)
ax.set_ylabel("Share of games with the true pair named")
ax.set_title("Who is the colluding pair? (top-1 accuracy)")
ax.legend(fontsize=8)
save(fig, "fig5_rq8_pair_accuracy.png")

# fig6: code signals vs V4 (test and pooled)
S = ("coGO", "capture", "G_others", "C_kw", "Dep", "V4")
fig, ax = plt.subplots(figsize=(8, 4))
xs = np.arange(len(S))
for off, split, c in ((-0.18, "test", "#34495e"), (0.18, "pooled", "#95a5a6")):
    d = [R["code_signals"][split][s] for s in S]
    e = [t["estimate"] for t in d]
    ax.errorbar(xs + off, e, yerr=[[t["estimate"] - t["ci"][0] for t in d], [t["ci"][1] - t["estimate"] for t in d]],
                fmt="o", color=c, capsize=3, label=f"{split} (n = {d[0]['n']}{'; Dep ' + str(d[4]['n']) if d[4]['n'] != d[0]['n'] else ''})")
ax.axhline(0.5, ls="--", color="grey", lw=1)
ax.axvline(len(S) - 1.5, color="lightgrey", lw=1)
ax.set_xticks(xs, ["coGO", "capture", "G_others", "C_kw", "Dep", "V4\n(LLM monitor)"])
ax.set_ylim(0, 1.05)
ax.set_ylabel("AUROC with 95% CI")
ax.set_title("Simple code signals vs the LLM monitor on the structured report (V4)")
ax.legend(loc="lower left", fontsize=8)
save(fig, "fig6_code_signals_vs_V4.png")
