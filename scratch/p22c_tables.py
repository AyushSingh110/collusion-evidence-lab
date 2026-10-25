"""Task 22C: side-by-side tables, replication (runs/replication_23/results.json) vs the original test (17C,
runs/study23/results.json). Reads result files only; no model calls, no recomputation.

  conda run -n collusion-lab python -B scratch/p22c_tables.py      -> prints markdown, writes runs/replication_23/tables.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

REP = json.loads((REPO_ROOT / "runs/replication_23/results.json").read_text(encoding="utf-8"))
O17 = json.loads((REPO_ROOT / "runs/study23/results.json").read_text(encoding="utf-8"))
TYPES = ("T1", "T2", "T3", "T4b")


def c(d):
    return "—" if d is None or d.get("estimate") is None else \
        f"{d['estimate']:.3f} [{d['ci_low']:.3f}, {d['ci_high']:.3f}]"


def kn(pt):
    return " | ".join(f"{pt[t]['k']}/{pt[t]['n']}" + (f" (≤{pt[t]['upper95_rule_of_three']:.2f})"
                                                      if pt[t]["upper95_rule_of_three"] is not None else "")
                      for t in TYPES)


L = []
for part in ("primary", "sensitivity"):
    p = REP[part]
    if "E1" not in p:
        L += [f"## {part}: {p['status']}", ""]
        continue
    L += [f"## {part} (n = {p['n']}; by type {p['n_by_type']}; score NA {p['n_score_na']})", "",
          "| Hyp. | Test | Replication [95% CI] | Verdict | Original test, 17C (n = 24) |", "|---|---|---|---|---|"]
    orig = {"E1": O17["rules"]["R2"]["auroc"], "E2": O17["rules"]["R1"]["auroc"], "E3": O17["rq_e3"]["auroc_diff"],
            "E3b": None}
    for e in ("E1", "E2", "E3", "E3b"):
        L.append(f"| {e} | {p[e]['test']} | {c(p[e])} | **{p[e]['verdict']}** | {c(orig[e])} |")
    L += ["", "| Rule | AUROC replication | AUROC 17C | TPR | FPR | T1 | T2 | T3 | T4b |", "|---|---|---|---|---|---|---|---|---|"]
    for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        f = p["flags"][r]
        a = c(p["auroc"].get(r)) if r in p["auroc"] else "—"
        a17 = c(O17["rules"][r].get("auroc")) if "auroc" in O17["rules"][r] else "—"
        L.append(f"| {r} | {a} | {a17} | {f['tpr']:.3f} | {f['fpr']:.3f} | {kn(f['per_type'])} |")
    pf = p["plus_factor_secondary"]
    o = O17["exploratory_plus_factor"]["plus_factor_rule"]
    L += ["", f"Plus-factor rule (secondary): TPR {pf['tpr']:.3f}, FPR {pf['fpr']:.3f}; per type {kn(pf['per_type'])} "
          f"(17C: TPR {o['tpr']:.3f}, FPR {o['fpr']:.3f}; {kn(o['per_type'])})", ""]
inp = REP["inputs"]
L += [f"Inputs: judge lines {inp['judge_lines']}/{inp['n_games']}, missing {inp['judge_missing']}, rejected "
      f"{inp['judge_rejected']}; quality file {inp['quality']}; machine {inp['machine_id']}"]
(REPO_ROOT / "runs/replication_23/tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
