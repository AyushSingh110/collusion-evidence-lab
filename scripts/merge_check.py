"""Check merged generation output against its plan (report 01 §8.4). Exit 0 = OK, 1 = problems listed.

  conda run -n collusion-lab python scripts/merge_check.py --plan configs/plans/pilot.json --raw-dir data/raw/pilot

Checks: (1) exactly one valid record per plan entry, no extras; (2) record config matches the plan entry
hash; (3) every call used the pinned model digest and Ollama version; (4) per-call seeds unique across the
plan; (5) every cached call's key exists in the merged cache (transport failures are never cached).
Records are found recursively under --raw-dir (so per-machine sub-folders are fine).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_pins  # noqa: E402
from core.plan import load_plan  # noqa: E402
from core.schema import PlanEntry, validate_game  # noqa: E402


def iter_calls(rec: dict):
    for r in rec["rounds"]:
        for a, e in r["stage1"].items():
            yield e["call"]
        for e in r["channel"]:
            yield e["call"]
        for e in r["stage2"]:
            yield e["call"]
        for a, e in r["stage3"].items():
            yield e["call"]


def find_cache_entry(cache_dir: Path, key: str):
    for p in cache_dir.glob(f"*/{key[:2]}/{key}.json"):
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def check(plan_path: Path, raw_dir: Path, cache_dir: Path, pins: dict) -> list[str]:
    problems: list[str] = []
    plan = {e.game_id: e for e in load_plan(plan_path)}
    files = defaultdict(list)
    for p in sorted(raw_dir.rglob("*.json")):
        if p.name.endswith(".partial.json"):
            problems.append(f"unfinished game file {p}")
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"unreadable {p}: {e}")
            continue
        files[rec.get("game_id")].append((p, rec))

    # (1) one record per entry, no extras, each valid
    for gid in plan:
        if gid not in files:
            problems.append(f"(1) missing record for plan game {gid}")
    for gid, lst in files.items():
        if gid not in plan:
            problems.append(f"(1) record {gid} is not in the plan ({[str(p) for p, _ in lst]})")
        if len(lst) > 1:
            problems.append(f"(1) duplicate records for {gid}: {[str(p) for p, _ in lst]}")
    seeds = defaultdict(list)
    for gid, lst in files.items():
        for p, rec in lst:
            errs = validate_game(rec)
            if errs:
                problems.append(f"(1) {gid} fails validation: {errs[:3]}")
            entry = plan.get(gid)
            cfg = rec.get("config", {})
            # (2) config matches the plan entry
            if entry is not None:
                rebuilt = PlanEntry(game_id=gid, plan_index=cfg.get("plan_index"), plan_name=cfg.get("plan_name"),
                                    master_seed=cfg.get("master_seed"), episode_type=cfg.get("episode_type"),
                                    variant=cfg.get("variant"), focal_pair=cfg.get("focal_pair"),
                                    game_seed=cfg.get("game_seed"), n_rounds=cfg.get("n_rounds"), machine="",
                                    est_minutes=0.0)
                if rebuilt.compute_sha256() != entry.config_sha256 or cfg.get("plan_config_sha256") != entry.config_sha256:
                    problems.append(f"(2) {gid} config does not match its plan entry hash")
            # (3) pins
            want_digest = pins["models"].get(cfg.get("agent_model"), {}).get("digest")
            if rec.get("ollama_version") != pins["ollama_version"]:
                problems.append(f"(3) {gid} Ollama version {rec.get('ollama_version')} != {pins['ollama_version']}")
            if cfg.get("agent_digest") != want_digest:
                problems.append(f"(3) {gid} agent digest {str(cfg.get('agent_digest'))[:12]} != pinned")
            for call in iter_calls(rec):
                seeds[call.get("seed")].append(gid)
                if call.get("error"):
                    continue  # transport failure: never cached, already a failures[] entry
                ce = find_cache_entry(cache_dir, call["cache_key"])
                if ce is None:  # (5)
                    problems.append(f"(5) {gid} call {call['cache_key'][:12]} ({call['purpose']}) missing from cache")
                    continue
                res = ce["result"]
                if res.get("model_digest") != want_digest or res.get("ollama_version") != pins["ollama_version"]:
                    problems.append(f"(3) {gid} call {call['cache_key'][:12]} used digest "
                                    f"{str(res.get('model_digest'))[:12]} / Ollama {res.get('ollama_version')}")
    # (4) seeds unique across the plan
    for seed, gids in seeds.items():
        if seed is None:
            problems.append(f"(4) calls without a recorded seed in {sorted(set(gids))}")
        elif len(gids) > 1:
            problems.append(f"(4) seed {seed} used by {len(gids)} calls in {sorted(set(gids))}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--cache-dir", default=str(REPO_ROOT / "cache" / "llm"))
    a = ap.parse_args(argv)
    problems = check(Path(a.plan), Path(a.raw_dir), Path(a.cache_dir), load_pins())
    if problems:
        print(f"MERGE CHECK FAILED ({len(problems)} problems):")
        for p in problems:
            print("  -", p)
        return 1
    print("MERGE CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
