"""Write a labels CSV from a plan file, to --out only. Never writes a split (replication prereg §2).

Same rows and format as data/labels.csv: every plan entry goes through core.labels.label_from_config (Rule G: the
label comes only from episode_type) and core.labels.write_labels. Refuses to write data/labels.csv or
data/split.json, refuses to overwrite any existing file, and refuses to run without --out.

  conda run -n collusion-lab python scripts/labels_from_plan.py --plan configs/plans/replication.json \
      --out data/replication/labels.csv
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.labels import LABELS_PATH, label_from_config, labels_sha256, write_labels  # noqa: E402
from core.plan import load_plan  # noqa: E402
from core.split import SPLIT_PATH  # noqa: E402

PROTECTED = (LABELS_PATH, SPLIT_PATH)


def _same_path(a: Path, b: Path) -> bool:
    return os.path.normcase(str(Path(a).resolve())) == os.path.normcase(str(Path(b).resolve()))


def labels_from_plan(plan_path: Path):
    return [label_from_config({"game_id": e.game_id, "episode_type": e.episode_type, "focal_pair": e.focal_pair,
                               "variant": e.variant, "synthetic": False}) for e in load_plan(plan_path)]


def write_labels_only(plan_path: Path, out: Path, protected=PROTECTED):
    """Labels for every plan entry -> out. Raises on a protected path or an existing out file."""
    if any(_same_path(out, p) for p in protected):
        raise PermissionError(f"{out} is a protected path (the ONE labels file / split); refusing")
    if Path(out).exists():
        raise FileExistsError(f"{out} already exists; refusing to overwrite")
    labels = labels_from_plan(plan_path)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    write_labels(labels, Path(out))
    return labels


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True, help="output CSV (never data/labels.csv or data/split.json)")
    a = ap.parse_args(argv)
    try:
        labels = write_labels_only(Path(a.plan), Path(a.out))
    except (PermissionError, FileExistsError) as e:
        print(f"REFUSED: {e}")
        return 1
    counts = {t: sum(lb.episode_type == t for lb in labels) for t in sorted({lb.episode_type for lb in labels})}
    print(f"wrote {a.out}: {len(labels)} labels, per type {counts}, labels sha256 {labels_sha256(labels)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
