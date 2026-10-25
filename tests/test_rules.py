"""Tests for study_2_3_evidence.rules (R1-R7 fit on dev, freeze, refusal, ablation) and scripts/analyse_23.py.

Synthetic data only; no model calls.
"""
import json
import random

import numpy as np
import pytest

from study_2_3_evidence import rules as R

PAIRS = ["J-M", "J-Q", "J-T", "J-Z", "M-Q", "M-T", "M-Z", "Q-T", "Q-Z", "T-Z"]
SIGS = ("C_judge", "G_others", "Dep", "W_joint", "coGO", "D_react", "D_private")


def game(top=None, base=0.0, na=(), **sig_top):
    """10 pair rows; every signal = base (+ small pair offset) except `top` pair gets sig_top values."""
    rows = []
    for i, p in enumerate(PAIRS):
        r = {"game_id": "g", "pair": p}
        for s in SIGS:
            r[s] = None if s in na else base + 0.001 * i
        if p == top:
            r.update(sig_top)
        rows.append(r)
    return rows


def synthetic(n_dev=12, n_test=12, seed=0):
    """Positives: one pair high on every family (noisy); negatives: one pair high on G_others/coGO only (lookalike)."""
    rng = random.Random(seed)
    games, labels, types, dev, test = {}, {}, {}, [], []
    for k in range(n_dev + n_test):
        gid = f"g_{k:03d}"
        pos = k % 2 == 0
        top = PAIRS[k % 10]
        if pos:
            rows = game(top, C_judge=60 + rng.randint(0, 30), G_others=3 + rng.random() * 4, Dep=1 + rng.random(),
                        W_joint=0.1 + rng.random() * 0.1, coGO=0.8, D_react=0.3, D_private=0.2)
        else:
            rows = game(top, C_judge=10 + rng.randint(0, 40), G_others=rng.random() * 4, Dep=rng.random() * 1.2,
                        W_joint=rng.random() * 0.12, coGO=0.5 + rng.random() * 0.4, D_react=0.1, D_private=0.05)
        games[gid] = rows
        labels[gid] = int(pos)
        types[gid] = 1 if pos else 2 + k % 3
        (dev if k < n_dev else test).append(gid)
    return games, labels, types, dev, test


# --------------------------------------------------------------------------- pieces

def test_game_max_argmax_and_ties():
    rows = game("M-T", C_judge=90)
    assert R.game_max(rows, "C_judge") == 90 and R.argmax_pair(rows, "C_judge") == "M-T"
    rows = game("M-T", C_judge=90)
    rows[0]["C_judge"] = 90
    assert R.argmax_pair(rows, "C_judge") is None
    assert R.game_max(game(na=("C_judge",)), "C_judge") is None


def test_single_threshold_max_ba_ties_go_higher():
    # scores 10,20 neg; 20,30 pos. thr 20: TPR 1, FPR .5 (BA .75); thr 30: TPR .5, FPR 0 (BA .75) -> higher (30)
    games = {f"g{i}": game("M-T", C_judge=v) for i, v in enumerate((10, 20, 20, 30))}
    labels = {"g0": 0, "g1": 0, "g2": 1, "g3": 1}
    f = R.fit_single(games, labels, sorted(games), "C_judge")
    assert f["threshold"] == 30 and f["dev_fit"]["balanced_accuracy"] == 0.75


def test_single_threshold_skips_na_games_and_counts_them():
    games = {"a": game("M-T", C_judge=10), "b": game("M-T", C_judge=80), "c": game(na=("C_judge",))}
    f = R.fit_single(games, {"a": 0, "b": 1, "c": 1}, ["a", "b", "c"], "C_judge")
    assert f["n_used"] == 2 and f["n_na"] == 1 and f["threshold"] == 80


def test_plus_threshold_is_90th_percentile_of_dev_negative_game_max():
    vals = [5, 1, 9, 3, 7, 2, 8, 4, 6, 10]
    games = {f"n{i}": game("J-M", W_joint=v) for i, v in enumerate(vals)}
    games["p"] = game("J-M", W_joint=100)                       # positive: must not enter
    labels = {**{g: 0 for g in games}, "p": 1}
    plus = R.fit_plus(games, labels, sorted(games), ["W_joint"])
    assert plus["W_joint"]["threshold"] == pytest.approx(float(np.percentile(vals, 90)))
    assert plus["W_joint"]["n_neg_used"] == 10


def test_plus_factor_needs_strictly_greater():
    plus = {"C_judge": {"threshold": 50.0, "neg_values": [50.0]}}
    assert R.pair_points({"C_judge": 50}, plus, ["E1"]) == 0
    assert R.pair_points({"C_judge": 51}, plus, ["E1"]) == 1
    assert R.pair_points({"C_judge": None}, plus, ["E1"]) == 0


