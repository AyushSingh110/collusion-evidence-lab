import copy
import json
import re

import pytest

from core.generate import prompts as P
from core.generate.elfarol import AGENTS, outcome
from core.generate.runner import call_seed, check_manifest, run_game
from core.schema import validate_game
from tests.genmock import agent_of, defaults, entries, mock_llm, stage_of

TYPE_OF = {1: "alliance", 2: "placebo", 3: "persona", 4: "incentive"}


# ------------------------------------------------------------------ payoffs (report 00 §1.2)
@pytest.mark.parametrize("n_go,goer,stayer", [(0, None, 0), (1, 10, 0), (2, 10, 0), (3, -5, 0), (4, -5, 0), (5, -5, None)])
def test_standard_payoffs(n_go, goer, stayer):
    ch = {a: ("GO" if i < n_go else "STAY") for i, a in enumerate(AGENTS)}
    o = outcome(ch)
    assert o["n_go"] == n_go and o["crowded"] == (n_go >= 3)
    for a, c in ch.items():
        assert o["payoffs_public"][a] == (goer if c == "GO" else stayer)
    assert o["payoffs_private"] == o["payoffs_public"]


@pytest.mark.parametrize("n_go", range(6))
def test_private_4b_payoffs(n_go):
    ch = {a: ("GO" if i < n_go else "STAY") for i, a in enumerate(AGENTS)}  # J,M go first
    o = outcome(ch, private_home={"J": -8.0, "Z": -8.0})
    for a in AGENTS:
        if a in ("J", "Z") and ch[a] == "STAY":
            assert o["payoffs_private"][a] == -8.0 and o["payoffs_public"][a] == 0.0
        else:
            assert o["payoffs_private"][a] == o["payoffs_public"][a]


def test_imputed_none_plays_as_stay():
    o = outcome({"J": "GO", "M": None, "Q": "STAY", "T": "GO", "Z": "STAY"})
    assert o["n_go"] == 2 and o["payoffs_public"]["M"] == 0 and o["imputed_agents"] == ["M"]


