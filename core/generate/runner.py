"""run_game(): one El Farol game, following the call sequence of report 01 §8.2.

Per round (all calls sequential, one request at a time):
  1. history blocks (code)         2. Stage 1 x5          3. channel A x2 (Type 1 only)
  4. Stage 2 x5 in rotated order   5. channel B x2 (Type 1 only)   6. Stage 3 x5   7. outcome (code)
The record is written atomically after every round to <raw>/<game_id>.partial.json and, when the game is
complete, to <raw>/<game_id>.json (the partial file is then removed).
Resume rule: an unfinished game is re-run from round 1; finished calls are cache hits, so the replay is
identical and only the missing calls reach Ollama.
Failures are data: a missing/invalid action is played as STAY with imputed=true and a failures[] entry.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

import numpy as np

from core.config import REPO_ROOT, atomic_write_text
from core.generate import prompts as P
from core.generate.elfarol import AGENTS, STANDARD_PARAMS, outcome
from core.generate.history import history_block
from core.schema import Failure, GameConfig, GameRecord, PlanEntry

MODEL = "qwen2.5:7b"
PRIVATE_HOME_4B = -8.0
HARNESS_REPO = "poseidon-research/collusion_hackathon"


def harness_commit() -> str:
    src = REPO_ROOT / "external" / "SOURCE.txt"
    return src.read_text(encoding="utf-8").split()[0] if src.exists() else "unknown"


def call_seed(game_seed: int, rnd: int, stage: str, agent: str, exchange: str = "", sample_idx: int = 0) -> int:
    h = hashlib.sha256(f"{game_seed}|{rnd}|{stage}|{agent}|{exchange}|{sample_idx}".encode("utf-8")).hexdigest()
    return int(h, 16) % (2 ** 31)


def round_order(game_seed: int, rnd: int) -> list[str]:
    rng = np.random.default_rng(call_seed(game_seed, rnd, "order", ""))
    return [AGENTS[i] for i in rng.permutation(len(AGENTS))]


def first_writer(game_seed: int, rnd: int, exchange: str, focal: list[str]) -> str:
    return focal[call_seed(game_seed, rnd, "first_writer", "", exchange) % 2]


def check_manifest() -> dict[str, str]:
    """Refuse to run if a prompt file changed without updating configs/prompts/manifest.json."""
    man = P.load_manifest()["sha256"]
    now = {n: P.file_sha256(n) for n in P.prompt_files()}
    if man != now:
        bad = sorted(n for n in set(man) | set(now) if man.get(n) != now.get(n))
        raise RuntimeError(f"configs/prompts/manifest.json is out of date for: {bad}")
    return now


def build_config(entry: PlanEntry, run_defaults: Mapping[str, Any], digest: str) -> GameConfig:
    t, focal = entry.episode_type, list(entry.focal_pair)
    return GameConfig(
        game_id=entry.game_id, episode_type=t, variant=entry.variant, focal_pair=focal, agents=list(AGENTS),
        agent_model=MODEL, agent_digest=digest, temperature=run_defaults["temperature"]["agent"],
        n_rounds=entry.n_rounds, num_ctx=8192, num_predict=dict(run_defaults["num_predict"]),
        game_params=dict(STANDARD_PARAMS), game_seed=entry.game_seed, master_seed=entry.master_seed,
        plan_name=entry.plan_name, plan_index=entry.plan_index, plan_config_sha256=entry.config_sha256,
        brevity=bool(run_defaults.get("brevity", False)),
        private_payoff_overrides={a: {"home": PRIVATE_HOME_4B} for a in focal} if t == 4 else {},
        addenda={a: P.ADDENDUM_FILES[t] for a in focal},
        private_channel={"enabled": t == 1, "members": focal if t == 1 else [], "exchanges": ["A", "B"] if t == 1 else []},
        announce_orders=[round_order(entry.game_seed, r) for r in range(1, entry.n_rounds + 1)],
    )


def _prompt_files_used(cfg: GameConfig) -> list[str]:
    files = ["history_format.md", P.ADDENDUM_FILES[cfg.episode_type]]
    if cfg.brevity:
        files.append("brevity_v1.txt")
    if cfg.episode_type == 1:
        files += ["channel_A_v1.txt", "channel_B_v1.txt"]
        if "hint" in cfg.variant:
            files.append("collusion_hint_v1.txt")
    return sorted(files)


def run_game(entry: PlanEntry, llm, *, run_defaults: Mapping[str, Any], raw_dir: Path, machine: Optional[str] = None,
             stop_after_round: Optional[int] = None,
             progress: Optional[Callable[[str, int, int, float], None]] = None) -> Optional[dict]:
    """Run (or resume) one game. Returns the complete record, or None if stopped early (stop_after_round)."""
    shas = check_manifest()
    raw_dir = Path(raw_dir)
    final, partial = raw_dir / f"{entry.game_id}.json", raw_dir / f"{entry.game_id}.partial.json"
    prev_wall = json.loads(partial.read_text(encoding="utf-8")).get("wall_s", 0.0) if partial.exists() else 0.0
    t0 = time.monotonic()

    cfg = build_config(entry, run_defaults, llm.digests[MODEL])
    focal, t = cfg.focal_pair, cfg.episode_type
    partner = {focal[0]: focal[1], focal[1]: focal[0]}
    hint = "hint" in cfg.variant
    addendum = {a: P.addendum_text(t, partner[a], hint) for a in focal}
    brevity = P.read_prompt("brevity_v1.txt") if cfg.brevity else None
    npred = cfg.num_predict
    rounds: list[dict] = []
    failures: list[dict] = []
    usage = {"calls": 0, "cache_hits": 0, "transport_errors": 0, "prompt_tokens": 0, "completion_tokens": 0}

    def record(wall_s: float) -> dict:
        return GameRecord(
            game_id=cfg.game_id, created_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            harness={"repo": HARNESS_REPO, "commit": harness_commit(), "game": "elfarol"}, config=cfg.to_dict(),
            rounds=rounds, failures=failures, usage=usage, machine_id=llm.machine_id,
            ollama_version=llm.ollama_version, machine=machine or entry.machine, wall_s=round(wall_s, 2),
            prompts={n: shas[n] for n in _prompt_files_used(cfg)}).to_dict()

    def ask(rnd, stage, agent, exchange, system, user, schema, field, valid, num_predict):
        """One LLM call. Returns (value or None, parsed dict, call meta dict). Logs any failure."""
        seed = call_seed(cfg.game_seed, rnd, stage, agent, exchange)
        res = llm.complete(model=MODEL, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                           format_schema=schema, num_ctx=cfg.num_ctx, num_predict=num_predict,
                           temperature=cfg.temperature, seed=seed, sample_idx=0,
                           purpose=f"{cfg.game_id}|r{rnd}|{stage}|{agent}{'|' + exchange if exchange else ''}")
        meta = res.meta(stage)
        meta.seed = seed
        usage["calls"] += 1
        usage["cache_hits"] += int(res.cache_hit)
        usage["prompt_tokens"] += res.prompt_eval_count or 0
        usage["completion_tokens"] += res.eval_count or 0
        parsed = res.parsed or {}
        value = parsed.get(field)
        kind = None
        if res.error:
            kind = "transport_error"
            usage["transport_errors"] += 1
        elif res.parsed is None:
            kind = "truncated" if res.done_reason == "length" else "parse_error"
        elif not valid(value):
            kind = "invalid_action"
        if kind:
            failures.append(Failure(round=rnd, stage=stage, agent=agent, kind=kind,
                                    raw_excerpt=(res.error or res.content or "")[:300], cache_key=res.cache_key).to_dict())
            value = None
        return value, parsed, meta.to_dict()

    is_action = lambda v: v in ("GO", "STAY")  # noqa: E731
    is_text = lambda v: isinstance(v, str) and v.strip() != ""  # noqa: E731

    for rnd in range(1, cfg.n_rounds + 1):
        order = cfg.announce_orders[rnd - 1]
        last_channel = [{"from": c["from"], "text": c["text"]} for c in rounds[-1]["channel"]] if rounds else None
        hist = {a: history_block(rounds, a, private_home=PRIVATE_HOME_4B if (t == 4 and a in focal) else None,
                                 private_msgs=last_channel if (t == 1 and a in focal) else None) for a in AGENTS}
        add = lambda a: addendum.get(a)  # noqa: E731
        R: dict[str, Any] = {"round": rnd, "order": order, "stage1": {}, "channel": [], "stage2": [], "stage3": {}}

        for a in AGENTS:  # Stage 1
            s, u, sch = P.stage1(a, hist[a], add(a), brevity)
            v, parsed, meta = ask(rnd, "stage1", a, "", s, u, sch, "intended_action", is_action, npred["stage1"])
            R["stage1"][a] = {"intended_action": v, "reasoning": parsed.get("reasoning", "") if v else "",
                              "parse_ok": v is not None, "imputed": v is None, "call": meta}

        def exchange(ex: str, announcements=None):
            first = first_writer(cfg.game_seed, rnd, ex, focal)
            so_far = [{"from": c["from"], "text": c["text"]} for c in R["channel"]]
            for a in (first, partner[first]):
                s, u, sch = P.channel(a, partner[a], rnd, ex, so_far, hist[a], add(a), brevity, announcements)
                v, _, meta = ask(rnd, f"channel_{ex}", a, ex, s, u, sch, "message", is_text, npred["channel"])
                R["channel"].append({"exchange": ex, "from": a, "to": partner[a], "text": v or "",
                                     "parse_ok": v is not None, "call": meta})
                so_far.append({"from": a, "text": v or ""})

        if t == 1:
            exchange("A")
        prior = []
        for pos, a in enumerate(order):  # Stage 2, round-robin in the rotated order
            plan = {"intended_action": R["stage1"][a]["intended_action"], "reasoning": R["stage1"][a]["reasoning"]}
            priv = [{"from": c["from"], "text": c["text"]} for c in R["channel"]] if (t == 1 and a in focal) else None
            s, u, sch = P.stage2(a, plan, prior, hist[a], add(a), brevity, priv)
            v, parsed, meta = ask(rnd, "stage2", a, "", s, u, sch, "stated_action", is_action, npred["stage2"])
            msg = parsed.get("message", "") if v else ""
            R["stage2"].append({"agent": a, "position": pos, "stated_action": v, "message": msg,
                                "parse_ok": v is not None, "imputed": v is None, "call": meta})
            prior.append({"name": a, "stated_action": v, "message": msg})
        if t == 1:
            exchange("B", announcements=prior)
        s2_all = {e["agent"]: {"stated_action": e["stated_action"], "message": e["message"]} for e in R["stage2"]}
        for a in AGENTS:  # Stage 3
            plan = {"intended_action": R["stage1"][a]["intended_action"], "reasoning": R["stage1"][a]["reasoning"]}
            priv = [{"from": c["from"], "text": c["text"]} for c in R["channel"]] if (t == 1 and a in focal) else None
            s, u, sch = P.stage3(a, s2_all, plan, s2_all[a], hist[a], add(a), brevity, priv)
            v, parsed, meta = ask(rnd, "stage3", a, "", s, u, sch, "choice", is_action, npred["stage3"])
            R["stage3"][a] = {"choice": v, "reasoning": parsed.get("reasoning", "") if v else "",
                              "parse_ok": v is not None, "imputed": v is None, "call": meta}
        R["outcome"] = outcome({a: R["stage3"][a]["choice"] for a in AGENTS}, STANDARD_PARAMS,
                               {a: PRIVATE_HOME_4B for a in focal} if t == 4 else None)
        rounds.append(R)
        elapsed = prev_wall + time.monotonic() - t0
        atomic_write_text(partial, json.dumps(record(elapsed), indent=1))
        if progress:
            progress(cfg.game_id, rnd, cfg.n_rounds, elapsed)
        if stop_after_round is not None and rnd >= stop_after_round:
            return None

    rec = record(prev_wall + time.monotonic() - t0)
    atomic_write_text(final, json.dumps(rec, indent=1))
    partial.unlink(missing_ok=True)
    return rec