def test_best_pair_points_then_percentile_then_tie_none():
    plus = {s: {"threshold": 0.5, "neg_values": [0.0, 0.5, 1.0]} for s in R.FAMILIES.values()}
    rows = game(base=0.0)
    rows[3].update({"C_judge": 0.9, "G_others": 0.9})        # 2 points
    rows[7].update({"C_judge": 0.9})                          # 1 point
    pair, _, pts = R.best_pair(rows, plus, list(R.FAMILIES))
    assert (pair, pts) == ("J-Z", 2)
    rows[7].update({"G_others": 0.9})                         # now same points AND same percentiles -> tie
    pair, used, pts = R.best_pair(rows, plus, list(R.FAMILIES))
    assert pair is None and pts == 2 and used["pair"] == "J-Z"   # features from the first pair in fixed order


def test_r6_k_ties_go_higher():
    plus = {s: {"threshold": 0.0, "neg_values": [0.0]} for s in R.FAMILIES.values()}
    # every positive has 4 points, every negative 0 -> k = 1..4 all BA 1.0 -> k = 4
    games = {"p": game("M-T", base=-1, C_judge=1, G_others=1, Dep=1, W_joint=1), "n": game(base=-1)}
    k = R.fit_k(games, {"p": 1, "n": 0}, ["n", "p"], plus, list(R.FAMILIES))
    assert k["k"] == 4 and k["balanced_accuracy"] == 1.0


def test_logreg_is_l2_optimum():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(30, 3))
    y = (X[:, 0] + 0.5 * rng.normal(size=30) > 0).astype(float)
    C = 0.7
    w, b = R.fit_logreg(X, y, C)
    p = 1 / (1 + np.exp(-(X @ w + b)))
    assert np.allclose(X.T @ (p - y) + w / C, 0, atol=1e-8)   # penalised gradient = 0
    assert abs(np.sum(p - y)) < 1e-8                          # intercept not penalised
    w2, _ = R.fit_logreg(X, y, 100.0)
    assert np.linalg.norm(w) < np.linalg.norm(w2)             # smaller C shrinks more


def test_r7_c_tie_goes_to_smaller_c_and_constant_features():
    games = {f"g{i}": game(base=1.0) for i in range(6)}       # identical features -> all C equal loss
    labels = {g: i % 2 for i, g in enumerate(sorted(games))}
    r7 = R.fit_r7(games, labels, sorted(games), list(R.FAMILIES))
    assert r7["C"] == min(R.C_GRID)


def test_r7_loo_refits_without_the_held_out_game(monkeypatch):
    games, labels, _, dev, _ = synthetic()
    seen = []
    orig = R._fit_r7_pipeline

    def spy(g, l, ids, fams, C):
        seen.append(tuple(ids))
        return orig(g, l, ids, fams, C)
    monkeypatch.setattr(R, "_fit_r7_pipeline", spy)
    R.fit_r7(games, labels, dev, list(R.FAMILIES))
    loo = [s for s in seen if len(s) == len(dev) - 1]
    assert len(loo) == len(dev) * len(R.C_GRID)
    assert all(sorted(dev)[i % len(dev)] not in s for i, s in enumerate(loo))


# --------------------------------------------------------------------------- rules on games

def _params(**single):
    th = {"R1": 50, "R2": 2.0, "R3": 1.0, "par": 0.7}
    th.update(single)
    plus = {s: {"threshold": t, "neg_values": [0.0]} for s, t in
            {"C_judge": 50, "G_others": 2.0, "Dep": 1.0, "W_joint": 0.1, "D_react": 0.2, "D_private": 0.1}.items()}
    return {"families": list(R.FAMILIES), "single": {k: {"threshold": v} for k, v in th.items()}, "plus": plus,
            "R6": {"k": 2}, "R7": {"families": list(R.FAMILIES), "plus": plus, "mean": [0] * 4, "sd": [1] * 4,
                                    "coef": [0.0] * 4, "intercept": 0.0, "flag_p": 0.5}}


def test_r1_r2_r3_flags_and_na():
    p = _params()
    d = R.apply_rules(p, game("M-T", C_judge=50, G_others=1.0, Dep=0.5))
    assert d["R1"] == {"flag": 1, "pair": "M-T", "score": 50}      # >= tau flags
    assert d["R2"]["flag"] == 0 and d["R3"]["flag"] == 0
    assert R.apply_rules(p, game(na=("C_judge",)))["R1"]["flag"] == 0


def test_r4_needs_parallel_conduct_and_a_plus_factor_on_the_same_pair():
    p = _params()
    assert R.apply_rules(p, game("M-T", coGO=0.9))["R4"]["flag"] == 0          # parallel conduct only
    rows = game("M-T", coGO=0.9)
    rows[0]["D_private"] = 0.5                                                   # plus factor on ANOTHER pair
    assert R.apply_rules(p, rows)["R4"]["flag"] == 0
    d = R.apply_rules(p, game("M-T", coGO=0.9, D_react=0.3))["R4"]
    assert d["flag"] == 1 and d["pair"] == "M-T"


