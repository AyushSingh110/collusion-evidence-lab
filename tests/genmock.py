"""Deterministic mock agent for generator tests: answers by stage (from the JSON schema) and seed."""
import copy
import json
import re

from core.config import load_run_defaults
from core.llm import CachedLLM, MockTransport, TransportError, ok_reply
from core.plan import build_entries

DIGEST = "a" * 64
PINS = {"ollama_version": "0.40.3",
        "models": {"qwen2.5:7b": {"digest": DIGEST, "role": "agent", "num_ctx": 8192, "required": True}}}


def agent_of(payload):
    return re.search(r"You are Agent (\w)", payload["messages"][0]["content"]).group(1)


def stage_of(payload):
    props = set((payload.get("format") or {}).get("properties", {}))
    if "intended_action" in props:
        return "stage1"
    if "stated_action" in props:
        return "stage2"
    if "choice" in props:
        return "stage3"
    return "channel"


def make_reply(fail=None):
    """fail: {(agent, stage): "badjson" | "transport" | "invalid"} applied on every matching call."""
    fail = fail or {}

    def reply(payload):
        a, st, seed = agent_of(payload), stage_of(payload), payload["options"]["seed"]
        mode = fail.get((a, st))
        if mode == "transport":
            raise TransportError("HTTP 404: mock failure", retryable=False)
        if mode == "badjson":
            return ok_reply('{"choice": "GO", "reas')
        act = "GO" if seed % 3 == 0 else "STAY"
        if mode == "invalid":
            act = "MAYBE"
        body = {"stage1": {"intended_action": act, "reasoning": f"plan {seed % 97}"},
                "stage2": {"stated_action": act, "message": f"I will {act.lower()} tonight ({seed % 89})."},
                "stage3": {"choice": act, "reasoning": f"final {seed % 83}"},
                "channel": {"message": f"Let's both go to the bar ({seed % 79})."}}[st]
        return ok_reply(json.dumps(body))

    return reply


def mock_llm(tmp_path, machine_id="A", fail=None, cache_dir=None):
    t = MockTransport("0.40.3", {"qwen2.5:7b": DIGEST}, [make_reply(fail)])
    llm = CachedLLM(transport=t, pins=copy.deepcopy(PINS), models=["qwen2.5:7b"],
                    cache_dir=cache_dir or (tmp_path / "cache"), machine_id=machine_id, gpu="test",
                    sleep=lambda s: None)
    return llm, t


def entries(counts=None, rounds=2, seed=777, machines=("A",)):
    return build_entries("test", seed, counts or {1: 1, 2: 1, 3: 1, 4: 1}, list(machines), rounds)


def defaults(brevity=True):
    rd = load_run_defaults()
    rd["brevity"] = brevity
    return rd
