"""Tests for the Study 2.3 replication analysis (study_2_3_evidence.replication, scripts/analyse_replication_23.py).

Synthetic data only, except test_reproduces_17c_test_tables, which re-derives report 17C's test results from the
existing local files (skipped where they are absent: data/, runs/ are never committed).
"""
import csv
import json
import random
from types import SimpleNamespace

import pytest

from core.config import REPO_ROOT, load_json
from core.evidence import signals as S
from study_2_3_evidence import replication as REP
from study_2_3_evidence import rules as R
from tests.test_rules import PAIRS, _clean

FROZEN_DOC = json.loads((REPO_ROOT / REP.FROZEN).read_text(encoding="utf-8"))


def ci(lo, hi, est=None):
    return {"estimate": (lo + hi) / 2 if est is None else est, "ci_low": lo, "ci_high": hi}


# --------------------------------------------------------------------------- decision rules: every branch

@pytest.mark.parametrize("c,want", [(ci(0.55, 0.9), "confirmed"), (ci(0.5, 0.9), "not confirmed"),
                                    (ci(0.3, 0.7), "not confirmed"), (ci(0.1, 0.4), "not confirmed")])
def test_e1_branches(c, want):
    assert REP.verdict_e1(c) == want


@pytest.mark.parametrize("c,want", [(ci(0.3, 0.7), "confirmed"), (ci(0.5, 0.8), "confirmed"),
                                    (ci(0.2, 0.5), "confirmed"), (ci(0.1, 0.45), "confirmed (below chance)"),
                                    (ci(0.55, 0.9), "not confirmed")])
def test_e2_branches(c, want):
    assert REP.verdict_e2(c) == want


@pytest.mark.parametrize("c,want", [(ci(0.01, 0.3), "replicated"), (ci(-0.2, 0.1), "not replicated"),
                                    (ci(0.0, 0.2), "not replicated"), (ci(-0.3, -0.05), "reversed")])
def test_e3_branches(c, want):
    assert REP.verdict_diff(c) == want


def test_verdict_without_ci_refuses():
    with pytest.raises(REP.ReplicationError):
        REP.verdict_e1({"estimate": None, "ci_low": None, "ci_high": None})


# --------------------------------------------------------------------------- analyse_set on synthetic decisions

def _set(n_per_type=6, seed=0, r2=None, r1=None, r6=None, r7=None):
    """Synthetic labels/decisions; each rule's score is a function (type, rng) -> value."""
    rng = random.Random(seed)
    labels, dec, games = {}, {}, {}
    k = 0
    for t in (1, 1, 2, 3, 4):
        for _ in range(n_per_type):
            g = f"g_s{k:08d}"
            k += 1
            labels[g] = SimpleNamespace(collusion=int(t == 1), episode_type=t)
            s = {"R1": r1(t, rng), "R2": r2(t, rng), "R6": r6(t, rng), "R7": r7(t, rng)}
            dec[g] = {r: {"flag": 0, "pair": None} for r in R.RULES}
            dec[g]["R1"].update(score=s["R1"], flag=int(s["R1"] is not None and s["R1"] >= 95))
            dec[g]["R2"].update(score=s["R2"], flag=int(s["R2"] >= 5))
            dec[g]["R3"].update(score=None)
            dec[g]["R6"].update(points=s["R6"], flag=int(s["R6"] >= 1))
            dec[g]["R7"].update(prob=s["R7"], flag=int(s["R7"] >= 0.5))
            games[g] = [{"game_id": g, "pair": p, "capture": 0.9 if (t in (1, 4) and p == "M-T") else 0.0,
                         "C_kw": 1.0 if (t == 1 and p == "M-T") else 0.0} for p in PAIRS]
    return games, dec, labels, sorted(labels)


SEP = lambda t, r: 10.0 if t == 1 else r.uniform(-2, 2)          # noqa: E731  perfect separation
NOISE = lambda t, r: r.uniform(0, 100)                             # noqa: E731
INV = lambda t, r: 0.0 if t == 1 else r.uniform(50, 100)           # noqa: E731  below chance
HALF = lambda t, r: r.choice([0, 1])                               # noqa: E731
PROB = lambda t, r: r.uniform(0, 1)                                # noqa: E731


def test_analyse_set_confirmed_branches_and_e3_reversed():
    games, dec, labels, ids = _set(r2=SEP, r1=NOISE, r6=HALF, r7=PROB, n_per_type=8)
    out = REP.analyse_set(games, dec, labels, ids, b=300)
    assert out["E1"]["verdict"] == "confirmed" and out["E1"]["estimate"] == 1.0
    assert out["E2"]["verdict"] == "confirmed"
    assert out["E3"]["verdict"] == "reversed" and out["E3b"]["verdict"] == "reversed"
    assert out["E3"]["test"] == "AUROC(R6) - AUROC(R2), paired" and out["E3b"]["status"] == "secondary"


