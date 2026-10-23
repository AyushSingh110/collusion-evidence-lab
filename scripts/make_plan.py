"""Create configs/plans/<name>.json (refuses to overwrite).

Example:
  conda run -n collusion-lab python scripts/make_plan.py --name pilot --seed 20261024 \
      --counts 1=4 2=2 3=1 4=1 --machines A B C --rounds 6 --speed A=1.0 B=0.9 C=1.1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_run_defaults  # noqa: E402
from core.plan import PLANS_DIR, load_plan, machine_minutes, make_plan  # noqa: E402


def _kv(items: list[str], cast) -> dict:
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        out[k] = cast(v)
    return out


def main(argv=None) -> int:
    rd = load_run_defaults()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--seed", type=int, required=True, help="master seed (pilot 20261024, dataset 20261023)")
    ap.add_argument("--counts", nargs="+", required=True, help="type=count, e.g. 1=24 2=8 3=8 4=8")
    ap.add_argument("--machines", nargs="+", required=True)
    ap.add_argument("--rounds", type=int, default=rd["n_rounds"])
    ap.add_argument("--speed", nargs="*", default=[], help="machine=factor (>1 = faster), default 1.0")
    ap.add_argument("--out-dir", default=str(PLANS_DIR))
    a = ap.parse_args(argv)
    counts = {int(k): v for k, v in _kv(a.counts, int).items()}
    speed = _kv(a.speed, float)
    try:
        path = make_plan(a.name, a.seed, counts, a.machines, a.rounds, out_dir=Path(a.out_dir), speed=speed,
                         minutes_per_round_other=rd["minutes_per_round_measured"]["other"],
                         type1_factor=rd["type1_time_factor"])
    except FileExistsError as e:
        print(f"REFUSED: {e}")
        return 1
    entries = load_plan(path)
    print(f"wrote {path} ({len(entries)} games)")
    print("estimated wall minutes per machine:", json.dumps(machine_minutes(entries, speed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
