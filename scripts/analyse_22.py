"""Study 2.2 RQ1-RQ8 tables from monitor outputs (no model calls).

Dev (choose + freeze):
  conda run -n collusion-lab python scripts/analyse_22.py --mode dev --monitor runs/<run>/outputs/monitor.jsonl \
      --labels data/labels.csv --split data/split.json [--signals <game_signals.csv>] \
      --freeze-out configs/frozen/study22_<name>.json [--monitor-manifest configs/monitor/manifest.json]
  -> prints the frozen file's sha256: record it in the DEVLOG BEFORE any test run.
Test (report once, with the frozen choices):
  conda run -n collusion-lab python scripts/analyse_22.py --mode test --monitor ... --labels ... --split ... \
      --frozen configs/frozen/study22_<name>.json --frozen-sha256 <hex>
  Refuses unless the frozen file's sha256 and the monitor prompt version match.
Outputs: <out>/rq1_per_view_<split>.csv, rq2_rq4_rq5_rq6_rq7_paired_<split>.csv, rq3_fpr_by_type_<split>.csv,
rq8_top1_pair_<split>.csv, summary_<split>.md (default out: runs/analysis22/).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT  # noqa: E402
from study_2_2_views import analysis as A  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("dev", "test"), required=True)
    ap.add_argument("--monitor", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--signals", type=Path, help="game-level code signals CSV (for RQ7 / RQ8 evidence argmax)")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "analysis22")
    ap.add_argument("--freeze-out", type=Path, help="dev mode: where to write the frozen choices JSON")
    ap.add_argument("--monitor-manifest", type=Path, help="dev mode: monitor manifest to record (sha256)")
    ap.add_argument("--frozen", type=Path, help="test mode: frozen choices JSON written in dev mode")
    ap.add_argument("--frozen-sha256", help="test mode: the sha256 recorded in the DEVLOG")
    ap.add_argument("--b", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261023)
    a = ap.parse_args(argv)

    scores, pairs, versions = A.load_monitor(a.monitor, a.sample_idx)
    labels, split = A.load_labels(a.labels), A.load_split(a.split)
    signals = A.load_signals(a.signals) if a.signals else None
    missing = sorted({g for g, _ in scores} - set(labels))
    if missing:
        print(f"REFUSED: {len(missing)} monitor games are not in the labels file (e.g. {missing[:3]})")
        return 2

    if a.mode == "dev":
        choices = A.dev_choices(scores, labels, split["dev"])
        note = "DEV split: thresholds and view choices are fitted here (in-sample)."
        text = A.build(scores, pairs, labels, split["dev"], choices, "dev", a.out, signals, a.b, a.seed, note)
        print(text)
        if a.freeze_out:
            man_sha = A.file_sha256(a.monitor_manifest) if a.monitor_manifest else None
            sha = A.write_frozen(choices, versions, man_sha, a.freeze_out)
            print(f"FROZEN choices written to {a.freeze_out}\nsha256 {sha}\n"
                  "Record this sha256 in the DEVLOG BEFORE any test run.")
        return 0

    try:
        frozen = A.check_frozen(a.frozen, a.frozen_sha256, versions)
    except A.FrozenError as e:
        print(f"REFUSED: {e}")
        return 3
    note = f"TEST split, frozen dev choices `{a.frozen}` (sha256 {a.frozen_sha256}); nothing refit on test."
    print(A.build(scores, pairs, labels, split["test"], frozen, "test", a.out, signals, a.b, a.seed, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
