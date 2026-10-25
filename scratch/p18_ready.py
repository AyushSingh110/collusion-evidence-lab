"""Task 18c: readiness checklist for the replication, to run AFTER generation (prereg §5 steps 4-5).

Without --after-generation it only prints the checklist and reads nothing under data/raw/replication/.
With it, it checks:
  1. records complete: every plan game has a valid record (core.schema.validate_game, as run_plan's is_finished),
     no *.partial.json left, no record outside the plan, and each record's machine matches the plan;
  2. merge_check OK (scripts/merge_check.py, read-only; exit 0 and "MERGE CHECK OK");
  3. labels match the plan: data/replication/labels.csv == labels_csv_text(labels from the plan).
Exit 0 only if every check passes. No model calls; writes nothing.

  conda run -n collusion-lab python -B scratch/p18_ready.py                       # print the checklist only
  conda run -n collusion-lab python -B scratch/p18_ready.py --after-generation    # after both machines finished
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT  # noqa: E402
from core.labels import labels_csv_text  # noqa: E402
from core.plan import load_plan  # noqa: E402
from core.schema import validate_game  # noqa: E402
from scripts.labels_from_plan import labels_from_plan  # noqa: E402

PLAN = REPO_ROOT / "configs/plans/replication.json"
RAW = REPO_ROOT / "data/raw/replication"
LABELS = REPO_ROOT / "data/replication/labels.csv"
CHECKS = ["records complete (valid record per plan game, no partials, no extras, machine as planned)",
          "merge_check OK (scripts/merge_check.py --plan configs/plans/replication.json --raw-dir data/raw/replication)",
          "labels match the plan (data/replication/labels.csv)"]


def check_records(plan=PLAN, raw=RAW) -> list[str]:
    problems = []
    entries = {e.game_id: e for e in load_plan(plan)}
    for gid, e in entries.items():
        p = raw / f"{gid}.json"
        if not p.exists():
            problems.append(f"missing record {gid}")
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        errs = validate_game(rec)
        if errs:
            problems.append(f"invalid record {gid}: {errs[:2]}")
        m = rec.get("machine_id") or rec.get("run", {}).get("machine_id")
        if m is not None and m != e.machine:
            problems.append(f"{gid}: machine {m} != plan {e.machine}")
    problems += [f"partial file left: {p.name}" for p in raw.glob("*.partial.json")]
    problems += [f"record not in plan: {p.name}" for p in raw.glob("g_*.json")
                 if not p.name.endswith(".partial.json") and p.stem not in entries]
    return problems


def check_merge(plan=PLAN, raw=RAW) -> list[str]:
    r = subprocess.run([sys.executable, str(REPO_ROOT / "scripts/merge_check.py"), "--plan", str(plan), "--raw-dir",
                        str(raw), "--cache-dir", str(REPO_ROOT / "cache/llm")], capture_output=True, text=True)
    return [] if r.returncode == 0 and "MERGE CHECK OK" in r.stdout else [f"merge_check failed (exit {r.returncode}): "
                                                                          f"{(r.stdout + r.stderr)[-500:]}"]


def check_labels(plan=PLAN, labels=LABELS) -> list[str]:
    if not labels.exists():
        return [f"{labels} missing"]
    want = labels_csv_text(labels_from_plan(plan))
    return [] if labels.read_text(encoding="utf-8") == want else [f"{labels} differs from the labels of the plan"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--after-generation", action="store_true", help="actually run the checks (only after generation)")
    a = ap.parse_args(argv)
    if not a.after_generation:
        print("Replication readiness checklist (NOT run; pass --after-generation once both machines finished):")
        for i, c in enumerate(CHECKS, 1):
            print(f"  {i}. {c}")
        return 0
    ok = True
    for name, fn in (("records", check_records), ("merge_check", check_merge), ("labels", check_labels)):
        problems = fn()
        ok &= not problems
        print(f"[{'OK' if not problems else 'FAIL'}] {name}" + "".join(f"\n    - {p}" for p in problems[:20]))
    print("READY" if ok else "NOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
