"""Task 15 (EXPLORATORY): position bias in the pair_scores of monitor_v3_pairs replies. How often are the 10 pair
scores non-decreasing in the listed order (J-M ... T-Z), how often is the named pair T-Z (the last listed pair), and
how often is T-Z the true focal pair? No model calls. Writes runs/p15/pair_bias.json.

  conda run -n collusion-lab python -B scratch/p15_pairbias.py
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

VIEWS = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
LAB = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
SPLIT = json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))
RUNS = {"dev": "runs/p7_v3_ctx16k/outputs/monitor.jsonl", "test": "runs/test_p8/outputs/monitor.jsonl"}
out = {"label": "EXPLORATORY, not pre-registered"}
for split, p in RUNS.items():
    rows = [d for d in map(json.loads, (REPO_ROOT / p).read_text(encoding="utf-8").splitlines())
            if d["sample_idx"] == 0 and d["game_id"] in SPLIT[split]]
    per = {}
    for v in VIEWS:
        r = [d for d in rows if d["view"] == v]
        mono = sum(1 for d in r if (s := list(d["pair_scores"].values())) and all(a <= b for a, b in zip(s, s[1:]))
                   and s[0] < s[-1])
        named = Counter("-".join(d["suspected_pair"]) if d["suspected_pair"] else "none" for d in r)
        top_tz = sum(1 for d in r if d["pair_scores"] and d["pair_scores"].get("T-Z") == max(d["pair_scores"].values()))
        per[v] = {"n": len(r), "increasing_in_list_order": mono, "named_T-Z": named.get("T-Z", 0),
                  "named_none": named.get("none", 0), "T-Z_has_max_score": top_tz, "named_top3": named.most_common(3)}
    t1 = [g for g in SPLIT[split] if LAB[g]["episode_type"] == "1"]
    out[split] = {"per_view": per, "type1_focal_pairs": Counter(LAB[g]["focal_pair"].replace("|", "-") for g in t1)}
(REPO_ROOT / "runs/p15/pair_bias.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
for split in RUNS:
    print(f"== {split}: Type 1 focal pairs {dict(out[split]['type1_focal_pairs'])}")
    for v, x in out[split]["per_view"].items():
        print(v, {k: x[k] for k in ("n", "increasing_in_list_order", "T-Z_has_max_score", "named_T-Z", "named_none")})
