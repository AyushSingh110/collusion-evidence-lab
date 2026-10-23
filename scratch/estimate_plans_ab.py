"""Task 06a: in-memory 2-machine estimates (no plan files written)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import load_run_defaults
from core.plan import build_entries, machine_minutes
rd = load_run_defaults()
kw = dict(minutes_per_round_other=rd["minutes_per_round_measured"]["other"], type1_factor=rd["type1_time_factor"])
speed = {"A": 1.0, "B": round(27.17 / 12.03, 2)}
for name, seed, counts in (("pilot", 20261024, {1: 4, 2: 2, 3: 1, 4: 1}), ("dataset", 20261023, {1: 24, 2: 8, 3: 8, 4: 8})):
    e = build_entries(name, seed, counts, ["A", "B"], rd["n_rounds"], speed=speed, **kw)
    print(name, "speed", speed, "games per machine", {m: sum(x.machine == m for x in e) for m in "AB"},
          "wall min per machine", machine_minutes(e, speed))
