"""Generation plans (report 01 §8.3): one central file with every game's id, type, focal pair, seed and machine.

game_id = "g_" + sha256("<master_seed>:<plan_index>")[:10], so different master seeds give disjoint ids.
Machines are assigned by longest-processing-time-first on estimated minutes, divided by each machine's
speed factor, so the slowest machine finishes as early as possible.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Mapping, Optional, Sequence

import numpy as np

from core.config import CONFIGS, atomic_write_text
from core.schema import EPISODE_TYPES, PlanEntry

PLANS_DIR = CONFIGS / "plans"
AGENTS = ("J", "M", "Q", "T", "Z")
DEFAULT_VARIANTS = {1: "collusion_v4_secrecy", 2: "placebo_v3", 3: "persona_v1", 4: "incentive_4b_v1"}


def game_id_for(master_seed: int, plan_index: int) -> str:
    return "g_" + hashlib.sha256(f"{master_seed}:{plan_index}".encode("utf-8")).hexdigest()[:10]


def build_entries(name: str, master_seed: int, counts_by_type: Mapping[int, int], machines: Sequence[str],
                  rounds: int, minutes_per_round_other: float = 4.6, type1_factor: float = 1.13,
                  speed: Optional[Mapping[str, float]] = None, variants: Mapping[int, str] = DEFAULT_VARIANTS,
                  agents: Sequence[str] = AGENTS) -> list[PlanEntry]:
    counts = {int(k): int(v) for k, v in counts_by_type.items()}
    if not machines or len(set(machines)) != len(machines):
        raise ValueError("machines must be a non-empty list of unique names")
    if any(t not in EPISODE_TYPES for t in counts):
        raise ValueError(f"episode types must be in {EPISODE_TYPES}")
    speed = {m: float((speed or {}).get(m, 1.0)) for m in machines}
    if any(s <= 0 for s in speed.values()):
        raise ValueError("speed factors must be > 0")
    pairs = list(combinations(sorted(agents), 2))
    n = sum(counts.values())
    seeds = [int(c.generate_state(1)[0]) for c in np.random.SeedSequence(master_seed).spawn(n)]

    entries, idx = [], 0
    for t in sorted(counts):
        for _ in range(counts[t]):
            gs = seeds[idx]
            focal = list(pairs[int(np.random.default_rng(gs).integers(len(pairs)))])
            est = rounds * minutes_per_round_other * (type1_factor if t == 1 else 1.0)
            entries.append(PlanEntry(game_id=game_id_for(master_seed, idx), plan_index=idx, plan_name=name,
                                     master_seed=master_seed, episode_type=t, variant=variants[t], focal_pair=focal,
                                     game_seed=gs, n_rounds=rounds, machine="", est_minutes=round(est, 2)))
            idx += 1

    # LPT: longest games first; each goes to the machine that would finish it earliest.
    load = {m: 0.0 for m in machines}
    for e in sorted(entries, key=lambda e: (-e.est_minutes, e.plan_index)):
        m = min(machines, key=lambda m: ((load[m] + e.est_minutes) / speed[m], machines.index(m)))
        e.machine = m
        load[m] += e.est_minutes
    for e in entries:
        e.config_sha256 = e.compute_sha256()
    return entries


def machine_minutes(entries: Sequence[PlanEntry], speed: Optional[Mapping[str, float]] = None) -> dict[str, float]:
    out: dict[str, float] = {}
    for e in entries:
        out[e.machine] = out.get(e.machine, 0.0) + e.est_minutes / float((speed or {}).get(e.machine, 1.0))
    return {m: round(v, 2) for m, v in out.items()}


def make_plan(name: str, master_seed: int, counts_by_type: Mapping[int, int], machines: Sequence[str], rounds: int,
              out_dir: Path = PLANS_DIR, speed: Optional[Mapping[str, float]] = None,
              minutes_per_round_other: float = 4.6, type1_factor: float = 1.13) -> Path:
    """Build and save configs/plans/<name>.json. Refuses to overwrite an existing plan."""
    path = Path(out_dir) / f"{name}.json"
    if path.exists():
        raise FileExistsError(f"{path} already exists; plans are created once")
    entries = build_entries(name, master_seed, counts_by_type, machines, rounds, minutes_per_round_other,
                            type1_factor, speed)
    doc = {"name": name, "master_seed": master_seed, "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "rounds": rounds, "counts_by_type": {str(k): v for k, v in counts_by_type.items()}, "machines": list(machines),
           "speed": {m: float((speed or {}).get(m, 1.0)) for m in machines},
           "est_minutes_per_machine": machine_minutes(entries, speed),
           "entries": [e.to_dict() for e in entries]}
    atomic_write_text(path, json.dumps(doc, indent=1))
    return path


def load_plan(path: Path) -> list[PlanEntry]:
    with open(path, encoding="utf-8") as f:
        return [PlanEntry.from_dict(e) for e in json.load(f)["entries"]]
