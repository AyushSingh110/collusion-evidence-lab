import pytest

from core.clean.leaks import scan_for_leaks
from core.generate import prompts as P

ALLIANCE = P.addendum_text(1, "T")
INCENTIVE = P.addendum_text(4, "T")


def kinds(hits):
    return {h["kind"] for h in hits}


def test_copy_of_eight_words_is_caught():
    msg = "Hey all, your aim is the combined payout of you and Agent T, so I go."
    hits = scan_for_leaks(msg, [ALLIANCE], game_id="g_1", agent="M", round=2, field="stage2.message")
    assert "copy8" in kinds(hits)
    assert hits[0]["game_id"] == "g_1" and hits[0]["agent"] == "M" and hits[0]["round"] == 2


def test_seven_words_are_not_a_copy():
    assert "copy8" not in kinds(scan_for_leaks("your aim is the combined payout of me", [ALLIANCE]))


@pytest.mark.parametrize("msg,term", [("This experiment is fun", "experiment"),
                                      ("I got a secret plan", "secret"),
                                      ("My PRIVATE NOTE says go", "private note"),
                                      ("I follow my instruction", "instruction")])
def test_banned_terms_are_caught(msg, term):
    hits = scan_for_leaks(msg, [])
    assert any(h["kind"] == "banned" and h["match"] == term for h in hits)


@pytest.mark.parametrize("msg", ["Staying home costs me -8 tonight", "home pays $-8 for me", "I lose my deposit",
                                 "my real payoff is better at the bar", "given your own situation", "it's − 8 for me"])
def test_4b_patterns_are_caught(msg):
    assert "pattern_4b" in kinds(scan_for_leaks(msg, [INCENTIVE]))


@pytest.mark.parametrize("msg", ["I'll go, payoffs are -5 if crowded", "5-8 people is too many", "-80 is silly",
                                 "-8.5 is not our number", "we got 8 points"])
def test_4b_minus_8_pattern_has_no_false_hits(msg):
    assert not [h for h in scan_for_leaks(msg, []) if h["match"].startswith(("minus_8", "dollar_minus_8"))]


def test_clean_message_has_no_hits():
    msg = "Last round the bar was packed, so I'll stay home this time. Have a good evening, everyone!"
    assert scan_for_leaks(msg, [ALLIANCE, INCENTIVE, P.addendum_text(2, "T"), P.addendum_text(3, "T")]) == []


def test_export_setup_texts_contains_every_fill_and_v3():
    from scripts.export_setup_texts import PRIVATE_LINES, setup_texts
    texts = setup_texts()
    for a in "JMQTZ":
        assert P.read_prompt("alliance_v3.txt").replace("{P}", a) in texts
        assert P.read_prompt("persona_v1.txt").replace("{P}", a) in texts
    assert P.read_prompt("placebo_v3.txt") in texts and P.read_prompt("incentive_4b_v1.txt") in texts
    assert all(line in texts for line in PRIVATE_LINES)
    assert not any("{P}" in t for t in texts) and len(texts) == len(set(texts))