def test_r5_needs_the_same_pair():
    p = _params()
    rows = game(base=0.0)
    rows[1]["G_others"] = 3.0            # J-Q passes tau_2 only
    rows[5]["Dep"] = 2.0                 # M-T passes tau_3 only
    assert R.apply_rules(p, rows)["R5"]["flag"] == 0
    rows[5]["G_others"] = 2.5
    d = R.apply_rules(p, rows)["R5"]
    assert d["flag"] == 1 and d["pair"] == "M-T"


def test_r6_points_threshold():
    p = _params()
    one = R.apply_rules(p, game("M-T", C_judge=90))["R6"]
    two = R.apply_rules(p, game("M-T", C_judge=90, W_joint=0.2))["R6"]
    assert (one["flag"], one["points"]) == (0, 1)
    assert (two["flag"], two["points"], two["pair"]) == (1, 2, "M-T")


# --------------------------------------------------------------------------- fit / freeze / apply

def test_fit_reads_dev_only():
    games, labels, _, dev, test = synthetic()
    a = R.fit_rules(games, labels, dev)
    games2 = {g: (rows if g in dev else game("J-M", C_judge=100, G_others=99, Dep=99, W_joint=9, coGO=1))
              for g, rows in games.items()}
    labels2 = {g: (y if g in dev else 1 - y) for g, y in labels.items()}
    b = R.fit_rules(games2, labels2, dev)
    assert json.dumps(R._jsonable(a), sort_keys=True) == json.dumps(R._jsonable(b), sort_keys=True)


def test_synthetic_fit_separates_dev():
    games, labels, types, dev, _ = synthetic()
    params = R.fit_rules(games, labels, dev)
    abl = R.fit_ablations(games, labels, dev, params["plus"])
    rep = R.dev_report(params, abl, games, labels, types, dev)
    assert rep["R1"]["balanced_accuracy"] >= 0.75
    assert 1 <= params["R6"]["k"] <= 4 and params["R7"]["C"] in R.C_GRID
    assert set(abl) == {"no_E1", "no_E2", "no_E3", "no_E4"}
    for name, a in abl.items():
        assert name[3:] not in a["families"] and len(a["families"]) == 3
        assert 1 <= a["R6"]["k"] <= 3 and len(a["R7"]["coef"]) == 3
    assert rep["R7"]["source"] == "leave-one-out"


def test_ablation_without_e1_ignores_the_judge():
    games, labels, _, dev, test = synthetic()
    params = R.fit_rules(games, labels, dev)
    abl = R.fit_ablations(games, labels, dev, params["plus"])["no_E1"]
    g = test[0]
    changed = [dict(r, C_judge=(0 if r["C_judge"] is None else 100 - r["C_judge"])) for r in games[g]]
    assert R.apply_ablation(abl, params["plus"], games[g]) == R.apply_ablation(abl, params["plus"], changed)


def _freeze(tmp_path):
    games, labels, types, dev, test = synthetic()
    params = R.fit_rules(games, labels, dev)
    abl = R.fit_ablations(games, labels, dev, params["plus"])
    path = tmp_path / "rules_frozen.json"
    sha = R.write_frozen({"params": params, "ablations": abl, "judge": {"prompt_version": "judge_v1"}}, path)
    return games, test, path, sha


def test_frozen_apply_refuses_without_matching_sha(tmp_path):
    games, test, path, sha = _freeze(tmp_path)
    for fp, s in ((None, sha), (path, None), (path, "0" * 64), (tmp_path / "missing.json", sha)):
        with pytest.raises(R.FrozenError):
            R.apply_frozen(fp, s, games, test)
    with pytest.raises(R.FrozenError):
        R.apply_frozen(path, sha, games, test, judge_prompt_version="judge_v2")
    out = R.apply_frozen(path, sha, games, test, judge_prompt_version="judge_v1")
    assert sorted(out) == sorted(test)
    assert set(out[test[0]]) == set(R.RULES) | {f"R{n}_no_E{e}" for n in (6, 7) for e in range(1, 5)}


