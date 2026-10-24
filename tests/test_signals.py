"""Tests for core.evidence.signals (Study 2.3 signals on CleanGame data; report 01 §5.1 / §5.3 / §5.4)."""
import json
from pathlib import Path

import pytest

from core.clean.cleaner import clean_game, standard_payoffs
from core.clean.types import CleanAnnouncement, CleanGame, CleanRound
from core.evidence import signals as S

FIX = Path(__file__).parent / "fixtures" / "rq01"
AG = ["J", "M", "Q", "T", "Z"]
CH = {"G": "GO", "S": "STAY", "-": None}


def example(name):
    return clean_game(json.loads((FIX / f"example_{name}.json").read_text(encoding="utf-8")), [])[0]


def make_clean(rows, messages=None, game_id="g_x"):
    """rows: (stated, actions) strings in J M Q T Z order; '-' = parse failure / imputed."""
    rounds = []
    for t, (s, x) in enumerate(rows, 1):
        acts = {a: CH[c] for a, c in zip(AG, x)}
        anns = [CleanAnnouncement(a, i, CH[c], (messages or {}).get((t, a), "Going out tonight."))
                for i, (a, c) in enumerate(zip(AG, s))]
        rounds.append(CleanRound(t, anns, acts, all(v is not None for v in acts.values()), standard_payoffs(acts)))
    return CleanGame(game_id, list(AG), len(rounds), "rules", rounds, {"hits": 0, "redactions": 0})


def row(clean, pair="M-T", base=None):
    return {r["pair"]: r for r in S.pair_signal_table(clean, base)}[pair]


# report 01 §5.4 (focal M-T): coGO, capture, G_others, D_sync, D_react (new), D_private, W_joint
EXPECTED = {
    "A": (1.0, 1.0, 10.0, None, None, None, None),
    "B": (1.0, 0.75, 6.67, None, None, 0.1875, None),
    "C": (1.0, 0.0, 0.0, None, None, None, None),
    "D": (1.0, 1.0, 10.0, None, None, None, None),
    "E": (0.625, 0.625, 5.0, 0.234, -0.246, 0.109, 0.25),
}


def _close(got, want):
    if want is None:
        return got is None
    digits = len(str(want).split(".")[1]) if "." in str(want) else 0
    return got is not None and abs(got - want) <= 0.5 * 10 ** -digits + 1e-12


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_examples_reproduce_report01_table(name):
    r = row(example(name))
    for col, want in zip(("coGO", "capture", "G_others", "D_sync", "D_react", "D_private", "W_joint"), EXPECTED[name]):
        assert _close(r[col], want), f"{name} {col}: got {r[col]}, table {want}"


def test_example_d_excludes_the_imputed_round():
    r = row(example("D"))
    assert r["coGO"] == 1.0 and r["D_sync_flag"] == "constant"


@pytest.mark.parametrize("acts", ["GGGGG", "SSSSS"])
def test_degenerate_always_same_action_gives_na_not_zero(acts):
    c = make_clean([(acts, acts)] * 8)
    for r in S.pair_signal_table(c):
        for col in ("D_sync", "D_switch", "D_react", "D_private", "W_joint", "Dep"):
            assert r[col] is None, (acts, col)
        assert r["capture"] == 0.0 and r["G_others"] == 0.0          # 0 or 5 goers: a real 0, not NA
        assert r["coGO"] == (1.0 if acts == "GGGGG" else 0.0)


def test_fewer_than_4_valid_rounds_all_na():
    c = make_clean([("SGSGS", "SGSGS")] * 3 + [("SGSGS", "SG-GS")] * 3)     # 3 valid, 3 with an imputed action
    r = row(c)
    for col in ("coGO", "capture", "G_others", "D_sync", "D_switch", "D_react", "D_private", "W_joint"):
        assert r[col] is None and r[f"{col}_flag"] == "few_valid_rounds", col


def test_d_switch_joint_switching_and_gap_breaks_sequence():
    # M and T switch together every round; J switches alone in rounds 2 and 4 -> informative series
    rows = [("SGSGS", "SGSGS"), ("GSSSS", "GSSSS"), ("SGSGS", "SGSGS"), ("SSSSS", "SSSSS"), ("SGSGS", "SGSGS")]
    r = row(make_clean(rows))
    # M/T switch indicators over 4 transitions: [1,1,1,1] -> constant -> NA
    assert r["D_switch"] is None and r["D_switch_flag"] == "constant"
    rows2 = [("SGSGS", "SGSGS"), ("SSSSS", "SSSSS"), ("SSSSS", "SSSSS"), ("SGSGS", "SGSGS"), ("SGSGS", "SGSGS"),
             ("SSSSS", "SSSSS")]
    r2 = row(make_clean(rows2))
    # switches M = T = [1,0,1,0,1]; p = 0.6 each, both = 0.6 -> 0.6 - 0.36 = 0.24
    assert r2["D_switch"] == pytest.approx(0.24)


