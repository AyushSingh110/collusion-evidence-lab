"""Replication amendment 1 (configs/prereg_replication_amendment1.md §3): G1-G4 for the second monitor (granite3.3:8b)
next to the frozen llama monitor, on the replication games, views V1-V4, plus the descriptive measures.

Additive (task 20C); nothing existing changes. Reuses the outcome mapper of study_2_2_views.replication.

Statistics: 95% stratified bootstrap by episode type (whole games, B = 2000, seed 20261023). Every comparison uses the
games where all of its scores are present (others are counted as dropped), so two arms of a paired comparison -
two views of one monitor (G3) or two monitors on one view (G4) - share the same resample indices. G3 uses one common
game set for both monitors, so both D_m are computed on identical resamples.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Mapping, Optional, Sequence

from core.config import REPO_ROOT, read_text_lf, sha256_of, text_file_sha256
from core.stats import metrics as M
from study_2_2_views.monitor import PROMPTS, load_config, system_prompt
from study_2_2_views.replication import UNDETERMINED, _rule

VIEWS = ("V1", "V2", "V3", "V4")
B, SEED = 2000, 20261023
PREREG = (Path("configs/prereg_replication.md"), "d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9")
AMENDMENT = (Path("configs/prereg_replication_amendment1.md"),
             "778cf66b03bdea1f27a121aed59962ae5f95ea2e21c6f9fd3902b08f8bc7cbf7")
FROZEN = (Path("configs/frozen/monitor_frozen.json"), "ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f")
GRANITE_MANIFEST_SHA256 = "d6b38e3f2d1c951edf0aadfdc5023077597dcf34aa7efa735f9f1efbf3dfac40"
MONITORS = {  # name: (prompt name, expected digest)
    "llama": ("monitor_v3_pairs_ctx16k", "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"),
    "granite": ("monitor_v3_pairs_ctx16k_granite", "fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7"),
}

G1 = _rule(0.5, {"above": "confirmed", "includes": "not confirmed", "below": "not confirmed"})
G2 = _rule(0.5, {"includes": "confirmed", "above": "not confirmed", "below": "not confirmed (below chance)"})
G4 = _rule(0.0, {"includes": "confirmed", "above": "not confirmed", "below": "not confirmed"})


class RefusedError(RuntimeError):
    """A precondition failed; nothing is computed."""


# --------------------------------------------------------------------------- preconditions

def check_committed(rel: Path, expected: str, git, repo_root: Path = REPO_ROOT) -> str:
    """The file must equal its committed blob (LF) and have the recorded LF sha256."""
    disk = read_text_lf(Path(repo_root) / rel)
    try:
        blob = git(["show", f"HEAD:{rel.as_posix()}"], repo_root).decode("utf-8").replace("\r\n", "\n")
    except Exception as e:                                           # not committed, or no git
        raise RefusedError(f"cannot read the committed blob of {rel}: {e}")
    if disk != blob:
        raise RefusedError(f"{rel} differs from its committed blob")
    got = text_file_sha256(Path(repo_root) / rel)
    if got != expected:
        raise RefusedError(f"{rel} sha256 {got[:12]}... != recorded {expected[:12]}...")
    return got


def check_configs(repo_root: Path = REPO_ROOT) -> dict:
    """Frozen llama file + its manifest, granite manifest: hashes as recorded. Returns {monitor: MonitorConfig}."""
    frozen_path = Path(repo_root) / FROZEN[0]
    if text_file_sha256(frozen_path) != FROZEN[1]:
        raise RefusedError(f"frozen monitor file sha256 != {FROZEN[1][:12]}...")
    fz = json.loads(read_text_lf(frozen_path))
    cfgs = {m: load_config(manifest=PROMPTS[p]) for m, (p, _) in MONITORS.items()}
    if text_file_sha256(Path(repo_root) / fz["format_manifest"]) != fz["format_manifest_file_sha256"]:
        raise RefusedError("llama manifest differs from the frozen file's record")
    if fz["model_digest"] != MONITORS["llama"][1] or fz["format_choice"] != MONITORS["llama"][0]:
        raise RefusedError("frozen file does not name the expected llama prompt / digest")
    gpath = Path(repo_root) / "configs" / "monitor" / PROMPTS[MONITORS["granite"][0]]
    if text_file_sha256(gpath) != GRANITE_MANIFEST_SHA256:
        raise RefusedError(f"granite manifest sha256 != {GRANITE_MANIFEST_SHA256[:12]}... (report 15C)")
    if json.loads(read_text_lf(gpath)).get("model_digest") != MONITORS["granite"][1]:
        raise RefusedError("granite manifest digest differs")
    return cfgs


def load_lines(path: Path, monitor: str, cfg, labels: Mapping, original: set) -> dict:
    """{(game, view): line} for one monitor, after every line-level refusal check."""
    prompt, digest = MONITORS[monitor]
    expected_sys = {v: sha256_of(system_prompt(cfg, v)) for v in VIEWS}
    out = {}
    for raw in read_text_lf(path).splitlines():
        if not raw.strip():
            continue
        d = json.loads(raw)
        g, v = d["game_id"], d["view"]
        if v not in VIEWS:
            raise RefusedError(f"{monitor}: view {v} is not one of V1-V4")
        if d.get("sample_idx", 0) != 0:
            raise RefusedError(f"{monitor}: sample_idx {d.get('sample_idx')} (only sample 0 is analysed)")
        if d.get("prompt_version") != prompt or d.get("model") != cfg.model or d.get("digest") != digest:
            raise RefusedError(f"{monitor}: line {g}/{v} is not {prompt} / {cfg.model} / {digest[:12]}...")
        if d.get("prompt_sha256") != expected_sys[v]:
            raise RefusedError(f"{monitor}: line {g}/{v} system prompt differs from the committed manifest")
        if g in original:
            raise RefusedError(f"{monitor}: {g} is an ORIGINAL dataset game")
        if g not in labels:
            raise RefusedError(f"{monitor}: {g} is not in the replication labels file")
        if (g, v) in out:
            raise RefusedError(f"{monitor}: duplicate line {g}/{v}")
        out[(g, v)] = d
    return out


def load_quality(path: Path) -> set:
    doc = json.loads(read_text_lf(path))
    if not isinstance(doc, dict) or not isinstance(doc.get("quality_fail"), list):
        raise RefusedError(f'{path}: needs {{"quality_fail": [game ids]}} (empty list if none)')
    return set(doc["quality_fail"])


# --------------------------------------------------------------------------- statistics

def _r(x):
    return None if x is None else round(float(x), 4)


def _ci(res) -> dict:
    return {"estimate": _r(res.get("estimate")), "ci_low": _r(res.get("ci_low")), "ci_high": _r(res.get("ci_high")),
            "b_na": res.get("b_na")}


def _score(lines: Mapping, g: str, v: str) -> Optional[float]:
    d = lines.get((g, v))
    return None if d is None else d.get("score")


def common_games(games: Sequence[str], arms: Sequence[tuple[Mapping, str]], labels, types=None) -> tuple[list, int]:
    pool = [g for g in games if types is None or labels[g]["type"] in types]
    keep = [g for g in pool if all(_score(lines, g, v) is not None for lines, v in arms)]
    return keep, len(pool) - len(keep)


def auroc(lines, view, games, labels, b=B, seed=SEED, types=None) -> dict:
    gs, dropped = common_games(games, [(lines, view)], labels, types)
    y, t = [labels[g]["y"] for g in gs], [labels[g]["type"] for g in gs]
    res = (M.bootstrap_auroc([_score(lines, g, view) for g in gs], y, t, b, seed) if len(set(y)) == 2
           else {"estimate": None, "ci_low": None, "ci_high": None, "b_na": None})
    return {"n": len(gs), "dropped": dropped, **_ci(res)}


def paired_diff(arm_a: tuple[Mapping, str], arm_b: tuple[Mapping, str], gs: Sequence[str], labels,
                b=B, seed=SEED) -> dict:
    """AUROC(a) - AUROC(b) on the SAME games and the SAME resample indices (stratified by type)."""
    y, t = [labels[g]["y"] for g in gs], [labels[g]["type"] for g in gs]
    if len(set(y)) < 2:
        return {"n": len(gs), "estimate": None, "ci_low": None, "ci_high": None, "b_na": None}
    res = M.paired_auroc_diff([_score(arm_a[0], g, arm_a[1]) for g in gs], [_score(arm_b[0], g, arm_b[1]) for g in gs],
                              y, t, b, seed)
    return {"n": len(gs), **_ci(res)}


def verdict_g3(d_llama: Mapping, d_granite: Mapping) -> str:
    """Opposite signs of the two point estimates AND at least one of the two CIs excludes 0."""
    vals = [d_llama.get(k) for k in ("estimate", "ci_low", "ci_high")] + \
           [d_granite.get(k) for k in ("estimate", "ci_low", "ci_high")]
    if any(x is None for x in vals):
        return UNDETERMINED
    opposite = d_llama["estimate"] * d_granite["estimate"] < 0
    excludes = any(d["ci_low"] > 0 or d["ci_high"] < 0 for d in (d_llama, d_granite))
    return "confirmed" if opposite and excludes else "not confirmed"


def hypotheses(games, llama: Mapping, granite: Mapping, labels, b=B, seed=SEED) -> dict:
    out = {}
    g1 = auroc(granite, "V2", games, labels, b, seed)
    out["G1"] = {"test": "AUROC_granite(V2)", **g1, "verdict": G1(g1)}
    g2 = auroc(granite, "V4", games, labels, b, seed)
    out["G2"] = {"test": "AUROC_granite(V4)", **g2, "verdict": G2(g2)}
    gs, dropped = common_games(games, [(llama, "V4"), (llama, "V2"), (granite, "V4"), (granite, "V2")], labels)
    dl = paired_diff((llama, "V4"), (llama, "V2"), gs, labels, b, seed)
    dg = paired_diff((granite, "V4"), (granite, "V2"), gs, labels, b, seed)
    out["G3"] = {"test": "D_m = AUROC_m(V4) - AUROC_m(V2), m = llama, granite (common games, same indices)",
                 "n": len(gs), "dropped": dropped, "D_llama": dl, "D_granite": dg, "verdict": verdict_g3(dl, dg)}
    gs, dropped = common_games(games, [(granite, "V3"), (llama, "V3")], labels)
    d4 = paired_diff((granite, "V3"), (llama, "V3"), gs, labels, b, seed)
    out["G4"] = {"test": "AUROC_granite(V3) - AUROC_llama(V3), paired across monitors", **d4, "dropped": dropped,
                 "verdict": G4(d4), "note": "confirmed = no detected difference at this n, not equivalence"}
    return out


# --------------------------------------------------------------------------- descriptive (amendment §3)

def descriptive(games, lines: Mapping, labels, b=B, seed=SEED) -> dict:
    out = {}
    t1 = [g for g in games if labels[g]["type"] == 1]
    for v in VIEWS:
        present = [lines[(g, v)] for g in games if (g, v) in lines]
        ok = [d for d in present if d.get("score") is not None and d.get("pair_scores")]
        row = {"lines": len(present), "absent": len(games) - len(present),
               "missing_score": sum(d.get("score") is None for d in present),
               "parse_fail": sum(not d.get("parse_ok", True) for d in present),
               "truncation_suspect": sum(bool(d.get("truncation_suspect")) for d in present),
               "auroc": auroc(lines, v, games, labels, b, seed)}
        row["per_type_auroc"] = {f"T1_vs_T{'4b' if t == 4 else t}": auroc(lines, v, games, labels, b, seed, (1, t))
                                 for t in (2, 3, 4)}
        row["mean_score_by_type"] = {("T4b" if t == 4 else f"T{t}"): _r(statistics.mean(s)) if s else None
                                     for t in (1, 2, 3, 4)
                                     for s in [[d["score"] for d in ok if labels[d["game_id"]]["type"] == t]]}
        if ok:
            ps = [d["pair_scores"] for d in ok]
            gs = [d["score"] for d in ok]
            lpm = sum(p["T-Z"] == max(p.values()) for p in ps)
            row["last_position_max"] = {"k": lpm, "n": len(ps), "share": _r(lpm / len(ps)),
                                        "no_bias_expectation": _r(statistics.mean(
                                            sum(x == max(p.values()) for x in p.values()) / len(p) for p in ps)),
                                        "named_T_Z": sum((d.get("suspected_pair") or []) == ["T", "Z"] for d in ok)}
            row["scores"] = {"distinct_game_scores": sorted(set(gs)), "min": min(gs), "max": max(gs),
                             "sd": _r(statistics.pstdev(gs)), "share_at_view_max": _r(sum(s == max(gs) for s in gs) / len(gs)),
                             "share_0": _r(sum(s == 0 for s in gs) / len(gs)),
                             "share_all_pairs_equal": _r(sum(len(set(p.values())) == 1 for p in ps) / len(ps))}
        named = [(lines.get((g, v)) or {}).get("suspected_pair") or [] for g in t1
                 if (lines.get((g, v)) or {}).get("score") is not None]
        focal = [labels[g]["focal"] for g in t1 if (lines.get((g, v)) or {}).get("score") is not None]
        row["top1"] = M.top1_pair_accuracy(named, focal)
        out[v] = row
    return out
