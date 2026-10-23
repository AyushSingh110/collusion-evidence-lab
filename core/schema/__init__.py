"""Data schemas (report 00 §5 as revised by report 01) and game-record validation.

Records are stored as JSON dicts; the dataclasses define the fields and give to_dict/from_dict.
validate_game() works on the JSON dict so it can check files written by any machine.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Optional

from core.config import sha256_of

SCHEMA_VERSION = "1.0"
ACTIONS = ("GO", "STAY")
EPISODE_TYPES = (1, 2, 3, 4)
GAME_ID_RE = re.compile(r"^g_[0-9a-f]{10}$")


def _from_dict(cls, d: dict[str, Any]):
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in d.items() if k in names})


@dataclass
class PlanEntry:
    game_id: str
    plan_index: int
    plan_name: str
    master_seed: int
    episode_type: int
    variant: str
    focal_pair: list[str]
    game_seed: int
    n_rounds: int
    machine: str
    est_minutes: float
    config_sha256: str = ""

    def config_fields(self) -> dict[str, Any]:
        """Fields that define the game; machine and time estimate are scheduling, not config."""
        d = asdict(self)
        for k in ("machine", "est_minutes", "config_sha256"):
            d.pop(k)
        return d

    def compute_sha256(self) -> str:
        return sha256_of(self.config_fields())

    to_dict = asdict

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PlanEntry":
        return _from_dict(cls, d)


@dataclass
class GameConfig:
    game_id: str
    episode_type: int
    variant: str
    focal_pair: list[str]
    agents: list[str]
    agent_model: str
    agent_digest: str
    temperature: float
    n_rounds: int
    num_ctx: int
    num_predict: dict[str, int]
    game_params: dict[str, float]
    game_seed: int
    master_seed: int
    plan_name: str
    synthetic: bool = False
    private_payoff_overrides: dict[str, dict[str, float]] = field(default_factory=dict)
    addenda: dict[str, str] = field(default_factory=dict)
    private_channel: dict[str, Any] = field(default_factory=dict)
    announce_orders: list[list[str]] = field(default_factory=list)

    to_dict = asdict

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameConfig":
        return _from_dict(cls, d)


@dataclass
class CallMeta:
    """Per-call metadata kept inside a GameRecord (the full call lives in the cache)."""
    cache_key: str
    purpose: str
    cache_hit: bool
    latency_s: Optional[float]
    prompt_eval_count: Optional[int]
    eval_count: Optional[int]
    done_reason: Optional[str]
    truncation_suspect: bool
    error: Optional[str]
    attempts: int = 1

    to_dict = asdict


@dataclass
class Failure:
    round: int
    stage: str          # stage1 | channel_A | stage2 | channel_B | stage3
    agent: str
    kind: str           # parse_error | truncated | transport_error | invalid_action
    raw_excerpt: str
    cache_key: Optional[str] = None

    to_dict = asdict


@dataclass
class GameRecord:
    game_id: str
    created_utc: str
    harness: dict[str, str]
    config: dict[str, Any]
    rounds: list[dict[str, Any]]
    failures: list[dict[str, Any]]
    usage: dict[str, Any]
    machine_id: str
    ollama_version: str
    schema_version: str = SCHEMA_VERSION

    to_dict = asdict

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameRecord":
        return _from_dict(cls, d)


@dataclass
class Label:
    game_id: str
    episode_type: int
    collusion: int
    focal_pair: list[str]
    variant: str
    synthetic: bool

    to_dict = asdict


@dataclass
class Split:
    created_utc: str
    seed: int
    dev_frac: float
    stratify: str
    labels_sha256: str
    dev: list[str]
    test: list[str]

    to_dict = asdict

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Split":
        return _from_dict(cls, d)


@dataclass
class LLMResult:
    cache_key: str
    cache_hit: bool
    content: Optional[str]
    parsed: Optional[dict[str, Any]]
    parse_error: Optional[str]
    prompt_eval_count: Optional[int]
    eval_count: Optional[int]
    durations_ns: dict[str, Optional[int]]
    done_reason: Optional[str]
    latency_s: Optional[float]
    truncation_suspect: bool
    model_tag: str
    model_digest: str
    ollama_version: str
    machine_id: str
    created_utc: str
    error: Optional[str]
    attempts: list[dict[str, Any]]

    to_dict = asdict

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LLMResult":
        return _from_dict(cls, d)

    def meta(self, purpose: str) -> CallMeta:
        return CallMeta(self.cache_key, purpose, self.cache_hit, self.latency_s, self.prompt_eval_count,
                        self.eval_count, self.done_reason, self.truncation_suspect, self.error, len(self.attempts) or 1)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
_TOP_KEYS = ("schema_version", "game_id", "created_utc", "harness", "config", "rounds", "failures", "usage",
             "machine_id", "ollama_version")
_DECISION_KEYS = {"stage1": "intended_action", "stage3": "choice"}


def _check_decision(errs, where, entry, action_key, failures_at):
    for k in (action_key, "parse_ok", "imputed", "call"):
        if k not in entry:
            errs.append(f"{where}: missing '{k}'")
            return
    act = entry[action_key]
    if act is not None and act not in ACTIONS:
        errs.append(f"{where}: invalid action {act!r}")
    if act is None and entry["parse_ok"]:
        errs.append(f"{where}: action is None but parse_ok is true")
    if not entry["parse_ok"]:
        if not entry["imputed"]:
            errs.append(f"{where}: failed decision must be marked imputed=true")
        if not failures_at:
            errs.append(f"{where}: failed decision has no failures[] entry")
    elif entry["imputed"]:
        errs.append(f"{where}: imputed=true but parse_ok is true")


def validate_game(rec: dict[str, Any]) -> list[str]:
    """Return a list of problems; an empty list means the record is valid."""
    errs: list[str] = []
    for k in _TOP_KEYS:
        if k not in rec:
            errs.append(f"missing top-level key '{k}'")
    if errs:
        return errs
    if rec["schema_version"] != SCHEMA_VERSION:
        errs.append(f"schema_version {rec['schema_version']!r} != {SCHEMA_VERSION!r}")
    if not GAME_ID_RE.match(str(rec["game_id"])):
        errs.append(f"game_id {rec['game_id']!r} does not match g_<10 hex>")
    cfg = rec["config"]
    for k in ("episode_type", "focal_pair", "agents", "n_rounds", "game_id"):
        if k not in cfg:
            errs.append(f"config missing '{k}'")
    if errs:
        return errs
    if cfg["game_id"] != rec["game_id"]:
        errs.append("config.game_id differs from record game_id")
    agents = list(cfg["agents"])
    if cfg["episode_type"] not in EPISODE_TYPES:
        errs.append(f"episode_type {cfg['episode_type']!r} not in {EPISODE_TYPES}")
    fp = cfg["focal_pair"]
    if len(fp) != 2 or fp[0] == fp[1] or any(a not in agents for a in fp):
        errs.append(f"focal_pair {fp!r} is not two distinct agents")
    if len(rec["rounds"]) != cfg["n_rounds"]:
        errs.append(f"{len(rec['rounds'])} rounds recorded but n_rounds={cfg['n_rounds']}")

    fail_index = {(f.get("round"), f.get("stage"), f.get("agent")) for f in rec["failures"]}
    for f in rec["failures"]:
        for k in ("round", "stage", "agent", "kind", "raw_excerpt"):
            if k not in f:
                errs.append(f"failure entry missing '{k}': {f}")

    for i, r in enumerate(rec["rounds"], start=1):
        w = f"round {i}"
        if r.get("round") != i:
            errs.append(f"{w}: round number {r.get('round')!r} out of sequence")
        for stage, key in _DECISION_KEYS.items():
            entries = r.get(stage, {})
            if sorted(entries) != sorted(agents):
                errs.append(f"{w} {stage}: agents {sorted(entries)} != {sorted(agents)}")
                continue
            for a in agents:
                _check_decision(errs, f"{w} {stage} {a}", entries[a], key, (i, stage, a) in fail_index)
        s2 = r.get("stage2", [])
        if sorted(e.get("agent") for e in s2) != sorted(agents):
            errs.append(f"{w} stage2: speakers {[e.get('agent') for e in s2]} are not each agent once")
        else:
            if [e.get("position") for e in s2] != list(range(len(agents))):
                errs.append(f"{w} stage2: positions are not 0..{len(agents) - 1} in order")
            for e in s2:
                _check_decision(errs, f"{w} stage2 {e['agent']}", e, "stated_action", (i, "stage2", e["agent"]) in fail_index)
        if r.get("channel") and cfg["episode_type"] != 1:
            errs.append(f"{w}: private channel messages in a type {cfg['episode_type']} game")
        out = r.get("outcome", {})
        for k in ("n_go", "crowded", "payoffs_public", "payoffs_private"):
            if k not in out:
                errs.append(f"{w} outcome: missing '{k}'")
        if all(k in out for k in ("n_go", "payoffs_public", "payoffs_private")) and sorted(r.get("stage3", {})) == sorted(agents):
            played = [r["stage3"][a]["choice"] or "STAY" for a in agents]  # imputed None plays as STAY
            if out["n_go"] != played.count("GO"):
                errs.append(f"{w} outcome: n_go={out['n_go']} but {played.count('GO')} agents went")
            for k in ("payoffs_public", "payoffs_private"):
                if sorted(out[k]) != sorted(agents):
                    errs.append(f"{w} outcome: {k} keys {sorted(out[k])} != agents")
    return errs
