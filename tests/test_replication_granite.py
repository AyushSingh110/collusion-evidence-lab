"""Tests for the amendment-1 analysis (study_2_2_views.replication_granite, scripts/analyse_replication_granite.py).

Synthetic data only, except test_reproduces_15c_aurocs, which re-derives report 15C's granite AUROCs from the local
RQ9 output (skipped where it is absent).
"""
import json
import random
from argparse import Namespace
from pathlib import Path

import pytest

from core.config import REPO_ROOT, sha256_of
from study_2_2_views import replication_granite as RG
from study_2_2_views.analysis import load_labels
from study_2_2_views.monitor import PROMPTS, load_config, system_prompt

PAIRS = ["J-M", "J-Q", "J-T", "J-Z", "M-Q", "M-T", "M-Z", "Q-T", "Q-Z", "T-Z"]
CFGS = {m: load_config(manifest=PROMPTS[p]) for m, (p, _) in RG.MONITORS.items()}


def ci(lo, hi, est=None):
    return {"estimate": (lo + hi) / 2 if est is None else est, "ci_low": lo, "ci_high": hi}


# --------------------------------------------------------------------------- decision rules: every branch

@pytest.mark.parametrize("c,want", [(ci(0.51, 0.9), "confirmed"), (ci(0.5, 0.9), "not confirmed"),
                                    (ci(0.3, 0.7), "not confirmed"), (ci(0.1, 0.45), "not confirmed"),
                                    ({"ci_low": None, "ci_high": None}, RG.UNDETERMINED)])
def test_g1_branches(c, want):
    assert RG.G1(c) == want


@pytest.mark.parametrize("c,want", [(ci(0.3, 0.7), "confirmed"), (ci(0.5, 0.8), "confirmed"),
                                    (ci(0.2, 0.5), "confirmed"), (ci(0.55, 0.9), "not confirmed"),
                                    (ci(0.1, 0.49), "not confirmed (below chance)")])
def test_g2_branches(c, want):
    assert RG.G2(c) == want


@pytest.mark.parametrize("c,want", [(ci(-0.2, 0.2), "confirmed"), (ci(0.0, 0.3), "confirmed"),
                                    (ci(-0.3, 0.0), "confirmed"), (ci(0.01, 0.3), "not confirmed"),
                                    (ci(-0.3, -0.01), "not confirmed")])
def test_g4_branches(c, want):
    assert RG.G4(c) == want


@pytest.mark.parametrize("dl,dg,want", [
    (ci(0.1, 0.5), ci(-0.4, 0.1), "confirmed"),            # opposite signs, llama CI excludes 0
    (ci(-0.1, 0.3), ci(-0.5, -0.1), "confirmed"),          # opposite signs, granite CI excludes 0
    (ci(-0.1, 0.3), ci(-0.4, 0.1), "not confirmed"),       # opposite signs, both CIs include 0
    (ci(0.0, 0.4), ci(-0.4, 0.0), "not confirmed"),        # CIs touch 0 exactly: neither excludes 0
    (ci(0.1, 0.5), ci(0.05, 0.4), "not confirmed"),        # same sign
    (ci(-0.2, 0.2, est=0.0), ci(-0.5, -0.1), "not confirmed"),   # a zero estimate has no sign
    ({"estimate": None, "ci_low": None, "ci_high": None}, ci(-0.5, -0.1), RG.UNDETERMINED),
])
def test_g3_branches(dl, dg, want):
    assert RG.verdict_g3(dl, dg) == want


# --------------------------------------------------------------------------- synthetic monitor lines

def labels_of(n_per=6):
    labels, k = {}, 0
    for t in (1, 1, 1, 2, 3, 4):
        for _ in range(n_per):
            labels[f"g_x{k:08d}"] = {"type": t, "y": int(t == 1), "focal": ["M", "T"]}
            k += 1
    return labels


def line(monitor, g, v, score, pair_scores=None, **kw):
    cfg = CFGS[monitor]
    ps = pair_scores or {p: (score if p == "M-T" else 0) for p in PAIRS}
    d = {"game_id": g, "view": v, "sample_idx": 0, "prompt_version": RG.MONITORS[monitor][0], "model": cfg.model,
         "digest": RG.MONITORS[monitor][1], "prompt_sha256": sha256_of(system_prompt(cfg, v)), "score": score,
         "pair_scores": ps, "suspected_pair": ["M", "T"] if score else [], "parse_ok": True,
         "truncation_suspect": False}
    d.update(kw)
    return d


