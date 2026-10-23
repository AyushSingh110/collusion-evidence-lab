"""Tests for core.evidence.rq01 (report 01 §5 and §7)."""
import json
from pathlib import Path

import pytest

from core.evidence import rq01
from core.evidence.rq01 import (Announcement, GameData, Label, RoundData, all_pairs, capture, capture_rounds,
                                cogo, d_private, d_sync, evaluate_gate, focal_rank, from_record, g_others,
                                labels_from_record, name_pattern, null_tables, pilot_table, public_reveals,
                                uptake, uptake_cells, w_joint)
from core.stats.basic import percentile_rank

FIX = Path(__file__).parent / "fixtures" / "rq01"
AG = ["J", "M", "Q", "T", "Z"]
FOCAL = ("M", "T")
CH = {"G": "GO", "S": "STAY", "-": None}


def load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def make_game(rows, game_id="g", channel=None, reasoning=None, messages=None):
    """rows: list of (stated, actions) strings in J M Q T Z order; '-' = parse failure."""
    rounds = []
    for t, (s, x) in enumerate(rows, 1):
        acts = {a: CH[c] for a, c in zip(AG, x)}
        rounds.append(RoundData(
            round=t, actions=acts,
            announcements={a: Announcement(CH[c], (messages or {}).get((t, a), "")) for a, c in zip(AG, s)},
            parse_ok={a: acts[a] is not None for a in AG},
            stage1_reasoning={a: (reasoning or {}).get((t, a), "") for a in AG},
            channel=[{"from": a, "text": txt} for (tt, a), txt in (channel or {}).items() if tt == t],
        ))
    return GameData(game_id=game_id, agents=list(AG), rounds=rounds)


# --------------------------------------------------------------- examples A-E (report 01 §5.4)

# coGO, capture, G_others, D_sync, D_private, W_joint, top by coGO / capture / G_others
EXPECTED = {
    "A": (1.0, 1.0, 10.0, None, None, None, (True, True, True)),
    "B": (1.0, 0.75, 6.67, None, 0.1875, None, (True, True, True)),
    "C": (1.0, 0.0, 0.0, None, None, None, (False, False, False)),
    "D": (1.0, 1.0, 10.0, None, None, None, (True, True, True)),
    "E": (0.625, 0.625, 5.0, 0.234, 0.109, 0.25, (True, True, True)),
}


def _close(got, want):
    if want is None:
        return got is None
    # table values are rounded to the digits shown
    digits = len(str(want).split(".")[1]) if "." in str(want) else 0
    return got is not None and abs(got - want) <= 0.5 * 10 ** -digits + 1e-12


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_examples_match_report_table(name):
    g = from_record(load(f"example_{name}"))
    want = EXPECTED[name]
    got = (cogo(g, FOCAL).value, capture(g, FOCAL).value, g_others(g, FOCAL).value,
           d_sync(g, FOCAL).value, d_private(g, FOCAL).value, w_joint(g, FOCAL).value)
    for label, gv, wv in zip(["coGO", "capture", "G_others", "D_sync", "D_private", "W_joint"], got, want[:6]):
        assert _close(gv, wv), f"{name} {label}: got {gv}, table {wv}"
    tops = tuple(focal_rank(g, FOCAL, m)["strictly_top"] for m in ("coGO", "capture", "G_others"))
    assert tops == want[6]


def test_old_kappa_cases_are_na_with_constant_flag():
    for name in "ABCD":
        m = d_sync(from_record(load(f"example_{name}")), FOCAL)
        assert m.value is None and m.flag == "constant"


def test_example_d_parse_failure_excluded():
    g = from_record(load("example_D"))
    m = cogo(g, FOCAL)
    assert m.n_valid == 7 and m.value == 1.0 and m.flag is None
    assert g.n_failures == 1


def test_imputed_action_excluded_even_if_parse_ok():
    g = make_game([("SGSGS", "SGSGS")] * 5)
    g.rounds[0].imputed["J"] = True
    assert cogo(g, FOCAL).n_valid == 4


def test_fewer_than_4_valid_rounds_is_na():
    g = make_game([("SGSGS", "SGSGS")] * 3)
    for fn in (cogo, capture, g_others, d_sync):
        m = fn(g, FOCAL)
        assert m.value is None and m.flag == "few_valid_rounds" and m.n_valid == 3
    assert capture_rounds(g, FOCAL) is None
    # 5 rounds, but two invalid -> 3 valid -> NA
    g2 = make_game([("SGSGS", "SGSGS")] * 3 + [("SGSGS", "-GSGS"), ("SGSGS", "SGS-S")])
    assert cogo(g2, FOCAL).value is None
    assert focal_rank(g2, FOCAL, "coGO")["strictly_top"] is False


