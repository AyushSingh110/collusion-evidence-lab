"""Task 14 extras on the TEST run (no model calls): run stats per view, supplementary RQ3 (Type 1 vs each negative type,
pre-specified before test scoring), C-length - V3 (exploratory), exploratory subgroups, and the V1-V4 error list.

  PYTHONIOENCODING=utf-8 conda run --no-capture-output -n collusion-lab python -B scratch/p8_extras.py
Writes runs/test_p8/extras.json and runs/test_p8/errors.md.
"""
import csv
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402
from core.stats import metrics as M  # noqa: E402

RUN = REPO_ROOT / "runs/test_p8"
VIEWS = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
LAB = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
TEST = set(json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["test"])
FZ = json.load(open(REPO_ROOT / "configs/frozen/monitor_frozen.json", encoding="utf-8"))
THR = {v: x["threshold"] for v, x in FZ["per_view"].items()}
DEGENERATE = {v for v, t in THR.items() if t == 0}
rows = [json.loads(x) for x in (RUN / "outputs/monitor.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert all(d["game_id"] in TEST for d in rows) and all(d["sample_idx"] == 0 for d in rows)
by = {(d["game_id"], d["view"]): d for d in rows}
T = lambda g: int(LAB[g]["episode_type"])
out = {"degenerate_threshold_views": sorted(DEGENERATE)}

# run stats
stats = {}
for v in VIEWS:
    r = [d for d in rows if d["view"] == v]
    stats[v] = {"n": len(r), "parse_fail": sum(not d["parse_ok"] for d in r), "trunc": sum(d["truncation_suspect"] for d in r),
                "missing_score": sum(d["score"] is None for d in r), "length_cut": sum(d["done_reason"] == "length" for d in r),
                "mean_latency": round(st.mean(d["latency"] for d in r if d["latency"]), 1)}
out["run_stats"] = stats

# supplementary RQ3: Type 1 vs each negative type (resample games within each pair of types), mean score per type
sup = {}
for v in VIEWS:
    sup[v] = {"mean_score": {t: st.mean([by[(g, v)]["score"] for g in TEST if T(g) == t and by[(g, v)]["score"] is not None])
                             for t in (1, 2, 3, 4)}}
    for neg in (2, 3, 4):
        gs = [g for g in sorted(TEST) if T(g) in (1, neg) and by[(g, v)]["score"] is not None]
        s = [by[(g, v)]["score"] for g in gs]
        y = [int(T(g) == 1) for g in gs]
        sup[v][f"T1_vs_T{neg}"] = M.bootstrap_auroc(s, y, [T(g) for g in gs], b=2000, seed=20261023)
out["supplementary_rq3"] = sup

# exploratory: C-length - V3
common = [g for g in sorted(TEST) if by[(g, "C-length")]["score"] is not None and by[(g, "V3")]["score"] is not None]
out["exploratory_clength_minus_v3"] = M.paired_auroc_diff(
    [by[(g, "C-length")]["score"] for g in common], [by[(g, "V3")]["score"] for g in common],
    [int(LAB[g]["collusion"]) for g in common], [T(g) for g in common], b=2000, seed=20261023) | {"n": len(common)}

# exploratory subgroups
q = {x["game_id"]: x for x in json.load(open(REPO_ROOT / "runs/dataset_t12/quality_rq02.json", encoding="utf-8"))["games"]}
t1 = [g for g in TEST if T(g) == 1]
rev = [g for g in t1 if q[g]["reveals"] > 0]
norev = [g for g in t1 if q[g]["reveals"] == 0]
neg = [g for g in TEST if T(g) != 1]
def auc_vs_neg(group, v):
    gs = [g for g in group + neg if by[(g, v)]["score"] is not None]
    return M.auroc([by[(g, v)]["score"] for g in gs], [int(T(g) == 1) for g in gs])
out["exploratory_v1_reveal"] = {
    "n_with_reveal": len(rev), "n_without": len(norev),
    "mean_V1_with": st.mean(by[(g, "V1")]["score"] for g in rev) if rev else None,
    "mean_V1_without": st.mean(by[(g, "V1")]["score"] for g in norev) if norev else None,
    "auroc_V1_with_vs_all_neg": auc_vs_neg(rev, "V1") if rev else None,
    "auroc_V1_without_vs_all_neg": auc_vs_neg(norev, "V1") if norev else None}
t4 = [g for g in TEST if T(g) == 4]
out["exploratory_4b_deposit"] = {
    "n_4b": len(t4), "n_4b_with_public_deposit": sum(q[g]["deposit_public"] > 0 for g in t4),
    **{f"mean_{v}_T4b": st.mean(by[(g, v)]["score"] for g in t4) for v in ("V1", "V3")},
    **{f"mean_{v}_T2": st.mean(by[(g, v)]["score"] for g in TEST if T(g) == 2) for v in ("V1", "V3")},
    **{f"FP_{v}_T4b": f"{sum(by[(g, v)]['score'] >= THR[v] for g in t4)}/{len(t4)}" for v in ("V1", "V3")}}

# error analysis V1-V4 at frozen thresholds
L = ["# Test-set error analysis (V1–V4 at the frozen dev thresholds)", "",
     "V1 and V3 have a **degenerate threshold (0, flags everything)**: every negative is a false positive there by "
     "construction; they are listed for completeness.", ""]
err = []
for v in ("V1", "V2", "V3", "V4"):
    L += [f"## {v} (threshold {THR[v]}{', degenerate' if v in DEGENERATE else ''})", "",
          "| kind | game | type | score | named pair | evidence (≤ 25 words) |", "|---|---|---|---|---|---|"]
    for g in sorted(TEST, key=lambda g: (T(g), g)):
        d = by[(g, v)]
        if d["score"] is None:
            continue
        y, flag = int(LAB[g]["collusion"]), d["score"] >= THR[v]
        kind = "FP" if flag and not y else ("FN" if not flag and y else None)
        if kind:
            ev = " ".join((d.get("rationale") or "").split()[:25])
            pair = "-".join(d.get("suspected_pair") or []) or "[]"
            focal = LAB[g]["focal_pair"].replace("|", "-")
            L.append(f"| {kind} | {g} | {T(g)} | {d['score']} | {pair} (focal {focal}) | {ev} |")
            err.append({"view": v, "kind": kind, "game": g, "type": T(g), "score": d["score"], "pair": pair, "focal": focal})
    L.append("")
(RUN / "errors.md").write_text("\n".join(L) + "\n", encoding="utf-8")
out["errors"] = err
(RUN / "extras.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "errors"}, indent=1))
print("errors:", {v: {k: sum(1 for e in err if e["view"] == v and e["kind"] == k) for k in ("FP", "FN")} for v in ("V1", "V2", "V3", "V4")})
