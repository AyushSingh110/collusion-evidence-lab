"""Task 14 (RQ7 / RQ8 code signal; no model calls): Study 2.3 signals for all 48 games from data/clean, with the honest
baseline fitted on DEV Type 2 games ONLY. Writes runs/p8_signals/game_signals.csv (game level = max over pairs,
argmax pair) and pair_signals.csv.

  conda run -n collusion-lab python -B scratch/p8_signals.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402
from core.evidence import signals as S  # noqa: E402

OUT = REPO_ROOT / "runs" / "p8_signals"
labels = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data/labels.csv", encoding="utf-8"))}
dev = set(json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["dev"])
clean = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((REPO_ROOT / "data/clean").glob("g_*.json"))}
assert set(clean) == set(labels), "clean games != labelled games"
dev_t2 = [c for g, c in clean.items() if g in dev and labels[g]["episode_type"] == "2"]
base = S.fit_honest_baseline(dev_t2)
print(f"honest baseline from {len(dev_t2)} DEV Type 2 games: {base}")
OUT.mkdir(parents=True, exist_ok=True)
pair_rows, game_rows = [], []
for g, c in clean.items():
    rows = S.pair_signal_table(c, base)
    pair_rows += rows
    game_rows.append(S.game_signals(rows))
for name, rows in (("pair_signals.csv", pair_rows), ("game_signals.csv", game_rows)):
    with open(OUT / name, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
json.dump({"n_dev_type2": len(dev_t2), "mu_pair": base.mu_pair, "sd_pair": base.sd_pair, "mu_others": base.mu_others,
           "n_pairs": base.n_pairs}, open(OUT / "honest_baseline.json", "w"), indent=1)
print(f"wrote {OUT / 'game_signals.csv'} ({len(game_rows)} games) and pair_signals.csv ({len(pair_rows)} rows)")
print("games with Dep NA:", sum(1 for r in game_rows if r["Dep"] is None))
