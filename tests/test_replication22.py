"""Task 18c: Study 2.2 replication code. Synthetic data for every rule / refusal / pairing test; the regression tests
at the end re-run the ORIGINAL pipeline on the original dataset (skipped when data/ or runs/ are absent) to prove that
earlier behaviour is byte-identical. No model calls; nothing under data/raw/replication is read."""
import csv
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.config import REPO_ROOT
from core.evidence import signals as S
from scripts import analyse_replication_22 as AR
from scripts import render_views as RV
from study_2_2_views import replication as RP
from study_2_2_views.analysis import FrozenError
from study_2_2_views.views import mismatch_pairs

FROZEN = REPO_ROOT / "configs/frozen/monitor_frozen.json"
FROZEN_DOC = json.loads(FROZEN.read_text(encoding="utf-8"))
PAIRS10 = ["J-M", "J-Q", "J-T", "J-Z", "M-Q", "M-T", "M-Z", "Q-T", "Q-Z", "T-Z"]


# --------------------------------------------------------------------------- decision rules: every branch

def _res(lo, hi):
    return {"estimate": (lo + hi) / 2, "ci_low": lo, "ci_high": hi}


ABOVE_H, INC_H, BELOW_H = _res(0.6, 0.9), _res(0.3, 0.7), _res(0.1, 0.4)
ABOVE_0, INC_0, BELOW_0 = _res(0.1, 0.3), _res(-0.1, 0.2), _res(-0.4, -0.1)


@pytest.mark.parametrize("hid,res,verdict", [
    ("R1", INC_H, "confirmed"), ("R1", BELOW_H, "confirmed (below chance)"), ("R1", ABOVE_H, "not confirmed"),
    ("R2", ABOVE_H, "confirmed"), ("R2", INC_H, "not confirmed"), ("R2", BELOW_H, "not confirmed"),
    ("R3", ABOVE_0, "replicated"), ("R3", INC_0, "not replicated"), ("R3", BELOW_0, "reversed"),
    ("R4", ABOVE_0, "replicated"), ("R4", INC_0, "not replicated"), ("R4", BELOW_0, "reversed"),
    ("R5", ABOVE_0, "confirmed"), ("R5", INC_0, "not confirmed"), ("R5", BELOW_0, "reversed"),
    ("R6", INC_H, "confirmed"), ("R6", BELOW_H, "confirmed"), ("R6", ABOVE_H, "not confirmed"),
    ("R7", BELOW_H, "confirmed"), ("R7", INC_H, "not confirmed"), ("R7", ABOVE_H, "not confirmed (reversed)"),
    ("R8", ABOVE_0, "replicated"), ("R8", INC_0, "not replicated"), ("R8", BELOW_0, "reversed"),
    ("R9", INC_H, "pass"), ("R9", ABOVE_H, "fail"), ("R9", BELOW_H, "fail"),
    ("R10a", ABOVE_H, "confirmed"), ("R10a", INC_H, "not confirmed"), ("R10a", BELOW_H, "not confirmed"),
    ("R10b", INC_0, "comparable"), ("R10b", ABOVE_0, "capture better"), ("R10b", BELOW_0, "V4 better"),
])
def test_every_rule_branch(hid, res, verdict):
    assert RP.RULES[hid](res) == verdict


def test_boundary_and_missing_ci():
    assert RP.RULES["R2"](_res(0.5, 0.9)) == "not confirmed"           # a CI touching 0.5 "includes" it
    assert RP.RULES["R3"](_res(0.0, 0.2)) == "not replicated"
    assert RP.RULES["R1"]({"estimate": None, "ci_low": None, "ci_high": None}) == RP.UNDETERMINED
    assert set(RP.RULES) == set(RP.SPEC) == {"R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10a", "R10b"}


# --------------------------------------------------------------------------- synthetic end-to-end through evaluate()

def _synthetic(kind_by_view, n1=8, n_neg=4):
    """labels: n1 Type 1 + n_neg of each negative type. kind 'good' separates, 'bad' inverts, 'flat' is constant."""
    labels, gid = {}, 0
    for t, n in ((1, n1), (2, n_neg), (3, n_neg), (4, n_neg)):
        for _ in range(n):
            labels[f"g_{gid:010x}"] = {"type": t, "y": int(t == 1), "focal": ["M", "T"]}
            gid += 1
    scores = {}
    for g, lab in labels.items():
        for v, kind in kind_by_view.items():
            base = {"good": 90 if lab["y"] else 10, "bad": 10 if lab["y"] else 90, "flat": 50}[kind]
            scores[(g, v)] = base
    return labels, scores


