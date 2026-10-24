"""Task 13 rule (d): pick the 12 RQ0.4 dev games (6 Type 1, 2 each of Types 2/3/4b) with seed 20261023, recorded
before any monitor call. Also prints the dev ids and the 2 longest dev V5 / first 2 dev V3 files for the measurement.

  conda run -n collusion-lab python -B scratch/p7_select_rq04.py
"""
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

L = {r["game_id"]: int(r["episode_type"]) for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
dev = json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["dev"]
rng = random.Random(20261023)
sel = []
for t, k in ((1, 6), (2, 2), (3, 2), (4, 2)):
    sel += rng.sample(sorted(g for g in dev if L[g] == t), k)
man = json.load(open(REPO_ROOT / "data/views/manifest.json", encoding="utf-8"))
v5 = sorted((f for f in man["files"] if f["view"] == "V5" and f["game_id"] in dev), key=lambda f: -f["chars"])
v3 = sorted(f["game_id"] for f in man["files"] if f["view"] == "V3" and f["game_id"] in dev)
out = {"rq04_games": sel, "rq04_types": [L[g] for g in sel], "dev_ids": sorted(dev),
       "measure_v5_longest": [(f["game_id"], f["chars"]) for f in v5[:2]], "measure_v3": v3[:2]}
print(json.dumps(out))
