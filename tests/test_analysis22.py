"""End-to-end test of the Study 2.2 analysis tables on a synthetic monitor.jsonl (no model calls)."""
import csv
import json
import random

import pytest

from scripts import analyse_22
from study_2_2_views import analysis as A

TYPES = [1] * 16 + [2] * 8 + [3] * 8 + [4] * 8


def _setup(tmp_path, prompt_version="monitor_v1"):
    rng = random.Random(1)
    games = [f"g_{i:010x}" for i in range(len(TYPES))]
    labels = {g: t for g, t in zip(games, TYPES)}
    with open(tmp_path / "labels.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "episode_type", "collusion", "focal_pair", "variant", "synthetic"])
        for g, t in labels.items():
            w.writerow([g, t, int(t == 1), "M|T", "v", "false"])
    dev = [g for i, g in enumerate(games) if i % 2 == 0]
    test = [g for i, g in enumerate(games) if i % 2 == 1]
    (tmp_path / "split.json").write_text(json.dumps({"dev": dev, "test": test}), encoding="utf-8")
    lines = []
    for g, t in labels.items():
        y = int(t == 1)
        score = {"V1": (70 if y else 40) + rng.randint(-25, 25), "V2": rng.randint(0, 100),
                 "V3": (80 if y else 30) + rng.randint(-10, 10), "V4": 90 if y else 10, "V5": 85 if y else 15,
                 "C-mismatch": rng.randint(0, 100), "C-length": (75 if y else 35) + rng.randint(-10, 10),
                 "C-shuffled": rng.randint(0, 100)}
        for v, s in score.items():
            failed = (v == "V1" and g == games[2])                  # one failed output (dev, type 1)
            pair = ["M", "T"] if (y and v == "V3" and rng.random() < 0.6) else ["J", "Q"]
            lines.append({"game_id": g, "view": v, "sample_idx": 0, "prompt_version": prompt_version,
                          "score": None if failed else s, "suspected_pair": [] if failed else pair})
    (tmp_path / "monitor.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    with open(tmp_path / "signals.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "Dep", "Dep_pair", "coGO_flag"])
        for g, t in labels.items():
            w.writerow([g, 1.5 if t in (1, 4) else -0.5, "M-T" if t == 1 else "", "constant"])
    return games, labels, dev, test


def _args(tmp_path, *extra):
    return ["--monitor", str(tmp_path / "monitor.jsonl"), "--labels", str(tmp_path / "labels.csv"), "--split",
            str(tmp_path / "split.json"), "--signals", str(tmp_path / "signals.csv"), "--out", str(tmp_path / "out"),
            "--b", "200", *extra]


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_dev_then_test_end_to_end(tmp_path):
    _setup(tmp_path)
    frozen = tmp_path / "frozen.json"
    assert analyse_22.main(["--mode", "dev", *_args(tmp_path, "--freeze-out", str(frozen))]) == 0
    sha = A.file_sha256(frozen)
    doc = json.loads(frozen.read_text(encoding="utf-8"))
    assert doc["prompt_versions"] == ["monitor_v1"] and doc["best_single_view"] == "V1"   # V1 informative, V2 noise
    top = max(doc["per_view"][v]["dev_auroc"] for v in A.LLM_VIEWS)
    earliest = next(v for v in A.LLM_VIEWS if doc["per_view"][v]["dev_auroc"] == top)
    assert doc["best_llm_view"] == earliest == "V3"                  # V3, V4, V5 tie at 1.0 -> earlier view
    assert set(doc["per_view"]) == set(A.VIEWS_ALL)
    dev_rows = {r["view"]: r for r in _read(tmp_path / "out" / "rq1_per_view_dev.csv")}
    assert dev_rows["V1"]["failed"] == "1" and dev_rows["V4"]["auroc"] == "1.0"
    # test mode refuses without / with a wrong frozen file
    assert analyse_22.main(["--mode", "test", *_args(tmp_path)]) == 3
    assert analyse_22.main(["--mode", "test", *_args(tmp_path, "--frozen", str(frozen), "--frozen-sha256", "0" * 64)]) == 3
    assert not (tmp_path / "out" / "summary_test.md").exists()
    assert analyse_22.main(["--mode", "test", *_args(tmp_path, "--frozen", str(frozen), "--frozen-sha256", sha)]) == 0
    rows = {r["view"]: r for r in _read(tmp_path / "out" / "rq1_per_view_test.csv")}
    for v in A.VIEWS_ALL:                                             # frozen dev thresholds, never refit on test
        assert float(rows[v]["threshold"]) == doc["per_view"][v]["threshold"]
    assert rows["V4"]["auroc"] == "1.0" and rows["V4"]["fpr"] == "0.0" and rows["V4"]["tpr"] == "1.0"
    paired = _read(tmp_path / "out" / "rq2_rq4_rq5_rq6_rq7_paired_test.csv")
    rq2 = next(r for r in paired if r["rq"] == "RQ2")
    assert (rq2["a"], rq2["b"], rq2["primary"]) == ("V3", "V1", "True")
    assert {r["rq"] for r in paired} == {"RQ2", "RQ4", "RQ5", "RQ6", "RQ7"}
    rq7 = next(r for r in paired if r["rq"] == "RQ7")
    assert rq7["a"] == "Dep" and rq7["b"] == doc["best_llm_view"]
    fpr = _read(tmp_path / "out" / "rq3_fpr_by_type_test.csv")
    assert {r["type"] for r in fpr} == {"2", "3", "4"} and all(r["view"] in A.VIEWS_ALL for r in fpr)
    top1 = {r["source"]: r for r in _read(tmp_path / "out" / "rq8_top1_pair_test.csv")}
    assert top1["evidence argmax (Dep)"]["accuracy"] == "1.0" and top1["monitor V2"]["accuracy"] == "0.0"
    text = (tmp_path / "out" / "summary_test.md").read_text(encoding="utf-8")
    assert "TEST split" in text and sha in text and "RQ3 FPR per negative type" in text


def test_prompt_version_mismatch_refused(tmp_path):
    _setup(tmp_path)
    frozen = tmp_path / "frozen.json"
    analyse_22.main(["--mode", "dev", *_args(tmp_path, "--freeze-out", str(frozen))])
    sha = A.file_sha256(frozen)
    _setup(tmp_path, prompt_version="monitor_v3_pairs")              # different monitor outputs, same file name
    with pytest.raises(A.FrozenError):
        A.check_frozen(frozen, sha, {"monitor_v3_pairs"})
    assert analyse_22.main(["--mode", "test", *_args(tmp_path, "--frozen", str(frozen), "--frozen-sha256", sha)]) == 3


def test_paired_rows_use_games_scored_in_both_arms(tmp_path):
    games, labels, dev, test = _setup(tmp_path)
    scores, pairs, _ = A.load_monitor(tmp_path / "monitor.jsonl")
    lab = A.load_labels(tmp_path / "labels.csv")
    choices = A.dev_choices(scores, lab, dev)
    rows = A.paired_table(scores, lab, dev, choices, None, b=100)
    rq2 = next(r for r in rows if r["rq"] == "RQ2")
    assert rq2["n"] == len(dev) - 1                                   # the failed V1 game is dropped from RQ2


def test_duplicate_monitor_line_rejected(tmp_path):
    p = tmp_path / "m.jsonl"
    line = json.dumps({"game_id": "g", "view": "V1", "score": 1, "sample_idx": 0})
    p.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        A.load_monitor(p)
