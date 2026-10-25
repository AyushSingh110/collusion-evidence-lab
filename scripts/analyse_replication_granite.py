"""Replication amendment 1: G1-G4 (granite3.3:8b vs the frozen llama monitor) + descriptive measures, run ONCE.

  conda run -n collusion-lab python scripts/analyse_replication_granite.py --plan        # prints the run order only
  conda run -n collusion-lab python scripts/analyse_replication_granite.py \
      --labels data/replication/labels.csv --quality data/replication/quality_fail.json \
      --llama <machine B replication monitor.jsonl> \
      --granite runs/rq9_granite_replication/outputs/monitor.jsonl [--out runs/replication_granite]

Refuses before computing anything unless: the base prereg and amendment 1 equal their committed blobs and recorded
sha256; the frozen monitor file (ccc4bf07...) and the granite manifest (d6b38e3f...) match; every line is sample 0, a
V1-V4 view, from the right prompt version / model / digest, with the system prompt of the committed manifest; every
game id is in the replication labels file and none is an ORIGINAL dataset game; no earlier results file exists.
Absent or failed lines are counted as missing (amendment 1 §2), never fatal. Primary = all labelled games;
sensitivity = without the quality-fail ids.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, text_file_sha256  # noqa: E402
from study_2_2_views import replication_granite as RG  # noqa: E402
from study_2_2_views.analysis import load_labels  # noqa: E402

RUN_ORDER = """Run order on machine C (printed, not run):
 (a) Machine B delivers: data/replication/clean/, data/replication/views/ (V1-V4), data/replication/labels.csv,
     data/replication/quality_fail.json ({"quality_fail": [...]}), and B's replication monitor.jsonl
     (frozen llama monitor, 48 games x 8 views; only V1-V4 are read here).
 (b) Judge (Study 2.3): 48 calls, ~22 min - needs the lead's OK.
     conda run --no-capture-output -n collusion-lab python -u scripts/run_replication_c.py --run judge --yes
 (c) Granite (amendment 1): 192 calls, ~2.9 h (budget 3.5 h) - needs the lead's OK.
     conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input data/replication/views \\
         --views V1,V2,V3,V4 --run-id rq9_granite_replication --prompt monitor_v3_pairs_ctx16k_granite --sec-per-call 55 --yes
 (d) One run each (no model calls):
     conda run -n collusion-lab python scripts/analyse_replication_23.py --clean-dir data/replication/clean \\
         --labels data/replication/labels.csv --judge runs/judge_v1_replication/outputs/judge.jsonl \\
         --quality data/replication/quality_fail.json
     conda run -n collusion-lab python scripts/analyse_replication_granite.py --labels data/replication/labels.csv \\
         --quality data/replication/quality_fail.json --llama <B's monitor.jsonl> \\
         --granite runs/rq9_granite_replication/outputs/monitor.jsonl"""


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout


def run(a) -> dict:
    if (a.out / "results.json").exists():
        raise RG.RefusedError(f"{a.out / 'results.json'} exists; the analysis runs once")
    shas = {str(rel): RG.check_committed(rel, sha, a.git, a.repo_root) for rel, sha in (RG.PREREG, RG.AMENDMENT)}
    cfgs = RG.check_configs(a.repo_root)
    labels = load_labels(a.labels)
    original = set(load_labels(a.original_labels)) if a.original_labels.exists() else set()
    overlap = sorted(set(labels) & original)
    if overlap:
        raise RG.RefusedError(f"{len(overlap)} labelled games are ORIGINAL dataset games, e.g. {overlap[:3]}")
    lines = {m: RG.load_lines(p, m, cfgs[m], labels, original) for m, p in (("llama", a.llama), ("granite", a.granite))}
    qfail = RG.load_quality(a.quality)
    if not qfail <= set(labels):
        raise RG.RefusedError("quality_fail lists games that are not labelled")
    games = sorted(labels)
    res = {"prereg_sha256": shas, "n_games": len(games), "quality_fail": sorted(qfail), "b": a.b, "seed": a.seed,
           "machine_id": os.environ.get("COLLUSION_LAB_MACHINE") or None,
           "inputs": {k: {"path": str(p), "sha256_lf": text_file_sha256(p)} for k, p in
                      (("labels", a.labels), ("quality", a.quality), ("llama", a.llama), ("granite", a.granite))}}
    for name, gs in (("primary", games), ("sensitivity", [g for g in games if g not in qfail])):
        res[name] = {"n": len(gs),
                     "hypotheses": RG.hypotheses(gs, lines["llama"], lines["granite"], labels, a.b, a.seed),
                     "descriptive": {m: RG.descriptive(gs, lines[m], labels, a.b, a.seed) for m in lines}}
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="print the run order and exit")
    ap.add_argument("--labels", type=Path)
    ap.add_argument("--quality", type=Path)
    ap.add_argument("--llama", type=Path, help="machine B's replication monitor.jsonl (frozen llama monitor)")
    ap.add_argument("--granite", type=Path, help="machine C's granite replication monitor.jsonl")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "replication_granite")
    ap.add_argument("--original-labels", type=Path, default=REPO_ROOT / "data" / "labels.csv")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    ap.add_argument("--b", type=int, default=RG.B)
    ap.add_argument("--seed", type=int, default=RG.SEED)
    a = ap.parse_args(argv)
    if a.plan:
        print(RUN_ORDER)
        return 0
    if None in (a.labels, a.quality, a.llama, a.granite):
        ap.error("--labels, --quality, --llama and --granite are required (or use --plan)")
    a.git = _git
    try:
        res = run(a)
    except RG.RefusedError as e:
        print(f"REFUSED: {e}")
        return 2
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "results.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    for name in ("primary", "sensitivity"):
        print(f"{name} (n = {res[name]['n']}):")
        for h, d in res[name]["hypotheses"].items():
            est = (f"D_llama {d['D_llama']['estimate']} [{d['D_llama']['ci_low']}, {d['D_llama']['ci_high']}], "
                   f"D_granite {d['D_granite']['estimate']} [{d['D_granite']['ci_low']}, {d['D_granite']['ci_high']}]"
                   if h == "G3" else f"{d['estimate']} [{d['ci_low']}, {d['ci_high']}]")
            print(f"  {h}: {est} -> {d['verdict']}")
    print(f"-> {a.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
