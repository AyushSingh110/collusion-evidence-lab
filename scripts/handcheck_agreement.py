"""Amendment 1: pilot-1 two-rater hand-check agreement (DESCRIPTIVE ONLY - it does not decide the gate).

  conda run -n collusion-lab python scripts/handcheck_agreement.py --key runs/pilot/handcheck_key.csv \
      --r1 runs/pilot/handcheck_blind_R1.csv --r2 runs/pilot/handcheck_blind_R2.csv

Reports percent agreement and Cohen's kappa for: R1 vs rule v1, R2 vs rule v1, R1 vs rule v2, R2 vs rule v2,
R1 vs R2. Each comparison uses the rows where both sides have a label; unfilled rows are counted.
Writes runs/pilot/handcheck_agreement.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, atomic_write_text  # noqa: E402
from core.stats.basic import cohen_kappa, percent_agreement  # noqa: E402

PAIRS = [("R1", "rule_v1"), ("R2", "rule_v1"), ("R1", "rule_v2"), ("R2", "rule_v2"), ("R1", "R2")]


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _labels(rows: list[dict], col: str, who: str) -> dict[str, int | None]:
    out = {}
    for r in rows:
        v = (r.get(col) or "").strip()
        if v not in ("", "0", "1"):
            raise ValueError(f"{who}: {col} must be 0, 1 or empty; row {r.get('row_id')} has {v!r}")
        out[r["row_id"]] = int(v) if v else None
    return out


def agreement(key_rows: list[dict], r1_rows: list[dict], r2_rows: list[dict]) -> dict:
    ids = [r["row_id"] for r in key_rows]
    for who, rows in (("R1", r1_rows), ("R2", r2_rows)):
        if sorted(r["row_id"] for r in rows) != sorted(ids):
            raise ValueError(f"{who} sheet row_ids do not match the key")
    src = {"rule_v1": _labels(key_rows, "U_v1", "key"), "rule_v2": _labels(key_rows, "U_v2", "key"),
           "R1": _labels(r1_rows, "U_hand", "R1"), "R2": _labels(r2_rows, "U_hand", "R2")}
    res = {"descriptive_only": True, "cells": len(ids),
           "filled": {"R1": sum(v is not None for v in src["R1"].values()),
                      "R2": sum(v is not None for v in src["R2"].values())},
           "comparisons": {}}
    for x, y in PAIRS:
        both = [i for i in ids if src[x][i] is not None and src[y][i] is not None]
        a, b = [src[x][i] for i in both], [src[y][i] for i in both]
        res["comparisons"][f"{x} vs {y}"] = {"n": len(both), "agree": sum(p == q for p, q in zip(a, b)),
                                             "percent": percent_agreement(a, b), "kappa": cohen_kappa(a, b)}
    return res


def _fmt(v):
    return "NA" if v is None else f"{v:.3f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", type=Path, default=REPO_ROOT / "runs" / "pilot" / "handcheck_key.csv")
    ap.add_argument("--r1", type=Path, default=REPO_ROOT / "runs" / "pilot" / "handcheck_blind_R1.csv")
    ap.add_argument("--r2", type=Path, default=REPO_ROOT / "runs" / "pilot" / "handcheck_blind_R2.csv")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "pilot" / "handcheck_agreement.json")
    a = ap.parse_args(argv)
    res = agreement(_read(a.key), _read(a.r1), _read(a.r2))
    print(f"Pilot-1 hand-check agreement (DESCRIPTIVE ONLY, not the gate): {res['cells']} cells; "
          f"filled R1 {res['filled']['R1']}, R2 {res['filled']['R2']}")
    for name, c in res["comparisons"].items():
        print(f"  {name:16s} n={c['n']:3d}  agree={c['agree']:3d}  percent={_fmt(c['percent'])}  kappa={_fmt(c['kappa'])}")
    atomic_write_text(a.out, json.dumps(res, indent=1) + "\n")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
