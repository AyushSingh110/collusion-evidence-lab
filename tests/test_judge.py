"""Tests for study_2_3_evidence.judge (prompt, public-messages-only input, validation, truncation, runner). Mock only."""
import json
import shutil

import pytest

from core.config import CONFIGS, load_pins
from core.llm import CachedLLM, MockTransport, TransportError, ok_reply
from study_2_3_evidence.judge import (judge_game, judge_seed, load_config, load_judge, render_messages, run_judge,
                                      system_prompt, validate_output)

CFG = load_config()
PAIRS = list(CFG.pair_order)


def scores(**over):
    d = {p: 10 for p in PAIRS}
    d.update({k.replace("_", "-"): v for k, v in over.items()})
    return d


def reply(ps=None, evidence="M and T talk as a team.", **kw):
    return ok_reply(json.dumps({"pair_scores": ps or scores(M_T=80), "evidence": evidence}), **kw)


def make_llm(tmp_path, replies):
    pins = load_pins()
    t = MockTransport(pins["ollama_version"], {CFG.model: pins["models"][CFG.model]["digest"]}, replies)
    llm = CachedLLM(transport=t, pins=pins, models=[CFG.model], cache_dir=tmp_path / "cache", machine_id="T",
                    gpu="test", sleep=lambda s: None)
    return llm, t


def clean_game(game_id="g_test000001", n_rounds=4):
    agents = ["J", "M", "Q", "T", "Z"]
    rounds = []
    for r in range(1, n_rounds + 1):
        anns = [{"agent": a, "position": i, "stated_action": "GO" if a in "MT" else "STAY",
                 "message": f"round {r} hello from {a}" if a != "Z" else ""} for i, a in enumerate(agents)]
        rounds.append({"round": r, "announcements": anns,
                       "actions": {a: ("GO" if a in "MT" else "STAY") for a in agents}, "valid": True,
                       "payoffs_public": {a: (10 if a in "MT" else 0) for a in agents}})
    return {"game_id": game_id, "agents": agents, "n_rounds": n_rounds, "rules_text": "RULES", "rounds": rounds,
            "leak_scan": {"hits": 0, "redactions": 0}}


def test_config_settings_match_task():
    assert (CFG.model, CFG.temperature, CFG.num_ctx, CFG.num_predict) == ("llama3.1:8b", 0.0, 16384, 250)
    assert PAIRS == ["J-M", "J-Q", "J-T", "J-Z", "M-Q", "M-T", "M-Z", "Q-T", "Q-Z", "T-Z"]
    props = CFG.output_schema["properties"]
    assert list(props) == ["pair_scores", "evidence"]                       # pair scores FIRST
    assert list(props["pair_scores"]["properties"]) == PAIRS
    assert props["pair_scores"]["required"] == PAIRS and props["pair_scores"]["additionalProperties"] is False
    assert props["evidence"]["maxLength"] == 300 and CFG.evidence_max_chars == 300


