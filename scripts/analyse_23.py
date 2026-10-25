"""Study 2.3: pair signal table, judge stability, fit R1-R7 on DEV and freeze; or apply the frozen rules to test.

  # fit (dev only) -> study_2_3_evidence/results/ + configs/frozen/rules_frozen.json (sha256 printed)
  conda run -n collusion-lab python scripts/analyse_23.py --mode fit --judge runs/judge_v1/outputs/judge.jsonl
  # test: REFUSES unless --frozen and --frozen-sha256 match
  conda run -n collusion-lab python scripts/analyse_23.py --mode test --judge ... --frozen configs/frozen/rules_frozen.json --frozen-sha256 <hex>

The honest baseline (G_honest, Harm) is fitted on DEV Type 2 games only. The pair table covers every game (signals
are computed per game; nothing is fitted on test). Labels come only from data/labels.csv (Rule G).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, canonical_json, load_json, sha256_of  # noqa: E402
from core.evidence.signals import SIGNALS, fit_honest_baseline, game_signals, pair_signal_table  # noqa: E402
from core.labels import read_labels  # noqa: E402
from core.stats import metrics as M  # noqa: E402
from study_2_3_evidence import rules as R  # noqa: E402
from study_2_3_evidence.judge import load_config, load_judge  # noqa: E402

RESULTS = REPO_ROOT / "study_2_3_evidence" / "results"
FROZEN = REPO_ROOT / "configs" / "frozen" / "rules_frozen.json"


def file_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_tables(clean_dir: Path, labels: dict, dev: list[str], judge: dict) -> tuple[dict, object]:
    dev_t2 = [load_json(clean_dir / f"{g}.json") for g in dev if labels[g].episode_type == 2]
    base = fit_honest_baseline(dev_t2)
    games = {}
    for g in sorted(labels):
        rows = pair_signal_table(load_json(clean_dir / f"{g}.json"), base)
        line = judge.get(g)
        ps = line.get("pair_scores") if line else None
        for r in rows:
            r["C_judge"] = None if ps is None else ps[r["pair"]]
            r["C_judge_flag"] = None if ps is not None else ("no_judge_line" if line is None else "judge_rejected")
        games[g] = rows
    return games, base


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def stability(j0: dict, j1: dict, ids: list[str], pair_order) -> dict:
    both = [g for g in ids if j0.get(g, {}).get("pair_scores") and j1.get(g, {}).get("pair_scores")]
    a = [j0[g]["pair_scores"][p] for g in both for p in pair_order]
    b = [j1[g]["pair_scores"][p] for g in both for p in pair_order]
    ga = [j0[g]["score"] for g in both]
    gb = [j1[g]["score"] for g in both]
    return {"n_games_both_ok": len(both), "n_games": len(ids),
            "pair_mean_abs_diff": M.mean_abs_diff(a, b) if both else None,
            "pair_spearman": M.spearman(a, b) if both else None,
            "pair_identical_share": sum(x == y for x, y in zip(a, b)) / len(a) if a else None,
            "game_max_mean_abs_diff": M.mean_abs_diff(ga, gb) if both else None,
            "game_max_spearman": M.spearman(ga, gb) if both else None,
            "top_pair_same": sum(j0[g]["top_pair"] == j1[g]["top_pair"] for g in both)}


def judge_summary(lines: dict, ids: list[str]) -> dict:
    ls = [lines[g] for g in ids if g in lines]
    lat = sorted(x["latency"] for x in ls if x.get("latency") is not None)
    return {"n_lines": len(ls), "n_expected": len(ids), "parse_ok": sum(x["parse_ok"] for x in ls),
            "accepted": sum(x["pair_scores"] is not None for x in ls),
            "truncation_suspect": sum(x["truncation_suspect"] for x in ls),
            "done_reason_length": sum(x.get("done_reason") == "length" for x in ls),
            "latency_median_s": lat[len(lat) // 2] if lat else None,
            "latency_max_s": lat[-1] if lat else None,
            "prompt_eval_max": max((x["prompt_eval_count"] or 0) for x in ls) if ls else None,
            "eval_count_max": max((x["eval_count"] or 0) for x in ls) if ls else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("fit", "test"), required=True)
    ap.add_argument("--clean-dir", type=Path, default=REPO_ROOT / "data" / "clean")
    ap.add_argument("--labels", type=Path, default=REPO_ROOT / "data" / "labels.csv")
    ap.add_argument("--split", type=Path, default=REPO_ROOT / "data" / "split.json")
    ap.add_argument("--judge", type=Path, required=True, help="judge.jsonl (sample_idx 0 is used for C_judge)")
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--frozen-out", type=Path, default=FROZEN)
    ap.add_argument("--frozen", type=Path)
    ap.add_argument("--frozen-sha256")
    a = ap.parse_args(argv)

    labels = {lb.game_id: lb for lb in read_labels(a.labels)}
    split = load_json(a.split)
    dev, test = sorted(split["dev"]), sorted(split["test"])
    if set(dev) | set(test) != set(labels):
        print("REFUSED: split and labels do not cover the same games")
        return 2
    cfg = load_config()
    j0 = load_judge(a.judge, 0)
    pv = {x["prompt_version"] for x in j0.values()}
    if pv != {cfg.prompt_version}:
        print(f"REFUSED: judge prompt versions {pv} != {cfg.prompt_version}")
        return 2

    if a.mode == "test":   # refuse before computing anything on test
        try:
            R.load_frozen(a.frozen, a.frozen_sha256)
        except R.FrozenError as e:
            print(f"REFUSED: {e}")
            return 2

    games, base = build_tables(a.clean_dir, labels, dev, j0)
    y = {g: labels[g].collusion for g in labels}
    types = {g: labels[g].episode_type for g in labels}

    if a.mode == "test":
        dec = R.apply_frozen(a.frozen, a.frozen_sha256, games, test, judge_prompt_version=cfg.prompt_version)
        rows = [{"game_id": g, **{f"{r}_flag": d[r]["flag"] for r in d}, **{f"{r}_pair": d[r]["pair"] for r in d}}
                for g, d in dec.items()]
        write_csv(a.out / "test_decisions.csv", rows)
        print(f"test decisions for {len(rows)} games -> {a.out / 'test_decisions.csv'}")
        return 0

    # ---- fit mode: tables for all games, rules fitted on dev only
    a.out.mkdir(parents=True, exist_ok=True)
    pair_rows = [r for g in sorted(games) for r in games[g]]
    write_csv(a.out / "pair_signals.csv", pair_rows)
    write_csv(a.out / "game_signals.csv", [game_signals(games[g]) | {"C_judge": R.game_max(games[g], "C_judge"),
                                                                     "C_judge_pair": R.argmax_pair(games[g], "C_judge")}
                                           for g in sorted(games)])
    j1 = load_judge(a.judge, 1)
    judge_info = {"all_sample0": judge_summary(j0, dev + test), "dev_sample1": judge_summary(j1, dev),
                  "stability_dev": stability(j0, j1, dev, cfg.pair_order)}

    params = R.fit_rules(games, y, dev)
    abl = R.fit_ablations(games, y, dev, params["plus"])
    rep = R.dev_report(params, abl, games, y, types, dev)
    lines0 = list(j0.values())
    doc = {
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine_id": os.environ.get("COLLUSION_LAB_MACHINE") or None,
        "judge": {"prompt_version": cfg.prompt_version, "manifest_sha256": cfg.manifest_sha256,
                  "template_sha256": cfg.template_sha256, "model": cfg.model,
                  "digest": sorted({x["digest"] for x in lines0}), "num_ctx": cfg.num_ctx,
                  "num_predict": cfg.num_predict, "temperature": cfg.temperature, "sample_idx_used": 0,
                  "judge_jsonl": str(a.judge),
                  "judge_jsonl_sha256": file_sha(a.judge)},
        "labels_sha256": file_sha(a.labels), "split_labels_sha256": split["labels_sha256"],
        "dev_ids": dev, "honest_baseline": asdict(base),
        "dev_pair_table_sha256": sha256_of(canonical_json([r for g in dev for r in games[g]])),
        "families": R.FAMILIES, "plus_percentile": R.PLUS_PERCENTILE, "c_grid": list(R.C_GRID),
        "conventions": "study_2_3_evidence/rules.py module docstring (task 13C)",
        "params": params, "ablations": abl, "dev_report": rep, "judge_dev": judge_info,
    }
    sha = R.write_frozen(doc, a.frozen_out)
    (a.out / "dev_report.json").write_text(json.dumps(R._jsonable({"dev_report": rep, "judge": judge_info,
                                                                   "honest_baseline": asdict(base)}),
                                                      indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(R._jsonable(judge_info), indent=1))
    print(f"honest baseline (dev Type 2): {asdict(base)}")
    for k, v in params["single"].items():
        print(f"  tau {k} ({v['signal']}): {v['threshold']}  n_used {v['n_used']} n_na {v['n_na']}")
    for s, v in params["plus"].items():
        print(f"  plus {s}: {v['threshold']}  (n_neg {v['n_neg_used']})")
    print(f"  R6 k = {params['R6']['k']};  R7 C = {params['R7']['C']}, coef {params['R7']['coef']}, "
          f"intercept {params['R7']['intercept']:.4f}")
    for r, m in rep.items():
        print(f"  dev {r:10s} BA {m['balanced_accuracy']}  TPR {m['tpr']}  FPR {m['fpr']}  ({m['source']})")
    print(f"frozen -> {a.frozen_out}\nsha256 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
