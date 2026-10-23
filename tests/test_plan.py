import json
from itertools import combinations

import pytest

from core.plan import build_entries, load_plan, machine_minutes, make_plan

DATASET = {1: 24, 2: 8, 3: 8, 4: 8}
PILOT = {1: 4, 2: 2, 3: 1, 4: 1}
M3 = ["A", "B", "C"]


def test_plan_is_deterministic(tmp_path):
    p1 = make_plan("d1", 20261023, DATASET, M3, 6, out_dir=tmp_path)
    p2 = make_plan("d2", 20261023, DATASET, M3, 6, out_dir=tmp_path)
    e1 = [(e.game_id, e.focal_pair, e.game_seed, e.machine) for e in load_plan(p1)]
    e2 = [(e.game_id, e.focal_pair, e.game_seed, e.machine) for e in load_plan(p2)]
    assert e1 == e2 and len(e1) == 48


def test_game_ids_unique_and_well_formed():
    ids = [e.game_id for e in build_entries("d", 20261023, DATASET, M3, 6)]
    assert len(set(ids)) == 48 and all(i.startswith("g_") and len(i) == 12 for i in ids)


def test_pilot_and_dataset_ids_are_disjoint():
    d = {e.game_id for e in build_entries("d", 20261023, DATASET, M3, 6)}
    p = {e.game_id for e in build_entries("p", 20261024, PILOT, M3, 6)}
    assert not d & p
    seeds_d = {e.game_seed for e in build_entries("d", 20261023, DATASET, M3, 6)}
    seeds_p = {e.game_seed for e in build_entries("p", 20261024, PILOT, M3, 6)}
    assert not seeds_d & seeds_p


def test_plan_refuses_to_overwrite(tmp_path):
    make_plan("pilot", 20261024, PILOT, M3, 6, out_dir=tmp_path)
    with pytest.raises(FileExistsError):
        make_plan("pilot", 20261024, PILOT, M3, 6, out_dir=tmp_path)


@pytest.mark.parametrize("counts", [DATASET, PILOT])
def test_machine_minutes_balanced_within_one_game(counts):
    entries = build_entries("x", 20261023, counts, M3, 6)
    mins = machine_minutes(entries)
    longest = max(e.est_minutes for e in entries)
    assert max(mins.values()) - min(mins.values()) <= longest + 1e-9
    assert sorted({e.machine for e in entries}) == M3


def test_speed_factor_shifts_work_to_faster_machine():
    entries = build_entries("x", 20261023, DATASET, M3, 6, speed={"A": 2.0, "B": 1.0, "C": 1.0})
    raw = {m: sum(e.est_minutes for e in entries if e.machine == m) for m in M3}
    assert raw["A"] > raw["B"] and raw["A"] > raw["C"]
    wall = machine_minutes(entries, {"A": 2.0, "B": 1.0, "C": 1.0})
    assert max(wall.values()) - min(wall.values()) <= max(e.est_minutes for e in entries)


def test_entries_have_valid_focal_pairs_types_and_hashes():
    entries = build_entries("x", 20261023, DATASET, M3, 6)
    pairs = set(combinations("JMQTZ", 2))
    assert all(tuple(e.focal_pair) in pairs for e in entries)
    assert [sum(e.episode_type == t for e in entries) for t in (1, 2, 3, 4)] == [24, 8, 8, 8]
    assert all(e.config_sha256 == e.compute_sha256() for e in entries)
    a, b = entries[0], entries[1]
    a2 = json.loads(json.dumps(a.to_dict()))
    a2["machine"] = "Z"
    from core.schema import PlanEntry
    assert PlanEntry.from_dict(a2).compute_sha256() == a.config_sha256  # machine is not part of the config
    assert a.config_sha256 != b.config_sha256