def lines_from(labels, monitor, fn, views=RG.VIEWS, seed=0):
    rng = random.Random(seed)
    return {(g, v): line(monitor, g, v, fn(v, lab["type"], rng)) for g, lab in labels.items() for v in views}


def sep(v, t, r):
    return 90 if t == 1 else r.choice([0, 10, 20])


def noise(v, t, r):
    return r.choice([0, 30, 60, 90])


def test_hypotheses_all_confirmed():
    labels = labels_of()
    games = sorted(labels)
    granite = lines_from(labels, "granite", lambda v, t, r: sep(v, t, r) if v in ("V2", "V3") else noise(v, t, r))
    llama = lines_from(labels, "llama", lambda v, t, r: sep(v, t, r) if v in ("V3", "V4") else noise(v, t, r), seed=1)
    h = RG.hypotheses(games, llama, granite, labels, b=300)
    assert h["G1"]["verdict"] == "confirmed" and h["G1"]["estimate"] == 1.0
    assert h["G2"]["verdict"] == "confirmed"
    assert h["G3"]["D_llama"]["estimate"] > 0 > h["G3"]["D_granite"]["estimate"]
    assert h["G3"]["verdict"] == "confirmed"
    assert h["G4"]["verdict"] == "confirmed" and h["G4"]["estimate"] == 0.0


def test_hypotheses_not_confirmed_and_below_chance():
    labels = labels_of()
    games = sorted(labels)
    inv = lambda v, t, r: 0 if t == 1 else 90                                       # noqa: E731
    granite = lines_from(labels, "granite", lambda v, t, r: inv(v, t, r) if v == "V4" else 50)   # V2, V3 constant
    llama = lines_from(labels, "llama", lambda v, t, r: sep(v, t, r) if v == "V3" else noise(v, t, r), seed=2)
    h = RG.hypotheses(games, llama, granite, labels, b=300)
    assert (h["G1"]["estimate"], h["G1"]["ci_low"], h["G1"]["ci_high"]) == (0.5, 0.5, 0.5)
    assert h["G1"]["verdict"] == "not confirmed"                                     # CI touches 0.5: not above
    assert h["G2"]["verdict"] == "not confirmed (below chance)"
    assert h["G4"]["verdict"] == "not confirmed"                                     # granite V3 noise vs llama V3 perfect


def test_paired_indices_shared_between_monitors():
    labels = labels_of()
    games = sorted(labels)
    same = lines_from(labels, "llama", noise, seed=7)
    gran = {k: line("granite", k[0], k[1], d["score"]) for k, d in same.items()}
    h = RG.hypotheses(games, same, gran, labels, b=300)
    assert (h["G4"]["estimate"], h["G4"]["ci_low"], h["G4"]["ci_high"]) == (0.0, 0.0, 0.0)   # same indices both arms
    dl, dg = h["G3"]["D_llama"], h["G3"]["D_granite"]
    assert (dl["estimate"], dl["ci_low"], dl["ci_high"]) == (dg["estimate"], dg["ci_low"], dg["ci_high"])


def test_missing_scores_are_dropped_and_counted():
    labels = labels_of()
    games = sorted(labels)
    granite = lines_from(labels, "granite", sep)
    llama = lines_from(labels, "llama", sep, seed=3)
    granite[(games[0], "V2")]["score"] = None                                       # parse failure
    del llama[(games[1], "V3")]                                                      # persistent transport error
    h = RG.hypotheses(games, llama, granite, labels, b=100)
    assert h["G1"]["dropped"] == 1 and h["G1"]["n"] == len(games) - 1
    assert h["G3"]["dropped"] == 1 and h["G4"]["dropped"] == 1
    d = RG.descriptive(games, llama, labels, b=50)
    assert d["V3"]["absent"] == 1 and d["V3"]["lines"] == len(games) - 1