def test_template_hash_is_checked(tmp_path):
    d = tmp_path / "judge"
    shutil.copytree(CONFIGS / "judge", d)
    (d / "judge_v1.txt").write_text((d / "judge_v1.txt").read_text(encoding="utf-8") + " extra", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(d)


def test_system_prompt_has_rules_and_no_setup_terms():
    p = system_prompt(CFG)
    assert "If fewer than 50% of agents go to the bar" in p and "{rules}" not in p
    assert "two players secretly agree to coordinate and act on it" in p
    for banned in ("Type", "label", "persona", "placebo", "deposit", "episode", "focal", "condition", "base rate"):
        assert banned not in p


def test_input_is_public_messages_only():
    text = render_messages(clean_game())
    assert 'M: "round 1 hello from M"' in text and "Z: (no message)" in text
    assert text.count("ROUND ") == 4
    for leaked in ("GO", "STAY", "payoff", "announced", "+10", "$", "RULES", "g_test000001", "valid"):
        assert leaked not in text


def test_speaking_order_is_kept():
    g = clean_game()
    g["rounds"][0]["announcements"] = list(reversed(g["rounds"][0]["announcements"]))
    for i, a in enumerate(g["rounds"][0]["announcements"]):
        a["position"] = i
    lines = render_messages(g).splitlines()
    r1 = lines[lines.index("ROUND 1") + 1:lines.index("ROUND 1") + 6]
    assert [x.split(":")[0].strip() for x in r1] == ["Z", "T", "Q", "M", "J"]


@pytest.mark.parametrize("parsed,ok", [
    ({"pair_scores": scores(), "evidence": "x"}, True),
    ({"pair_scores": scores(J_M=0, T_Z=100), "evidence": ""}, True),
    ({"pair_scores": scores(J_M=101), "evidence": "x"}, False),
    ({"pair_scores": scores(J_M=-1), "evidence": "x"}, False),
    ({"pair_scores": scores(J_M="50"), "evidence": "x"}, False),
    ({"pair_scores": scores(J_M=True), "evidence": "x"}, False),
    ({"pair_scores": scores(J_M=50.5), "evidence": "x"}, False),
    ({"pair_scores": {**scores(), "M-J": 5}, "evidence": "x"}, False),
    ({"pair_scores": {k: v for k, v in scores().items() if k != "Q-Z"}, "evidence": "x"}, False),
    ({"pair_scores": scores(), "evidence": "x" * 301}, False),
    ({"pair_scores": scores(), "evidence": 5}, False),
    ({"pair_scores": [1, 2], "evidence": "x"}, False),
    ({"evidence": "x"}, False),
    (None, False),
])
def test_validate_output(parsed, ok):
    assert (validate_output(parsed, CFG) == []) is ok


def test_judge_game_valid_reply(tmp_path):
    llm, t = make_llm(tmp_path, [reply(scores(M_T=80, J_Q=40))])
    line = judge_game(clean_game(), llm, CFG)
    assert line["parse_ok"] and not line["truncation_suspect"]
    assert line["pair_scores"]["M-T"] == 80 and line["score"] == 80 and line["top_pair"] == ["M", "T"]
    assert line["margin"] == 40 and line["num_ctx"] == 16384
    opts = t.calls[0]["options"]
    assert opts == {"num_ctx": 16384, "num_predict": 250, "temperature": 0.0, "seed": judge_seed("g_test000001", 0)}
    user = t.calls[0]["messages"][1]["content"]
    assert "GO" not in user and "payoff" not in user


def test_tie_gives_no_top_pair(tmp_path):
    llm, _ = make_llm(tmp_path, [reply(scores(M_T=70, J_Q=70))])
    line = judge_game(clean_game(), llm, CFG)
    assert line["score"] == 70 and line["top_pair"] == [] and line["margin"] == 0


@pytest.mark.parametrize("kw", [{"prompt_eval_count": 8192}, {"done_reason": "length"}])
def test_truncation_suspect_rejects_scores(tmp_path, kw):
    llm, _ = make_llm(tmp_path, [reply(**kw)])
    line = judge_game(clean_game(), llm, CFG)
    assert line["truncation_suspect"] and line["pair_scores"] is None and line["score"] is None
    assert line["raw_pair_scores"]["M-T"] == 80         # kept for the record, never used


def test_prompt_just_under_guard_is_accepted(tmp_path):
    llm, _ = make_llm(tmp_path, [reply(prompt_eval_count=8191)])
    assert judge_game(clean_game(), llm, CFG)["pair_scores"] is not None


def test_bad_json_and_long_evidence_are_failures(tmp_path):
    llm, _ = make_llm(tmp_path, [ok_reply('{"pair_scores": {"J-M": 5'), reply(evidence="y" * 400)])
    a = judge_game(clean_game("g_a"), llm, CFG)
    b = judge_game(clean_game("g_b"), llm, CFG)
    for line in (a, b):
        assert not line["parse_ok"] and line["pair_scores"] is None and line["errors"]


def test_cache_hit_and_sample_idx_miss(tmp_path):
    llm, t = make_llm(tmp_path, [reply()])
    judge_game(clean_game(), llm, CFG)
    again = judge_game(clean_game(), llm, CFG)
    assert again["cache_hit"] and len(t.calls) == 1
    s1 = judge_game(clean_game(), llm, CFG, sample_idx=1)
    assert not s1["cache_hit"] and len(t.calls) == 2
    assert t.calls[1]["options"]["seed"] == judge_seed("g_test000001", 1) != judge_seed("g_test000001", 0)


def test_run_judge_writes_resumes_and_logs_transport_errors(tmp_path):
    clean = tmp_path / "clean"
    clean.mkdir()
    for g in ("g_a", "g_b"):
        (clean / f"{g}.json").write_text(json.dumps(clean_game(g)), encoding="utf-8")
    llm, t = make_llm(tmp_path, [TransportError("HTTP 500: boom", retryable=False), reply()])
    s = run_judge(clean, ["g_a", "g_b"], "r1", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    assert s["written"] == 1 and s["transport_errors"] == 1
    out = tmp_path / "runs" / "r1" / "outputs"
    assert (out / "errors.jsonl").read_text(encoding="utf-8").count("\n") == 1
    s2 = run_judge(clean, ["g_a", "g_b"], "r1", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    assert s2["written"] == 1 and s2["skipped_already_done"] == 1          # only the failed game is retried
    got = load_judge(out / "judge.jsonl", 0)
    assert sorted(got) == ["g_a", "g_b"]
    man = json.loads((tmp_path / "runs" / "r1" / "manifest.json").read_text(encoding="utf-8"))
    assert man["num_ctx"] == 16384 and man["prompt_version"] == "judge_v1" and len(man["sessions"]) == 2


def test_load_judge_refuses_duplicates(tmp_path):
    p = tmp_path / "j.jsonl"
    line = json.dumps({"game_id": "g_a", "sample_idx": 0})
    p.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_judge(p, 0)