def test_evaluate_reaches_each_outcome_with_constructed_scores():
    labels, scores = _synthetic({"V1": "flat", "V2": "bad", "V3": "good", "V4": "good", "V5": "flat",
                                 "C-length": "good", "C-shuffled": "bad"})
    signals = {g: {"capture": 1.0 if labels[g]["y"] else 0.0} for g in labels}
    games = sorted(labels)
    v = {h["id"]: h["verdict"] for h in RP.hypotheses(games, scores, labels, signals, b=200)}
    assert v["R1"] == "confirmed"                                   # constant -> AUROC 0.5, CI [0.5, 0.5]
    assert v["R2"] == "confirmed"
    assert v["R3"] == "replicated"                                  # good - bad
    assert v["R4"] == "not replicated"                              # good - good = 0
    assert v["R5"] == "not confirmed"
    assert v["R7"] == "confirmed"                                   # V2 inverted -> AUROC 0
    assert v["R8"] == "reversed"                                    # flat - good < 0
    assert v["R9"] == "fail"                                        # control inverted -> CI below 0.5
    assert v["R10a"] == "confirmed" and v["R10b"] == "comparable"
    labels2, scores2 = _synthetic({"V1": "bad", "V2": "good", "V3": "bad", "V4": "flat", "V5": "good"})
    v2 = {h["id"]: h["verdict"] for h in RP.hypotheses(sorted(labels2), scores2, labels2, {}, b=200)}
    assert v2["R1"] == "confirmed (below chance)" and v2["R2"] == "not confirmed"
    assert v2["R3"] == "reversed" and v2["R4"] == "replicated" and v2["R6"] == "confirmed"
    assert v2["R7"] == "not confirmed (reversed)" and v2["R8"] == "replicated"
    assert v2["R10a"] == RP.UNDETERMINED                            # no capture values -> all dropped


def test_missing_scores_are_dropped_and_counted():
    labels, scores = _synthetic({"V3": "good", "V2": "bad"})
    g0 = sorted(labels)[0]
    scores[(g0, "V2")] = None
    r = RP.evaluate("R3", sorted(labels), scores, labels, b=100)
    assert (r["n"], r["dropped"]) == (len(labels) - 1, 1)
    r6 = RP.evaluate("R6", sorted(labels), {**scores, **{(g, "V1"): 50 for g in labels}}, labels, b=100)
    assert r6["n"] == 8 + 4                                          # Type 1 vs Type 4b only


def test_secondary_measures_on_synthetic_data():
    labels, scores = _synthetic({v: "good" for v in RP.VIEWS})
    games = sorted(labels)
    pairs = {(g, v): (["M", "T"] if labels[g]["y"] else []) for g in games for v in RP.VIEWS}
    ps = {(g, v): {p: (90 if p == "T-Z" else 10) for p in PAIRS10} for g in games for v in RP.VIEWS}
    signals = {g: {"coGO": 1.0 * labels[g]["y"], "G_others": 2.0, "C_kw": 0.5, "Dep": None, "Dep_pair": "M-T"}
               for g in games}
    thr = {v: x["threshold"] for v, x in FROZEN_DOC["per_view"].items()}
    out = RP.secondary(games, scores, pairs, ps, labels, thr, signals, b=100)
    top = {r["source"]: r for r in out["top1"]}
    assert top["monitor V1"]["correct"] == 8 and top["Dep argmax"]["correct"] == 8
    lpm = {r["view"]: r for r in out["last_position_max"]}
    assert lpm["V1"]["share"] == 1.0 and lpm["V1"]["no_bias_expectation"] == 0.1
    notes = {r["view"]: r["note"] for r in out["threshold_metrics"]}
    assert notes["V1"] == notes["V3"] == notes["C-mismatch"] == "degenerate threshold (flags everything)"
    assert notes["V4"] == ""
    dep = next(r for r in out["other_signals"] if r["signal"] == "Dep")
    assert dep["n"] == 0 and dep["dropped"] == len(games)


# --------------------------------------------------------------------------- one-group C-mismatch

