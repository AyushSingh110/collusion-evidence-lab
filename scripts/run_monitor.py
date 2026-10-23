"""Score rendered views with the monitor (llama3.1:8b, pinned) and write runs/<run_id>/.

Run from the repo root:
  conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py \
      --input data/views --views V1,V2,V3,V4 --run-id mon_v1_smoke [--games g_a,g_b] [--dry-run] [--yes]

--dry-run prints the number of pending calls and the estimated time. Rule H: a run estimated at more
than 15 minutes refuses to start without --yes (get the user's OK first). Resumable: re-running the
same --run-id skips what is already in runs/<run_id>/outputs/monitor.jsonl.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_pins, load_run_defaults  # noqa: E402
from study_2_2_views.monitor import load_config, pending, run_monitor  # noqa: E402

# report 01 §3.6 [M]: 30-48 s for a ~3k-token View 3 call with llama3.1:8b on the lead laptop
DEFAULT_SEC_PER_CALL = 35.0
LIMIT_MIN = 15.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "views")
    ap.add_argument("--views", required=True, help="comma list of view folders to score, e.g. V1,V2,V3,V4")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--games", help="optional comma list of game ids")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--runs-dir", type=Path, default=REPO_ROOT / "runs")
    ap.add_argument("--sec-per-call", type=float, default=DEFAULT_SEC_PER_CALL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help=f"allow a run estimated above {LIMIT_MIN:.0f} min")
    a = ap.parse_args(argv)

    games = set(a.games.split(",")) if a.games else None
    files = [p for v in a.views.split(",") for p in sorted((a.input / v.strip()).glob("*.txt"))
             if games is None or p.stem in games]
    todo = pending(files, a.run_id, a.runs_dir, a.sample_idx)
    est = len(todo) * a.sec_per_call / 60
    print(f"{len(files)} view files, {len(todo)} pending calls (sample_idx {a.sample_idx}); "
          f"estimate {est:.1f} min at {a.sec_per_call:.0f} s/call")
    if a.dry_run:
        return 0
    if est > LIMIT_MIN and not a.yes:
        print(f"REFUSED: estimate above {LIMIT_MIN:.0f} min. Get the user's OK, then re-run with --yes.")
        return 2
    if not todo:
        return 0

    from core.llm import CachedLLM, OllamaTransport, PinError, TransportError
    cfg = load_config()
    rd = load_run_defaults()
    try:
        llm = CachedLLM(transport=OllamaTransport(rd["llm"]["base_url"]), pins=load_pins(), models=[cfg.model],
                        cache_dir=REPO_ROOT / "cache" / "llm", timeout_s=rd["llm"]["timeout_s"],
                        retry_delays_s=rd["llm"]["retry_delays_s"], keep_alive=rd["llm"]["keep_alive"])
    except (PinError, TransportError) as e:
        print(f"REFUSED (start-up pin check): {e}")
        return 3
    s = run_monitor(files, a.run_id, llm, cfg, runs_dir=a.runs_dir, sample_idx=a.sample_idx)
    print(f"done: {s['written']} written, {s['transport_errors']} transport errors, "
          f"{s['truncation_suspect']} truncation-suspect, {s['skipped_already_done']} skipped (already done)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