def test_analyse_set_below_chance_not_confirmed_and_replicated():
    games, dec, labels, ids = _set(r2=NOISE, r1=INV, r6=lambda t, r: 2 if t == 1 else 0, r7=PROB, n_per_type=8)
    out = REP.analyse_set(games, dec, labels, ids, b=300)
    assert out["E2"]["verdict"] == "confirmed (below chance)"
    assert out["E1"]["verdict"] == "not confirmed"
    assert out["E3"]["verdict"] == "replicated"


def test_e4_and_plus_factor_counts_per_type_with_rule_of_three():
    games, dec, labels, ids = _set(r2=SEP, r1=NOISE, r6=HALF, r7=PROB, n_per_type=4)
    out = REP.analyse_set(games, dec, labels, ids, b=50)
    e4 = out["E4"]["R2"]
    assert e4["T1"] == {"k": 8, "n": 8, "rate": 1.0, "upper95_rule_of_three": None}
    assert e4["T2"]["k"] == 0 and e4["T2"]["upper95_rule_of_three"] == 0.75
    pf = out["plus_factor_secondary"]
    assert pf["thresholds"] == {"capture": 0.625, "C_kw": 0.7375}
    assert pf["per_type"]["T1"]["k"] == 8 and pf["per_type"]["T4b"]["k"] == 0       # T4b: capture but no keywords


def test_na_scores_are_left_out_and_counted():
    games, dec, labels, ids = _set(r2=SEP, r1=NOISE, r6=HALF, r7=PROB, n_per_type=4)
    for g in ids[:3]:
        dec[g]["R1"]["score"] = None
    out = REP.analyse_set(games, dec, labels, ids, b=50)
    assert out["n_score_na"]["R1"] == 3 and out["E3"]["n"] == len(ids)


def test_sensitivity_without_quality_fail_games():
    games, dec, labels, ids = _set(r2=SEP, r1=NOISE, r6=HALF, r7=PROB, n_per_type=4)
    out = REP.analyse_replication(games, dec, labels, ids, ids[:2], b=50)
    assert out["primary"]["n"] == 20 and out["sensitivity"]["n"] == 18 and out["sensitivity"]["quality_fail"] == ids[:2]
    assert REP.analyse_replication(games, dec, labels, ids, [], b=50)["sensitivity"]["status"].startswith("identical")
    assert REP.analyse_replication(games, dec, labels, ids, None, b=50)["sensitivity"]["status"].startswith("not run")
    with pytest.raises(REP.ReplicationError):
        REP.analyse_replication(games, dec, labels, ids, ["g_unknown"], b=50)


def test_read_quality_fail_formats(tmp_path):
    (tmp_path / "a.json").write_text('["g_b", "g_a"]', encoding="utf-8")
    (tmp_path / "b.json").write_text('{"quality_fail": []}', encoding="utf-8")
    (tmp_path / "c.json").write_text('{"quality_fail": [1]}', encoding="utf-8")
    assert REP.read_quality_fail(tmp_path / "a.json") == ["g_a", "g_b"]
    assert REP.read_quality_fail(tmp_path / "b.json") == [] and REP.read_quality_fail(None) is None
    with pytest.raises(REP.ReplicationError):
        REP.read_quality_fail(tmp_path / "c.json")


# --------------------------------------------------------------------------- refusals

def test_prereg_refusals(tmp_path):
    real = REPO_ROOT / REP.PREREG
    assert REP.check_prereg() == REP.PREREG_SHA256                                   # committed and unchanged
    with pytest.raises(REP.ReplicationError):
        REP.check_prereg(real, "0" * 64)                                             # wrong sha
    with pytest.raises(REP.ReplicationError):
        REP.check_prereg(tmp_path / "missing.md")
    with pytest.raises(REP.ReplicationError):                                        # differs from the blob
        REP.check_prereg(real, blob=lambda: b"something else")
    assert REP.check_prereg(real, blob=lambda: real.read_bytes().replace(b"\n", b"\r\n"))   # CRLF blob is fine


def test_apply_refuses_wrong_sha_and_dev_ids():
    with pytest.raises(R.FrozenError):
        REP.apply(REPO_ROOT / REP.FROZEN, "0" * 64, {}, [], "judge_v1")
    with pytest.raises(REP.ReplicationError):
        REP.apply(REPO_ROOT / REP.FROZEN, REP.FROZEN_SHA256, {}, FROZEN_DOC["dev_ids"][:1], "judge_v1")