def test_frozen_file_edit_is_refused_and_overwrite_refused(tmp_path):
    games, test, path, sha = _freeze(tmp_path)
    with pytest.raises(FileExistsError):
        R.write_frozen({"params": {}}, path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["params"]["R6"]["k"] = 1
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(R.FrozenError):
        R.apply_frozen(path, sha, games, test)


def test_frozen_sha_ignores_line_endings(tmp_path):
    _, _, path, sha = _freeze(tmp_path)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert R.file_sha256(path) == sha


def test_frozen_apply_equals_in_memory_apply(tmp_path):
    games, test, path, sha = _freeze(tmp_path)
    doc = R.load_frozen(path, sha)
    out = R.apply_frozen(path, sha, games, test)
    for g in test:
        mem = R.apply_rules(doc["params"], games[g])
        assert {r: out[g][r]["flag"] for r in R.RULES} == {r: mem[r]["flag"] for r in R.RULES}


# --------------------------------------------------------------------------- analyse_23 end to end (synthetic)

def _clean(gid, actions_by_round, msgs=None):
    agents = ["J", "M", "Q", "T", "Z"]
    rounds = []
    for r, acts in enumerate(actions_by_round, start=1):
        n_go = sum(a == "GO" for a in acts.values())
        pay = {a: ((10 if n_go < 2.5 else -5) if acts[a] == "GO" else 0) for a in agents}
        rounds.append({"round": r, "valid": True, "actions": acts, "payoffs_public": pay, "announcements": [
            {"agent": a, "position": i, "stated_action": acts[a], "message": (msgs or {}).get(a, f"hi {r}")}
            for i, a in enumerate(agents)]})
    return {"game_id": gid, "agents": agents, "n_rounds": len(rounds), "rules_text": "RULES", "rounds": rounds,
            "leak_scan": {"hits": 0, "redactions": 0}}


def test_analyse_23_fit_writes_frozen_and_test_refuses(tmp_path, capsys):
    from scripts import analyse_23
    rng = random.Random(3)
    agents = ["J", "M", "Q", "T", "Z"]
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    lab_lines = ["game_id,episode_type,collusion,focal_pair,variant,synthetic"]
    dev, test, judge = [], [], []
    for k in range(16):
        gid = f"g_{k:010d}"
        et = (1, 1, 2, 3)[k % 4] if k % 8 < 4 else (1, 1, 2, 4)[k % 4]
        acts = []
        for _ in range(8):
            a = {x: rng.choice(["GO", "STAY", "STAY"]) for x in agents}
            if et == 1:
                a["M"] = a["T"] = rng.choice(["GO", "GO", "STAY"])
            acts.append(a)
        (clean_dir / f"{gid}.json").write_text(json.dumps(_clean(gid, acts)), encoding="utf-8")
        lab_lines.append(f"{gid},{et},{int(et == 1)},M|T,v,false")
        (dev if k < 8 else test).append(gid)
        for s in (0, 1):
            ps = {p: rng.randint(0, 30) for p in PAIRS}
            if et == 1:
                ps["M-T"] = 70 + rng.randint(0, 20)
            judge.append({"game_id": gid, "sample_idx": s, "prompt_version": "judge_v1", "digest": "d",
                          "pair_scores": ps, "score": max(ps.values()), "top_pair": [], "parse_ok": True,
                          "truncation_suspect": False, "done_reason": "stop", "latency": 1.0,
                          "prompt_eval_count": 900, "eval_count": 120})
    (tmp_path / "labels.csv").write_text("\n".join(lab_lines) + "\n", encoding="utf-8")
    (tmp_path / "split.json").write_text(json.dumps({"dev": dev, "test": test, "labels_sha256": "x"}),
                                         encoding="utf-8")
    jp = tmp_path / "judge.jsonl"
    jp.write_text("".join(json.dumps(x) + "\n" for x in judge), encoding="utf-8")
    common = ["--clean-dir", str(clean_dir), "--labels", str(tmp_path / "labels.csv"),
              "--split", str(tmp_path / "split.json"), "--judge", str(jp), "--out", str(tmp_path / "res")]
    frozen = tmp_path / "rules_frozen.json"
    assert analyse_23.main(["--mode", "test", *common]) == 2                       # no frozen file -> refused
    assert not (tmp_path / "res").exists()
    assert analyse_23.main(["--mode", "fit", *common, "--frozen-out", str(frozen)]) == 0
    sha = capsys.readouterr().out.strip().splitlines()[-1].split()[-1]
    assert sha == R.file_sha256(frozen)
    doc = json.loads(frozen.read_text(encoding="utf-8"))
    assert doc["dev_ids"] == sorted(dev) and doc["judge"]["sample_idx_used"] == 0
    assert doc["judge_dev"]["stability_dev"]["n_games_both_ok"] == 8
    pair_csv = (tmp_path / "res" / "pair_signals.csv").read_text(encoding="utf-8").splitlines()
    assert len(pair_csv) == 1 + 16 * 10 and "C_judge" in pair_csv[0] and "G_honest" in pair_csv[0]
    assert analyse_23.main(["--mode", "test", *common, "--frozen", str(frozen), "--frozen-sha256", "0" * 64]) == 2
    with pytest.raises(FileExistsError):                                            # frozen once, never rewritten
        analyse_23.main(["--mode", "fit", *common, "--frozen-out", str(frozen)])
