"""Per-stage prompts: harness builders (read-only import) + history block + addendum + brevity line.

Slot (report 01 §6): system = harness system prompt + "\n\n" + history + ["\n\n" + addendum, focal only].
The brevity line (if on) is appended to EVERY user prompt of EVERY agent, identically.
Imports only the harness prompt builders and games - never its settings.py, LLM clients or poseidon_compute.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from core.config import CONFIGS, REPO_ROOT, atomic_write_text
from core.generate.elfarol import AGENTS, STANDARD_PARAMS

HARNESS_DIR = REPO_ROOT / "external" / "llm-trust-breaking"
PROMPTS_DIR = CONFIGS / "prompts"
MANIFEST = PROMPTS_DIR / "manifest.json"
GAME = "elfarol"
# Type 1 uses alliance_v3 = alliance_v2 + collusion_hint_v1 (pre-freeze change, task 06a); placebo_v3 is
# length-matched to it. The v2 and hint files stay in configs/prompts/ for history.
ADDENDUM_FILES = {1: "alliance_v3.txt", 2: "placebo_v3.txt", 3: "persona_v1.txt", 4: "incentive_4b_v1.txt"}

if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))
_old_dwb, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # Rule F: write nothing into external/
try:
    from src.endogenous.core import prompt_builders as _pb  # noqa: E402  (harness, read-only)
    import src.games  # noqa: E402,F401  the builders import this lazily; import it here, under the guard
finally:
    sys.dont_write_bytecode = _old_dwb

CHANNEL_SCHEMA = {"type": "object", "properties": {"message": {"type": "string",
                  "description": "Your private message, at most 60 words."}},
                  "required": ["message"], "additionalProperties": False}


def read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip("\n")


def file_sha256(name: str) -> str:
    return hashlib.sha256((PROMPTS_DIR / name).read_bytes()).hexdigest()


def prompt_files() -> list[str]:
    return sorted(p.name for p in PROMPTS_DIR.iterdir() if p.is_file() and p.name != "manifest.json")


def write_manifest(measured_tokens: Optional[Mapping[str, Any]] = None) -> dict:
    """Recompute sha256 of every prompt file (keeps the stored measured token counts)."""
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    doc = {"sha256": {n: file_sha256(n) for n in prompt_files()},
           "measured_tokens_qwen2.5_7b": dict(measured_tokens or old.get("measured_tokens_qwen2.5_7b", {}))}
    atomic_write_text(MANIFEST, json.dumps(doc, indent=1) + "\n")
    return doc


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def addendum_text(episode_type: int, partner: str) -> str:
    return read_prompt(ADDENDUM_FILES[episode_type]).replace("{P}", partner)


def _system(harness_system: str, history: str, addendum: Optional[str]) -> str:
    out = harness_system.rstrip() + "\n\n" + history
    return out + ("\n\n" + addendum if addendum else "")


def _user(text: str, brevity: Optional[str]) -> str:
    return text + ("\n\n" + brevity if brevity else "")


def _private_block(private_now: Optional[Sequence[Mapping[str, str]]]) -> str:
    return ("Private messages with your partner this round (nobody else saw them):\n"
            + "\n".join(f'  {m["from"]}: "{m.get("text") or ""}"' for m in private_now))


def stage1(agent: str, history: str, addendum: Optional[str], brevity: Optional[str]):
    s, u, schema = _pb.build_stage1_prompt(GAME, agent, list(AGENTS), dict(STANDARD_PARAMS), True, takeaways=None)
    return _system(s, history, addendum), _user(u, brevity), schema["schema"]


def stage2(agent: str, plan: Mapping[str, Any], prior: Sequence[Mapping[str, Any]], history: str,
           addendum: Optional[str], brevity: Optional[str], private_now=None):
    s, u, schema = _pb.build_stage2_prompt(GAME, agent, list(AGENTS), dict(plan), dict(STANDARD_PARAMS), True,
                                           prior_announcements=list(prior))
    if private_now:
        u += "\n\n" + _private_block(private_now)
    return _system(s, history, addendum), _user(u, brevity), schema["schema"]


def stage3(agent: str, stage2_all: Mapping[str, Mapping[str, Any]], plan: Mapping[str, Any],
           own_s2: Mapping[str, Any], history: str, addendum: Optional[str], brevity: Optional[str], private_now=None):
    s, u, schema = _pb.build_stage3_prompt(GAME, agent, list(AGENTS), {k: dict(v) for k, v in stage2_all.items()},
                                           dict(STANDARD_PARAMS), dict(plan), dict(own_s2), True, True)
    if private_now:
        marker = "\nNow choose your ACTUAL action"
        u = u.replace(marker, "\n" + _private_block(private_now) + "\n" + marker, 1)
    return _system(s, history, addendum), _user(u, brevity), schema["schema"]


def channel(agent: str, partner: str, rnd: int, exchange: str, so_far: Sequence[Mapping[str, str]], history: str,
            addendum: Optional[str], brevity: Optional[str], announcements=None):
    """System prompt = the agent's own Stage-1 system prompt (rules + history + addendum)."""
    s, _, _ = _pb.build_stage1_prompt(GAME, agent, list(AGENTS), dict(STANDARD_PARAMS), True, takeaways=None)
    so = ("Private messages so far this round:\n" + "\n".join(f'  {m["from"]}: "{m.get("text") or ""}"' for m in so_far)
          + "\n") if so_far else ""
    if exchange == "A":
        u = read_prompt("channel_A_v1.txt").format(round=rnd, partner=partner, so_far=so)
    else:
        ann = ("Public announcements made this round:\n"
               + "\n".join(f'  Agent {p["name"]} (stated action: {p["stated_action"]}): "{p["message"]}"'
                           for p in announcements or []) + "\n")
        u = read_prompt("channel_B_v1.txt").format(round=rnd, partner=partner, so_far=so, announcements=ann)
    return _system(s, history, addendum), _user(u, brevity), CHANNEL_SCHEMA