def test_descriptive_lpm_ties_scores_top1():
    labels = labels_of(n_per=2)
    games = sorted(labels)
    lines = {}
    for g in games:
        tz = {p: (80 if p == "T-Z" else 10) for p in PAIRS}                         # T-Z strict top
        tie = {p: 0 for p in PAIRS}                                                   # all equal
        lines[(g, "V1")] = line("granite", g, "V1", 80, tz, suspected_pair=["T", "Z"])
        lines[(g, "V2")] = line("granite", g, "V2", 0, tie)
        lines[(g, "V3")] = line("granite", g, "V3", 90)
        lines[(g, "V4")] = line("granite", g, "V4", 50)
    d = RG.descriptive(games, lines, labels, b=50)
    assert d["V1"]["last_position_max"] == {"k": 12, "n": 12, "share": 1.0, "no_bias_expectation": 0.1,
                                            "named_T_Z": 12}
    assert d["V2"]["last_position_max"]["share"] == 1.0 and d["V2"]["last_position_max"]["no_bias_expectation"] == 1.0
    assert d["V2"]["scores"]["share_all_pairs_equal"] == 1.0 and d["V2"]["scores"]["share_0"] == 1.0
    assert d["V3"]["top1"]["correct"] == 6 and d["V1"]["top1"]["correct"] == 0     # 6 Type 1 games, focal M-T
    assert d["V2"]["top1"]["no_pair"] == 6
    assert d["V4"]["scores"]["distinct_game_scores"] == [50] and d["V4"]["auroc"]["estimate"] == 0.5


# --------------------------------------------------------------------------- refusals (CLI run)

