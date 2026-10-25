"""Study 2.3 replication analysis (configs/prereg_replication.md §4): the FROZEN rules on the replication games.

  conda run -n collusion-lab python scripts/analyse_replication_23.py \
      --clean-dir data/replication/clean --labels data/replication/labels.csv \
      --judge runs/judge_v1_replication/outputs/judge.jsonl --quality <quality-fail JSON> \
      [--out runs/replication_23]

Refuses (before computing anything) unless: the replication prereg equals its committed blob with LF sha256
d9d25b58…; the frozen rules file has sha256 ce0b8840…; the judge lines are judge_v1 with the frozen digest; no game
id is a frozen DEV game; every labelled game has a clean file; the output folder holds no earlier result (one
analysis run). The honest baseline is the frozen one (never refit). Missing judge lines are counted, not fatal.
Quality file: JSON list of quality-fail game ids or {"quality_fail": [...]} (sensitivity analysis); without it the
sensitivity analysis is reported as not run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_json  # noqa: E402
from core.labels import read_labels  # noqa: E402
from study_2_3_evidence import replication as REP  # noqa: E402
from study_2_3_evidence import rules as R  # noqa: E402
from study_2_3_evidence.judge import load_judge  # noqa: E402


def file_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clean-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--judge", type=Path, required=True, help="judge.jsonl (sample_idx 0)")
    ap.add_argument("--quality", type=Path, help="quality-fail ids (JSON); omit only if no quality file exists")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "replication_23")
    ap.add_argument("--frozen", type=Path, default=REPO_ROOT / REP.FROZEN)
    ap.add_argument("--frozen-sha256", default=REP.FROZEN_SHA256)
    ap.add_argument("--prereg", type=Path, default=REPO_ROOT / REP.PREREG)
    ap.add_argument("--prereg-sha256", default=REP.PREREG_SHA256)
    a = ap.parse_args(argv)

    try:
        REP.check_prereg(a.prereg, a.prereg_sha256)
        doc = R.load_frozen(a.frozen, a.frozen_sha256)
        if (a.out / "results.json").exists():
            raise REP.ReplicationError(f"{a.out / 'results.json'} exists; the replication is analysed once")
        labels = {lb.game_id: lb for lb in read_labels(a.labels)}
        ids = sorted(labels)
        missing_clean = [g for g in ids if not (a.clean_dir / f"{g}.json").exists()]
        if missing_clean:
            raise REP.ReplicationError(f"{len(missing_clean)} labelled games have no clean file: {missing_clean[:3]}")
        judge = load_judge(a.judge, 0)
        fj = doc["judge"]
        bad = sorted({(x["prompt_version"], x["digest"]) for x in judge.values()}
                     - {(fj["prompt_version"], d) for d in fj["digest"]})
        if bad:
            raise REP.ReplicationError(f"judge lines not from the frozen judge configuration: {bad}")
        extra = sorted(set(judge) - set(ids))
        if extra:
            raise REP.ReplicationError(f"judge file has games outside the labels file: {extra[:3]}")
        quality_fail = REP.read_quality_fail(a.quality)
        clean = {g: load_json(a.clean_dir / f"{g}.json") for g in ids}
        games = REP.build_games(clean, judge, REP.frozen_baseline(doc))
        _, decisions = REP.apply(a.frozen, a.frozen_sha256, games, ids, judge_prompt_version=fj["prompt_version"])
    except (REP.ReplicationError, R.FrozenError) as e:
        print(f"REFUSED: {e}")
        return 2

    res = REP.analyse_replication(games, decisions, labels, ids, quality_fail)
    res["inputs"] = {
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine_id": os.environ.get("COLLUSION_LAB_MACHINE") or None,
        "prereg_sha256": a.prereg_sha256, "frozen_sha256": a.frozen_sha256,
        "labels": str(a.labels), "labels_sha256": file_sha(a.labels), "judge": str(a.judge),
        "judge_sha256": file_sha(a.judge), "quality": str(a.quality) if a.quality else None,
        "n_games": len(ids), "judge_lines": sum(g in judge for g in ids),
        "judge_missing": [g for g in ids if g not in judge],
        "judge_rejected": [g for g in ids if g in judge and judge[g].get("pair_scores") is None],
        "honest_baseline": doc["honest_baseline"], "baseline_source": "frozen rules file (original dev Type 2; not refit)",
    }
    a.out.mkdir(parents=True, exist_ok=True)
    rows = [{"game_id": g, "episode_type": labels[g].episode_type, "collusion": labels[g].collusion,
             **{f"{r}_flag": d[r]["flag"] for r in d}, **{f"{r}_pair": d[r]["pair"] for r in d},
             **{f"{r}_{k}": d[r][k] for r in d for k in ("score", "points", "prob") if k in d[r]}}
            for g, d in sorted(decisions.items())]
    with open(a.out / "decisions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (a.out / "results.json").write_text(json.dumps(R._jsonable(res), indent=1) + "\n", encoding="utf-8")
    for part in ("primary", "sensitivity"):
        p = res[part]
        if "E1" not in p:
            print(f"{part}: {p['status']}")
            continue
        print(f"{part} (n {p['n']}):")
        for e in ("E1", "E2", "E3", "E3b"):
            print(f"  {e}: {p[e]['test']} = {p[e]['estimate']:.3f} [{p[e]['ci_low']:.3f}, {p[e]['ci_high']:.3f}]"
                  f" -> {p[e]['verdict']}")
        for r in ("R2", REP.BEST_COMBINED):
            print(f"  E4 {r}: " + ", ".join(f"{t} {v['k']}/{v['n']}" for t, v in p["E4"][r].items()))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
