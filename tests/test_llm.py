import ast
import json
from pathlib import Path

import pytest

from core.llm import CachedLLM, MockTransport, PinError, TransportError, ok_reply
from tests.conftest import CALL, PINS, make_llm


def test_repeated_call_is_cache_hit_with_no_transport_call(tmp_path):
    llm, t = make_llm(tmp_path)
    first = llm.complete(**CALL)
    assert not first.cache_hit and len(t.calls) == 1
    second = llm.complete(**CALL)
    assert second.cache_hit and len(t.calls) == 1
    assert second.parsed == {"choice": "GO"} and second.cache_key == first.cache_key


@pytest.mark.parametrize("field,value", [("num_ctx", 4096), ("num_predict", 200), ("temperature", 0.7),
                                         ("seed", 8), ("sample_idx", 1),
                                         ("format_schema", {"type": "object", "properties": {}})])
def test_changing_one_option_is_a_cache_miss(tmp_path, field, value):
    llm, t = make_llm(tmp_path)
    a = llm.complete(**CALL)
    b = llm.complete(**dict(CALL, **{field: value}))
    assert not b.cache_hit and b.cache_key != a.cache_key and len(t.calls) == 2


def test_changing_digest_is_a_cache_miss(tmp_path):
    llm, _ = make_llm(tmp_path)
    a = llm.complete(**CALL)
    pins2 = json.loads(json.dumps(PINS))
    pins2["models"]["qwen2.5:7b"]["digest"] = "c" * 64
    llm2, t2 = make_llm(tmp_path, pins=pins2)  # same cache dir
    b = llm2.complete(**CALL)
    assert not b.cache_hit and b.cache_key != a.cache_key and len(t2.calls) == 1


def test_startup_refuses_wrong_digest(tmp_path):
    with pytest.raises(PinError, match="digest"):
        make_llm(tmp_path, tags={"qwen2.5:7b": "f" * 64})


def test_startup_refuses_wrong_version(tmp_path):
    with pytest.raises(PinError, match="version"):
        make_llm(tmp_path, version="0.40.10")


def test_startup_refuses_missing_model(tmp_path):
    with pytest.raises(PinError, match="not installed"):
        make_llm(tmp_path, tags={})


def test_truncation_suspect_when_prompt_fills_half_the_context(tmp_path):
    llm, _ = make_llm(tmp_path, replies=[ok_reply('{"choice": "GO"}', prompt_eval_count=4096)])
    assert llm.complete(**CALL).truncation_suspect


def test_truncation_suspect_when_output_hits_length_limit(tmp_path):
    llm, _ = make_llm(tmp_path, replies=[ok_reply('{"choice": "G', done_reason="length")])
    r = llm.complete(**CALL)
    assert r.truncation_suspect and r.parsed is None and r.parse_error


def test_no_truncation_flag_for_normal_call(tmp_path):
    llm, _ = make_llm(tmp_path, replies=[ok_reply('{"choice": "GO"}', prompt_eval_count=4095)])
    assert not llm.complete(**CALL).truncation_suspect


def test_transport_error_retried_at_most_twice_and_logged(tmp_path):
    sleeps = []
    llm, t = make_llm(tmp_path, replies=[TransportError("connection refused", retryable=True)], sleeps=sleeps)
    r = llm.complete(**CALL)
    assert len(t.calls) == 3 and sleeps == [5.0, 20.0]
    assert [a["attempt"] for a in r.attempts] == [1, 2, 3] and not any(a["ok"] for a in r.attempts)
    assert r.error and r.content is None
    assert not list((tmp_path / "cache").rglob("*.json"))  # transport failures are not cached


def test_transient_transport_error_then_success(tmp_path):
    sleeps = []
    llm, t = make_llm(tmp_path, replies=[TransportError("HTTP 503", retryable=True), ok_reply('{"choice": "STAY"}')],
                      sleeps=sleeps)
    r = llm.complete(**CALL)
    assert r.parsed == {"choice": "STAY"} and len(t.calls) == 2 and sleeps == [5.0]
    assert [a["ok"] for a in r.attempts] == [False, True]


def test_non_retryable_transport_error_is_not_retried(tmp_path):
    llm, t = make_llm(tmp_path, replies=[TransportError("HTTP 404: model not found", retryable=False)])
    r = llm.complete(**CALL)
    assert len(t.calls) == 1 and r.error


def test_parse_failure_is_not_retried(tmp_path):
    llm, t = make_llm(tmp_path, replies=[ok_reply("not json at all")])
    r = llm.complete(**CALL)
    assert len(t.calls) == 1 and r.parsed is None and "JSONDecodeError" in r.parse_error
    assert r.content == "not json at all" and len(r.attempts) == 1


def test_cache_layout_and_stored_fields(tmp_path):
    llm, _ = make_llm(tmp_path)
    r = llm.complete(**CALL)
    p = tmp_path / "cache" / "T1" / r.cache_key[:2] / f"{r.cache_key}.json"
    assert p.exists() and not list(p.parent.glob(".*.tmp"))
    e = json.loads(p.read_text(encoding="utf-8"))
    for k in ("request", "raw_response", "result", "purpose", "sample_idx"):
        assert k in e
    res = e["result"]
    for k in ("parsed", "prompt_eval_count", "eval_count", "durations_ns", "done_reason", "latency_s", "model_digest",
              "ollama_version", "machine_id", "created_utc", "error", "truncation_suspect"):
        assert k in res
    assert e["request"]["options"] == {"num_ctx": 8192, "num_predict": 350, "temperature": 1.0, "seed": 7}


def test_cache_from_another_machine_shard_is_reused(tmp_path):
    llm_a, _ = make_llm(tmp_path)
    llm_a.complete(**CALL)
    t = MockTransport("0.40.3", {m: v["digest"] for m, v in PINS["models"].items()})
    llm_b = CachedLLM(transport=t, pins=PINS, models=["qwen2.5:7b"], cache_dir=tmp_path / "cache", machine_id="B",
                      gpu="test")
    assert llm_b.complete(**CALL).cache_hit and not t.calls


def test_generation_options_are_required(tmp_path):
    llm, _ = make_llm(tmp_path)
    kwargs = dict(CALL)
    kwargs.pop("num_ctx")
    with pytest.raises(TypeError):
        llm.complete(**kwargs)


def test_unchecked_model_is_refused(tmp_path):
    llm, _ = make_llm(tmp_path)
    with pytest.raises(PinError):
        llm.complete(**dict(CALL, model="llama3.1:8b"))


def test_core_llm_does_not_import_the_harness():
    root = Path(__file__).resolve().parents[1] / "core" / "llm"
    for py in root.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        mods += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not [m for m in mods if m.startswith(("src", "external", "poseidon_compute"))], py
