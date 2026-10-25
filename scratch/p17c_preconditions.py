"""Task 17C §0 preconditions + dev-only choices (read-only, no model calls, NO test number computed).

  conda run -n collusion-lab python -B scratch/p17c_preconditions.py      -> runs/study23/preconditions.json

Checks: frozen rules file committed and equal to its blob (LF sha256), judge.jsonl sha256 == frozen, honest baseline
refits to the frozen one from the 4 DEV Type 2 games, every test game has an accepted judge line (sample 0).
Dev choices (RQ-E3) from the frozen dev report; exploratory plus-factor thresholds (capture, C_kw) on DEV only.
Test games are touched only to check that a judge line exists (no score is read).
"""
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT, load_json  # noqa: E402
from core.evidence.signals import fit_honest_baseline, game_signals, pair_signal_table  # noqa: E402
from core.labels import read_labels  # noqa: E402
from core.stats import metrics as M  # noqa: E402
from study_2_3_evidence import rules as R  # noqa: E402
from study_2_3_evidence.judge import load_judge  # noqa: E402

SHA = "ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5"
FROZEN = REPO_ROOT / "configs/frozen/rules_frozen.json"
JUDGE = REPO_ROOT / "runs/judge_v1/outputs/judge.jsonl"
OUT = REPO_ROOT / "runs/study23/preconditions.json"


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=True).stdout


fz = json.loads(FROZEN.read_text(encoding="utf-8"))
commit = git("log", "-1", "--format=%H %ci", "--", "configs/frozen/rules_frozen.json").decode().strip()
blob = git("show", "HEAD:configs/frozen/rules_frozen.json")
labels = {lb.game_id: lb for lb in read_labels(REPO_ROOT / "data/labels.csv")}
split = load_json(REPO_ROOT / "data/split.json")
dev, test = sorted(split["dev"]), sorted(split["test"])
dev_t2 = [g for g in dev if labels[g].episode_type == 2]
base = fit_honest_baseline([load_json(REPO_ROOT / "data/clean" / f"{g}.json") for g in dev_t2])
j0 = load_judge(JUDGE, 0)
missing = [g for g in test if g not in j0 or j0[g].get("pair_scores") is None]

checks = {
    "frozen_commit": commit,
    "working copy == HEAD blob": FROZEN.read_bytes() == blob,
    "LF sha256 == expected": R.file_sha256(FROZEN) == SHA,
    "raw sha256 of HEAD blob": hashlib.sha256(blob).hexdigest(),
    "judge.jsonl sha256 == frozen": hashlib.sha256(JUDGE.read_bytes()).hexdigest() == fz["judge"]["judge_jsonl_sha256"],
    "frozen dev_ids == split dev": fz["dev_ids"] == dev,
    "dev Type 2 games": dev_t2,
    "baseline refit on dev Type 2 == frozen": asdict(base) == fz["honest_baseline"],
    "frozen baseline n_pairs == 10 x n(dev Type 2)": fz["honest_baseline"]["n_pairs"] == 10 * len(dev_t2),
    "test games missing an accepted judge line (sample 0)": missing,
}
ok = (checks["working copy == HEAD blob"] and checks["LF sha256 == expected"] and checks["judge.jsonl sha256 == frozen"]
      and checks["frozen dev_ids == split dev"] and checks["baseline refit on dev Type 2 == frozen"]
      and checks["frozen baseline n_pairs == 10 x n(dev Type 2)"] and not missing)

# ---- RQ-E3 dev choices: the frozen file does not record them -> rule fixed in task 17C (ties -> lower number)
rep = fz["dev_report"]
assert "best_single" not in fz and "best_combined" not in fz
def pick(rs):
    return max(rs, key=lambda r: (round(rep[r]["balanced_accuracy"], 12), -int(r[1:])))
choices = {"best_single": pick(["R1", "R2", "R3"]), "best_combined": pick(["R4", "R5", "R6", "R7"]),
           "dev_ba": {r: rep[r]["balanced_accuracy"] for r in R.RULES}, "R7_source": rep["R7"]["source"]}

# ---- exploratory plus-factor rule thresholds, DEV ONLY
ys = {g: labels[g].collusion for g in dev}
gs = {g: game_signals(pair_signal_table(load_json(REPO_ROOT / "data/clean" / f"{g}.json"), base)) for g in dev}
cap = [(gs[g]["capture"], ys[g]) for g in dev if gs[g]["capture"] is not None]
cap_fit = M.best_threshold([s for s, _ in cap], [y for _, y in cap])
kw_neg = sorted(gs[g]["C_kw"] for g in dev if ys[g] == 0 and gs[g]["C_kw"] is not None)
plus_factor = {"capture_threshold": cap_fit["threshold"], "capture_dev_fit": cap_fit,
               "capture_n_used": len(cap), "capture_n_na": len(dev) - len(cap),
               "C_kw_threshold": float(np.percentile(kw_neg, 90)), "C_kw_dev_negatives": kw_neg,
               "rule": "flag if game-max capture >= capture_threshold AND game-max C_kw >= C_kw_threshold "
                       "(each signal's own max pair; NA never flags)"}
flags = [int(R._ge(gs[g]["capture"], plus_factor["capture_threshold"]) and R._ge(gs[g]["C_kw"], plus_factor["C_kw_threshold"]))
         for g in dev]
plus_factor["dev_in_sample"] = {**R.binary_metrics(flags, [ys[g] for g in dev]),
                                "fpr_by_type": M.fpr_by_type(flags, [ys[g] for g in dev],
                                                             [labels[g].episode_type for g in dev])}

doc = R._jsonable({"all_ok": ok, "checks": checks, "dev_choices": choices, "plus_factor_dev": plus_factor})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
print(json.dumps(doc, indent=1))
sys.exit(0 if ok else 1)