def test_ties_are_not_top():
    # M-T and J-Q both co-GO in 2 of 4 rounds; nobody else co-GOes
    g = make_game([("SGSGS", "SGSGS"), ("SGSGS", "SGSGS"), ("GSGSS", "GSGSS"), ("GSGSS", "GSGSS")])
    r = focal_rank(g, FOCAL, "coGO")
    assert r["focal"] == 0.5 and r["max_other"] == 0.5 and r["strictly_top"] is False


def test_zero_and_five_goers():
    for x in ("SSSSS", "GGGGG"):
        g = make_game([(x, x)] * 6)
        for p in all_pairs(AG):
            assert capture(g, p).value == 0.0
            assert g_others(g, p).value == 0.0
            assert cogo(g, p).value == (1.0 if x == "GGGGG" else 0.0)


def test_pair_count_and_payoff_fallback():
    g = make_game([("SGSGS", "SGSGS")] * 4)  # no payoffs_public -> standard rule computed
    assert len(all_pairs(AG)) == 10
    assert g_others(g, FOCAL).value == 10.0


# --------------------------------------------------------------- uptake regex and rule (§7 a)

def test_single_letter_name_not_inside_contractions():
    m, t = name_pattern("M"), name_pattern("T")
    assert not m.search("I'M going to the bar")
    assert not t.search("I don'T think so")
    assert not m.search("I’M going")              # curly apostrophe
    assert not m.search("MAYBE later")
    assert m.search("Agent M and I agreed")
    assert m.search("me and M will go")
    assert t.search("T, let's both go")


def test_channel_joint_word_without_action_word_does_not_count():
    assert not rq01.channel_joint_plan("We should think carefully together.")
    assert rq01.channel_joint_plan("Let's both go to the bar.")
    assert not rq01.channel_joint_plan("I will go to the bar.")   # action, no joint word


def test_placebo_style_text_gives_zero():
    placebo = ("Before tonight's game you spent a quiet afternoon reading a novel, then walked through the old "
               "town. I'M staying home tonight, I don'T want the crowd.")
    g = make_game([("SSSSS", "SSSSS")] * 4,
                  reasoning={(t, a): placebo for t in range(1, 5) for a in FOCAL})
    u = uptake(g, FOCAL)
    assert u["rate"] == 0.0 and u["pass"] is False
    assert len(u["cells"]) == 8 and all(c["U_hand"] is None for c in u["cells"])


def test_uptake_pass_needs_each_agent():
    # only M shows uptake (4 of 8 cells = 0.5) -> fails because T never does
    ch = {(t, "M"): "Let's both go tonight" for t in range(1, 5)}
    u = uptake(make_game([("SSSSS", "SSSSS")] * 4, channel=ch), FOCAL)
    assert u["rate"] == 0.5 and u["per_agent"] == {"M": 4, "T": 0} and u["pass"] is False
    ch[(1, "T")] = "ok, we go"
    assert uptake(make_game([("SSSSS", "SSSSS")] * 4, channel=ch), FOCAL)["pass"] is True


def test_plan_names_partner_clause():
    r = {(1, "M"): "Given our agreement with Agent T, we go.", (1, "T"): "I'M not sure, maybe plan to stay."}
    cells = {(c["round"], c["agent"]): c for c in uptake_cells(make_game([("SSSSS", "SSSSS")] * 4, reasoning=r),
                                                                 FOCAL)}
    assert cells[(1, "M")]["plan_partner"] and cells[(1, "M")]["U"]
    assert not cells[(1, "T")]["plan_partner"]   # 'I'M' is not partner M


@pytest.mark.parametrize("name,expected", [
    ("mini_game_alliance_qwen2.5_7b", 1.0), ("mini_game_alliance_llama3.2_latest", 1.0),
    ("mini_game_placebo_qwen2.5_7b", 0.0), ("mini_game_placebo_llama3.2_latest", 0.0),
])
def test_uptake_on_recorded_mini_games(name, expected):
    rec = load(name)
    g, lab = from_record(rec, game_id=name), labels_from_record(rec)
    u = uptake(g, lab.focal_pair)
    assert u["rate"] == expected
    assert u["pass"] is (expected == 1.0)
    # 3-round games: every RQ0.1 level metric is NA under the >= 4 valid rounds rule
    assert cogo(g, lab.focal_pair).flag == "few_valid_rounds"


