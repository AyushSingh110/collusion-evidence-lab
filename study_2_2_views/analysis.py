"""Study 2.2 analysis tables (report 00 §10): RQ1-RQ8 from monitor.jsonl + labels + split.

Two steps, so nothing on test is ever tuned:
  1. dev:  per-view AUROC (+CI), the balanced-accuracy threshold chosen on dev, the dev choices (best single view
           among V1/V2 for RQ2, best LLM view among V1-V5 for RQ7). Writes a frozen-choices JSON; its sha256 goes
           into the DEVLOG before any test run.
  2. test: REFUSES unless that frozen JSON is given AND its sha256 matches AND the monitor prompt version matches.
           Uses the frozen thresholds and choices as they are (nothing refit on test).
Unit of analysis = game. Failed monitor outputs (score None) are excluded per view and counted; paired comparisons
use the games scored in both arms. CIs: stratified bootstrap by episode type, whole games, B = 2000, seed 20261023.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from core.config import read_text_lf
from core.stats import metrics as M

VIEWS_ALL = ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled")
LLM_VIEWS = ("V1", "V2", "V3", "V4", "V5")
SINGLE_VIEWS = ("V1", "V2")
PAIRED = [("RQ2", "V3", "BEST_SINGLE"), ("RQ4", "V3", "C-mismatch"), ("RQ5", "V4", "V3"), ("RQ5", "V4", "C-length"),
          ("RQ6", "V5", "V3")]
PRIMARY = {"RQ2", "RQ5"}
CODE_SIGNAL = "Dep"            # pre-registered best code signal for RQ7 (report 00 §10)


class FrozenError(RuntimeError):
    """Test numbers requested without a matching frozen dev configuration."""


# --------------------------------------------------------------------------- loading

def load_monitor(path: Path, sample_idx: int = 0) -> tuple[dict, dict, set]:
    """(scores[(game, view)] -> score or None, pairs[(game, view)] -> suspected pair, prompt versions)."""
    scores, pairs, versions = {}, {}, set()
    for line in read_text_lf(path).splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("sample_idx", 0) != sample_idx:
            continue
        key = (d["game_id"], d["view"])
        if key in scores:
            raise ValueError(f"duplicate monitor line for {key}")
        scores[key] = d.get("score")
        pairs[key] = d.get("suspected_pair") or []
        versions.add(d.get("prompt_version"))
    return scores, pairs, versions


def load_labels(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["game_id"]: {"type": int(r["episode_type"]), "y": int(r["collusion"]),
                               "focal": r["focal_pair"].split("|")} for r in csv.DictReader(f)}


def load_split(path: Path) -> dict[str, list[str]]:
    d = json.loads(read_text_lf(path))
    return {"dev": list(d["dev"]), "test": list(d["test"])}


def load_signals(path: Path) -> dict[str, dict]:
    """Game-level code signals (core.evidence.signals.game_signals rows as CSV): game_id + columns."""
    def parse(k, v):
        if v in ("", "None", "NA") or v is None:
            return None
        if k == "game_id" or k.endswith("_pair"):
            return v
        try:
            return float(v)
        except ValueError:
            return v            # e.g. a flag column: kept as text, never used as a score
    with open(path, encoding="utf-8", newline="") as f:
        return {r["game_id"]: {k: parse(k, v) for k, v in r.items()} for r in csv.DictReader(f)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(read_text_lf(path).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- helpers

def _arm(scores: Mapping, view: str, games: Sequence[str], labels: Mapping) -> tuple[list, list, list, list, int]:
    g, s, y, t, n_fail = [], [], [], [], 0
    for gid in games:
        if (gid, view) not in scores:
            continue
        v = scores[(gid, view)]
        if v is None:
            n_fail += 1
            continue
        g.append(gid)
        s.append(v)
        y.append(labels[gid]["y"])
        t.append(labels[gid]["type"])
    return g, s, y, t, n_fail


def _fmt(v: Any) -> str:
    if v is None:
        return "NA"
    return f"{v:.3f}" if isinstance(v, float) else str(v)


# --------------------------------------------------------------------------- dev step

def dev_choices(scores: Mapping, labels: Mapping, dev: Sequence[str], views: Sequence[str] = VIEWS_ALL) -> dict:
    """Thresholds (max balanced accuracy, ties -> higher) and view choices, ALL on dev."""
    per_view, auc = {}, {}
    for v in views:
        _, s, y, _, n_fail = _arm(scores, v, dev, labels)
        if not s:
            continue
        bt = M.best_threshold(s, y)
        auc[v] = M.auroc(s, y)
        per_view[v] = {"threshold": None if bt is None else bt["threshold"], "dev_auroc": auc[v], "dev_n": len(s),
                       "dev_failed": n_fail}

    def best(cands):
        c = [v for v in cands if auc.get(v) is not None]
        return max(c, key=lambda v: (auc[v], -cands.index(v))) if c else None   # tie -> the earlier view in the list
    return {"per_view": per_view, "best_single_view": best(list(SINGLE_VIEWS)), "best_llm_view": best(list(LLM_VIEWS)),
            "rules": {"threshold": "max balanced accuracy on dev, ties -> higher threshold",
                      "best_single_view": "higher dev AUROC among V1, V2 (tie -> V1)",
                      "best_llm_view": "higher dev AUROC among V1-V5 (tie -> earlier view)",
                      "code_signal": CODE_SIGNAL}}


def write_frozen(choices: dict, prompt_versions: set, monitor_manifest_sha256: Optional[str], path: Path) -> str:
    doc = {"kind": "study22_frozen_choices", "prompt_versions": sorted(v for v in prompt_versions if v),
           "monitor_manifest_sha256": monitor_manifest_sha256, **choices}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return file_sha256(path)


def check_frozen(frozen_path: Optional[Path], expected_sha256: Optional[str], prompt_versions: set) -> dict:
    """Refuse test reporting unless the frozen dev file exists, its sha256 matches and the prompt version matches."""
    if frozen_path is None or expected_sha256 is None:
        raise FrozenError("test numbers need --frozen <file> AND --frozen-sha256 <hex> recorded before the test run")
    got = file_sha256(Path(frozen_path))
    if got != expected_sha256:
        raise FrozenError(f"frozen file sha256 {got[:12]}... != expected {expected_sha256[:12]}...")
    doc = json.loads(read_text_lf(Path(frozen_path)))
    if doc.get("kind") != "study22_frozen_choices":
        raise FrozenError("not a study22 frozen-choices file")
    pv = sorted(v for v in prompt_versions if v)
    if pv != doc.get("prompt_versions"):
        raise FrozenError(f"monitor prompt version {pv} != frozen {doc.get('prompt_versions')}")
    return doc


# --------------------------------------------------------------------------- tables

def per_view_table(scores, labels, games, choices, b=M.DEFAULT_B, seed=M.DEFAULT_SEED) -> list[dict]:
    rows = []
    for v in VIEWS_ALL:
        g, s, y, t, n_fail = _arm(scores, v, games, labels)
        if not g and not n_fail:
            continue
        ci = M.bootstrap_auroc(s, y, t, b, seed) if s else {"estimate": None, "ci_low": None, "ci_high": None}
        thr = choices["per_view"].get(v, {}).get("threshold")
        m = M.metrics_at_threshold(s, y, thr) if s and thr is not None else {}
        rows.append({"view": v, "n": len(s), "failed": n_fail, "n_pos": sum(y), "n_neg": len(y) - sum(y),
                     "auroc": ci["estimate"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"], "threshold": thr,
                     "accuracy": m.get("accuracy"), "tpr": m.get("tpr"), "fpr": m.get("fpr"),
                     "tp": m.get("tp"), "fp": m.get("fp"), "tn": m.get("tn"), "fn": m.get("fn")})
    return rows


def paired_table(scores, labels, games, choices, signals=None, b=M.DEFAULT_B, seed=M.DEFAULT_SEED) -> list[dict]:
    rows = []
    comps = [(rq, a, choices["best_single_view"] if bb == "BEST_SINGLE" else bb) for rq, a, bb in PAIRED]
    for rq, a, bb in comps:
        if bb is None:
            continue
        common = [gid for gid in games if scores.get((gid, a)) is not None and scores.get((gid, bb)) is not None]
        rows.append(_paired_row(rq, a, bb, [scores[(g, a)] for g in common], [scores[(g, bb)] for g in common],
                                common, labels, b, seed))
    best_llm = choices.get("best_llm_view")
    if signals is not None and best_llm is not None:          # RQ7: code signal vs best LLM view
        common = [gid for gid in games if signals.get(gid, {}).get(CODE_SIGNAL) is not None
                  and scores.get((gid, best_llm)) is not None]
        rows.append(_paired_row("RQ7", CODE_SIGNAL, best_llm, [signals[g][CODE_SIGNAL] for g in common],
                                [scores[(g, best_llm)] for g in common], common, labels, b, seed))
    return rows


def _paired_row(rq, a, b_name, sa, sb, games, labels, b, seed) -> dict:
    y = [labels[g]["y"] for g in games]
    t = [labels[g]["type"] for g in games]
    d = M.paired_auroc_diff(sa, sb, y, t, b, seed) if games else {"estimate": None, "ci_low": None, "ci_high": None}
    return {"rq": rq, "primary": rq in PRIMARY, "a": a, "b": b_name, "n": len(games),
            "auroc_a": M.auroc(sa, y) if games else None, "auroc_b": M.auroc(sb, y) if games else None,
            "diff": d["estimate"], "ci_low": d["ci_low"], "ci_high": d["ci_high"]}


def fpr_type_table(scores, labels, games, choices) -> list[dict]:
    rows = []
    for v in VIEWS_ALL:
        thr = choices["per_view"].get(v, {}).get("threshold")
        g, s, y, t, _ = _arm(scores, v, games, labels)
        if not g or thr is None:
            continue
        flags = [int(x >= thr) for x in s]
        rows += [{"view": v, **r} for r in M.fpr_by_type(flags, y, t)]
    return rows


def top1_table(pairs, labels, games, signals=None) -> list[dict]:
    t1 = [g for g in games if labels[g]["type"] == 1]
    rows = []
    for v in LLM_VIEWS:
        have = [g for g in t1 if (g, v) in pairs]
        if have:
            r = M.top1_pair_accuracy([pairs[(g, v)] for g in have], [labels[g]["focal"] for g in have])
            rows.append({"source": f"monitor {v}", **r})
    if signals is not None:
        have = [g for g in t1 if g in signals]
        if have:
            pred = [(signals[g].get(f"{CODE_SIGNAL}_pair") or "").split("-") if signals[g].get(f"{CODE_SIGNAL}_pair")
                    else [] for g in have]
            rows.append({"source": f"evidence argmax ({CODE_SIGNAL})",
                         **M.top1_pair_accuracy(pred, [labels[g]["focal"] for g in have])})
    return rows


# --------------------------------------------------------------------------- report

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        if not rows:
            f.write("")
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build(scores, pairs, labels, split_games, choices, split_name, out_dir: Path, signals=None,
          b=M.DEFAULT_B, seed=M.DEFAULT_SEED, note: str = "") -> str:
    tabs = {"rq1_per_view": per_view_table(scores, labels, split_games, choices, b, seed),
            "rq2_rq4_rq5_rq6_rq7_paired": paired_table(scores, labels, split_games, choices, signals, b, seed),
            "rq3_fpr_by_type": fpr_type_table(scores, labels, split_games, choices),
            "rq8_top1_pair": top1_table(pairs, labels, split_games, signals)}
    for name, rows in tabs.items():
        write_csv(out_dir / f"{name}_{split_name}.csv", rows)
    L = [f"# Study 2.2 analysis — {split_name.upper()} split", "", note, "",
         f"Games in split: {len(split_games)}. Bootstrap: B = {b}, seed {seed}, stratified by episode type, whole games.",
         f"Dev choices: best single view (RQ2) = {choices.get('best_single_view')}; best LLM view (RQ7) = "
         f"{choices.get('best_llm_view')}; code signal = {CODE_SIGNAL}.", "",
         "## RQ1 per view (threshold chosen on dev)", "",
         "| view | n | failed | AUROC | 95% CI | thr | acc | TPR | FPR |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['view']} | {r['n']} | {r['failed']} | {_fmt(r['auroc'])} | [{_fmt(r['ci_low'])}, {_fmt(r['ci_high'])}] | "
          f"{_fmt(r['threshold'])} | {_fmt(r['accuracy'])} | {_fmt(r['tpr'])} | {_fmt(r['fpr'])} |"
          for r in tabs["rq1_per_view"]]
    L += ["", "## Paired AUROC differences (same resample indices; primary = RQ2, RQ5)", "",
          "| RQ | primary | a | b | n | AUROC a | AUROC b | a − b | 95% CI |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['rq']} | {r['primary']} | {r['a']} | {r['b']} | {r['n']} | {_fmt(r['auroc_a'])} | {_fmt(r['auroc_b'])} | "
          f"{_fmt(r['diff'])} | [{_fmt(r['ci_low'])}, {_fmt(r['ci_high'])}] |" for r in tabs["rq2_rq4_rq5_rq6_rq7_paired"]]
    L += ["", "## RQ3 FPR per negative type (at the dev threshold)", "",
          "| view | type | n | FP | FPR | upper 95% (rule of 3, if FP = 0) |", "|---|---|---|---|---|---|"]
    L += [f"| {r['view']} | {r['type']} | {r['n']} | {r['fp']} | {_fmt(r['fpr'])} | {_fmt(r['upper95_rule_of_three'])} |"
          for r in tabs["rq3_fpr_by_type"]]
    L += ["", "## RQ8 top-1 pair accuracy (Type 1 games)", "", "| source | n | correct | no pair | accuracy |",
          "|---|---|---|---|---|"]
    L += [f"| {r['source']} | {r['n']} | {r['correct']} | {r['no_pair']} | {_fmt(r['accuracy'])} |"
          for r in tabs["rq8_top1_pair"]]
    L += ["", "No multiple-comparison correction (report 00 §10); everything except RQ2 and RQ5 is exploratory. "
              "Small pilot samples: word claims as 'in this pilot'."]
    text = "\n".join(L) + "\n"
    (out_dir / f"summary_{split_name}.md").write_text(text, encoding="utf-8", newline="\n")
    return text
