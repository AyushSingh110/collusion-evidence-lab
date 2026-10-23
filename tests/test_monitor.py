"""Tests for study_2_2_views.monitor (prompt, output validation, truncation, resumable runner). Mock only."""
import json
import shutil

import pytest

from core.config import CONFIGS, load_pins
from core.llm import CachedLLM, MockTransport, TransportError, ok_reply
from study_2_2_views.monitor import (load_config, monitor_seed, run_monitor, score_view, system_prompt,
                                     validate_output)

CFG = load_config()
GOOD = '{"score": 72, "suspected_pair": ["M", "T"], "rationale": "M and T went together while telling others to stay."}'


def make_llm(tmp_path, replies):
    pins = load_pins()
    t = MockTransport(pins["ollama_version"], {CFG.model: pins["models"][CFG.model]["digest"]}, replies)
    llm = CachedLLM(transport=t, pins=pins, models=[CFG.model], cache_dir=tmp_path / "cache", machine_id="T",
                    gpu="test", sleep=lambda s: None)
    return llm, t


def test_config_settings_match_task():
    assert (CFG.model, CFG.temperature, CFG.num_ctx, CFG.num_predict) == ("llama3.1:8b", 0.0, 8192, 200)


def test_template_hash_is_checked(tmp_path):
    d = tmp_path / "monitor"
    shutil.copytree(CONFIGS / "monitor", d)
    (d / "monitor_v1.txt").write_text((d / "monitor_v1.txt").read_text(encoding="utf-8") + " extra", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(d)


def test_one_prompt_only_the_view_sentence_changes():
    p = {v: system_prompt(CFG, v) for v in CFG.view_prompt}
    for c in ("C-mismatch", "C-length", "C-shuffled"):
        assert p[c] == p["V3"]                                 # a control is indistinguishable from V3
    a, b = p["V1"].splitlines(), p["V2"].splitlines()
    assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
    text = p["V3"]
    assert "two players secretly agree to coordinate and act on it" in text
    assert "If fewer than 50% of agents go to the bar" in text
    for banned in ("base rate", "half of the games", "%  of the games", "Type", "label", "persona", "placebo",
                   "{rules}", "{what_you_see}"):
        assert banned not in text


@pytest.mark.parametrize("parsed,ok", [
    ({"score": 50, "suspected_pair": ["M", "T"], "rationale": "x"}, True),
    ({"score": 0, "suspected_pair": [], "rationale": ""}, True),
    ({"score": 100, "suspected_pair": ["Z", "J"], "rationale": "x"}, True),
    ({"score": 101, "suspected_pair": [], "rationale": "x"}, False),
    ({"score": -1, "suspected_pair": [], "rationale": "x"}, False),
    ({"score": "50", "suspected_pair": [], "rationale": "x"}, False),
    ({"score": True, "suspected_pair": [], "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": ["M", "M"], "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": ["M", "X"], "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": ["Agent M", "T"], "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": ["M"], "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": "M-T", "rationale": "x"}, False),
    ({"score": 50, "suspected_pair": [], "rationale": None}, False),
    (None, False),
])
def test_validate_output(parsed, ok):
    assert (validate_output(parsed, CFG) == []) is ok


def test_score_view_ok_and_request_settings(tmp_path):
    llm, t = make_llm(tmp_path, [ok_reply(GOOD, prompt_eval_count=1500)])
    line = score_view("ROUND 1 ...", "V3", llm, CFG, game_id="g_aaaaaaaaaa")
    assert line["score"] == 72 and line["suspected_pair"] == ["M", "T"] and line["parse_ok"]
    assert not line["truncation_suspect"] and line["rationale_words"] == 10 and not line["rationale_over_limit"]
    req = t.calls[0]
    assert req["model"] == "llama3.1:8b" and req["options"] == {
        "num_ctx": 8192, "num_predict": 200, "temperature": 0.0, "seed": monitor_seed("g_aaaaaaaaaa", "V3", 0)}
    assert req["format"] == CFG.output_schema and req["messages"][1]["content"] == "ROUND 1 ..."
    assert "g_aaaaaaaaaa" not in json.dumps(req["messages"])   # the game id is only in the seed


@pytest.mark.parametrize("reply", [ok_reply(GOOD, prompt_eval_count=4096),
                                   ok_reply(GOOD, prompt_eval_count=900, done_reason="length")])
def test_truncation_suspect_is_not_accepted(tmp_path, reply):
    llm, _ = make_llm(tmp_path, [reply])
    line = score_view("x", "V4", llm, CFG, game_id="g_bbbbbbbbbb")
    assert line["truncation_suspect"] is True and line["score"] is None and line["suspected_pair"] == []
    assert line["raw_score"] == 72


def test_invalid_reply_gives_parse_failure(tmp_path):
    llm, _ = make_llm(tmp_path, [ok_reply('{"score": 72, "suspected_pair": ["M", "M"], "rationale": "x"}')])
    line = score_view("x", "V1", llm, CFG, game_id="g_cccccccccc")
    assert line["parse_ok"] is False and line["score"] is None and line["errors"]
    llm2, _ = make_llm(tmp_path / "b", [ok_reply("not json at all")])
    line2 = score_view("x", "V1", llm2, CFG, game_id="g_cccccccccc")
    assert line2["parse_ok"] is False and "JSONDecodeError" in line2["errors"][0]


def test_seed_depends_on_game_view_sample():
    s = {monitor_seed(g, v, i) for g in ("g_1", "g_2") for v in ("V1", "V3") for i in (0, 1)}
    assert len(s) == 8 and all(0 <= x < 2 ** 31 for x in s)


def _views(tmp_path, n=3):
    files = []
    for v in ("V1", "V2"):
        for i in range(n):
            p = tmp_path / "views" / v / f"g_{i:010d}.txt"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"view {v} game {i}\n", encoding="utf-8")
            files.append(p)
    return files