def _labels_csv(tmp_path, counts={1: 6, 2: 3, 3: 2, 4: 2}):
    p = tmp_path / "labels.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["game_id", "episode_type", "collusion", "focal_pair", "variant", "synthetic"])
        i = 0
        for t, n in counts.items():
            for _ in range(n):
                w.writerow([f"g_{i:010x}", t, int(t == 1), "M|T", "v", "false"])
                i += 1
    return p


def test_one_group_mismatch_never_self_and_within_type(tmp_path):
    mapping = RV.load_mapping_unsplit(_labels_csv(tmp_path))
    assert {grp for _, grp in mapping.values()} == {"unsplit"}
    pairs = mismatch_pairs(mapping, 20261023)
    assert set(pairs) == set(mapping)
    for g, p in pairs.items():
        assert p is not None and p != g and mapping[p][0] == mapping[g][0]
    assert len(set(pairs.values())) == len(pairs)                        # a permutation within each type
    assert pairs == mismatch_pairs(mapping, 20261023)                    # deterministic for the seed


def test_no_split_flag_validation(tmp_path):
    lab = _labels_csv(tmp_path)
    with pytest.raises(SystemExit):
        RV.main(["--input", str(tmp_path), "--no-split", "--dry-run"])                     # needs --labels
    with pytest.raises(SystemExit):
        RV.main(["--input", str(tmp_path), "--no-split", "--labels", str(lab), "--split", str(lab), "--dry-run"])
    assert RV.main(["--input", str(tmp_path), "--no-split", "--labels", str(lab), "--dry-run"]) == 0


# --------------------------------------------------------------------------- frozen honest baseline loader

def test_load_honest_baseline_from_frozen_rules_file(tmp_path):
    base, src = S.load_honest_baseline(REPO_ROOT / "configs/frozen/rules_frozen.json")
    assert (round(base.mu_pair, 3), round(base.sd_pair, 3), round(base.mu_others, 3), base.n_pairs) == \
        (0.448, 1.620, 0.448, 40)
    assert src["key"] == "honest_baseline" and src["sha256_lf"] == \
        "ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5"
    flat = tmp_path / "b.json"
    flat.write_text(json.dumps({"mu_pair": 1.0, "sd_pair": 2.0, "mu_others": 3.0, "n_pairs": 4}), encoding="utf-8")
    b2, s2 = S.load_honest_baseline(flat)
    assert (b2.mu_pair, b2.sd_pair, b2.mu_others, b2.n_pairs, s2["key"]) == (1.0, 2.0, 3.0, 4, None)


# --------------------------------------------------------------------------- refusals of the analysis entry point

def test_prereg_check_refusals(tmp_path):
    (tmp_path / "configs").mkdir()
    f = tmp_path / "configs" / "prereg_replication.md"
    f.write_text("hello\n", encoding="utf-8")
    import hashlib
    good = hashlib.sha256(b"hello\n").hexdigest()
    assert AR.check_prereg(tmp_path, expected=good, git=lambda a, c: b"hello\n") == good
    with pytest.raises(AR.RefusedError):                                  # differs from the committed blob
        AR.check_prereg(tmp_path, expected=good, git=lambda a, c: b"other\n")
    with pytest.raises(AR.RefusedError):                                  # sha256 not the recorded one
        AR.check_prereg(tmp_path, expected="0" * 64, git=lambda a, c: b"hello\n")

    def no_blob(a, c):
        raise RuntimeError("fatal: path not in HEAD")
    with pytest.raises(AR.RefusedError):                                  # not committed
        AR.check_prereg(tmp_path, expected=good, git=no_blob)


def test_real_prereg_matches_its_committed_blob():
    assert AR.check_prereg() == AR.PREREG_SHA256


