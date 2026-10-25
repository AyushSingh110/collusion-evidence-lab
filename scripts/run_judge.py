"""Run the Study 2.3 conversation judge (configs/judge, llama3.1:8b, pinned) and write runs/<run_id>/.

Run from the repo root (machine C only):
  conda run --no-capture-output -n collusion-lab python -u scripts/run_judge.py \
      --games dev --run-id judge_v1 [--sample-idx 1] [--limit 3] [--dry-run] [--yes]

--games: dev | test | all | a comma list of game ids (from data/split.json). --limit N takes the first N pending
games (sorted), e.g. for the 3-call measurement. --dry-run prints the number of pending calls and the estimated
time. Rule H: a run estimated at more than 15 minutes refuses to start without --yes (get the user's OK first).
Resumable: re-running the same --run-id skips what is already in runs/<run_id>/outputs/judge.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_pins, load_run_defaults  # noqa: E402
from study_2_3_evidence.judge import load_config, pending, run_judge  # noqa: E402

DEFAULT_SEC_PER_CALL = 20.0
LIMIT_MIN = 15.0


def select_games(spec: str, split_path: Path) -> list[str]:
    split = json.loads(split_path.read_text(encoding="utf-8"))
    if spec == "dev":
        return sorted(split["dev"])
    if spec == "test":
        return sorted(split["test"])
    if spec == "all":
        return sorted(split["dev"] + split["test"])
    ids = [g.strip() for g in spec.split(",") if g.strip()]
    known = set(split["dev"]) | set(split["test"])
    unknown = [g for g in ids if g not in known]
    if unknown:
        raise SystemExit(f"unknown game ids: {unknown}")
    return sorted(ids)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clean-dir", type=Path, default=REPO_ROOT / "data" / "clean")
    ap.add_argument("--split", type=Path, default=REPO_ROOT / "data" / "split.json")
    ap.add_argument("--games", required=True, help="dev | test | all | comma list of game ids")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--limit", type=int, help="only the first N pending games")
    ap.add_argument("--runs-dir", type=Path, default=REPO_ROOT / "runs")
    ap.add_argument("--sec-per-call", type=float, default=DEFAULT_SEC_PER_CALL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help=f"allow a run estimated above {LIMIT_MIN:.0f} min")
    a = ap.parse_args(argv)

    games = select_games(a.games, a.split)
    todo = pending(games, a.run_id, a.runs_dir, a.sample_idx)
    if a.limit is not None:
        todo = todo[:a.limit]
    est = len(todo) * a.sec_per_call / 60
    print(f"judge: {len(games)} games, {len(todo)} pending calls (sample_idx {a.sample_idx}); "
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
    s = run_judge(a.clean_dir, todo, a.run_id, llm, cfg, runs_dir=a.runs_dir, sample_idx=a.sample_idx)
    print(f"done: {s['written']} written, {s['transport_errors']} transport errors, {s['not_parse_ok']} not parse_ok, "
          f"{s['truncation_suspect']} truncation-suspect, {s['skipped_already_done']} skipped (already done)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