# --------------------------------------------------------------------------- baseline: loaded, never refit

def test_frozen_baseline_is_loaded_not_refit(monkeypatch):
    base = REP.frozen_baseline(FROZEN_DOC)
    assert (base.mu_pair, base.sd_pair, base.n_pairs) == (FROZEN_DOC["honest_baseline"]["mu_pair"],
                                                           FROZEN_DOC["honest_baseline"]["sd_pair"], 40)
    monkeypatch.setattr(S, "fit_honest_baseline", lambda *a, **k: pytest.fail("baseline refit"))
    acts = [{"J": "GO", "M": "GO", "Q": "STAY", "T": "STAY", "Z": "STAY"}] * 8
    g = REP.build_games({"g_x": _clean("g_x", acts)}, {}, base)["g_x"]
    jm = next(r for r in g if r["pair"] == "J-M")
    assert jm["G_honest"] == pytest.approx((10 - base.mu_pair) / max(base.sd_pair, 1.0))
    assert all(r["C_judge"] is None and r["C_judge_flag"] == "no_judge_line" for r in g)


# --------------------------------------------------------------------------- end to end (synthetic games, real frozen file)

def _write_set(tmp_path, n=16, seed=5, digest=None):
    rng = random.Random(seed)
    agents = ["J", "M", "Q", "T", "Z"]
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    lab = ["game_id,episode_type,collusion,focal_pair,variant,synthetic"]
    judge = []
    for k in range(n):
        gid = f"g_r{k:09d}"
        et = (1, 1, 2, 3, 1, 1, 4, 2)[k % 8]
        acts = []
        for _ in range(8):
            a = {x: rng.choice(["GO", "STAY", "STAY"]) for x in agents}
            if et == 1:
                a["M"] = a["T"] = "GO"
                for x in "JQZ":
                    a[x] = "STAY"
            acts.append(a)
        (clean_dir / f"{gid}.json").write_text(json.dumps(_clean(gid, acts)), encoding="utf-8")
        lab.append(f"{gid},{et},{int(et == 1)},M|T,v,false")
        if k == 0:
            continue                                                                 # one missing judge line
        ps = {p: rng.randint(0, 98) for p in PAIRS}
        judge.append({"game_id": gid, "sample_idx": 0, "prompt_version": "judge_v1",
                      "digest": digest or FROZEN_DOC["judge"]["digest"][0], "pair_scores": ps})
    (tmp_path / "labels.csv").write_text("\n".join(lab) + "\n", encoding="utf-8")
    jp = tmp_path / "judge.jsonl"
    jp.write_text("".join(json.dumps(x) + "\n" for x in judge), encoding="utf-8")
    return ["--clean-dir", str(clean_dir), "--labels", str(tmp_path / "labels.csv"), "--judge", str(jp),
            "--out", str(tmp_path / "out")]


def test_script_end_to_end_and_refusals(tmp_path, monkeypatch, capsys):
    from scripts import analyse_replication_23 as A
    monkeypatch.setattr(S, "fit_honest_baseline", lambda *a, **k: pytest.fail("baseline refit"))
    args = _write_set(tmp_path)
    q = tmp_path / "quality.json"
    q.write_text('{"quality_fail": ["g_r000000003"]}', encoding="utf-8")
    assert A.main([*args, "--frozen-sha256", "0" * 64]) == 2 and not (tmp_path / "out").exists()
    assert A.main([*args, "--prereg-sha256", "0" * 64]) == 2 and not (tmp_path / "out").exists()
    assert A.main([*args, "--quality", str(q)]) == 0
    res = json.loads((tmp_path / "out" / "results.json").read_text(encoding="utf-8"))
    assert res["inputs"]["honest_baseline"] == FROZEN_DOC["honest_baseline"]
    assert res["inputs"]["judge_missing"] == ["g_r000000000"] and res["primary"]["n"] == 16
    assert res["primary"]["n_score_na"]["R1"] == 1 and res["sensitivity"]["n"] == 15
    assert {res["primary"][e]["verdict"] for e in ("E1", "E2", "E3", "E3b")} <= {
        "confirmed", "not confirmed", "confirmed (below chance)", "replicated", "not replicated", "reversed"}
    assert res["primary"]["E1"]["verdict"] == "confirmed"                            # M-T gain separates by design
    rows = list(csv.DictReader(open(tmp_path / "out" / "decisions.csv", encoding="utf-8")))
    assert len(rows) == 16 and "R6_no_E4_points" in rows[0]
    assert A.main([*args, "--quality", str(q)]) == 2                                 # analysed once
    assert "REFUSED" in capsys.readouterr().out