# ------------------------------------------------------------------ full mock games
@pytest.fixture(scope="module")
def four_games(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("games")
    llm, t = mock_llm(tmp)
    out = {}
    for e in entries(rounds=2):
        start = len(t.calls)
        rec = run_game(e, llm, run_defaults=defaults(), raw_dir=tmp / "raw")
        out[e.episode_type] = (e, rec, t.calls[start:])
    return out


def test_all_four_types_validate(four_games):
    for et, (e, rec, calls) in four_games.items():
        assert validate_game(rec) == [], et
        assert len(calls) == 2 * (19 if et == 1 else 15)
        assert rec["machine"] == "A" and rec["wall_s"] >= 0 and rec["prompts"]
        assert rec["harness"]["commit"].startswith("d585a7b")


def _system(p):
    return p["messages"][0]["content"]


def _user(p):
    return p["messages"][1]["content"]


def test_addendum_only_focal_same_slot_every_stage(four_games):
    for et, (e, rec, calls) in four_games.items():
        focal = e.focal_pair
        partner = {focal[0]: focal[1], focal[1]: focal[0]}
        stages_seen = set()
        for p in calls:
            a, st = agent_of(p), stage_of(p)
            sysp = _system(p)
            if a in focal:
                add = P.addendum_text(et, partner[a])
                assert sysp.endswith("\n\n" + add), (et, a, st)      # same slot: last block of the system prompt
                stages_seen.add(st)
            else:
                assert "PRIVATE NOTE" not in sysp and "PRIVATE NOTE" not in _user(p), (et, a, st)
        assert stages_seen == ({"stage1", "stage2", "stage3", "channel"} if et == 1 else {"stage1", "stage2", "stage3"})


def test_placebo_alliance_length_ratio():
    tok = P.load_manifest()["measured_tokens_qwen2.5_7b"]
    assert P.ADDENDUM_FILES[1] == "alliance_v3.txt" and P.ADDENDUM_FILES[2] == "placebo_v3.txt"
    assert (tok["alliance_v3.txt"], tok["placebo_v3.txt"]) == (130, 139)     # measured, task 06a
    assert abs(tok["placebo_v3.txt"] / tok["alliance_v3.txt"] - 1) <= 0.10
    assert abs(tok["placebo_v2.txt"] / tok["alliance_v2.txt"] - 1) <= 0.10   # history


def test_alliance_v3_is_v2_plus_hint_byte_exact():
    d = P.PROMPTS_DIR
    v2 = (d / "alliance_v2.txt").read_bytes().rstrip(b"\n")
    hint = (d / "collusion_hint_v1.txt").read_bytes().rstrip(b"\n")
    assert (d / "alliance_v3.txt").read_bytes() == v2 + b" " + hint + b"\n"


HEADER = "PRIVATE NOTE (only you can see this):"


def test_placebo_v3_is_neutral():
    from core.clean.leaks import scan_for_leaks
    text = P.read_prompt("placebo_v3.txt")
    assert text.startswith(HEADER) and P.read_prompt("placebo_v2.txt").startswith(HEADER)
    body = text[len(HEADER):]          # the header is shared by all 4 addenda by design
    others = [P.read_prompt(f)[len(HEADER):] for f in ("alliance_v3.txt", "persona_v1.txt", "incentive_4b_v1.txt")]
    assert scan_for_leaks(body, others) == []
    assert not re.search(r"(?<![A-Za-z'’])[JMQTZ](?![A-Za-z])", body) and "Agent" not in body
    assert not re.search(r"\b(go|going|stay|staying|home|bar|team|together|both|we|us|our|partner)\b", body, re.I)


def test_type1_records_carry_v3_variant(four_games):
    e, rec, _ = four_games[1]
    assert rec["config"]["variant"] == "collusion_v3_hint" and "alliance_v3.txt" in rec["prompts"]
    assert four_games[2][1]["config"]["variant"] == "placebo_v3" and "placebo_v3.txt" in four_games[2][1]["prompts"]
    assert "collusion_hint_v1.txt" not in rec["prompts"]      # hint is inside alliance_v3, not appended twice


def test_manifest_matches_prompt_files():
    assert check_manifest() == P.load_manifest()["sha256"]


def test_4b_private_line_only_focal_and_never_public(four_games):
    e, rec, calls = four_games[4]
    for p in calls:
        has = "your real payoffs under your own situation" in _system(p)
        if has:
            assert agent_of(p) in e.focal_pair
    # it appears from round 2 for both focal agents
    assert {agent_of(p) for p in calls if "your real payoffs" in _system(p)} == set(e.focal_pair)
    public = json.dumps([[s["message"] for s in r["stage2"]] for r in rec["rounds"]]
                        + [[r["stage3"][a]["choice"] for a in AGENTS] for r in rec["rounds"]]
                        + [r["outcome"]["payoffs_public"] for r in rec["rounds"]])
    assert "real payoff" not in public and "-8" not in public and "deposit" not in public


def test_channel_messages_only_in_partner_prompts(four_games):
    e, rec, calls = four_games[1]
    texts = {c["text"] for r in rec["rounds"] for c in r["channel"]}
    assert texts
    for p in calls:
        whole = _system(p) + _user(p)
        if any(tx in whole for tx in texts):
            assert agent_of(p) in e.focal_pair
    for et in (2, 3, 4):
        assert all(r["channel"] == [] for r in four_games[et][1]["rounds"])


def test_brevity_line_identical_for_all_agents(four_games):
    line = P.read_prompt("brevity_v1.txt")
    for et, (e, rec, calls) in four_games.items():
        assert all(_user(p).endswith("\n\n" + line) for p in calls)
        assert {agent_of(p) for p in calls} == set(AGENTS)


def test_seeds_unique_within_and_across_games(four_games):
    seeds = [p["options"]["seed"] for (_, _, calls) in four_games.values() for p in calls]
    assert len(seeds) == len(set(seeds))
    assert call_seed(1, 1, "stage1", "J") != call_seed(1, 1, "stage1", "M")


def test_speaking_order_rotates_and_stage3_hides_stated_action(four_games):
    e, rec, calls = four_games[2]
    orders = [tuple(r["order"]) for r in rec["rounds"]]
    assert all(sorted(o) == sorted(AGENTS) for o in orders)
    s3 = [p for p in calls if stage_of(p) == "stage3"]
    assert all("stated action:" not in _user(p) for p in s3)


# ------------------------------------------------------------------ failures are data
def test_invalid_action_logged_and_imputed(tmp_path):
    e = entries(counts={2: 1}, rounds=2)[0]
    llm, _ = mock_llm(tmp_path, fail={("Q", "stage3"): "invalid", ("J", "stage1"): "badjson"})
    rec = run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw")
    assert validate_game(rec) == []
    kinds = {(f["stage"], f["agent"], f["kind"]) for f in rec["failures"]}
    assert ("stage3", "Q", "invalid_action") in kinds and ("stage1", "J", "parse_error") in kinds
    q = rec["rounds"][0]["stage3"]["Q"]
    assert q["choice"] is None and q["imputed"] and not q["parse_ok"]
    assert "Q" in rec["rounds"][0]["outcome"]["imputed_agents"]


def test_transport_failure_logged(tmp_path):
    e = entries(counts={1: 1}, rounds=2)[0]
    a = e.focal_pair[0]
    llm, _ = mock_llm(tmp_path, fail={(a, "stage2"): "transport", (a, "channel"): "transport"})
    rec = run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw")
    assert validate_game(rec) == []
    f = [x for x in rec["failures"] if x["kind"] == "transport_error"]
    assert {x["stage"] for x in f} == {"stage2", "channel_A", "channel_B"}
    e2 = [s for s in rec["rounds"][0]["stage2"] if s["agent"] == a][0]
    assert e2["stated_action"] is None and e2["imputed"] and e2["call"]["error"]
    assert rec["usage"]["transport_errors"] == len(f)


# ------------------------------------------------------------------ resume
def _strip(rec):
    r = copy.deepcopy(rec)
    r.pop("created_utc"), r.pop("wall_s")
    for rd in r["rounds"]:
        for e in list(rd["stage1"].values()) + rd["channel"] + rd["stage2"] + list(rd["stage3"].values()):
            e["call"].pop("latency_s"), e["call"].pop("cache_hit")
    r["usage"].pop("cache_hits")
    return r


def test_resume_replays_from_cache(tmp_path):
    e = entries(counts={1: 1}, rounds=3)[0]
    full_llm, full_t = mock_llm(tmp_path / "full")
    full = run_game(e, full_llm, run_defaults=defaults(), raw_dir=tmp_path / "full" / "raw")

    llm1, t1 = mock_llm(tmp_path / "res")
    assert run_game(e, llm1, run_defaults=defaults(), raw_dir=tmp_path / "res" / "raw", stop_after_round=2) is None
    assert (tmp_path / "res" / "raw" / f"{e.game_id}.partial.json").exists()
    calls_r12 = len(t1.calls)
    llm2, t2 = mock_llm(tmp_path / "res", cache_dir=tmp_path / "res" / "cache")
    resumed = run_game(e, llm2, run_defaults=defaults(), raw_dir=tmp_path / "res" / "raw")
    assert len(t2.calls) == len(full_t.calls) - calls_r12 == 19       # only round 3 reached the transport
    assert resumed["usage"]["cache_hits"] == calls_r12
    assert _strip(resumed) == _strip(full)
    assert not (tmp_path / "res" / "raw" / f"{e.game_id}.partial.json").exists()


def test_rerun_of_finished_game_makes_no_calls(tmp_path):
    e = entries(counts={3: 1}, rounds=2)[0]
    llm, t = mock_llm(tmp_path)
    run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw")
    n = len(t.calls)
    run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw")
    assert len(t.calls) == n


def test_prompts_module_does_not_import_harness_clients():
    import sys
    from pathlib import Path
    assert not any(m.startswith(("src.config", "src.llm", "poseidon_compute")) for m in sys.modules)
    ext = Path(__file__).resolve().parents[1] / "external"
    assert not list(ext.rglob("__pycache__"))      # Rule F: nothing written into external/
    src = (Path(__file__).resolve().parents[1] / "core" / "generate" / "prompts.py").read_text(encoding="utf-8")
    assert not re.search(r"import .*(settings|client_factory|poseidon_compute)", src)
