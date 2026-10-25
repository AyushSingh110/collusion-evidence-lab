"""Task 15C RQ9 analysis: granite3.3:8b with the frozen v3_pairs_ctx16k format on the 24 test games x V1-V4.
Threshold-free; no new thresholds. No model calls.

  conda run -n collusion-lab python -B scratch/p15c_analysis.py     -> runs/rq9_granite/results.json, tables.md

Granite: runs/rq9_granite/outputs/monitor.jsonl (sample 0). Llama (primary monitor, frozen test run test_p8 on
machine B) is NOT on this machine; its values are copied from report 14 (AUROC, per-type, RQ8), report 15 §4.3
(V3 - V1) and report 16 §4.3 (last-position max, frozen run) and are marked as such.
CIs: 95% stratified bootstrap by episode type (whole games), B = 2000, seed 20261023; paired differences share the
resample indices; per-type AUROCs resample within the two types. Missing scores are counted and left out.
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT, load_json  # noqa: E402
from core.labels import read_labels  # noqa: E402
from core.stats import metrics as M  # noqa: E402
from study_2_2_views.monitor import PROMPTS, load_config  # noqa: E402

VIEWS = ("V1", "V2", "V3", "V4")
TN = {1: "T1", 2: "T2", 3: "T3", 4: "T4b"}
OUT = REPO_ROOT / "runs/rq9_granite"
LLAMA = {  # frozen test run test_p8 (llama3.1:8b, machine B)
    "auroc": {"V1": (0.490, 0.299, 0.691), "V2": (0.372, 0.170, 0.601), "V3": (0.736, 0.535, 0.920),
              "V4": (0.896, 0.771, 0.979)},                                                        # report 14 §4.2
    "paired": {"V3-V2": (0.365, 0.094, 0.611), "V4-V3": (0.160, -0.021, 0.351),                   # report 14
               "V3-V1": (0.247, 0.024, 0.476)},                                                    # report 15 §4.3
    "per_type": {"V1": {"T2": 0.385, "T3": 0.740, "T4b": 0.344}, "V2": {"T2": 0.438, "T3": 0.219, "T4b": 0.458},
                 "V3": {"T2": 0.667, "T3": 0.917, "T4b": 0.625}, "V4": {"T2": 1.000, "T3": 0.792, "T4b": 0.896}},
    "mean_by_type": {"V1": (72.9, 73.5, 24.5, 88.5), "V2": (50.8, 45.0, 72.0, 47.5), "V3": (70.5, 39.5, 0.0, 63.8),
                     "V4": (79.2, 10.0, 55.0, 35.0)},                                              # report 14 §4.4
    "top1": {"V1": 1, "V2": 6, "V3": 2, "V4": 7},                                                  # report 14 §4.9
    "lpm": {"V1": 21, "V2": 14, "V3": 17, "V4": 7},                                                # report 16 §4.3
}

cfg = load_config(manifest=PROMPTS["monitor_v3_pairs_ctx16k_granite"])
labels = {lb.game_id: lb for lb in read_labels(REPO_ROOT / "data/labels.csv")}
test = sorted(load_json(REPO_ROOT / "data/split.json")["test"])
lines = {}
for raw in (OUT / "outputs/monitor.jsonl").read_text(encoding="utf-8").splitlines():
    if raw.strip():
        d = json.loads(raw)
        key = (d["game_id"], d["view"])
        assert d["sample_idx"] == 0 and key not in lines and d["prompt_version"] == cfg.prompt_version
        lines[key] = d
errors_path = OUT / "outputs/errors.jsonl"
n_transport = len(errors_path.read_text(encoding="utf-8").splitlines()) if errors_path.exists() else 0
y = [labels[g].collusion for g in test]
types = [labels[g].episode_type for g in test]
order = list(cfg.pair_order)
res = {"model": cfg.model, "prompt_version": cfg.prompt_version, "n_test": len(test), "transport_errors": n_transport,
       "llama_reference": LLAMA, "views": {}}


def auroc_stat(sc, idx_keep):
    def stat(idx):
        k = [i for i in idx if sc[i] is not None and i in idx_keep]
        return M.auroc([sc[i] for i in k], [y[i] for i in k]) if k else None
    return stat


scores = {}
for v in VIEWS:
    ls = [lines.get((g, v)) for g in test]
    sc = [None if l is None else l["score"] for l in ls]
    scores[v] = sc
    ok = [l for l in ls if l is not None and l["pair_scores"] is not None]
    run = {"lines": sum(l is not None for l in ls), "parse_ok": sum(bool(l and l["parse_ok"]) for l in ls),
           "truncation_suspect": sum(bool(l and l["truncation_suspect"]) for l in ls),
           "length_cut": sum(bool(l and l["done_reason"] == "length") for l in ls),
           "missing_score": sum(s is None for s in sc),
           "latency_mean_s": statistics.mean(l["latency"] for l in ls if l and l["latency"] is not None),
           "prompt_eval_max": max(l["prompt_eval_count"] or 0 for l in ls if l)}
    allidx = set(range(len(test)))
    au = M.bootstrap_ci(auroc_stat(sc, allidx), types)
    per_type = {}
    for t in (2, 3, 4):
        sub = {i for i, tt in enumerate(types) if tt in (1, t)}
        st = [types[i] if i in sub else "out" for i in range(len(test))]
        b = M.bootstrap_ci(auroc_stat(sc, sub), st)
        per_type[TN[t]] = {k: b[k] for k in ("estimate", "ci_low", "ci_high")}
    mean_t = {TN[t]: statistics.mean([s for s, tt in zip(sc, types) if tt == t and s is not None]) for t in TN}
    # RQ8 top-1 (strict argmax; tie -> no pair)
    t1 = [(g, lines[(g, v)]) for g in test if labels[g].episode_type == 1 and (g, v) in lines]
    top1 = sum(sorted(l["suspected_pair"]) == sorted(labels[g].focal_pair) for g, l in t1 if l["suspected_pair"])
    ties = sum(1 for _, l in t1 if l["score"] is not None and not l["suspected_pair"])
    ties_all = sum(1 for l in ok if not l["suspected_pair"])
    # last-position max (ties included) + no-bias expectation
    lpm = sum(l["pair_scores"]["T-Z"] == max(l["pair_scores"].values()) for l in ok)
    nobias = statistics.mean(sum(x == max(l["pair_scores"].values()) for x in l["pair_scores"].values()) / 10
                             for l in ok)
    named = {}
    for l in ok:
        if l["suspected_pair"]:
            k = "-".join(l["suspected_pair"])
            named[k] = named.get(k, 0) + 1
    gs = [l["score"] for l in ok]
    allps = [x for l in ok for x in l["pair_scores"].values()]
    diag = {"distinct_game_scores": sorted(set(gs)), "n_distinct_game_scores": len(set(gs)),
            "n_distinct_pair_scores": len(set(allps)), "game_score_min": min(gs), "game_score_max": max(gs),
            "game_score_sd": statistics.pstdev(gs), "share_at_view_max": sum(s == max(gs) for s in gs) / len(gs),
            "share_game_score_0": sum(s == 0 for s in gs) / len(gs),
            "share_all_pairs_equal": sum(len(set(l["pair_scores"].values())) == 1 for l in ok) / len(ok)}
    res["views"][v] = {"run": run, "auroc": {k: au[k] for k in ("estimate", "ci_low", "ci_high", "b_na")},
                       "per_type_auroc": per_type, "mean_score_by_type": mean_t,
                       "top1": {"correct": top1, "n_type1": len(t1), "ties_no_pair_type1": ties,
                                "ties_no_pair_all": ties_all},
                       "lpm": {"k": lpm, "n": len(ok), "share": lpm / len(ok), "no_bias_expectation": nobias},
                       "named_pair_counts": dict(sorted(named.items(), key=lambda x: -x[1])),
                       "scores": diag}

# ranking + Kendall tau-b vs llama's test AUROCs
g_au = [res["views"][v]["auroc"]["estimate"] for v in VIEWS]
l_au = [LLAMA["auroc"][v][0] for v in VIEWS]
res["ranking"] = {"granite": sorted(VIEWS, key=lambda v: -res["views"][v]["auroc"]["estimate"]),
                  "llama": sorted(VIEWS, key=lambda v: -LLAMA["auroc"][v][0]),
                  "kendall_tau_b": M.kendall_tau(g_au, l_au),
                  "tau_note": "4 views -> 6 view pairs; without ties tau can only be -1, -2/3, -1/3, 0, 1/3, 2/3, 1"}
allidx = set(range(len(test)))
res["paired"] = {f"{a}-{b}": {k: d[k] for k in ("estimate", "ci_low", "ci_high", "b_na")}
                 for a, b in (("V3", "V2"), ("V4", "V3"), ("V3", "V1"))
                 for d in [M.paired_bootstrap_diff(auroc_stat(scores[a], allidx), auroc_stat(scores[b], allidx), types)]}
(OUT / "results.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")


# ---- tables.md
def f(x, n=3):
    return "—" if x is None else f"{x:.{n}f}"


def c(d):
    return f"{f(d['estimate'])} [{f(d['ci_low'])}, {f(d['ci_high'])}]"


L = ["## Run", "", "| View | lines | parse_ok | trunc | length cut | missing | mean latency s | max prompt_eval |",
     "|---|---|---|---|---|---|---|---|"]
for v in VIEWS:
    r = res["views"][v]["run"]
    L.append(f"| {v} | {r['lines']} | {r['parse_ok']} | {r['truncation_suspect']} | {r['length_cut']} | "
             f"{r['missing_score']} | {r['latency_mean_s']:.1f} | {r['prompt_eval_max']} |")
L += ["", f"transport errors: {n_transport}", "", "## AUROC", "", "| View | granite [CI] | llama (report 14) [CI] |",
      "|---|---|---|"]
for v in VIEWS:
    la = LLAMA["auroc"][v]
    L.append(f"| {v} | {c(res['views'][v]['auroc'])} | {la[0]:.3f} [{la[1]:.3f}, {la[2]:.3f}] |")
rk = res["ranking"]
L += ["", f"granite ranking {' > '.join(rk['granite'])}; llama {' > '.join(rk['llama'])}; "
      f"Kendall tau-b {f(rk['kendall_tau_b'])} ({rk['tau_note']})", "", "## Paired (granite) vs llama", "",
      "| Diff | granite [CI] | llama [CI] |", "|---|---|---|"]
for k, d in res["paired"].items():
    la = LLAMA["paired"][k]
    L.append(f"| {k} | {c(d)} | {la[0]:+.3f} [{la[1]:.3f}, {la[2]:.3f}] |")
L += ["", "## Per type (T1 vs X) and mean score per type", "",
      "| View | T1 vs T2 | T1 vs T3 | T1 vs T4b | llama T2/T3/T4b | mean T1/T2/T3/T4b granite | llama |",
      "|---|---|---|---|---|---|---|"]
for v in VIEWS:
    p, m, lp = res["views"][v]["per_type_auroc"], res["views"][v]["mean_score_by_type"], LLAMA["per_type"][v]
    L.append(f"| {v} | {c(p['T2'])} | {c(p['T3'])} | {c(p['T4b'])} | {lp['T2']:.3f}/{lp['T3']:.3f}/{lp['T4b']:.3f} | "
             + "/".join(f"{m[t]:.1f}" for t in ("T1", "T2", "T3", "T4b")) + " | "
             + "/".join(f"{x:.1f}" for x in LLAMA["mean_by_type"][v]) + " |")
L += ["", "## Top-1 pair, last-position max, score diagnostics", "",
      "| View | top-1 granite | ties T1 (all) | top-1 llama | LPM granite | no-bias exp. | LPM llama | distinct game "
      "scores | min–max | SD | share at view max | share 0 | all pairs equal |", "|---" * 13 + "|"]
for v in VIEWS:
    t, lp, s = res["views"][v]["top1"], res["views"][v]["lpm"], res["views"][v]["scores"]
    L.append(f"| {v} | {t['correct']}/{t['n_type1']} | {t['ties_no_pair_type1']} ({t['ties_no_pair_all']}) | "
             f"{LLAMA['top1'][v]}/12 | {lp['k']}/{lp['n']} | {f(lp['no_bias_expectation'])} | {LLAMA['lpm'][v]}/24 | "
             f"{s['n_distinct_game_scores']} {s['distinct_game_scores']} | {s['game_score_min']}–{s['game_score_max']} | "
             f"{s['game_score_sd']:.1f} | {f(s['share_at_view_max'])} | {f(s['share_game_score_0'])} | "
             f"{f(s['share_all_pairs_equal'])} |")
(OUT / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