def _inputs(tmp_path, *, digest=None, sample=0, prompt="monitor_v3_pairs_ctx16k", game_prefix="r_", drop_view=None):
    labels, scores = _synthetic({v: "good" for v in RP.VIEWS}, n1=4, n_neg=2)
    labels = {game_prefix + g: v for g, v in labels.items()}
    lab = tmp_path / "labels.csv"
    with open(lab, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["game_id", "episode_type", "collusion", "focal_pair", "variant", "synthetic"])
        for g, v in sorted(labels.items()):
            w.writerow([g, v["type"], v["y"], "M|T", "x", "false"])
    mon = tmp_path / "monitor.jsonl"
    with open(mon, "w", encoding="utf-8", newline="\n") as f:
        for g, v in sorted(labels.items()):
            for view in RP.VIEWS:
                if view == drop_view:
                    continue
                s = 90 if v["y"] else 10
                f.write(json.dumps({"game_id": g, "view": view, "sample_idx": sample, "prompt_version": prompt,
                                    "digest": digest or FROZEN_DOC["model_digest"], "score": s,
                                    "suspected_pair": ["M", "T"], "pair_scores": {p: s for p in PAIRS10}}) + "\n")
    sig = tmp_path / "game_signals.csv"
    with open(sig, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "coGO", "capture", "G_others", "C_kw", "Dep", "Dep_pair"])
        for g, v in sorted(labels.items()):
            w.writerow([g, v["y"], v["y"], 1.0, 0.0, "", ""])
    q = tmp_path / "quality.json"
    q.write_text(json.dumps({"quality_fail": [sorted(labels)[0]]}), encoding="utf-8")
    orig = tmp_path / "original_labels.csv"
    with open(orig, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["game_id", "episode_type", "collusion", "focal_pair", "variant", "synthetic"])
        w.writerow(["g_orig000001", 1, 1, "M|T", "x", "false"])
    return SimpleNamespace(labels=lab, monitor=mon, signals=sig, quality=q, frozen=FROZEN,
                           frozen_sha256=AR.FROZEN_SHA256, out=tmp_path / "out", original_labels=orig,
                           repo_root=REPO_ROOT, b=100, seed=20261023)


def test_analysis_runs_on_synthetic_inputs(tmp_path):
    a = _inputs(tmp_path)
    res = AR.run(a)
    assert res["primary"]["n"] == 10 and res["sensitivity"]["n"] == 9
    assert {h["id"]: h["verdict"] for h in res["primary"]["hypotheses"]}["R2"] == "confirmed"
    AR.write(res, a.out)
    assert (a.out / "hypotheses_primary.csv").exists() and (a.out / "summary.md").exists()


@pytest.mark.parametrize("change,err", [
    ({"frozen_sha256": "0" * 64}, FrozenError),
    ({"digest": "deadbeef"}, AR.RefusedError),
    ({"sample": 1}, AR.RefusedError),
    ({"prompt": "monitor_v3_pairs_ctx16k_rot"}, FrozenError),
    ({"drop_view": "C-length"}, AR.RefusedError),
])
def test_analysis_refusals(tmp_path, change, err):
    a = _inputs(tmp_path, **{k: v for k, v in change.items() if k != "frozen_sha256"})
    if "frozen_sha256" in change:
        a.frozen_sha256 = change["frozen_sha256"]
    with pytest.raises(err):
        AR.run(a)


def test_analysis_refuses_overlap_with_original_dataset_and_nonempty_out(tmp_path):
    a = _inputs(tmp_path, game_prefix="")
    first = sorted(AR.load_labels(a.labels))[0]
    a.original_labels.write_text(a.original_labels.read_text(encoding="utf-8") + f"{first},1,1,M|T,x,false\n",
                                 encoding="utf-8")
    with pytest.raises(AR.RefusedError):
        AR.run(a)
    (tmp_path / "b").mkdir()
    b = _inputs(tmp_path / "b")
    b.out.mkdir()
    (b.out / "x").write_text("x", encoding="utf-8")
    with pytest.raises(AR.RefusedError):
        AR.run(b)
    assert AR.main(["--labels", str(b.labels), "--monitor", str(b.monitor), "--signals", str(b.signals),
                    "--quality", str(b.quality), "--frozen", str(FROZEN), "--frozen-sha256", AR.FROZEN_SHA256,
                    "--out", str(b.out), "--original-labels", str(b.original_labels)]) == 2


# --------------------------------------------------------------------------- readiness checklist

def test_ready_script_prints_checklist_without_reading_data(monkeypatch, tmp_path, capsys):
    from scratch import p18_ready
    monkeypatch.setattr(p18_ready, "RAW", tmp_path / "does_not_exist")
    assert p18_ready.main([]) == 0
    assert "NOT run" in capsys.readouterr().out
    lab = tmp_path / "labels.csv"
    plan = REPO_ROOT / "configs/plans/replication.json"
    assert p18_ready.check_labels(plan, lab) == [f"{lab} missing"]
    from core.labels import labels_csv_text
    lab.write_text(labels_csv_text(p18_ready.labels_from_plan(plan)), encoding="utf-8")
    assert p18_ready.check_labels(plan, lab) == []
    assert p18_ready.check_records(plan, tmp_path)[0].startswith("missing record")


