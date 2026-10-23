import copy

import pytest

from core.llm import CachedLLM, MockTransport, ok_reply

PINS = {
    "ollama_version": "0.40.3",
    "models": {
        "qwen2.5:7b": {"digest": "a" * 64, "role": "agent", "num_ctx": 8192, "required": True},
        "llama3.1:8b": {"digest": "b" * 64, "role": "monitor_judge", "num_ctx": 8192, "required": True},
    },
}
SCHEMA = {"type": "object", "properties": {"choice": {"type": "string", "enum": ["GO", "STAY"]}},
          "required": ["choice"]}
MESSAGES = [{"role": "system", "content": "You are Agent J."}, {"role": "user", "content": "GO or STAY?"}]
CALL = dict(model="qwen2.5:7b", messages=MESSAGES, format_schema=SCHEMA, num_ctx=8192, num_predict=350,
            temperature=1.0, seed=7, sample_idx=0, purpose="test")


@pytest.fixture
def pins():
    return copy.deepcopy(PINS)


def make_llm(tmp_path, replies=None, pins=None, version="0.40.3", tags=None, sleeps=None):
    pins = pins or copy.deepcopy(PINS)
    tags = tags if tags is not None else {m: v["digest"] for m, v in pins["models"].items()}
    t = MockTransport(version, tags, replies or [ok_reply('{"choice": "GO"}')])
    llm = CachedLLM(transport=t, pins=pins, models=["qwen2.5:7b"], cache_dir=tmp_path / "cache", machine_id="T1",
                    gpu="test", sleep=(sleeps.append if sleeps is not None else (lambda s: None)))
    return llm, t


AGENTS = ["J", "M", "Q", "T", "Z"]


def valid_record():
    """A minimal valid 2-round Type 1 record; Q's round-2 Stage 3 failed and was imputed."""
    def dec(key, a):
        return {key: a, "reasoning": "r", "parse_ok": True, "imputed": False, "call": "k"}

    rounds = []
    for r in (1, 2):
        choices = {"J": "STAY", "M": "GO", "Q": "STAY", "T": "GO", "Z": "STAY"}
        s3 = {a: dec("choice", c) for a, c in choices.items()}
        if r == 2:
            s3["Q"] = {"choice": None, "reasoning": "", "parse_ok": False, "imputed": True, "call": "k"}
        rounds.append({
            "round": r, "order": AGENTS,
            "stage1": {a: dec("intended_action", "GO") for a in AGENTS},
            "channel": [{"exchange": "A", "from": "M", "to": "T", "text": "both go", "call": "k"}],
            "stage2": [dict(dec("stated_action", "STAY"), agent=a, position=i, message="m") for i, a in enumerate(AGENTS)],
            "stage3": s3,
            "outcome": {"n_go": 2, "crowded": False, "payoffs_public": {a: (10 if a in "MT" else 0) for a in AGENTS},
                        "payoffs_private": {a: (10 if a in "MT" else 0) for a in AGENTS}},
        })
    return {
        "schema_version": "1.0", "game_id": "g_0123456789", "created_utc": "2026-10-24T09:00:00Z",
        "harness": {"repo": "poseidon-research/collusion_hackathon", "commit": "d585a7b", "game": "elfarol"},
        "config": {"game_id": "g_0123456789", "episode_type": 1, "focal_pair": ["M", "T"], "agents": AGENTS,
                   "n_rounds": 2},
        "rounds": rounds,
        "failures": [{"round": 2, "stage": "stage3", "agent": "Q", "kind": "parse_error", "raw_excerpt": "{oops"}],
        "usage": {"calls": 38}, "machine_id": "A", "ollama_version": "0.40.3",
        "machine": "A", "wall_s": 90.0, "prompts": {"alliance_v2.txt": "0" * 64},
    }