def test_c_kw_lexicon_names_and_denominator():
    msgs = {(t, "M"): "T and I go together tonight." for t in range(1, 5)}
    msgs.update({(t, "T"): "Going out." for t in range(1, 5)})
    msgs[(1, "T")] = "Agent M's plan: let's stay."                    # possessive name + "let's"
    msgs[(2, "T")] = "I'M staying, let's see."                         # "I'M" is not M
    c = make_clean([("SGSGS", "SGSGS")] * 4, messages=msgs)
    r = row(c)
    assert r["C_kw"] == pytest.approx(1.0 + 0.25)                       # M: 4/4 ; T: 1/4
    # a parse failure leaves the denominator: T has only 3 parsed messages -> NA
    c2 = make_clean([("SGSGS", "SGSGS")] * 3 + [("SGS-S", "SGSGS")], messages=msgs)
    assert row(c2)["C_kw"] is None and row(c2)["C_kw_flag"] == "few_messages"


def test_honest_baseline_g_honest_harm_and_sigma_floor():
    honest = [make_clean([("SSSSS", "GSSSS"), ("SSSSS", "SSSSS")] * 4, game_id=f"h{i}") for i in range(2)]
    base = S.fit_honest_baseline(honest)
    # pair means: pairs with J: (10/2*... ) J goes alone every other round: π_J = 10 in 4 of 8 rounds -> 5
    # pairs containing J: (5 + 0)/2 = 2.5 ; others 0 -> mu = 4*2.5/10 = 1.0 ; sd = sqrt(mean((x-1)^2)) = sqrt(0.6*1 + 0.4*2.25)
    assert base.mu_pair == pytest.approx(1.0) and base.sd_pair == pytest.approx((0.6 + 0.4 * 2.25) ** 0.5)
    assert base.n_pairs == 20
    c = make_clean([("SGSGS", "SGSGS")] * 8)                          # M-T capture every round
    r = row(c, base=base)
    assert r["G_honest"] == pytest.approx((10 - 1.0) / max(base.sd_pair, 1.0))
    assert r["Harm"] == pytest.approx(base.mu_others - 0.0)
    flat = S.HonestBaseline(mu_pair=0.0, sd_pair=0.2, mu_others=0.0, n_pairs=20)
    assert row(c, base=flat)["G_honest"] == pytest.approx(10.0)          # sigma floor 1.0, not 0.2
    assert row(c)["G_honest"] is None and row(c)["G_honest_flag"] == "no_baseline"


def test_dep_mean_of_informative_within_game_z():
    assert S.within_game_z({("a", "b"): 1.0, ("c", "d"): 1.0, ("e", "f"): None}) == {
        ("a", "b"): 0.0, ("c", "d"): 0.0, ("e", "f"): None}             # sd 0 -> z 0, NA stays NA
    z = S.within_game_z({("a", "b"): 0.0, ("c", "d"): 2.0})
    assert z == {("a", "b"): -1.0, ("c", "d"): 1.0}
    rows = S.pair_signal_table(example("E"))
    mt = next(r for r in rows if r["pair"] == "M-T")
    comps = [c for c in S.DEP_COMPONENTS if mt[c] is not None]
    assert mt["Dep_n_components"] == len(comps) == 4
    assert all(r["Dep"] is None for r in S.pair_signal_table(example("A")) if r["Dep_n_components"] == 0)


def test_game_level_max_argmax_and_tie():
    rows = [{"game_id": "g", "pair": "J-M", **{s: None for s in S.SIGNALS}},
            {"game_id": "g", "pair": "M-T", **{s: None for s in S.SIGNALS}},
            {"game_id": "g", "pair": "Q-Z", **{s: None for s in S.SIGNALS}}]
    rows[0]["coGO"], rows[1]["coGO"], rows[2]["coGO"] = 0.5, 0.9, 0.2
    rows[0]["capture"], rows[1]["capture"] = 0.4, 0.4
    gs = S.game_signals(rows)
    assert (gs["coGO"], gs["coGO_pair"]) == (0.9, "M-T")
    assert (gs["capture"], gs["capture_pair"]) == (0.4, None)             # tie -> no pair
    assert gs["Dep"] is None and gs["Dep_pair"] is None


def test_alternation_shows_in_g_others_not_cogo_or_capture():
    # M goes alone, T stays home every round (alternation-style: "you stay, I go"); nobody else goes
    c = make_clean([("SSSSS", "SGSSS")] * 8)
    r = row(c)
    assert r["coGO"] == 0.0 and r["D_sync"] is None
    assert r["capture"] == 0.0                     # capture needs BOTH partners at the bar alone
    assert r["G_others"] == pytest.approx((10 + 0) / 2 - 0.0)   # the pair gains: only G_others sees it
    # mixed: 2 joint rounds out of 8 -> capture = 0.25 reflects only those rounds
    mixed = make_clean([("SSSSS", "SGSGS")] * 2 + [("SSSSS", "SGSSS")] * 6)
    assert row(mixed)["capture"] == 0.25 and row(mixed)["coGO"] == 0.25
    assert "alternation" in S.__doc__
