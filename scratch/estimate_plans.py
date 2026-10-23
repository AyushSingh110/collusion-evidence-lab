"""Task 04: in-memory estimates (no plan files written) with the final run_defaults."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import load_run_defaults
from core.plan import build_entries, machine_minutes
rd = load_run_defaults()
kw = dict(minutes_per_round_other=rd["minutes_per_round_measured"]["other"], type1_factor=rd["type1_time_factor"])
for name, seed, counts in (("pilot", 20261024, {1: 4, 2: 2, 3: 1, 4: 1}), ("dataset", 20261023, {1: 24, 2: 8, 3: 8, 4: 8})):
    e = build_entries(name, seed, counts, ["A", "B", "C"], rd["n_rounds"], **kw)
    calls = sum((19 if x.episode_type == 1 else 15) * x.n_rounds for x in e)
    print(name, "games", len(e), "calls", calls, "single-laptop min", round(sum(x.est_minutes for x in e)),
          "per machine (speed 1.0):", machine_minutes(e))
