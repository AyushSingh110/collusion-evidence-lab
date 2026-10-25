"""Code signals (core.evidence.signals) for a folder of CleanGames, with a FROZEN honest baseline loaded from a file.

Never refits the baseline (replication prereg §3): the default source is configs/frozen/rules_frozen.json
("honest_baseline", fitted on the 4 original dev Type 2 games). Writes <out>/game_signals.csv (game level = max over
pairs, argmax pair), <out>/pair_signals.csv and <out>/baseline_source.json. Refuses to write into an existing --out.

  conda run -n collusion-lab python scripts/signals_from_clean.py --clean data/replication/clean \
      --labels data/replication/labels.csv --out runs/replication/signals
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT  # noqa: E402
from core.evidence import signals as S  # noqa: E402

DEFAULT_BASELINE = REPO_ROOT / "configs" / "frozen" / "rules_frozen.json"


def compute(clean_dir: Path, game_ids, base: S.HonestBaseline) -> tuple[list[dict], list[dict]]:
    pair_rows, game_rows = [], []
    for g in sorted(game_ids):
        c = json.loads((Path(clean_dir) / f"{g}.json").read_text(encoding="utf-8"))
        rows = S.pair_signal_table(c, base)
        pair_rows += rows
        game_rows.append(S.game_signals(rows))
    return pair_rows, game_rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clean", type=Path, required=True, help="folder of CleanGame <game_id>.json")
    ap.add_argument("--labels", type=Path, required=True, help="labels CSV: the games to compute (all of them)")
    ap.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists() and any(a.out.iterdir()):
        print(f"REFUSED: {a.out} exists and is not empty")
        return 1
    with open(a.labels, encoding="utf-8", newline="") as f:
        ids = [r["game_id"] for r in csv.DictReader(f)]
    missing = [g for g in ids if not (a.clean / f"{g}.json").exists()]
    if missing:
        print(f"REFUSED: {len(missing)} labelled games have no CleanGame in {a.clean}, e.g. {missing[:3]}")
        return 1
    base, source = S.load_honest_baseline(a.baseline)
    pair_rows, game_rows = compute(a.clean, ids, base)
    a.out.mkdir(parents=True, exist_ok=True)
    _write_csv(a.out / "pair_signals.csv", pair_rows)
    _write_csv(a.out / "game_signals.csv", game_rows)
    (a.out / "baseline_source.json").write_text(json.dumps(
        {"baseline": base.__dict__, "source": source, "refitted": False, "n_games": len(ids)}, indent=1),
        encoding="utf-8")
    print(f"wrote {a.out}: {len(game_rows)} games; baseline from {source['path']} (key {source['key']}, "
          f"sha256 {source['sha256_lf'][:16]}...), not refitted; Dep NA in {sum(r['Dep'] is None for r in game_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
