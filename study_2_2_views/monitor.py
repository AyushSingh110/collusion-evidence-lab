"""Monitor runner: score rendered views with a local LLM through core.llm.CachedLLM (report 00 §7).

One system prompt for all views (configs/monitor/monitor_v1.txt); only the what-you-see sentence
changes. No calibration, thresholds or freezing here (that is P7).

A response is never silently accepted when it may be truncated: the truncation_suspect flag from
CachedLLM (prompt_eval_count >= num_ctx/2 or done_reason == "length") sets score to None.
Transport failures go to errors.jsonl, not monitor.jsonl, so a resumed run tries them again.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

from core.clean.cleaner import RULES_TEXT
from core.config import (CONFIGS, REPO_ROOT, atomic_write_text, canonical_json, load_json, read_text_lf, sha256_of,
                         text_file_sha256)

MONITOR_DIR = CONFIGS / "monitor"


@dataclass(frozen=True)
class MonitorConfig:
    prompt_version: str
    template: str
    template_sha256: str
    model: str
    temperature: float
    num_ctx: int
    num_predict: int
    max_rationale_words: int
    agents: tuple[str, ...]
    what_you_see: dict[str, str]
    view_prompt: dict[str, str]
    output_schema: dict[str, Any]
    manifest_sha256: str
    format: str = "single"            # "single": one score + pair; "pairs": one score per pair
    pair_order: tuple[str, ...] = ()  # pairs format: fixed key order, e.g. ("J-M", "J-Q", ...)
    rationale_field: str = "rationale"
    pairs_extras: bool = False        # v3_pairs: also validate the model's suspected_pair, store it and the margin
    evidence_max_chars: Optional[int] = None


# candidate prompts live side by side in configs/monitor/ (task 07, task 11); v1 stays the default
PROMPTS = {"monitor_v1": "manifest.json", "monitor_v2_anchored": "manifest_v2_anchored.json",
           "monitor_v2_pairs": "manifest_v2_pairs.json", "monitor_v3_pairs": "manifest_v3_pairs.json"}


def load_config(directory: Path = MONITOR_DIR, manifest: str = "manifest.json") -> MonitorConfig:
    """Load a monitor manifest + its template; refuse if the template hash does not match."""
    man = load_json(directory / manifest)
    template = read_text_lf(directory / man["template"])
    got = text_file_sha256(directory / man["template"])
    if got != man["template_sha256"]:
        raise ValueError(f"monitor template sha256 {got[:12]}... != manifest {man['template_sha256'][:12]}...")
    return MonitorConfig(
        prompt_version=man["prompt_version"], template=template, template_sha256=got,
        model=man["model"], temperature=float(man["temperature"]), num_ctx=int(man["num_ctx"]),
        num_predict=int(man["num_predict"]), max_rationale_words=int(man["max_rationale_words"]),
        agents=tuple(man["agents"]), what_you_see=dict(man["what_you_see"]), view_prompt=dict(man["view_prompt"]),
        output_schema=man["output_schema"], manifest_sha256=sha256_of(man),
        format=man.get("format", "single"), pair_order=tuple(man.get("pair_order", ())),
        rationale_field=man.get("rationale_field", "rationale"), pairs_extras=bool(man.get("pairs_extras", False)),
        evidence_max_chars=man["output_schema"]["properties"].get(man.get("rationale_field", "rationale"), {})
        .get("maxLength"))


def system_prompt(cfg: MonitorConfig, view: str) -> str:
    if view not in cfg.view_prompt:
        raise ValueError(f"no prompt sentence for view {view!r}")
    sentence = cfg.what_you_see[cfg.view_prompt[view]]
    return cfg.template.replace("{rules}", RULES_TEXT).replace("{what_you_see}", sentence).strip()


def monitor_seed(game_id: str, view: str, sample_idx: int) -> int:
    return int(hashlib.sha256(f"{game_id}|{view}|{sample_idx}".encode("utf-8")).hexdigest(), 16) % 2 ** 31


def _bad_score(s) -> bool:
    return isinstance(s, bool) or not isinstance(s, int) or not 0 <= s <= 100


def validate_output(parsed: Optional[dict], cfg: MonitorConfig) -> list[str]:
    """Problems with a parsed monitor reply; an empty list means it is valid."""
    if not isinstance(parsed, dict):
        return ["not a JSON object"]
    errs = []
    if cfg.format == "pairs":
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
        if cfg.pairs_extras:
            p = parsed.get("suspected_pair")
            if not isinstance(p, list) or len(p) not in (0, 2):
                errs.append(f"suspected_pair {p!r} is not a list of 0 or 2 names")
            elif len(p) == 2 and (p[0] == p[1] or any(x not in cfg.agents for x in p)):
                errs.append(f"suspected_pair {p!r} must be two distinct names from {list(cfg.agents)}")
    else:
        s = parsed.get("score")
        if _bad_score(s):
            errs.append(f"score {s!r} is not an integer in 0..100")
        p = parsed.get("suspected_pair")
        if not isinstance(p, list) or len(p) not in (0, 2):
            errs.append(f"suspected_pair {p!r} is not a list of 0 or 2 names")
        elif len(p) == 2 and (p[0] == p[1] or any(x not in cfg.agents for x in p)):
            errs.append(f"suspected_pair {p!r} must be two distinct names from {list(cfg.agents)}")
    ev = parsed.get(cfg.rationale_field)
    if not isinstance(ev, str):
        errs.append(f"{cfg.rationale_field} is not a string")
    elif cfg.evidence_max_chars is not None and len(ev) > cfg.evidence_max_chars:
        errs.append(f"{cfg.rationale_field} longer than {cfg.evidence_max_chars} characters ({len(ev)})")
    return errs


def game_score_from_pairs(pair_scores: dict[str, int], pair_order: Sequence[str]) -> tuple[int, list[str]]:
    """Game score = max over pairs; suspected pair = argmax, or [] when the max is shared (tie)."""
    top = max(pair_scores[k] for k in pair_order)
    winners = [k for k in pair_order if pair_scores[k] == top]
    return top, (winners[0].split("-") if len(winners) == 1 else [])


def pair_margin(pair_scores: dict[str, int], pair_order: Sequence[str]) -> int:
    """Max minus second-highest pair score (0 when the max is tied), for later tie analysis."""
    vals = sorted((pair_scores[k] for k in pair_order), reverse=True)
    return vals[0] - vals[1] if len(vals) > 1 else 0


def _decode(parsed: dict, cfg: MonitorConfig) -> tuple[int, list[str]]:
    if cfg.format == "pairs":
        return game_score_from_pairs(parsed["pair_scores"], cfg.pair_order)
    return parsed["score"], list(parsed["suspected_pair"])


def score_view(text: str, view: str, llm, cfg: MonitorConfig, *, game_id: str, sample_idx: int = 0) -> dict:
    """One monitor call. Returns an output line (without run_id)."""
    sys_p = system_prompt(cfg, view)
    messages = [{"role": "system", "content": sys_p}, {"role": "user", "content": text}]
    res = llm.complete(model=cfg.model, messages=messages, format_schema=cfg.output_schema, num_ctx=cfg.num_ctx,
                       num_predict=cfg.num_predict, temperature=cfg.temperature,
                       seed=monitor_seed(game_id, view, sample_idx), sample_idx=sample_idx,
                       purpose=f"monitor:{cfg.prompt_version}:{view}")
    errs = [] if res.error else ([res.parse_error] if res.parse_error else validate_output(res.parsed, cfg))
    parse_ok = res.error is None and not errs
    pec = res.prompt_eval_count
    trunc = bool(res.truncation_suspect or (pec is not None and pec >= cfg.num_ctx / 2))
    accepted = parse_ok and not trunc
    rationale = res.parsed.get(cfg.rationale_field) if parse_ok else None
    raw_score, raw_pair = _decode(res.parsed, cfg) if parse_ok else (None, [])
    if raw_score is None and cfg.format == "single" and isinstance(res.parsed, dict):
        raw_score = res.parsed.get("score")
    line = {
        "game_id": game_id, "view": view, "model": cfg.model, "digest": res.model_digest,
        "prompt_version": cfg.prompt_version, "prompt_sha256": sha256_of(messages[0]["content"]),
        "view_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "sample_idx": sample_idx,
        "score": raw_score if accepted else None,
        "suspected_pair": raw_pair if accepted else [],
        "rationale": rationale, "rationale_words": len(rationale.split()) if rationale else None,
        "rationale_over_limit": bool(rationale) and len(rationale.split()) > cfg.max_rationale_words,
        "parse_ok": parse_ok, "errors": errs, "truncation_suspect": trunc,
        "raw_score": raw_score,
        "cache_key": res.cache_key, "cache_hit": res.cache_hit, "latency": res.latency_s,
        "prompt_eval_count": pec, "eval_count": res.eval_count, "done_reason": res.done_reason,
        "error": res.error,
    }
    if cfg.format == "pairs":
        line["pair_scores"] = ({k: res.parsed["pair_scores"][k] for k in cfg.pair_order} if parse_ok else None)
        if cfg.pairs_extras:
            line["margin"] = pair_margin(res.parsed["pair_scores"], cfg.pair_order) if parse_ok else None
            line["model_suspected_pair"] = list(res.parsed.get("suspected_pair") or []) if parse_ok else None
    return line


# --------------------------------------------------------------------------- runner

def _git(*args: str) -> Optional[str]:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def code_version() -> dict:
    """Read-only git info + pip freeze hash (report 00 §12)."""
    try:
        freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True,
                                timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        freeze = ""
    status = _git("status", "--porcelain")
    return {"git_head": _git("rev-parse", "HEAD"), "uncommitted_changes": bool(status) if status is not None else None,
            "pip_freeze_sha256": hashlib.sha256(freeze.encode("utf-8")).hexdigest() if freeze else None}


def view_file_id(path: Path) -> tuple[str, str]:
    """data/views/<view>/<game_id>.txt -> (view, game_id)."""
    return path.parent.name, path.stem


def _read_done(path: Path) -> set[tuple[str, str, int]]:
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                done.add((d["game_id"], d["view"], d["sample_idx"]))
    return done


def pending(view_files: Sequence[Path], run_id: str, runs_dir: Path, sample_idx: int = 0) -> list[Path]:
    done = _read_done(Path(runs_dir) / run_id / "outputs" / "monitor.jsonl")
    return [p for p in sorted(map(Path, view_files)) if (view_file_id(p)[1], view_file_id(p)[0], sample_idx) not in done]


def run_monitor(view_files: Sequence[Path], run_id: str, llm, cfg: MonitorConfig, *,
                runs_dir: Path = REPO_ROOT / "runs", sample_idx: int = 0, progress=print) -> dict:
    """Score every view file once (per sample_idx). Resumable: lines already written are skipped."""
    run_dir = Path(runs_dir) / run_id
    out, err_path = run_dir / "outputs" / "monitor.jsonl", run_dir / "outputs" / "errors.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    todo = pending(view_files, run_id, runs_dir, sample_idx)
    man_path = run_dir / "manifest.json"
    man = load_json(man_path) if man_path.exists() else {
        "run_id": run_id, "kind": "monitor", "prompt_version": cfg.prompt_version,
        "template_sha256": cfg.template_sha256, "monitor_manifest_sha256": cfg.manifest_sha256,
        "model": cfg.model, "digest": llm.digests.get(cfg.model), "ollama_version": llm.ollama_version,
        "temperature": cfg.temperature, "num_ctx": cfg.num_ctx, "num_predict": cfg.num_predict,
        "seed_rule": "sha256(game_id|view|sample_idx) mod 2^31", "sessions": []}
    session = {"machine_id": llm.machine_id, "gpu": llm.gpu, "n_files": len(view_files), "n_pending": len(todo),
               "sample_idx": sample_idx, **code_version()}
    written = errors = truncated = 0
    for k, path in enumerate(todo, start=1):
        view, gid = view_file_id(path)
        line = {"run_id": run_id, **score_view(path.read_text(encoding="utf-8"), view, llm, cfg, game_id=gid,
                                               sample_idx=sample_idx)}
        target = err_path if line["error"] else out
        with open(target, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")
        errors += bool(line["error"])
        written += not line["error"]
        truncated += line["truncation_suspect"]
        progress(f"[{k}/{len(todo)}] {view} {gid}: score={line['score']} pair={line['suspected_pair']} "
                 f"parse_ok={line['parse_ok']} trunc={line['truncation_suspect']} latency={line['latency']}")
    session.update({"written": written, "transport_errors": errors, "truncation_suspect": truncated,
                    "skipped_already_done": len(view_files) - len(todo)})
    man["sessions"].append(session)
    atomic_write_text(man_path, canonical_json(man))
    return session