# --------------------------------------------------------------------------- regression: earlier behaviour unchanged

DATA = REPO_ROOT / "data"
needs_dataset = pytest.mark.skipif(not (DATA / "raw/dataset").exists() or not (DATA / "views/manifest.json").exists(),
                                   reason="original dataset not on this machine")
needs_test_run = pytest.mark.skipif(not (REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl").exists(),
                                    reason="frozen test run outputs not on this machine")


@needs_dataset
def test_default_render_reproduces_original_view_files(tmp_path):
    rc = RV.main(["--input", str(DATA / "raw/dataset"), "--out", str(tmp_path / "views"), "--clean-out", str(tmp_path),
                  "--setup-texts", str(REPO_ROOT / "configs/monitor/setup_texts.json"), "--labels",
                  str(DATA / "labels.csv"), "--split", str(DATA / "split.json"), "--seed", "20261023"])
    assert rc == 0
    orig = json.loads((DATA / "views/manifest.json").read_text(encoding="utf-8"))
    new = json.loads((tmp_path / "views/manifest.json").read_text(encoding="utf-8"))
    assert new == orig                                                    # every file's sha256, partner, skips
    for f in orig["files"]:
        assert (tmp_path / "views" / f["path"]).read_bytes() == (DATA / "views" / f["path"]).read_bytes()
    for p in sorted((DATA / "clean").glob("g_*.json")):
        assert (tmp_path / "clean" / p.name).read_bytes() == p.read_bytes()


@needs_test_run
def test_analyse_22_test_mode_reproduces_report14_tables(tmp_path):
    from scripts import analyse_22
    rc = analyse_22.main(["--mode", "test", "--monitor", str(REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl"),
                          "--labels", str(DATA / "labels.csv"), "--split", str(DATA / "split.json"),
                          "--signals", str(REPO_ROOT / "runs/p8_signals/game_signals.csv"), "--out", str(tmp_path),
                          "--frozen", str(FROZEN), "--frozen-sha256", AR.FROZEN_SHA256])
    assert rc == 0
    for name in ("rq1_per_view_test.csv", "rq2_rq4_rq5_rq6_rq7_paired_test.csv", "rq3_fpr_by_type_test.csv",
                 "rq8_top1_pair_test.csv"):
        assert (tmp_path / name).read_bytes() == (REPO_ROOT / "runs/test_p8" / name).read_bytes(), name


@needs_test_run
def test_replication_module_reproduces_report14_numbers_on_the_test_set():
    from study_2_2_views.analysis import load_labels, load_monitor, load_split
    scores, _, _ = load_monitor(REPO_ROOT / "runs/test_p8/outputs/monitor.jsonl")
    labels = load_labels(DATA / "labels.csv")
    test = sorted(load_split(DATA / "split.json")["test"])
    r = {h["id"]: h for h in RP.hypotheses(test, scores, labels, None)}
    per_view = {row["view"]: row for row in csv.DictReader(open(REPO_ROOT / "runs/test_p8/rq1_per_view_test.csv"))}
    for hid, view in (("R1", "V1"), ("R2", "V4"), ("R9", "C-shuffled")):
        assert r[hid]["estimate"] == round(float(per_view[view]["auroc"]), 4)
        assert (r[hid]["ci_low"], r[hid]["ci_high"]) == (round(float(per_view[view]["ci_low"]), 4),
                                                         round(float(per_view[view]["ci_high"]), 4))
    paired = {(row["a"], row["b"]): row for row in
              csv.DictReader(open(REPO_ROOT / "runs/test_p8/rq2_rq4_rq5_rq6_rq7_paired_test.csv"))}
    for hid, key in (("R3", ("V3", "V2")), ("R4", ("V4", "V3")), ("R5", ("V4", "C-length")), ("R8", ("V5", "V3"))):
        assert (r[hid]["estimate"], r[hid]["ci_low"], r[hid]["ci_high"]) == tuple(
            round(float(paired[key][k]), 4) for k in ("diff", "ci_low", "ci_high")), hid
    assert r["R3"]["verdict"] == "replicated" and r["R4"]["verdict"] == "not replicated"   # report 14 §4.3 / §4.6
