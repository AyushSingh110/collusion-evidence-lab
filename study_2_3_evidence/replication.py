"""Study 2.3 replication (configs/prereg_replication.md §4): apply the FROZEN rules to a new set of games and compute
E1, E2, E3, E3b, E4 with their pre-registered decision rules. Never refits anything.

Additive (task 19C): rules.py, judge.py and scripts/analyse_23.py are unchanged. The frozen rules file is applied with
rules.apply_frozen to ANY set of game ids (no split), with the frozen honest baseline (original dev Type 2 games) for
the code signals. Refuses unless the frozen file's sha256 matches and the replication prereg equals its committed blob.

Statistics (prereg §3): 95% stratified bootstrap by episode type (whole games), B = 2000, seed 20261023; paired
differences share the resample indices. Games are ordered by id, so the resamples are reproducible. A game whose
score is NA is left out of that score's AUROC (paired: of both) and counted.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from core.config import REPO_ROOT, load_json, read_text_lf
from core.evidence.signals import HonestBaseline, game_signals, pair_signal_table
from core.stats import metrics as M
from study_2_3_evidence import rules as R

PREREG = Path("configs/prereg_replication.md")
PREREG_SHA256 = "d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9"
FROZEN = Path("configs/frozen/rules_frozen.json")
FROZEN_SHA256 = "ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5"
BEST_SINGLE, BEST_COMBINED = "R2", "R6"           # prereg §4 E3 (from the frozen dev report; same as task 17C)
SCORE = {"R1": "score", "R2": "score", "R3": "score", "R6": "points", "R7": "prob"}
# 17C exploratory plus-factor rule, thresholds fitted on the original DEV games and recorded in the DEVLOG
# ("Task 17C (part 0)") before the 17C test run; prereg §4 "Secondary".
PLUS_FACTOR = {"capture": 0.625, "C_kw": 0.7375}
TYPE_NAME = {1: "T1", 2: "T2", 3: "T3", 4: "T4b"}


class ReplicationError(RuntimeError):
    """A precondition of the replication analysis failed (nothing is computed)."""


# --------------------------------------------------------------------------- preconditions

def git_blob(rel_path: Path, rev: str = "HEAD") -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{Path(rel_path).as_posix()}"], cwd=REPO_ROOT, capture_output=True,
                          check=True).stdout


def check_prereg(path: Path = REPO_ROOT / PREREG, expected_sha256: str = PREREG_SHA256,
                 blob: Optional[Callable[[], bytes]] = None) -> str:
    """Refuse unless the prereg exists, has the expected LF sha256 and equals its committed blob (LF-normalised)."""
    path = Path(path)
    if not path.exists():
        raise ReplicationError(f"prereg {path} does not exist")
    got = R.file_sha256(path)
    if got != expected_sha256:
        raise ReplicationError(f"prereg sha256 {got[:12]}... != expected {expected_sha256[:12]}...")
    try:
        committed = (blob or (lambda: git_blob(PREREG)))()
    except (OSError, subprocess.CalledProcessError) as e:
        raise ReplicationError(f"prereg is not committed ({e})") from e
    if committed.decode("utf-8").replace("\r\n", "\n") != read_text_lf(path):
        raise ReplicationError("prereg working copy differs from its committed blob")
    return got


def frozen_baseline(doc: Mapping) -> HonestBaseline:
    """The ORIGINAL honest baseline stored in the frozen rules file (never refit)."""
    return HonestBaseline(**doc["honest_baseline"])


# --------------------------------------------------------------------------- tables + decisions

def build_games(clean: Mapping[str, Mapping], judge: Mapping[str, Mapping], base: HonestBaseline) -> dict:
    """{game_id: pair rows with C_judge}. `clean` = {game_id: CleanGame dict}; a missing or rejected judge line
    gives C_judge None for every pair (flagged), exactly as scripts/analyse_23.build_tables."""
    games = {}
    for g in sorted(clean):
        rows = pair_signal_table(clean[g], base)
        line = judge.get(g)
        ps = line.get("pair_scores") if line else None
        for r in rows:
            r["C_judge"] = None if ps is None else ps[r["pair"]]
            r["C_judge_flag"] = None if ps is not None else ("no_judge_line" if line is None else "judge_rejected")
        games[g] = rows
    return games


def apply(frozen_path: Path, frozen_sha256: str, games: Mapping[str, Sequence[Mapping]], ids: Sequence[str],
          judge_prompt_version: Optional[str]) -> tuple[dict, dict]:
    """(frozen doc, decisions) — rules.apply_frozen on any ids; refuses on a sha256 mismatch."""
    doc = R.load_frozen(frozen_path, frozen_sha256)
    overlap = sorted(set(ids) & set(doc["dev_ids"]))
    if overlap:
        raise ReplicationError(f"{len(overlap)} game ids are frozen DEV games (rules were fitted on them): {overlap[:3]}")
    return doc, R.apply_frozen(frozen_path, frozen_sha256, games, ids, judge_prompt_version=judge_prompt_version)


# --------------------------------------------------------------------------- decision rules (prereg §3/§4 wording)

def _lo_hi(ci: Mapping) -> tuple[float, float]:
    if ci is None or ci.get("ci_low") is None or ci.get("ci_high") is None:
        raise ReplicationError("no CI (too few informative games)")
    return ci["ci_low"], ci["ci_high"]


def verdict_e1(ci: Mapping) -> str:
    lo, _ = _lo_hi(ci)
    return "confirmed" if lo > 0.5 else "not confirmed"


def verdict_e2(ci: Mapping) -> str:
    lo, hi = _lo_hi(ci)
    if hi < 0.5:
        return "confirmed (below chance)"
    return "not confirmed" if lo > 0.5 else "confirmed"


def verdict_diff(ci: Mapping) -> str:
    lo, hi = _lo_hi(ci)
    if lo > 0:
        return "replicated"
    return "reversed" if hi < 0 else "not replicated"


# --------------------------------------------------------------------------- statistics

def _auroc_stat(scores: Sequence[Optional[float]], y: Sequence[int]):
    def stat(idx):
        keep = [i for i in idx if scores[i] is not None]
        return M.auroc([scores[i] for i in keep], [y[i] for i in keep]) if keep else None
    return stat


def _ci(d: Mapping) -> dict:
    return {k: d[k] for k in ("estimate", "ci_low", "ci_high", "b_na")}


def per_type(flags: Sequence[int], types: Sequence[int]) -> dict:
    out = {}
    for t in sorted(set(types)):
        f = [fl for fl, tt in zip(flags, types) if tt == t]
        k = sum(f)
        out[TYPE_NAME.get(t, str(t))] = {"k": k, "n": len(f), "rate": k / len(f) if f else None,
                                         "upper95_rule_of_three": M.rule_of_three_upper(len(f)) if k == 0 else None}
    return out


def rule_scores(decisions: Mapping[str, Mapping], ids: Sequence[str], rule: str) -> list[Optional[float]]:
    return [decisions[g][rule][SCORE[rule]] for g in ids]


def plus_factor_flags(games: Mapping[str, Sequence[Mapping]], ids: Sequence[str]) -> list[int]:
    gs = {g: game_signals(games[g]) for g in ids}
    return [int(R._ge(gs[g]["capture"], PLUS_FACTOR["capture"]) and R._ge(gs[g]["C_kw"], PLUS_FACTOR["C_kw"]))
            for g in ids]


def analyse_set(games: Mapping[str, Sequence[Mapping]], decisions: Mapping[str, Mapping], labels: Mapping[str, object],
                ids: Sequence[str], b: int = M.DEFAULT_B, seed: int = M.DEFAULT_SEED) -> dict:
    """E1, E2, E3, E3b, E4 (+ secondary plus-factor rule) on `ids`. labels[g] needs .collusion and .episode_type."""
    ids = sorted(ids)
    y = [labels[g].collusion for g in ids]
    types = [labels[g].episode_type for g in ids]
    if not any(y) or all(y):
        raise ReplicationError("both classes are needed")
    sc = {r: rule_scores(decisions, ids, r) for r in SCORE}
    out = {"n": len(ids), "n_pos": sum(y), "n_by_type": {TYPE_NAME.get(t, str(t)): types.count(t) for t in sorted(set(types))},
           "n_score_na": {r: sum(v is None for v in s) for r, s in sc.items()}, "auroc": {}}
    for r in SCORE:
        out["auroc"][r] = _ci(M.bootstrap_ci(_auroc_stat(sc[r], y), types, b, seed))
    e1, e2 = out["auroc"]["R2"], out["auroc"]["R1"]
    out["E1"] = {"test": "AUROC(R2 gain = game-level G_others)", **e1, "verdict": verdict_e1(e1)}
    out["E2"] = {"test": "AUROC(R1 judge = game-level C_judge)", **e2, "verdict": verdict_e2(e2)}
    for name, combined in (("E3", BEST_COMBINED), ("E3b", "R7")):
        both = [None if a is None or c is None else (a, c) for a, c in zip(sc[combined], sc[BEST_SINGLE])]
        sa = [None if p is None else p[0] for p in both]
        sb = [None if p is None else p[1] for p in both]
        d = _ci(M.paired_bootstrap_diff(_auroc_stat(sa, y), _auroc_stat(sb, y), types, b, seed))
        out[name] = {"test": f"AUROC({combined}) - AUROC({BEST_SINGLE}), paired", "n": sum(p is not None for p in both),
                     **d, "verdict": verdict_diff(d)}
    out["E3b"]["status"] = "secondary"
    out["E4"] = {"status": "descriptive", "R2": per_type([decisions[g]["R2"]["flag"] for g in ids], types),
                 BEST_COMBINED: per_type([decisions[g][BEST_COMBINED]["flag"] for g in ids], types)}
    out["flags"] = {r: {**R.binary_metrics([decisions[g][r]["flag"] for g in ids], y),
                        "per_type": per_type([decisions[g][r]["flag"] for g in ids], types)} for r in R.RULES}
    pf = plus_factor_flags(games, ids)
    out["plus_factor_secondary"] = {"status": "secondary (exploratory rule of task 17C, dev thresholds)",
                                    "thresholds": PLUS_FACTOR, **R.binary_metrics(pf, y), "per_type": per_type(pf, types)}
    return out


def read_quality_fail(path: Optional[Path]) -> Optional[list[str]]:
    """Quality file: JSON list of game ids, or {"quality_fail": [...]}. None if no file was given."""
    if path is None:
        return None
    d = load_json(Path(path))
    ids = d["quality_fail"] if isinstance(d, dict) else d
    if not isinstance(ids, list) or not all(isinstance(g, str) for g in ids):
        raise ReplicationError("quality file must be a JSON list of game ids or {\"quality_fail\": [...]}")
    return sorted(ids)


def analyse_replication(games, decisions, labels, ids, quality_fail: Optional[Sequence[str]], **kw) -> dict:
    """Primary = all `ids`; sensitivity = without the quality-fail games (only if a quality file was given)."""
    ids = sorted(ids)
    out = {"primary": analyse_set(games, decisions, labels, ids, **kw)}
    if quality_fail is None:
        out["sensitivity"] = {"status": "not run: no quality file given"}
    else:
        unknown = sorted(set(quality_fail) - set(ids))
        if unknown:
            raise ReplicationError(f"quality-fail ids not in the set: {unknown[:3]}")
        keep = [g for g in ids if g not in set(quality_fail)]
        out["sensitivity"] = ({"status": "identical to primary (no quality-fail game)", "quality_fail": []}
                              if len(keep) == len(ids) else
                              {"quality_fail": sorted(quality_fail), **analyse_set(games, decisions, labels, keep, **kw)})
    return out