def _setup(tmp_path, mutate=None, views=RG.VIEWS, original_ids=()):
    labels = labels_of(n_per=2)
    lab = ["game_id,episode_type,collusion,focal_pair,variant,synthetic"] + \
          [f"{g},{d['type']},{d['y']},M|T,v,false" for g, d in labels.items()]
    (tmp_path / "labels.csv").write_text("\n".join(lab) + "\n", encoding="utf-8")
    orig = ["game_id,episode_type,collusion,focal_pair,variant,synthetic"] + \
           [f"{g},2,0,M|T,v,false" for g in (original_ids or ["g_orig000001"])]
    (tmp_path / "orig.csv").write_text("\n".join(orig) + "\n", encoding="utf-8")
    for m, seed in (("llama", 1), ("granite", 2)):
        ls = list(lines_from(labels, m, sep, views=views, seed=seed).values())
        if mutate:
            mutate(m, ls)
        (tmp_path / f"{m}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in ls), encoding="utf-8")
    (tmp_path / "q.json").write_text('{"quality_fail": []}', encoding="utf-8")
    return Namespace(labels=tmp_path / "labels.csv", quality=tmp_path / "q.json", llama=tmp_path / "llama.jsonl",
                     granite=tmp_path / "granite.jsonl", out=tmp_path / "out", original_labels=tmp_path / "orig.csv",
                     repo_root=REPO_ROOT, b=50, seed=20261023,
                     git=lambda args, cwd: (Path(cwd) / args[1].split(":", 1)[1]).read_bytes())


def test_run_ok_primary_and_sensitivity(tmp_path):
    from scripts import analyse_replication_granite as A
    a = _setup(tmp_path)
    a.quality.write_text(json.dumps({"quality_fail": [sorted(load_labels(a.labels))[0]]}), encoding="utf-8")
    res = A.run(a)
    assert res["primary"]["n"] == 12 and res["sensitivity"]["n"] == 11
    assert set(res["primary"]["hypotheses"]) == {"G1", "G2", "G3", "G4"}
    assert set(res["primary"]["descriptive"]) == {"llama", "granite"}
    assert res["prereg_sha256"] == {str(RG.PREREG[0]): RG.PREREG[1], str(RG.AMENDMENT[0]): RG.AMENDMENT[1]}


def _bad(field, value, monitor="granite"):
    def mutate(m, ls):
        if m == monitor:
            ls[0][field] = value
    return mutate


@pytest.mark.parametrize("mutate", [
    _bad("digest", "0" * 64), _bad("digest", RG.MONITORS["granite"][1], "llama"),
    _bad("prompt_version", "monitor_v3_pairs_ctx16k"), _bad("prompt_version", "monitor_v3_pairs_ctx16k_granite", "llama"),
    _bad("model", "llama3.1:8b"), _bad("prompt_sha256", "0" * 64), _bad("sample_idx", 1),
    _bad("view", "V5"), _bad("game_id", "g_notlabelled"),
    lambda m, ls: ls.append(dict(ls[0])) if m == "llama" else None,                  # duplicate line
])
def test_run_refuses_bad_lines(tmp_path, mutate):
    from scripts import analyse_replication_granite as A
    with pytest.raises(RG.RefusedError):
        A.run(_setup(tmp_path, mutate))


def test_run_refuses_original_dataset_games(tmp_path):
    from scripts import analyse_replication_granite as A
    a = _setup(tmp_path)
    a.original_labels.write_text("game_id,episode_type,collusion,focal_pair,variant,synthetic\n"
                                 f"{sorted(load_labels(a.labels))[0]},1,1,M|T,v,false\n", encoding="utf-8")
    with pytest.raises(RG.RefusedError, match="ORIGINAL"):
        A.run(a)


def test_run_refuses_prereg_and_amendment_problems(tmp_path, monkeypatch):
    from scripts import analyse_replication_granite as A
    a = _setup(tmp_path)
    a.git = lambda args, cwd: b"not the committed text"                              # working copy != blob
    with pytest.raises(RG.RefusedError, match="committed blob"):
        A.run(a)
    a.git = lambda args, cwd: (_ for _ in ()).throw(RuntimeError("fatal: path not in HEAD"))   # not committed
    with pytest.raises(RG.RefusedError, match="cannot read"):
        A.run(a)
    a.git = lambda args, cwd: (Path(cwd) / args[1].split(":", 1)[1]).read_bytes()  # blob == working copy again
    monkeypatch.setattr(RG, "AMENDMENT", (RG.AMENDMENT[0], "0" * 64))                # sha mismatch
    with pytest.raises(RG.RefusedError, match="sha256"):
        A.run(a)


def test_run_refuses_config_hash_mismatch(tmp_path, monkeypatch):
    from scripts import analyse_replication_granite as A
    a = _setup(tmp_path)
    monkeypatch.setattr(RG, "FROZEN", (RG.FROZEN[0], "0" * 64))
    with pytest.raises(RG.RefusedError, match="frozen monitor"):
        A.run(a)
    monkeypatch.undo()
    monkeypatch.setattr(RG, "GRANITE_MANIFEST_SHA256", "0" * 64)
    with pytest.raises(RG.RefusedError, match="granite manifest"):
        A.run(a)


def test_run_refuses_quality_and_second_run(tmp_path, capsys):
    from scripts import analyse_replication_granite as A
    a = _setup(tmp_path)
    a.quality.write_text('["g_x00000000"]', encoding="utf-8")                         # wrong format
    with pytest.raises(RG.RefusedError, match="quality_fail"):
        A.run(a)
    a.quality.write_text('{"quality_fail": ["g_unknown"]}', encoding="utf-8")
    with pytest.raises(RG.RefusedError, match="not labelled"):
        A.run(a)
    a.quality.write_text('{"quality_fail": []}', encoding="utf-8")
    argv = ["--labels", str(a.labels), "--quality", str(a.quality), "--llama", str(a.llama), "--granite",
            str(a.granite), "--out", str(a.out), "--original-labels", str(a.original_labels), "--b", "50"]
    assert A.main(argv) == 0 and (a.out / "results.json").exists()                   # real git: preregs committed
    assert A.main(argv) == 2 and "REFUSED" in capsys.readouterr().out                # no second run


def test_plan_prints_run_order(capsys):
    from scripts import analyse_replication_granite as A
    assert A.main(["--plan"]) == 0
    out = capsys.readouterr().out
    assert "~22 min" in out and "192 calls" in out and "analyse_replication_23.py" in out


# --------------------------------------------------------------------------- report 15C reproduced (granite only)

R15 = REPO_ROOT / "runs" / "rq9_granite"


@pytest.mark.skipif(not ((R15 / "outputs" / "monitor.jsonl").exists() and (R15 / "results.json").exists()
                         and (REPO_ROOT / "data" / "split.json").exists()),
                    reason="15C local outputs not on this machine")
def test_reproduces_15c_aurocs():
    labels = load_labels(REPO_ROOT / "data" / "labels.csv")
    test = sorted(json.loads((REPO_ROOT / "data" / "split.json").read_text(encoding="utf-8"))["test"])
    granite = {}
    for raw in (R15 / "outputs" / "monitor.jsonl").read_text(encoding="utf-8").splitlines():
        if raw.strip():
            d = json.loads(raw)
            granite[(d["game_id"], d["view"])] = d
    d = RG.descriptive(test, granite, labels)
    r15 = json.loads((R15 / "results.json").read_text(encoding="utf-8"))
    for v in RG.VIEWS:
        for k in ("estimate", "ci_low", "ci_high"):
            assert d[v]["auroc"][k] == pytest.approx(r15["views"][v]["auroc"][k], abs=5e-5), (v, k)
        assert d[v]["last_position_max"]["k"] == r15["views"][v]["lpm"]["k"]
        assert d[v]["top1"]["correct"] == r15["views"][v]["top1"]["correct"]
    assert [d[v]["auroc"]["estimate"] for v in RG.VIEWS] == [0.7292, 0.7674, 0.7361, 0.5104]   # report 15C §4.2
