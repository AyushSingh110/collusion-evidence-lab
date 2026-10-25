"""Machine C, replication: print the plan (default) or run one part of it.

  conda run -n collusion-lab python scripts/run_replication_c.py                    # dry-run plan, prints only
  conda run --no-capture-output -n collusion-lab python -u scripts/run_replication_c.py --run judge --yes

Thin wrapper (task 19C): the judge part calls study_2_3_evidence.judge.run_judge on the ids of the replication
labels file (scripts/run_judge.py only accepts ids from data/split.json). The granite part only prints its
command, and only once configs/prereg_replication_amendment1.md is committed (the amendment is a lead decision).
Every part checks that the replication prereg equals its committed blob. Rule H: the judge (~22-25 min) needs --yes.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_pins, load_run_defaults  # noqa: E402
from core.labels import read_labels  # noqa: E402
from study_2_3_evidence import replication as REP  # noqa: E402

REPL = REPO_ROOT / "data" / "replication"
DEFAULTS = {"clean": REPL / "clean", "views": REPL / "views", "labels": REPL / "labels.csv",
            "quality": REPL / "quality_fail.json"}
JUDGE_RUN, GRANITE_RUN = "judge_v1_replication", "rq9_granite_replication"
AMENDMENT = Path("configs/prereg_replication_amendment1.md")
# per-call times measured on machine C: judge median 27.5 s (report 13C §4.3); granite mean per view (report 15C §4.1)
JUDGE_S = 27.5
GRANITE_S = {"V1": 68.4, "V2": 37.4, "V3": 62.9, "V4": 45.8}


def amendment_committed() -> bool:
    r = subprocess.run(["git", "log", "-1", "--format=%H", "--", AMENDMENT.as_posix()], cwd=REPO_ROOT,
                       capture_output=True, text=True)
    return bool(r.stdout.strip()) and subprocess.run(["git", "diff", "--quiet", "HEAD", "--", AMENDMENT.as_posix()],
                                                     cwd=REPO_ROOT).returncode == 0


def plan(a) -> None:
    have = {k: Path(getattr(a, k)).exists() for k in DEFAULTS}
    n = len(read_labels(a.labels)) if have["labels"] else 48
    g_min = n * sum(GRANITE_S.values()) / 60
    print(f"machine id: {os.environ.get('COLLUSION_LAB_MACHINE')!r} (must be 'C')")
    print("files machine C needs (from machine B):")
    for k, desc in (("clean", "replication CleanGames (render_views --clean-out data/replication)"),
                    ("views", "rendered views, at least V1-V4 (only for the granite part)"),
                    ("labels", "data/replication/labels.csv (sha256 27a0d4bf... in report 18b)"),
                    ("quality", "quality-fail ids, JSON list or {\"quality_fail\": [...]}")):
        print(f"  [{'present' if have[k] else 'MISSING'}] {getattr(a, k)}  - {desc}")
    ids_note = "ids from the labels file" if have["labels"] else "48 ids (labels file not here yet)"
    print(f"\n1. judge (Study 2.3, prereg §4): {n} calls x {JUDGE_S} s = {n * JUDGE_S / 60:.0f} min "
          f"(budget ~25 min; {ids_note})")
    print(f"   conda run --no-capture-output -n collusion-lab python -u scripts/run_replication_c.py --run judge --yes")
    print(f"   -> runs/{JUDGE_RUN}/outputs/judge.jsonl; cache cache/llm/C/")
    print("2. analysis (once, after the judge run; no model calls):")
    print(f"   conda run -n collusion-lab python scripts/analyse_replication_23.py --clean-dir {a.clean} "
          f"--labels {a.labels} --judge runs/{JUDGE_RUN}/outputs/judge.jsonl --quality {a.quality}")
    ok = amendment_committed()
    print(f"3. granite second monitor (ONLY if {AMENDMENT} is committed: {'yes' if ok else 'NO - not allowed yet'}):")
    print(f"   {n * 4} calls (V1-V4), measured basis {g_min:.0f} min = {g_min / 60:.1f} h "
          f"(V1 {GRANITE_S['V1']} / V2 {GRANITE_S['V2']} / V3 {GRANITE_S['V3']} / V4 {GRANITE_S['V4']} s); budget ~3.5 h")
    if ok:
        print(f"   conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input {a.views} "
              f"--views V1,V2,V3,V4 --run-id {GRANITE_RUN} --prompt monitor_v3_pairs_ctx16k_granite "
              f"--sec-per-call 55 --yes")


def run_judge_part(a) -> int:
    from core.llm import CachedLLM, OllamaTransport, PinError, TransportError
    from study_2_3_evidence.judge import load_config, pending, run_judge
    if os.environ.get("COLLUSION_LAB_MACHINE") != "C":
        print("REFUSED: COLLUSION_LAB_MACHINE is not C (judge calls run on machine C only)")
        return 2
    if not Path(a.labels).exists():
        print(f"REFUSED: labels file {a.labels} does not exist (it comes from machine B)")
        return 2
    ids = sorted(lb.game_id for lb in read_labels(a.labels))
    missing = [g for g in ids if not (Path(a.clean) / f"{g}.json").exists()]
    if missing:
        print(f"REFUSED: {len(missing)} games have no clean file, e.g. {missing[:3]}")
        return 2
    todo = pending(ids, JUDGE_RUN, REPO_ROOT / "runs")
    est = len(todo) * JUDGE_S / 60
    print(f"judge: {len(ids)} games, {len(todo)} pending; estimate {est:.0f} min")
    if est > 15 and not a.yes:
        print("REFUSED: estimate above 15 min. Get the user's OK, then re-run with --yes.")
        return 2
    cfg, rd = load_config(), load_run_defaults()
    try:
        llm = CachedLLM(transport=OllamaTransport(rd["llm"]["base_url"]), pins=load_pins(), models=[cfg.model],
                        cache_dir=REPO_ROOT / "cache" / "llm", timeout_s=rd["llm"]["timeout_s"],
                        retry_delays_s=rd["llm"]["retry_delays_s"], keep_alive=rd["llm"]["keep_alive"])
    except (PinError, TransportError) as e:
        print(f"REFUSED (start-up pin check): {e}")
        return 3
    s = run_judge(Path(a.clean), todo, JUDGE_RUN, llm, cfg)
    print(f"done: {s['written']} written, {s['transport_errors']} transport errors, {s['not_parse_ok']} not parse_ok, "
          f"{s['truncation_suspect']} truncation-suspect")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=v)
    ap.add_argument("--run", choices=("judge",), help="run this part (default: print the plan only)")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    try:
        REP.check_prereg()
    except REP.ReplicationError as e:
        print(f"REFUSED: {e}")
        return 2
    if a.run is None:
        plan(a)
        return 0
    return run_judge_part(a)


if __name__ == "__main__":
    sys.exit(main())
