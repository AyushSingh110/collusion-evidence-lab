"""Write data/labels.csv and data/split.json directly from a plan file (before any game is generated).

Labels depend only on episode_type in the config (Rule G), which the plan already fixes, so the ONE split
can be made before generation. Refuses to overwrite an existing split (and a differing labels file).

  conda run -n collusion-lab python scripts/labels_split_from_plan.py --plan configs/plans/dataset.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_run_defaults  # noqa: E402
from core.labels import LABELS_PATH, label_from_config, write_labels  # noqa: E402
from core.plan import load_plan  # noqa: E402
from core.split import SPLIT_PATH, make_split  # noqa: E402


def labels_from_plan(plan_path: Path):
    return [label_from_config({"game_id": e.game_id, "episode_type": e.episode_type, "focal_pair": e.focal_pair,
                               "variant": e.variant, "synthetic": False}) for e in load_plan(plan_path)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--labels", default=str(LABELS_PATH))
    ap.add_argument("--split", default=str(SPLIT_PATH))
    ap.add_argument("--seed", type=int, default=load_run_defaults()["master_seeds"]["dataset"])
    ap.add_argument("--dev-frac", type=float, default=0.5)
    a = ap.parse_args(argv)
    labels = labels_from_plan(Path(a.plan))
    try:
        write_labels(labels, Path(a.labels))
        split = make_split(labels, a.seed, a.dev_frac, path=Path(a.split))
    except FileExistsError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"wrote {a.labels} ({len(labels)} labels) and {a.split}: dev {len(split.dev)}, test {len(split.test)}, "
          f"labels sha256 {split.labels_sha256[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