def test_script_refuses_foreign_judge_digest(tmp_path):
    from scripts import analyse_replication_23 as A
    args = _write_set(tmp_path, digest="f" * 64)
    assert A.main(args) == 2 and not (tmp_path / "out").exists()


# --------------------------------------------------------------------------- earlier behaviour: report 17C reproduced

P17 = REPO_ROOT / "runs" / "study23"
NEEDED = [REPO_ROOT / "data/clean", REPO_ROOT / "data/labels.csv", REPO_ROOT / "data/split.json",
          REPO_ROOT / "runs/judge_v1/outputs/judge.jsonl", P17 / "test_decisions.csv", P17 / "results.json"]


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="17C local outputs not on this machine")
def test_reproduces_17c_test_tables():
    from core.labels import read_labels
    from study_2_3_evidence.judge import load_judge
    labels = {lb.game_id: lb for lb in read_labels(REPO_ROOT / "data/labels.csv")}
    test = sorted(load_json(REPO_ROOT / "data/split.json")["test"])
    judge = load_judge(REPO_ROOT / "runs/judge_v1/outputs/judge.jsonl", 0)
    clean = {g: load_json(REPO_ROOT / "data/clean" / f"{g}.json") for g in test}
    games = REP.build_games(clean, judge, REP.frozen_baseline(FROZEN_DOC))
    _, dec = REP.apply(REPO_ROOT / REP.FROZEN, REP.FROZEN_SHA256, games, test, "judge_v1")
    with open(P17 / "test_decisions.csv", encoding="utf-8") as f:
        old = {r["game_id"]: r for r in csv.DictReader(f)}
    for g in test:                                                                    # every flag and score as in 17C
        for r, d in dec[g].items():
            assert int(old[g][f"{r}_flag"]) == d["flag"], (g, r)
            for k in ("score", "points", "prob"):
                if k in d:
                    v = old[g][f"{r}_{k}"]
                    assert (None if v == "" else float(v)) == pytest.approx(d[k]), (g, r, k)
    out = REP.analyse_set(games, dec, labels, test)
    r17 = json.loads((P17 / "results.json").read_text(encoding="utf-8"))
    for r in ("R1", "R2", "R3", "R6", "R7"):                                          # AUROC + CI, exactly
        for k in ("estimate", "ci_low", "ci_high"):
            assert out["auroc"][r][k] == pytest.approx(r17["rules"][r]["auroc"][k], abs=1e-12), (r, k)
    for k in ("estimate", "ci_low", "ci_high"):                                       # RQ-E3 R6 - R2
        assert out["E3"][k] == pytest.approx(r17["rq_e3"]["auroc_diff"][k], abs=1e-12)
    assert out["E3"]["verdict"] == "not replicated"                                   # 17C: "no clear difference"
    for r in R.RULES:                                                                 # per-type k/n tables
        for t, v in out["flags"][r]["per_type"].items():
            assert (v["k"], v["n"]) == (r17["rules"][r]["per_type"][t]["k"], r17["rules"][r]["per_type"][t]["n"])
    pf = r17["exploratory_plus_factor"]["plus_factor_rule"]
    assert out["plus_factor_secondary"]["per_type"] == {t: {**v} for t, v in pf["per_type"].items()}
    assert (out["auroc"]["R2"]["estimate"], round(out["auroc"]["R1"]["estimate"], 3)) == \
        (pytest.approx(0.872, abs=5e-4), 0.396)                                       # report 17C §4.1


# --------------------------------------------------------------------------- machine-C wrapper (no model calls)

def test_wrapper_plan_and_refusals(tmp_path, monkeypatch, capsys):
    from scripts import run_replication_c as W
    args = ["--clean", str(tmp_path / "clean"), "--views", str(tmp_path / "views"),
            "--labels", str(tmp_path / "labels.csv"), "--quality", str(tmp_path / "q.json")]
    monkeypatch.setattr(W, "amendment_committed", lambda: False)
    assert W.main(args) == 0
    out = capsys.readouterr().out
    assert "48 calls" in out and "192 calls" in out and "NO - not allowed yet" in out and "run_monitor.py" not in out
    monkeypatch.setenv("COLLUSION_LAB_MACHINE", "B")
    assert W.main([*args, "--run", "judge", "--yes"]) == 2                          # judge only on machine C
    monkeypatch.setenv("COLLUSION_LAB_MACHINE", "C")
    assert W.main([*args, "--run", "judge", "--yes"]) == 2                          # no labels file
    monkeypatch.setattr(REP, "check_prereg", lambda *a, **k: (_ for _ in ()).throw(REP.ReplicationError("x")))
    assert W.main(args) == 2                                                         # prereg must match its blob
