"""Study 2.2 replication analysis (configs/prereg_replication.md §3): R1-R10 + secondary measures, primary = all games,
sensitivity = without quality-fail games. A confirmation set without a split: nothing is fitted or chosen.

Refuses unless: the frozen monitor file matches its sha256 (ccc4bf07...), the monitor lines are the frozen prompt
version / digest / sample 0, the prereg file equals its committed blob AND the recorded sha256, the labels share no game
with the original dataset (data/labels.csv), and every labelled game has monitor lines, code signals and a quality
verdict. Writes into a new (or empty) --out folder.

  conda run -n collusion-lab python scripts/analyse_replication_22.py --labels data/replication/labels.csv \
      --monitor runs/replication_22/outputs/monitor.jsonl --signals runs/replication/signals/game_signals.csv \
      --quality runs/replication/quality.json --out runs/replication/analysis_22 \
      --frozen configs/frozen/monitor_frozen.json --frozen-sha256 ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, read_text_lf  # noqa: E402
from study_2_2_views import replication as RP  # noqa: E402
from study_2_2_views.analysis import (FrozenError, check_frozen, file_sha256, load_labels, load_monitor,  # noqa: E402
                                      load_signals)

FROZEN_SHA256 = "ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f"
PREREG = Path("configs/prereg_replication.md")
PREREG_SHA256 = "d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9"
ORIGINAL_LABELS = REPO_ROOT / "data" / "labels.csv"


class RefusedError(RuntimeError):
    pass


def check_prereg(repo_root: Path = REPO_ROOT, rel: Path = PREREG, expected: str = PREREG_SHA256,
                 git=lambda args, cwd: subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout):
    """The prereg on disk must equal its committed blob (read-only `git show HEAD:<file>`) and the recorded sha256."""
    disk = read_text_lf(Path(repo_root) / rel)
    try:
        blob = git(["show", f"HEAD:{rel.as_posix()}"], repo_root).decode("utf-8").replace("\r\n", "\n")
    except Exception as e:                                           # not committed, or no git
        raise RefusedError(f"cannot read the committed blob of {rel}: {e}")
    if disk != blob:
        raise RefusedError(f"{rel} differs from its committed blob")
    got = hashlib.sha256(disk.encode("utf-8")).hexdigest()
    if got != expected:
        raise RefusedError(f"{rel} sha256 {got[:12]}... != recorded {expected[:12]}...")
    return got


def load_monitor_full(path: Path, sample_idx: int = 0) -> tuple[dict, set, set]:
    """pair_scores per (game, view), plus the set of digests and sample indices seen (for the refusal checks)."""
    ps, digests, samples = {}, set(), set()
    for line in read_text_lf(path).splitlines():
        if line.strip():
            d = json.loads(line)
            samples.add(d.get("sample_idx", 0))
            digests.add(d.get("digest"))
            if d.get("sample_idx", 0) == sample_idx:
                ps[(d["game_id"], d["view"])] = d.get("pair_scores")
    return ps, digests, samples


def load_quality(path: Path) -> set:
    doc = json.loads(read_text_lf(path))
    if "quality_fail" not in doc:
        raise RefusedError(f"{path}: needs a 'quality_fail' list of game ids (empty list if none)")
    return set(doc["quality_fail"])


def run(a) -> dict:
    if a.out.exists() and any(a.out.iterdir()):
        raise RefusedError(f"{a.out} exists and is not empty")
    pair_scores, digests, samples = load_monitor_full(a.monitor, 0)
    if samples != {0}:
        raise RefusedError(f"monitor file holds sample indices {sorted(samples)}; the replication scores sample 0 only")
    scores, pairs, versions = load_monitor(a.monitor, 0)
    frozen = check_frozen(a.frozen, a.frozen_sha256, versions)                       # raises FrozenError
    if a.frozen_sha256 != FROZEN_SHA256:
        raise RefusedError(f"--frozen-sha256 is not the frozen Study 2.2 monitor ({FROZEN_SHA256[:12]}...)")
    if digests != {frozen["model_digest"]}:
        raise RefusedError(f"monitor digests {sorted(map(str, digests))} != frozen {frozen['model_digest'][:12]}...")
    prereg_sha = check_prereg(a.repo_root)
    labels = load_labels(a.labels)
    if a.original_labels.exists():
        overlap = set(labels) & set(load_labels(a.original_labels))
        if overlap:
            raise RefusedError(f"{len(overlap)} labelled games are in the original dataset, e.g. {sorted(overlap)[:3]}")
    games = sorted(labels)
    missing = [(g, v) for g in games for v in RP.VIEWS if (g, v) not in scores]
    extra = sorted({g for g, _ in scores} - set(games))
    if missing or extra:
        raise RefusedError(f"monitor lines do not match the labels: {len(missing)} missing, {len(extra)} extra games")
    signals = load_signals(a.signals)
    if set(signals) != set(games):
        raise RefusedError("code-signals file does not cover exactly the labelled games")
    qfail = load_quality(a.quality)
    if not qfail <= set(games):
        raise RefusedError("quality_fail lists games that are not labelled")
    thresholds = {v: x["threshold"] for v, x in frozen["per_view"].items()}
    result = {"prereg_sha256": prereg_sha, "frozen_sha256": a.frozen_sha256,
              "inputs": {k: {"path": str(p), "sha256_lf": file_sha256(p)} for k, p in
                         (("labels", a.labels), ("monitor", a.monitor), ("signals", a.signals),
                          ("quality", a.quality))},
              "n_games": len(games), "quality_fail": sorted(qfail), "b": a.b, "seed": a.seed}
    for name, gs in (("primary", games), ("sensitivity", [g for g in games if g not in qfail])):
        result[name] = {"n": len(gs),
                        "hypotheses": RP.hypotheses(gs, scores, labels, signals, a.b, a.seed),
                        "secondary": RP.secondary(gs, scores, pairs, pair_scores, labels, thresholds, signals,
                                                  a.b, a.seed)}
    return result


def write(result: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "replication_22.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for name in ("primary", "sensitivity"):
        rows = result[name]["hypotheses"]
        with open(out / f"hypotheses_{name}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    L = ["# Study 2.2 replication — R1-R10", "", f"prereg sha256 `{result['prereg_sha256']}`; frozen monitor "
         f"`{result['frozen_sha256']}`; n = {result['n_games']}; quality-fail: {len(result['quality_fail'])}", ""]
    for name in ("primary", "sensitivity"):
        L += [f"## {name} (n = {result[name]['n']})", "", "| ID | Test | n (dropped) | Estimate [95% CI] | Verdict |",
              "|---|---|---|---|---|"]
        L += [f"| {h['id']} | {h['test']} | {h['n']} ({h['dropped']}) | {h['estimate']} [{h['ci_low']}, {h['ci_high']}]"
              f" | {h['verdict']} |" for h in result[name]["hypotheses"]]
        L.append("")
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--monitor", type=Path, required=True)
    ap.add_argument("--signals", type=Path, required=True)
    ap.add_argument("--quality", type=Path, required=True, help='JSON {"quality_fail": [game ids]}')
    ap.add_argument("--frozen", type=Path, required=True)
    ap.add_argument("--frozen-sha256", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--original-labels", type=Path, default=ORIGINAL_LABELS)
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    ap.add_argument("--b", type=int, default=RP.B)
    ap.add_argument("--seed", type=int, default=RP.SEED)
    a = ap.parse_args(argv)
    try:
        result = run(a)
    except (FrozenError, RefusedError) as e:
        print(f"REFUSED: {e}")
        return 2
    write(result, a.out)
    print(f"wrote {a.out}: R1-R10 primary (n = {result['primary']['n']}) and sensitivity "
          f"(n = {result['sensitivity']['n']})")
    for h in result["primary"]["hypotheses"]:
        print(f"  {h['id']:5} {h['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