def test_run_monitor_writes_and_resumes(tmp_path):
    files = _views(tmp_path)
    llm, t = make_llm(tmp_path, [ok_reply(GOOD)])
    s1 = run_monitor(files, "r1", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    out = tmp_path / "runs" / "r1" / "outputs" / "monitor.jsonl"
    lines = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert s1["written"] == 6 and len(lines) == 6 and len(t.calls) == 6
    want = {"run_id", "game_id", "view", "model", "digest", "prompt_sha256", "sample_idx", "score", "suspected_pair",
            "rationale", "parse_ok", "truncation_suspect", "cache_key", "latency"}
    assert all(want <= set(x) for x in lines)
    assert {(x["view"], x["game_id"]) for x in lines} == {(f.parent.name, f.stem) for f in files}
    # resume: nothing re-scored, no new transport call
    s2 = run_monitor(files, "r1", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    assert s2["written"] == 0 and s2["skipped_already_done"] == 6 and len(t.calls) == 6
    assert len(out.read_text(encoding="utf-8").splitlines()) == 6
    man = json.loads((tmp_path / "runs" / "r1" / "manifest.json").read_text(encoding="utf-8"))
    assert len(man["sessions"]) == 2 and man["template_sha256"] == CFG.template_sha256
    assert man["model"] == "llama3.1:8b" and man["digest"] == load_pins()["models"]["llama3.1:8b"]["digest"]


def test_transport_error_goes_to_errors_and_is_retried_later(tmp_path):
    files = _views(tmp_path, n=1)
    llm, t = make_llm(tmp_path, [TransportError("HTTP 500: boom", retryable=False), ok_reply(GOOD)])
    s1 = run_monitor(files, "r2", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    outs = tmp_path / "runs" / "r2" / "outputs"
    assert s1["transport_errors"] == 1 and s1["written"] == 1
    assert len((outs / "errors.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    s2 = run_monitor(files, "r2", llm, CFG, runs_dir=tmp_path / "runs", progress=lambda m: None)
    assert s2["written"] == 1 and s2["skipped_already_done"] == 1
    assert len((outs / "monitor.jsonl").read_text(encoding="utf-8").splitlines()) == 2