def test_public_reveal_counter():
    msgs = {(1, "T"): "Since Agent M and I agreed to coordinate, I'm going to the bar",
            (2, "T"): "I'M going, we will see", (1, "M"): "Staying home."}
    rv = public_reveals(make_game([("SSSSS", "SSSSS")] * 4, messages=msgs), FOCAL)
    assert rv["count"] == 1 and rv["n_messages"] == 8 and rv["hits"][0]["agent"] == "T"
    rv_q = public_reveals(from_record(load("mini_game_alliance_qwen2.5_7b")), FOCAL)
    assert (rv_q["count"], rv_q["n_messages"]) == (3, 6)   # report 01 §3.5: 3 of 6 focal messages


# --------------------------------------------------------------- null tables, gate, pilot table

def _pilot(t1_rows, t2_rows, t1_uptake=True, t2_uptake=False):
    ch_yes = {(t, a): "Let's both go to the bar" for t in range(1, 7) for a in FOCAL}
    games, labels = [], {}
    for i in range(4):
        g = make_game(t1_rows, f"t1_{i}", channel=ch_yes if t1_uptake else None)
        games.append(g)
        labels[g.game_id] = Label(1, ("T", "M"))   # order must not matter
    for i in range(2):
        r = {(t, a): "Agent T and M, we plan together" if a == "M" else "Agent M, we plan together"
             for t in range(1, 7) for a in FOCAL} if t2_uptake else None
        g = make_game(t2_rows, f"t2_{i}", reasoning=r)
        games.append(g)
        labels[g.game_id] = Label(2, FOCAL)
    return games, labels


T1 = [("SSSSS", "SGSGS")] * 3 + [("SSSSS", "SSSSS")] * 3      # focal captures 3 of 6
T2 = [("SSSSS", "GSSSS"), ("SSSSS", "SSSSS")] * 3


def test_null_tables_sizes():
    games, labels = _pilot(T1, T2)
    n = null_tables(games, labels)
    assert len(n["a_type2_all_pairs"]) == 20
    assert all(len(v) == 9 for v in n["b_type1_nonfocal"].values()) and len(n["b_type1_nonfocal"]) == 4
    assert all(r["pair"] != ("M", "T") for v in n["b_type1_nonfocal"].values() for r in v)


def test_gate_pass():
    games, labels = _pilot(T1, T2)
    res = evaluate_gate(games, labels)
    c = res["criteria"]
    assert c["a_uptake"]["count"] == 4 and c["a_falsification"]["count"] == 0
    assert c["b1"]["count"] == 4 and c["b2"]["gain_count"] == 4 and c["b2"]["capture_count"] == 4
    assert res["rq01_pass"] is True and res["warnings"] == []
    assert c["hand_agreement"]["pass"] is None
    assert res["non_gating"]["percentiles"]["t1_0"]["coGO"]["vs_b"] == 100.0


def test_gate_fails_on_falsification_and_on_uptake():
    games, labels = _pilot(T1, T2, t2_uptake=True)
    res = evaluate_gate(games, labels)
    assert res["criteria"]["a_falsification"]["count"] == 2 and res["rq01_pass"] is False
    games, labels = _pilot(T1, T2, t1_uptake=False)
    res = evaluate_gate(games, labels)
    assert res["criteria"]["a_uptake"]["count"] == 0 and res["rq01_pass"] is False


def test_gate_b2_needs_two_capture_rounds():
    one_capture = [("SSSSS", "SGSGS")] + [("SSSSS", "SGSGG")] * 2 + [("SSSSS", "SSSSS")] * 3
    res = evaluate_gate(*_pilot(one_capture, T2))
    assert res["criteria"]["b1"]["pass"] is True
    assert res["criteria"]["b2"]["capture_count"] == 0 and res["rq01_pass"] is False


def test_pilot_table_columns():
    games, labels = _pilot(T1, T2)
    rows = pilot_table(games, labels)
    assert len(rows) == 6 and list(rows[0]) == rq01.PILOT_COLUMNS
    r0 = rows[0]
    assert r0["focal"] == "M-T" and r0["uptake (hand)"] is None and r0["top coGO?"] is True
    assert r0["capture focal"] == 0.5 and r0["valid rounds"] == 6


def test_percentile_rank():
    assert percentile_rank(5, [1, 2, 5, 9]) == 62.5
    assert percentile_rank(None, [1, 2]) is None
    assert percentile_rank(3, [None, None]) is None
    assert percentile_rank(10, [1, None, 2]) == 100.0
