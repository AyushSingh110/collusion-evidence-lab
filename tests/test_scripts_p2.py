import json
import shutil

import pytest

from core.generate.runner import run_game
from core.labels import label_from_config, read_labels
from core.plan import load_plan, make_plan
from core.split import load_split
from scripts import labels_split_from_plan, make_plan as make_plan_cli, merge_check, run_plan
from tests.genmock import PINS, defaults, mock_llm

COUNTS = {1: 2, 2: 1, 3: 1, 4: 1}


@pytest.fixture
def plan_path(tmp_path):
    return make_plan("t", 4242, COUNTS, ["A", "B"], 2, out_dir=tmp_path / "plans")


# ------------------------------------------------------------------ make_plan CLI
def test_make_plan_cli_and_refusal(tmp_path, capsys):
    args = ["--name", "p", "--seed", "1", "--counts", "1=2", "2=1", "--machines", "A", "B", "--rounds", "2",
            "--speed", "A=1.0", "B=2.0", "--out-dir", str(tmp_path)]
    assert make_plan_cli.main(args) == 0
    assert "wrote" in capsys.readouterr().out
    assert make_plan_cli.main(args) == 1 and "REFUSED" in capsys.readouterr().out


# ------------------------------------------------------------------ labels + split from plan
def test_labels_split_from_plan(tmp_path, plan_path):
    lab, spl = tmp_path / "labels.csv", tmp_path / "split.json"
    args = ["--plan", str(plan_path), "--labels", str(lab), "--split", str(spl), "--seed", "20261023"]
    assert labels_split_from_plan.main(args) == 0
    by_id = {l.game_id: l for l in read_labels(lab)}
    for e in load_plan(plan_path):
        exp = label_from_config({"game_id": e.game_id, "episode_type": e.episode_type, "focal_pair": e.focal_pair,
                                 "variant": e.variant})
        assert by_id[e.game_id].collusion == exp.collusion and by_id[e.game_id].episode_type == e.episode_type
    s = load_split(spl)
    assert set(s.dev) | set(s.test) == set(by_id) and not set(s.dev) & set(s.test)
    t1 = [g for g in by_id if by_id[g].episode_type == 1]
    assert sum(g in s.dev for g in t1) == 1                       # stratified: 2 Type 1 -> 1 dev
    # deterministic: same plan + seed into a fresh place gives the same split
    assert labels_split_from_plan.main(["--plan", str(plan_path), "--labels", str(tmp_path / "l2.csv"),
                                        "--split", str(tmp_path / "s2.json"), "--seed", "20261023"]) == 0
    assert load_split(tmp_path / "s2.json").dev == s.dev
    assert labels_split_from_plan.main(args) == 1                   # refuses to overwrite


# ------------------------------------------------------------------ run_plan --dry-run
def test_run_plan_dry_run(tmp_path, plan_path, capsys):
    assert run_plan.main(["--plan", str(plan_path), "--machine", "A", "--dry-run", "--raw-dir", str(tmp_path / "raw")]) == 0
    out = capsys.readouterr().out
    n_a = sum(e.machine == "A" for e in load_plan(plan_path))
    assert f"machine A has {n_a} games" in out and "calls" in out and "min" in out


def test_run_plan_needs_machine(plan_path, monkeypatch):
    monkeypatch.delenv("COLLUSION_LAB_MACHINE", raising=False)
    assert run_plan.main(["--plan", str(plan_path), "--dry-run"]) == 2


# ------------------------------------------------------------------ merge_check
@pytest.fixture
def merged(tmp_path, plan_path):
    """Run every plan game on its machine (separate cache shards), then merge into one raw/ and one cache/."""
    cache = tmp_path / "cache"
    for m in ("A", "B"):
        llm, _ = mock_llm(tmp_path, machine_id=m, cache_dir=cache)
        for e in load_plan(plan_path):
            if e.machine == m:
                run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw" / m, machine=m)
    return plan_path, tmp_path / "raw", cache


def _check(merged):
    plan, raw, cache = merged
    return merge_check.check(plan, raw, cache, PINS)


def test_merge_check_passes(merged):
    assert _check(merged) == []


def test_merge_check_duplicate(merged):
    plan, raw, _ = merged
    f = next((raw / "A").glob("*.json"))
    shutil.copy(f, raw / "B" / ("copy_" + f.name))
    assert any("duplicate" in p for p in _check(merged))


def test_merge_check_missing_game(merged):
    plan, raw, _ = merged
    next((raw / "B").glob("*.json")).unlink()
    assert any("missing record" in p for p in _check(merged))


def test_merge_check_wrong_digest(merged):
    plan, raw, _ = merged
    f = next((raw / "A").glob("*.json"))
    rec = json.loads(f.read_text())
    rec["config"]["agent_digest"] = "f" * 64
    f.write_text(json.dumps(rec))
    assert any(p.startswith("(3)") for p in _check(merged))


def test_merge_check_duplicated_seed(merged):
    plan, raw, _ = merged
    f = next((raw / "A").glob("*.json"))
    rec = json.loads(f.read_text())
    rec["rounds"][0]["stage1"]["J"]["call"]["seed"] = rec["rounds"][0]["stage1"]["M"]["call"]["seed"]
    f.write_text(json.dumps(rec))
    assert any(p.startswith("(4)") for p in _check(merged))


def test_merge_check_missing_cache_entry(merged):
    plan, raw, cache = merged
    victim = next(cache.rglob("*.json"))
    victim.unlink()
    assert any(p.startswith("(5)") for p in _check(merged))


def test_merge_check_config_mismatch(merged):
    plan, raw, _ = merged
    f = next((raw / "A").glob("*.json"))
    rec = json.loads(f.read_text())
    rec["config"]["focal_pair"] = ["J", "Q"] if rec["config"]["focal_pair"] != ["J", "Q"] else ["M", "T"]
    f.write_text(json.dumps(rec))
    assert any(p.startswith("(2)") for p in _check(merged))
