"""Task 21: print the secondary measures from runs/replication/analysis_22/replication_22.json (formatting only; no new
analysis on the replication games).

  conda run -n collusion-lab python -B scratch/p21_print_secondary.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

R = json.loads((REPO_ROOT / "runs/replication/analysis_22/replication_22.json").read_text(encoding="utf-8"))
S = R["primary"]["secondary"]
f = lambda x: "NA" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))
print("inputs:", {k: v["sha256_lf"][:16] for k, v in R["inputs"].items()}, "| quality_fail:", R["quality_fail"])
print("\n## other code signals")
for r in S["other_signals"]:
    print(f"| {r['signal']} | n {r['n']} (dropped {r['dropped']}) | AUROC {f(r.get('auroc'))} [{f(r.get('ci_low'))}, "
          f"{f(r.get('ci_high'))}] | T1 vs T4b {f(r.get('t1_vs_t4b'))} {r.get('t1_vs_t4b_ci')} |")
print("\n## top-1 pair (24 Type 1 games)")
for r in S["top1"]:
    print(f"| {r['source']} | {r['correct']}/{r['n']} | no pair {r['no_pair']} | acc {f(r['accuracy'])} |")
print("\n## frozen-threshold metrics")
for r in S["threshold_metrics"]:
    print(f"| {r['view']} | thr {r['threshold']} | acc {f(r['accuracy'])} | TPR {f(r['tpr'])} | FPR {f(r['fpr'])} | "
          f"BA {f(r['balanced_accuracy'])} | {r['note']} |")
print("\n## FP per negative type at frozen thresholds")
for r in S["fpr_by_type"]:
    print(f"| {r['view']} | T{r['type']} | {r['fp']}/{r['n']} | rule-of-3 {f(r['upper95_rule_of_three'])} | {r['note']} |")
print("\n## last-position-max (T-Z max, ties included)")
for r in S["last_position_max"]:
    print(f"| {r['view']} | {r['k']}/{r['n']} = {f(r['share'])} | no-bias expectation {f(r['no_bias_expectation'])} |")
print("\n## extra paired differences")
for r in S["paired_extra"]:
    print(f"| {r['comparison']} | n {r['n']} | {f(r['estimate'])} [{f(r['ci_low'])}, {f(r['ci_high'])}] |")
same = R["primary"]["hypotheses"] == R["sensitivity"]["hypotheses"]
print("\nsensitivity hypotheses identical to primary:", same)
