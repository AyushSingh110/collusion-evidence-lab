"""Task 15 helper: list TEST case-study candidates and dump their public text + monitor outputs to runs/p15/cases/.
The excerpts in writeup/excerpts_22.md are hand-picked from these dumps (quotes <= 25 words). No model calls.

  conda run -n collusion-lab python -B scratch/p15_excerpts.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

R = json.loads((REPO_ROOT / "runs/p15/results.json").read_text(encoding="utf-8"))
G = {g: d for g, d in R["games"].items() if d["split"] == "test"}
FZ = json.load(open(REPO_ROOT / "configs/frozen/monitor_frozen.json", encoding="utf-8"))
THR = {v: x["threshold"] for v, x in FZ["per_view"].items()}
MON = {(d["game_id"], d["view"]): d for d in map(json.loads, (REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl")
                                                 .read_text(encoding="utf-8").splitlines())}
LAB = {l.split(",")[0]: l.strip().split(",") for l in open(REPO_ROOT / "data/labels.csv", encoding="utf-8")}
HDR = LAB.pop("game_id")
focal = lambda g: LAB[g][HDR.index("focal_pair")].replace("|", "-")
OUT = REPO_ROOT / "runs/p15/cases"
OUT.mkdir(parents=True, exist_ok=True)

cands = {
    "a_T1_V4_caught_V1_low": [g for g, d in G.items() if d["type"] == 1 and d["scores"]["V4"] >= THR["V4"]
                              and d["scores"]["V1"] <= 60],
    "b_T3_fooled_V2": [g for g, d in G.items() if d["type"] == 3 and d["scores"]["V2"] >= THR["V2"]],
    "c_T4b_fooled_V1": [g for g, d in G.items() if d["type"] == 4 and d["scores"]["V1"] >= 60],
    "d_V4_false_positive": [g for g, d in G.items() if d["y"] == 0 and d["scores"]["V4"] >= THR["V4"]],
}
for case, gs in cands.items():
    print(f"\n== {case}: {gs}")
    for g in gs:
        c = json.loads((REPO_ROOT / "data/clean" / f"{g}.json").read_text(encoding="utf-8"))
        L = [f"# {g} type {G[g]['type']} focal {focal(g)}", ""]
        for v in ("V1", "V2", "V3", "V4", "V5"):
            m = MON[(g, v)]
            L.append(f"{v}: score {m['score']} pair {'-'.join(m['suspected_pair'] or []) or '[]'} | {m['rationale']}")
        L.append("")
        for r in c["rounds"]:
            acts = " ".join(f"{a}:{x}" for a, x in r["actions"].items())
            L.append(f"R{r['round']} actions {acts}")
            for a in r["announcements"]:
                L.append(f"  {a['agent']} ({a['stated_action']}): {a['message']}")
        if case == "a_T1_V4_caught_V1_low" or case == "d_V4_false_positive":
            L += ["", "--- V4 view ---", (REPO_ROOT / "data/views/V4" / f"{g}.txt").read_text(encoding="utf-8")]
        (OUT / f"{case}_{g}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
        hits = sum(bool(re.search(r"deposit", a["message"], re.I)) for r in c["rounds"] for a in r["announcements"])
        print(g, {v: G[g]["scores"][v] for v in ("V1", "V2", "V3", "V4")}, "deposit msgs:", hits)
