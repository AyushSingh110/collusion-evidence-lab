"""Conversation judge C_judge(P) (report 00 §8 E1): one llama3.1:8b call per game returns all 10 pair scores.

Input = the cleaned PUBLIC MESSAGES ONLY (data/clean CleanGame): no announced actions, no final actions, no payoffs,
no setup text, no condition names, no labels. All calls go through core.llm.CachedLLM (cache, pins, num_ctx).

Validation follows monitor_v3_pairs: all 10 pairs in the fixed order, integers 0..100, no unknown pairs, evidence a
string of at most maxLength characters. A reply is never silently accepted when it may be truncated
(prompt_eval_count >= num_ctx/2 or done_reason == "length"): its pair scores become None (C_judge NA, never 0).
Transport failures go to errors.jsonl, not judge.jsonl, so a resumed run tries them again.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from core.clean.cleaner import RULES_TEXT
from core.clean.types import CleanGame
from core.config import CONFIGS, REPO_ROOT, atomic_write_text, canonical_json, load_json, read_text_lf, sha256_of, \
    text_file_sha256
from study_2_2_views.monitor import code_version, game_score_from_pairs, pair_margin

JUDGE_DIR = CONFIGS / "judge"


@dataclass(frozen=True)
class JudgeConfig:
    prompt_version: str
    template: str
    template_sha256: str
    model: str
    temperature: float
    num_ctx: int
    num_predict: int
    agents: tuple[str, ...]
    pair_order: tuple[str, ...]
    evidence_field: str
    evidence_max_chars: Optional[int]
    output_schema: dict[str, Any]
    manifest_sha256: str


def load_config(directory: Path = JUDGE_DIR, manifest: str = "manifest.json") -> JudgeConfig:
    """Load the judge manifest + template; refuse if the template hash does not match."""
    man = load_json(directory / manifest)
    template = read_text_lf(directory / man["template"])
    got = text_file_sha256(directory / man["template"])
    if got != man["template_sha256"]:
        raise ValueError(f"judge template sha256 {got[:12]}... != manifest {man['template_sha256'][:12]}...")
    ev = man["evidence_field"]
    return JudgeConfig(
        prompt_version=man["prompt_version"], template=template, template_sha256=got, model=man["model"],
        temperature=float(man["temperature"]), num_ctx=int(man["num_ctx"]), num_predict=int(man["num_predict"]),
        agents=tuple(man["agents"]), pair_order=tuple(man["pair_order"]), evidence_field=ev,
        evidence_max_chars=man["output_schema"]["properties"].get(ev, {}).get("maxLength"),
        output_schema=man["output_schema"], manifest_sha256=sha256_of(man))


def system_prompt(cfg: JudgeConfig) -> str:
    return cfg.template.replace("{rules}", RULES_TEXT).strip()


def render_messages(clean: CleanGame | Mapping[str, Any]) -> str:
    """Public messages only, per round in speaking order. Nothing else from the CleanGame is used."""
    c = clean if isinstance(clean, CleanGame) else CleanGame.from_dict(dict(clean))
    lines = [f"PUBLIC MESSAGES: 5 players ({', '.join(c.agents)}), {len(c.rounds)} rounds.", ""]
    for r in c.rounds:
        lines.append(f"ROUND {r.round}")
        for a in sorted(r.announcements, key=lambda x: x.position):
            msg = (a.message or "").strip()
            lines.append(f'  {a.agent}: "{msg}"' if msg else f"  {a.agent}: (no message)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def judge_seed(game_id: str, sample_idx: int) -> int:
    return int(hashlib.sha256(f"judge|{game_id}|{sample_idx}".encode("utf-8")).hexdigest(), 16) % 2 ** 31


def _bad_score(s) -> bool:
    return isinstance(s, bool) or not isinstance(s, int) or not 0 <= s <= 100


def validate_output(parsed: Optional[dict], cfg: JudgeConfig) -> list[str]:
    """Problems with a parsed judge reply; an empty list means it is valid."""
    if not isinstance(parsed, dict):
        return ["not a JSON object"]
    errs = []
    ps = parsed.get("pair_scores")
    if not isinstance(ps, dict):
        errs.append("pair_scores is not an object")
    else:
        missing = [k for k in cfg.pair_order if k not in ps]
        extra = sorted(k for k in ps if k not in cfg.pair_order)
        if missing:
            errs.append(f"pair_scores missing {missing}")
        if extra:
            errs.append(f"pair_scores has unknown pairs {extra}")
        bad = [k for k in cfg.pair_order if k in ps and _bad_score(ps[k])]
        if bad:
            errs.append(f"pair_scores not integers in 0..100 for {bad}")
    ev = parsed.get(cfg.evidence_field)
    if not isinstance(ev, str):
        errs.append(f"{cfg.evidence_field} is not a string")
    elif cfg.evidence_max_chars is not None and len(ev) > cfg.evidence_max_chars:
        errs.append(f"{cfg.evidence_field} longer than {cfg.evidence_max_chars} characters ({len(ev)})")
    return errs


def judge_game(clean: CleanGame | Mapping[str, Any], llm, cfg: JudgeConfig, *, sample_idx: int = 0) -> dict:
    """One judge call for one game. Returns an output line (without run_id)."""
    c = clean if isinstance(clean, CleanGame) else CleanGame.from_dict(dict(clean))
    text = render_messages(c)
    messages = [{"role": "system", "content": system_prompt(cfg)}, {"role": "user", "content": text}]
    res = llm.complete(model=cfg.model, messages=messages, format_schema=cfg.output_schema, num_ctx=cfg.num_ctx,
                       num_predict=cfg.num_predict, temperature=cfg.temperature,
                       seed=judge_seed(c.game_id, sample_idx), sample_idx=sample_idx,
                       purpose=f"judge:{cfg.prompt_version}")
    errs = [] if res.error else ([res.parse_error] if res.parse_error else validate_output(res.parsed, cfg))
    parse_ok = res.error is None and not errs
    pec = res.prompt_eval_count
    trunc = bool(res.truncation_suspect or (pec is not None and pec >= cfg.num_ctx / 2))
    accepted = parse_ok and not trunc
    raw = {k: res.parsed["pair_scores"][k] for k in cfg.pair_order} if parse_ok else None
    score, pair = game_score_from_pairs(raw, cfg.pair_order) if parse_ok else (None, [])
    ev = res.parsed.get(cfg.evidence_field) if parse_ok else None
    return {
        "game_id": c.game_id, "model": cfg.model, "digest": res.model_digest, "prompt_version": cfg.prompt_version,
        "prompt_sha256": sha256_of(messages[0]["content"]), "input_sha256": sha256_of(text), "sample_idx": sample_idx,
        "pair_scores": raw if accepted else None, "raw_pair_scores": raw,
        "score": score if accepted else None, "top_pair": pair if accepted else [],
        "margin": pair_margin(raw, cfg.pair_order) if accepted else None,
        "evidence": ev, "evidence_chars": len(ev) if isinstance(ev, str) else None,
        "parse_ok": parse_ok, "errors": errs, "truncation_suspect": trunc, "done_reason": res.done_reason,
        "cache_key": res.cache_key, "cache_hit": res.cache_hit, "latency": res.latency_s,
        "prompt_eval_count": pec, "eval_count": res.eval_count, "num_ctx": cfg.num_ctx,
        "num_predict": cfg.num_predict, "temperature": cfg.temperature, "error": res.error,
    }


# --------------------------------------------------------------------------- runner

def _read_done(path: Path) -> set[tuple[str, int]]:
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                done.add((d["game_id"], d["sample_idx"]))
    return done


def output_path(run_id: str, runs_dir: Path) -> Path:
    return Path(runs_dir) / run_id / "outputs" / "judge.jsonl"


def pending(game_ids: Sequence[str], run_id: str, runs_dir: Path, sample_idx: int = 0) -> list[str]:
    done = _read_done(output_path(run_id, runs_dir))
    return [g for g in sorted(game_ids) if (g, sample_idx) not in done]


def run_judge(clean_dir: Path, game_ids: Sequence[str], run_id: str, llm, cfg: JudgeConfig, *,
              runs_dir: Path = REPO_ROOT / "runs", sample_idx: int = 0, progress=print) -> dict:
    """Judge every game once (per sample_idx). Resumable: lines already written are skipped."""
    run_dir = Path(runs_dir) / run_id
    out, err_path = output_path(run_id, runs_dir), run_dir / "outputs" / "errors.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    todo = pending(game_ids, run_id, runs_dir, sample_idx)
    man_path = run_dir / "manifest.json"
    man = load_json(man_path) if man_path.exists() else {
        "run_id": run_id, "kind": "judge", "prompt_version": cfg.prompt_version,
        "template_sha256": cfg.template_sha256, "judge_manifest_sha256": cfg.manifest_sha256, "model": cfg.model,
        "digest": llm.digests.get(cfg.model), "ollama_version": llm.ollama_version, "temperature": cfg.temperature,
        "num_ctx": cfg.num_ctx, "num_predict": cfg.num_predict, "input": "data/clean public messages only",
        "seed_rule": "sha256(judge|game_id|sample_idx) mod 2^31", "sessions": []}
    session = {"machine_id": llm.machine_id, "gpu": llm.gpu, "n_games": len(game_ids), "n_pending": len(todo),
               "sample_idx": sample_idx, **code_version()}
    written = errors = truncated = bad = 0
    for k, gid in enumerate(todo, start=1):
        clean = load_json(Path(clean_dir) / f"{gid}.json")
        line = {"run_id": run_id, **judge_game(clean, llm, cfg, sample_idx=sample_idx)}
        target = err_path if line["error"] else out
        with open(target, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")
        errors += bool(line["error"])
        written += not line["error"]
        truncated += line["truncation_suspect"]
        bad += not line["parse_ok"]
        progress(f"[{k}/{len(todo)}] {gid} s{sample_idx}: score={line['score']} top={line['top_pair']} "
                 f"parse_ok={line['parse_ok']} trunc={line['truncation_suspect']} pec={line['prompt_eval_count']} "
                 f"eval={line['eval_count']} latency={line['latency']}")
    session.update({"written": written, "transport_errors": errors, "truncation_suspect": truncated,
                    "not_parse_ok": bad, "skipped_already_done": len(game_ids) - len(todo)})
    man["sessions"].append(session)
    atomic_write_text(man_path, canonical_json(man))
    return session


def load_judge(path: Path, sample_idx: int = 0) -> dict[str, dict]:
    """judge.jsonl -> {game_id: line} for one sample_idx (refuses duplicates)."""
    out: dict[str, dict] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d["sample_idx"] != sample_idx:
            continue
        if d["game_id"] in out:
            raise ValueError(f"duplicate judge line for {d['game_id']} sample {sample_idx}")
        out[d["game_id"]] = d
    return out
