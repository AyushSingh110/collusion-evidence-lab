"""Run this machine's games from a plan, one at a time. Skips finished games, resumes unfinished ones.

  conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/pilot.json --dry-run
  conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/pilot.json

--machine defaults to the COLLUSION_LAB_MACHINE environment variable. Records go to data/raw/<plan>/,
the LLM cache to cache/llm/<machine_id>/. Refuses to start if the Ollama pin check fails.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_json, load_pins, load_run_defaults  # noqa: E402
from core.plan import load_plan  # noqa: E402
from core.schema import validate_game  # noqa: E402

CALLS_PER_ROUND = {1: 19, 2: 15, 3: 15, 4: 15}


def is_finished(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return validate_game(json.loads(path.read_text(encoding="utf-8"))) == []
    except (OSError, json.JSONDecodeError):
        return False


def main(argv=None, transport=None) -> int:
    rd = load_run_defaults()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--machine", default=os.environ.get("COLLUSION_LAB_MACHINE", ""))
    ap.add_argument("--raw-dir", default=None, help="default data/raw/<plan name>")
    ap.add_argument("--cache-dir", default=str(REPO_ROOT / "cache" / "llm"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not a.machine:
        print("No machine letter: pass --machine A|B|C or set COLLUSION_LAB_MACHINE.")
        return 2
    plan_doc = load_json(Path(a.plan))
    entries = [e for e in load_plan(Path(a.plan)) if e.machine == a.machine]
    raw_dir = Path(a.raw_dir) if a.raw_dir else REPO_ROOT / "data" / "raw" / plan_doc["name"]
    speed = float(plan_doc.get("speed", {}).get(a.machine, 1.0))
    todo = [e for e in entries if not is_finished(raw_dir / f"{e.game_id}.json")]
    calls = sum(CALLS_PER_ROUND[e.episode_type] * e.n_rounds for e in todo)
    minutes = sum(e.est_minutes for e in todo) / speed
    print(f"plan {plan_doc['name']}: machine {a.machine} has {len(entries)} games, {len(entries) - len(todo)} finished, "
          f"{len(todo)} to run: {calls} calls, about {minutes:.0f} min (speed factor {speed})")
    for e in todo:
        partial = (raw_dir / f"{e.game_id}.partial.json").exists()
        print(f"  {e.game_id} type {e.episode_type} focal {'-'.join(e.focal_pair)} {e.n_rounds} rounds "
              f"~{e.est_minutes / speed:.0f} min{' (resume)' if partial else ''}")
    if a.dry_run or not todo:
        return 0

    from core.generate.runner import MODEL, run_game  # imports the harness builders
    from core.llm import CachedLLM, OllamaTransport, PinError
    try:
        llm = CachedLLM(transport=transport or OllamaTransport(rd["llm"]["base_url"]), pins=load_pins(), models=[MODEL],
                        cache_dir=Path(a.cache_dir), timeout_s=rd["llm"]["timeout_s"],
                        retry_delays_s=rd["llm"]["retry_delays_s"], keep_alive=rd["llm"]["keep_alive"])
    except PinError as err:
        print(f"REFUSED: pin check failed: {err}\nRun scripts/check_env.py.")
        return 1
    t_start = time.monotonic()

    def progress(gid, rnd, n, elapsed):
        print(f"  [{time.strftime('%H:%M:%S')}] {gid} round {rnd}/{n} done, game {elapsed / 60:.1f} min, "
              f"session {(time.monotonic() - t_start) / 60:.1f} min", flush=True)

    for i, e in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] start {e.game_id} (type {e.episode_type})", flush=True)
        rec = run_game(e, llm, run_defaults=rd, raw_dir=raw_dir, machine=a.machine, progress=progress)
        errs = validate_game(rec)
        print(f"[{i}/{len(todo)}] done {e.game_id}: {len(rec['failures'])} failures, "
              f"{rec['usage']['calls']} calls ({rec['usage']['cache_hits']} cache hits), {rec['wall_s'] / 60:.1f} min"
              + (f", VALIDATION ERRORS: {errs}" if errs else ""), flush=True)
    print(f"all done in {(time.monotonic() - t_start) / 60:.1f} min. Send the lead: {raw_dir} and "
          f"{Path(a.cache_dir) / llm.machine_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
